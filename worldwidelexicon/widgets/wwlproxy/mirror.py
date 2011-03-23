#!/usr/bin/env python
# Copyright 2008 Brett Slatkin
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Brett Slatkin (bslatkin@gmail.com)"

import datetime
import hashlib
import logging
import pickle
import re
import time
import urllib
import string
import wsgiref.handlers

from translate import DerMundoProjects

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.runtime import apiproxy_errors
from google.appengine.api.labs import taskqueue
from database import Translation
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup, Comment

import facebook
from home import User
from database import Settings
from home import geolocate
from webappcookie import Cookies

import transform_content

blocked_extensions = ['mpg', 'mov', 'mp4']

blocked_domains = ['youtube.com', 'vimeo.com']

acceptable_elements = ['a', 'abbr', 'acronym', 'address', 'area', 'b', 'big',
      'blockquote', 'br', 'button', 'caption', 'center', 'cite', 'code', 'col',
      'colgroup', 'dd', 'del', 'dfn', 'dir', 'div', 'dl', 'dt', 'em',
      'font', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 
      'ins', 'kbd', 'label', 'legend', 'li', 'map', 'menu', 'ol', 
      'p', 'pre', 'q', 's', 'samp', 'small', 'span', 'strike',
      'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
      'thead', 'tr', 'tt', 'u', 'ul', 'var']

acceptable_attributes = ['abbr', 'accept', 'accept-charset', 'accesskey',
  'action', 'align', 'alt', 'axis', 'border', 'cellpadding', 'cellspacing',
  'char', 'charoff', 'charset', 'checked', 'cite', 'clear', 'cols',
  'colspan', 'color', 'compact', 'coords', 'datetime', 'dir', 
  'enctype', 'for', 'headers', 'height', 'href', 'hreflang', 'hspace',
  'id', 'ismap', 'label', 'lang', 'longdesc', 'maxlength', 'method',
  'multiple', 'name', 'nohref', 'noshade', 'nowrap', 'prompt', 
  'rel', 'rev', 'rows', 'rowspan', 'rules', 'scope', 'shape', 'size',
  'span', 'src', 'start', 'summary', 'tabindex', 'target', 'title', 'type',
  'usemap', 'valign', 'value', 'vspace', 'width']

def clean_html( fragment ):
    #while True:
        soup = BeautifulSoup( fragment )
        removed = False        
        for tag in soup.findAll(True): # find all tags
            if tag.name == 'script':
            #if tag.name not in acceptable_elements:
                tag.extract() # remove the bad ones
                removed = True
            else: # it might have bad attributes
                # a better way to get all attributes?
                for attr in tag._getAttrMap().keys():
                    if attr not in acceptable_attributes:
                        del tag[attr]

        # turn it back to html
        fragment = unicode(soup)
        #
        #if removed:
        #    # we removed tags and tricky can could exploit that!
        #    # we need to reparse the html until it stops changing
        #    continue # next round
        return fragment

javascript_header = """<link href="/wwlproxy/dermundo.css" rel="stylesheet" type="text/css" charset="utf-8"/>
<script language="javascript" type="text/javascript" charset="utf-8">
var dermundo_serviceUrl = "www.dermundo.com";
var dermundo_imagesPath = "/wwlproxy/img/";
</script>
<script src="/wwlproxy/dermundo.js" type="text/javascript" charset="utf-8"></script>"""

################################################################################

DEBUG = False
EXPIRATION_DELTA_SECONDS = 90
EXPIRATION_RECENT_URLS_SECONDS = 90

## DEBUG = True
## EXPIRATION_DELTA_SECONDS = 10
## EXPIRATION_RECENT_URLS_SECONDS = 1

HTTP_PREFIX = "http://"
HTTPS_PREFIX = "http://"

IGNORE_HEADERS = frozenset([
  'set-cookie',
  'expires',
  'cache-control',

  # Ignore hop-by-hop headers
  'connection',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailers',
  'transfer-encoding',
  'upgrade',
])

TRANSFORMED_CONTENT_TYPES = frozenset([
  "text/html",
  "text/css",
])

MIRROR_HOSTS = frozenset([
  'mirrorr.com',
  'mirrorrr.com',
  'www.mirrorr.com',
  'www.mirrorrr.com',
  'www1.mirrorrr.com',
  'www2.mirrorrr.com',
  'www3.mirrorrr.com',
])

MAX_CONTENT_SIZE = 10 ** 6

MAX_URL_DISPLAY_LENGTH = 50

################################################################################

def get_url_key_name(url):
  url_hash = hashlib.sha256()
  url_hash.update(url)
  return "hash_" + url_hash.hexdigest()

################################################################################

class EntryPoint(db.Model):
  translated_address = db.TextProperty(required=True)
  last_updated = db.DateTimeProperty(auto_now=True)
  display_address = db.TextProperty()


class MirroredContent(object):
  def __init__(self, original_address, translated_address,
               status, headers, data, base_url):
    self.original_address = original_address
    self.translated_address = translated_address
    self.status = status
    self.headers = headers
    self.data = data
    self.base_url = base_url

  @staticmethod
  def get_by_key_name(key_name):
    return memcache.get(key_name)

  @staticmethod
  def fetch_and_store(key_name, base_url, translated_address, mirrored_url):
    """Fetch and cache a page.
    
    Args:
      key_name: Hash to use to store the cached page.
      base_url: The hostname of the page that's being mirrored.
      translated_address: The URL of the mirrored page on this site.
      mirrored_url: The URL of the original page. Hostname should match
        the base_url.
    
    Returns:
      A new MirroredContent object, if the page was successfully retrieved.
      None if any errors occurred or the content could not be retrieved.
    """
    # Check for the X-Mirrorrr header to ignore potential loops.
    if base_url in MIRROR_HOSTS:
      logging.warning('Encountered recursive request for "%s"; ignoring',
                      mirrored_url)
      return None
    
    blocked=False
    logging.debug("Fetching '%s'", mirrored_url)
    for b in blocked_extensions:
      if string.count(mirrored_url, b) > 0:
        blocked=True
    for b in blocked_domains:
      if string.count(mirrored_url, b) > 0:
        blocked=True
    if not blocked:
      try:
        response = urlfetch.fetch(mirrored_url)
      except (urlfetch.Error, apiproxy_errors.Error):
        #logging.exception("Could not fetch URL")
        return None
    else:
      return None

    adjusted_headers = {}
    for key, value in response.headers.iteritems():
      adjusted_key = key.lower()
      if adjusted_key not in IGNORE_HEADERS:
        adjusted_headers[adjusted_key] = value

    content = response.content
    page_content_type = adjusted_headers.get("content-type", "")
    for content_type in TRANSFORMED_CONTENT_TYPES:
      # Startswith() because there could be a 'charset=UTF-8' in the header.
      if page_content_type.startswith(content_type):
        content = transform_content.TransformContent(base_url, mirrored_url,
                                                     content)
        break

    # If the transformed content is over 1MB, truncate it (yikes!)
    if len(content) > MAX_CONTENT_SIZE:
      logging.warning('Content is over 1MB; truncating')
      content = content[:MAX_CONTENT_SIZE]

    new_content = MirroredContent(
      base_url=base_url,
      original_address=mirrored_url,
      translated_address=translated_address,
      status=response.status_code,
      headers=adjusted_headers,
      data=content)
    if not memcache.add(key_name, new_content, time=EXPIRATION_DELTA_SECONDS):
      logging.error('memcache.add failed: key_name = "%s", '
                    'original_url = "%s"', key_name, mirrored_url)
      
    return new_content

################################################################################

class BaseHandler(webapp.RequestHandler):
  def direction(self, language):
      rtl = ['ar', 'fa', 'he', 'ur']
      if language in rtl:
          return 'RTL'
      else:
          return 'LTR'
  @property
  def language(self):
      if not hasattr(self, "_language"):
          self._language = 'en'
          user = self.current_user
          if not user:
              try:
                  locales = string.split(self.request.headers['Accept-Language'],',')
              except:
                  locales = 'en-us'
              langloc = string.split(locales[0],'-')
              if len(langloc[0]) > 1:
                  self._language = langloc[0]
          else:
              try:
                  locale = user.locale
                  langloc = string.split(locale, '_')
                  if len(langloc[0]) > 1:
                      self._language = langloc[0]
              except:
                  pass
      return self._language
  @property
  def current_user(self):
    if not hasattr(self, "_current_user"):
        self._current_user = None
        cookie = facebook.get_user_from_cookie(
            self.request.cookies, Settings.get('facebook_app_id'), Settings.get('facebook_app_secret'))
        if cookie:
            # Store a local instance of the user data so we don't need
            # a round-trip to Facebook on every request
            user = User.get_by_key_name(cookie["uid"])
            if not user:
                location = geolocate(self.request.remote_addr)
                localelist = string.split(self.request.headers['Accept-Language'],',')
                locales = list()
                for l in localelist:
                    langloc = string.split(l, ';')
                    locales.append(langloc[0])
                if location is not None:
                    city = location.get('city','')
                    country = location.get('country','')
                    try:
                        latitude = float(location.get('latitude',''))
                        longitude = float(location.get('longitude',''))
                    except:
                        latitude = None
                        longitude = None
                graph = facebook.GraphAPI(cookie["access_token"])
                profile = graph.get_object("me")
                if latitude is not None:
                    user = User(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                gender=profile['gender'],
                                city=city,
                                country=country,
                                latitude=latitude,
                                longitude=longitude,
                                locale = profile["locale"],
                                locales = locales,
                                profile_url=profile["link"],
                                access_token=cookie["access_token"])
                else:
                    user = User(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                gender=profile['gender'],
                                city=city,
                                country=country,
                                locale = profile["locale"],
                                locales = locales,
                                profile_url=profile["link"],
                                access_token=cookie["access_token"])
                user.put()
                p=dict()
                p['name']=profile['name']
                p['city']=city
                p['country']=country
                p['locale']=profile['locale']
                taskqueue.add(url='/wwl/userstatsworker', queue_name='counter', params=p)
            elif user.access_token != cookie["access_token"]:
                user.access_token = cookie["access_token"]
                user.put()
            self._current_user = user
    return self._current_user
  def get_relative_url(self):
    slash = self.request.url.find("/", len(self.request.scheme + "://"))
    if slash == -1:
      return "/"
    return self.request.url[slash:]


class HomeHandler(BaseHandler):
  def get(self):
    # Handle the input form to redirect the user to a relative url
    form_url = self.request.get("url")
    if form_url:
      # Accept URLs that still have a leading 'http://'
      inputted_url = urllib.unquote(form_url)
      if inputted_url.startswith(HTTP_PREFIX):
        inputted_url = inputted_url[len(HTTP_PREFIX):]
      return self.redirect("/" + inputted_url)

    latest_urls = memcache.get('latest_urls')
    if latest_urls is None:
      latest_urls = EntryPoint.gql("ORDER BY last_updated DESC").fetch(25)

      # Generate a display address that truncates the URL, adds an ellipsis.
      # This is never actually saved in the Datastore.
      for entry_point in latest_urls:
        entry_point.display_address = \
          entry_point.translated_address[:MAX_URL_DISPLAY_LENGTH]
        if len(entry_point.display_address) == MAX_URL_DISPLAY_LENGTH:
          entry_point.display_address += '...'

      if not memcache.add('latest_urls', latest_urls,
                          time=EXPIRATION_RECENT_URLS_SECONDS):
        logging.error('memcache.add failed: latest_urls')

    # Do this dictionary construction here, to decouple presentation from
    # how we store data.
    secure_url = None
    if self.request.scheme == "http":
      secure_url = "https://mirrorrr.appspot.com"
    context = {
      "latest_urls": latest_urls,
      "secure_url": secure_url,
    }
    self.response.out.write(template.render("main.html", context))
    
def squeaky_clean(html):
    clean_html = cleaner.clean_html(html)
    # now remove the useless empty tags
    root = fromstring(clean_html)
    context = etree.iterwalk(root) # just the end tag event
    for action, elem in context:
        clean_text = elem.text and elem.text.strip(' \t\r\n')
        if elem.tag in nonempty_tags and \
        not (len(elem) or clean_text): # no children nor text
            elem.getparent().remove(elem)
            continue
        elem.text = clean_text # if you want
        # and if you also wanna remove some attrs:
        for badattr in remove_attrs:
            if elem.attrib.has_key(badattr):
                del elem.attrib[badattr]
    return tostring(root)

class MirrorHandler(BaseHandler):
  def get(self, base_url):
    #if not self.current_user:
    #  self.error(401)
    #  self.response.out.write('Facebook login required to use this service.')
    #  return
    if base_url[0] == 'x':
      base_url = DerMundoProjects.geturl(base_url[1:20])
    
    assert base_url
    
    # Log the user-agent and referrer, to see who is linking to us.
    logging.debug('User-Agent = "%s", Referrer = "%s"',
                  self.request.user_agent,
                  self.request.referer)
    logging.debug('Base_url = "%s", url = "%s"', base_url, self.request.url)

    translated_address = self.get_relative_url()[1:]  # remove leading /
    mirrored_url = HTTP_PREFIX + translated_address

    # Use sha256 hash instead of mirrored url for the key name, since key
    # names can only be 500 bytes in length; URLs may be up to 2KB.
    key_name = get_url_key_name(mirrored_url)
    logging.info("Handling request for '%s' = '%s'", mirrored_url, key_name)

    content = MirroredContent.get_by_key_name(key_name)
    cache_miss = False
    if content is None:
      logging.debug("Cache miss")
      cache_miss = True
      content = MirroredContent.fetch_and_store(key_name, base_url,
                                                translated_address,
                                                mirrored_url)
    if content is None:
      return self.error(404)

    # Store the entry point down here, once we know the request is good and
    # there has been a cache miss (i.e., the page expired). If the referrer
    # wasn't local, or it was '/', then this is an entry point.
    if (cache_miss and
        'Googlebot' not in self.request.user_agent and
        'Slurp' not in self.request.user_agent and
        (not self.request.referer.startswith(self.request.host_url) or
         self.request.referer == self.request.host_url + "/")):
      # Ignore favicons as entry points; they're a common browser fetch on
      # every request for a new site that we need to special case them here.
      if not self.request.url.endswith("favicon.ico"):
        logging.info("Inserting new entry point")
        entry_point = EntryPoint(
          key_name=key_name,
          translated_address=translated_address)
        try:
          entry_point.put()
        except (db.Error, apiproxy_errors.Error):
          logging.exception("Could not insert EntryPoint")
    
    for key, value in content.headers.iteritems():
      self.response.headers[key] = value
    if not DEBUG:
      self.response.headers['cache-control'] = \
        'max-age=%d' % EXPIRATION_DELTA_SECONDS
      
    soup = BeautifulSoup(content.data)
    to_extract = soup.findAll('script')
    for item in to_extract:
      item.extract()
    content.data = soup.renderContents(encoding='utf-8')

    
    #content.data = clean_html(content.data)
    
    #content.data = string.replace(content.data, '\'<script', '<!--')
    #content.data = string.replace(content.data, '\"<script', '<!--')
    #content.data = string.replace(content.data, '<script', '<!--')
    #content.data = string.replace(content.data, '</script>', ' -->')
    content.data = string.replace(content.data, 'src=/', 'src=http://')
    content.data = string.replace(content.data, 'src="/', 'src="http://')
    if self.current_user:
      meta = '<meta name=facebookid content="' + self.current_user.id + '">'
      meta = meta + '<meta name=facebookname content="' + self.current_user.name + '">'
    else:
      meta = '<meta name=facebookid content=""><meta name=facebookname content="">'
    #if self.current_user:
    try:
      content.data = string.replace(content.data, '</head>', meta + javascript_header + '</head>')
    except:
      try:
        content.data = string.replace(content.data, '</head>' + db.Text(meta + javascript_header) + '</head>')
      except:
        try:
          content.data = string.replace(content.data, '</head>', javascript_header + '</head>')
        except:
          pass
    #else:
    #  content.data = db.Text(content.data, encoding='utf_8')
    #  results = Translation.getbyurl(base_url, self.language)
    #  for r in results:
    #    if len(r.tt) > 3: content.data = string.replace(content.data, r.st, r.tt)
    content.data = string.replace(content.data, 'SOURCE_URL',base_url)
    content.data = string.replace(content.data, 'fb:', 'fb_:')
    self.response.out.write(content.data)
    
class OfflineHandler(webapp.RequestHandler):
  def get(self, path):
    self.error(404)
    self.response.out.write("The translation proxy server is currently offline, ")
    self.response.out.write("and will be available when we begin our beta test in a few days.")


app = webapp.WSGIApplication([
  (r"/", HomeHandler),
#  (r"/main", HomeHandler),
#  (r"/([^/]+).*", OfflineHandler)
#  (r"/main", HomeHandler),
  (r"/([^/]+).*", MirrorHandler)
], debug=DEBUG)


def main():
  wsgiref.handlers.CGIHandler().run(app)


if __name__ == "__main__":
  main()

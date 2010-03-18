# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Multilingual Content Management System
Content Management System / Web Server (wwl.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module serves page and document requests, and is the primary module used to
render pages, blog posts, RSS feeds, etc. 

Copyright (c) 1998-2009, Worldwide Lexicon Inc, Brian S McConnell. 
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer. Web services
      derived from this software must provide a link to www.worldwidelexicon.org
      with a "translations powered by the Worldwide Lexicon" caption (or
      appropriate translation.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of the Worldwide Lexicon Inc/Worldwide Lexicon Project
      nor the names of its contributors may be used to endorse or promote
      products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
# import standard Python libraries
import urllib
import string
import sys
import demjson
import md5
import datetime
import pydoc
import codecs
import types
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
# import Worldwide Lexicon modules
import feedparser
from database import CSS
from database import Images
from database import languages
from database import Objects
from database import Translation
from database import Websites
from geo import geo
from webappcookie import Cookies

# Define convenience functions

def smart_str(s, encoding='utf-8', errors='ignore', from_encoding='utf-8'):
    if type(s) in (int, long, float, types.NoneType):
        return str(s)
    elif type(s) is str:
        if encoding != from_encoding:
            return s.decode(from_encoding, errors).encode(encoding, errors)
        else:
            return s
    elif type(s) is unicode:
        return s.encode(encoding, errors)
    elif hasattr(s, '__str__'):
        return smart_str(str(s), encoding, errors, from_encoding)
    elif hasattr(s, '__unicode__'):
        return smart_str(unicode(s), encoding, errors, from_encoding)
    else:
        return smart_str(str(s), encoding, errors, from_encoding)

def tx(sl, tl, st, split = 'n'):
    """
    tx()
    
    This convenience function fetches a human or machine translation for a text
    and displays it in a bilingual format.
    """
    tt = Translation.lucky(sl=sl, tl=tl, st=st)
    if sl == tl or len(tl) < 2:
        return st
    if len(tt) > 0:
        if split == 'n':
            return tt
        else:
            return st + ' / ' + tt
    else:
        return st

# Define default settings

encoding = 'utf-8'

default_language = 'en'

default_title = 'Welcome to the Worldwide Lexicon'

default_css = 'blueprint'

# Alex Tolley's Javascript translation widget
#javascript_header_init = '<script src="/ajax/com.wwl.Translator.nocache.js"></script>'
javascript_header_init = '<script src="/translator/translator.nocache.js"></script>'
javascript_global_div = '<div id="wwlapi" sl="en" dermundo="http://worldwidelexicon.appspot.com/" allow_machine="y" allow_anonymous="y" allow_unscored="y" minimum_score="0"></div>'

# Google Analytics Header
google_analytics_header = '<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");\
document.write(unescape("%3Cscript src=\'\" + gaJsHost + \"google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));\
</script>\
<script type="text/javascript">\
try {\
var pageTracker = _gat._getTracker("api_key");\
pageTracker._trackPageview();\
} catch(err) {}</script>'

# Define default settings for Blueprint CSS framework, included with this package as the default style sheet

blueprint_header='<link rel="stylesheet" href="/blueprint_overrides.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/screen.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/print.css" type="text/css" media="print">\
            <link rel="stylesheet" href="/blueprint/plugins/fancy-type/screen.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/plugins/link-icons/screen.css" type="text/css" media="screen, projection">\
            <!--[if IE]><link rel="stylesheet" href="/blueprint-css/blueprint/ie.css" type="text/css" media="screen, projection"><![endif]-->'

blueprint_container = '<div class="container"><hr class="space">'

blueprint_wide = '<div class="span-15 prepend-1 colborder">'

blueprint_sidebar = '<div class="span-7 last">'

# standard footer and source code attribution, do not modify or hide
standard_footer = 'Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2009 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  WWL multilingual CMS and translation memory is open source software published \
                  under a BSD style license.'

translation_server = 'http://worldwidelexicon.appspot.com'

class WebServer(webapp.RequestHandler):
    """
    
    This web service handles most requests to render and display pages. It
    performs the following tasks:
    
    1. geolocates the user by IP address (MaxMind account required)
    2. identifies user (session cookie, if logged in)
    3. generates HTML header, identifies required CSS style sheet and references it
    4. loads and displays the standard page objects
        * masthead
        * menu (links to sections, if not present, generates a boilerplate menu)
        * login/register
        * language selector
        * body
        * about
        * sidebar
        * footer
        * analytics
        
    The server assumes that the CSS stylesheet associated with the page follows a
    fairly standard layout, and has the following elements:
    
    * header
    * masthead
    * body
    * sidebar (if not present, the sidebar elements are not shown)
    * about (if not present, the about section is not shown)
    * footer
    
    When rendering a page element that has a CSS element associated with it, it
    will check to see if the CSS stylesheet has a div id or class associated with
    that field. If yes, it will display the element. If not, it will not display the
    element. 
    
    """
    sl = ''
    title = ''
    meta = ''
    keywords = ''
    css = ''
    cssloaded = False
    cssname = default_css
    location = dict()
    def get(self,p1='', p2='', p3=''):
        # get HTTP headers
        headers = self.request.headers
        remote_addr = self.request.remote_addr
        # get cookies
        cookies = Cookies(self)
        try:
            language = cookies['tl']
        except:
            language = ''
        if len(p3) > 0:
            website = p1
            language = p2
            page = p3
        else:
            website = p1
            page = p2
        if p2 == 'search':
            q = self.request.get('q')
        # if website is a short name, resolve domain name mapping
        website = Websites.resolve(website)
        if len(website) > 0 and website != 'create':
            title = smart_str('<h1>' + Websites.parm(website,'title') + '</h1>')
            description = smart_str(Websites.parm(website,'description'))
        else:
            title = smart_str('<h1>Create Website</h1>')
            description = ''
        if len(website) < 1:
            sitemap = True
        else:
            sitemap = False
        # geolocate user via Maxmind (API key required)
        location = geo.get(remote_addr, website=website)
        # load main page content and metadata from Objects data store
        body = Objects.get(website, page, language)
        if page == 'create':
            reserved = True
        elif website == 'create':
            reserved = True
        elif page == 'news':
            reserved = True
        elif page == 'rss':
            reserved = True
        elif page == 'search':
            reserved = True
        elif page == 'twitter':
            reserved = True
        elif sitemap:
            reserved = True
        else:
            reserved = False
        if type(body) is dict and not reserved:
            title = smart_str('<h1>' + body.get('title', '') + '</h1>')
            description = smart_str(body.get('descrtiption',''))
        else:
            title = smart_str('<h1>' + page + '</h1>')
            description = ''
        # get CSS stylesheet associated with page
        csstext = CSS.get(page, language)
        if len(csstext) > 0:
            self.css = csstext
            self.cssloaded = True
        # generate HTML header and link to CSS stylesheet
        self.header(language,body,page)
        # geolocate user based on IP address
        location = geo.get(self.request.remote_addr)
        # fetch and render title and masthead
        if not self.cssloaded:
            # use Blueprint CSS
            self.response.out.write(blueprint_container)
        # render title and masthead
        self.response.out.write('<table border=0 width=100%>')
        self.response.out.write('<tr><td width=70%>')
        self.render(title, language, divid='title')
        self.response.out.write('</td><td width=30%>')
        self.response.out.write('<table border=0><tr><td colspan=3>')
        self.selectlanguage()
        self.response.out.write('</td></tr></table>')
        self.response.out.write('</table>')
        self.render(Objects.get(website, 'masthead', language), language, divid='masthead')
        # render main page body
        homepage = False
        if not self.cssloaded:
            self.response.out.write(blueprint_wide)
        # fetch and render navbar
        if not self.cssloaded:
            self.response.out.write('<hr>')
        self.navbar(website)
        if page == 'news':
            self.news(website=website,language=language)
        elif p1 == 'create':
            self.create()
        elif sitemap:
            self.sitemap()
        elif p2 == 'search':
            self.news(website=website, language=language, q=q)
        elif page == '' or page == 'home' or page == 'index':
            self.homepage(website,language)
            homepage = True
        else:
            self.render(body, language, divid='body')
        if not self.cssloaded:
            self.response.out.write('</div>')
        # start sidebar (if multi-column layout)
        if not self.cssloaded:
            self.response.out.write(blueprint_sidebar)
        # fetch and render About section
        if homepage:
            self.search(website=website)
            self.twitter(website=website)
            self.news(website=website, language=language, verbose=False, limit=6)
            self.render(Objects.get(website, 'about', language), language, divid='about')
        else:
            self.search(website=website)
            self.twitter(website=website)
            if page != 'news':
                self.news(website=website,language=language, verbose=False,limit=6)
        # close sidebar
        if not self.cssloaded:
            self.response.out.write('</div><hr>')
        # render footer, copyright, etc
        self.footer(website, language)
        if not self.cssloaded:
            self.response.out.write('</div>')
            
    def create(self):
        referrer = self.request.referrer
        # check to see if the system allows the public to create a website
        # if yes, proceed. if no, redirect to previous page
        self.response.out.write('<h3>Create a New Website or Blog</h3>')
        self.response.out.write('<table><form action=/newsite method=post>')
        self.response.out.write('<tr><td>Title</td><td><input type=text name=title>')
        self.response.out.write('<tr><td>Hostname (yoursite.wordpress.com)</td><td><input type=text name=host></td></tr>')
        self.response.out.write('<tr><td>Primary Language</td><td><select name=language>')
        self.response.out.write(languages.select())
        self.response.out.write('</select></td></tr>')
        self.response.out.write('<tr><td colspan=2>Description<br><textarea name=description></textarea></td></tr>')
        self.response.out.write('<tr><td colspan=2><input type=submit value="Create Website"></td></tr>')
        self.response.out.write('</form></table>')
        
    def header(self, language, content, page='', website=''):
        head_title = 'Welcome'
        head_css = 'blueprint'
        if len(language) < 1:
            language = default_language
        if type(content) is dict:
            # if page content is known, override standard header elements
            head_title = content.get('title', head_title)
            head_css = content.get('css', head_css)
        # generate HTML header, link to CSS stylesheet
        self.response.headers['Content-Type']='text/html'
        self.response.out.write('<head><title>' + smart_str(head_title) + '</title>')
        self.response.out.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></meta>')
        if len(website) > 0:
            googleanalyticsapi = Websites.parm(website, 'googleanalytics')
            if len(googleanalyticsapi) > 0:
                analytics_header = string.replace(google_analytics_header, 'api-key', googleanalyticsapi)
                self.response.out.write(analytics_header)
        self.response.out.write(javascript_header_init)
        self.title = head_title
        if not self.cssloaded:
            self.response.out.write(blueprint_header)
        else:
            self.response.out.write('<link rel="stylesheet" href="/css/' + head_css + '" type="text/css">')
        self.response.out.write('</head>')
        self.response.out.write(javascript_global_div)

    def homepage(self, website, language):
        text = memcache.get('homepage|website=' + website + '|language=' + language)
        if text is None:
            text = smart_str(Objects.query(website, published=True, blog=True, news=False))
            if text is None:
                text = ''
            else:
                memcache.set('homepage|website=' + website + '|language=' + language, text, 240)
        self.response.out.write(text)
        
    def footer(self, website, language):
        self.response.out.write('<div id="footer"><font size=-2>')
        self.render(Objects.get(website, 'footer', language), language)
        self.response.out.write(standard_footer)
        self.response.out.write('</font></div>')
        
    def navbar(self, website, language=''):
        nb = memcache.get('navbar|website=' + website)
        if nb is not None:
            self.response.out.write(nb)
        else:
            odb = db.Query(Objects)
            odb.filter('website = ', website)
            odb.filter('news = ', False)
            odb.filter('published = ', True)
            odb.filter('blog = ', False)
            results = odb.fetch(limit=10)
            nblist = list()
            nbdict = dict()
            for r in results:
                if r.name not in nblist:
                    nblist.append(r.title)
                    nbdict[r.title]=r.guid
            nblist.sort()
            nb = '<h2>'
            for n in nblist:
                nb = nb + '<a href=/' + website + '/' + nbdict[n] + '>' + n + '</a>  '
            nb = nb + '</h2><hr>'
            #memcache.set('navbar|website=' + website, nb, 300)
            self.response.out.write(nb)
    def news(self, language='', p1='', website='', verbose=True, limit=20, q = ''):
        self.response.out.write('<h3><a href=/' + website + '/news>Todays News</a></h3>')
        text = smart_str(Objects.query(website, news=True, published=True, verbose=verbose, limit=limit, q=q))
        self.response.out.write(text)
    
    def render(self, object, language='', divid='', classid=''):
        if type(object) is dict:
            text = object.get('content', '')
            sl = object.get('sl','')
        else:
            sl = 'en'
            if object is not None:
                try:
                    text = str(object)
                except:
                    text = ''
            else:
                text = ''
        text = string.replace(text, '<br>', '<p>')
        text = string.replace(text, '</p>', '<p>')
        text = string.replace(text, '<div>', '')
        text = string.replace(text, '</div>', '')
        if type(object) is dict:
            if len(object.get('divid','')) > 0:
                divid = object.get('divid', '')
            if len(object.get('divclass', '')) > 0:
                divclass = object.get('divclass','')
        divopen = ''
        divclose = ''
        if len(divid) > 0:
            if self.cssloaded:
                divopen = '<div id="' + divid + '">'
                divclose = '</div>'
        if len(classid) > 0:
            if self.cssloaded:
                divtext = '<div class="' + divclass + '">'
                divclose = '</div>'
        if len(text) > 0:
            if language != sl:    
                texts = string.split(text, '<p>')
                self.response.out.write(divopen)
                for t in texts:
                    if len(t) > 10 and type(object) is dict:
                        self.response.out.write('<div wwlapi="tr">' + smart_str(t) + '</div>')
                    else:
                        self.response.out.write(t)
                self.response.out.write(divclose)
            else:
                self.response.out.write(divopen)
                self.response.out.write(text)
                self.response.out.write(divclose)
                
    def search(self, website=''):
        self.response.out.write('<h3>Search</h3>')
        self.response.out.write('<form action=/' + website + '/search method=get>')
        self.response.out.write('<input type=text name=q size=25>')
        self.response.out.write('<input type=image src=/image/search.png>')
        self.response.out.write('</form>')
        self.response.out.write('<font size=-2>Tags: ')
        tagcloud = memcache.get('tags|website=' + website)
        if tagcloud is not None:
            self.response.out.write(tagcloud)
        else:
            odb = db.Query(Objects)
            odb.filter('website = ', website)
            odb.order('-created')
            results = odb.fetch(limit=100)
            tagcloud = ''
            taglist = list()
            for r in results:
                content = codecs.encode(r.content, encoding)
                tags = r.tags
                for t in tags:
                    if t not in taglist and len(content) > 0:
                        taglist.append(t)
            ctr = 0
            for t in taglist:
                ctr = ctr + 1
                if ctr < 25:
                    tagcloud = tagcloud + ' <a href=/' + website + '/search?q=' + t + '>' + t + '</a>'
            memcache.set('tags|website=' + website, tagcloud, 500)
            self.response.out.write(tagcloud)
        self.response.out.write('</font><br><br>')
            
    def selectlanguage(self):
        cookies = Cookies(self)
        try:
            tl = cookies['tl']
        except:
            tl = ''
            # add code to check browser prefs here
        self.response.out.write('<table><tr><td><form action=/language method=post>')
        self.response.out.write('<select name=tl>')
        text = languages.select(selected=tl)
        self.response.out.write(text)
        self.response.out.write('</select>')
        self.response.out.write('</td><td><input type=submit value=OK></td></tr></form></table>')
        
    def sitemap(self):
        wdb = db.Query(Websites)
        wdb.order('-created')
        results = wdb.fetch(limit = 20)
        for r in results:
            self.response.out.write('<h3><a href=/' + r.host + '/>' + r.title + '</a></h3>')
            self.response.out.write('<em wwlapi="tr">' + r.description + '</em>')
    
    def trans(self, sl, tl, st):
        return st
        t = memcache.get('trans|sl=' + sl + '|tl=' + tl + '|st=' + st)
        if t is not None:
            return t
        else:
            url = translation_server + '/' + sl + '/' + tl + '/?st=' + urllib.quote_plus(st)
            response = urlfetch.fetch(url = url)
            if response.status_code == 200:
                t = codecs.encode(response.content, encoding)
                memcache.set('trans|sl=' + sl + '|tl=' + tl + '|st=' + st, t, 300)
                return t
            else:
                return ''
    def twitter(self, website):
        t = memcache.get('twitter|website=' + website)
        if t is not None:
            self.response.out.write(t)
        else:
            t = ''
            twitter = Websites.parm(website, 'twitter')
            if twitter is not None:
                url = 'http://twitter.com/statuses/user_timeline/' + twitter + '.rss'
                try:
                    response = urlfetch.fetch(url=url)
                    if response.status_code == 200:
                        text = response.content
                        r = feedparser.parse(text)
                        entries = r.entries
                        ctr = 0
                        t = t + '<h3>Twitter</h3>'
                        for e in entries:
                            ctr = ctr + 1
                            if len(e.title) > 0:
                                if ctr < 4:
                                    t = t + '<h4 wwlapi="tr">' + e.title + '</h4>'
                except:
                    t = ''
            if len(t) > 0:
                memcache.set('twitter|website=' + website, t, 600)
            self.response.out.write(t)
            
class SetLanguage(webapp.RequestHandler):
    def get(self):
        cookies = Cookies(self)
        try:
            tl = cookies['tl']
        except:
            tl = ''
            # add code to check browser prefs here
        self.response.out.write('<table><tr><td><form action=/language method=post>')
        self.response.out.write('<select name=tl>')
        text = languages.select()
        self.response.out.write('</select>')
        self.response.out.write('</td><td><input type=submit value=OK></td></tr></form></table>')
    def post(self):
        tl = self.request.get('tl')
        referrer = self.request.referrer
        if len(tl) == 2 or len(tl) == 3:
            cookies = Cookies(self)
            cookies['tl']=tl
        self.redirect(referrer)
        
class CreateWebsite(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        referrer = self.request.referrer
        host = self.request.get('host')
        title = self.request.get('title')
        description = self.request.get('description')
        language = self.request.get('language')
        sourcelanguages = list()
        if len(language) > 0:
            sourcelanguages.append(language)
        result = Websites.create(host, title, description, sourcelanguages=sourcelanguages)
        if result:
            self.redirect('/' + host)
        else:
            self.redirect(referrer)

application = webapp.WSGIApplication([(r'/(.*)/(.*)/(.*)', WebServer),
                                     (r'/(.*)/(.*)', WebServer),
                                     ('/language', SetLanguage),
                                     ('/newsite', CreateWebsite),
                                     (r'/(.*)', WebServer),
                                     ('/', WebServer)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
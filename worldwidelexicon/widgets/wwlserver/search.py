# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Translation Search Engine (search.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module implements a search engine that enables users to see which sites and URLs
are being translated most actively, to do keyword searches for translations and the
documents they are related to. 

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
import sgmllib
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
import feedfinder
from database import languages
from database import Groups
from database import Translation
from database import Search
from database import Users
from database import Websites
from geo import geo
from geo import GeoDB
from webappcookie import Cookies
from mt import MTWrapper
from deeppickle import DeepPickle
from www import www
from config import Config

# Define convenience functions

class MyParser(sgmllib.SGMLParser):
    """
    This class implements a basic HTML parser that is used to extract
    title, description and keywords from a page's HTML header. 
    """
    inside_title = False
    title = ''
    inside_meta = False
    keywords = ''
    description = ''

    def start_title(self, attrs):
        self.inside_title = True

    def end_title(self):
        self.inside_title = False

    def start_meta(self, attrs):
        self.inside_meta = True
        name = attrs[0]
        content = attrs[1]
        if string.lower(name[1]) == 'description':
            self.description = content[1]
        if string.lower(name[1]) == 'keywords':
            self.keywords = content[1]

    def end_meta(self, attrs):
        self.inside_meta = False

    def handle_data(self, data):
        if self.inside_title and data:
            self.title = self.title + data + ' '

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

def clean(text):
    if text is not None:
        try:
            utext = text.encode('utf-8')
        except:
            try:
                utext = text.encode('iso-8859-1')
            except:
                try:
                    utext = text.encode('ascii')
                except:
                    utext = text
        try:
            text = utext.decode('utf-8')
        except:
            text = utext
        return text
    else:
        return ''

def tx(sl, tl, st, split = 'n'):
    """
    tx()
    
    This convenience function fetches a human or machine translation for a text
    and displays it in a bilingual format.
    """
    tt = Translation.lucky(sl=sl, tl=tl, st=st, domain='www.worldwidelexicon.org', lsp='speaklike', lspusername=Config.speaklike_username, lsppw=Config.speaklike_pw)
    if sl == tl or len(tl) < 2:
        return st
    elif len(tt) > 0:
        return tt
    else:
        return st

# Define default settings

encoding = 'utf-8'

default_language = 'en'

default_title = 'Welcome to the Worldwide Lexicon'

default_css = 'blueprint'

# Alex Tolley's Javascript translation widget
javascript_header_init = '<script src="/ajax/com.wwl.Translator.nocache.js"></script>'
#javascript_header_init = '<script src="/translator/translator.nocache.js"></script>'
javascript_global_div = '<div id="wwlapi" sl="en" dermundo="http://worldwidelexicon.appspot.com/" allow_machine="y" allow_anonymous="y" allow_unscored="y" minimum_score="0"></div>'

# Google Analytics Header
google_analytics_header = '<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");\
document.write(unescape("%3Cscript src=\'\" + gaJsHost + \"google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));\
</script>\
<script type="text/javascript">\
try {\
var pageTracker = _gat._getTracker("UA-7294247-1");\
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
                  under a BSD style license. Contact: bsmcconnell on skype or gmail.'

translation_server = 'http://worldwidelexicon.appspot.com'

class WebServer(webapp.RequestHandler):
    """
    
    This web service handles most requests to render and display pages. It
    performs the following tasks:
    
    1. geolocates the user by IP address
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
    usercities = list()
    usertl = list()
    usersl = list()
    usertopsites = list()
    usertranslations = 0
    usertwords = 0
    useravgscore = None
    usersupvotes = 0
    userdownvotes = 0
    userblockedvotes = 0
    
    def get(self,p1='', p2='', p3=''):
        # get HTTP headers
        username = ''
        domain = ''
        url = self.request.get('url')
        add = self.request.get('add')
        if p1 == 'profiles':
            username = p2
        elif p1 == 'rss':
            domain = p2
        elif p1 == 'reader':
            domain = p2
        elif p1 == 'channel':
            domain = p2
        elif string.count(p1, '.') > 0:
            domain = p1
        else:
            pass
        headers = self.request.headers
        lang = headers.get('Accept-Language', '')
        remote_addr = self.request.remote_addr
        q = self.request.get('q')
        # get cookies
        cookies = Cookies(self)
        try:
            language = cookies['tl']
            if len(language) < 1 or len(language) > 3:
                language = 'en'
                cookies['tl'] = language
        except:
            try:
                language = languages.auto(lang)
                if len(language) == 2 or len(language) == 3:
                    cookies['tl']=language
                else:
                    cookies['tl']='en'
            except:
                language = 'en'
        # geolocate user via Maxmind (API key required)
        location = geo.get(remote_addr, website='www.dermundo.com')
        # generate HTML header and link to CSS stylesheet
        self.header(language)
        # geolocate user based on IP address
        location = geo.get(self.request.remote_addr)
        # fetch and render title and masthead
        self.response.out.write(blueprint_container)
        # render title and masthead
        prompt_about = 'About WWL'
        prompt_help = 'Help'
        prompt_groups = 'Groups'
        prompt_news = 'News'
        prompt_publishers = 'For Publishers'
        prompt_api = 'API'
        prompt_developers = 'Software Developers'
        prompt_donate = 'Donate'
        prompt_essay = 'Essay : The End of the Language Barrier'
        prompt_services = 'Professional Services'
        #prompt_subtitle = 'Debug: Accept-Language=' + lang + ' language=' + language
        mt = MTWrapper()
        if language != 'en' and len(language) > 1:
            prompt_about = mt.getTranslation('en', language, prompt_about)
            prompt_help = mt.getTranslation('en', language, prompt_help)
            prompt_news = mt.getTranslation('en', language, prompt_news)
            prompt_groups = mt.getTranslation('en', language, prompt_groups)
            prompt_publishers = mt.getTranslation('en', language, prompt_publishers)
            prompt_donate = mt.getTranslation('en', language, prompt_donate)
            prompt_essay = tx('en', language, prompt_essay)
            prompt_developers = tx('en', language, prompt_developers)
            prompt_services = mt.getTranslation('en', language, prompt_services)
        self.response.out.write('<table border=0 width=100%>')
        self.response.out.write('<tr><td width=70%>')
        self.response.out.write('<h1><a href=/>Der Mundo</a></h1><hr>')
        self.response.out.write('<h4><a href=http://blog.worldwidelexicon.org/?page_id=2>' + prompt_about + '</a>')
        self.response.out.write(' | <a href=http://blog.worldwidelexicon.org/?page_id=26>' + prompt_essay + '</a>')
        # self.response.out.write(' | <a href=http://blog.worldwidelexicon.org>' + prompt_help + '</a>')
        # self.response.out.write(' | ' + prompt_groups)
        # self.response.out.write(' | ' + prompt_news)
        # self.response.out.write(' | <a href=/s/donate.html>' + prompt_donate + '</a>')
        self.response.out.write(' | <a href=http://blog.worldwidelexicon.org/?page_id=29>' + prompt_publishers + '</a>')
        self.response.out.write(' | <a href=/api>' + prompt_api + '</a>')
        self.response.out.write(' | <a href=http://blog.worldwidelexicon.org/?page_id=12>' + prompt_developers + '</a>')
        # self.response.out.write(' | <a href=http://blog.worldwidelexicon.org>' + prompt_services+ '</a>')
        self.response.out.write('</h4>')
        self.response.out.write('<hr>')
        #self.response.out.write('<hr><h3>' + prompt_subtitle + '</h3><hr>')
        self.response.out.write('</td><td width=30%>')
        self.response.out.write('<table border=0><tr><td colspan=3>')
        self.selectlanguage(language)
        self.response.out.write('</td></tr></table>')
        self.response.out.write('</table>')
        # render main page body
        self.response.out.write(blueprint_wide)
        if p1 == 'p':
            self.page(language)
        elif p1 == 's':
            self.static(language, page=p2)
        elif p1 == 'group':
            if p2 == 'create':
                self.creategroup(language)
            else:
                self.group(p2, language)
        elif p1 == 'reader':
            self.rss(p2, language)
        elif p1 == 'rss':
            self.rss(p2, language)
        elif len(url) > 0:
            self.profile(url, language)
        elif p1 == 'help':
            self.help(language)
        elif p1 == 'channel':
            self.feed(language, 'http://www2c.cdc.gov/podcasts/download.asp?f=252&af=x&t=3', limit=10)
        elif p1 == 'p':
            self.page(language)
        elif add == 'y':
            self.addsite(language)
        elif len(username) > 0:
            self.userprofile(username, language)
        else:
            self.search(q=q, language=language, domain=domain)
            self.static(language, 'featured.html')
            self.activegroups(language)
            self.activesites(language)
        self.response.out.write('</div>')
        # start sidebar (if multi-column layout)
        self.response.out.write(blueprint_sidebar)
        # fetch and render About section
        self.sidebar(language, q, username=username, domain=domain, page=p2)
        self.topsites(language)
        # close sidebar
        self.response.out.write('</div><hr>')
        # render footer, copyright, etc
        self.footer(language)
        self.response.out.write('</div>')
    def rss(self, url, language):
        url = feedfinder.feed(url)
        self.response.out.write('Feed is at : ' + str(url))
    def activesites(self, language):
        prompt_active_sites = 'Most Translated Websites'
        if language != 'en' and len(language) > 1:
            mt = MTWrapper()
            prompt_active_sites = mt.getTranslation('en', language, prompt_active_sites)
        sdb = db.Query(Search)
        sdb.order('-translations')
        results = sdb.fetch(limit=100)
        domains = list()
        if results is not None:
            for r in results:
                if r.domain not in domains:
                    domains.append(r.domain)
        txt = ''
        if len(domains) > 0:
            txt = '<h3>' + prompt_active_sites + '</h3>'
            txt = txt + '<font size=-1>'
            for d in domains:
                txt = txt + '<a href=/' + d + '>' + d + '</a>  '
            txt = txt + '</font><hr>'
        self.response.out.write(txt)
                
    def header(self, language):
        head_title = 'Der Mundo'
        head_css = 'blueprint'
        if len(language) < 1:
            language = default_language
        # generate HTML header, link to CSS stylesheet
        self.response.headers['Content-Type']='text/html'
        self.response.out.write('<head><title>' + smart_str(head_title) + '</title>')
        self.response.out.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></meta>')
        self.response.out.write(google_analytics_header)
#        self.response.out.write(javascript_header_init)
        self.title = head_title
        self.response.out.write(blueprint_header)
        self.response.out.write('</head>')
        self.response.out.write(javascript_global_div)
        
    def feed(self, language, url, limit = 5):
        if len(language) > 0 and len(url) > 0:
            if string.count(url, 'http://') < 1:
                url = 'http://' + url
            txt = memcache.get('rss|language=' + language + '|url=' + url)
            if txt is not None:
                self.response.out.write(txt)
            else:
                mt = MTWrapper()
                txt = ''
                response = urlfetch.fetch(url = url)
                if response.status_code == 200:
                    r = response.content
                else:
                    r = ''
                rss = feedparser.parse(r)
                entries = rss.entries
                if len(entries) > 0:
                    ctr = 0
                    for e in entries:
                        ctr = ctr + 1
                        if ctr < (limit + 1):
                            title = clean(e.title)
                            link = e.link
                            lt = string.split(string.replace(link, 'http://', ''), '/')
                            if len(lt) > 0:
                                domain = '(' + lt[0] + ') '
                            else:
                                domain = ''
                            if language != 'en':
                                ttitle = ' / ' + Translation.lucky('en', language, title) 
                            else:
                                ttitle = ''
                            txt = txt + '<h4><a href=' + link + '>' + domain + title + ttitle + '</a></h4>'
                            entry = clean(e.description)
                            if len(entry) > 0:
                                tentry = Translation.lucky('en', language, entry)
                                if len(tentry) > 400:
                                    tentry = tentry[0:400] + ' ... '
                                txt = txt + '<font size=-2>' + tentry + '</font><br><br>'
                memcache.set('rss|language=' + language + '|url=' + url,txt, 60)
                self.response.out.write(txt)
    def footer(self, language):
        self.response.out.write('<div id="footer"><font size=-2>')
        self.response.out.write(standard_footer)
        self.response.out.write('</font></div>')
        
    def creategroup(self, language):
        prompt_heading = 'Create A Group'
        prompt_instructions = 'Create a group where you and your friends can meet to discuss and translate your favorite websites.'
        prompt_title = 'Title'
        prompt_description = 'Description'
        prompt_create_group = 'Create Group'
        self.response.out.write('<h3>' + prompt_heading + '</h3>')
        self.response.out.write(prompt_instructions)
        self.response.out.write('<table><form action=/search method=post>')
        self.response.out.write('<input type=hidden name=action value=creategroup>')
        self.response.out.write('<tr><td>' + prompt_title + '</td><td><input type=text name=title></td></tr>')
        self.response.out.write('<tr><td colspan=2>' + prompt_description + '<br><textarea name=description></textarea></td></tr>')
        self.response.out.write('<tr><td colspan=2><input type=submit value="' + prompt_create_group + '"></td></tr>')
        self.response.out.write('</form></table>')
        
    def help(self, language, interface='firefox'):
        self.redirect('/s/help-firefox.html')
        
    def profile(self, url='', language=''):
        prompt_site_added = 'Website Added Successfully'
        prompt_title = 'Title'
        prompt_language = 'Language'
        prompt_description = 'Description'
        prompt_keywords = 'Keywords'
        if language != 'en' and len(language) > 1:
            mt = MTWrapper()
            prompt_site_added = mt.getTranslation('en', language, prompt_site_added)
            prompt_title = mt.getTranslation('en', language, prompt_title)
            prompt_language = mt.getTranslation('en', language, prompt_language)
            prompt_description = mt.getTranslation('en', language, prompt_description)
            prompt_keywords = mt.getTranslation('en', language, prompt_keywords)
        if len(url) > 0:
            sdb = db.Query(Search)
            sdb.filter('url = ', url)
            item = sdb.get()
            if item is not None:
                title = item.title
                description = clean(item.description)
                keywords = item.keywords
                language = item.sl
                keytext = ''
                if len(keywords) > 0:
                    for k in keywords:
                        keytext = keytext + ' ' + k
                self.response.out.write('<table>')
                self.response.out.write('<tr><td>' + prompt_title + '</td><td>' + title + '</td></tr>')
                self.response.out.write('<tr><td>' + prompt_language + '</td><td>' + languages.getlist(item.sl) + '</td></tr>')
                self.response.out.write('<tr><td colspan=2>' + prompt_description + '<br>' + description + '</td></tr>')
                self.response.out.write('<tr><td colspan=2>' + prompt_keywords + '<br>' + keytext + '</td></tr>')
                self.response.out.write('</table>')
                self.response.out.write('<a href=/search>Back to search page</a>')
    
    def group(self, group='', language = ''):
        if len(group) > 0:
            gdb = db.Query(Groups)
            gdb.filter('name = ', group)
            item = gdb.get()
            if item is not None:
                title = item.title
                description = item.description
                self.response.out.write('<h2>' + title + '</h2>')
                self.response.out.write(description)
                self.response.out.write('<hr>')
                self.response.out.write('<h3>Recently Translated Articles</h3>')
                self.response.out.write('...')
                self.response.out.write('<h3>Discussion</h3>')
                self.response.out.write('...')
            else:
                self.creategroup(language)
        else:
            self.creategroup(language)
            
    def guide(self, language):
        return
        tags = ['art', 'news', 'travel']
        tx = dict()
        if language != 'en':
            txt = memcache.get('txtags|language=' + language)
            if txt is None:
                tx = dict()
                ttags = list()
                mt = MTWrapper()
                for t in tags:
                    tt = mt.getTranslation('en', language, t)
                    if len(tt) > 0:
                        tx[tt] = t
                        ttags.append(tt)
                txt = '<font size=-1>'
                txk = tx.keys()
                txk.sort()
                for t in txk:
                    txt = txt + '<a href=/s/' + tx.get(t, '') + '.html>' + t + '</a> '
                txt = txt + '</font><br><br>'
                memcache.set('txtags|language=' + language, txt, 300)
                self.response.out.write(txt)
        else:
            txt = '<font size=-1>'
            for t in tags:
                txt = txt + '<a href=/s/' + t + '.html>' + t + '</a> '
            txt = txt + '</font><br><br>'
            self.response.out.write(txt)
        
    def activegroups(self, language, q=''):
        return
        prompt_active_groups = 'New Groups'
        if language != 'en' and len(language) > 1:
            prompt_active_groups = mt.getTranslation('en', language, prompt_active_groups)
        gdb = db.Query(Groups)
        gdb.order('-posts')
        results = gdb.fetch(limit=10)
        if results is not None:
            self.response.out.write('<h3>'+ prompt_active_groups + '</h3>')
            for r in results:
                if len(r.title) > 0:
                    self.response.out.write('<h4><a href=/group/' + r.name + '>' + r.title + '</a></h4>')
                    self.response.out.write('<em>' + r.description + '</em>')
            self.response.out.write('<hr>')

    def search(self, q ='', language='', domain=''):
        if language == '':
            language = 'en'
        if len(q) > 0:
            q = clean(q)
        prompt_add_website = 'Add Website'
        prompt_create_group = 'Create A New Group'
        prompt_top_sites_in = 'Top Websites (' + languages.getlist(language) + ')'
        prompt_top_sites_translated = 'Translated To ' + languages.getlist(language)
        if language != 'en' and len(language) > 1:
            mt = MTWrapper()
            prompt_add_website = mt.getTranslation('en', language, prompt_add_website)
            prompt_top_sites_in = mt.getTranslation('en', language, prompt_top_sites_in)
            prompt_top_sites_translated = mt.getTranslation('en', language, prompt_top_sites_translated)
        self.response.out.write('<center>')
        self.response.out.write('<form action=/search method=get>')
        self.response.out.write('<input type=text name=q value="' + q + '" size=50>')
        self.response.out.write('<input type=image src=/image/search.png>')
        self.response.out.write('</form><br>')
        self.guide(language)
        self.response.out.write('</center>')
        self.response.out.write('<hr>')
        # self.response.out.write('<h4><a href=/search?add=y>' + prompt_add_website + '</a> | ' + prompt_create_group + ' </h4></center><hr>')
        if len(q) < 1 and len(domain) < 1:
            pass
        else:
            mt = MTWrapper()
            prompt_recent_translations = 'Recently Submitted Translations'
            if language != 'en' and len(language) > 1:
                prompt_recent_translations = mt.getTranslation('en', language, prompt_recent_translations)
            tdb = db.Query(Translation)
            if len(q) > 0:
                tdb.filter('ngrams = ', q)
            if len(domain) > 0:
                tdb.filter('domain = ', domain)
            tdb.order('-date')
            results = tdb.fetch(limit=25)
            urls = list()
            if results is None or len(results) < 1:
                tdb = db.Query(Translation)
                tdb.order('-date')
                results = tdb.fetch(limit=25)
                self.response.out.write('<h3>' + prompt_recent_translations + '</h3>')
            else:
                query = ''
                if len(domain) > 0:
                    query = '<a href=http://' + domain + '>' + domain + '</a>'
                if len(q) > 0:
                    if len(q) > 0:
                        query = ' / ' + q
                    else:
                        query = q
                self.response.out.write('<h3>' + prompt_recent_translations + ' (' + query + ') </h3>')
            if results is not None:
                for r in results:
                    if len(r.url) > 0 and r.url not in urls:
                        urls.append(r.url)
                        url = r.url
                        if string.count(r.url, 'https:') > 0:
                            url = ''
                        if string.count(url, 'http://') > 0:
                            url = string.replace(url, 'http://', '')
                        if len(url) > 0 and not r.spam:
                            urltexts = string.split(url, '/')
                            domain = urltexts[0]
                            self.response.out.write('<h4>(' + domain + ') <a href=http://' + url + '>' + url + '</a></h4>')
                            txt = '(' + languages.getlist(r.sl) + ' &rarr; ' + languages.getlist(r.tl) + ') '
                            txt = txt + '<p><font size=-1>' + clean(r.st) + ' / '
                            txt = txt + '<i>' + clean(r.tt) + '</i></font><br>'
                            self.response.out.write(txt)
                            
    def page(self, language):
        self.response.out.write('<!-- display or share an article -->')
        prompt_page_not_found = 'Page Not Found'
        prompt_share = 'Share This With Friends'
        prompt_recent_translations = 'Recent Translations'
        if language != 'en' and len(language) > 1 and len(language) < 4:
            mt = MTWrapper()
            prompt_page_not_found = mt.getTranslation('en', language, prompt_page_not_found)
            prompt_share = mt.getTranslation('en', language, prompt_share)
            prompt_recent_translations = mt.getTranslation('en', language, prompt_recent_translations)
        url = self.request.get('url')
        tl = self.request.get('tl')
        founditem = False
        if len(url) > 0:
            if string.count(url, 'http://') > 0:
                url = string.replace(url, 'http://','')
            sdb = db.Query(Search)
            sdb.filter('url = ', url)
            if len(tl) > 0:
                sdb.filter('tl = ', tl)
            item = sdb.get()
            if item is not None:
                founditem = True
                sl = item.sl
                title = codecs.encode(item.title, 'utf-8')
                ttitle = codecs.encode(item.ttitle, 'utf-8')
                description = codecs.encode(item.description, 'utf-8')
                tdescription = codecs.encode(item.tdescription, 'utf-8')
                domain = item.domain
                views = item.views
                views = views + 1
                item.views = views
                item.put()
        if not founditem:
            self.response.out.write('<h3>' + prompt_page_not_found + '</h3>')
        else:
            if len(title) < 1:
                title = url
                # title = htmlscrape(url, 'title')
            if len(ttitle) > 0:
                htitle = title + ' / ' + ttitle
            else:
                htitle = title
            if len(description) < 1:
                pass
                # description = htmlscrape(url, 'description')
            slang = languages.getlist(sl)
            self.response.out.write('<h3>(' + slang + ') <a href=http://' + url + '>' + htitle + '</a></h3>')
            if len(description) > 0:
                self.response.out.write('<em><font size=-1>' + description)
                if len(tdescription) > 0:
                    self.response.out.write(' / <i>' + tdescription + '</i></font></em>')
                self.response.out.write('<br><br>')
            self.response.out.write('<hr>')
            self.response.out.write('<h3>' + prompt_share + '</h3>')
            self.response.out.write('<!-- AddThis Button BEGIN -->\
<a class="addthis_button" href="http://www.addthis.com/bookmark.php?v=250&amp;pub=worldwidelex">\
<img src="http://s7.addthis.com/static/btn/v2/lg-share-en.gif" width="125" height="16" alt="Bookmark and Share" style="border:0"/>\
</a><script type="text/javascript" src="http://s7.addthis.com/js/250/addthis_widget.js?pub=worldwidelex"></script>\
<!-- AddThis Button END -->\
')
            self.response.out.write('<hr>')
            tdb = db.Query(Translation)
            tdb.filter('url = ', url)
            tdb.filter('tl = ', tl)
            tdb.order('-date')
            results = tdb.fetch(limit=30)
            if results is not None:
                self.response.out.write('<h3>' + prompt_recent_translations + '</h3>')
                for r in results:
                    if len(r.username) > 0:
                        userinfo = clean(r.username) + ' (' + r.city + ')'
                    else:
                        userinfo = r.remote_addr + ' (' + r.city + ')'
                    st = clean(r.st)
                    tt = clean(r.tt)
                    if len(st) > 0 and len(tt) > 0:
                        self.response.out.write('<h4>' + userinfo + ' @ ' + str(r.date) + '</h4>')
                        self.response.out.write('<em><font size=-1>' + st + ' / <i> ' + tt + '</i></font></em><br><br>')
    
    def addsite(self, language):
        prompt_add_website = 'Add Your Website To The Directory'
        prompt_title = 'Title of Website'
        prompt_description = 'Description'
        prompt_tags = 'Keywords'
        prompt_language = 'Primary Language'
        prompt_submit = 'Submit'
        if language != 'en' and len(language) > 1:
            mt = MTWrapper()
            prompt_add_website=mt.getTranslation('en', language, prompt_add_website)
            prompt_title=mt.getTranslation('en', language, prompt_title)
            prompt_description=mt.getTranslation('en', language, prompt_description)
            prompt_tags=mt.getTranslation('en', language, prompt_tags)
            prompt_language=mt.getTranslation('en', language, prompt_language)
            prompt_submit=mt.getTranslation('en', language, prompt_submit)
        self.response.out.write('<h2>' + prompt_add_website + '</h2>')
        self.response.out.write('<table><form action=/search method=post>')
        self.response.out.write('<tr><td>URL</td><td><input type=text name=url></td></tr>')
        self.response.out.write('<tr><td>RSS</td><td><input type=text name=rssurl></td></tr>')
        self.response.out.write('<tr><td>' + prompt_title + '</td><td><input type=text name=title></td></tr>')
        self.response.out.write('<tr><td>' + prompt_tags + '</td><td><input type=text name=keywords></td></tr>')
        self.response.out.write('<tr><td>' + prompt_language + '</td><td><select name=language>' + languages.select() + '</select></td></tr>')
        self.response.out.write('<tr><td colspan=2>' + prompt_description + '<br><textarea name=description></textarea></td></tr>')
        self.response.out.write('<tr><td>' + prompt_submit + '</td><td><input type=submit value="' + prompt_submit + '"></td></tr>')
        self.response.out.write('</form></table>')
    
    def recenttranslations(self, language='en'):
        txt = memcache.get('sidebar|recenttranslations|language=all')
        cached = False
        if txt is not None:
            if len(txt) > 0:
                cached = True
        if not cached:
            sdb = db.Query(Translation)
            sdb.order('-date')
            results = sdb.fetch(limit=50)
            ctr = 0
            txt = ''
            urls = list()
            if results is not None:
                for r in results:
                    ctr = ctr + 1
                    if ctr < 25:
                        title = r.domain
                        user = r.username
                        userip = r.remote_addr
                        city = r.city
                        sl = r.sl
                        tl = r.tl
                        sl = languages.getlist(sl)
                        tl = languages.getlist(tl)
                        turl = r.url
                        if string.count(turl, 'http://') < 1:
                            turl = 'http://' + turl
                        description = clean(r.st) + ' / ' + clean(r.tt)
                        if len(title) < 1:
                            title = r.domain
                        if r.url not in urls and string.count(r.url, 'mail') < 1:
                            urls.append(r.url)
                            txt = txt + '<h4>(' + sl + ' &rarr; ' + tl + ') <a href=http://' + r.domain + '>' + title + '</a></h4>'
                            if len(description) > 0:
                                if len(city) > 0:
                                    city = ' / ' + city
                                txt = txt + '<font size=-2>'
                                if len(user) > 0:
                                    txt = txt + '(<a href=/profiles/' + user + '>' + user + city + '</a>) '
                                else:
                                    txt = txt + '(<a href=/profiles/' + userip + '>' + userip + city + '</a>)'
                                txt = txt + '<a href=' + turl + '>' + description + '</a></font><br><br>'
                memcache.set('sidebar|recenttranslations|language=all', txt, 300)
        else:
            return txt
        
    def sidebar(self, language, q='', username='', domain='', page=''):
        prompt_recent_translations = 'Recent Translations'
        prompt_add_website = 'Add A Website To The Directory'
        prompt_get_firefox = 'New: Firefox Translator'
        prompt_essay = 'Essay : The End of the Language Barrier'
        prompt_essay_details = 'Brian McConnell, founder of WWL, published this essay, \
<a href=/s/essay.html>"The End of the Language Barrier"</a>. This essay describes the future \
of the worldwide web, and how it will become a multilingual system. We invite you to share \
and translate the essay and, if you think this is valuable work, to join our \
<a href=/s/donate.html>fundraising campaign.</a><hr>'
        prompt_google_group = 'Visit This Group'
        google_group_badge = '<table style="background-color: #fff; padding: 5px;" cellspacing=0><tr><td>\
<img src="http://groups.google.com/intl/en/images/logos/groups_logo_sm.gif" height=30 width=140 alt="Google Groups"></td></tr>\
<tr><td style="padding-left: 5px;font-size: 125%">\
<b>Worldwide Lexicon</b></td></tr><tr><td style="padding-left: 5px">\
<a href="http://groups.google.com/group/worldwide-lexicon">Visit This Group</a></td></tr></table>'
        if language == 'en':
            ffl = 'en-US'
        elif language == 'es':
            ffl = 'es-ES'
        elif language == 'pt':
            ffl = 'pt-BR'
        else:
            ffl = language
        prompt_get_firefox_details = '<a href=https://addons.mozilla.org/' + ffl + '/firefox/addon/13897>Download the WWL Translator for Firefox</a> \
This free tool automatically translates foreign websites into your language. Now, browsing the web in other languages is as easy as browsing the web in your language.'
        if language != 'en' and len(language) > 1:
            prompt_add_website = tx('en', language, prompt_add_website)
            prompt_get_firefox = tx('en', language, prompt_get_firefox)
            prompt_get_firefox_details = tx('en', language, prompt_get_firefox_details)
            prompt_recent_translatons = tx('en', language, prompt_recent_translations)
            prompt_essay = tx('en', language, prompt_essay)
            prompt_essay_details = tx('en', language, prompt_essay_details)
            prompt_google_group = tx('en', language, prompt_google_group)
            google_group_badge = string.replace(google_group_badge, 'Visit This Group', prompt_google_group)
        self.response.out.write('<h2>' + prompt_get_firefox + '</h2>')
        self.response.out.write('<img src=/image/firefoxlogo.jpg align=left>' + prompt_get_firefox_details)
        self.response.out.write('<hr>')
        self.response.out.write(google_group_badge)
        self.response.out.write('<hr>')
        self.response.out.write('<h2>' + prompt_essay + '</h2>')
        self.response.out.write(prompt_essay_details)
        if page == 'about.html':
            self.feed(language, 'http://wwl.unthinkingly.com/?feed=rss2', limit=10)
        if len(q) < 1 and len(username) < 1 and page != 'about.html':
            self.response.out.write('<h3>Press</h3>')
            self.static(language, 'inthenews.html')
            self.response.out.write('<hr>')
            self.response.out.write('<h3>' + prompt_recent_translations + '</h3>')
            self.response.out.write(self.recenttranslations(language))
        elif len(username) > 0:
            prompt_favorite_sites = 'Recently Translated Websites'
            prompt_statistics = 'Statistics'
            prompt_translations = 'Translations'
            prompt_words = 'Words'
            prompt_languages = 'Languages'
            prompt_cities = 'Cities'
            if language != 'en' and len(language) > 1:
                mt = MTWrapper()
                prompt_statistics = mt.getTranslation('en', language, prompt_statistics)
                prompt_translations = mt.getTranslation('en', language, prompt_translations)
                prompt_words = mt.getTranslation('en', language, prompt_words)
                prompt_languages = mt.getTranslation('en', language, prompt_languages)
                prompt_cities = mt.getTranslation('en', language, prompt_cities)
                prompt_favorite_websites = mt.getTranslation('en', language, prompt_favorite_sites)
            self.response.out.write('<h3>' + prompt_favorite_sites + '</h3>')
            self.response.out.write('<table>')
            for s in self.usertopsites:
                self.response.out.write('<tr><td><a href=http://' + s + '>' + s + '</a></td></tr>')
            self.response.out.write('</table>')
            self.response.out.write('<h3>' + prompt_statistics + '</h3>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>' + prompt_translations + '</td><td>' + str(self.usertranslations) + '</td></tr>')
            self.response.out.write('<tr><td>' + prompt_words + '</td><td>' + str(self.usertwords) + '</td></tr>')
            self.response.out.write('<tr><td>' + prompt_languages + '</td><td>')
            langs = list()
            for l in self.usersl:
                if l not in langs:
                    langs.append(l)
            for l in self.usertl:
                if l not in langs:
                    langs.append(l)
            langs.sort()
            for l in langs:
                self.response.out.write(languages.getlist(l) + '<br>')
            self.response.out.write('</td></tr>')
            self.response.out.write('<tr><td>' + prompt_cities + '</td><td>')
            for c in self.usercities:
                self.response.out.write(c + '<br>')
            self.response.out.write('</td></tr>')
            self.response.out.write('</table>')
            self.response.out.write('</hr>')
        else:
            mt = MTWrapper()
            qtexts = list()
            urls = list()
            qtexts.append(q)
            langs = ['ar', 'de', 'es', 'en', 'fr', 'ja', 'ko', 'ru', 'zh']
            sl = mt.testLanguage(q)
            for l in langs:
                if l != sl:
                    ttext = mt.getTranslation(sl, l, q)
                else:
                    ttext = q
                if len(ttext) > 0 and ttext not in qtexts:
                    qtexts.append(ttext)
            for qtext in qtexts:
                try:
                    qtext = urllib.quote_plus(clean(qtext))
                    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=' + qtext
                    response = urlfetch.fetch(url = url)
                    if response.status_code == 200:
                        r = clean(response.content)
                    else:
                        r = ''
                    if len(r) > 0:
                        json = demjson.decode(r)
                        results = json['responseData']['results']
                        if len(results) > 0:
                            for i in results:
                                if i['unescapedUrl'] not in urls:
                                    urls.append(i['unescapedUrl'])
                                    self.response.out.write('<h4><a href=' + i['unescapedUrl'] + '>' + i['title'] + '</a></h4>')
                except:
                    pass
                
    def static(self, language, page):
        if len(page) > 0:
            txt = memcache.get('static|language=' + language + '|page=' + page)
            if txt is not None:
                self.response.out.write(txt)
            else:
                host = self.request.host
                url = 'http://' + host + '/static/' + page
                try:
                    response = urlfetch.fetch(url=url)
                    if response.status_code == 200:
                        txt = response.content
                except:
                    txt = ''
                texts = string.split(txt, '\n')
                if len(texts) > 0 and language != 'en':
                    txt = ''
                    for t in texts:
                        if len(t) > 8 and language != 'en' and len(language) > 1:
                            txt = txt + tx('en', language, t)
                        else:
                            txt = txt + t
                memcache.set('static|language=' + language + '|page=' + page, txt, 300)
                self.response.out.write(txt)
                
    def topsites(self, language):
        pass
    
    def newusers(self, language):
        """
        This class generates a list of new users. It will be activated as translation activity picks up.
        """
        pass

    def selectlanguage(self, language):
        self.response.out.write('<table><tr><td><form action=/language method=post>')
        self.response.out.write('<select name=tl>')
        if len(language) < 1:
            language = 'en'
        text = languages.select(selected=language)
        self.response.out.write(text)
        self.response.out.write('</select>')
        self.response.out.write('</td><td><input type=submit value=OK></td></tr></form></table>')
    
    def post(self, p1='', p2='', p3=''):
        if p1 == 'profiles':
            action = 'updateuser'
            username = p2
        else:
            action = self.request.get('action')
        if action == 'addsite':
            remote_addr = self.request.remote_addr
            url = self.request.get('url')
            rssurl = self.request.get('rssurl')
            title = self.request.get('title')
            description = self.request.get('description')
            keywords = self.request.get('keywords')
            keywords = string.replace(keywords, ',',' ')
            keylist = string.split(keywords, ' ')
            language = self.request.get('language')
            validurl = True
            if len(url) > 0:
                if string.count(url, 'http://') < 1:
                    url = 'http://' + url
                response = urlfetch.fetch(url = url)
                if response.status_code == 200:
                    validurl = True
            if validurl:
                Search.add(url, sl = language, title = title, description = description, keywords = keylist, rssurl=rssurl)
            url = string.replace(url, 'http://', '')
            self.redirect('/search?url=' + url)
        elif action == 'creategroup':
            title = clean(self.request.get('title'))
            name = string.lower(title)
            name = string.strip(name)
            name = string.replace(name, ' ', '')
            name = string.replace(name, ',', '')
            name = string.replace(name, '.', '')
            name = string.replace(name, '\'', '')
            description = clean(self.request.get('description'))
            if len(name) > 0 and len(title) > 0:
                result = Groups.new(name, title = title, description = description, owner = '')
                self.redirect('/group/' + name)
            else:
                self.redirect('/group/create')
            
        elif action == 'updateuser':
            remote_addr = self.request.remote_addr
            sid = self.request.get('sid')
            description = self.request.get('description')
            skype = self.request.get('skype')
            linkedin = self.request.get('linkedin')
            facebook = self.request.get('facebook')
            www = self.request.get('www')
            tags = self.request.get('tags')
            location = geo.get(remote_addr)
            if len(username) > 0 and len(sid) > 0:
                udb = db.Query(Users)
                udb.filter('username = ', username)
                item = udb.get()
                if item is not None:
                    if item.pwhash == sid:
                        if len(description) > 0:
                            item.description = description
                        if len(skype) > 0:
                            item.skype = skype
                        if len(linkedin) > 0:
                            item.linkedin = linkedin
                        if len(facebook) > 0:
                            item.facebook = facebook
                        if len(www) > 0:
                            item.www = www
                        if len(tags) > 0:
                            tags = string.replace(tags, ',', ' ')
                            tags = string.split(tags)
                            if len(tags) > 0:
                                item.tags = tags
                        if type(location) is dict:
                            item.city = location.get('city','')
                            item.state = location.get('state', '')
                            item.country = location.get('country', '')
                            try:
                                item.latitude = str(location['latitude'])
                                item.longitude = str(location['longitude'])
                            except:
                                pass
                        item.put()
            self.redirect('/profiles/' + username)

    def userprofile(self, username, language):
        prompt_recent_translations = 'Recent Translations'
        prompt_map = 'Map'
        prompt_top_sites = 'Top Sites'
        prompt_user_not_found = 'User Not Found'
        prompt_edit_profile = 'Edit Profile'
        sid = self.request.get('sid')
        edit = self.request.get('edit')
        remote_addr = self.request.remote_addr
        if language != 'en' and len(language) > 1:
            mt = MTWrapper()
            prompt_recent_translations = mt.getTranslation('en', language, prompt_recent_translations)
            prompt_map = mt.getTranslation('en', language, prompt_map)
            prompt_top_sites = mt.getTranslation('en', language, prompt_top_sites)
            prompt_user_not_found = mt.getTranslation('en', language, prompt_user_not_found)
            prompt_edit_profile = mt.getTranslation('en', language, prompt_edit_profile)
        loggedin = False
        if string.count(username, '.') > 2:
            udb = db.Query(GeoDB)
            udb.filter('remote_addr = ', username)
            item = udb.get()
            if item is not None:
                city = item.city
                state = item.state
                country = item.country
            else:
                city = ''
                state = ''
                country = ''
            if len(city) > 0:
                self.response.out.write('<h3>' + username + ' (' + city + ')</h3>')
            else:
                self.response.out.write('<h3>' + username + '</h3>')
        else:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                if item.pwhash == sid:
                    loggedin = True
                self.userupvotes = item.upvotes
                self.userdownvotes = item.downvotes
                self.userblockedvotes = item.blockedvotes
                self.useravgscore = item.avgscore
                self.response.out.write('<h3>' + username + ' @ ' + item.city + ' , ' + item.country + '</h3>')
                self.response.out.write(clean(item.description))
                if loggedin:
                    self.response.out.write('<p><a href=/profiles/' + username + '?sid=' + sid + '&edit=y>' + prompt_edit_profile + '</a>')
        self.response.out.write('<hr>')
        if loggedin and edit == 'y':
            prompt_title = 'Title'
            prompt_website = 'Website'
            prompt_proz = 'ProZ Username'
            prompt_submit = 'Update Profile'
            prompt_description = 'Description'
            prompt_tags = 'Tags'
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                title = clean(item.title)
                description = clean(item.description)
                skype = item.skype
                linkedin = item.linkedin
                facebook = item.facebook
                www = item.www
                proz = item.proz
                tags = item.tags
                taglist = ''
                if type(tags) is list:
                    firsttag = True
                    for t in tags:
                        if firsttag:
                            taglist = t
                            firsttag = False
                        else:
                            taglist = taglist + ' ' + t
            else:
                title = ''
                description = ''
                skype = ''
                linkedin = ''
                facebook = ''
                www = ''
                proz = ''
            if language != 'en' and len(language) > 1 and len(language) < 4:
                mt = MTWrapper()
                prompt_title = mt.getTranslation('en', language, prompt_title)
                prompt_website = mt.getTranslation('en', language, prompt_website)
                prompt_proz = mt.getTranslation('en', language, prompt_proz)
                prompt_description = mt.getTranslation('en', language, prompt_description)
                prompt_tags = mt.getTranslation('en', language, prompt_tags)
            self.response.out.write('<table>')
            self.response.out.write('<form action=/profiles/' + username + ' method=post>')
            self.response.out.write('<input type=hidden name=sid value="' + sid + '">')
            self.response.out.write('<tr><td>Skype</td><td><input type=text name=skype value="' + clean(skype) + '"></td></tr>')
            self.response.out.write('<tr><td>Linked In URL</td><td><input type=text name=linkedin value="' + clean(linkedin) + '"></td></tr>')
            self.response.out.write('<tr><td>Facebook URL</td><td><input type=text name=facebook value="' + clean(facebook) + '"></td></tr>')
            self.response.out.write('<tr><td>' + prompt_proz + '</td><td><input type=text name=proz value="' + clean(proz) + '"></td></tr>')
            self.response.out.write('<tr><td>' + prompt_website + '</td><td><input type=text name=www value="' + clean(www) + '"></td></tr>')
            self.response.out.write('<tr><td>' + prompt_tags + '</td><td><input type=text name=tags value="' + taglist + '"></td></tr>')
            self.response.out.write('<tr><td colspan=2>' + prompt_description + '<br><textarea name=description>' + clean(description) + '</textarea></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="' + prompt_submit + '"></td></tr>')
            self.response.out.write('</form></table>')
        else:
            self.response.out.write('<h3>' + prompt_recent_translations + '</h3>')
            tdb = db.Query(Translation)
            if string.count(username, '.') > 2:
                tdb.filter('remote_addr = ', username)
            else:
                tdb.filter('username = ', username)
            tdb.order('-date')
            results = tdb.fetch(limit=100)
            ctr = 0
            for r in results:
                if r.city not in self.usercities:
                    self.usercities.append(r.city)
                st = clean(r.st)
                tt = clean(r.tt)
                if r.domain not in self.usertopsites:
                    self.usertopsites.append(r.domain)
                if len(r.domain) > 0 and len(st) > 0 and len(tt) > 0:
                    ctr = ctr + 1
                    if r.sl not in self.usersl:
                        self.usersl.append(r.sl)
                    if r.tl not in self.usertl:
                        self.usertl.append(r.tl)
                    self.usertranslations = self.usertranslations + 1
                    try:
                        self.usertwords = self.usertwords + r.twords
                    except:
                        pass
                    url = r.url
                    if len(url) > 4 and string.count(url, 'http://') < 1:
                        url = 'http://' + url
                    if ctr < 30:
                        self.response.out.write('<h4><a href=http://' + r.domain + '>' + r.domain + '</a> (' + languages.getlist(r.sl) + '&rarr;' + languages.getlist(r.tl) + ')</h4>')
                        self.response.out.write('<a href=' + url + '>' + st + ' / ' + tt + '</a><br><br>')
        
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

class item():
    title = ''
        
class Stream(webapp.RequestHandler):
    """
    /stream
    
    Generates JSON object with summary statistics, and a few recent translations
    with properties:
    
    title = title or message
    description = description or tooltip
    sl = source language
    tl = target language
    url = url to link to
    
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        output = 'json'
        tl = self.request.get('tl')
        if len(tl) < 2:
            tl = 'en'
        txt = memcache.get('stream|tl=' + tl)
        if txt is not None:
            self.response.headers['Content-Type']='application/json'
            self.response.out.write(txt)
        else:
            translations = 0
            langs = list()
            cities = list()
            countries = list()
            # count recent translations
            now = datetime.datetime.now()
            year = now.year
            month = now.month
            day = now.day
            tdb = db.Query(Translation)
            tdb.order('-date')
            results = tdb.fetch(limit=100)
            for r in results:
                ts = r.date
                skiprecord = False
                if ts.year == year and ts.month == month and ts.day == day:
                    pass
                else:
                    skiprecord = True
                if r.spam:
                    skiprecord = True
                if len(r.url) < 4:
                    skiprecord = True
                if not skiprecord:
                    translations = translations + 1
                    if r.sl not in langs:
                        langs.append(r.sl)
                    if r.tl not in langs:
                        langs.append(r.tl)
                    if r.city not in cities:
                        if string.count(r.city, 'Null') < 1:
                            cities.append(r.city)
                    if r.country not in countries and len(r.country) == 2:
                        countries.append(r.country)
            i = item()
            items = list()
            if translations > 2:
                title = str(translations) + ' translations from ' + str(len(cities)) + ' cities in ' + str(len(countries)) + ' countries'
                if tl != 'en' and len(tl) == 2:
                    mt = MTWrapper()
                    title = mt.getTranslation('en', tl, title)
                i.title = title
                i.description = title
                i.sl = ''
                i.tl = tl
                i.url = 'www.dermundo.com'
                items.append(i)
            t = 'Download the newest version of the Firefox translator (v 0.935)'
            u = 'https://addons.mozilla.org/en-US/firefox/addon/13897'
            if tl != 'en' and len(tl) > 1:
                mt = MTWrapper()
                t = mt.getTranslation('en', tl, t)
            x = item()
            x.title = t
            x.sl = 'en'
            x.tl = tl
            x.description = t
            x.url = u
            items.append(x)
            d = DeepPickle()
            txt = d.pickleTable(items, 'json')
            memcache.set('stream|tl=' + tl, txt, 1200)
            self.response.headers['Content-Type']='application/json'
            self.response.out.write(txt)

class recommendation():
    sl = 'en'
        
class Request(webapp.RequestHandler):
    """
    /request
    
    This web API implements a simple interface to submit requests for translation,
    and to request a list of URLs that other users have recommended for translation.
    To fetch a list of recommended URLs, call /request via a HTTP GET request with
    the following parameters:
    
    sl = source language code
    tl = target language code
    q = optional keyword or search term (not implemented yet)
    output = output format (xml, json, rss)
    
    To submit a request for translation, call /request via HTTP POST with the
    following parameters:
    
    sl = source language code
    tl = target language code
    domain = web domain
    url = source document URL
    title = document title
    description = document description
    comment = comment (explain why it's worth translating)
    username = WWL username
    pw = WWL password
    price = price user is willing to pay in US dollars (decimal format, e.g. 4.50)
    email = user email (so translator can contact user directly)
    
    It will reply with an OK or error message. A user login is required to submit
    translation requests. If the user tries to submit without a username and pw
    it will reject the request.
    """
    def get(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        if len(sl) > 0:
            sdb = db.Query(Search)
            sdb.filter('sl = ', sl)
            if len(tl) > 0:
                sdb.filter('tl = ', tl)
            sdb.order('-upvotes')
            results = sdb.fetch(limit=100)
            recommendations = list()
            if results is not None:
                for r in results:
                    rec = recommendation()
                    rec.sl = r.sl
                    rec.tl = r.tl
                    rec.domain = r.domain
                    rec.url = r.url
                    rec.title = clean(r.title)
                    rec.description = clean(r.description)
                    recommendations.append(rec)
            d = DeepPickle()
            txt = d.pickleTable(recommendations, 'json')
            self.response.headers['Content-Type']='application/json'
            self.response.out.write(txt)
        else:
            www.serve(self, self.__doc__)
    def post(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        domain = self.request.get('domain')
        url = self.request.get('url')
        title = clean(self.request.get('title'))
        description = clean(self.request.get('description'))
        comment = clean(self.request.get('comment'))
        username = self.request.get('username')
        pw = self.request.get('pw')
        price = self.request.get('price')
        email = self.request.get('email')
        if len(url) > 0 and len(username) > 0 and len(pw) > 0:
            result = Search.request(url, title = title, description = description, comment = comment, sl=sl, tl=tl, username=username, pw=pw, price=price, email=email)
            if result:
                self.response.out.write('ok')
            else:
                self.response.out.write('error')
        else:
            if len(url) < 1 and len(username) < 1 and len(pw) < 1:
                www.serve(self, self.__doc__)
            else:
                self.response.headers['Content-Type']='text/plain'
                if len(url) < 1:
                    self.response.out.write('error\nno url provided')
                elif len(username) < 1 or len(pw) < 1:
                    self.response.out.write('error\ninvalid user login')
                else:
                    self.response.out.write('error')

application = webapp.WSGIApplication([(r'/(.*)/(.*)/(.*)', WebServer),
                                     (r'/(.*)/(.*)', WebServer),
                                     ('/request', Request),
                                     ('/stream', Stream),
                                     ('/language', SetLanguage),
                                     (r'/(.*)', WebServer),
                                     ('/', WebServer)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

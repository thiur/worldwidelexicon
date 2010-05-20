# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Translation Web Server (main.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module serves the main views to the Worldwide Lexicon public system. This is
being phased in to replace the old search.py module, which to be perfectly honest
is a god awful mess.

Copyright (c) 1998-2010, Worldwide Lexicon Inc, Brian S McConnell. 
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
import md5
import datetime
import pydoc
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
# import Worldwide Lexicon modules
import feedparser
from database import APIKeys
from database import Directory
from database import Settings
from database import Translation
from database import UserScores
from language import TestLanguage
from transcoder import transcoder
from www import web
from www import www

# Define convenience functions
            
def clean(text):
    return transcoder.clean(text)

# Define default settings

addthis_button = '<!-- AddThis Button BEGIN -->\
<a class="addthis_button" href="http://www.addthis.com/bookmark.php?v=250&amp;pub=worldwidelex">\
<img src="http://s7.addthis.com/static/btn/v2/lg-share-en.gif" width="125" height="16" alt="Bookmark and Share" style="border:0"/>\
</a><script type="text/javascript" src="http://s7.addthis.com/js/250/addthis_widget.js?pub=worldwidelex"></script>\
<!-- AddThis Button END -->\
'
encoding = 'utf-8'

default_language = 'en'

default_title = 'Worldwide Lexicon'

default_css = 'blueprint'

# Google Analytics Header
google_analytics_header = '<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");\
document.write(unescape("%3Cscript src=\'\" + gaJsHost + \"google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));\
</script>\
<script type="text/javascript">\
try {\
var pageTracker = _gat._getTracker("' + Settings.get('googleanalytics') + '");\
pageTracker._trackPageview();\
} catch(err) {}</script>'

# Define default settings for Blueprint CSS framework, included with this package as the default style sheet

template = 'http://www.worldwidelexicon.org/css/template.html'
template1col = 'http://3.latest.worldwidelexicon.appspot.com/css/template1col.html'
downloads = 'http://www.worldwidelexicon.org/static/downloads.html'

proxy_settings = '<meta name="allow_edit" content="y" />'

sidebar_about = '<h1>About</h1>The Worldwide Lexicon is an open source collaborative translation platform. It is similar to \
                systems like <a href=http://www.wikipedia.org>Wikipedia</a>, and combines machine translation \
                with submissions from volunteers and professional translators. WWL is a translation memory, \
                essentially a giant database of translations, which can be embedded in almost any website or \
                web application. \
                Our mission is to eliminate the language barrier for interesting websites and articles, by \
                enabling people to create translation communities around their favorite webites, topics or \
                groups.\
                <h1>Services</h1>\
                In addition to publishing free, open source software for translation, we offer a wide variety \
                of hosting and consulting services to customers including:\
                <ul><li>Turnkey, hosted translation solutions for business websites</li>\
                <li>Translation community solutions, where your own readers translate your website</li>\
                <li>Custom software development services</li>\
                </ul>\
                Visit our <a href=/services>services page</a> to learn more.<br><br>'

# standard footer and source code attribution, do not modify or hide
standard_footer = 'Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2010 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  WWL multilingual CMS and translation memory is open source software published \
                  under a BSD style license. Contact: bsmcconnell on skype or gmail.'

class WebServer(webapp.RequestHandler):
    def get(self, p1='', p2='', p3=''):
        user_language = TestLanguage.browserlanguage(self.request.headers['Accept-Language'])
        proxy_settings = '<meta name="allow_edit" content="y" />'        
        lsp = ''
        lspusername = ''
        lsppw = ''
        professional_translation_languages = ''
        #professional_translation_languages = Settings.get('professional_translation_languages')
        if len(lsp) > 0:
            proxy_settings = proxy_settings + '<meta name="lsp" content="'+ lsp + '" />'
        if len(lspusername) > 0:
            proxy_settings = proxy_settings + '<meta name="lspusername" content="' + lspusername + '" />'
        if len(lsppw) > 0:
            proxy_settings = proxy_settings + '<meta name="lsppw" content="' + lsppw + '" />'
        if len(professional_translation_languages) > 0:
            proxy_settings = proxy_settings + '<meta name="professional_translation_languages" content="' + professional_translation_languages + '" />'
        menus = '<ul><li><a href=/api>API</a></li>\
<li><a href=http://blog.worldwidelexicon.org>Blog</a></li>\
<li><a href=/drupal>Drupal</a></li>\
<li><a href=/lsps>LSPs</a></li>\
<li><a href=/proxy>Proxy</a></li>\
<li><a href=http://wordpress.org/extend/plugins/speaklike-worldwide-lexicon-translator/>WP</a></li>\
</ul>'
        if p1 == 'blog':
            self.redirect('http://blog.worldwidelexicon.org')
        elif p1 == 's':
            self.error(404)
            self.response.out.write('<h2>Page Not Found</h2>')
        elif p1 == 'review':
            t = '<h2>Review New Translators</h2>'
            t = t + 'Help make the Worldwide Lexicon better by reviewing these translations which were '
            t = t + 'submitted by new volunteer translators.<p>'
            t = t + '<table><form action=/p/submit method=get>'
            results = UserScores.peerreview(limit = 5)
            for r in results:
                tdb = db.Query(Translation)
                if len(r.username) > 0:
                    tdb.filter('username = ', r.username)
                else:
                    tdb.filter('remote_addr = ', r.remote_addr)
                tdb.order('-date')
                translations = tdb.fetch(limit=5)
                ctr = 0
                if len(translations) > 0:
                    for tx in translations:
                        ctr = ctr+1
                        t = t + '<tr valign=top><td width=75%>'
                        t = t + tx.st
                        t = t + '<blockquote>' + tx.tt + '</blockquote>'
                        t = t + '</td><td>'
                        t = t + '<input type=hidden name=guid' + str(ctr) + ' value=' + tx.guid + '>'
                        t = t + '<select name=score' + str(ctr) + '>'
                        t = t + '<option selected value="">---</option>'
                        t = t + '<option value=5>5</option>'
                        t = t + '<option value=4>4</option>'
                        t = t + '<option value=3>3</option>'
                        t = t + '<option value=2>2</option>'
                        t = t + '<option value=1>1</option>'
                        t = t + '<option value=0>0/spam</option>'
                        t = t + '</select></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value="Submit Scores"></td></tr>'
            t = t + '</table></form>'
            w = web()
            w.get(template1col)
            w.replace(template1col,'[google_analytics]',google_analytics_header)
            p1 = 'Worldwide Lexicon : Review New Translators'
            w.replace(template1col,'[title]',p1)
            w.replace(template1col,'[meta]', proxy_settings)
            w.replace(template1col,'[footer]',standard_footer)
            w.replace(template1col,'[menu]',menus)
            w.replace(template1col,'[left_column]',t)
            self.response.out.write(w.out(template1col))
        elif len(p1) > 0:
            page = 'http://www.worldwidelexicon.org/static/' + p1 + '.html'
            w = web()
            w.get(page)
            t = w.out(page)
            w.get(template)
            w.replace(template,'[google_analytics]',google_analytics_header)
            if len(p1) < 4:
                p1 = 'Worldwide Lexicon'
            w.replace(template,'[title]',p1)
            w.replace(template,'[meta]', proxy_settings)
            w.replace(template,'[footer]',standard_footer)
            w.replace(template,'[menu]',menus)
            w.replace(template,'[left_column]',t)
            r = sidebar_about
            r = r + Feeds.get('http://blog.worldwidelexicon.org/?feed=rss2')
            w.replace(template,'[right_column]', r)
            self.response.out.write(w.out(template))
        else:
            w = web()
            w.get(template)
            w.replace(template,'[google_analytics]',google_analytics_header)
            if len(p1) < 4:
                p1 = 'Worldwide Lexicon'
            w.replace(template,'[title]',p1)
            w.replace(template,'[meta]', proxy_settings)
            w.replace(template,'[footer]',standard_footer)
            w.replace(template,'[menu]',menus)
            w.get(downloads)
            t = clean(w.out(downloads))
            sdb = db.Query(Directory)
            sdb.filter('tl = ', 'root')
            sdb.order('-lastupdated')
            results = sdb.fetch(limit=25)
            sites = list()
            for r in results:
                if r.domain not in sites:
                    skip=False
                    if string.count(r.domain,'localhost') > 0:
                        skip=True
                    domains = string.split(r.domain, '.')
                    ld = len(domains)
                    if ld > 1:
                        if ld == 3:
                            if len(domains[2]) > 3 and domains[2] != 'info':
                                skip = True
                        if ld == 2:
                            if len(domains[1]) > 3 and domains[1] != 'info':
                                skip=True
                    if not skip:
                        sites.append(r.domain)
            t = t + '<h2>New Websites On The WWL Network</h2><ul>'
            for s in sites:
                t = t +'<li><a href=http://' + s + '>' + s + '</a></li>'
            t = t + '<li><a href=/sites>(more)</a></li></ul>'
            w.replace(template,'[left_column]',t)
            r = sidebar_about
            r = r + Feeds.get('http://blog.worldwidelexicon.org/?feed=rss2')
            w.replace(template,'[right_column]', r)
            self.response.out.write(w.out(template))
    def post(self, p1='', p2='', p3=''):
        self.redirect('http://blog.worldwidelexicon.org')

class Feeds():
    @staticmethod
    def get(url, fulltext=True, limit=10, maxlength=200):
        t = memcache.get('/feeds/' + url)
        if t is not None:
            return t
        else:
            try:
                f = feedparser.parse(url)
                entries = f.entries
                ctr = 0
                if len(entries) > 0:
                    t = '<h1>News From WWL</h1>'
                    for e in entries:
                        ctr = ctr + 1
                        if ctr < limit:
                            t = t + '<h3><a href=' + e.link + '>' + clean(e.title) + '</a></h3>'
                            if fulltext:
                                txt = clean(e.description)
                                t = t + txt[0:maxlength] + ' ...'
                memcache.set('/feeds/' + url, t, 300)
                return t
            except:
                return ''

application = webapp.WSGIApplication([(r'/(.*)/(.*)/(.*)', WebServer),
                                      (r'/(.*)/(.*)', WebServer),
                                      (r'/(.*)', WebServer),
                                      ('/', WebServer)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

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
from database import languages
from database import Translation
from database import Search
from database import Settings
from database import Users
from geo import geo
from webappcookie import Cookies
from mt import MTWrapper
from deeppickle import DeepPickle
from transcoder import transcoder
from www import www

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
            
def clean(text):
    return transcoder.clean(text)

def tx(sl, tl, st, split = 'n'):
    """
    tx()
    
    This convenience function fetches a human or machine translation for a text
    and displays it in a bilingual format.
    """
    tt = Translation.lucky(sl=sl, tl=tl, st=st, domain='www.worldwidelexicon.org', lsp='speaklike', lspusername=Settings.get('speaklikeusername'), lsppw=Settings.get('speaklikepw'))
    if sl == tl or len(tl) < 2:
        return st
    elif len(tt) > 0:
        return tt
    else:
        return st

# Define default settings

addthis_button = '<!-- AddThis Button BEGIN -->\
<a class="addthis_button" href="http://www.addthis.com/bookmark.php?v=250&amp;pub=worldwidelex">\
<img src="http://s7.addthis.com/static/btn/v2/lg-share-en.gif" width="125" height="16" alt="Bookmark and Share" style="border:0"/>\
</a><script type="text/javascript" src="http://s7.addthis.com/js/250/addthis_widget.js?pub=worldwidelex"></script>\
<!-- AddThis Button END -->\
'
encoding = 'utf-8'

default_language = 'en'

default_title = 'Welcome to the Worldwide Lexicon'

default_css = 'blueprint'

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
    def get(self, p1='', p2='', p3=''):
        self.redirect('http://blog.worldwidelexicon.org')
    def post(self, p1='', p2='', p3=''):
        self.redirect('http://blog.worldwidelexicon.org')

application = webapp.WSGIApplication([(r'/(.*)/(.*)/(.*)', WebServer),
                                      (r'/(.*)/(.*)', WebServer),
                                      (r'/(.*)', WebServer),
                                      ('/', WebServer)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

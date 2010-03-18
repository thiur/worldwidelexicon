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
import urllib2
import string
import datetime
import codecs
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from google.appengine.api import urlfetch
# import WWL modules
from wwlgae import wwl

# Define convenience functions

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

# Define default settings

encoding = 'utf-8'
default_language = 'en'
default_title = 'Hello World'

# standard footer and source code attribution, do not modify or hide
standard_footer = 'Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2009 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  WWL multilingual CMS and translation memory is open source software published \
                  under a BSD style license. Contact: bsmcconnell on skype or gmail.'

translation_server = 'http://worldwidelexicon.appspot.com'

class Test(webapp.RequestHandler):
    """
    This web service finds and displays a page with translations. It expects the
    following URL format:
    
    /test/languagecode/page
    
    It will load the page and then call the WWL translation server to request translations
    as needed. You can run this as a standalone App Engine script without the rest of the WWL
    environment, so it can interact with a remote or public WWL server. 
    
    """
    
    def get(self,p1='', p2='', p3=''):
        # get HTTP headers
        tl = p1
        page = p2
        headers = self.request.headers
        lang = headers.get('Accept-Language', '')
        remote_addr = self.request.remote_addr
        self.header(tl)
        self.static(tl, page)
        self.footer(tl)
        
    def header(self, language):
        head_title = default_title
        head_css = 'blueprint'
        if len(language) < 1:
            language = default_language
        # generate HTML header, link to CSS stylesheet
        self.response.headers['Content-Type']='text/html'
        self.response.out.write('<head><title>' + clean(head_title) + '</title>')
        self.response.out.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></meta>')
        self.title = head_title
        self.response.out.write('</head>')
        
    def footer(self, language):
        self.response.out.write('<div id="footer"><font size=-2>')
        self.response.out.write(standard_footer)
        self.response.out.write('</font></div>')
                
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
                        txt = clean(response.content)
                except:
                    txt = ''
                texts = string.split(txt, '\n')
                if len(texts) > 0 and language != 'en':
                    txt = ''
                    for t in texts:
                        t = t
                        if len(t) > 8 and language != 'en' and len(language) > 1:
                            txt = txt + clean(wwl.get('en', language, t))
                        else:
                            txt = txt + t
                memcache.set('static|language=' + language + '|page=' + page, txt, 300)
                self.response.out.write(txt)

application = webapp.WSGIApplication([(r'/test/(.*)/(.*)', Test)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
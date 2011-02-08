# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Experimental Proxy Server (proxy.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements an experimental translation proxy server.

Copyright (c) 1998-2011, Worldwide Lexicon Inc.
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
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
# import standard Python modules
import sys
import urllib
import string
import md5
import datetime
import codecs
from webappcookie import Cookies
# import WWL modules
from transcoder import transcoder
from BeautifulSoup import BeautifulSoup

def clean(text):
    return transcoder.clean(text)
    
class ProxyHome(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        self.response.out.write('Go to www.worldwidelexicon.org/proxy/...url...')

class ProxyServer(webapp.RequestHandler):
    def get(self, url):
        if string.count(url, ',http://') < 1:
            url = 'http://' + url
        result = urlfetch.fetch(url = url)
        if result.status_code == 200:
            soup = BeautifulSoup(result.content, smartQuotesTo=None)
            self.response.out.write(soup.contents[0])
        else:
            text = ''
            self.response.out.write(text)

application = webapp.WSGIApplication([(r'/proxy/(.*)', ProxyServer),
                                      ('/proxy', ProxyHome)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Language Utilities (language.py)
by Brian S McConnell <brian@worldwidelexicon.org>

OVERVIEW

This module is used in conjunction with the translation proxy server to keep track
of hosts, proxy settings, and subscriptions. This is currently implemented as a
dummy web service for testing purposes. It will implement the following services:

/hosts/auth : authenticates a domain and provides proxy server with settings to
              follow
/hosts/log : logs bandwidth usage, queries, etc for billing purposes

Copyright (c) 1998-2009, Worldwide Lexicon Inc.
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
# import Google App Engine Modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
# import standard Python libraries
import string
import datetime
import codecs
import urllib
# import WWL and third party modules
import demjson

class HostsAuth(webapp.RequestHandler):
    def get(self, domain):
        dtxts = string.split(domain, '.')
        if len(dtxts) == 3 and dtxts[0] != 'www':
            realdomain = 'www.' + dtxts[1] + '.' + dtxts[2]
        elif len(dtxts) == 3 and dtxts[0] == 'www':
            realdomain = 'www2.' + dtxts[1] + '.' + dtxts[2]
        elif len(dtxts) == 2:
            realdomain = 'www.' + dtxts[0] + '.' + dtxts[1]
        else:
            realdomain = domain
            
        self.response.headers['Content-Type']='text/plain'
        self.response.out.write('ok\n' + realdomain)

class HostsLog(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        self.response.headers['Content-Type']='text/plain'
        self.response.out.write('ok\n')
      
application = webapp.WSGIApplication([(r'/hosts/auth/(.*)', HostsAuth),
                                      ('/hosts/log', HostsLog)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()


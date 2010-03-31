# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Language Service Provider Gateway (lsp.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module implements gateway services to send translation requests to
participating language service providers. This module automates the process
of sending requests out to LSPs, and is used to capture results from external
translation memories. 

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
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
import demjson
import urllib
import string
import md5
import codecs
from database import APIKeys
from database import Queue
from database import Translation
from deeppickle import DeepPickle
from config import Config
from www import www

def clean(text):
    try:
        utext = text.encode('utf-8')
    except:
        try:
            utext = text.encode('iso-8859-1')
        except:
            utext = text
    text = utext.decode('utf-8')
    return text

class ReadQueue(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        apikey = self.request.get('apikey')
        if len(apikey) > 0:
            username = APIKeys.auth(apikey)
            if len(username) > 0:
                pass
        else:
            self.response.out.write('error')

class SubmitTranslation(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        pass

application = webapp.WSGIApplication([('/lsp/get', ReadQueue),
                                      ('/lsp/submit', SubmitTranslation)],
                                     debug=True)

# Note: to run this service as a standalone machine translation proxy,
# add an entry ('/', MTServer) to the WSGIApplication call, and update
# app.yaml to send queries to / to my.py instead of main.py

def main():
  run_wsgi_app(application)

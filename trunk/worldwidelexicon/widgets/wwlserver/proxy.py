# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Translations Module (translations.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements classes and data stores to retrieve and save translations and
metadata. This module also encapsulates all calls to translation related data stores.
It is designed to work with Google's App Engine platform, but can be ported relatively
easily to other databases and hosting environments. 

NOTE: this documentation is generated automatically, and directly from the current
version of the WWL source code, via the PyDoc service. Because of the way App
Engine works, the hyperlinks in these files will not work, so your best option
is to print the documentation for offline review.

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
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
# import standard Python modules
import sys
import urllib
import string
import md5
import datetime
import codecs

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

class ProxyController(webapp.RequestHandler):
    def get(self, domain):
        self.requesthandler(domain)
    def post(self, domain):
        self.requesthandler(domain)
    def requesthandler(self, domain):
        self.response.headers['Content-Type']='text/plain'
        subdomains = string.split(domain,'.')
        if len(subdomains) == 3:
            targetdomain = 'www.' + subdomains[1] + '.' + subdomains[2]
        elif len(subdomains) == 4:
            targetdomain = subdomains[1] + '.' + subdomains[2] + '.' + subdomains[3]
        elif len(subdomains) == 5:
            targetdomain = subdomains[1] + '.' + subdomains[2] + '.' + subdomains[3] + '.' + subdomains[4]
        elif len(subdomains) == 2:
            targetdomain = subdomains[1]
        else:
            targetdomain = ''
        self.response.out.write('targetdomain=' + targetdomain + '\n')
        self.response.out.write('translate=y\n')
        self.response.out.write('languages=all\n')
        self.response.out.write('allow_machine=y\n')
        self.response.out.write('allow_edit=y\n')
        self.response.out.write('allow_anonymous=y\n')
        self.response.out.write('require_professional=n\n')
        self.response.out.write('lsp=speaklike\n')
        self.response.out.write('lspusername=foo\n')
        self.response.out.write('lsppw=bar\n')

application = webapp.WSGIApplication([(r'/proxy/(.*)', ProxyController)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

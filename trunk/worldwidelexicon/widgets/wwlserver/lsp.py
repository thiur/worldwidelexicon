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
from database import LSPQueue
from deeppickle import DeepPickle
from transcoder import transcoder
from www import www

def clean(text):
    return transcoder.clean(text)

class SubmitTranslation(webapp.RequestHandler):
    """
    /lsp/submit

    Used to submit a completed translation to the translation memory.
    This bypasses the usual community translation workflow that may require
    additional review or scoring, and treats the submission as a trusted
    source.

    It expects the following parameters:

    apikey = LSP api key
    guid = unique ID of the translation job
    tt = translated text (UTF-8 encoding only)
    score = 0..5 (if submitting a score for a translation)

    It returns ok or an error message

    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        apikey = self.request.get('apikey')
        tt = clean(self.request.get('tt'))
        score = self.request.get('score')        
        if len(apikey) > 0 and len(guid) > 0:
            result = LSPQueue.submit(apikey, guid, tt=tt, score=score)
            if result:
                self.response.out.write('ok')
            else:
                self.response.out.write('error')
        else:
            www.serve(self, self.__doc__)
            self.response.out.write('<table>')
            self.response.out.write('<form action=/lsp/submit method=post>')
            self.response.out.write('<tr><td>LSP API Key (apikey)</td><td><input type=text name=apikey></td></tr>')
            self.response.out.write('<tr><td>Job ID (guid)</td><td><input type=text name=guid></td></tr>')
            self.response.out.write('<tr><td>Translated Text (tt)</td><td><input type=text name=tt></td></tr>')
            self.response.out.write('<tr><td>Score (score=0..5)</td><td><input type=text name=score></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Submit"></td></tr>')
            self.response.out.write('</table></form>')

application = webapp.WSGIApplication([('/lsp/submit', SubmitTranslation)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Proxy Relay Service (relay.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module relays requests sent to the public translation proxy server to the
main WWL translation memory, and caches results locally to minimize loading on
the primary system.

The relay module implements the following API calls at present:

/u : request a batch of translations associated with a URL and target language
/submit : submit a translation for a text
/scores/submit : submit a score for a translation

More functions will be implemented as the proxy service is developed further.

Copyright (c) 1998-2011, Brian S McConnell, Worldwide Lexicon Inc.
All rights reserved.

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
from www import www
from transcoder import transcoder

def clean(text):
    return transcoder.clean(text)

class BatchTranslations(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = self.request.get('url')
        url = string.replace(url, 'http://', '')
        url = string.replace(url, 'https://', '')
        tl = self.request.get('tl')
        m = md5.new()
        m.update(url)
        m.update(tl)
        md5hash = str(m.hexdigest())
        text = memcache.get('/u/' + md5hash)
        if text is not None:
            self.response.out.write(text)
        else:
            burl="http://www.worldwidelexicon.org/u"
            form_fields = {
                "url" : url,
                "tl" : tl
            }
            form_data = urllib.urlencode(form_fields)
            result = urlfetch.fetch(url=burl,
            payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type' : 'application/x-www-form-urlencoded','Accept-Charset' : 'utf-8'})
            text = clean(result.content)
            if len(text) > 2:
                memcache.set('/u/' + md5hash, text, 300)
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(text)

class SubmitTranslation(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        pass

class SubmitScore(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        pass

application = webapp.WSGIApplication([('/u', BatchTranslations),
                                      ('/submit', SubmitTranslation),
                                      ('/scores/submit', SubmitScore)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

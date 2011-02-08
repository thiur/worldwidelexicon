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
from BeautifulSoup import BeautifulSoup

td = dict()
td['eg']='ar'
td['ly']='ar'
td['sa']='ar'
td['kw']='ar'
td['jo']='ar'
td['fr']='fr'
td['de']='de'
td['ru']='ru'
td['jp']='ja'
td['kr']='ko'
td['cn']='zh'
td['hk']='en'
td['tw']='zh'
td['au']='en'
td['uk']='en'
td['ie']='en'
td['ca']='en'
td['nz']='en'
td['se']='sv'
td['no']='nb'
td['fi']='fi'
td['it']='it'
td['es']='es'
td['gr']='el'
td['cz']='cs'
td['pl']='po'
td['ch']='de'
td['hu']='hu'
td['tr']='tr'
td['il']='he'
td['pt']='pt'
td['br']='pt'
td['mx']='es'
td['ni']='es'
td['cr']='es'
td['cl']='es'
td['py']='es'
td['pa']='es'
td['cu']='es'
td['ar']='es'
td['bg']='bg'

def utf(text):
    soup = BeautifulSoup(text, smartQuotesTo=None)
    return soup.contents[0]

def clean(text):
    return utf(text)
    #return transcoder.clean(text)

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
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = clean(self.request.get('st'))
        tt = clean(self.request.get('tt'))
        url = self.request.get('url')
        remote_addr = self.request.remote_addr
        username = self.request.get('username')
        burl="http://www.worldwidelexicon.org/submit"
        form_fields = {
            "sl" : sl,
            "tl" : tl,
            "st" : st,
            "tt" : tt,
            "url" : url,
            "ip" : remote_addr,
            "username" : username
        }
        form_data = urllib.urlencode(form_fields)
        result = urlfetch.fetch(url=burl,
        payload=form_data,
        method=urlfetch.POST,
        headers={'Content-Type' : 'application/x-www-form-urlencoded','Accept-Charset' : 'utf-8'})
        if result.status_code == 200:
            self.response.out.write('ok')
        else:
            self.error(result.status_code)
            self.response.out.write('error')

class SubmitScore(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        guid = self.request.get('guid')
        score = self.request.get('score')
        remote_addr = self.request.remote_addr
        burl="http://www.worldwidelexicon.org/scores/vote"
        form_fields = {
            "guid" : guid,
            "score" : score,
            "ip" : remote_addr
        }
        form_data = urllib.urlencode(form_fields)
        result = urlfetch.fetch(url=burl,
        payload=form_data,
        method=urlfetch.POST,
        headers={'Content-Type' : 'application/x-www-form-urlencoded','Accept-Charset' : 'utf-8'})
        if result.status_code == 200:
            self.response.out.write('ok')
        else:
            self.error(result.status_code)
            self.response.out.write('error')
            
class TestLanguage(webapp.RequestHandler):
    def get(self):
        text=self.request.get('text')
        if len(text) > 0:
            encodedtext = urllib.quote_plus(clean(text))
            url = 'http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=' + encodedtext
            response = urlfetch.fetch(url = url)
            if response.status_code == 200:
                results = demjson.decode(response.content)
            else:
                results = ''
            self.response.out.write(results)
        else:
            self.response.out.write(results)

class TestDomain(webapp.RequestHandler):
    def get(self):
        domain = self.request.get('domain')
        if len(domain) > 0:
            sd = string.split(domain,'.')
            tld = sd[len(sd)-1]
            language = td.get(tld, '')
            self.response.out.write(language)
        else:
            self.response.out.write('')
            
class FetchTranslation(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = clean(self.request.get('st'))
        url = self.request.get('url')
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        allow_machine = 'y'
        output = 'json'
        m = md5.new()
        m.update(sl)
        m.update(tl)
        m.update(st)
        md5hash = str(m.hexdigest())
        text = memcache.get('/t/' + md5hash)
        if text is not None:
            self.response.out.write(text)
        burl="http://www.worldwidelexicon.org/t"
        form_fields = {
            "sl" : sl,
            "tl" : tl,
            "st" : st,
            "url" : url,
            "lsp" : lsp,
            "lspusername" : lspusername,
            "lsppw" : lsppw,
            "allow_machine" : allow_machine,
            "output" : output
        }
        form_data = urllib.urlencode(form_fields)
        try:
            result = urlfetch.fetch(url=burl,
            payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type' : 'application/x-www-form-urlencoded','Accept-Charset' : 'utf-8'})
            if result.status_code == 200:
                memcache.set('/t/' + md5hash, text)
                self.response.out.write(result.content)
            else:
                self.error(result.status_code)
                self.response.out.write('error')
        except:
            self.error(400)
            self.response.out.write('error')
            
class GeoLocate(webapp.RequestHandler):
    def get(self):
        ip = self.request.remote_addr
        try:
            result = urlfetch.fetch(url='http://www.worldwidelexicon.org/geo?ip=' + ip)
            if result.status_code == 200:
                text = result.content
            else:
                text = ''
        except:
            text = ''
        self.response.out.write(text)

application = webapp.WSGIApplication([('/wwl/u', BatchTranslations),
                                      ('/wwl/t', FetchTranslation),
                                      ('/wwl/geo', GeoLocate),
                                      ('/wwl/submit', SubmitTranslation),
                                      ('/wwl/language', TestLanguage),
                                      ('/wwl/domain', TestDomain),
                                      ('/wwl/scores/vote', SubmitScore)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

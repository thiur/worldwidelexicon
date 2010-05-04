# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Machine Translation Proxy Service (mt.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module enables you to proxy queries through to several different
machine translation services, such as Google, Apertium and Systran,
as well as any number of custom MT engines you deploy for specialized
language pairs. The basic idea is to build wrapper functions that
expect a short list of parameters (source language, target language and
text to translate). The module decides which engine to route the
query to based on the language pair, calls a class specific to that MT
engine, and returns the translated string as UTF-8 Unicode.

The MTWrapper class encapsulates all of this, so it is pretty
straightforward to extend this library to work with any combination of
public and private machine translation engines. In the version 1 API, we
would archive the machine translated texts in the permanent data store,
but discontinued that practice in the version 2 API because we would often
receive error messages instead of translations (the WWL translation memory,
of course, has no way of knowing that "server not available" is not a correct
translation for "If I had known you were coming, I would have baked a cake."

We now assume that if a user edits a machine translation and saves those
changes that this is probably a good enough translation to save in the permanent
data store.

NOTE: This module can be hosted independently of other Worldwide Lexicon
components. If you simply want to build an efficient machine translation
proxy to front end multiple translation engines, you can configure your
app.yaml file to run mt.py as your server's default script with the entry
at the bottom of the configuration file:

    - url: .*
      script: mt.py
      secure: optional

In this scenario, you can then go to the following URL to fetch translations:

yoursite.appspot.com?sl=source_lang&tl=target_lang&st=escaped_text

The request handler accepts both HTTP GET queries (OK for short texts) and
HTTP POST (recommended for translating longer texts). It returns its response
as a simple text/plain response with Unicode UTF-8 encoding unless you explicitly
force it to use a different character set or encoding.

Copyright (c) 1998-2010, Brian S McConnell, Worldwide Lexicon Inc.
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
from deeppickle import DeepPickle
from www import www
from transcoder import transcoder

def clean(text):
    return transcoder.clean(text)

# 
# Machine Translation Settings
#
# Language Pair --> Translation Engine Assignments
#

# Define default engine
default_engine = 'google'

# Define language specific settings
#
# These predefined default settings will be overridden if you
# manage your machine translation settings via the admin web
# interface at /admin on your WWL server. 
#
lp = dict()
lp['es-en']='google'
lp['en-es']='google'
lp['en-ca']='google'
lp['en-gl']='apertium'

lp['es-gl']='apertium'
lp['es-ca']='apertium'
lp['es-fr']='apertium'
lp['es-oc']='apertium'
lp['es-pt']='apertium'

lp['ca-en']='apertium'
lp['ca-es']='apertium'
lp['ca-fr']='apertium'
lp['ca-oc']='apertium'

lp['cy-en']='apertium'

lp['fr-ca']='apertium'
lp['fr-es']='apertium'

lp['gl-en']='apertium'
lp['gl-es']='apertium'
lp['gl-pt']='apertium'

lp['oc-ca']='apertium'
lp['oc-es']='apertium'

lp['pt-es']='apertium'
lp['pt-fr']='apertium'

lp['eu-es']='apertium'

lp['sv-da']='apertium'
lp['nn-nb']='apertium'
lp['nb-nn']='apertium'
lp['no-nb']='apertium'
lp['nb-no']='apertium'

baseurls=dict()
baseurls['google']='http://ajax.googleapis.com/ajax/services/language/translate'
baseurls['apertium']='http://api.apertium.org/json/translate'

class MT(db.Model):
    langpair = db.StringProperty(default='')
    mtengine = db.StringProperty(default='')
    url = db.StringProperty(default='')
    output = db.StringProperty(default='')
    @staticmethod
    def add(sl, tl, mtengine):
        if len(sl) > 1 and len(tl) > 1:
            mdb = db.Query(MT)
            mdb.filter('langpair = ', sl + '-' + tl)
            item = mdb.get()
            if item is None:
                item = MT()
                item.langpair = sl + '-' + tl
            item.mtengine = mtengine
            item.put()
            memcache.delete('/mtengines')
            memcache.set('/mtengines/' + sl + '-' + tl, mtengine,300)
            return True
        else:
            return False
    @staticmethod
    def defaults():
        lpkeys = lp.keys()
        for l in lpkeys:
            mdb = db.Query(MT)
            mdb.filter('langpair = ', l)
            item = mdb.get()
            if item is None:
                item = MT()
                item.langpair = l
            item.mtengine = lp[l]
            item.put()
            memcache.set('/mtengines/' + l, lp[l], 300)
    @staticmethod
    def find():
        results = memcache.get('/mtengines')
        if results is not None:
            return results
        mdb = db.Query(MT)
        mdb.order('langpair')
        results = mdb.fetch(limit=200)
        if len(results) < 1:
            MT.defaults()
            mdb = db.Query(MT)
            mdb.order('langpair')
            results = mdb.fetch(limit=200)
            memcache.set('/mtengines', results, 300)
            return results
        else:
            memcache.set('/mtengines', results, 300)
            return results
    @staticmethod
    def pickengine(sl, tl):
        mtengine = memcache.get('/mtengines/' + sl + '-' + tl)
        if mtengine is not None:
            return mtengine
        else:
            mdb = db.Query(MT)
            mdb.filter('langpair = ', sl + '-' + tl)
            item = mdb.get()
            if item is not None:
                memcache.set('/mtengines/' + sl + '-' + tl, item.mtengine, 300)
                return item.mtengine
            else:
                mtengine = memcache.get('/mtengines/default-default')
                if mtengine is not None:
                    return mtengine
                else:
                    mdb = db.Query(MT)
                    mdb.filter('langpair = ', 'default-default')
                    item = mdb.get()
                    if item is not None:
                        mtengine = item.mtengine
                        memcache.set('/mtengines/default-default', mtengine,900)
                        return mtengine
                    else:
                        memcache.set('/mtengines/default-default', 'google', 900)
                        return 'google'
    @staticmethod
    def geturl(sl,tl):
        mtengine=MT.pickengine(sl,tl)
        url = baseurls.get(mtengine,'')
        if len(mtengine) > 0:
            t = 'mtengine=' + mtengine + '\nurl=' + url + '\nformat=google'
        else:
            t = ''
        return t
    @staticmethod
    def remove(langpair):
        if len(langpair) > 2:
            mdb = db.Query(MT)
            mdb.filter('langpair = ', langpair)
            item = mdb.get()
            if item is not None:
                item.delete()
                memcache.delete('/mtengines')
                memcache.delete('/mtengines/' + langpair)
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def select():
        engines = list()
        engines.append('apertium')
        engines.append('google')
        engines.append('moses')
        engines.append('worldlingo')
        t = '<select name=mtengine>'
        defaultengine = MT.pickengine('default', 'default')
        if len(defaultengine) < 1:
            defaultengine = 'google'
        t = t + '<option selected value="' + defaultengine + '">' + string.capitalize(defaultengine) + '</option>'
        for e in engines:
            if e != defaultengine:
                t = t + '<option value="' + e + '">' + string.capitalize(e) + '</option>'
        t = t + '</select>'
        return t

class MTWrapper():
    """
    This is a wrapper class that encapsulates methods to make HTTP queries to other
    machine translation engines. It implements a consistent input/output interface
    so that all machine translation services are called in the same manner and return their
    results in the same format.
    """
    google_url = 'http://ajax.googleapis.com/ajax/services/language/translate'
    apertium_url = 'http://xixona.dlsi.ua.es/webservice/ws.php'

    def testLanguage(self,text):
        try:
            encodedtext = urllib.quote_plus(clean(text))
        except:
            try:
                encodedtext = urllib.urlencode(clean(text))
            except:
                encodedtext = ''
        url = 'http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=' + encodedtext
        response = urlfetch.fetch(url = url)
        if response.status_code == 200:
            results = demjson.decode(response.content)
        try:
            sl = results['responseData']['language']
        except:
            sl = ''
        return sl
    def pickEngine(self,sl,tl):
        """
        Decides which translation engine to use based on language pairs,
        use default_engine if no specific setting is found
        Returns a string with the name of the selected translation engine,
        which is used, in turn, to decide which
        MT proxy class to call to submit an external CGI query. 
        """
        engine = MT.pickengine(sl,tl)
        return engine
    def geturl(self, sl, tl):
        return MT.geturl(sl,tl)
    def getTranslation(self,sl='en',tl='es',st='',mtengine='',domain='',url='', mode='text', userip=''):
      """
      Fetches machine translation, if mtengine is specified then override automatic MT engine selection
      calls selected MT engine via wrapper class, returns text or empty string to calling function.
      """
      response = dict()
      tt=''
      if sl == tl:
          if mode == 'text':
            return st
          else:
            response['engine']=''
            response['tt']=st
            return response
      if len(mtengine) < 1:
          mtengine=self.pickEngine(sl,tl)
      st = clean(st)
      if len(st) < 2:
        if mode == 'text':
            return ''
        else:
            response['engine']=''
            response['tt']=''
            return response
      m = md5.new()
      m.update(sl)
      m.update(tl)
      m.update(st)
      md5hash = str(m.hexdigest())
      tt = memcache.get('/mt/' + sl + '/' + tl + '/' + md5hash)
      if tt is not None:
          if len(tt) > 0:
              if mode == 'text':
                return tt
              else:
                response['engine']=mtengine
                response['tt']=tt
                return response
          else:
              if mode == 'text':
                return st
              else:
                response['engine']=''
                response['tt']=tt
                return response
      tt = ''
      if mtengine=='google':
        mt = GoogleMTProxy()
        tt = mt.getTranslation(sl,tl,st,userip)
      if mtengine=='babelfish':
        mt = BabelfishMTProxy()
        tt = mt.getTranslation(sl,tl,st,userip)
      if mtengine=='apertium':
        mt = ApertiumProxy()
        tt = mt.getTranslation(sl,tl,st,userip)
      if mtengine=='worldlingo':
        mt = WorldLingoProxy()
        tt = mt.getTranslation(sl,tl,st,userip)
      if mtengine=='moses':
        mt = MosesProxy()
        tt = mt.getTranslation(sl,tl,st,userip)
      # parse return results
      if tt is not None:
        tt = clean(tt)
        if len(tt) > 0:
            if len(md5hash) > 0:
                memcache.set('/mt/' + sl + '/' + tl + '/' + md5hash, tt, 3600)
            elif len(st) < 200:
                memcache.set('/mt/' + sl + '/' + tl + '/' + st, tt, 3600)
            else:
                pass
            if mode == 'text':
                return tt
            else:
                response['engine']=mtengine
                response['tt']=tt
                return response
        else:
            if mode == 'text':
                return st
            else:
                response['engine']=''
                response['tt']=st
      else:
        if mode == 'text':
            return st
        else:
            response['engine']=''
            response['tt']=st
            return response
    
class BabelfishMTProxy():
    """
    Makes query to Babelfish MT Engine
    """
    def getTranslation(self,sl='en',tl='ca',st='',userip=''):
      url="http://babelfish.yahoo.com/translate_txt"
      form_fields = {
        "intl" : "1",
        "lp" : sl + '_' + tl,
        "urltext" : st
      }
      form_data = urllib.urlencode(form_fields)
      try:
          result = urlfetch.fetch(url=url,
                              payload=form_data,
                              method=urlfetch.POST,
                              headers={'Content-Type' : 'application/x-www-form-urlencoded','Accept-Charset' : 'utf-8'})
          tt = result.content
      except:
          tt=''
      return clean(tt)

class GoogleMTProxy():
    """
    Makes query to and parses response from Google Translate machine translation
    engine (uses the demjson module to parse JSON response)
    """
    def getTranslation(self, sl='en', tl='es',st = '',userip=''):
      url="http://ajax.googleapis.com/ajax/services/language/translate"
      form_fields = {
        "langpair": sl + '|' + tl,
        "v" : "1.0",
        "q": st,
        "ie" : "UTF8",
        "userip" : userip
      }
      form_fields
      form_data = urllib.urlencode(form_fields)
      try:
          result = urlfetch.fetch(url=url,
                            payload=form_data,
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
          results = demjson.decode(result.content)
          try:
              tt = results['responseData']['translatedText']
          except:
              tt = ''
          return clean(tt)
      except:
          return ''
        
class ApertiumProxy():
    """
    Makes query to Apertium open source, rules based translation engine.

    Thanks to Fran Tyers for help debugging the CGI interface to Apertium.
    """
    def getTranslation(self,sl='en',tl='ca',st='',userip=''):
      url="http://api.apertium.org/json/translate"
      form_fields = {
        "format" : "html",
        "langpair" : sl + '|' + tl,
        "ie" : "UTF8",
        "q" : st
      }
      form_data = urllib.urlencode(form_fields)
      try:
          result = urlfetch.fetch(url=url,
                              payload=form_data,
                              method=urlfetch.POST,
                              headers={'Content-Type' : 'application/x-www-form-urlencoded','Accept-Charset' : 'utf-8'})
          results = demjson.decode(result.content)
          try:
              tt = results['responseData']['translatedText']
          except:
              tt = ''
          return clean(tt)
      except:
          return ''

#
# Some addition stubs for other machine translation systems (not yet implemented)
#
# As you can see, it is pretty straightforward to add additional MT engines as needed. For now language pair --> engine mappings
# are defined in code, but at some point, we will implement a web control panel for this.
#

class MosesProxy():
    """
    Wrapper class for Moses statistical machine translation systems
    (will probably need to be modified on case by case basis)
    """
    def getTranslation(self,sl='en',tl='',st='',userip=''):
        url = 'http://demo.statmt.org/translate.php'
        form_fields = {
            "langpair": sl + '|' + tl,
            "v" : "1.0",
            "q": st,
            "ie" : "UTF8"
        }
        form_data = urllib.urlencode(form_fields)
        try:
            result = urlfetch.fetch(url=url,
                            payload=form_data,
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
            results = demjson.decode(result.content)
            try:
                tt = results['responseData']['translatedText']
            except:
                tt = ''
            return clean(tt)
        except:
            return ''

class WorldLingoProxy():
    """
    Makes query to and parses response from WorldLingo machine translation
    service (requires user credentials)
    """
    def getTranslation(self, sl='en', tl='es',st = '',userip=''):
        if len(st) > 0:
            sl = WorldLingoLanguage(sl)
            tl = WorldLingoLanguage(tl)
            subscription = Settings.get('worldlingosubscription')
            pw = Settings.get('worldlingopw')
            baseurl = 'http://www.worldlingo.com/' + subscription + '/api?'
            ust = urllib.quote_plus(st)
            suffix = 'wl_password=' + pw + '&wl_srclang=' + sl + '&wl_trglang=' + tl + '&wl_opt=0&wl_errorstyle=1&' + '&wl_data=' + ust
            url = baseurl + suffix
            response = urlfetch.fetch(url=url)
            try:
                tt = response.content
                return clean(tt)
            except:
                return ''
        else:
            return ''
        
def WorldLingoLanguage(l):
    if l == 'bg':
        l = 'lwa_bg'
    if l == 'cs':
        l = 'lwa_cs'
    if l == 'da':
        l = 'lwa_da'
    if l == 'fi':
        l = 'lwa_fi'
    if l == 'ha':
        l = 'lwa_ha'
    if l == 'he':
        l = 'lwa_he'
    if l == 'hi':
        l = 'lwa_hi'
    if l == 'hu':
        l = 'lwa_hu'
    if l == 'no':
        l = 'lwa_no'
    if l == 'ps':
        l = 'lwa_ps'
    if l == 'fa':
        l = 'lwa_fa'
    if l == 'pl':
        l = 'lwa_pl'
    if l == 'ro':
        l = 'lwa_ro'
    if l == 'sr':
        l = 'lwa_sr'
    if l == 'so':
        l = 'lwa_so'
    if l == 'th':
        l = 'lwa_th'
    if l == 'tr':
        l = 'lwa_tr'
    if l == 'ur':
        l = 'lwa_ur'
    return l

class MTServer(webapp.RequestHandler):
    """
    /mt
    
    This web API interface is a general purpose machine translation proxy server.
    It front ends one or many different machine translation services, and presents
    a common interface to the clients using this interface, so the client can just
    submit one query to WWL, which proxies the request through to upstream services.
    It expects the following parameters:<p>
    
    <ul><li>sl = source language (ISO code)</li>
    <li>tl = target language (ISO code)</li>
    <li>st = source text (Unicode UTF-8 encoding)</li>
    <li>mtengine = machine translation engine to use (to override automatic selection)</li></ul>
    
    It replies with a plain text response with the translated text, or an empty
    string if the query fails. The proxy server will memcache queries so frequently
    requested texts are cached in memory (such as in a page that is being reloaded
    frequently). Unless otherwise noted, the returned text will be Unicode with
    UTF-8 encoding.<p>
    
    The proxy server currently supports the following machine translation
    services (more are being added for the June OSS release):<p>
    
      <ul><li>Google : about 50 languages supported</li>
      <li>Apertium : Spanish, Catalan, French, Portuguese, Galician, Basque, Bretton</li>
      <li>Moses : open source statistical machine translation system</li>
      <li>World Lingo: commercial machine translation service (SaaS)</li></ul>
    
    We are planning to add connectors to several popular enterprise machine
    translation systems, as soon as we receive documentation from vendors
    on their SaaS offerings. If you have a machine translation system that
    you would like to add to WWL, just email brian@worldwidelexicon.org
    with instructions for querying your web API. The service should be
    accessible via a standard HTTP GET/POST CGI query and return Unicode
    compliant (UTF-8 encoded) text in response. You can also extend the
    mt.py module to create your own custom MT connectors for private or
    intranet applications.<p>
     
    NOTE: to request a combined recordset containing both human and
    machine translations, call the /q (get.py) web service instead, as it
    returns both types of translations depending on query settings. This
    method is provided specifically for MT queries, and for backward
    compatibility with the version 1 web API.<p>
    
    """
    def get(self, sl='', tl='', st=''):
        """Handles HTTP GET calls"""
        self.requesthandler(sl, tl, st)
    def post(self, sl='', tl='', st=''):
        """Handles HTTP POST calls"""
        self.requesthandler(sl, tl, st)
    def requesthandler(self, sl, tl, st):
        """Combined request handler for both GET and POST calls"""
        mode = 'form'
        if len(sl) < 1:
            sl = self.request.get('sl')
            mode = 'rest'
        if len(tl) < 1:
            tl = self.request.get('tl')
            mode = 'rest'
        if len(st) > 0:
            st = transcoder.clean(st)
            st = string.replace(st, '+', ' ')
        if len(st) < 1:
            st = clean(self.request.get('st'))
        mtengine = self.request.get('mtengine')
        output = self.request.get('output')
        q = clean(self.request.get('q'))
        langpair = self.request.get('langpair')
        if len(q) > 0 and len(langpair) > 0:
            st = q
            langs = string.split(langpair, '|')
            if len(langs) == 2:
                sl = langs[0]
                tl = langs[1]
                output = 'google'
            else:
                sl = ''
                tl = ''
        userip = self.request.remote_addr
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            m = MTWrapper()
            tt = m.getTranslation(sl, tl, st, mtengine=mtengine,userip=userip)
            tt = string.replace(tt, '\n', '')
            if mode == 'rest' or output != 'google':
                self.response.headers['Content-Type']='text/plain'
                self.response.headers['Accept-Encoding']='utf-8'
                self.response.out.write(tt)
            else:
                self.response.headers['Content-Type']='text/javascript'
                self.response.headers['Accept-Encoding']='utf-8'
                response='{"responseData": {"translatedText":"[translation]"},"responseDetails": null, "responseStatus": 200}'
                response=string.replace(response,'[translation]', string.replace(tt, '\"', '\''))
                self.response.out.write(response)
        else:
            t = '<form action=/mt method=post><table>'
            t = t + '<tr><td>Source Language Code</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language Code</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Machine Translation Engine</td><td><input type=text name=mtengine></td></tr>'
            t = t + '<tr><td>Output Format (text|google)</td><td><input type=text name=output></td></tr>'
            t = t + '<tr><td colspan=2><textarea name=st rows=4 cols=60>Hello World</textarea></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=Translate></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = self.__doc__, title = '/mt (Machine Translation API)')

class MTGetUrl(webapp.RequestHandler):
    def get(self, sl, tl):
        self.response.headers['Content-Type']='text/plain'
        if len(sl) > 0 and len(tl) > 0:
            self.response.out.write(MT.geturl(sl,tl))

application = webapp.WSGIApplication([('/mt', MTServer),
                                      (r'/mt/(.*)/(.*)/(.*)', MTServer),
                                      (r'/mt/(.*)/(.*)',MTGetUrl)],
                                     debug=True)

def main():
  run_wsgi_app(application)

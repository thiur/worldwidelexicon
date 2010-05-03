# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Language Service Provider Gateway (lsp.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module implements gateway services to send translation requests to
participating language service providers. This module automates the process
of sending requests out to LSPs.

LSPs can easily join the WWL network by requesting an API key (used to validate
submissions), and then implement a very simple web API on their end to process
requests for translations. 

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
from database import Translation
from transcoder import transcoder
try:
    from www import www
except:
    pass

# Define constants

def clean(text):
    return transcoder.clean(text)

class LSP():
    @staticmethod
    def get(sl, tl, st, domain='', url='', lsp='', lspusername='', lsppw='', ttl = 3600):
        """
        This function is checks memcached for a cached translation from the desired LSP and text,
        and if one is cached locally returns it. If the cache has expired or does not exist, it
        makes an HTTP/S call to the language service provider to request the translation. The LSP
        will return either a blank text, a completed translation or an HTTP error. 
        """
        if len(lsp) > 0 and len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            url = memcache.get('/lsp/url/' + lsp)
            if url is None:
                url = APIKeys.geturl(lsp=lsp)
                if len(url) > 0:
                    memcache.set('/lsp/url/' + lsp, url, 1800)
            if len(url) > 0:
                st = clean(st)
                m = md5.new()
                m.update(sl)
                m.update(tl)
                m.update(st)
                guid = str(m.hexdigest())
                text = memcache.get('/lsp/' + lsp + '/' + guid)
                if text is not None:
                    return text
                else:
                    parms = dict()
                    parms['sl']=sl
                    parms['tl']=tl
                    parms['st']=st
                    parms['domain']=domain
                    parms['url']=url
                    parms['lspusername']=lspusername
                    parms['lsppw']=lsppw
                    form_data = urllib.urlencode(parms)
                    try:
                        result = urlfetch.fetch(url=url, payload = form_data, method = urlfetch.POST, headers = {'Content-Type' : 'application/x-www-form-urlencoded' , 'Accept-Charset' : 'utf-8'})
                        if result.status_code == 200:
                            tt = clean(result.content)
                        else:
                            tt = ''
                    except:
                        tt=''
                    if len(tt) > 0:                        
                        memcache.set('/lsp/' + lsp + '/' + guid, tt, ttl)
                    return tt
            else:
                    return ''
        else:
            return ''

class TestTranslation(webapp.RequestHandler):
    """
    <h3>/lsp/test</h3>

    This is a test form you can use to submit translation requests to LSPs via WWL, to verify that
    your API is processing queries correctly.<p>

    The form handler will submit the query to your server as defined in the guidelines for language
    service providers (see blog.worldwidelexicon.org for details). You should return one of the following:<p>

    <ul><li>a UTF-8 encoded text with the translation for the source text</li>
    <li>a blank text, if no translation has been created yet (we will assume it is in queue)</li>
    <li>a HTTP error message, if the request is incomplete or the user credentials are invalid</li></ul>

    WWL will cache the translation for 1 to 2 hours, after which it will resend the request to you. If the
    translation has changed since then, you can return the newest translation. (You should be sure to
    design your script so that it first checks to see if a text has already been translated, so you do not
    resubmit an already translated text to translators again.<p>
    """
    def get(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = clean(self.request.get('st'))
        domain = self.request.get('domain')
        url = self.request.get('url')
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            tt = LSP.get(sl, tl, st, domain=domain, url=url, lsp=lsp, lspusername=lspusername, lsppw=lsppw)
            tt = clean(tt)
            self.response.out.write(tt)
        else:
            doc_text = self.__doc__
            t = '<table><form action=/lsp/test method=get>'
            t = t + '<tr><td>Source Language Code</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language Code</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Source Text</td><td><input type=text name=st></td></tr>'
            t = t + '<tr><td>Domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>URL</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td>LSP</td><td><input type=text name=lsp></td></tr>'
            t = t + '<tr><td>LSP Username</td><td><input type=text name=lspusername></td></tr>'
            t = t + '<tr><td>LSP PW/Key</td><td><input type=text name=lsppw></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</form></table>'
            www.serve(self, t, sidebar = doc_text)

class SubmitTranslation(webapp.RequestHandler):
    """
    <h3>/lsp/submit</h3>

    Used to submit a completed translation to the translation memory.
    This bypasses the usual community translation workflow that may require
    additional review or scoring, and treats the submission as a trusted
    source.<p>

    It expects the following parameters:<p>
    <ul>
    <li>apikey = LSP api key</li>
    <li>sl = source language code</li>
    <li>tl = target language code</li>
    <li>st = source text (utf8)</li>
    <li>tt = translated text (utf8)</li>
    <li>domain = optional domain text is from (e.g. foo.com)</li>
    <li>url = optional source url text is from</li>
    <li>guid = unique ID of the translation job</li>
    </ul>

    It returns ok or an error message. The web service will store the translation in the permanent translation memory,
    and will also update the real-time cache associated with LSP queries. 

    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        apikey = self.request.get('apikey')
        lsp = self.request.get('lsp')
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = clean(self.request.get('st'))
        tt = clean(self.request.get('tt'))
        domain = self.request.get('domain')
        url = self.request.get('url')
        if len(apikey) > 0:
            username = APIKeys.getusername(apikey)
            if len(sl) > 0 and len(tl) > 0 and len(tt) > 0 and len(username) > 0:
                m = md5.new()
                m.update(sl)
                m.update(tl)
                m.update(st)
                md5hash = str(m.hexdigest())
                memcache.set('/lsp/' + lsp + '/' + md5hash, tt, 3600)
                m = md5.new()
                m.update(sl)
                m.update(tl)
                m.update(st)
                m.update(tt)
                guid = str(m.hexdigest())
                tdb = db.Query(Translation)
                tdb.filter('sl = ', sl)
                tdb.filter('tl = ', tl)
                tdb.filter('guid = ', guid)
                item = tdb.get()
                if item is None:
                    item = Translation()
                    item.guid = guid
                    item.md5hash = md5hash
                    item.sl = sl
                    item.tl = tl
                    item.st = st
                    item.tt = tt
                    item.domain = domain
                    item.url = url
                    item.username = username
                    item.professional = True
                    item.anonymous = False
                    item.put()
                self.response.out.write('ok')
            else:
                self.response.out.write('error')
        else:
            doc_text = self.__doc__
            t = '<table>'
            t = t + '<form action=/lsp/submit method=post>'
            t = t + '<tr><td>LSP Name (lsp)</td><td><input type=text name=lsp></td></tr>'
            t = t + '<tr><td>LSP API Key (apikey)</td><td><input type=text name=apikey></td></tr>'
            t = t + '<tr><td>Source Language Code (sl)</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language Code (tl)</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Source Text (st)</td><td><input type=text name=st></td></tr>'
            t = t + '<tr><td>Translated Text (tt)</td><td><input type=text name=tt></td></tr>'
            t = t + '<tr><td>Domain (domain)</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>URL (url)</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value="Submit"></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = doc_text)

application = webapp.WSGIApplication([('/lsp/submit', SubmitTranslation),
                                      ('/lsp/test', TestTranslation)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
    main()

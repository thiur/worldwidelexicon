# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Language Utilities (language.py)
by Brian S McConnell <brian@worldwidelexicon.org>

OVERVIEW

This module implements utilities to set and detect languages. It can be used to:

* Set and memorize the preferred target language (via cookie)
* Detect the language associated with a domain or block of text

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
from deeppickle import DeepPickle
from www import www
from mt import MTWrapper
from webappcookie import Cookies
from database import Comment
from database import languages

class Domains(db.Model):
    domain = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    date = db.DateTimeProperty(auto_now_add = True)
    @staticmethod
    def language(d='', text=''):
        if len(text) > 0 and len(domain) < 1:
            encodedtext = urllib.quote_plus(codecs.encode(text, 'utf-8'))
            url = 'http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=' + encodedtext
            response = urlfetch.fetch(url = url)
            if response.status_code == 200:
                results = demjson.decode(response.content)
            try:
                sl = results['responseData']['language']
            except:
                sl = ''
            return sl
        else:
            if string.count(d, 'http://') > 0:
                d = string.replace(d, 'http://', '')
            if string.count(d, 'google') > 0  or string.count(d, 'dermundo') > 0 or string.count(d, 'worldwidelexicon') > 0:
                return 'disabled'
            subdomains = string.split(d, '.')
            if len(subdomains) > 1:
                numsub = len(subdomains)
                suffix= subdomains[numsub-1]
            else:
                suffix = ''
            if suffix == 'es' or suffix == 'mx' or suffix == 'ar' or suffix == 'cl' or suffix == 'pe':
                return 'es'
            elif suffix == 'fr':
                return 'fr'
            elif suffix == 'de':
                return 'de'
            elif suffix == 'jp':
                return 'ja'
            elif suffix == 'cn' or suffix == 'tw':
                return 'zh'
            elif suffix == 'br' or suffix == 'pt':
                return 'pt'
            elif suffix == 'po':
                return 'po'
            elif suffix == 'ru':
                return 'ru'
            else:
                return ''
            
class lx():
    code = ''
    name = ''

class ProcessForm(webapp.RequestHandler):
    """
    /language
    
    This request handler enables you to set the target language (to translate to), and also to detect the
    source language of a web domain or block of text. It expects any of the following parameters:
    
    sl = to set the source language (if requesting a list of machine translation servers)
    tl = to set the target language (it will set a cookie, tl, on the user's browser)
    domain = to detect the language associated with a web domain (e.g. lemonde.fr)
    text = to detect the language for a block of text (auto detection)
    
    if you use this API call to detect the source language, it will return the source language code (2 or 3
    letter ISO code), or a blank response if it cannot detect or guess the language. 
    
    You can use this API to do the following tasks:
    
    * get a list of machine translation servers and their APIs for a sl-->tl language pair
    * find out if a specific language is associated with a domain, eg. lemonde.fr = french
    * test a text to automatically guess its source language (about 90% reliable)
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        list = self.request.get('list')
        domain = self.request.get('domain')
        text = self.request.get('text')
        if list == 'y':
            self.picklist()
        elif len(text) < 1 and len(sl) > 0 and len(tl) > 0:
            self.mt(sl, tl)
        elif len(tl) < 1 and len(domain) < 1 and len(text) < 1:
            www.serve(self, self.__doc__)
            self.response.out.write('<form action=/language method=get accept-charset=utf-8>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Set Target Language</td><td><input type=text name=tl maxlength=3 size=3></td></tr>')
            self.response.out.write('<tr><td>Web Domain (e.g. www.xyz.com)</td><td><input type=text name=domain></td></tr>')
            self.response.out.write('<tr><td colspan=2>Detect Source Language For A Block of Text<br><textarea name=text></textarea></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr>')
            self.response.out.write('</table></form>')
        else:
            if len(tl) > 0:
                referrer = self.request.referrer
                cookies = Cookies(self)
                cookies['tl'] = tl
                self.redirect('/')
            else:
                sl = Domains.language(d=domain, text=text)
                self.response.headers['Content-Type']='text/plain'
                self.response.out.write(sl)
    def mt(self, sl, tl):
        self.response.headers['Content-Type']='text/plain'
        if sl == 'es' and (tl == 'ca' or tl == 'pt' or tl == 'fr' or tl == 'oc' or tl == 'eu'):
            self.response.out.write('apertium, googlejson, ' + m.apertium_url + '\n')
        elif sl == 'fr' and (tl == 'es' or tl == 'ca'):
            self.response.out.write('apertium, googlejson, ' + m.apertium_url + '\n')
        else:
            self.response.out.write('google, googlejson, ' + m.google_url + '\n')
    def picklist(self):
        langs = languages.getlist(english='y')
        langkeys = langs.keys()
        langkeys.sort()
        results = list()
        for l in langkeys:
            language = lx()
            language.code = l
            language.name = langs[l]
            results.append(language)
        d = DeepPickle()
        txt = d.pickleTable(results, 'json')
        self.response.headers['Content-Type']='application/json'
        self.response.out.write(txt)
      
application = webapp.WSGIApplication([('/language', ProcessForm)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

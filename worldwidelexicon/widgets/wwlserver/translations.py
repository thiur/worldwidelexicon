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

Copyright (c) 1998-2010, Worldwide Lexicon Inc, Brian S McConnell.
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
#
# import Google App Engine modules
#
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
#
# import standard Python modules
#
import demjson
import urllib
import string
import md5
import datetime
import time
import pydoc
import codecs
import types
#
# import WWL and third party modules
#
from deeppickle import DeepPickle
from mt import MTWrapper
from webappcookie import Cookies
from www import www
from geo import geo
from akismet import Akismet
from transcoder import transcoder
from database import Cache
from database import Comment
from database import Directory
from database import Log
from database import Search
from database import Translation
from database import languages
from database import Users
from database import UserScores
from database import Settings
from language import TestLanguage
from lsp import LSP
from ip import ip

def clean(text, charset=''):
    return transcoder.clean(text, charset)

class tx():
    sl = ''

class GetTranslations(webapp.RequestHandler):
    """
    
    <h3>/q (get translations)</h3>
    
    This API handler returns a list of translations that match your search
    criteria. The request handler expects the following parameters:<p>
    
    <ul><li>sl : source language (ISO language code), required</li>
    <li>tl : target language (ISO language code), required</li>
    <li>st : source text (Unicode, UTF-8 encoding), either st or md5hash must be present</li>
    <li>md5hash : MD5 hashkey generated from source text (more efficient when retrieving archived translations for large texts, except auto-fallback to machine translation will not work</li>
    <li>allow_anonymous : (y/n) include anonymous translations (enabled by default)</li>
    <li>allow_machine : (y/n) include machine translations (enabled by default)</li>
    <li>allow_unscored : (y/n) include unscored human translations (enabled by default)</li>
    <li>minimum_score : minimum score (0 to 5 scale)</li>
    <li>fuzzy : (y/n), if yes searches for the word or phrase within translations
                    (e.g. fuzzy=y and st=hello world will find any translations whose
                    source text contains the phrase 'hello world'), currently limited
                    to searching for short phrases of 1 to 4 words within larger texts.</li>
    <li>lsp : language service provider (for on demand professional translation)</li>
    <li>lspusername : LSP username</li?
    <li>lsppw : LSP password</li>
    <li>mtengine : optional machine translation engine to call out to for machine translations
                    if no human translations are available (options are: google, apertium,
                    moses, with more coming soon)</li>
    <li>ttl : cache time to live (for professional translations, in seconds</li>
    <li>output : output format (xml, rss, json, po, xliff)</li></ul><p>
    
    The request handler returns the recordset in the desired format (xml if not specified)
     
    """
    def get(self):
        """Processes HTTP GET calls"""
        self.requesthandler()
    def post(self):
        """Processes HTTP POST calls"""
        self.requesthandler()
    def requesthandler(self):
        """Combined request handler, processes both GET and POST calls."""
        cookies = Cookies(self)
        d = DeepPickle()
        d.rss_title = 'Worldwide Lexicon Translations'
        d.rss_item_title = 'st'
        d.rss_item_description = 'tt'
        d.rss_item_guid = 'guid'
        d.rss_item_url = 'md5hash'
        d.rss_item_author = 'username'
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('st')
        st = clean(st)
        try:
            st = unicode(st, 'utf-8', 'ignore')
            #st = urllib.unquote_plus(st)
        except:
            pass
        domain = self.request.get('domain')
        url = self.request.get('url')
        md5hash = self.request.get('md5hash')
        fuzzy = self.request.get('fuzzy')
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        mtengine = self.request.get('mtengine')
        ip = self.request.get('ip')
        hostname = self.request.get('hostname')
        if len(ip) > 0:
            remote_addr = ip
        try:
            ttl = int(self.request.get('ttl'))
            if ttl < 1:
                ttl = 7200
        except:
            ttl = 7200
        remote_addr = self.request.remote_addr
        if md5hash == 'test':
            test = True
        else:
            test = False
        username = ''
        try:
            session = cookies['session']
            if len(session) > 0:
                username = memcache.get('sessions|' + session)
                if username is None:
                    username = ''
        except:
            pass
        try:
            allow_anonymous = cookies['allow_anonymous']
        except:
            allow_anonymous = self.request.get('allow_anonymous')
        doc = self.request.get('doc')
        if string.lower(allow_anonymous) == 'n':
            display_anonymous = False
        else:
            display_anonymous = True
        try:
            allow_machine = cookies['allow_machine']
        except:
            allow_machine = self.request.get('allow_machine')
        if string.lower(allow_machine) == 'n':
            display_machine = False
        else:
            display_machine = True
        try:
            allow_unscored = cookies['allow_unscored']
        except:
            allow_unscored = self.request.get('allow_unscored')
        if string.lower(allow_unscored) == 'n':
            display_unscored = False
        else:
            display_unscored = True
        try:
            max_blocked_votes = cookies['max_blocked_votes']
        except:
            max_blocked_votes = self.request.get('max_blocked_votes')
        if len(max_blocked_votes) > 0:
            max_blocked_votes = int(max_blocked_votes)
        else:
            max_blocked_votes = 3
        output = self.request.get('output')
        if len(output) < 1:
            output='xml'
        try:
            minimum_score = float(self.request.get('minimum_score'))
            require_score = True
        except:
            minimum_score = float(0)
            require_score = False
        validquery = False
        if len(sl) > 0 and len(tl) > 0:
            if len(st) > 0 or len(md5hash) > 3:
                validquery = True
            else:
                validquery = True
        if validquery:
            results = None
            if len(hostname) > 0:
                Directory.hostname(hostname, sl, tl, remote_addr=remote_addr)
            if len(lsp) > 0:
                result = LSP.get(sl,tl,st,domain=domain,url=url,lsp=lsp,lspusername=lspusername,lsppw=lsppw, ttl = ttl)
                if type(result) is str:
                    tt = result
                    guid = ''
                else:
                    tt = result.get('tt','')
                    guid = result.get('guid','')
                t = tx()
                t.guid = guid
                t.sl = sl
                t.tl = tl
                t.st = clean(st)
                t.tt = clean(tt)
                t.domain = domain
                t.url = url
                t.username = lsp
                t.professional = True
                t.spam = False
                t.anonymous = False
                translations = list()
                translations.append(t)
                if len(translations) < 1:
                    results = None
                else:
                    results = 'Found translations'
            if len(url) > 0:
                p = dict()
                p['remote_addr']=self.request.remote_addr
                p['url']=url
                p['sl']=sl
                p['tl']=tl
                taskqueue.add(url='/log', params=p)
            if results is None:
                results = Translation.fetch(sl=sl, st=st, tl=tl, domain='', url=url, userip=remote_addr, allow_machine=allow_machine, allow_anonymous=allow_anonymous, min_score=minimum_score, max_blocked_votes=max_blocked_votes, fuzzy=fuzzy, lsp=lsp, lspusername=lspusername, lsppw=lsppw)
                translations = list()
                for r in results:
                    try:
                        t = tx()
                        t.sl = r.sl
                        t.tl = r.tl
                        try:
                            t.st = codecs.encode(r.st, 'utf-8')
                        except:
                            t.st = clean(r.st)
                        try:
                            t.tt = codecs.encode(r.tt, 'utf-8')
                        except:
                            t.tt = clean(r.tt)
                        t.domain = r.domain
                        t.url = r.url
                        t.anonymous = r.anonymous
                        t.username = r.username
                        t.remote_addr = r.remote_addr
                        t.date = str(r.date)
                        t.avgscore = r.avgscore
                        t.scores = r.scores
                        try:
                            t.spam = r.spam
                        except:
                            t.spam = False
                        t.professional = r.professional
                        translations.append(t)
                    except:
                        pass
            if len(results) < 1:
                try:
                    st = urllib.unquote(st)
                except:
                    pass
                mt = MTWrapper()
                tt = mt.getTranslation(sl=sl, tl=tl, st=st, mtengine=mtengine, userip=remote_addr)
                if len(mtengine) > 0:
                    engine = mtengine
                else:
                    engine = mt.pickEngine(sl=sl, tl=tl)
                translations = list()
                t = tx()
                t.st=st
                t.sl=sl
                t.tl=tl
                try:
                    t.tt=urllib.unquote_plus(tt)
                except:
                    t.tt=tt
                t.username='robot'
                t.mtengine=engine
                translations.append(t)
            d.autoheader = True
            self.response.headers['Accept-Charset']='utf-8'
            if output=='xml' or output=='rss':
                self.response.headers['Content-Type']='text/xml'
            elif output=='json' or output=='po':
                self.response.headers['Content-Type']='text/plain'
            else:
                self.response.headers['Content-Type']='text/html'
            text = d.pickleTable(translations, output)
            self.response.out.write(text)
        else:
            doc_text = self.__doc__
            t = '<table><form action=/q method=post accept-charset=utf-8>'
            t = t + '<tr><td>Source Language</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Source Text</td><td><textarea name=st rows=4 cols=40></textarea></td></tr>'
            t = t + '<tr><td>Source Text MD5 Hash</td><td><input type=text name=md5hash></td></tr>'
            t = t + '<tr><td>URL to request translations for</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td>Display Anonymous Texts (y/n)</td><td><input type=text name=allow_anonymous></td></tr>'
            t = t + '<tr><td>Display Machine Texts (y/n)</td><td><input type=text name=allow_machine></td></tr>'
            t = t + '<tr><td>Minimum Score (0 to 5)</td><td><input type=text name=minimum_score></td></tr>'
            t = t + '<tr><td>Fuzzy Search</td><td><input type=text name=fuzzy value=n></td></tr>'
            t = t + '<tr><td>Machine Translation Engine</td><td>'
            t = t + '<select name=mtengine><option selected value="">--Automatic--</option>'
            t = t + '<option value=google>Google</option>'
            t = t + '<option value=apertium>Apertium</option>'
            t = t + '<option value=moses>Moses</option>'
            t = t + '</select></td></tr>'
            t = t + '<tr><td>Language Servuce Provider (lsp)</td><td><input type=text name=lsp></td></tr>'
            t = t + '<tr><td>LSP Username</td><td><input type=text name=lspusername></td></tr>'
            t = t + '<tr><td>LSP Password</td><td><input type=text name=lsppw></td></tr>'
            t = t + '<tr><td>Cache Time to Live (seconds)</td><td><input type=text name=ttl></td></tr>'
            t = t + '<tr><td>Output Format</td><td><input type=text name=output value=rss></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=SEARCH></td></tr>'
            t = t + '</table></form>'
            www.serve(self,t, sidebar=doc_text,title = '/q')

class SubmitTranslation(webapp.RequestHandler):
    """
    
    <h3>/submit : (submit a translation)</h3>
    
    This web service API call stores newly submitted translations to the datastore. 
    It expects the following parameters:<p>
    
    <ul><li>sl - source language (ISO language code), required</li>
    <li>tl - target language (ISO language code), required</li>
    <li>st - source text (UTF-8 encoded), required</li>
    <li>tt - translated text (UTF-8 encoded), required</li>
    <li>domain - site domain or API key, optional but recommended (submit in nnn.com format)</li>
    <li>url - parent URL of source document, optional but recommended (submit full permalink)</li>
    <li>username - WWL or remote username, optional (system allows anonymous translations)</li>
    <li>facebookid - optional facebook id</li>
    <li>profile_url - optional profile url</li>
    <li>pw - WWL or remote user password</li>
    <li>proxy - if submission is being submitted via a proxy gateway, default = n if omitted
            (in proxy mode, we use you are filtering submissions upstream and will accept
            whatever username you provide)</li>
    <li>session - session key (cookie, stored whenever user logs into system)</li>
    <li>apikey - API key (for trusted submitters and LSPs)</li>
    <li>ip - user IP address (if proxy=y, include this field to provide the user's IP address</li></ul>
    
    The API call returns a text/plain object, with either an ok response or an error message.<p>
    
    <blockquote>IMPORTANT: always use UTF-8 encoding when submitting data. If you are generating an HTML
    form that points back to the WWL server, be sure to include accept-charset=utf-8 in the
    <form > tag. If you are submitting data from a separate application, be sure to set the
    accept-charset=utf-8 header in the HTTP call, and to encode characters using UTF-8. If
    you do not do this consistently, you will see character encoding errors or receive
    garbage characters in your translations. Use UTF-8 everywhere, and specifically do not
    use language specific character sets. </blockquote>
    
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        """Combined GET and POST request handler """
        validquery = True
        emptyform = False
        remote_addr = self.request.remote_addr
        userip = self.request.get('ip')
        if len(userip) > 3:
            remote_addr = userip
        cookies = Cookies(self,max_age=3600)
        try:
            session = cookies['session']
        except:
            session = ''
        validuser = False
        username = self.request.get('username')
        proxy = self.request.get('proxy')
        pw = self.request.get('pw')
        apikey = self.request.get('apikey')
        if len(username) > 0 and len(pw) > 0:
            sessinfo = Users.auth(username, pw, '', remote_addr)
            if type(sessinfo) is dict:
                username = sessinfo['username']
                session = sessinfo['session']
                validuser = True
                cookies['session']=sessinfo['session']
        if len(username) > 0 and proxy == 'y':
            validuser = True
        if len(session) > 0 and not validuser:
            username = memcache.get('sessions|' + session)
            if username is None:
                username = ''
            else:
                validuser = True
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        domain = self.request.get('domain')
        url = self.request.get('url')
        title = clean(self.request.get('title'))
        ttitle = clean(self.request.get('ttitle'))
        description = clean(self.request.get('description'))
        tdescription = clean(self.request.get('tdescription'))
        facebookid = self.request.get('facebookid')
        profile_url = self.request.get('profile_url')
        headers = self.request.headers
        headerkeys = headers.keys()
        headerkeys.sort()
        lt = ''
        for h in headerkeys:
             lt = lt + h + ' : ' + headers[h] + '\n'
        try:
            charset = string.lower(headers['Accept-Charset'])
        except:
            charset = ''
        st = self.request.get('st')
        st = clean(st, charset=charset)
        tt = self.request.get('tt')
        tt = clean(tt, charset=charset)
        lt = lt + 'sl=' + sl + '\n'
        lt = lt + 'tl=' + tl + '\n'
        lt = lt + 'domain=' + domain + '\n'
        lt = lt + 'url=' + url + '\n'
        try:
            lt = lt + 'st=' + st + '\n'
        except:
            lt = lt + 'st=ERROR\n'
        try:
            lt = lt + 'tt=' + tt + '\n'
        except:
            lt = lt + 'tt=ERROR\n'
        Log.log('/submit', lt)
        if len(sl) < 1 or len(tl) < 1 or len(st) < 1 or len(tt) < 1:
            validquery=False
        if len(sl) < 1 and len(tl) < 1:
            emptyform = True
        doc = self.request.get('doc')
        lsp = self.request.get('lsp')
        if doc == 'y':
            display_docs = True
        else:
            display_docs = False
        akismetapi = Settings.get('akismet')
        if akismetapi is not None:
            if len(akismetapi) > 0:
                a = Akismet()
                a.setAPIKey(akismetapi)
                try:
                    a.verify_key()
                    data = dict()
                    data['user_ip']= remote_addr
                    try:
                        data['user_agent'] = self.request.headers['User-Agent']
                    except:
                        pass
                    if a.comment_check(tt, data):
                        spam = True
                    else:
                        spam = False
                except:
                    spam = False
            else:
                spam = False
        else:
            spam = False
        if len(tl) > 0 and len(tt) > 5:
            tl2 = TestLanguage.language(d='', text=tt)
            if tl != tl2:
                spam = True
        location = geo.get(remote_addr)
        if location is not None:
            city = location['city']
            state = location['state']
            country = location['country']
            latitude = location['latitude']
            longitude = location['longitude']
        sys_allow_anonymous = 'y'
        if sys_allow_anonymous is not None and sys_allow_anonymous == 'n' and validuser == False:
            valid_query = False
        result = False
        if len(url) > 0 and not spam:
            p = dict()
            p['url']=url
            p['sl']=sl
            p['tl']=tl
            p['action']='translate'
            p['remote_addr']=self.request.remote_addr
            taskqueue.add(url = '/log', params = p)
        result = Translation.submit(sl=sl, st=st, tl=tl, tt=tt, username=username, remote_addr=remote_addr, domain=domain, url=url, city=city, state=state, country=country, latitude=latitude, longitude=longitude, lsp=lsp, facebookid = facebookid, profile_url=profile_url, spam=spam, proxy=proxy, apikey=apikey)
        if len(title) > 0 and len(url) > 0:
            p = dict()
            p['remote_addr'] = remote_addr
            p['username'] = username
            p['domain'] = domain
            p['url'] = url
            p['title'] = title
            p['ttitle'] = ttitle
            p['description'] = description
            p['tdescription'] = tdescription
            p['sl']=sl
            p['tl']=tl
            try:
                taskqueue.add(url = '/share', params = p)
            except:
                pass
        if len(url) > 0 and string.count(url, 'https://') < 1:
            if string.count(url, 'http://') < 1:
                url = 'http://' + url
            p = dict()
            p['url']= url
            if len(username) > 0:
                p['email']=username
            else:
                p['email']=remote_addr
            taskqueue.add(url = '/translate/shortcut', params = p)
        callback = self.request.get('callback')
        if len(callback) > 0:
            self.redirect(callback)
        else:
            if len(result) > 0:
                p = dict()
                p['guid'] = result
                taskqueue.add(url = '/ngrams', params=p)
                self.response.out.write('ok\n' + result)
            elif not emptyform:
                self.error(500)
                self.response.out.write('error\ninvalid user')
            else:
                pass
            if emptyform:
                doc_text = self.__doc__
                t = '<table>'
                t = t + '<form action=/submit method=post accept-charset=utf-8>'
                t = t + '<tr><td>Source Language</td><td><input type=text name=sl value=en></td></tr>'
                t = t + '<tr><td>Target Language</td><td><input type=text name=tl value=es></td></tr>'
                t = t + '<tr><td>Source Text</td><td><input type=text name=st value=\"' + st + '\"></td></tr>'
                t = t + '<tr><td>Translation</td><td><input type=text name=tt value=\"' + tt + '\"></td></tr>'
                t = t + '<tr><td>Domain</td><td><input type=text name=domain value=\"' + domain + '\"></td></tr>'
                t = t + '<tr><td>URL</td><td><input type=text name=url value=\"' + url + '\"></td></tr>'
                t = t + '<tr><td>WWL Username</td><td><input type=text name=username></td></tr>'
                t = t + '<tr><td>WWL Password</td><td><input type=password name=pw></td></tr>'
                t = t + '<tr><td>Proxy Mode (y/n)</td><td><input type=text name=proxy value=n></td></tr>'
                t = t + '<tr><td>Proxy User IP Address</td><td><input type=text name=ip></td></tr>'
                t = t + '<tr><td>API Key</td><td><input type=text name=apikey></td></tr>'
                t = t + '<tr><td>Output format</td><td><input type=text name=output value=text></td></tr>'
                t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
                t = t + '</table></form>'
                www.serve(self,t, sidebar=doc_text, title = '/submit')
    
class SimpleTranslation(webapp.RequestHandler):
    """
    <h3>/t : Simple Translation Service</h3>

    This request handler implements the /t/*/*/* web service which provides a simple
    text-only interface for retrieving translations from WWL. The web service is called via
    a RESTful interface as follows:<p>
    
    /t/{source_language}/{target_language}/{escape encoded text}<p>
    or<p>
    /t/{source_language}/{target_language}<p>
    or<p>
    /t
    
    with the parameters<p>
    
    <ul><li>sl = source language code (if not in URL)</li>
    <li>tl = target language code (if not in URL)</li>
    <li>st = source text (UTF-8 or ASCII only, no other encodings supported, if not in URL)</li>
    <li>allow_anonymous = y/n (allow anonymous translations, default = y)</li>
    <li>allow_machine = y/n (allow machine translations, default = y)</li>
    <li>min_score = minimum average quality score (0 to 5, default 0)</li>
    <li>domain = optional domain</li>
    <li>url = optional url</li>
    <li>lsp = name of professional translation service provider (will request a professional translation)</li>
    <li>lspusername = username to submit to professional translation svc (overrides system default)</li>
    <li>lsppw = password or API key to submit to professional translation svc (overrides system default)</li>
    <li>queue = add translation to translation queue for third party service (e.g. beextra.org)</li>
    <li>mtengine = request translation via a specific machine translation service, if not specified will
                select MT engine automatically using defaults in mt.py</li>
    <li>ttl = cache time to live (for professional translations), in seconds</li>
    <li>ip = dotted IP address or prefix (e.g. ip=206.1.2) to limit results to translations submitted from
                a specific IP address or range (so you can ignore submissions that were not posted from
                a trusted gateway you control)</li>
    <li>output = text|html|xml|rss|json|google (google will mimic Google Translate API and response format)</li></ul>
    
    The request handler will return the best available translation in simple HTML by
    default. If you need a full revision history, you should use the /q interface.<p>
    
    This interface makes it easy to merge translations into web documents as they are
    served, as it can be used as a type of server side include. This enables a website
    to exert direct control over how translations are displayed, to cache them locally
    and host the translations on the same publishing or web application environment.
    Note that this can also be used to localize a web interface as it provides a simple
    gettext() style interface for fetching a translation for a string.<p>

    NOTE: we _strongly_ recommend that you use the POST method to submit texts for translation.
    You can use HTTP GET for requests, but you need to be very careful to correctly encoded texts.<p>
    """
    def get(self, sl='', tl='', st=''):
        self.requesthandler(sl, tl, st)
    def post(self, sl='', tl='', st=''):
        self.requesthandler(sl, tl, st)
    def requesthandler(self, sl='', tl='', st=''):
        if len(sl) < 1:
            sl = self.request.get('sl')
        if len(tl) < 1:
            tl = self.request.get('tl')
        if len(st) < 1:
            st = self.request.get('st')
        domain = self.request.get('domain')
        url = self.request.get('url')
        userip = self.request.remote_addr
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        allow_anonymous = self.request.get('allow_anonymous')
        allow_machine = self.request.get('allow_machine')
        min_score = self.request.get('min_score')
        domain = self.request.get('domain')
        url = self.request.get('url')
        output = self.request.get('output')
        mtengine = self.request.get('mtengine')
        queue = self.request.get('queue')
        try:
            ttl = int(self.request.get('ttl'))
            if ttl < 1:
                ttl = 7200
        except:
            ttl = 7200
        ip = self.request.get('ip')
        if len(ip) < 1:
            ip = self.request.remote_addr
        hostname = self.request.get('hostname')
        st = transcoder.clean(st)
        st = string.replace(st, '+', ' ')
        username = ''
        guid = ''
        if output == 'google':
            q = self.request.get('q')
            langpair = self.request.get('langpair')
            if len(q) > 0:
                st = q
            if len(langpair) > 0:
                langs = string.split(langpair, '|')
                if len(langs) == 2:
                    sl = langs[0]
                    tl = langs[1]
        m = md5.new()
        m.update(sl)
        m.update(tl)
        m.update(st)
        m.update(allow_anonymous)
        m.update(allow_machine)
        m.update(lsp)
        md5hash = str(m.hexdigest())
        if len(output) < 2:
            output = 'text'
        text = memcache.get('/t/' + md5hash + '/' + output)
        self.response.headers['Accept-Charset'] = 'utf-8'
        createdon = ''
        username = ''
        remote_addr = ''
        city = ''
        country = ''
        timestamp = ''
        if text is not None:
            if output == 'xml' or output == 'rss':
                self.response.headers['Content-Type']='text/xml'
            elif output == 'html':
                self.response.headers['Content-Type']='text/html'
            else:
                self.response.headers['Content-Type']='text/plain'
            self.response.out.write(text)
            return
        if len(hostname) > 0:
            Directory.hostname(hostname, sl, tl, remote_addr=ip)
        if len(tl) > 0 and len(st) > 0:
            tt = ''
            if len(lsp) > 0:
                translation = LSP.get(sl, tl, st, domain=domain, url=url, lsp=lsp, lspusername=lspusername, lsppw=lsppw, ttl=ttl)
                if type(translation) is str:
                    tt = translation
                    guid = ''
                else:
                    tt = translation.get('tt','')
                    guid = translation.get('guid','')
                username = lsp
            if len(tt) < 1:
                m = md5.new()
                m.update(st)
                md5hash = str(m.hexdigest())                
                tdb = db.Query(Translation)
                tdb.filter('sl = ', sl)
                tdb.filter('tl = ', tl)
                tdb.filter('md5hash = ', md5hash)
                tdb.filter('professional = ', True)
                item = tdb.get()
                if item is not None:
                    tt = codecs.encode(item.tt, 'utf-8')
                    guid = item.guid
                    username = item.username
                    city = item.city
                    country = item.country
                    timestamp = str(item.date)
            if len(tt) < 1:
                tdb = db.Query(Translation)
                tdb.filter('sl = ', sl)
                tdb.filter('tl = ', tl)
                tdb.filter('md5hash = ', md5hash)
                tdb.order('-date')
                results = tdb.fetch(limit=20)
                if len(min_score) > 0:
                    try:
                        min_score = float(min_score)
                    except:
                        min_score = None
                else:
                    min_score = None
                for r in results:
                    if len(tt) < 1 and len(r.tt) > 0:
                        if allow_anonymous == 'n':
                            if r.anonymous == False or len(r.username) > 0:
                                tt = codecs.encode(r.tt, 'utf-8')
                                guid = r.guid
                                username = r.username
                                city = r.city
                                country = r.country
                                timestamp = str(r.date)
                        else:
                            tt = codecs.encode(r.tt, 'utf-8')
                            guid = r.guid
                            username = r.username
                            city = r.city
                            country = r.country
                            timestamp = str(r.date)
            if len(tt) < 1 and allow_machine != 'n':
                mt = MTWrapper()
                mtengine = mt.pickEngine(sl,tl)
                tt = mt.getTranslation(sl, tl, st, domain=domain, url=url)

            # phasing out call to Translation.lucky() due to issues with properly finding user generated translations
            #
            # if len(tt) < 1:
            #    tt = Translation.lucky(sl=sl, tl=tl, st=st, allow_anonymous=allow_anonymous, allow_machine=allow_machine, min_score=min_score, output=output, lsp=lsp, lspusername=lspusername, lsppw = lsppw, mtengine=mtengine, queue=queue, ip=ip, userip=userip, hostname=hostname)
            #
            if output == 'text':
                self.response.headers['Content-Type']='text/plain'
                self.response.out.write(tt)
                text = tt
                memcache.set('/t/' + md5hash + '/text', tt, 1200)
            elif output == 'google':
                self.response.headers['Content-Type']='text/javascript'
                response='{"responseData": {"translatedText":"[translation]"},"responseDetails": null, "responseStatus": 200}'
                tt = string.replace(tt,'\"', '\'')
                text = string.replace(response,'[translation]', tt)
                self.response.out.write(text)
            else:
                d = DeepPickle()
                d.autoheader=True
                t = tx()
                t.sl = sl
                t.tl = tl
                t.st = st
                t.tt = tt
                t.guid = guid
                t.username = username
                t.mtengine = mtengine
                t.remote_addr = remote_addr
                t.date = timestamp
                t.city = city
                t.country = country
                results = list()
                results.append(t)
                if output == 'xml' or output == 'rss' or output == 'xliff':
                    self.response.headers['Content-Type']='text/xml'
                    self.response.out.write(d.pickleTable(results, output))
                elif output == 'json':
                    self.response.headers['Content-Type']='text/javascript'
                    self.response.out.write(d.pickleTable(results, output))
                elif output == 'po':
                    self.response.headers['Content-Type']='text/plain'
                    self.response.out.write(d.pickleTable(results, output))
                else:
                    self.response.headers['Content-Type']='text/html'
                    self.response.out.write(text)
                if len(results) > 0:
                    memcache.set('/t/' + md5hash + '/' + output, d.pickleTable(results,output), 300)
        else:
            doc_text = self.__doc__
            t = '<table><form action=/t method=get accept-charset=utf-8>'
            t = t + '<tr><td>Source Language</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td colspan><b>Text To Translate</b><br><textarea name=st></textarea></td></tr>'
            t = t + '<tr><td>Optional Domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>Optional Source URL</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td>Language Service Provider (request pro translation)</td>'
            t = t + '<td><input type=text name=lsp></td></tr>'
            t = t + '<tr><td>LSP Username</td><td><input type=text name=lspusername></td></tr>'
            t = t + '<tr><td>LSP Password</td><td><input type=text name=lsppw></td></tr>'
            t = t + '<tr><td>Cache Time to Live (seconds)</td><td><input type=text name=ttl></td></tr>'
            t = t + '<tr><td>Limit Results By IP Address or Pattern</td><td><input type=text name=ip></td></tr>'
            t = t + '<tr><td>Allow Machine Translation (y/n)</td><td><input type=text name=allow_machine value=y></td></tr>'
            t = t + '<tr><td>Allow Anonymous Translation (y/n)</td><td><input type=text name=allow_anonymous value=y></td></tr>'
            t = t + '<tr><td>Output Format</td><td><input type=text name=output value=text></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=GO></td></tr>'
            t = t + '</form></table>'
            www.serve(self,t, sidebar = doc_text, title='/t')

class LogQueries(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = self.request.get('url')
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        action = self.request.get('action')
        remote_addr = clean(self.request.get('remote_addr'))
        languages = string.split(self.request.get('languages'),',')
        if len(remote_addr) > 0:
            location = geo.get(remote_addr)
            city = location.get('city','')
            state = location.get('state','')
            country = location.get('country', '')
            try:
                latitude = location['latitude']
                longitude = location['longitude']
            except:
                latitude = None
                longitude = None
            try:
                Search.log(url, sl=sl, tl=tl, action=action, remote_addr = remote_addr, city=city, state=state, country=country, latitude=latitude,longitude=longitude)
            except:
                pass
        self.response.out.write('ok')
        
class BatchTranslation(webapp.RequestHandler):
    """
    /batch

    Batch translation request handler. This request handler allows a client to submit a batch of texts to
    be translated, and to requery in a separate transaction if desired. This request handler will spawn
    a number of parallel queries that, in turn, write back to memcached. This allows for fast response
    times on queries for a large number of texts. It expects the following parameters:<p>

    <ul><li>sl = source language</li>
    <li>tl = target language</li>
    <li>st0..199 = source text to translate</li>
    <li>allow_machine = y/n (use machine translation)</li>
    <li>lsp = name of LSP, if requesting professional translations</li>
    <li>lspusername = username for LSP query</li>
    <li>lsppw = pw or API key for LSP query</li>
    <li>guid = MD5hash (if repeating a recently submitted query)</li>
    <li>async = y/n (if yes, returns an MD5hash, and expects user to re-query after some delay)</li>
    <li>output = xml, rss, or json</li></ul>
    
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        #
        # capture form fields
        #
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        allow_machine = self.request.get('allow_machine')
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        remote_addr = self.request.get('remote_addr')
        guid = self.request.get('guid')
        query = self.request.get('query')
        output = self.request.get('output')
        if len(guid) > 8 and query != 'y':
            ctr = 0
            while ctr < 200:
                #
                # check memcache for list of recently cached translations
                #
                text = memcache.get('/batch/' + guid + '/' +output + '/' + str(ctr))
                if text is not None:
                    self.response.out.write(text)
                ctr = ctr + 1
        else:
            #
            # capture list of translation requests from form
            #
            if len(sl) > 1 and query != 'y':
                st = self.request.get('st')
                m = md5.new()
                m.update(remote_addr)
                m.update(sl)
                m.update(st)
                m.update(str(datetime.datetime.now()))
                md5hash = str(m.hexdigest())
                ctr = 0
                st = dict()
                while ctr < 200:
                    st[ctr]=urllib.unquote_plus(self.request.get('st' + str(ctr)))
                    ctr = ctr + 1
                ctr = 0
                #
                # generate response header, based on desired output format
                #
                if output == 'xml' or output == 'rss':
                    self.response.headers['Content-Type']='text/xml'
                    self.response.out.write('<?xml version=\"1.0\" encoding="utf-8"?>')
                    if output == 'xml':
                        self.response.out.write('<translations>')
                    else:
                        self.response.out.write('<rss version=\"2.0\"><channel>')
                        self.response.out.write('<title>Translations</title>')
                elif output == 'html':
                    self.response.headers['Content-Type']='text/html'
                else:
                    self.response.headers['Content-Type']='text/plain'
                while ctr < 200:
                    #
                    # generate list of translations from batch request
                    #
                    stext = st.get(ctr)
                    if len(stext) > 1:
                        # make call to Translation.lucky() method (this is being deprecated and will be replaced soon)
                        tt = Translation.lucky(sl=sl, tl=tl, st=stext, output=output)
                        if output == 'rss':
                            tt = '<item><title>' + stext + '</title><description>' + tt + '</description></item>'
                        elif output == 'xml':
                            tt = '<item><sl>' + sl + '</sl><tl>' + tl + '</tl><st>' + stext + '</st><tt>' + tt + '</tt></item>'
                        self.response.out.write(tt)
                    ctr = ctr + 1
                if output == 'xml' or output == 'rss':
                    if output == 'rss':
                        self.response.out.write('</channel></rss>')
                    else:
                        self.response.out.write('</translations>')
            else:
                #
                # form fields were empty, so generate a blank form instead
                #
                doc_text = self.__doc__
                t = '<table><form action=/batch method=get>'
                t = t + '<tr><td>Async Query</td><td><input type=text name=async value=n></td></tr>'
                t = t + '<tr><td>Source Language</td><td><input type=text name=sl></td></tr>'
                t = t + '<tr><td>Target Language</td><td><input type=text name=tl></td></tr>'
                t = t + '<tr><td>Output Format</td><td><input type=text name=output value=rss></td></tr>'
                ctr = 0
                while ctr < 20:
                    t = t + '<tr><td>Source Text #' + str(ctr+1) + '</td>'
                    t = t + '<td><input type=text name=st' + str(ctr) + '></td></tr>'
                    ctr = ctr + 1
                t = t + '<tr><td colspan=2><input type=submit value="OK"></td></tr>'
                t = t + '</form></table>'
                www.serve(self,t, sidebar=doc_text)
#
# Main request handler, decides which request handler to call based on the URL pattern
#

class IndexNgrams(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        guid = self.request.get('guid')
        result = Translation.generatengrams(guid)
        self.response.out.write('ok')

class RevisionHistory(webapp.RequestHandler):
    """
    /r

    This request handler returns the revision history (newest-oldest) for
    all translations associated with a particular source text. The results
    can be filtered by source language, target language, or domain. It assumes
    that other filtering criteria will be applied by the requester.

    It expects the following parameters:

    st = source text (utf8 encoding)
    sl = optional source language code
    tl = optional target language code
    domain = optional domain to limit results too (e.g. foonews.com)
    output = output format (json, xml, rss, po, xliff)
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        st = clean(self.request.get('st'))
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        domain = self.request.get('domain')
        output = self.request.get('output')
        m = md5.new()
        m.update(st)
        md5hash = str(m.hexdigest())
        if len(output) < 1:
            output = 'json'
        if len(st) > 0:
            text = memcache.get('/revisionhistory/' + md5hash + '/' + sl + '/' + tl + '/' + domain + '/' + output)
            if text is not None:
                self.response.out.write(text)
            else:
                tdb = db.Query(Translation)
                tdb.filter('md5hash = ', md5hash)
                if len(sl) > 0:
                    tdb.filter('sl = ', sl)
                if len(tl) > 0:
                    tdb.filter('tl = ', tl)
                if len(domain) > 0:
                    tdb.filter('domain = ', domain)
                tdb.order('-date')
                results = tdb.fetch(limit=500)
                translations = list()
                for r in results:
                    t = tx()
                    t.guid = r.guid
                    t.sl = r.sl
                    t.tl = r.tl
                    try:
                        t.st = codecs.encode(r.st, 'utf-8')
                    except:
                        t.st = clean(r.st)
                    try:
                        t.tt = codecs.encode(r.tt, 'utf-8')
                    except:
                        t.tt = clean(r.tt)
                    t.anonymous = r.anonymous
                    t.avgscore = r.avgscore
                    t.scores = r.scores
                    t.city = r.city
                    t.country = r.country
                    t.username = r.username
                    t.remote_addr = r.remote_addr
                    t.professional = r.professional
                    t.date = r.date
                    t.reviewed = r.reviewed
                    t.avgscore = r.avgscore
                    t.date = r.date
                    try:
                        t.spam = r.spam
                    except:
                        t.spam = False
                    t.domain = r.domain
                    t.url = r.url
                    translations.append(t)
                d = DeepPickle()
                d.autoheader = True
                if output == 'xml' or output == 'rss' or output == 'xliff':
                    self.response.headers['Content-Type']='text/xml'
                elif output == 'json':
                    self.response.headers['Content-Type']='text/javascript'
                elif output == 'po':
                    self.response.headers['Content-Type']='text/plain'
                else:
                    self.response.headers['Content-Type']='text/html'
                self.response.out.write(d.pickleTable(translations,output))
        else:
            doc_text = self.__doc__
            t = '<table><form action=/r method=get accept-charset=utf-8>'
            t = t + '<tr><td>Source Text (UTF8)</td><td><input type=text name=st></td></tr>'
            t = t + '<tr><td>Source Language (optional)</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language (optional)</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Domain (optional)</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>Output Format</td><td><input type=text name=output value=json></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=GO></td></tr>'
            t = t + '</form></table>'
            www.serve(self,t, sidebar = doc_text, title='/t')

class URLHistory(webapp.RequestHandler):
    """
    /u

    This request handler is used to quickly retrieve a list of translations
    associated with a particular URL, optionally filtered by target language.
    It assumes that the requester may filter the list further, for example
    based on score data, or translation type. This is left up to the requester
    to decide.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = self.request.get('url')
        tl = self.request.get('tl')
        output = self.request.get('output')
        if len(output) < 1:
            output = 'json'
        if len(url) > 0:
            text = memcache.get('/urlhistory/' + url + '/' + tl + '/' + output)
            if text is not None:
                self.response.out.write(text)
            else:
                translations = list()
                tdb = db.Query(Translation)
                tdb.filter('url = ', url)
                if len(tl) > 0:
                    tdb.filter('tl = ', tl)
                tdb.order('-date')
                results = tdb.fetch(limit=500)
                for r in results:
                    t = tx()
                    t.guid = r.guid
                    t.sl = r.sl
                    t.tl = r.tl
                    try:
                        t.st = codecs.encode(r.st, 'utf-8')
                    except:
                        t.st = clean(r.st)
                    try:
                        t.tt = codecs.encode(r.tt, 'utf-8')
                    except:
                        t.tt = clean(r.tt)
                    t.anonymous = r.anonymous
                    t.avgscore = r.avgscore
                    t.scores = r.scores
                    t.city = r.city
                    t.country = r.country
                    t.username = r.username
                    t.remote_addr = r.remote_addr
                    t.machine = r.machine
                    t.professional = r.professional
                    t.date = r.date
                    t.reviewed = r.reviewed
                    t.avgscore = r.avgscore
                    try:
                        t.spam = r.spam
                    except:
                        t.spam = False
                    t.domain = r.domain
                    translations.append(t)
                d = DeepPickle()
                d.autoheader = True
                if output == 'xml' or output == 'rss' or output == 'xliff':
                    self.response.headers['Content-Type']='text/xml'
                elif output == 'json':
                    self.response.headers['Content-Type']='text/javascript'
                elif output == 'po':
                    self.response.headers['Content-Type']='text/plain'
                else:
                    self.response.headers['Content-Type']='text/html'
                self.response.out.write(d.pickleTable(translations,output))
        else:
            doc_text = self.__doc__
            t = '<table><form action=/u method=get accept-charset=utf-8>'
            t = t + '<tr><td>URL</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td>Target Language</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Output Format</td><td><input type=text name=output value=json></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=GO></td></tr>'
            t = t + '</form></table>'
            www.serve(self,t, sidebar = doc_text, title='/t')

class SpamTranslations(webapp.RequestHandler):
    """
    /spam

    This request handler is triggered by a frequent cron job. It looks for translations that
    have been flagged as spam more than N times, or that have an average score < X with more
    than Y votes logged. It will mark these translations as spam, so they will cease being
    returned in search results.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        spamcount = Translation.purgespam()
        #lowvotecount = Translation.purgebadtranslations()
        self.response.out.write('ok<p>purged ' + str(spamcount) + ' spam translations and ')
        self.response.out.write('0 low quality translations.')

class PeerReviewServer(webapp.RequestHandler):
    """
    /p

    This web service returns a list of translations from new or unknown translators. Developers
    can use this service to build peer review tools that encourage users to score translations, and
    to teach the system who the good and bad translators are. 
    """
    def get(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        domain = self.request.get('domain')
        min_scores = self.request.get('min_scores')
        output = self.request.get('output')
        if len(output) > 0:
            try:
                min_scores = int(min_scores)
            except:
                pass
            if min_scores < 1:
                min_scores = 20
            results = UserScores.peerreview(sl=sl, tl=tl, domain=domain, min_scores=min_scores)
            translations = list()
            for r in results:
                tdb = db.Query(Translation)
                if len(r.username) > 0:
                    tdb.filter('username = ', r.username)
                else:
                    tdb.filter('remote_addr = ', r.remote_addr)
                if len(sl) > 0:
                    tdb.filter('sl = ', sl)
                if len(tl) > 0:
                    tdb.filter('tl = ', tl)
                if len(domain) > 0:
                    tdb.filter('domain')
                tdb.order('-date')
                xl = tdb.fetch(limit=5)
                if len(xl) > 0:
                    for x in xl:
                        t = tx()
                        t.sl = x.sl
                        try:
                            t.st = codecs.encode(x.st,'utf-8')
                        except:
                            t.st = clean(x.st)
                        t.tl = x.tl
                        try:
                            t.tt = codecs.encode(x.tt, 'utf-8')
                        except:
                            t.tt = clean(x.tt)
                        t.domain = x.domain
                        t.guid = x.guid
                        translations.append(t)
            if output == 'xml':
                self.response.headers['Content-Type']='text/xml'
            elif output == 'jason':
                self.response.headers['Content-Type']='text/javascript'
            else:
                self.response.headers['Content-Type']='text/html'
            d = DeepPickle()
            d.autoheaders = True
            self.response.out.write(d.pickleTable(translations,output))
        else:
            t = '<table><form action=/p method=get>'
            t = t + '<tr><td>Source Language (sl)</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language (tl)</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Domain (domain)</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>Output Format (output)</td><td><input type=text name=output value=json></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</form></table>'
            www.serve(self, t, sidebar=self.__doc__, title = '/p')

class SubmitPeerReviewScores(webapp.RequestHandler):
    def get(self):
        ctr = 0
        remote_addr = self.request.remote_addr
        ip = self.request.get('ip')
        if len(ip) > 0:
            remote_addr = ip
        while ctr < 50:
            ctr = ctr + 1
            guid = self.request.get('guid' + str(ctr))
            score = self.request.get('score' + str(ctr))
            if len(guid) > 0 and len(score) > 0:
                p = dict()
                p['guid']=guid
                p['score']=score
                p['ip']=remote_addr
                p['proxy']='y'
                taskqueue.add(url = '/scores/vote', params=p)
        self.response.out.write('ok')

class FuzzySearch(webapp.RequestHandler):
    """
    <h3>/f</h3>

    This request handler is used to request a 'fuzzy search' of the translation memory. 
    This feature is currently experimental, and will be refined over time. it expects the 
    following parameters.<p>

    <ul>
    <li>sl : source language code (optional)</li>
    <li>tl : target language code (optional)</li>
    <li>q : search term</li>
    <li>domain : domain (optional)</li>
    <li>output : output format (xml, json)</li>
    </ul>
    """
    def get(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        q = self.request.get('q')
        domain = self.request.get('domain')
        output = self.request.get('output')
        if len(q) > 0:
            tdb = db.Query(Translation)
            if len(sl) > 0:
                tdb.filter('sl = ', sl)
            if len(tl) > 0:
                tdb.filter('tl  =', tl)
            if len(domain) > 0:
                tdb.filter('domain = ', domain)
            q = string.lower(q)
            q = string.replace(q, '\"', '')
            q = string.replace(q, '\'', '')
            words = string.split(q, ' ')
            for w in words:
                tdb.filter('ngrams = ', w)
            results = tdb.fetch(limit=25)
            translations = list()
            for r in results:
                t = tx()
                t.sl = r.sl
                t.tl = r.tl
                t.st = codecs.encode(r.st, 'utf-8')
                t.tt = codecs.encode(r.tt, 'utf-8')
                t.domain = r.domain
                t.date = str(r.date)
                t.username = r.username
                t.scores = r.scores
                t.rawscore = r.rawscore
                t.avgscore = r.avgscore
                t.remote_addr = r.remote_addr
                t.anonymous = r.anonymous
                t.professional = r.professional
                t.spam = r.spam
                translations.append(t)
            d = DeepPickle()
            d.autoheader = True
            if output == 'xml':
                self.response.headers['Content-Type']='text/xml'
            else:
                self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(d.pickleTable(translations,output))
        else:
            t = '<form action=/f method=get>'
            t = t + '<table>'
            t = t + '<tr><td>Source Language (sl)</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language (tl)</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Search Term (q)</td><td><input type=text name=q></td></tr>'
            t = t + '<tr><td>Domain, optional (domain)</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>Output Format (output)</td><td><input type=text name=output value=xml></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = self.__doc__, title = '/f')

class CacheTranslation(webapp.RequestHandler):
    """
    <h3>/cache</h3>

    This web API is used to cache machine translations and other placeholder translations to
    optimize performance and to reduce load on upstream machine translation services. These
    translations will be stored in memcache, but not in the persistent data store, both for
    performance reasons, and to comply with the terms of service for popular machine translation
    services.<p>

    The API expects the following parameters:<p>

    <ul>
    <li>sl = source language</li>
    <li>tl = target language</li>
    <li>st = source text</li>
    <li>tt = translated text</li>
    <li>domain = domain</li>
    <li>url = source URL</li>
    <li>mtengine = name of MT engine (google, apertium, microsoft, etc)</li>
    <li>apikey = API key (may be required if system is locked down)</li>
    </ul>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = clean(self.request.get('st'))
        tt = clean(self.request.get('tt'))
        domain = self.request.get('domain')
        url = self.request.get('url')
        apikey = self.request.get('apikey')
        mtengine = self.request.get('mtengine')
        batch = self.request.get('batch')
        purge = self.request.get('purge')
        if batch == 'y':
            ctr = 0
            while ctr < 100:
                ctr = ctr + 1
                st = clean(self.request.get('st' + str(ctr)))
                tt = clean(self.request.get('tt' + str(ctr)))
                if len(st) > 0 and len(tt) > 0:
                    p = dict()
                    p['sl']=sl
                    p['tl']=tl
                    p['st']=st
                    p['tt']=tt
                    p['domain']=domain
                    p['url']=url
                    p['apikey']=apikey
                    p['mtengine']=mtengine
                    taskqueue.add(url='/cache', params=p)
        elif purge == 'y':
            Cache.purge()
        elif len(st) > 0 and len(tt) > 0:
            m = md5.new()
            m.update(st)
            m.update(tt)
            guid = str(m.hexdigest())
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is None:
                m = md5.new()
                m.update(st)
                md5hash = str(m.hexdigest())
                timestamp = datetime.datetime.now()
                timediff = datetime.timedelta(days=3)
                timestamp = timestamp + timediff
                item = Translation()
                item.guid = guid
                item.md5hash = md5hash
                item.sl = sl
                item.tl = tl
                item.st = unicode(st, 'utf-8')
                item.tt = unicode(tt, 'utf-8')
                item.domain = domain
                item.url = url
                item.mtengine = mtengine
                item.expirationdate = timestamp
                item.machine = True
                item.anonymous = True
                item.professional = False
                if len(mtengine) > 0:
                    item.username = mtengine
                else:
                    item.username = 'google'
                item.put()
            self.response.out.write('ok')
        else:
            t = '<form action=/cache method=get><table>'
            t = t + '<tr><td>Source Language</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>Target Language</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>Source Text</td><td><input type=text name=st></td></tr>'
            t = t + '<tr><td>Translated Text</td><td><input type=text name=tt></td></tr>'
            t = t + '<tr><td>Machine Translation Engine</td><td><input type=text name=mtengine value=google></td></tr>'
            t = t + '<tr><td>Domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>URL</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = self.__doc__, title = '/cache')

class Statistics(webapp.RequestHandler):
    """
    <h3>/stats</h3>

    This API returns statistics about translations. It expects one or more of the following
    parameters:<p>
    <ul>
    <li>url</li>
    <li>domain</li>
    <li>username</li>
    <li>remote_addr</li>
    <li>sl</li>
    <li>tl</li>
    <li>startdate</li>
    <li>enddate</li>
    </ul>

    It returns an XML or JSON object with a the following fields:<p>

    <ul>
    <li>swords : source text words</li>
    <li>twords : translated words</li>
    <li>translations : number of translations</li>
    <li>users : comma separated list of users</li>
    <li>languages : comma separate list of languages</li>
    </ul>

    NOTE: because of the way App Engine indexes data, this API can't be used
    to query the entire system for global statistics. It works best when queries
    are done on a per URL, per target language basis, since the number of transactions
    will typically be small enough not to exceed Google's limit on query sizes.
    We will add global statistics in a future release when Google supports map
    reduce type functionality in App Engine.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = self.request.get('url')
        domain = self.request.get('domain')
        username = self.request.get('username')
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        remote_addr = self.request.get('ip')
        url = string.replace(url, 'http://','')
        url = string.replace(url, 'https://', '')
        if len(url) > 0 or len(domain) > 0 or len(username) > 0 or len(sl) > 0 or len(tl) > 0 or len(remote_addr) > 0:
            results = Translation.stats(sl=sl, tl=tl, domain=domain, url=url, remote_addr=remote_addr)
            self.response.out.write(str(results))
        else:
            t = '<form action=/stats method=get><table>'
            t = t + '<tr><td>url</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td>domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>source language (sl)</td><td><input type=text name=sl></td></tr>'
            t = t + '<tr><td>target language (tl)</td><td><input type=text name=tl></td></tr>'
            t = t + '<tr><td>username</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>user ip (ip)</td><td><input type=text name=ip></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = self.__doc__, title = '/stats')
                
application = webapp.WSGIApplication([('/q', GetTranslations),
                                      ('/f', FuzzySearch),
                                      ('/cache', CacheTranslation),
                                      ('/batch', BatchTranslation),
                                      ('/log', LogQueries),
                                      ('/ngrams', IndexNgrams),
                                      ('/p/submit', SubmitPeerReviewScores),
                                      ('/p', PeerReviewServer),
                                      (r'/t/(.*)/(.*)/(.*)', SimpleTranslation),
                                      (r'/t/(.*)/(.*)', SimpleTranslation),
                                      ('/t', SimpleTranslation),
                                      ('/r', RevisionHistory),
                                      ('/u', URLHistory),
                                      ('/spam', SpamTranslations),
                                      ('/stats', Statistics),
                                      ('/submit', SubmitTranslation)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

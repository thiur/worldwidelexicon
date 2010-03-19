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
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
# import standard Python modules
import sys
import demjson
import urllib
import string
import md5
import datetime
import pydoc
import codecs
import types
# import WWL and third party modules
from deeppickle import DeepPickle
from mt import MTWrapper
from webappcookie import Cookies
from www import www
from geo import geo
from akismet import Akismet
from config import Config
from database import Comment
from database import Queue
from database import Search
from database import Translation
from database import languages
from database import Users
from database import Websites
import feedparser

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

def smart_str(s, encoding='utf-8', errors='ignore', from_encoding='utf-8'):
    if type(s) in (int, long, float, types.NoneType):
        return str(s)
    elif type(s) is str:
        if encoding != from_encoding:
            return s.decode(from_encoding, errors).encode(encoding, errors)
        else:
            return s
    elif type(s) is unicode:
        return s.encode(encoding, errors)
    elif hasattr(s, '__str__'):
        return smart_str(str(s), encoding, errors, from_encoding)
    elif hasattr(s, '__unicode__'):
        return smart_str(unicode(s), encoding, errors, from_encoding)
    else:
        return smart_str(str(s), encoding, errors, from_encoding)
    
class tx():
    sl = ''
    
class AddQueue(webapp.RequestHandler):
    """
    /queue/add
    
    This request handler is used to add a text to the translation queue. This API is typically used to queue
    translations for processing by an external language service provider, volunteer community, etc, where
    texts are translated outside of the source website (for example in the Extraordinaries mobile translation app)
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = clean(self.request.get('st'))
        domain = self.request.get('domain')
        url = self.request.get('url')
        lsp = self.request.get('lsp')
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            Queue.add(sl, tl, st, domain=domain, url=url, lsp=lsp)
            self.response.headers['Content-Type']='text/plain'
            self.response.out.write('ok')
        else:
            www.serve(self, self.__doc__)
            self.response.out.write('<form action=/queue/add method=get>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Source Language (sl)</td><td><input type=text name=sl></td></tr>')
            self.response.out.write('<tr><td>Target Language (tl)</td><td><input type=text name=tl></td></tr>')
            self.response.out.write('<tr><td>Source Text (st)</td><td><input type=text name=st></td></tr>')
            self.response.out.write('<tr><td>Domain (domain)</td><td><input type=text name=domain></td></tr>')
            self.response.out.write('<tr><td>URL (url)</td><td><input type=text name=url></td></tr>')
            self.response.out.write('<tr><td>Language Service Provider (lsp)</td><td><input type=text name=lsp></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="OK"></td></tr>')
            self.response.out.write('</table></form>')
    
class SearchQueue(webapp.RequestHandler):
    """
    SearchQueue()
    /queue/search
    
    This request handler is used to search for pending translation jobs that
    have been scheduled for dispatch to services like The Extraordinaries. The
    API expects the following parameters:
    
    sl : source language code
    tl : target language code
    domain : source domain (to limit scope of search to source texts from domain www.xyz.com)
    lsp : language service provider (limit scope of search to jobs for a specific agency)
    output : output format (xml, rss, json)
    limit : optional limit on max number of jobs
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        domain = self.request.get('domain')
        lsp = self.request.get('lsp')
        output = self.request.get('output')
        if len(output) < 1:
            output = 'json'
        if output == 'xml' or output == 'rss':
            self.response.headers['Content-Type']='text/xml'
        elif output == 'json':
            self.response.headers['Content-Type']='application/json'
        else:
            self.response.headers['Content-Type']='text/html'
        if len(sl) > 0 and len(tl) > 0:
            jobs = Queue.query(sl, tl, domain=domain, lsp=lsp)
            d = DeepPickle()
            self.response.out.write(d.pickleTable(jobs,output))
        else:
            www.serve(self, self.__doc__)
            self.response.out.write('<form action=/queue/search method=get>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Source Language (sl)</td><td><input type=text name=sl></td></tr>')
            self.response.out.write('<tr><td>Target Language (tl)</td><td><input type=text name=tl></td></tr>')
            self.response.out.write('<tr><td>Domain</td><td><input type=text name=domain></td></tr>')
            self.response.out.write('<tr><td>Language Service Provide (lsp)</td><td><input type=text name=lsp></td></tr>')
            self.response.out.write('<tr><td>Output Format (output)</td><td><input type=text name=output value=xml></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="OK"></td></tr>')
            self.response.out.write('</form></table>')
        
class QueueSubmit(webapp.RequestHandler):
    """
    /queue/submit
    
    This web API is used to submit translations that have been processed via an external translation service or
    volunteer community. It expects the following parameters:
    
    guid : record locator for the translation job
    tt : translated text (utf 8)
    username : username to attribute translation to
    pw : password (for WWL user, send an API key if submitting on behalf of an LSP)
    
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        guid = self.request.get('guid')
        tt = clean(self.request.get('tt'))
        domain = self.request.get('domain')
        url = self.request.get('url')
        remote_addr = self.request.remote_addr
        username = self.request.get('username')
        pw = self.request.get('pw')
        remote_addr = self.request.remote_addr
        result = Queue.submit(guid, tt, username, pw, remote_addr)
        if len(guid) > 0:
            self.response.headers['Content-Type']='text/plain'
            if result:
                self.response.out.write('ok')
            else:
                self.response.out.write('error')
        else:
            www.serve(self, self.__doc__)
            self.response.out.write('<form action=/queue/submit method=get>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>guid (guid)</td><td><input type=text name=guid></td></tr>')
            self.response.out.write('<tr><td>Translated Text (tt)</td><td><input type=text name=tt></td></tr>')
            self.response.out.write('<tr><td>Username (username)</td><td><input type=text name=username></td></tr>')
            self.response.out.write('<tr><td>Password or LSP API key</td><td><input type=password name=pw></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="OK"></td></tr>')
            self.response.out.write('</table></form>')

class GetTranslations(webapp.RequestHandler):
    """
    
    GetTranslations()
    /q
    
    This API handler returns a list of translations that match your search
    criteria. The request handler expects the following parameters:
    
    sl : source language (ISO language code), required
    tl : target language (ISO language code), required
    st : source text (Unicode, UTF-8 encoding), either st or md5hash must be present
    md5hash : MD5 hashkey generated from source text (more efficient when retrieving
              archived translations for large texts, except auto-fallback to
              machine translation will not work)
    allow_anonymous : (y/n) include anonymous translations (enabled by default)
    allow_machine : (y/n) include machine translations (enabled by default)
    allow_unscored : (y/n) include unscored human translations (enabled by default)
    minimum_score : minimum score (0 to 5 scale)
    fuzzy : (y/n), if yes searches for the word or phrase within translations
                    (e.g. fuzzy=y and st=hello world will find any translations whose
                    source text contains the phrase 'hello world'), currently limited
                    to searching for short phrases of 1 to 4 words within larger texts.
    lsp : language service provider (for on demand professional translation)
    lspusername : LSP username
    lsppw : LSP password
    mtengine : optional machine translation engine to call out to for machine translations
                    if no human translations are available (options are: google, apertium,
                    moses, with more coming soon)
    output : output format (xml, rss, json, po, xliff)
    
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
        sys_allow_anonymous = Websites.parm(domain,'tm_allow_anonymous')
        sys_allow_machine = Websites.parm(domain,'tm_allow_machine')
        sys_allow_unscored = Websites.parm(domain,'tm_allow_unscored')        
        url = self.request.get('url')
        md5hash = self.request.get('md5hash')
        fuzzy = self.request.get('fuzzy')
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        mtengine = self.request.get('mtengine')
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
        if string.lower(allow_anonymous) == 'n' or sys_allow_anonymous != 'y':
            display_anonymous = False
        else:
            display_anonymous = True
        try:
            allow_machine = cookies['allow_machine']
        except:
            allow_machine = self.request.get('allow_machine')
        if string.lower(allow_machine) == 'n' or sys_allow_machine != 'y':
            display_machine = False
        else:
            display_machine = True
        try:
            allow_unscored = cookies['allow_unscored']
        except:
            allow_unscored = self.request.get('allow_unscored')
        if string.lower(allow_unscored) == 'n' or sys_allow_unscored != 'y':
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
            if len(url) > 0:
                p = dict()
                p['remote_addr']=self.request.remote_addr
                p['url']=url
                p['sl']=sl
                p['tl']=tl
                taskqueue.add(url='/log', params=p)
            results = Translation.fetch(sl=sl, st=st, tl=tl, domain='', url=url, userip=remote_addr, allow_machine=allow_machine, allow_anonymous=allow_anonymous, min_score=minimum_score, max_blocked_votes=max_blocked_votes, fuzzy=fuzzy)
            if len(results) < 1 or fuzzy=='y':
                if len(lsp) > 0:
                    p = dict()
                    p['sl'] = sl
                    p['tl'] = tl
                    p['st'] = st
                    p['domain'] = domain
                    p['url'] = url
                    p['username'] = lspusername
                    p['pw'] = lsppw
                    lspurl = Config.lspurl(lsp)
                    if len(lspurl) > 0:
                        taskqueue.add(url = lspurl, params=p)
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
                results.append(t)
            d.autoheader = True
            self.response.headers['Accept-Charset']='utf-8'
            if output=='xml' or output=='rss':
                self.response.headers['Content-Type']='text/xml'
            elif output=='json' or output=='po':
                self.response.headers['Content-Type']='text/plain'
            else:
                self.response.headers['Content-Type']='text/html'
            text = d.pickleTable(results, output)
            self.response.out.write(text)
        else:
            www.serve(self,self.__doc__, title = '/q')
            self.response.out.write('<h3>Test Form</h3>')
            self.response.out.write('<table><form action=/q method=post accept-charset=utf-8>')
            self.response.out.write('<tr><td>Source Language</td><td><input type=text name=sl></td></tr>')
            self.response.out.write('<tr><td>Target Language</td><td><input type=text name=tl></td></tr>')
            self.response.out.write('<tr><td>Source Text</td><td><textarea name=st rows=4 cols=40></textarea></td></tr>')
            self.response.out.write('<tr><td>Source Text MD5 Hash</td><td><input type=text name=md5hash></td></tr>')
            self.response.out.write('<tr><td>URL to request translations for</td><td><input type=text name=url></td></tr>')
            self.response.out.write('<tr><td>Display Anonymous Texts (y/n)</td><td><input type=text name=allow_anonymous></td></tr>')
            self.response.out.write('<tr><td>Display Machine Texts (y/n)</td><td><input type=text name=allow_machine></td></tr>')
            self.response.out.write('<tr><td>Minimum Score (0 to 5)</td><td><input type=text name=minimum_score></td></tr>')
            self.response.out.write('<tr><td>Fuzzy Search</td><td><input type=text name=fuzzy value=n></td></tr>')
            self.response.out.write('<tr><td>Machine Translation Engine</td><td>')
            self.response.out.write('<select name=mtengine><option selected value="">--Automatic--</option>')
            self.response.out.write('<option value=google>Google</option>')
            self.response.out.write('<option value=apertium>Apertium</option>')
            self.response.out.write('<option value=moses>Moses</option>')
            self.response.out.write('</select></td></tr>')
            self.response.out.write('<tr><td>Output Format</td><td><input type=text name=output value=rss></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=SEARCH></td></tr>')
            self.response.out.write('</table></form>')

class SubmitTranslation(webapp.RequestHandler):
    """
    
    /submit
    
    This web service API call stores newly submitted translations to the datastore. 
    It expects the following parameters:
    
    sl - source language (ISO language code), required
    tl - target language (ISO language code), required
    st - source text (UTF-8 encoded), required
    tt - translated text (UTF-8 encoded), required
    domain - site domain or API key, optional but recommended (submit in nnn.com format)
    url - parent URL of source document, optional but recommended (submit full permalink)
    username - WWL or remote username, optional (system allows anonymous translations)
    pw - WWL or remote user password
    proxy - if submission is being submitted via a proxy gateway, default = n if omitted
            (in proxy mode, we use you are filtering submissions upstream and will accept
            whatever username you provide)
    session - session key (cookie, stored whenever user logs into system)
    
    The API call returns a text/plain object, with either an ok response or an error message.
    
    IMPORTANT: always use UTF-8 encoding when submitting data. If you are generating an HTML
    form that points back to the WWL server, be sure to include accept-charset=utf-8 in the
    <form > tag. If you are submitting data from a separate application, be sure to set the
    accept-charset=utf-8 header in the HTTP call, and to encode characters using UTF-8. If
    you do not do this consistently, you will see character encoding errors or receive
    garbage characters in your translations. Use UTF-8 everywhere, and specifically do not
    use language specific character sets. 
    
    """
    def requesthandler(self):
        """Combined GET and POST request handler """
        validquery = True
        emptyform = False
        remote_addr = self.request.remote_addr
        exists = memcache.get('ratelimit|remote_addr=' + remote_addr)
        if exists is not None:
            self.response.headers['Content-Type']='text/plain'
            self.response.out.write('error\nrate limit exceeeded')
        else:
            memcache.set('ratelimit|remote_addr=' + remote_addr, True, 5)
        cookies = Cookies(self,max_age=3600)
        try:
            session = cookies['session']
        except:
            session = ''
        validuser = False
        username = self.request.get('username')
        proxy = self.request.get('proxy')
        pw = self.request.get('pw')
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
        st = self.request.get('st')
        st = clean(st)
        tt = self.request.get('tt')
        tt = clean(tt)
        title = clean(self.request.get('title'))
        ttitle = clean(self.request.get('ttitle'))
        description = clean(self.request.get('description'))
        tdescription = clean(self.request.get('tdescription'))
        if len(sl) < 1 or len(tl) < 1 or len(st) < 1 or len(tt) < 1:
            validquery=False
        if len(sl) < 1 and len(tl) < 1:
            emptyform = True
        domain = self.request.get('domain')
        url = self.request.get('url')
        doc = self.request.get('doc')
        remote_addr = self.request.remote_addr
        lsp = self.request.get('lsp')
        if doc == 'y':
            display_docs = True
        else:
            display_docs = False
        akismetapi = Websites.parm(domain, 'akismetapi')
        if akismetapi is not None:
            if len(akismetapi) > 0:
                a = Akismet()
                a.setAPIKey(akismetapi)
                try:
                    a.verify_key()
                    data = dict()
                    data['user_ip']= remote_addr
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
        location = geo.get(remote_addr)
        if location is not None:
            city = location['city']
            state = location['state']
            country = location['country']
            latitude = location['latitude']
            longitude = location['longitude']
        sys_allow_anonymous = Websites.parm(domain, 'tm_allow_anonymous')
        if sys_allow_anonymous is not None and sys_allow_anonymous == 'n' and validuser == False:
            valid_query = False
        result = False
        if len(url) > 0:
            p = dict()
            p['url']=url
            p['sl']=sl
            p['tl']=tl
            p['action']='translate'
            p['remote_addr']=self.request.remote_addr
            taskqueue.add(url = '/log', params = p)
        result = Translation.submit(sl=sl, st=st, tl=tl, tt=tt, username=username, remote_addr=remote_addr, domain=domain, url=url, city=city, state=state, country=country, latitude=latitude, longitude=longitude, lsp=lsp, proxy=proxy)
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
        callback = self.request.get('callback')
        if len(callback) > 0:
            self.redirect(callback)
        else:
            if result:
                self.response.out.write('ok')
            elif not emptyform:
                self.response.out.write('error : invalid user')
            else:
                pass
            if emptyform:
                www.serve(self,self.__doc__, title = '/submit')
                self.response.out.write('<h3>Test Form</h3>')
                self.response.out.write('<table border=1>')
                self.response.out.write('<form action=/submit method=post accept-charset=utf-8>')
                self.response.out.write('<tr><td>Source Language</td><td><input type=text name=sl value=en></td></tr>')
                self.response.out.write('<tr><td>Target Language</td><td><input type=text name=tl value=es></td></tr>')
                self.response.out.write('<tr><td>Source Text</td><td><input type=text name=st value=\"' + st + '\"></td></tr>')
                self.response.out.write('<tr><td>Translation</td><td><input type=text name=tt value=\"' + tt + '\"></td></tr>')
                self.response.out.write('<tr><td>Domain</td><td><input type=text name=domain value=\"' + domain + '\"></td></tr>')
                self.response.out.write('<tr><td>URL</td><td><input type=text name=url value=\"' + url + '\"></td></tr>')
                self.response.out.write('<tr><td>WWL Username</td><td><input type=text name=username></td></tr>')
                self.response.out.write('<tr><td>WWL Password</td><td><input type=password name=pw></td></tr>')
                self.response.out.write('<tr><td>Proxy Mode (y/n)</td><td><input type=text name=proxy value=n></td></tr>')
                self.response.out.write('<tr><td>Output format</td><td><input type=text name=output value=text></td></tr>')
                self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr>')
                self.response.out.write('</table></form>')
    def post(self):
        """ Processes HTTP POST calls """
        self.requesthandler()
    def get(self):
        """ Processes HTTP GET calls """
        self.requesthandler()

class ManageTranslations(webapp.RequestHandler):
    """
    This request handler implements the /translators/manage interface which allows
    translators with permission to create and edit translations to edit, score
    and delete translations via a system administrator's interface. 
    """
    def get(self):
        pass
    def post(self):
        pass
    
class SimpleTranslation(webapp.RequestHandler):
    """
    This request handler implements the /t/*/*/* web service which provides a simple
    text-only interface for retrieving translations from WWL. The web service is called via
    a RESTful interface as follows:
    
    /t/{source_language}/{target_language}/{escape encoded text}
    
    or
    
    /t/{source_language}/{target_language}
    
    with the parameters
    
    st = source text (UTF-8 encoded)
    allow_anonymous = y/n (allow anonymous translations, default = y)
    allow_machine = y/n (allow machine translations, default = y)
    min_score = minimum average quality score (0 to 5, default 0)
    lsp = name of professional translation service provider (will request a professional
                            translation)
    lspusername = username to submit to professional translation svc (overrides system default)
    lsppw = password or API key to submit to professional translation svc (overrides system default)
    queue = add translation to translation queue for third party service (e.g. beextra.org)
    mtengine = request translation via a specific machine translation service, if not specified will
                select MT engine automatically using defaults in mt.py
    ip = dotted IP address or prefix (e.g. ip=206.1.2) to limit results to translations submitted from
                a specific IP address or range (so you can ignore submissions that were not posted from
                a trusted gateway you control)
    output = text|html|json (default is html response, json will return translation in the same
                             format used by Google Translate)
    
    The request handler will return the best available translation in simple HTML by
    default. If you need a full revision history, you should use the /q interface.
    
    This interface makes it easy to merge translations into web documents as they are
    served, as it can be used as a type of server side include. This enables a website
    to exert direct control over how translations are displayed, to cache them locally
    and host the translations on the same publishing or web application environment.
    Note that this can also be used to localize a web interface as it provides a simple
    gettext() style interface for fetching a translation for a string. 
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
        userip = self.request.remote_addr
        tt = self.request.get('tt')
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        allow_anonymous = self.request.get('allow_anonymous')
        allow_machine = self.request.get('allow_machine')
        min_score = self.request.get('min_score')
        output = self.request.get('output')
        edit = self.request.get('edit')
        mtengine = self.request.get('mtengine')
        queue = self.request.get('queue')
        ip = self.request.get('ip')
        st = urllib.unquote(st)
        m = md5.new()
        m.update(sl)
        m.update(tl)
        m.update(st)
        m.update(lsp)
        md5hash = str(m.hexdigest())
        text = memcache.get('/t/' + md5hash)
        if text is not None:
            self.response.out.write(text)
            return
        self.response.headers['Accept-Charset'] = 'utf-8'
        if len(tl) > 0 and len(st) > 0:
            if edit == 'y':
                www.serve(self, 'Edit this translation using the form below.', title='Edit Translation')
                self.response.out.write('<table><form action=/t/' + sl + '/' + tl + ' method=post accept-charset=utf-8>')
                self.response.out.write('<input type=hidden name=st value="' + st + '">')
                self.response.out.write('<tr><td>WWL Username <input type=text name=username></td></tr>')
                self.response.out.write('<tr><td>WWL Password <input type=password name=pw></td></tr>')
                self.response.out.write('<tr><td width=300>' + st + '</td></tr>')
                self.response.out.write('<tr><td width=300><textarea name=tt>' + tt + '</textarea></td></tr>')
                self.response.out.write('<tr><td colspan=2><input type=submit value="OK" onclick="window.close();"></td></tr>')
                self.response.out.write('</table></form>')
            else:
                tt = Translation.lucky(sl=sl, tl=tl, st=st, allow_anonymous=allow_anonymous, allow_machine=allow_machine, min_score=min_score, output=output, edit=edit, lsp=lsp, lspusername=lspusername, lsppw = lsppw, mtengine=mtengine, queue=queue, ip=ip, userip=userip)
                self.response.out.write(tt)
                memcache.set('/t/' + md5hash, text, 300)
        else:
            www.serve(self,self.__doc__, title='/t')
            self.response.out.write('<table><form action=/t method=get accept-charset=utf-8>')
            self.response.out.write('<tr><td>Source Language</td><td><input type=text name=sl></td></tr>')
            self.response.out.write('<tr><td>Target Language</td><td><input type=text name=tl></td></tr>')
            self.response.out.write('<tr><td colspan><b>Text To Translate</b><br><textarea name=st></textarea></td></tr>')
            self.response.out.write('<tr><td>Language Service Provider (request pro translation)</td>')
            self.response.out.write('<td><input type=text name=lsp></td></tr>')
            self.response.out.write('<tr><td>LSP Username</td><td><input type=text name=lspusername></td></tr>')
            self.response.out.write('<tr><td>LSP Password</td><td><input type=text name=lsppw></td></tr>')
            self.response.out.write('<tr><td>Limit Results By IP Address or Pattern</td><td><input type=text name=ip></td></tr>')
            self.response.out.write('<tr><td>Output Format</td><td><input type=text name=output value=html></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=GO></td></tr>')
            self.response.out.write('</form></table>')
            
class EditTranslations(webapp.RequestHandler):
    def get(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('st')
        url = self.request.get('url')
        domain = self.request.get('domain')
        md5hash = self.request.get('md5hash')
        prompt_edit_translations = 'Edit Translations'
        prompt_save = 'Save Translation'
        prompt_good = 'Good'
        prompt_bad = 'Bad'
        prompt_spam = 'Spam/Delete'
        prompt_original = 'Original'
        prompt_translation = 'Translation'
        prompt_quality = 'Translation Quality'
        www.serve(self, '', title=prompt_edit_translations)
        results = Translation.fetch(sl=sl, tl=tl, st=st, url=url, md5hash=md5hash)
        self.response.out.write('<table>')
        self.response.out.write('<tr valign=top><td>' + prompt_original + '</td><td>' + prompt_translation + '</td><td>' + prompt_good + '</td><td>' + prompt_bad + '</td><td>' + prompt_spam + '</td></tr>')
        for r in results:
            self.response.out.write('<form action=/t/edit method=post>')
            self.response.out.write('<input type=hidden name=guid value="' + r.guid + '">')
            self.response.out.write('<tr valign=top><td>' + codecs.encode(r.st, 'utf-8') + '</td>')
            self.response.out.write('<td><textarea name=tt rows=2>' + codecs.encode(r.tt, 'utf-8') + '</textarea><br>')
            self.response.out.write('<input type=submit value="' + prompt_save + '"></form></td>')
            self.response.out.write('<td><a href=/scores/vote?guid=' + r.guid + '&votetype=up><img src=/image/go-up.png></a></td>')
            self.response.out.write('<td><a href=/scores/vote?guid=' + r.guid + '&votetype=down><img src=/image/go-down.png></a></td>')
            self.response.out.write('<td><a href=/scores/vote?guid=' + r.guid + '&votetype=block><img src=/image/trash.png></a></td>')
            self.response.out.write('</tr>')
        self.response.out.write('</table>')
    def post(self):
        cookies = Cookies(self)
        try:
            session = cookies['session']
        except:
            session = ''
        username = ''
        validuser = False
        if len(session) > 0:
            username = memcache.get('sessions|' + session)
            if username is None:
                username = ''
            else:
                validuser = True
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('st')
        tt = self.request.get('tt')
        domain = self.request.get('domain')
        url = self.request.get('url')
        remote_addr = self.request.remote_addr
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0 and len(tt) > 0:
            result = Translation.submit(sl, st, tl, tt, domain, url, remote_addr, username)
        self.redirect('/t/edit')
        
class Sidebar(webapp.RequestHandler):
    def post(self):
        self.requesthandler()
    def get(self):
        self.requesthandler()
    def requesthandler(self):
        self.response.out.write('<table border=0><tr><td>')
        self.response.out.write('<img src=/image/logo.png align=left valign=center>')
        self.response.out.write('<font size=+1>Worldwide<br>Lexicon</font></td></tr></table><hr>')
        cookies = Cookies(self)
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        if len(sl) < 2:
            sl = tl
        url = self.request.get('url')
        version = string.replace(self.request.get('v'), 'firefox.', '')
        if string.count(version, '.') > 0:
            version = float(version)
        else:
            version = float(0)
        url = string.replace(url, 'http://', '')
        try:
            session = cookies['session']
        except:
            session = ''
        username = ''
        if len(session) > 0:
            username = memcache.get('sessions|' + session)
            if username is None:
                username = ''
        comment = self.request.get('comment')
        if len(comment) > 0:
            guid = ''
            fields = dict()
            fields['tl'] = tl
            fields['cl'] = tl
            fields['comment']=comment
            fields['username']=username
            fields['remote_addr']=self.request.remote_addr
            Comment.save(guid, fields, url=url)
        urltexts = string.split(url, '/')
        if len(urltexts) > 0:
            domain = urltexts[0]
        else:
            domain = ''
        if tl == 'es':
            proz = 'esp'
        elif tl == 'fr':
            proz = 'fra'
        elif tl == 'de':
            proz = 'deu'
        else:
            proz = 'rus'
        google_analytics_header = '<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");\
        document.write(unescape("%3Cscript src=\'\" + gaJsHost + \"google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));\
        </script>\
        <script type="text/javascript">\
        try {\
        var pageTracker = _gat._getTracker("UA-7294247-1");\
        pageTracker._trackPageview();\
        } catch(err) {}</script>'
        self.response.out.write(google_analytics_header)
        prozurl = 'http://www.proz.com/connectapi?key=b60c3f792ed225efcc473fa8cfeb309b&version=0.4&pair=eng_' + proz + '&output=rss'
        f = memcache.get('proz|eng|' + proz)
        if f is None:
            response = urlfetch.fetch(url = prozurl)
            if response.status_code == 200:
                f = response.content
                memcache.set('proz|eng|' + proz, f, 900)
            else:
                f = ''
        mt = MTWrapper()
        if version < 1.000:
            prompt_upgrade = '<h4>Upgrade To The Newest Firefox Translator</h4>\
<font size=-1>Upgrade to the newest version of the <b><a href=http://www.worldwidelexicon.org target=_new>Firefox Translator</a></b>. This version \
includes several new features and improvements, including: faster page translation, more options for displaying translations, and new \
community features.</font><hr>'
            prompt_donate = '<h4>New Essay</h4>\
<font size=-1>Read this <b><a href=http://www.worldwidelexicon.org/s/essay.html target=_new>recently published essay, The End of the Language Barrier</a></b> by \
Brian McConnell. The essay describes his vision for the future, where people will be able to read any website in any language. If you think this \
is valuable work, consider <a href=http://www.worldwidelexicon.org target=_new>making a donation</a> to support ongoing software development.</font><hr>'
            if tl != 'en' and len(tl) > 1:
                prompt_upgrade = mt.getTranslation('en', tl, prompt_upgrade)
                prompt_donate = mt.getTranslation('en', tl, prompt_donate)
            self.response.out.write(prompt_upgrade)
            self.response.out.write(prompt_donate)
        if len(url) > 0:
            txt = memcache.get('recenttranslations|tl=' + tl + '|url=' + url)
            if txt is not None:
                self.response.out.write(txt)
            else:
                tdb = db.Query(Translation)
                if string.count(url, 'http://') > 0:
                    url = string.replace(url, 'http://', '')
                tdb.filter('url = ', url)
                if len(tl) > 0:
                    tdb.filter('tl = ', tl)
                tdb.order('-date')
                results = tdb.fetch(limit=200)
                authors = list()
                for r in results:
                    if r.anonymous:
                        if len(r.city) > 0:
                            t = r.remote_addr + ' (' + r.city + ')'
                        else:
                            t = r.remote_addr
                    else:
                        if len(r.city) > 0:
                            t = r.username + ' (' + r.city + ')'
                        else:
                            t = r.username
                        if string.count(t, 'proz.') > 0:
                            t = string.replace(t, 'proz.', '')
                            t = '[PRO] ' + t
                    if t not in authors:
                        authors.append(t)
                translator_heading = mt.getTranslation('en', tl, 'Translators')
                txt = '<h4 style="font-family: sans-serif">'+ translator_heading + '</h4>'
                if len(authors) > 0:
                    txt = txt + '<ul><font size=-2>'
                    for a in authors:
                        if string.count(a, '[PRO]') > 0:
                            link = string.replace(a, '[PRO] ', 'proz.')
                        else:
                            link = a
                        txt = txt + '<li><a target=_new href=/profiles/' + link + '>' + a + '</a></li>'
                    txt = txt + '</font></ul>'
                else:
                    no_mt = mt.getTranslation('en', tl, 'This page has not been translated by other users. Only machine translations are available at this time\
     To edit, score or replace a translation, hover over a translated text, and then a popup editor will appear.')
                    txt = txt + '<p style="font-family: sans-serif"><font size=-1>'
                    txt = txt + no_mt
                    txt = txt + '</font></p>'
                    memcache.set('recentranslations|tl=' + tl + '|url=' + url, txt, 240)
                self.response.out.write(txt)
            self.response.out.write('<hr>')
            txt = memcache.get('topsites|all')
            if txt is not None:
                self.response.out.write(txt)
            else:
                prompt_top_sites = 'Top Sites'
                prompt_worldwide = 'Worldwide'
                if sl != 'en' and len(sl) > 1:
                    prompt_top_sites = mt.getTranslation('en', tl, prompt_top_sites)
                    prompt_worldwide = mt.getTranslation('en', tl, prompt_worldwide)
                txt = '<h4>' + prompt_top_sites + '(' + prompt_worldwide + ')'
                sdb = db.Query(Search)
                sdb.order('-translations')
                results = sdb.fetch(limit=50)
                sitelist = list()
                if results is not None:
                    txt = txt + '<ul><font size=-2>'
                    ctr = 0
                    for r in results:
                        if r.domain not in sitelist and ctr < 15:
                            ctr = ctr + 1
                            sitelist.append(r.domain)
                            txt = txt + '<li><a target=_new href=http://' + r.domain + '>' + r.domain + '</a></li>'
                    txt = txt + '</font></ul>'
                    memcache.set('topsites|all', txt, 1800)
                    self.response.out.write(txt)
            self.response.out.write('<hr>')
            txt = memcache.get('topsites|sl=' + sl)
            if txt is not None:
                self.response.out.write(txt)
            else:
                prompt_top_sites = 'Top Sites'
                if sl != 'en' and len(sl) > 1:
                    prompt_top_sites = mt.getTranslation('en', tl, prompt_top_sites)
                txt = '<h4>' + prompt_top_sites + ' (' + languages.getlist(sl) + ')'
                sdb = db.Query(Search)
                sdb.filter('sl = ', sl)
                sdb.filter('issite = ', True)
                sdb.order('-views')
                results = sdb.fetch(limit=50)
                sitelist = list()
                if results is not None:
                    txt = txt + '<ul><font size=-2>'
                    for r in results:
                        if r.domain not in sitelist:
                            sitelist.append(r.domain)
                            title = clean(r.title)
                            if len(title) > 0:
                                txt = txt + '<li><a target=_new href=http://' + r.domain + '>' + title + '</a></li>'
                            else:
                                txt = txt + '<li><a target=_new href=http://' + r.domain + '>' + r.domain + '</a></li>'
                    txt = txt + '</font></ul>'
                    memcache.set('topsites|sl=' + sl, txt, 1800)
                    self.response.out.write(txt)
            self.response.out.write('<hr>')
            proz_heading = mt.getTranslation('en', tl, 'Find Professional Translators On ProZ.Com')
            self.response.out.write('<h4 style="font-family: sans-serif"><a href=http://www.proz.com>' + proz_heading + '</a></h4>')
            d = feedparser.parse(f)
            entries = d.entries
            if len(entries) > 0:
                self.response.out.write('<ul>')
                ctr = 0
                for e in entries:
                    ctr = ctr + 1
                    if ctr < 10:
                        self.response.out.write('<li style="font-family: sans-serif size: small"><a target=_new href=' + e.link + '>' + e.title + '</a></li>')
                self.response.out.write('</ul>')
        else:
            self.response.out.write('<form action=/sidebar method=get>')
            self.response.out.write('URL: <input type=text name=url size=30><p>')
            self.response.out.write('Language: <input type=text name=tl size=3><p>')
            self.response.out.write('<input type=submit value=OK></form>')
            
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
        
class UnicodeTest(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        text = self.request.get('text')
        try:
            utext = text.encode('utf-8')
        except:
            try:
                utext = text.encode('iso-8859-1')
            except:
                utext = text.encode('ascii')
        text = utext.decode('utf-8')
        self.response.headers['Accept-Charset']='utf-8'
        self.response.out.write(text)
        
class Cache(webapp.RequestHandler):
    """
    /cache/*
    
    This request handler provides client applications (widgets, browser addons, etc)
    with a simple interface for uploading and fetching cached machine translations
    from a shared memcache system. This was implemented to boost page rendering
    performance in the Firefox translation addon. 
    """
    def get(self, md5hash):
        if len(md5hash) > 0:
            self.response.headers['Content-Type']='text/plain'
            text = memcache.get('cache|' + md5hash)
            if text is None:
                text = ''
            self.response.out.write(text)
        else:
            self.response.out.write('<form action=/cache/ method=post>')
            self.response.out.write('<table><tr><td>MD5 Hash</td><td><input type=text name=md5hash></td></tr>')
            self.response.out.write('<tr><td colspan=2>Text<br><textarea name=text></textarea></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr>')
            self.response.out.write('</form></table>')
    def post(self, md5hash):
        self.response.headers['Content-Type']='text/plain'
        if len(md5hash) < 1:
            md5hash = self.request.get('md5hash')
        if len(md5hash) > 0:
            text = self.request.get('text')
            memcache.set('cache|' + md5hash, text, 300)
            memcache.set('ratelimit|cache|remote_addr=' + self.request.remote_addr, True, 2)
            self.response.out.write('ok')
        else:
            self.response.out.write('error')

class SendLSP(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = self.request.get('url')
        form_data = self.request.get('form_data')
        lsp = self.request.get('lsp')
        m = md5.new()
        m.update(url)
        m.update(form_data)
        guid = str(m.hexdigest())
        qdb = db.Query(Queue)
        qdb.filter('guid = ', guid)
        item = qdb.get()
        if item is None:
            result = urlfetch.fetch(url=url,
                            payload=form_data,
                            method=urlfetch.POST,
                            headers={'Content-Type': 'application/x-www-form-urlencoded'})
            results = result.content
            item = Queue()
            item.guid = guid
            item.lsp = lsp
            item.put()
        self.response.out.write('ok')

application = webapp.WSGIApplication([('/q', GetTranslations),
                                      ('/log', LogQueries),
                                      ('/cache/(.*)', Cache),
                                      ('/queue/add', AddQueue),
                                      ('/queue/send', SendLSP),
                                      ('/queue/search', SearchQueue),
                                      ('/queue/submit', QueueSubmit),
                                      ('/t/edit', EditTranslations),
                                      (r'/t/(.*)/(.*)/(.*)', SimpleTranslation),
                                      (r'/t/(.*)/(.*)', SimpleTranslation),
                                      ('/t', SimpleTranslation),
                                      ('/submit', SubmitTranslation),
                                      ('/sidebar', Sidebar),
                                      ('/unicode', UnicodeTest)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

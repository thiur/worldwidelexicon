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
import time
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
from transcoder import transcoder
from database import Comment
from database import Queue
from database import Search
from database import Translation
from database import languages
from database import Users
from database import Settings
from ip import ip
import feedparser

def clean(text):
    return transcoder.clean(text)
    # skip this for now
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
    st (optional) : if submitting an inline translation directly, rather than picking a source text from the queue
    domain (optional) : if submitting an inline translation directly, rather than via the translator user interface
    url (optional) : if submitting an inline translation directly, rather than via the translator user interface
    
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        guid = self.request.get('guid')
        st = clean(self.request.get('st'))
        tt = clean(self.request.get('tt'))
        domain = self.request.get('domain')
        url = self.request.get('url')
        username = self.request.get('username')
        pw = self.request.get('pw')
        remote_addr = self.request.remote_addr
        # check if this IP address is rate limited (> one submit per second)
        # if yes, return 500 error code
        if not ip.allow(remote_addr, action='submit'):
            self.response.clear()
            self.response.set_status(500)
            self.response.out.write('Rate limit exceeded')
            return
        # IP address not rate limited, so proceed normally
        data = dict()
        data['user_ip']=remote_addr
        if len(username) > 0:
            data['comment_author']=username
        if len(url) > 0:
            data['permalink']=url
        comment = tt
        # call Akismet to check that it is not a spam comment / translation
        # if yes, say OK but discard the translation
        # if no, say OK and accept the translation
        pass
        # lookup user and see if the user is valid and has a scoring history
        # if user has > N scores and an average score > X, accept the submission
        # automatically
        pass
        # otherwise, add it to the translation queue for scoring
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
        if not spam:
            result = Queue.submit(guid, tt, username, pw, remote_addr)
        if len(guid) > 0 or len(st) > 0:
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

class QueueScore(webapp.RequestHandler):
    """
    /queue/score

    Submit a score for a translation that has been submitted by another user.

    Expects:

    guid : guid of the translation
    username : WWL username (if blank, uses IP)
    pw : WWL password
    score : score from 0-5

    Returns:

    ok or error
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        remote_addr = self.request.remote_addr
        allow = ip.allow(remote_addr)
        if not allow:
            self.response.clear()
            self.response.set_status(500)
            self.response.out.write('Rate limited exceeeded.')
        else:
            www.serve(self, self.__doc__)

class QueueView(webapp.RequestHandler):
    """
    /queue/view

    Loads an HTML interface to view, translate and score items in the
    community translation queue. This view is initiated by linking to the
    URL:

    www.worldwidelexicon.org/queue/view?sl=lang1&tl=lang2&domain=optionaldomain&tag=optionaltag

    It will display a list of jobs that are awaiting translation from the source to the
    target language, and it will display a list of jobs that are waiting to be scored. The user
    interface is pretty basic, and does not use Flash, AJAX or other technologies so that it will
    work on a wide range of browsers, including mobile devices.

    If it senses the user is connecting from something other than Firefox, Safari, Chrome or
    Internet Explorer, it will assume the user is connecting via a mobile browser and will display
    fewer results and simplify the interface. It should work on any browser, including old text
    mode browsers for mobile phones. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        domain = self.request.get('domain')
        tag = self.request.get('tag')
        if len(sl) > 0 and len(tl) > 0:
            qdb = db.Query(Queue)
            qdb.filter('sl = ', sl)
            qdb.filter('tl = ', tl)
            if len(domain) > 0:
                qdb.filter('domain = ', domain)
            qdb.filter('translated = ', False)
            qdb.order('createdon')
            results = qdb.fetch(limit=100)
            self.response.out.write('<h2><img src=/logo align=left>Worldwide Lexicon Translation Queue</h2><br><hr>')
            self.response.out.write('<table><tr><td><b>Original Text</b></td><td><b>Translation</b></td><td></td></tr>')
            for r in results:
                self.response.out.write('<tr valign=top><td>' + r.st + '</td>')
                self.response.out.write('<form action=/queue/submit method=get><td><textarea name=tt>' + r.tt + '</textarea></td>')
                self.response.out.write('<td><input type=submit value="Save"></td></tr></form>')
            self.response.out.write('</table>')
        else:
            self.response.out.write('<h2><img src=/logo align=left>Worldwide Lexicon Translations</h2>')
            self.response.out.write('<br><hr>')
            self.response.out.write('<form action=/queue/view method=get><table>')
            self.response.out.write('<tr><td>Source Language Code</td><td><input type=text name=sl maxlength=3></td></tr>')
            self.response.out.write('<tr><td>Target Language Code</td><td><input type=text name=tl maxlength=3></td></tr>')
            self.response.out.write('<tr><td>Optional Domain</td><td><input type=text name=domain></td></tr>')
            self.response.out.write('<tr><td>Optional Tag / Keyword</td><td><input type=text name=tag></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Go To Translation Queue"></td></tr>')
            self.response.out.write('</table></form>')
            self.response.out.write('<hr>')

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
            if len(url) > 0:
                p = dict()
                p['remote_addr']=self.request.remote_addr
                p['url']=url
                p['sl']=sl
                p['tl']=tl
                taskqueue.add(url='/log', params=p)
            results = Translation.fetch(sl=sl, st=st, tl=tl, domain='', url=url, userip=remote_addr, allow_machine=allow_machine, allow_anonymous=allow_anonymous, min_score=minimum_score, max_blocked_votes=max_blocked_votes, fuzzy=fuzzy, lsp=lsp, lspusername=lspusername, lsppw=lsppw)
            if len(results) < 1 or fuzzy=='y':
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
            self.response.out.write('<tr><td>Language Servuce Provider (lsp)</td><td><input type=text name=lsp></td></tr>')
            self.response.out.write('<tr><td>LSP Username</td><td><input type=text name=lspusername></td></tr>')
            self.response.out.write('<tr><td>LSP Password</td><td><input type=text name=lsppw></td></tr>')
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
    apikey - API key (for trusted submitters and LSPs)
    
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
        # check if this IP address is rate limited, if yes return a 500 error
        result = ip.allow(remote_addr)
        if not result:
            self.response.clear()
            self.response.set_status(500)
            self.response.out.write('Rate limit exceeded')
            return
        # IP address is not rate limited, proceed normally
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
        if not spam:
            result = Translation.submit(sl=sl, st=st, tl=tl, tt=tt, username=username, remote_addr=remote_addr, domain=domain, url=url, city=city, state=state, country=country, latitude=latitude, longitude=longitude, lsp=lsp, proxy=proxy, apikey=apikey)
        else:
            result = True
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
                self.response.out.write('<tr><td>API Key</td><td><input type=text name=apikey></td></tr>')
                self.response.out.write('<tr><td>Output format</td><td><input type=text name=output value=text></td></tr>')
                self.response.out.write('<tr><td colspan=2><input type=submit value=OK></td></tr>')
                self.response.out.write('</table></form>')
    def post(self):
        """ Processes HTTP POST calls """
        self.requesthandler()
    def get(self):
        """ Processes HTTP GET calls """
        self.requesthandler()
    
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

    NOTE: we _strongly_ recommend that you use the POST method to submit texts for translation.
    You can use HTTP GET for ASCII texts, but it will frequently break if you are submitting
    UTF-8 (Unicode) texts. This happens because of the way characters are escape encoded in URLs.
    We also recommend using POST because of the URL length limits that apply to GET queries. 
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
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        allow_anonymous = self.request.get('allow_anonymous')
        allow_machine = self.request.get('allow_machine')
        min_score = self.request.get('min_score')
        output = self.request.get('output')
        mtengine = self.request.get('mtengine')
        queue = self.request.get('queue')
        ip = self.request.get('ip')
        hostname = self.request.get('hostname')
        st = urllib.unquote(st)
        st = transcoder.clean(st)
        m = md5.new()
        m.update(sl)
        m.update(tl)
        m.update(st)
        m.update(lsp)
        md5hash = str(m.hexdigest())
        if len(output) < 2:
            output = 'text'
        text = memcache.get('/t/' + md5hash + '/' + output)
        self.response.headers['Accept-Charset'] = 'utf-8'
        if text is not None:
            if output == 'xml' or output == 'rss':
                self.response.headers['Content-Type']='text/xml'
            elif output == 'html':
                self.response.headers['Content-Type']='text/html'
            else:
                self.response.headers['Content-Type']='text/plain'
            self.response.out.write(text)
            return
        if len(tl) > 0 and len(st) > 0:
            tt = Translation.lucky(sl=sl, tl=tl, st=st, allow_anonymous=allow_anonymous, allow_machine=allow_machine, min_score=min_score, output=output, lsp=lsp, lspusername=lspusername, lsppw = lsppw, mtengine=mtengine, queue=queue, ip=ip, userip=userip, hostname=hostname)
            if output == 'text':
                self.response.headers['Content-Type']='text/plain'
                self.response.out.write(tt)
                text = tt
            else:
                d = DeepPickle()
                p = dict()
                p['sl']=sl
                p['tl']=tl
                p['st']=st
                p['tt']=tt
                text = d.makeRow(p, output)
                if output == 'xml' or output == 'rss':
                    text = '<item>' + text + '</item>'
                    self.response.headers['Content-Type']='text/xml'
                    self.response.out.write(text)
                else:
                    self.response.headers['Content-Type']='text/html'
                    self.response.out.write(text)
            if len(text) > 0:
                memcache.set('/t/' + md5hash + '/' + output, text, 300)
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
            self.response.out.write('<tr><td>Output Format</td><td><input type=text name=output value=text></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=GO></td></tr>')
            self.response.out.write('</form></table>')
            
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
        
class BatchTranslation(webapp.RequestHandler):
    """
    /batch

    Batch translation request handler. This request handler allows a client to submit a batch of texts to
    be translated, and to requery in a separate transaction if desired. This request handler will spawn
    a number of parallel queries that, in turn, write back to memcached. This allows for fast response
    times on queries for a large number of texts. It expects the following parameters:

    sl = source language
    tl = target language
    st0..199 = source text to translate
    allow_machine = y/n (use machine translation)
    lsp = name of LSP, if requesting professional translations
    lspusername = username for LSP query
    lsppw = pw or API key for LSP query
    guid = MD5hash (if repeating a recently submitted query)
    async = y/n (if yes, returns an MD5hash, and expects user to re-query after some delay)
    output = xml, rss, or json
    
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
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
                text = memcache.get('/batch/' + guid + '/' +output + '/' + str(ctr))
                if text is not None:
                    self.response.out.write(text)
                ctr = ctr + 1
        else:
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
                    stext = st.get(ctr)
                    if len(stext) > 1:
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
                www.serve(self,self.__doc__, title='/batch')
                self.response.out.write('<table><form action=/batch method=get>')
                self.response.out.write('<tr><td>Async Query</td><td><input type=text name=async value=n></td></tr>')
                self.response.out.write('<tr><td>Source Language</td><td><input type=text name=sl></td></tr>')
                self.response.out.write('<tr><td>Target Language</td><td><input type=text name=tl></td></tr>')
                self.response.out.write('<tr><td>Output Format</td><td><input type=text name=output value=rss></td></tr>')
                ctr = 0
                while ctr < 20:
                    self.response.out.write('<tr><td>Source Text #' + str(ctr+1) + '</td>')
                    self.response.out.write('<td><input type=text name=st' + str(ctr) + '></td></tr>')
                    ctr = ctr + 1
                self.response.out.write('<tr><td colspan=2><input type=submit value="OK"></td></tr>')
                self.response.out.write('</form></table>')
                
application = webapp.WSGIApplication([('/q', GetTranslations),
                                      ('/batch', BatchTranslation),
                                      ('/log', LogQueries),
                                      ('/queue/add', AddQueue),
                                      ('/queue/send', SendLSP),
                                      ('/queue/search', SearchQueue),
                                      ('/queue/score', QueueScore),
                                      ('/queue/view', QueueView),
                                      ('/queue/submit', QueueSubmit),
                                      (r'/t/(.*)/(.*)/(.*)', SimpleTranslation),
                                      (r'/t/(.*)/(.*)', SimpleTranslation),
                                      ('/t', SimpleTranslation),
                                      ('/submit', SubmitTranslation)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
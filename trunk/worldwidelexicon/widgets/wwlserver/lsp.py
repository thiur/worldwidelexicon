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

Copyright (c) 1998-2010, Worldwide Lexicon Inc.
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
    def get(sl, tl, st, domain='', url='', lsp='', lspusername='', lsppw='', ttl = 1800):
        """
        This function is checks memcached for a cached translation from the desired LSP and text,
        and if one is cached locally returns it. If the cache has expired or does not exist, it
        makes an HTTP/S call to the language service provider to request the translation. The LSP
        will return either a blank text, a completed translation or an HTTP error. 
        """
        if lsp == 'speaklike':
            lsp = 'speaklikeapi'
        if len(lsp) > 0 and len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            baseurl = None
            #baseurl = memcache.get('/lsp/url/' + lsp)
            if baseurl is None:
                baseurl = APIKeys.geturl(lsp=lsp)
                if len(baseurl) > 0:
                    memcache.set('/lsp/url/' + lsp, baseurl, 1800)
            apikey = None
            #apikey = memcache.get('/lsp/apikey/' + lsp)
            if apikey is None:
                apikey = APIKeys.getapikey(lsp)
                if len(apikey) > 0:
                    memcache.set('/lsp/apikey/' + lsp, apikey, 1800)
            if len(baseurl) > 0:
                st = clean(st)
                m = md5.new()
                m.update(sl)
                m.update(tl)
                m.update(st)
                guid = str(m.hexdigest())
                text = memcache.get('/lspd/' + lsp + '/' + guid)
                if text is not None:
                    return text
                else:
                    # generate and send HTTP query to language service provider
                    fullurl = baseurl + '/t'
                    parms = dict()
                    parms['sl']=sl
                    parms['tl']=tl
                    parms['st']=st
                    parms['domain']=domain
                    parms['url']=url
                    parms['lspusername']=lspusername
                    parms['lsppw']=lsppw
                    parms['apikey']=apikey
                    parms['output']='json'
                    form_data = urllib.urlencode(parms)
                    try:
                        result = urlfetch.fetch(url=fullurl, payload = form_data, method = urlfetch.POST, headers = {'Content-Type' : 'application/x-www-form-urlencoded' , 'Accept-Charset' : 'utf-8'})
                        status_code = result.status_code
                    except:
                        result = None
                        status_code = 500
                    if status_code == 200:
                        tt = result.content
                    else:
                        tt = ''
                    # check to see if response is in JSON format and contains
                    # a guid field.
                    try:
                        results = demjson.decode(tt)
                        tt = results.get('tt','')
                    except:
                        results = dict()
                        results['guid']=''
                        results['tt']=tt
                        results['st']=st
                        results['sl']=sl
                        results['tl']=tl
                    if len(tt) > 0 and status_code == 200:
                        found = True
                        memcache.set('/lsp/' + lsp + '/' + guid, tt, ttl)
                        memcache.set('/lspd/' + lsp + '/' + guid, results, ttl)
                    else:
                        found = False
                    return results
            else:
                    return ''
        else:
            return ''
    @staticmethod
    def score(guid, score, lsp='', sl='', tl='', st='', tt='', domain='', url='', remote_addr=''):
        if lsp == 'speaklike':
            lsp = 'speaklikeapi'
        baseurl = ''
        apikey = ''
        if len(guid) > 0:
            baseurl = APIKeys.geturl(lsp=lsp)
            apikey = APIKeys.getapikey(lsp)
            if len(baseurl) > 0:
                fullurl = baseurl + '/scores/vote'
                p = dict()
                p['guid'] = guid
                p['score']=str(score)
                p['sl']=sl
                p['tl']=tl
                p['st']=st
                p['tt']=tt
                p['domain']=domain
                p['url']=url
                p['remote_addr']=remote_addr
                p['apikey']=apikey
                form_data = urllib.urlencode(p)
                try:
                    result = urlfetch.fetch(url=fullurl, payload=form_data, method = urlfetch.POST, headers = {'Content-Type' : 'application/x-www-form-urlencoded' , 'Accept-Charset' : 'utf-8'})
                    if result.status_code == 200:
                        return True
                    else:
                        return False
                except:
                    return False
        return False
    @staticmethod
    def comment(guid, comment, lsp='', username='', remote_addr=''):
        if lsp == 'speaklike':
            lsp = 'speaklikeapi'
        baseurl = ''
        apikey = ''
        if len(guid) > 0:
            baseurl = APIKeys.geturl(lsp=lsp)
            apikey = APIKeys.getapikey(lsp)
        if len(baseurl) > 0:
            fullurl = baseurl + '/comments/submit'
            p = dict()
            p['guid']=guid
            p['comment']=comment
            p['username']=username
            p['remote_addr']=remote_addr
            p['apikey']=apikey
            form_data = urllib.urlencode(p)
            try:
                result = urlfetch.fetch(url=fullurl, payload=form_data, method = urlfetch.POST, headers = {'Content-Type' : 'application/x-www-form-urlencoded' , 'Accept-Charset' : 'utf-8'})
                if result.status_code == 200:
                    return True
                else:
                    return False
            except:
                return False
        else:
            return False

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
            www.serve(self, t, sidebar = doc_text, title = '/lsp/test (LSP Interface Test Form)')

class TestScore(webapp.RequestHandler):
    """
    <h3>/lsp/testscore</h3>

    This is a test form you can use to submit a score to your translation management system, to
    simulate end user scores being submitted from WWL based translation viewers and editors. The
    system will submit a score to a form handler at {baseurl}/scores/vote on your system with the
    following parameters:<p>

    <ul>
    <li>guid : a unique record locator in your system</li>
    <li>score : a quality score from 0..5 where 0=spam</li>
    <li>lsp : LSP nickname (e.g. speaklikeapi)</li>
    <li>username : optional username or email of the score submitter</li>
    <li>remote_addr : IP address of submitter</li>
    <li>comment : optional comment for translator</li>
    </ul>

    It will reply with ok or an error message, and if successful, you should see this form repost
    to your system.
    """
    def get(self):
        guid = self.request.get('guid')
        lsp = self.request.get('lsp')
        score = self.request.get('score')
        username = self.request.get('username')
        remote_addr = self.request.get('remote_addr')
        comment = clean(self.request.get('clean'))
        if len(guid) > 0:
            if LSP.score(guid, score, lsp = lsp, username = username, remote_addr = remote_addr, comment = comment):
                self.response.out.write('ok')
            else:
                self.error(500)
                self.response.out.write('error')
        else:
            t = '<table><form action=/lsp/testscore method=get>'
            t = t + '<tr><td>GUID</td><td><input type=text name=guid></td></tr>'
            t = t + '<tr><td>LSP</td><td><input type=text name=lsp></td></tr>'
            t = t + '<tr><td>Score (0..5)</td><td><input type=text name=score></td></tr>'
            t = t + '<tr><td>Username</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>User IP</td><td><input type=text name=remote_addr></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = self.__doc__, title = '/lsp/testscore')

class TestComment(webapp.RequestHandler):
    """
    <h3>/lsp/testcomment</h3>

    This is a test form you can use to submit comments back to your translation management system.
    It expects the following parameters, and will report this form to your system at:
    {baseurl}/comments/submit:<p>

    <ul>
    <li>guid : unique record locator (from your system)</li>
    <li>lsp : LSP nickname (e.g. speaklikeapi)</li>
    <li>comment : comment text</li>
    <li>username : optional submitter username or email</li>
    <li>remote_addr : submitter IP address</li>
    </ul>
    """
    def get(self):
        guid = self.request.get('guid')
        lsp = self.request.get('lsp')
        comment = self.request.get('comment')
        username = self.request.get('username')
        remote_addr = self.request.get('remote_addr')
        if len(guid) > 0:
            if LSP.comment(guid, comment, lsp = lsp, username = username, remote_addr = remote_addr):
                self.response.out.write('ok')
            else:
                self.error(500)
                self.response.out.write('error')
        else:
            t = '<table><form action=/lsp/testcomment method=get>'
            t = t + '<tr><td>GUID</td><td><input type=text name=guid></td></tr>'
            t = t + '<tr><td>LSP</td><td><input type=text name=lsp></td></tr>'
            t = t + '<tr><td>Comment</td><td><input type=text name=comment></td></tr>'
            t = t + '<tr><td>Username</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>User IP</td><td><input type=text name=remote_addr></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar = self.__doc__, title = '/lsp/testcomment')

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
            www.serve(self, t, sidebar = doc_text, title='/lsp/submit (LSP Submit Interface)')

application = webapp.WSGIApplication([('/lsp/submit', SubmitTranslation),
                                      ('/lsp/testscore', TestScore),
                                      ('/lsp/testcomment', TestComment),
                                      ('/lsp/test', TestTranslation)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
    main()

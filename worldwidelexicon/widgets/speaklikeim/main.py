# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os.path
import wsgiref.handlers
import string
import md5
import datetime
import time
import urllib
import codecs
import demjson

from google.appengine.api import users
from google.appengine.api import xmpp
from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.api import channel

from BeautifulSoup import BeautifulSoup

def clean(text):
    soup = BeautifulSoup(text)
    return soup.renderContents()

def detectLanguage(text):
    text = clean(text)
    encodedtext = urllib.quote_plus(text)
    url = 'http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&userip=208.113.71.138&q=' + encodedtext
    response = urlfetch.fetch(url = url)
    if response.status_code == 200:
        results = demjson.decode(response.content)
    try:
        sl = results['responseData']['language']
    except:
        sl = ''
    return sl

def mt(sl, tl, st, userip='208.113.71.138',apikey='AIzaSyDvvlNuNLEmVqWllNRM2BoyxnZdd44TjQY'):
    st=urllib.quote_plus(clean(st))
    url='https://www.googleapis.com/language/translate/v2?key={apikey}&source={sl}&target={tl}&q={st}'
    url=string.replace(url,'{sl}',sl)
    url=string.replace(url,'{tl}',tl)
    url=string.replace(url,'{st}',st)
    url=string.replace(url,'{apikey}',apikey)
    #try:
    result = urlfetch.fetch(url=url)
    #try:
    results = demjson.decode(result.content)
    translations = results['data']['translations']
    tt = ''
    for t in translations:
        tt = t.get('translatedText','')
    clean (tt)
    return tt

def languageDetect(text):
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
        confidence = results['responseData']['confidence']
    except:
        sl = ''
        confidence = 0.0
    response = dict(
        language=sl,
        confidence=confidence,
    )
    return demjson.encode(response)

def SpeakLikeStartSession(username,pw,languages, callback_url, debug=False):
    xml = """<SLClientMsg>
<cmd type="Login" id="1">
<responseFormat>json</responseFormat>
<u>{username}</u>
<p>{pw}</p>
</cmd>
<cmd type="NewTranslationSession" id="2">
<documentType>text</documentType>
<sourceLangs>
{langtext}
</sourceLangs>
<targetLangs>
{langtext}
</targetLangs>
<eventCallbackUrl>{url}</eventCallbackUrl>
<tag>foo</tag>
</cmd>
</SLClientMsg>
"""
    xml = urllib.unquote_plus(xml)
    xml = string.replace(xml,'{username}',username)
    xml = string.replace(xml,'{pw}',pw)
    langtext=''
    for l in languages:
        langtext = langtext + '<langId>' + l + '</langId>'
    xml = string.replace(xml, '{langtext}', langtext)
    xml = string.replace(xml, '{url}', callback_url)
    url = 'http://api.speaklike.com/REST/controller/send'
    headers = {
        "Content-Size" : len(xml),
        "Content-Type" : "text/plain",
        }
    response = urlfetch.fetch(url=url, method=urlfetch.POST, payload=xml, headers=headers)
    if debug:
        return response.content
    error = ''
    session = ''
    result = demjson.decode(response.content)
    cmdResponses = result.get('cmdResponses')
    login = False
    success = False
    error = False
    for c in cmdResponses:
        if c.get('id','') == '1':
            if c.get('success','') == 'true':
                login = True
        if c.get('id','') == '2':
            if c.get('success','') == 'true':
                success=True
                sessioninfo = c.get('sessionInfo')
                session = sessioninfo.get('sessionId','')
                error_code = ''
            else:
                error = True
                error_code = c.get('error','')
    response = dict(
        session = session,
        error = error,
        error_code = error,
        success = success,
        login = login,
    )
    return response

def SpeakLikeStopSession(username, pw, session, debug=False):
    xml = """<SLClientMsg>
<cmd type="Login" id="1">
<responseFormat>json</responseFormat>
<u>{username}</u>
<p>{pw}</p>
</cmd>
<cmd type="StopTranslationSession" id="2">
<sessionId>{session}</sessionId>
</cmd>
</SLClientMsg>
"""
    xml = urllib.unquote_plus(xml)
    xml = string.replace(xml,'{username}',username)
    xml = string.replace(xml,'{pw}',pw)
    xml = string.replace(xml, '{session}', session)
    url = 'http://api.speaklike.com/REST/controller/send'
    headers = {
        "Content-Size" : len(xml),
        "Content-Type" : "text/plain",
        }
    response = urlfetch.fetch(url=url, method=urlfetch.POST, payload=xml, headers=headers)
    if debug:
        return response.content
    try:
        error = ''
        session = ''
        result = demjson.decode(response.content)
        cmdResponses = result.get('cmdResponses')
        login = False
        success = False
        for c in cmdResponses:
            if c.get('id','') == '1':
                if c.get('success','') == 'true':
                    login = True
            if c.get('id','') == '2':
                if c.get('success','') == 'true':
                    success = True
                else:
                    error = c.get('error','')
        response = dict(
            session = session,
            error = error,
            success = success,
            login = login,
        )
        return response
    except:
        response = dict(
            session = '',
            error = 'SERVER_NOT_AVAILABLE',
            success = False,
            login = False,
        )
        return response

def SpeakLikeRequestTranslation(username, pw, session, sl, tl, text, guid=''):
    xml = """<SLClientMsg>
<cmd type="Login" id="1">
<responseFormat>json</responseFormat>
<u>{username}</u>
<p>{pw}</p>
</cmd>
<cmd type="TranslateDocument" id="2">
<sessionId>{session}</sessionId>
<document>
<originalLangId>{sl}</originalLangId>
<targetLangId>{tl}</targetLangId>
<mimeType>text</mimeType>
<contents>{text}</contents>
<guid>{guid}</guid>
</document>
</cmd>
</SLClientMsg>
"""
    callback_url = 'http://speaklikeim.appspot.com/realtime/channel'
    xml = urllib.unquote_plus(xml)
    xml = string.replace(xml, '{username}', username)
    xml = string.replace(xml, '{pw}', pw)
    xml = string.replace(xml, '{session}', session)
    xml = string.replace(xml, '{sl}', sl)
    xml = string.replace(xml, '{tl}', tl)
    xml = string.replace(xml, '{text}', text)
    xml = string.replace(xml, '{guid}', guid)
    url = 'http://api.speaklike.com/REST/controller/send'
    headers = {
        "Content-Size" : len(xml),
        "Content-Type" : "text/plain",
        }
    response = urlfetch.fetch(url=url, method=urlfetch.POST, payload=xml, headers=headers)
    try:
        result = demjson.decode(response.content)
        cmdResponses = result.get('cmdResponses')
        login = False
        success = False
        for c in cmdResponses:
            if c.get('id','') == '2':
                if c.get('success','') == 'true':
                    success=True
                    return True
        return False
    except:
        return False

class Messages(db.Model):
    session = db.StringProperty(default='')
    guid = db.IntegerProperty(default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    sender = db.StringProperty(default='')
    name = db.StringProperty(default='')
    language = db.StringProperty(default='')
    text = db.TextProperty(default='')
    original = db.BooleanProperty(default=False)
    @staticmethod
    def post(session, sender, name, language, text):
        if len(session) > 0 and len(sender) > 0 and len(text) > 0:
            mdb = db.Query(Messages)
            mdb.filter('session = ', session)
            mdb.order('-guid')
            item = mdb.get()
            if item is not None:
                lastmsg = item.guid
            else:
                lastmsg = None
            if lastmsg is not None:
                currentmsg = 0
            else:
                currentmsg = lastmsg + 1
            item = Messages()
            item.guid = currentmsg
            item.session = session
            item.sender = sender
            item.name = name
            item.language = language
            item.text = db.Text(text)
            item.original = True
            item.put()
            return currentmsg
        else:
            return
    @staticmethod
    def translate(session, guid, language, text):
        if len(session) > 0 and len(text) > 0:
            if type(guid) is str: guid = int(guid)
            mdb = db.Query(Messages)
            mdb.filter('session = ', session)
            mdb.filter('guid = ', guid)
            mdb.filter('original = ', True)
            item = mdb.get()
            sender = item.sender
            name = item.name
            item = Messages()
            item.session = session
            item.guid = guid
            item.sender = sender
            item.name = name
            item.original = False
            item.language = language
            item.text = db.Text(text)
            item.put()
    @staticmethod
    def transcript(session, languages=None):
        if len(session) > 0:
            mdb = db.Query(Messages)
            mdb.filter('session = ', session)
            mdb.order('guid')
            results = mdb.fetch(250)
            messages = list()
            for r in results:
                message = dict(
                    session = r.session,
                    guid = r.guid,
                    created = str(r.created),
                    sender = r.sender,
                    name = r.name,
                    language = r.language,
                    text = r.text,
                )
                if type(languages) is list:
                    if r.language in languages:
                        messages.append(message)
                else:
                    messages.append(message)
            return messages
                
class Sessions(db.Model):
    session = db.StringProperty(default='')
    mode = db.StringProperty(default='')
    name = db.StringProperty(default='')
    languages = db.ListProperty(str)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    createdby = db.StringProperty(default='')
    token = db.StringProperty(default='')
    xmpp_address = db.StringProperty(default='')
    callback_url = db.StringProperty(default='')
    username = db.StringProperty(default='')
    pw = db.StringProperty(default='')
    @staticmethod
    def getBySession(session):
        sdb = db.Query(Sessions)
        sdb.filter('session = ', session)
        item = sdb.get()
        if item is not None:
            return item
    @staticmethod
    def purge():
        day_ago = datetime.datetime.now() + datetime.timedelta(minutes=-15)
        sdb = db.Query(Sessions)
        sdb.filter('updated <', day_ago)
        results = sdb.fetch(100)
        if results is not None:
            records = len(results)
            db.delete(results)
        else:
            records = 0
        return len(records)
    @staticmethod
    def start(username, pw, languages, callback_url='', token='', mode='', xmpp_address='', debug=False):
        item = Sessions()
        if type(languages) is not list:
            languages=string.split(languages,',')
        # replace this with call to SpeakLike API to validate and start session
        result = SpeakLikeStartSession(username, pw, languages, callback_url, debug)
        session = ''
        if debug:
            return result
        if result is not None:
            session = result.get('session','')
            if len(session) > 0:
                # end comment
                item = Sessions()
                item.username = username
                item.pw = pw
                if not debug:
                    item.session=str(session)
                item.createdby=username
                item.languages=languages
                if mode == 'xmpp':
                    item.mode = 'xmpp'
                    item.callback_url = callback_url
                    if len(xmpp_address) < 1:
                        item.xmpp_address = username
                elif mode == 'socket':
                    item.mode = 'socket'
                    item.callback_url = callback_url
                    token = channel.create_channel(username)
                    item.token = token
                else:
                    if len(callback_url) > 0:
                        item.mode = 'rest'
                        item.key = key
                        item.callback_url = callback_url
                    else:
                        response = dict(
                            error = True,
                            error_code = 400,
                            reason = "No callback URL specified",
                        )
                        return response
                if not debug:
                    item.put()
                error = False
                error_code = result['error_code']
            else:
                error = True,
                error_code = result['error_code']
            response = dict(
                error = result['error'],
                error_code = error_code,
                reason = "ok",
                session = session,
                mode = mode,
                token = token,
            )
            return response
        else:
            response = dict(
                error = True,
                error_code = "Invalid request",
            )
            return response
    @staticmethod
    def stop(session, username='', pw='', debug=False):
        sdb = db.Query(Sessions)
        sdb.filter('session = ', session)
        item = sdb.get()
        if item is not None:
            item.delete()
        return SpeakLikeStopSession(username, pw, session, debug=debug)
    @staticmethod
    def url(session):
        sdb = db.Query(Sessions)
        sdb.filter('session = ', session)
        item = sdb.get()
        if item is not None:
            callback_url = item.callback_url
            if string.count(callback_url, 'http://') < 1 and string.count(callback_url, 'https://') < 1:
                callback_url = 'http://' + callback_url
            return callback_url
        else:
            return ''
    @staticmethod
    def user(username):
        sdb = db.Query(Sessions)
        sdb.filter('createdby = ', username)
        item = sdb.get()
        if item is not None:
            return item.session
        else:
            return ''
    @staticmethod
    def valid(session):
        sdb = db.Query(Sessions)
        sdb.filter('session = ', session)
        item = sdb.get()
        if item is not None:
            return True
        else:
            return False

class Translations(db.Model):
    session = db.StringProperty(default='')
    guid = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    st = db.StringProperty(default='',multiline=True)
    tt = db.StringProperty(default='',multiline=True)
    username = db.StringProperty(default='')
    date = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def find(sl,tl,st):
        tdb = db.Query(Translations)
        tdb.filter('sl = ', sl)
        tdb.filter('tl = ', tl)
        tdb.filter('st = ', st)
        tdb.order('-date')
        item = tdb.get()
        return item
    @staticmethod
    def submit(sl,tl,st,tt,session='',guid='',username=''):
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0 and len(tt) > 0:
            item = Translations()
            item.sl = sl
            item.tl = tl
            item.st = db.Text(st)
            item.tt = db.Text(tt)
            item.session = session
            item.guid = guid
            item.username = username
            item.put()
            return True
        return False
    
class SendHandler(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        user = self.request.get('user')
        message = self.request.get('message')
        languages = self.request.get('languages')
        if len(languages) > 0:
            Presence.add(user,languages)
        if len(user) > 0 and len(message) > 0:
            status = xmpp.send_message(user,message)
            if status == xmpp.NO_ERROR:
                self.response.out.write('ok')
            else:
                self.error(400)
                self.response.out.write('Message not sent')

class XMPPTranslateHandler(webapp.RequestHandler):
    def post(self):
        session = self.request.get('session')
        text = self.request.get('text')
        mode = self.request.get('mode')
        sdb = db.Query(Sessions)
        sdb.filter('session = ', session)
        item = sdb.get()
        if item is not None:
            languages = item.languages
            sl = detectLanguage(text)
            for l in languages:
                if l != sl:
                    tl = l
            tt = mt(sl, tl, text)
            if mode == 'xmpp':
                text = dict(
                    action = 'translation',
                    session = session,
                    sl = sl,
                    tl = tl,
                    st = st,
                    tt = tt,
                )
                text = demjson.encode(text)
            else:
                text = 'Translation: [' + sl + ' --> ' + tl + '] ' + text + ' / ' + tt
            p = dict(
                session = session,
                text = text,
            )
            time.sleep(3)
            taskqueue.add(url='/realtime/xmpp_post', params=p)
        self.response.out.write('ok')

class XMPPPostHandler(webapp.RequestHandler):
    def post(self):
        action = self.request.get('action')
        session = self.request.get('session')
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('sl')
        tt = self.request.get('tt')
        guid = self.request.get('guid')
        sdb = db.Query(Sessions)
        sdb.filter('session = ', session)
        item = sdb.get()
        if item is not None:
            rcpt = item.createdby
            p = dict(
                sl = sl,
                tl = tl,
                st = st,
                tt = tt,
                guid = guid,
                session = session,
            )
            text = demjson.encode(p)
            xmpp.send_message(rcpt,text)
        self.response.out.write('ok')

def parse_JSON(json):
    action = json.get('action','')
    if action == 'start':
        key = json.get('key','')
        user = json.get('username','')
        languages = json.get('languages','')
        callback_url = json.get('callback_url','')
        session = Sessions.start(user, key, languages, 'speaklikeim.appspot.com/realtime/xmpp_post')
        response = dict(
            session = session,
            key = key,
            languages=languages,
            callback_url="speaklikeim.appspot.com/realtime/xmpp_post",
        )
        return demjson.encode(response)
    elif action == 'stop':
        session = json.get('session','')
        result = Sessions.stop(session)
        if result:
            response = dict(
                session = session,
                status = "ok",
            )
        else:
            response = dict(
                session = session,
                status = "error",
                reason = "session not found",
            )
        return demjson.encode(response)
    elif action == 'translate':
        session = json.get('session','')
        sl = json.get('sl','')
        tl = json.get('tl','')
        st = json.get('st','')
        guid = json.get('guid','')
        p = dict(
            session = session,
            sl = sl,
            tl = tl,
            st = st,
            guid = guid,
        )
        taskqueue.add(url='/realtime/translate', params=p)
        response = dict(
            status = 'ok',
            session = session,
        )
        return demjson.encode(response)
    else:
        pass

class XMPPHandler(webapp.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        sender = message.sender
        sendstring = string.split(sender, '/')
        if len(sendstring) > 1:
            sender = sendstring[0]
        try:
            json = demjson.decode(message.body)
        except:
            json = None
        if json is not None:
            message.reply(parse_JSON(json))
        else:
            message.reply('Send a valid JSON command to start an XMPP session, in the form:')
            message.reply('To start a session, say: {"action":"start","username":"username","pw":"pw","key":"nickname","languages":"l1,l2"}')
            message.reply('To end a session, say: {"action":"stop","session":"sessionid"}')
            message.reply('To request a translation, say: {"action":"translate","session":"sessionid","sl":"sourcelang","tl":"targetlang","st":"sourcetext","guid":"messageid"}')
                    
class PresenceHandler(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        self.response.out.write('ok')

class SearchAgents(webapp.RequestHandler):
    def get(self, sl, tl):
        self.requesthandler(sl, tl)
    def post(self, sl, tl):
        self.requesthandler(sl, tl)
    def requesthandler(self, sl, tl):
        languages = [ sl, tl]
        results = Presence.search(languages)
        self.response.headers['Content-Type']='text/javascript'
        self.response.out.write(demjson.encode(results))

class AddAgent(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        user = self.request.get('user')
        languages = self.request.get('languages')
        languages = string.split(languages,',')
        if Presence.add(user, languages):
            self.response.out.write('ok')
        else:
            self.error(400)
            self.response.out.write('Unable to create user')

class StartSessionHandler(webapp.RequestHandler):
    """
    <h3>/realtime/start</h3>

    <p>This request handler is used to start a real-time translation session. It expects the following
    parameters:</p>

    <ul>
    <li>mode : interface type (rest or socket)</li>
    <li>username : SpeakLike username (or dummy for test calls)</li>
    <li>pw : SpeakLike password</li>
    <li>key : optional user assigned key or nickname for session</li>
    <li>languages : comma separated list of language codes</li>
    <li>callback_url : URL to submit translation and event messages to</li>
    <li>ajax : load demo AJAX code (y/n, default=n)
    </ul>

    <p>The request handler will respond with either an HTTP error message or a JSON dictionary containing the
    following fields:</p>

    <ul>
    <li>session : system assigned session ID</li>
    <li>key : user assigned session ID</li>
    <li>createdby : username</li>
    <li>languages : language codes</li>
    </ul>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        username = self.request.get('username')
        pw = self.request.get('pw')
        key = self.request.get('key')
        languages = self.request.get('languages')
        languages = string.split(languages,',')
        callback_url = self.request.get('callback_url')
        debug = self.request.get('debug')
        if debug == 'y':
            debug = True
        else:
            debug = False
        mode = self.request.get('mode')
        if mode == 'socket':
            callback_url = 'http://speaklikeim.appspot.com/realtime/channel'
        elif mode == 'xmpp':
            callback_url = 'http://speaklikeim.appspot.com/realtime/xmpp_post'
        else:
            pass
        ajax = self.request.get('ajax')
        if len(username) > 0:
            if len(key) < 1: key = 'rest_' + username
            response = Sessions.start(username, pw, languages, callback_url=callback_url, mode=mode, debug=debug)
            if debug:
                self.response.out.write(response)
            else:
                if not response['error']:
                    if ajax == 'y' and mode == 'socket':
                        path = os.path.join(os.path.dirname(__file__), "channel.html")
                        args = dict(
                            token = response.get('token',''),
                            session = response.get('session',''),
                        )
                        self.response.out.write(template.render(path, args))
                    else:
                        self.response.headers['Content-Type']='text/javascript'
                        self.response.out.write(demjson.encode(response))
                else:
                    self.error(400)
                    self.response.out.write(demjson.encode(response))
        else:
            self.error(400)
            doc_text = self.__doc__
            form = """
            <h3>[GET/POST] Start A Translation Session</h3>
            <table><form action=/realtime/start method=get>
            <tr><td>[mode] Session mode</td><td><select name=mode>
            <option selected value=rest>REST with callback</option>
            <option value=socket>Asynchronous socket</option></select></td></tr>
            <tr><td>[username] Username or email</td><td><input type=text name=username></td></tr>
            <tr><td>[pw] SpeakLike PW</td><td><input type=text name=pw></td></tr>
            <tr><td>[key] User assigned session ID or nickname</td><td><input type=text name=key></td></tr>
            <tr><td>[languages] Language codes (comma separated)</td><td><input type=text name=languages></td></tr>
            <tr><td>[callback_url] Callback URL to send translations and events to</td><td><input type=text name=callback_url></td></tr>
            <tr><td>[ajax] Load demo AJAX code</td><td><input type=text name=ajax value=n></td></tr>
            <tr><td>[debug] Debug SpeakLike response</td><td><input type=text name=debug value=n></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/realtime/start',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))
        
class StopSessionHandler(webapp.RequestHandler):
    """
    <h3>/realtime/stop</h3>

    <p>This request handler is used to end a translation session. It responds with OK or an error message.</p>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        session = self.request.get('session')
        debug = self.request.get('debug')
        if debug == 'y':
            debug=True
        else:
            debug=False
        if len(session) > 0:
            item = Sessions.getBySession(session)
            if item is not None:
                username = item.username
                pw = item.pw
            else:
                username = self.request.get('username')
                pw = self.request.get('pw')
            response = Sessions.stop(session, username, pw, debug)
            if debug:
                self.response.out.write(response)
            else:
                self.response.headers['Content-Type']='text/javascript'
                if response['error'] != '':
                    self.error(404)
                self.response.out.write(demjson.encode(response))
        else:
            self.error(401)
            doc_text = self.__doc__
            form = """
            <h3>[GET/POST] End Translation Session</h3>
            <table><form action=/realtime/stop method=get>
            <tr><td>[session] Session ID</td><td><input type=text name=session></td></tr>
            <tr><td>[username] SpeakLike username (if session=all)</td><td><input type=text name=username></td></tr>
            <tr><td>[pw] SpeakLike password (if session=all)</td><td><input type=text name=pw></td></tr>
            <tr><td>[debug] Debug SpeakLike response</td><td><input type=text name=debug value=n></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/realtime/stop',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class TranslateHandler(webapp.RequestHandler):
    """
    <h3>/realtime/translate</h3>

    <p>This API handler is used to request a translation for a text. You first need to start a real time
    translation session using the <a href=/realtime/start>/realtime/start</a> API call (to reserve translators
    to translate messages in real time). Once you have initiated a session, you simply call this API to request
    translations, which will be submitted to the callback URL associated with your session. The handler expects
    the following parameters:</p>

    <ul>
    <li>session : session ID</li>
    <li>guid : message ID or sequence number (optional but recommended because tranlations may not be returned in the same
    order</li>
    <li>sl : source language code</li>
    <li>tl : target language code</li>
    <li>st : source text (UTF8 encoding)</li>
    </ul>

    <p>The translation, along with event messages, will be submitted to the callback URL specified when you started
    the real time translation session. The callback handler should expect the following fields in an HTTP POST (form):</p>

    <ul>
    <li>action : translation|event</li>
    <li>session : session ID</li>
    <li>guid : optional message ID</li>
    <li>sl : source language code</li>
    <li>tl : target language code</li>
    <li>st : source text</li>
    <li>tt : translated text</li>
    </ul>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        session = self.request.get('session')
        guid = self.request.get('guid')
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('st')
        if len(st) > 0:
            item = Sessions.getBySession(session)
            if item is not None:
                username = item.username
                pw = item.pw
            else:
                username = self.request.get('username')
                pw = self.request.get('pw')
            response = dict(
                error = False,
                error_code = 200,
                reason = "ok",
            )
            if item is not None:
                mode = item.mode
                callback_url = item.callback_url
                if mode == 'socket':
                    callback_url = 'http://speaklikeim.appspot.com/realtime/channel'
                if callback_url == 'queue':
                    callback_url = 'http://speaklikeim.appspot.com/realtime/submit'
                result = SpeakLikeRequestTranslation(username, pw, session, sl, tl, st, guid)
                #tt = mt(sl, tl, st, userip=self.request.remote_addr)
                #p = dict(
                #    action = 'translation',
                #    mode = mode,
                #    callback_url = callback_url,
                #    session = session,
                #    guid = guid,
                #    sl = sl,
                #    tl = tl,
                #    st = st,
                #    tt = tt,
                #)
                #taskqueue.add(url='/realtime/callback', params=p, queue_name='slow')
                if result:
                    self.response.out.write(demjson.encode(response))
                else:
                    response['error']=True
                    response['error_code']=400
                    response['reason']='SpeakLike query failed'
                    self.error(400)
                    self.response.out.write(demjson.encode(response))
            else:
                response['error']=True
                response['error_code']=401
                response['reason']="Session not found"
                self.response.out.write(demjson.encode(response))
        else:
            self.error(400)
            doc_text = self.__doc__
            form = """
            <h3>[GET/POST] Request A Translation</h3>
            <table><form action=/realtime/translate method=get>
            <tr><td>[session] Session ID</td><td><input type=text name=session></td></tr>
            <tr><td>[sl] Source Language Code</td><td><input type=text name=sl></td></tr>
            <tr><td>[tl] Target Language Code</td><td><input type=text name=tl></td></tr>
            <tr><td>[st] Source Text (UTF8)</td><td><input type=text name=st></td></tr>
            <tr><td>[guid] Optional Message ID</td><td><input type=text name=guid></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/realtime/translate',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class LanguageDetectHandler(webapp.RequestHandler):
    """
    <h3>/realtime/language</h3>

    <p>This language detection API, powered by Google Translate, allows you to submit a text
    to be tested. It expects the parameter:</p>

    <ul><li>text : text to be tested</li>
    </ul>

    <p>It returns a JSON dictionary with the parameters:</p>
    <ul>
    <li>language : language code</li>
    <li>confidence : confidence level (0.0 to 1.0)</li>
    </ul>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        text = self.request.get('text')
        if len(text) > 0:
            response=languageDetect(text)
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(response)
        else:
            self.error(400)
            doc_text = self.__doc__
            form = """
            <h3>[GET/POST] Language Detection</h3>
            <table><form action=/realtime/language method=get>
            <tr><td>[text] Text to test</td><td><input type=text name=text></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/realtime/language',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class MachineTranslationHandler(webapp.RequestHandler):
    """
    <h3>/realtime/mt</h3>

    <p>This API handler enables you to request machine translations and receive an immediate response.
    The request handler expects the following parameters:</p>
    <ul>
    <li>sl : source language code</li>
    <li>tl : target language code</li>
    <li>st : source text</li>
    <li>apikey : Google Translate API key</li>
    </ul>
    <p>The request handler returns an HTTP error or JSON dictionary containing the following fields:</p>
    <ul>
    <li>sl : source language code</li>
    <li>tl : target language code</li>
    <li>st : source text</li>
    <li>tt : translated text</li>
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
        apikey = self.request.get('apikey')
        if len(st) > 0:
            try:
                if len(apikey) > 0:
                    tt = mt(sl, tl, st, apikey=apikey)
                else:
                    tt = mt(sl, tl, st)
                response = dict(
                    sl = sl,
                    tl = tl,
                    st = st,
                    tt = tt,
                )
                self.response.headers['Content-Type']='text/javascript'
                self.response.out.write(demjson.encode(response))
            except:
                self.error(401)
                self.response.out.write('Invalid request or API key')
        else:
            self.error(400)
            doc_text = self.__doc__
            form = """
            <h3>[GET/POST] Machine Translation (Google Translate)</h3>
            <table><form action=/realtime/mt method=get>
            <tr><td>[sl] Source Language Code</td><td><input type=text name=sl></td></tr>
            <tr><td>[tl] Target Language Code</td><td><input type=text name=tl></td></tr>
            <tr><td>[st] Text to Translate</td><td><input type=text name=st></td></tr>
            <tr><td>[apikey] Google Translate API Key</td><td><input type=text name=apikey></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/realtime/mt',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class QueueHandler(webapp.RequestHandler):
    """
    <h3>/realtime/queue</h3>

    <p>This API handler enables you to poll for recently completed translations if you
    are unable to use the asynchronous callback or socket interfaces. Note that this will
    introduce additional latency to your application, so we don't recommend this except when
    necessary or for prototyping purposes. The API expects the parameter:</p>

    <ul>
    <li>session : session ID</li>
    </ul>

    <p>The API returns a list of JSON dictionaries with up to 50 recent translations, sorted
    newest to oldest.</p>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        session = self.request.get('session')
        if len(session) > 0:
            tdb = db.Query(Translations)
            tdb.filter('session = ', session)
            tdb.order('-date')
            results = tdb.fetch(50)
            translations = list()
            for r in results:
                translation = dict(
                    session = r.session,
                    guid = r.guid,
                    sl = r.sl,
                    tl = r.tl,
                    st = r.st,
                    tt = r.tt,
                )
                translations.append(translation)
            json = demjson.encode(translations)
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(json)
        else:
            self.error(400)
            doc_text = self.__doc__
            form = """
            <h3>[GET/POST] Fetch Recent Translations From Queue</h3>
            <table><form action=/realtime/queue method=get>
            <tr><td>[session] Session ID</td><td><input type=text name=session></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/realtime/queue',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))   

class CallbackWorker(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        callback_url = self.request.get('callback_url')
        if len(callback_url) > 0:
            if callback_url == 'queue':
                callback_url = 'http://speaklikeim.appspot.com/submit'
            action = self.request.get('action')
            apikey = self.request.get('apikey')
            session = self.request.get('session')
            guid = self.request.get('guid')
            sl = self.request.get('sl')
            tl = self.request.get('tl')
            st = self.request.get('st')
            tt = self.request.get('tt')
            p = {
                "action" : action,
                "apikey" : apikey,
                "session" : session,
                "guid" : guid,
                "sl" : sl,
                "tl" : tl,
                "st" : clean(st),
                "tt" : clean(tt)
            }
            time.sleep(1)
            form_fields = urllib.urlencode(p)
            headers = {"Content-Type" : "application/x-www-form-urlencoded"}
            try:
                response=urlfetch.fetch(url=callback_url, payload=form_fields, method=urlfetch.POST, headers=headers, deadline=10)
            except:
                self.error(504)
        self.response.out.write('ok')

class ChannelHandler(webapp.RequestHandler):
    """
    <h3>[GET/POST] /realtime/channel</h3>

    <p>This API handler enables Javascript applications and widgets to receive asynchronous event notifications from
    the real-time translation server, and can be used to build human translated web chat applications. The GET version
    of the API is used to create a channel, while the POST handler is used to submit JSON messages and commands to the
    interface.</p>
    """
    def post(self):
        data = self.request.get('data')
        if len(data) > 0:
            json = demjson.decode(data)
        else:
            json = None
        if json is None:
            message = self.request.get('message')
            action = self.request.get('action')
            session = self.request.get('session')
            guid = self.request.get('guid')
            sl = self.request.get('sl')
            tl = self.request.get('tl')
            st = self.request.get('st')
            tt = self.request.get('tt')
        else:
            action = 'translation'
            message = ''
            session = json.get('sessionId','')
            document = json.get('document')
            sl = document.get('sourceLang','')
            st = document.get('sourceText','')
            guid = document.get('guid','')
            translations = document.get('translations')
            t = translations[0]
            tl = t.get('langId','')
            tt = t.get('body','')
        item = Sessions.getBySession(session)
        if item is not None:
            username = item.createdby
            text = dict(
                session = session,
                guid = guid,
                username = username,
                message = message,
                action = action,
                sl = sl,
                tl = tl,
                st = st,
                tt = tt,
            )
            json = demjson.encode(text)
            channel.send_message(username, json)
            self.response.out.write('ok')
        else:
            self.response.out.write('bad request')

class SubmitHandler(webapp.RequestHandler):
    """
    <h3>[GET/POST] /realtime/submit</h3>

    <p>This API handler receives completed translations back from the translation engine or professional
    translation service. It expects the following parameters:</p>

    <ul>
    <li>sl : source language code</li>
    <li>tl : target language code</li>
    <li>st : source text</li>
    <li>tt : translated text</li>
    <li>session : session key</li>
    <li>guid : optional message id or sequence number</li>
    <li>username : translator name or id</li>
    </ul>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('st')
        tt = self.request.get('tt')
        session = self.request.get('session')
        guid = self.request.get('guid')
        username = self.request.get('username')
        if len(sl) > 0 and len(tl) > 0:
            Translations.submit(sl,tl,st,tt,session=session,guid=guid,username=username)
            self.response.out.write('ok')
        else:
            doc_text = self.__doc__
            tdb = db.Query(Translations)
            tdb.order('date')
            item = tdb.get()
            guid = item.guid
            form = """
            <h3>[GET/POST] Submit Translation For A Message</h3>
            <table><form action=/realtime/submit method=post>
            <tr><td>[sl] Source Language Code</td><td><input type=text name=sl></td></tr>
            <tr><td>[tl] Target Language Code</td><td><input type=text name=tl></td></tr>
            <tr><td>[st] Source Text</td><td><input type=text name=st></td></tr>
            <tr><td>[tt] Translated Text</td><td><input type=text name=tt></td></tr>
            <tr><td>[session] Session Key</td><td><input type=text name=session></td></tr>
            <tr><td>[guid] Message ID or Seq #</td><td><input type=text name=guid></td></tr>
            <tr><td>[username] Translator name or ID</td><td><input type=text name=username></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/realtime/submit',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class TranslateURLHandler(webapp.RequestHandler):
    """
    <h3>/translate/url</h3>

    <p>This API call enables you to request translations for any URL on the public web.
    The SpeakLike service will crawl this page, and queue texts for professional translation.
    The API call expects the following parameters:</p>

    <ul>
    <li>url : URL to translate</li>
    <li>sl : source language code (if omitted, will auto-detect source language</li>
    <li>tl : target language code</li>
    <li>tags : optional list of HTML tags to translate (comma separated, e.g. a,b,h1,h2)</li>
    <li>username : SpeakLike username</li>
    <li>pw : SpeakLike password</li>
    <li>sla : optional service level agreement</li>
    <li>count : return word count before translating (y/n, if yes returns word count but does _not_
    initiate translation</li>
    </ul>

    <p>The service will response with a JSON response, which includes the following fields:</p>
    <ul>
    <li>url : URL translation will be hosted at</li>
    <li>eta : estimated job completion time, in minutes</li>
    <li>words : total word count</li>
    </ul>
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = self.request.get('url')
        language = self.request.get('language')
        username = self.request.get('username')
        pw = self.request.get('pw')
        if len(url) > 0:
            pass
        else:
            doc_text = self.__doc__
            tdb = db.Query(Translations)
            tdb.order('date')
            item = tdb.get()
            guid = item.guid
            form = """
            <h3>[GET/POST] Submit Translation For A Message</h3>
            <table><form action=/translate/url method=post>
            <tr><td>[url] URL to translate</td><td><input type=text name=url></td></tr>
            <tr><td>[sl] Source Language Code</td><td><input type=text name=sl></td></tr>
            <tr><td>[tl] Target Language Code</td><td><input type=text name=tl></td></tr>
            <tr><td>[tags] HTML tags to translate</td><td><input type=text name=tags value="h1,h2,h3,p,br,b,i,u,a"></td></tr>
            <tr><td>[sla] Service Level Agreement code</td><td><input type=text name=sla></td></tr>
            <tr><td>[username] SpeakLike username</td><td><input type=text name=username></td></tr>
            <tr><td>[pw] SpeakLike password</td><td><input type=text name=pw></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/translate/url',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class MainHandler(webapp.RequestHandler):
    """
    <h3>SpeakLike REST/Callback API</h3>
    <ul>
    <li><a href=/realtime/queue>/realtime/queue : Fetch Recent Translations (Polling API)</a></li>
    <li><a href=/realtime/start>/realtime/start : Start Translation Session</a></li>
    <li><a href=/realtime/stop>/realtime/stop : Stop Translation Session</a></li>
    <li><a href=/realtime/mt>/realtime/mt : Fetch Machine Translation</a></li>
    <li><a href=/realtime/language>/realtime/language : Detect Source Language</a></li>
    <li><a href=/realtime/translate>/realtime/translate : Request A Translation</a></li>
    </ul>
    <h3>Documentation</h3>
    <ul>
    <li><a href=/docs/realtime.pdf>Real-Time API Documentation</a></li>
    </ul>
    """
    def get(self):
        doc_text = self.__doc__
        form = """
        <p>Welcome to the Real Time API Server. This is currently in beta, and will be rolled out to
        im.speaklike.com in April/May 2011.</p>
        """
        path = os.path.join(os.path.dirname(__file__), "doc.html")
        args = dict(
            title = 'Real Time API',
            left_text = form,
            right_text = doc_text,
        )
        self.response.out.write(template.render(path, args))

application = webapp.WSGIApplication([('/realtime/add', AddAgent),
                                    ('/realtime/callback', CallbackWorker),
                                    ('/realtime/channel', ChannelHandler),
                                    ('/realtime/language', LanguageDetectHandler),
                                    ('/realtime/mt', MachineTranslationHandler),
                                    ('/realtime/xmpp_translate', XMPPTranslateHandler),
                                    ('/realtime/xmpp_post', XMPPPostHandler),
                                    ('/realtime/queue', QueueHandler),
                                    ('/realtime/start', StartSessionHandler),
                                    ('/realtime/stop', StopSessionHandler),
                                    ('/realtime/submit', SubmitHandler),
                                    ('/realtime/translate', TranslateHandler),
                                    ('/_ah/xmpp/message/chat/', XMPPHandler),
                                    ('/_ah/xmpp/presence/available/', PresenceHandler),
                                    ('/_ah/xmpp/presence/unavailable/', PresenceHandler),
                                    ('/_ah/xmpp/presence/subscribe/', PresenceHandler),
                                    ('/_ah/xmpp/subscription/subscribed/', PresenceHandler),
                                    ('/_ah/xmpp/subscription/unsubscribed/', PresenceHandler),
                                    ('/', MainHandler)],
                                     debug=True)


def main():
    util.run_wsgi_app(application)

if __name__ == "__main__":
    main()

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

"""
Worldwide Lexicon v2.0 API Handler
Brian S McConnell, Worldwide Lexicon Inc <bsmcconnell@gmail.com>

This program implements the Worldwide Lexicon API and documentation server
and is also used as a reference implementation for a proposed interoperability
API for translation services. It implements the following API handlers:
<ul>
<li>[GET]  /comments/{guid}/{language}</li>
<li>[POST] /comments/{guid}/{language}</li>
<li>[GET]  /doc/{handler}</li>
<li>[GET]  /lsp/status</li>
<li>[GET]  /lsp/status/{guid}</li>
<li>[POST] /lsp/status/{guid}</li>
<li>[GET]  /scores/translation</li>
<li>[POST] /scores/translation</li>
<li>[GET]  /scores/user</li>
<li>[POST] /submit</li>
<li>[GET]  /r/{guid}</li>
<li>[GET]  /r</li>
<li>[GET]  /t</li>
<li>[GET]  /u/{lang}/{url}</li>
<li>[GET]  /u</li>
</ul>
"""

error_other = 400
error_auth = 401
error_not_found = 404

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template
#
# import standard Python modules
#
import os.path
import demjson
import urllib
import string
import md5
import datetime
import time
import pydoc
import codecs
import types

class BaseHandler(webapp.RequestHandler):
    @property
    def language(self):
	if not hasattr(self, "_language"):
	    self._language = 'en'
            try:
                locales = string.split(self.request.headers['Accept-Language'],',')
            except:
                locales = 'en-us'
            langloc = string.split(locales[0],'-')
            if len(langloc[0]) > 1:
                self._language = langloc[0]
	return self._language
    def direction(self, language):
	rtl = ['ar', 'fa', 'he', 'ur']
	if language in rtl:
	    return 'RTL'
	else:
	    return 'LTR'

class Comments(db.Model):
    guid = db.StringProperty(default='')
    language = db.StringProperty(default='')
    text = db.TextProperty(default='')
    created = db.DateTimeProperty(auto_now_add = True)
    name = db.StringProperty(default='')
    userid = db.StringProperty(default='')
    @staticmethod
    def fetch(guid, language='', maxlen=100):
        cdb = db.Query(Comments)
        cdb.filter('guid = ', guid)
        if len(language) > 0: cdb.filter('language = ', language)
        cdb.order('-created')
        return cdb.fetch(maxlen)
    @staticmethod
    def save(guid, language, text, userid='', name=''):
        if len(guid) > 0 and len(language) > 0 and len(text) > 0:
            item = Comments()
            item.guid = guid
            item.language = language
            try:
                item.text = db.Text(text)
            except:
                try:
                    item.text = db.Text(text, encoding = 'utf-8')
                except:
                    item.text = text
            item.name = name
            item.userid = userid
            item.put()
            return True
        else:
            return False
        
class Languages(db.Model):
    code = db.StringProperty(default='')
    name = db.StringProperty(default='')
    @staticmethod
    def add(code, name):
        if len(code) > 0 and len(name) > 0:
            ldb = db.Query(Languages)
            ldb.filter('code = ', code)
            item = ldb.get()
            if item is None:
                item = Languages()
                item.code = code
            item.name = name
            item.enabled = True
            item.put()
            return True
        else:
            return False
    @staticmethod
    def getname(code):
        if len(code) < 4:
            txt = memcache.get('/languages/code/' + code)
            if txt is not None:
                return txt
            else:
                ldb = db.Query(Languages)
                ldb.filter('code = ', code)
                item = ldb.get()
                if item is not None:
                    memcache.set('/languages/code/' + code, item.name, 3600)
                    return item.name
        return ''
    @staticmethod
    def init():
        l=dict()
        l['en']=u'English'
        l['es']=u'Español'
        l['af']=u'Afrikaans'
        l['ar']=u'العربية'
        l['bg']=u'български език'
        l['bo']=u'བོད་ཡིག'
        l['de']=u'Deutsch'
        l['fr']=u'Français'
        l['he']=u'עברית '
        l['id']=u'Indonesian'
        l['it']=u'Italiano'
        l['ja']=u'日本語'
        l['ko']=u'한국어'
        l['ru']=u'русский'
        l['th']=u'ไทย '
        l['tl']=u'Tagalog'
        l['zh']=u'中文 '
        l['ca']=u'Català'
        l['cs']=u'česky'
        l['cy']=u'Cymraeg'
        l['da']=u'Dansk'
        l['el']=u'Ελληνικά'
        l['et']=u'Eesti keel'
        l['eu']=u'Euskara'
        l['fa']=u'فارسی '
        l['fi']=u'suomen kieli'
        l['ga']=u'Gaeilge'
        l['gl']=u'Galego'
        l['gu']=u'ગુજરાતી'
        l['hi']=u'हिन्दी '
        l['hr']=u'Hrvatski'
        l['ht']=u'Kreyòl ayisyen'
        l['hu']=u'Magyar'
        l['is']=u'Íslenska'
        l['iu']=u'ᐃᓄᒃᑎᑐᑦ'
        l['jv']=u'basa Jawa'
        l['ku']=u'كوردی'
        l['la']=u'lingua latina'
        l['lt']=u'lietuvių'
        l['lv']=u'latviešu'
        l['mn']=u'Монгол '
        l['ms']=u'بهاس ملايو‎'
        l['my']=u'Burmese'
        l['ne']=u'नेपाली '
        l['nl']=u'Nederlands'
        l['no']=u'Norsk Bokmal'
        l['nn']=u'Norsk'
        l['oc']=u'Occitan'
        l['pa']=u'ਪੰਜਾਬੀ '
        l['po']=u'polski'
        l['ps']=u'پښتو'
        l['pt']=u'Português'
        l['ro']=u'română'
        l['sk']=u'slovenčina'
        l['sr']=u'српски језик'
        l['sv']=u'svenska'
        l['sw']=u'Kiswahili'
        l['tr']=u'Türkçe'
        l['uk']=u'Українська'
        l['vi']=u'Tiếng Việt'
        l['yi']=u'ייִדיש'
        lnkeys = l.keys()
        for ln in lnkeys:
            Languages.add(ln, l[ln])
    @staticmethod
    def remove(code):
        if len(code) < 4:
            ldb = db.Query(Languages)
            ldb.filter('code = ', code)
            item = ldb.get()
            if item is not None:
                item.delete()
                return True
        return False
    @staticmethod
    def find():
        ldb = db.Query(Languages)
        ldb.order('code')
        results = ldb.fetch(limit=200)
        return results
    @staticmethod
    def select(selected=''):
        selected = string.lower(selected)
        if len(selected) < 1:
            text = memcache.get('/languages/select')
            if text is not None:
                return text
        else:
            text = memcache.get('/languages/select/' + selected)
            if text is not None:
                return text
        text = ''
        if len(selected) > 0:
            ldb = db.Query(Languages)
            ldb.filter('code = ', selected)
            item = ldb.get()
            if item is not None:
                text = text + '<option selected value="' + item.code + '">' + item.name + '</option>'
        ldb = db.Query(Languages)
        ldb.order('code')
        results = ldb.fetch(limit=200)
        for r in results:
            text = text + '<option value="' + r.code + '">' + r.name + '</option>'
        if len(selected) < 1:
            memcache.set('/languages/select', text, 300)
        else:
            memcache.set('/languages/select/' + selected, text, 300)
        return text

class Scores(db.Model):
    guid = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add = True)
    score = db.IntegerProperty(default=0)
    translator_userid = db.StringProperty(default='')
    translator_ip = db.StringProperty(default='')
    score_userid = db.StringProperty(default='')
    score_ip = db.StringProperty(default='')
    score_type = db.StringProperty(default='crowd')
    @staticmethod
    def fetch(guid='', translator_userid='', translator_ip='', score_userid='', score_ip='', score_type='crowd', maxlen=100):
        sdb = db.Query(Scores)
        sdb.order('-created')
        if len(guid) > 0: sdb.filter('guid = ', guid)
        if len(translator_userid) > 0: sdb.filter('translator_userid = ', translator_userid)
        if len(translator_ip) > 0: sdb.filter('translator_ip = ', translator_ip)
        if len(score_type) > 0: sdb.filter('score_type = ', score_type)
        return sdb.fetch(maxlen)
    @staticmethod
    def save(guid, score, score_userid = '', score_ip='', score_type=''):
        item = Translations.getbyguid(guid)
        if item is None:
            return False
        else:
            translator_userid = item.userid
            translator_ip = item.remote_addr
            sdb = db.Query(Scores)
            sdb.filter('guid = ', guid)
            sdb.filter('score_ip = ', score_ip)
            item = sdb.get()
            if item is None:
                item = Scores()
                item.guid = guid
                item.score_ip = score_ip
                item.score_userid = score_userid
            item.score = score
            item.translator_userid = translator_userid
            item.translator_ip = translator_ip
            item.score_type = score_type
            item.put()
            return True
    @staticmethod
    def stats(guid='', translator_userid='', translator_ip='', score_type='crowd', maxlen=100):
        sdb = db.Query(Scores)
        sdb.order('-created')
        if len(guid) > 0: sdb.filter('guid = ', guid)
        if len(translator_userid) > 0: sdb.filter('translator_userid = ', translator_userid)
        if len(translator_ip) > 0: sdb.filter('translator_ip = ', translator_ip)
        if len(score_type) > 0: sdb.filter('score_type = ', score_type)
        records = sdb.fetch(maxlen)
        rawscore = 0
        scores = 0
        for r in records:
            scores = scores + 1
            rawscore = rawscore + r.score
        if scores > 0:
            avgscore = float(float(rawscore)/scores)
        else:
            avgscore = None
        results = dict(
            scores = scores,
            rawscore = rawscore,
            avgscore = avgscore,
        )
        return results
    
class Settings(db.Model):
    parameter = db.StringProperty(default='')
    value = db.StringProperty(default='')
    updated = db.DateTimeProperty(auto_now=True)
    @staticmethod
    def fetch(maxlen=250):
        sdb = db.Query(Settings)
        sdb.order('parameter')
        return sdb.fetch(maxlen)
    @staticmethod
    def find(parameter):
        v = memcache.get('/settings/' + parameter)
        if v is None:
            sdb = db.Query(Settings)
            sdb.filter('parameter = ', parameter)
            item = sdb.get()
            if item is not None:
                v = item.value
                memcache.set('/settings/' + parameter, v)
                return v
        return v
    @staticmethod
    def save(parameter, value):
        sdb = db.Query(Settings)
        sdb.filter('parameter = ', parameter)
        item = sdb.get()
        if item is None:
            item = Settings()
            item.parameter = parameter
        item.value = value
        item.put()
        memcache.set('/settings/' + parameter, value)
        return True
    
class Translations(db.Model):
    guid = db.StringProperty(default='')
    srchash = db.StringProperty(default='')
    date = db.DateTimeProperty(auto_now_add=True)
    sl = db.StringProperty(default='')
    st = db.TextProperty(default='')
    tl = db.StringProperty(default='')
    tt = db.TextProperty(default='')
    url = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    username = db.StringProperty(default='')
    userid = db.StringProperty(default='')
    useremail = db.StringProperty(default='')
    userprofile = db.StringProperty(default='')
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    machine = db.BooleanProperty(default=False)
    human = db.BooleanProperty(default=True)
    professional = db.BooleanProperty(default=False)
    lsp = db.StringProperty(default='')
    avgscore = db.FloatProperty(default=5.0)
    scores = db.IntegerProperty(default=0)
    rawscore = db.IntegerProperty(default=0)
    scoredby = db.ListProperty(str)
    flagged = db.IntegerProperty(default=0)
    flaggedby = db.ListProperty(str)
    mirrored = db.BooleanProperty(default=False)
    @staticmethod
    def besteffort(sl, tl, st, orderby='-date', require_professional=False, maxlen=100):
        tdb = db.Query(Translations)
        tdb.filter('sl = ', sl)
        tdb.filter('tl = ', tl)
        m = md5.new()
        m.update(st)
        srchash = str(m.hexdigest())
        tdb.filter('srchash = ', srchash)
        if require_professional: tdb.filter('professional = ', True)
        tdb.order(orderby)
        return tdb.fetch(maxlen)
    @staticmethod
    def getbyguid(guid):
        tdb = db.Query(Translations)
        tdb.filter('guid = ', guid)
        item = tdb.get()
        return item
    @staticmethod
    def getbyurl(url, tl='', maxlen=100):
        string.replace(url, 'http://', '')
        string.replace(url, 'https://', '')
        tdb = db.Query(Translations)
        tdb.filter('url = ', url)
        if len(tl) > 0: tdb.filter('tl = ', tl)
        tdb.order('-date')
        return tdb.fetch(maxlen)
    @staticmethod
    def revisionhistory(st, tl='', maxlen=100):
        m = md5.new()
        m.update(st)
        srchash = str(m.hexdigest())
        tdb = db.Query(Translations)
        tdb.filter('srchash = ', srchash)
        if len(tl) > 1: tdb.filter('tl = ', tl)
        tdb.order('-date')
        return tdb.fetch(maxlen)
    @staticmethod
    def score(guid, score, score_type='crowd', score_userid='', score_ip=''):
        tdb = db.Query(Translations)
        tdb.filter('guid = ', guid)
        item = tdb.get()
        if item is not None:
            rawscore = item.rawscore + score
            scores = item.scores + 1
            avgscore = float(float(rawscore)/scores)
            item.rawscore = rawscore
            item.scores = scores
            item.avgscore = avgscore
            item.put()
            Scores.save(guid,score, score_userid=score_userid, score_ip=score_ip, score_type=score_type)
            return True
        else:
            return False
    @staticmethod
    def submit(sl, tl, st, tt, url='', username='', remote_addr='', human=True, professional=False, lsp=''):
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0 and len(tt) > 0:
            m = md5.new()
            m.update(str(datetime.datetime.now()))
            guid = str(m.hexdigest())
            m = md5.new()
            m.update(st)
            srchash = str(m.hexdigest())
            item = Translations()
            item.guid = guid
            item.srchash = srchash
            item.sl = sl
            item.tl = tl
            item.st = db.Text(st, encoding = 'utf-8')
            item.tt = db.Text(tt, encoding = 'utf-8')
            item.url = url
            item.username = username
            item.remote_addr = remote_addr
            item.human = human
            item.professional = professional
            item.lsp = lsp
            item.put()
            # Users.inc()
            return guid
        return

class Users(db.Model):
    id = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    name = db.StringProperty(default='')
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    email = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add = True)
    updated = db.DateTimeProperty(auto_now = True)
    avgscore = db.FloatProperty()
    scores = db.IntegerProperty(default=0)
    rawscore = db.IntegerProperty(default=0)
    lastscored = db.DateTimeProperty(auto_now_add=True)
    translations = db.IntegerProperty(default=0)
    words = db.IntegerProperty(default=0)
    languages = db.ListProperty(str)
    @staticmethod
    def add():
        pass
    @staticmethod
    def inc():
        pass
    @staticmethod
    def score(id = '', name='', remote_addr=''):
        pass
    @staticmethod
    def update(id = '', name='', city='', country='', latitude=None, longitude=None):
        pass

class HandleComments(webapp.RequestHandler):
    """
    This request handler implements the /comments/{guid} API, which enables client applications
    to request and submit comments about translations.
    """
    def get(self, guid='', language=''):
        if len(guid) < 1: guid = self.request.get('guid')
        if len(language) < 1: language = self.request.get('language')
        if len(guid) > 0:
            results = Comments.fetch(guid, language)
            records = list()
            if results is not None:
                for r in results:
                    comment = dict(
                        created = str(r.created),
                        guid = r.guid,
                        language = r.language,
                        text = r.text,
                    )
                    records.append(comment)
            json=demjson.encode(records)
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(json)
        else:
            doc_text = self.__doc__
            tdb = db.Query(Translations)
            tdb.order('date')
            item = tdb.get()
            guid = item.guid
            form = """
            <h3>[GET] Request Comments</h3>
            <table><form action=/comments/ method=get>
            <tr><td>[guid] Translation GUID</td><td><input type=text name=guid value=""" + guid + """></td></tr>
            <tr><td>[language] Comment Language Code</td><td><input type=text name=language></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            <h3>[POST] Submit Comment</h3>
            <table><form action=/comments/ method=post>
            <tr><td>[guid] Translation GUID</td><td><input type=text name=guid value=""" + guid + """></td></tr>
            <tr><td>[language] Comment Language Code</td><td><input type=text name=language></td></tr>
            <tr><td>[text] Comment Text (UTF8)</td><td><input type=text name=text></td></tr>
            <tr><td>[username] Username</td><td><input type=text name=username></td></tr>
            <tr><td>[name] Name</td><td><input type=text name=name></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/comments',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))
    def post(self, guid='', language=''):
        if len(guid) < 1: guid = self.request.get('guid')
        if len(language) < 1: language = self.request.get('language')
        if len(guid) > 0:
            text = self.request.get('text')
            userid = self.request.get('username')
            name = self.request.get('name')
            if Comments.save(guid, language, text, userid=userid, name=name):
                self.response.out.write('ok')
            else:
                self.error(error_not_found)
                self.response.out.write('comment not saved')
        else:
            self.error(error_other)
            self.response.out.write('Incomplete submission')
            
class HandleInstall(webapp.RequestHandler):
    """
    <h3>/heartbeat</h3>
    
    This is a system heartbeat task that is run by a cron job once per minute,
    and also serves as an auto-installer that performs initial system configuration
    if your code is running for the first time.
    """
    def get(self):
        if Settings.find('installed') == 'y':
            self.response.out.write('already installed')
        else:
            # generate a trusted API key for other LSPs and mirrors to use when
            # submitting to your translation memory
            m = md5.new()
            m.update(str(datetime.datetime.now()))
            md5hash = str(m.hexdigest())
            Settings.save('installed', 'y')
            Settings.save('secret_key', md5hash)
            # generate default list of languages
            Languages.init()
            # create dummy records
            guid = Translations.submit('en','es','hello','hola', url='www.foo.com', remote_addr='0.0.0.0')
            Translations.score(guid, 5)
            Comments.save(guid,'en','Hello World')
            self.response.out.write('ok')

class HandleLSPStatus(webapp.RequestHandler):
    def get(self, guid=''):
        #if guid is blank, return LSP operating status instead of job status
        pass
    def post(self, guid=''):
        pass
    
class HandleMirror(webapp.RequestHandler):
    def get(self):
        pass
    def post(self):
        pass

class HandleScoresTranslation(webapp.RequestHandler):
    """
    <h3>/scores</h3>
    
    <p>This request handler implements the REST API to request and submit
    scores for a translation.</p>
    """
    def get(self, guid=''):
        if len(guid) < 1: guid = self.request.get('guid')
        if len(guid) > 0:
            records = list()
            stats = Scores.stats(guid)
            record = dict(
                guid = '_average',
                score = stats['avgscore'],
                scores = stats['scores'],
            )
            records.append(record)
            results = Scores.fetch(guid=guid)
            for r in results:
                record = dict(
                    guid = r.guid,
                    created = str(r.created),
                    score = r.score,
                    score_type = r.score_type,
                    score_ip = r.score_ip,
                    score_userid = r.score_userid,
                )
                records.append(record)
            json = demjson.encode(records)
            self.response.out.write(json)
        else:
            doc_text = self.__doc__
            tdb = db.Query(Translations)
            tdb.order('date')
            item = tdb.get()
            guid = item.guid
            form = """
            <h3>[GET] Request Scores</h3>
            <table><form action=/scores/ method=get>
            <tr><td>[guid] Translation GUID</td><td><input type=text name=guid value=""" + guid + """></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            <h3>[POST] Submit Score For Translation</h3>
            <table><form action=/scores/ method=post>
            <tr><td>[guid] Translation GUID</td><td><input type=text name=guid value=""" + guid + """></td></tr>
            <tr><td>[score] Score (0..5)</td><td><input type=text name=score></td></tr>
            <tr><td>[username] Username</td><td><input type=text name=username></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/scores',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))
    def post(self, guid=''):
        if len(guid) < 1: guid = self.request.get('guid')
        valid_score = True
        try:
            score = int(self.request.get('score'))
            if score > 0 and score < 6:
                valid_score=True
            else:
                valid_score=False
        except:
            valid_score = False
        if valid_score:
            username = self.request.get('username')
            userip = self.request.remote_addr
            score_type = 'crowd'
            if len(guid) > 0:
                if Scores.save(guid, score, score_userid=username, score_ip=userip, score_type=score_type):
                    self.response.out.write('ok')
                else:
                    self.error(error_not_found)
                    self.response.out.write('Translation not located')
            else:
                self.error(error_not_found)
                self.response.out.write('Translation not located')
        else:
            self.error(error_other)
            self.response.out.write('score must be between 0 and 5')

class HandleScoresUser(webapp.RequestHandler):
    """
    <h3>/scores/user</h3>
    
    <p>This request handler implements the /scores/user API, which can be used
    to request summary and detailed score histories for individual users or
    IP addresses. It is called as follows:</p>
    
    <ul><li>/scores/user/{username_or_IP}</li>
    <li>/scores/user?username={username_or_IP}</li>
    </ul>
    
    <p>It returns a JSON recordset containing scores submitted for that user or
    IP address. The record labeled _average contains the average and raw score
    for the user, and is followed by individual scores.</p>
    """
    def get(self, username=''):
        if len(username) < 1:
            username = self.request.get('username')
        if len(username) > 0:
            if string.count(username, '.') > 1:
                results = Scores.fetch(translator_ip = username)
            else:
                results = Scores.fetch(translator_userid = username)
            records=list()
            for r in results:
                record = dict(
                    guid = r.guid,
                    created = str(r.created),
                    score = r.score,
                    score_ip = r.score_ip,
                    score_userid = r.score_userid,
                    score_type = r.score_type,
                    translator_ip = r.translator_ip,
                    translator_userid = r.translator_userid,
                )
                records.append(record)
            json = demjson.encode(records)
            self.response.out.write(json)
        else:
            doc_text = self.__doc__
            tdb = db.Query(Scores)
            tdb.order('created')
            item = tdb.get()
            guid = '0.0.0.0'
            form = """
            <h3>[GET] Request Scores For Translator</h3>
            <table><form action=/scores/user method=get>
            <tr><td>[username] Username or IP Address</td><td><input type=text name=username value=""" + guid + """></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/scores/user',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class HandleSubmit(webapp.RequestHandler):
    def post(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('st')
        stencoding = self.request.get('stencoding')
        tt = self.request.get('tt')
        ttencoding = self.request.get('ttencoding')
        url = self.request.get('url')
        lsp = self.request.get('lsp')
        username = self.request.get('username')
        remote_addr = self.request.remote_addr
        if len(lsp) > 0:
            professional = True
        else:
            professional = False
        Translations.submit(sl, tl, st, tt, url=url, username=username, remote_addr=remote_addr, lsp=lsp, professional=professional)
        self.response.out.write('ok')
        
class HandleR(webapp.RequestHandler):
    def get(self, srchash='', tl=''):
        if len(srchash) < 1:
            st = self.request.get('st')
            m = md5.new()
            m.update(st)
            srchash=str(m.hexdigest())
        if len(tl) < 1: tl = self.request.get('tl')
        results = Translations.revisionhistory(srchash, tl=tl)
        records = list()
        for r in results:
            record = dict(
                guid = r.guid,
                date = str(r.date),
                sl = r.sl,
                tl = r.tl,
                st = r.st,
                tt = r.tt,
                url = r.url,
                human = r.human,
                professional = r.professional,
                remote_addr = r.remote_addr,
                username = r.username,
            )
            records.append(record)
        json = demjson.encode(records)
        self.response.headers['Content-Type']='text/javascript'
        self.response.out.write(json)

class HandleT(webapp.RequestHandler):
    """
    <h3>/t</h3>
    
    <p>This request handler implements the /t API which enables users to
    request the best available machine, crowd or professional translation for a
    text, as well as to initiate a professional translation request. It is called
    as follows:</p>
    
    <ul><li>/t/{source_lang}/{target_lang}/{encoded_text}?optional_params</li>
    <li>/t/{source_lang/{target_lang}?optional_params</li>
    <li>/t?params</li>
    </ul>
    
    <p>It expects the following parameters:</p>
    
    <ul>
    <li>sl : source language</li>
    <li>tl : target language</li>
    <li>st : source text</li>
    <li>stencoding : source text encoding (if omitted, assumes utf-8)</li>
    <li>url : parent URL text came from (optional)</li>
    <li>lsp : optional LSP name (for pro translation)</li>
    <li>lspusername : LSP username</li>
    <li>lsppw : LSP pw/key</li>
    <li>allow_machine : allow machine translation</li>
    </ul>
    
    """
    def get(self, sl='', tl='', st=''):
        self.requesthandler(sl, tl, st)
    def post(self, sl='', tl='', st=''):
        self.requesthandler(sl, tl, st)
    def requesthandler(self, sl='', tl='', st=''):
        if len(sl) < 1: sl = self.request.get('sl')
        if len(tl) < 1: tl = self.request.get('tl')
        if len(st) < 1:
            st = self.request.get('st')
        else:
            st = urllib.unquote_plus(st)
        if self.request.get('require_professional') == 'y':
            require_professional = True
        else:
            require_professional = False
        allow_machine = self.request.get('allow_machine')
        if allow_machine == 'n':
            allow_machine = False
        else:
            allow_machine = True
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            results = Translations.besteffort(sl, tl, st, require_professional=require_professional)
            records = list()
            if results is None:
                if allow_machine:
                    pass
                    # get result from MT engine
            else:
                for r in results:
                    record = dict(
                        guid = r.guid,
                        date = str(r.date),
                        sl = r.sl,
                        tl = r.tl,
                        st = r.st,
                        tt = r.tt,
                        url = r.url,
                        human = r.human,
                        professional = r.professional,
                        remote_addr = r.remote_addr,
                        username = r.username,
                        lsp = r.lsp,
                    )
                    records.append(record)
            json = demjson.encode(records)
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(json)
        else:
            doc_text = self.__doc__
            tdb = db.Query(Scores)
            tdb.order('created')
            item = tdb.get()
            guid = '0.0.0.0'
            form = """
            <h3>[GET] Request Best Available Translation For A Text</h3>
            <table><form action=/t method=get>
            <tr><td>[sl] Source Language</td><td><input type=text name=sl></td></tr>
            <tr><td>[tl] Target Language</td><td><input type=text name=tl></td></tr>
            <tr><td>[st] Source Text</td><td><input type=text name=st></td></tr>
            <tr><td>[stencoding] Source Text Encoding (UTF8 default)</td><td><input type=text name=stencoding></td></tr>
            <tr><td>[url] Parent URL</td><td><input type=text name=url></td></tr>
            <tr><td>[lsp] LSP</td><td><input type=text name=lsp></td></tr>
            <tr><td>[lspusername] LSP Username</td><td><input type=text name=lspusername></td></tr>
            <tr><td>[lsppw] LSP password/key</td><td><input type=text name=lsppw></td></tr>
            <tr><td>[allow_machine]</td><td><input type=text name=allow_machine value=y></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/t',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))
    
class HandleU(webapp.RequestHandler):
    """
    <h3>/u</h3>
    
    <p>This request handler enables users to retrieve human edited translations
    associated with a specific URL and optional target language. This is useful
    when you need to retrieve a batch of translations submitted for a given URL,
    as is common in crowd translation scenarios. The service can be called as
    follows:</p>
    
    <ul><li>/u/{target_lang_code}/{url}</li>
    <li>/u?tl={target_lang_code}&url={url}</li>
    </ul>
    """
    def get(self, tl='', url=''):
        if len(tl) < 1: tl = self.request.get('tl')
        if len(url) < 1: url = self.request.get('url')
        if len(url) > 0:
            results = Translations.getbyurl(url, tl=tl)
            records = list()
            for r in results:
                record = dict(
                    guid = r.guid,
                    date = str(r.date),
                    sl = r.sl,
                    tl = r.tl,
                    st = r.st,
                    tt = r.tt,
                    url = r.url,
                    human = r.human,
                    professional = r.professional,
                    remote_addr = r.remote_addr,
                    username = r.username,
                )
                records.append(record)
            json = demjson.encode(records)
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(json)
        else:
            doc_text = self.__doc__
            tdb = db.Query(Translations)
            tdb.order('date')
            item = tdb.get()
            guid = item.guid
            form = """
            <h3>[GET] Request Scores</h3>
            <table><form action=/u method=get>
            <tr><td>[tl] Target Language Code</td><td><input type=text name=tl></td></tr>
            <tr><td>[url] Parent URL</td><td><input type=text name=url></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/u',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')
        
def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          (r'/comments/(.*)', HandleComments),
                                          ('/comments', HandleComments),
                                          ('/install', HandleInstall),
                                          (r'/scores/user/(.*)', HandleScoresUser),
                                          ('/scores/user', HandleScoresUser),
                                          (r'/scores/(.*)', HandleScoresTranslation),
                                          ('/scores', HandleScoresTranslation),
                                          (r'/t/(.*)/(.*)/(.*)', HandleT),
                                          (r'/t/(.*)/(.*)', HandleT),
                                          ('t/', HandleT),
                                          (r'/u/(.*)/(.*)', HandleU),
                                          ('/u', HandleU)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

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
from google.appengine.api import users
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

from BeautifulSoup import BeautifulSoup

def clean(text, encoding=''):
    soup = BeautifulSoup(text)
    return soup.renderContents()
    
def is_admin():
    user = users.get_current_user()
    if users.is_current_user_admin():
        return True
    else:
        return False

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
        
class MTProxy():
    """
    Makes query to and parses response from Google Translate machine translation
    engine (uses the demjson module to parse JSON response)
    """
    @staticmethod
    def getTranslation(mtengine='google', sl='en', tl='es',st = '',userip=''):
        tt = memcache.get('/mt/' + mtengine + '/' + sl + '/' + tl + '/' + st)
        if tt is not None:
            return tt
        if mtengine == 'google':
            url="http://ajax.googleapis.com/ajax/services/language/translate"
            form_fields = {
                "langpair": sl + '|' + tl,
                "v" : "1.0",
                "q": st,
                "ie" : "UTF8",
                "userip" : userip
            }
            form_data = urllib.urlencode(form_fields)
            #try:
            result = urlfetch.fetch(url=url, payload=form_data, method=urlfetch.POST, headers={'Content-Type': 'application/x-www-form-urlencoded'})
            results = demjson.decode(result.content, encoding='utf-8')
            tt = clean(results['responseData']['translatedText'])
            if len(tt) > 0:
                memcache.set('/mt/' + mtengine + '/' + sl + '/' + tl + '/' + st, tt, 7200)
        return tt
        
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

class LSPQueue(db.Model):
    guid = db.StringProperty(default='')
    jobtype = db.StringProperty(default='')
    status = db.StringProperty(default='queued')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    st = db.TextProperty(default='')
    tt = db.TextProperty(default='')
    score = db.IntegerProperty(default=0)
    url = db.StringProperty(default='')
    callback_url = db.StringProperty(default='')
    apikey = db.StringProperty(default='')
    username = db.StringProperty(default='')
    translator = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    deadline = db.DateTimeProperty()
    message = db.TextProperty(default='')
    completed = db.DateTimeProperty()
    last_callback = db.DateTimeProperty(auto_now_add=True)
    billed = db.BooleanProperty(default=False)
    @staticmethod
    def request_score(guid,sl,tl,st,tt,url='',username='',message='',deadline=24, callback_url='',
                      apikey=''):
        jdb = db.Query(LSPQueue)
        jdb.filter('guid = ', guid)
        item = jdb.get()
        if item is None:
            item = LSPQueue()
            item.guid = guid
            item.jobtype = 'score'
            item.status = 'queued'
            item.sl = sl
            item.tl = tl
            item.st = st
            item.tt = tt
            item.url = url
            item.callback_url = callback_url
            item.message = message
            item.apikey = apikey
            td = datetime.timedelta(hours=deadline)
            item.deadline = datetime.datetime.now() + td
            item.put()
            return True
        else:
            return False
    @staticmethod
    def request_translation(guid,sl,tl,st,url='',username='',message='', deadline=24, callback_url=''):
        jdb = db.Query(LSPQueue)
        jdb.filter('guid = ', guid)
        item = jdb.get()
        if item is None:
            item = LSPQueue()
            item.guid = guid
            item.jobtype = 'translation'
            item.status = 'queued'
            item.sl = sl
            item.tl = tl
            item.st = st
            item.url = url
            item.callback_url = callback_url
            item.apikey = apikey
            item.message = message
            td = datetime.timedelta(hours=deadline)
            item.deadline = datetime.datetime.now() + td
            item.put()
            return True
        else:
            return False
    @staticmethod
    def update_record(guid, lock=False, unlock=False, complete=False, tt='', score='', translator=''):
        jdb = db.Query(LSPQueue)
        jdb.filter('guid = ', guid)
        item = jdb.get()
        if item is not None:
            if lock:
                item.status = 'locked'
            elif unlock:
                item.status = 'queued'
            elif complete:
                item.status = 'complete'
            else:
                pass
            if len(tt) > 0: item.tt = tt
            if len(score) > 0: item.score = int(score)
            if len(translator) > 0: item.translator = translator
            item.put()
            return True
        else:
            return False
    @staticmethod
    def send_completed_records(maxlen=10):
        jdb = db.Query(LSPQueue)
        jdb.filter('status = ', 'complete')
        jdb.order('last_callback')
        results = jdb.fetch(maxlen)
        for r in results:
            if r.jobtype == 'translation':
                form_fields = {
                    "guid" : r.guid,
                    "api" : r.apikey,
                    "sl" : r.sl,
                    "tl" : r.tl,
                    "st" : r.st,
                    "tt" : r.tt,
                    "url" : r.url,
                    "username" : r.translator
                }
                form_data = urllib.urlencode(form_fields)
                result = urlfetch.fetch(url=r.callback_url, payload=form_data, method=urlfetch.POST,
                                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
                if result.status_code == 200:
                    r.status='sent'
                    r.put()
                else:
                    r.last_callback = datetime.datetime.now()
                    r.put()
            elif r.jobtype == 'score':
                form_fields = {
                    "guid" : r.guid,
                    "api" : r.apikey,
                    "sl" : r.sl,
                    "tl" : r.tl,
                    "st" : r.st,
                    "tt" : r.tt,
                    "score" : r.score,
                    "url" : r.url,
                    "username" : r.translator
                }
                form_data = urllib.urlencode(form_fields)
                result = urlfetch.fetch(url=r.callback_url, payload=form_data, method=urlfetch.POST,
                                        headers={'Content-Type': 'application/x-www-form-urlencoded'})
                if result.status_code == 200:
                    r.status='sent'
                    r.put()            # send form to callback url
            else:
                pass
        return True
            

class LSPs(db.Model):
    id = db.StringProperty(default='')
    name = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    apikey = db.StringProperty(default='')
    apiurl = db.StringProperty(default='')
    @staticmethod
    def auth(key):
        ldb = db.Query(LSPs)
        ldb.filter('apikey = ', key)
        item = ldb.get()
        if item is not None:
            return item.id
        else:
            return ''
    @staticmethod
    def add(id, name, apiurl=''):
        ldb = db.Query(LSPs)
        ldb.filter('id = ', id)
        item = ldb.get()
        if item is None:
            m = md5.new()
            m.update(str(datetime.datetime.now()))
            key = str(m.hexdigest())
            item = LSPs()
            item.id = id
            item.name = name
            item.apikey = key
            item.apiurl = apiurl
            item.put()
            return True
        return False
    @staticmethod
    def find():
        ldb=db.Query(LSPs)
        ldb.order('name')
        return ldb.fetch(200)
    @staticmethod
    def geturl(id):
        ldb=db.Query(LSPs)
        ldb.filter('id = ', id)
        item = ldb.get()
        if item is not None:
            return item.apirul
        else:
            return ''
    @staticmethod
    def remove(id):
        ldb = db.Query(LSPs)
        ldb.filter('id = ', id)
        item = ldb.get()
        if item is not None:
            item.delete()
            return True
        return False

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
    def fetch(guid='', translator_userid='', translator_ip='', score_userid='', score_ip='', score_type= 'crowd', maxlen=100):
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
    def revisionhistory(srchash, tl='', maxlen=100):
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
            st = clean(st)
            tt = clean(tt)
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

class HandleAdmin(webapp.RequestHandler):
    """
    <h3>Main Menu</h3>
    <ul>
    <li><a href=/admin/languages>Manage Languages</a></li>
    <li><a href=/admin/lsps>Manage LSPs</a></li>
    </ul>
    """
    def get(self, path=''):
        doc_text = self.__doc__
        if path == 'login':
            user = users.get_current_user()
            if is_admin():
                self.response.out.write(header())
                self.response.out.write('<div class="col1">')
                greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                                (user.nickname(), users.create_logout_url("/admin")))
                self.response.out.write(greeting)
                self.response.out.write('</div>')
                self.response.out.write(footer())
                return
            elif user:
                greeting = ("Sorry, %s, you must be an administrator to access this module. (<a href=\"%s\">sign out</a>)" %
                                (user.nickname(), users.create_logout_url("/admin")))
            else:
                greeting = ("<a href=\"%s\">Sign in or register</a>." %
                            users.create_login_url("/admin"))
            left_text=greeting
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = 'Admin Console',
                left_text = left_text,
                right_text = '',
            )
            self.response.out.write(template.render(path, args))
        else:
            if is_admin():
                left_text=''
                if path == 'lsps':
                    lt = '<h3>Add New LSP</h3>'
                    lt = lt + '<form action=/admin method=post>'
                    lt = lt + '<input type=hidden name=action value=add_lsp>'
                    lt = lt + '<table><tr><td>LSP ID (e.g. foocorp)</td><td><input type=text name=id>'
                    lt = lt + '<tr><td>Proper Name</td><td><input type=text name=name></td>'
                    lt = lt + '<tr><td>API URL</td><td><input type=text name=apiurl></td>'
                    lt = lt + '<tr><td colspan=2><input type=submit value="Add LSP"></td></tr></table></form>'
                    lt = lt + '<H3>LSP Directory</H3>'
                    lsps = LSPs.find()
                    lt = lt + '<table><tr><td>Name</td><td>Callback URL</td><td>API Key</td><td></td></tr>'
                    for l in lsps:
                        lt = lt + '<tr><td>' + l.name + '</td><td>' + l.apiurl + '</td><td>' + l.apikey + '</td>'
                        lt = lt + '<td><form action=/admin method=post><input type=hidden name=action value=delete_lsp><input type=hidden name=id value="' + l.id + '"><input type=submit value=Delete></form></td></tr>'
                    lt = lt + '</table>'
                    left_text = lt
                elif path == 'languages':
                    langlist = Languages.find()
                    lt = '<h3>Add Language</h3>'
                    lt = lt + '<table><form action=/admin method=post>'
                    lt = lt + '<input type=hidden name=action value=add_language>'
                    lt = lt + '<tr><td>ISO Code</td><td><input type=text name=code></td></tr>'
                    lt = lt + '<tr><td>Name</td><td><input type=text name=name></td></tr>'
                    lt = lt + '<tr><td colspan=2><input type=submit value=Add></form></td></tr></table>'
                    lt = lt + '<h3>Manage Languages</h3>'
                    lt = lt + '<table><tr><td>Code</td><td>Language</td><td></td></tr>'
                    for l in langlist:
                        lt = lt + '<tr><td>' + l.code + '</td><td>' + l.name + '</td><td>'
                        lt = lt + '<form action=/admin method=post><input type=hidden name=action value=delete_language><input type=hidden name=code value="' + l.code + '"><input type=submit value=Delete></form></td></tr>'
                    lt = lt + '</table>'
                    left_text = lt
                path = os.path.join(os.path.dirname(__file__), "doc.html")
                args = dict(
                    title = 'Admin Console',
                    left_text = left_text,
                    right_text = doc_text,
                )
                self.response.out.write(template.render(path, args))
            else:
                self.redirect('/admin/login')
    def post(self, path=''):
        if is_admin():
            action = self.request.get('action')
            if action == 'add_lsp':
                id = self.request.get('id')
                name = self.request.get('name')
                apiurl = self.request.get('apiurl')
                LSPs.add(id, name, apiurl=apiurl)
                self.redirect('/admin/lsps')
            elif action == 'delete_lsp':
                id = self.request.get('id')
                LSPs.remove(id)
                self.redirect('/admin/lsps')
            elif action == 'add_language':
                code = self.request.get('code')
                name = self.request.get('name')
                Languages.add(code,name)
                self.redirect('/admin/languages')
            elif action == 'delete_language':
                code = self.request.get('code')
                Languages.remove(code)
                self.redirect('/admin/languages')
            else:
                self.redirect('/admin')
        else:
            self.redirect('/admin')

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
        if Settings.find('installed') == 'yn':
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
            LSPs.add('dummy', 'Dummy LSP Account', '/lsp')
            # create dummy records
            guid = Translations.submit('en','es','hello','hola', url='www.foo.com', remote_addr='0.0.0.0')
            Translations.score(guid, 5)
            Comments.save(guid,'en','Hello World')
            self.response.out.write('ok')
            
class HandleLSPQuote(webapp.RequestHandler):
    """
    <h3>/lsp/quote</h3>
    
    <p>This web service standardizes the process of requesting a quote from an LSP.
    The service resides at www.baseurl.com/lsp/quote and expects the following
    parameters:</p>
    <ul>
    <li>lsp : LSP id/nickname (not needed if this API is called directly at the LSP</li>
    <li>username : username or account ID</li>
    <li>sl : source language code</li>
    <li>tl : target language code</li>
    <li>words : number of words</li>
    <li>sla : service level agreement code</li>
    <li>currency : currency</li>
    </ul>
    
    <p>The service or LSP will respond with a JSON dictionary with the following fields:</p>
    <ul>
    <li>price : price of job in requested currency (float)</li>
    <li>eta : approximate delivery time in dd:hh:mm (string)</li>
    <li>message : optional remarks or message</li>
    </ul>
    """
    def get(self, lsp=''):
        self.requesthandler(lsp)
    def post(self, lsp=''):
        self.requesthandler(lsp)
    def requesthandler(self, lsp=''):
        if len(lsp) < 1: lsp=self.request.get('lsp')
        sla = self.request.get('sla')
        username = self.request.get('username')
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        words = self.request.get('words')
        jobtype = self.request.get('jobtype')
        current = self.request.get('currency')
        if len(lsp) > 0:
            apiurl = LSPs.geturl(lsp)
            if len(url) > 0:
                form_fields = {
                    "sla" : sla,
                    "username" : username,
                    "sl" : sl,
                    "tl" : tl,
                    "words" : words,
                    "jobtype" : jobtype,
                    "currency" : currency
                }
                form_data = urllib.urlencode(form_fields)
                url = apiurl + '/lsp/quote'
                result = urlfetch.fetch(url=url, payload=form_data, method=urlfetch.POST, headers={'Content-Type': 'application/x-www-form-urlencoded'})
                if result.status_code == 200:
                    quote = result.content
                    self.response.headers['Content-Type']='text/javascript'
                    self.response.out.write(quote)
                else:
                    self.error(error_other)
                    self.response.out.write('Request to LSP Failed')
            else:
                self.error(error_not_found)
                self.response.out.write('Unknown LSP')
        else:
            doc_text = self.__doc__
            form = """
            <h3>[GET/POST] Request Quote</h3>
            <table><form action=/lsp/quote method=get>
            <tr><td>[lsp] LSP ID or Nickname</td><td><input type=text name=lsp></td></tr>
            <tr><td>[username] Username</td><td><input type=text name=username></td></tr>
            <tr><td>[sla] SLA Code</td><td><input type=text name=sla></td></tr>
            <tr><td>[sl] Source Language</td><td><input type=text name=sl></td></tr>
            <tr><td>[tl] Target Language</td><td><input type=text name=tl></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/lsp/quote',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))

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
    """
    <h3>/submit</h3>
    
    <p>This request handler accepts human edited translations from the user community
    and from professional translation agencies. The /submit API is called using the POST
    method. If the submission is from a professional translation agency or a trusted user,
    it should be accompanied with an API key assigned to the LSP.</p>
    """
    def post(self):
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = clean(self.request.get('st'))
        tt = clean(self.request.get('tt'))
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
    def get(self):
        doc_text = self.__doc__
        form = """
        <h3>[POST] Submit Translation For A Text</h3>
        <table><form action=/submit method=post>
        <tr><td>[sl] Source Language</td><td><input type=text name=sl></td></tr>
        <tr><td>[tl] Target Language</td><td><input type=text name=tl></td></tr>
        <tr><td>[st] Source Text</td><td><input type=text name=st></td></tr>
        <tr><td>[tt] Translated Text</td><td><input type=text name=tt></td></tr>
        <tr><td>[url] Parent URL</td><td><input type=text name=url></td></tr>
        <tr><td>[username] Username</td><td><input type=text name=username></td></tr>
        <tr><td>[api] API Key (For LSP Submissions)</td><td><input type=text name=api></td></tr>
        <tr><td>[lsp] LSP Name</td><td><input type=text name=lsp></td></tr>
        <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
        """
        path = os.path.join(os.path.dirname(__file__), "doc.html")
        args = dict(
            title = '/t',
            left_text = form,
            right_text = doc_text,
        )
        self.response.out.write(template.render(path, args))

class HandleR(webapp.RequestHandler):
    """
    <h3>/r : Revision History</h3>
    <p>This API enables you to request a translation revision history for a source text,
    sorted from newest to oldest. The API is called at www.baseurl.com/r with the following
    parameters:</p>
    <ul>
    <li>st : source text (UTF8 encoding)</li>
    <li>tl : target language code (optional)</li>
    </ul>
    
    <p>The service responds with a JSON object containing a list of matching records.</p>
    """
    def get(self, srchash='', tl=''):
        if len(srchash) < 1:
            st = self.request.get('st')
            if len(st) > 0:
                m = md5.new()
                m.update(st)
                srchash=str(m.hexdigest())
            else:
                srchash=''
        if len(tl) < 1: tl = self.request.get('tl')
        if len(srchash) > 0:
            results = Translations.revisionhistory(srchash, tl=tl)
            records = list()
            for r in results:
                record = dict(
                    guid = r.guid,
                    srchash = r.srchash,
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
            json = demjson.encode(records, encoding = 'utf-8')
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(json)
        else:
            doc_text = self.__doc__
            tdb = db.Query(Translations)
            tdb.order('date')
            item = tdb.get()
            tl = item.tl
            st = item.st
            form = """
            <h3>[GET] Request Revision History For A Text</h3>
            <table><form action=/r method=get>
            <tr><td>[tl] Target Language</td><td><input type=text name=tl value=""" + tl + """></td></tr>
            <tr><td>[st] Source Text</td><td><input type=text name=st value=""" + st + """></td></tr>
            <tr><td colspan=2><input type=submit value=Submit></td></tr></form></table>
            """
            path = os.path.join(os.path.dirname(__file__), "doc.html")
            args = dict(
                title = '/r',
                left_text = form,
                right_text = doc_text,
            )
            self.response.out.write(template.render(path, args))    

class HandleT(webapp.RequestHandler):
    """
    <h3>/t</h3>
    
    <p>This request handler implements the /t API which enables users to
    request the best available machine, crowd or professional translation for a
    text, as well as to initiate a professional translation request. It is called
    as follows:</p>
    
    <ul><li>/t/{source_lang}/{target_lang}/{encoded_text}?optional_params</li>
    <li>/t/{source_lang}/{target_lang}?optional_params</li>
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
        stencoding = self.request.get('stencoding')
        if len(stencoding) > 0 and len(st) > 0:
            try:
                st = clean(st, stencoding)
            except:
                st = clean(st)
        else:
            st = clean(st)
        lsp = self.request.get('lsp')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            if len(lsp) > 0:
                apiurl = LSPs.geturl(lsp)
                if len(apiurl) > 0:
                    result = memcache.get('/lsp/' + sl + '/' + tl + '/' + st)
                    if result is not None:
                        return result
                    form_fields = {
                        "sl" : sl,
                        "tl" : tl,
                        "st" : st,
                        "url": url,
                        "lspusername" : lspusername,
                        "lsppw" : lsppw,
                        "output" : "json"
                    }
                    form_data = urllib.urlencode(form_fields)
                    #try:
                    result = urlfetch.fetch(url=url, payload=form_data, method=urlfetch.POST, headers={'Content-Type': 'application/x-www-form-urlencoded'})
                    if result.status_code == 200:
                        memcache.set('/lsp/' + sl + '/' + tl + '/' + st, result.content, 3600)
                        return result.content
            results = Translations.besteffort(sl, tl, st, require_professional=require_professional)
            records = list()
            if results is None or len(results) < 1:
                if allow_machine:
                    tt = MTProxy.getTranslation(sl=sl, tl=tl, st=st, userip=self.request.remote_addr)
                    if len(tt) > 0:
                        record = dict(
                            sl = sl,
                            tl = tl,
                            st = db.Text(st, encoding='utf-8'),
                            tt = db.Text(tt, encoding='utf-8'),
                            mtengine = 'google',
                            human = False,
                            professional = False,
                        )
                        records.append(record)
                    json = demjson.encode(records, encoding='utf-8')
                    self.response.headers['Content-Type']='text/javascript'
                    self.response.out.write(json)
                    return
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
            json = demjson.encode(records, encoding = 'utf-8')
            self.response.headers['Content-Type']='text/javascript'
            self.response.out.write(json)
            return
        else:
            doc_text = self.__doc__
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
            json = demjson.encode(records, encoding = 'utf-8')
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
    """
    <h3>Worldwide Lexicon API v2</h3>
    <ul>
    <li><a href=/comments>/comments : Get/Submit Comments</a></li>
    <li><a href=/lsp/quote>/lsp/quote : Request Quote From Network LSP</a></li>
    <li><a href=/r>/r : Revision History</a></li>
    <li><a href=/scores>/scores : Get/Submit Scores</a></li>
    <li><a href=/scores/user> /scores/user : Get User Score History</a></li>
    <li><a href=/submit>/submit : Submit Translation</a></li>
    <li><a href=/t>/t : Request Translations for text</a></li>
    <li><a href=/u>/u : Request Translations for URL</a></li>
    </ul>
    """
    def get(self):
        doc_text = self.__doc__
        form = """
        <p>Welcome to the Worldwide Lexicon translation server. This service provides a simple, scalable
        web service that enables you to request, submit and comment on translations from a variety of
        machine, crowd and professional translation services.</p>
        <p>We have updated and simplified the web API to make it even easier to develop best effort
        hybrid translation solutions. This API is currently in testing at the address
        <a href=http://worldwidelexicon2.appspot.com>worldwidelexicon2.appspot.com</a> and will be
        migrated to the production server in April 2011. The new API is backward compatible with the
        version 1 API so existing tools, plugins and other modules will continue to function normally.
        </p>
        <h4>Major Changes</h4>
        <p>We have focused on several key areas in this system upgrade, including:</p>
        <ul>
        <li>Easy installation : installing and configuring an instance of a WWL server is now as simple
        as extracting a ZIP file and using the Google App Engine launcher to deploy the code to your
        App Engine account</li>
        <li>Simplified API : we have consolidated API calls and made the API as fully REST oriented.
        You can now build a robust and sophisticated translation app while using fewer than a dozen web
        API calls.</li>
        <li>JSON by default : we use JSON as our default output format. We made this switch primarily
        because JSON is natively supported in Javascript, the language of choice for building interactive
        web applications, and is also widely supported in server side languages including Java, PHP,
        Python and Ruby. Compared to XML, it is much easier to parse reliably, and can represent
        structured data sets just as well, so users can map JSON results easily into other formats.
        We will continue to support translation specific formats when returning translation recordsets,
        which can be requested in: XML, XLIFF, and PO formats to start off with.</li>
        <li>Code maintenance : we have dramatically reduced the size of the WWL code base, and have
        fully documented the source code. This will enable users to customize their WWL server as needed
        for example to add hooks to their existing user registration and authentication system.</li>
        <li>Performance : we have also upgraded the system to take advantage of new features in App
        Engine to further improve performance and economics.</li>
        </ul>
        """
        path = os.path.join(os.path.dirname(__file__), "doc.html")
        args = dict(
            title = 'Worldwide Lexicon Translation Server',
            left_text = form,
            right_text = doc_text,
        )
        self.response.out.write(template.render(path, args))
        
def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          (r'/admin/(.*)', HandleAdmin),
                                          ('/admin', HandleAdmin),
                                          (r'/comments/(.*)', HandleComments),
                                          ('/comments', HandleComments),
                                          ('/install', HandleInstall),
                                          ('/lsp/quote', HandleLSPQuote),
                                          ('/r', HandleR),
                                          (r'/scores/user/(.*)', HandleScoresUser),
                                          ('/scores/user', HandleScoresUser),
                                          (r'/scores/(.*)', HandleScoresTranslation),
                                          ('/scores', HandleScoresTranslation),
                                          ('/submit', HandleSubmit),
                                          (r'/t/(.*)/(.*)/(.*)', HandleT),
                                          (r'/t/(.*)/(.*)', HandleT),
                                          ('/t', HandleT),
                                          (r'/u/(.*)/(.*)', HandleU),
                                          ('/u', HandleU)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

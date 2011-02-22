# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Database Interface
Content Management System / Web Server (database.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module defines persistent datastores and the functions used to fetch and
submit data to them.

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
# set constants
encoding = 'utf-8'
# import Python standard modules
import codecs
import datetime
import md5
import hashlib
import string
import types
import urllib
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
# import WWL modules
from mt import MTWrapper
from transcoder import transcoder
from BeautifulSoup import BeautifulSoup
import sgmllib

class MyParser(sgmllib.SGMLParser):
    """
    This class implements a basic HTML parser that is used to extract
    title, description and keywords from a page's HTML header. 
    """
    inside_title = False
    title = ''
    inside_meta = False
    keywords = ''
    description = ''

    def start_title(self, attrs):
        self.inside_title = True

    def end_title(self):
        self.inside_title = False

    def start_meta(self, attrs):
        self.inside_meta = True
        name = attrs[0]
        content = attrs[1]
        if string.lower(name[1]) == 'description':
            self.description = content[1]
        if string.lower(name[1]) == 'keywords':
            self.keywords = content[1]

    def end_meta(self, attrs):
        self.inside_meta = False

    def handle_data(self, data):
        if self.inside_title and data:
            self.title = self.title + data + ' '

def clean(text):
    soup = BeautifulSoup(text)
    return soup.contents[0]
    return transcoder.clean(text)

class AccessControlList(db.Model):
    guid = db.StringProperty(default='')
    rule = db.StringProperty(default='')
    value = db.StringProperty(default='')
    parm = db.StringProperty(default='')
    updatedon = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def deleterule(guid):
        if len(guid) > 0:
            adb = db.Query(AccessControlList)
            adb.filter('guid = ', guid)
            item = adb.get()
            if item is not None:
                item.delete()
                return True
        return False
    @staticmethod
    def addrule(rule, value, parm):
        if len(rule) > 0 and len(value) > 0 and len(parm) > 0:
            adb = db.Query(AccessControlList)
            adb.filter('rule = ', rule)
            adb.filter('parm = ', parm)
            item = adb.get()
            if item is None:
                m = md5.new()
                m.update(str(datetime.datetime.now()))
                guid = str(m.hexdigest())
                item = AccessControlList()
                item.guid = guid
                item.rule = rule
                item.parm = parm
            item.value = value
            item.updatedon = datetime.datetime.now()
            item.put()
            return guid
        return ''
    @staticmethod
    def viewrules():
        adb = db.Query(AccessControlList)
        adb.order('rule')
        results = adb.fetch(limit=100)
        return results

class APIKeys(db.Model):
    """
    Data store for managing API keys for trusted submitters. The system
    administrator will go to /admin/keys to create and manage API keys
    which are then used to validate trusted submitters. Servers that submit
    to the translation memory with an apikey parameter will be treated as
    trusted sources, and their submissions will be stored directly in the
    translation memory.
    """
    guid = db.StringProperty(default='')
    username = db.StringProperty(default='')
    description = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    createdon = db.DateTimeProperty(auto_now_add = True)
    lastupdate = db.DateTimeProperty()
    lastlogin = db.DateTimeProperty()
    url = db.StringProperty(default='')
    @staticmethod
    def add(username, description='', url=''):
        adb = db.Query(APIKeys)
        adb.filter('username = ', username)
        item = adb.get()
        if item is None:
            item = APIKeys()
            item.username = username
            item.description = description
            item.url = url
            m = md5.new()
            m.update(username)
            m.update(str(datetime.datetime.now()))
            guid = str(m.hexdigest())
            item.guid = guid
            item.put()
            return guid
        else:
            return ''
    @staticmethod
    def remove(guid):
        adb = db.Query(APIKeys)
        adb.filter('guid = ', guid)
        item = adb.get()
        if item is not None:
            item.delete()
            return True
        else:
            return False
    @staticmethod
    def fetch():
        adb = db.Query(APIKeys)
        adb.order('username')
        results = adb.fetch(limit=100)
        return results
    @staticmethod
    def getapikey(username):
        if len(username) > 0:
            adb = db.Query(APIKeys)
            adb.filter('username = ', username)
            item = adb.get()
            if item is not None:
                return item.guid
            else:
                return ''
    @staticmethod
    def getusername(guid):
        if len(guid) > 8:
            adb = db.Query(APIKeys)
            adb.filter('guid = ', guid)
            item = adb.get()
            if item is not None:
                return item.username
            else:
                return ''
        else:
            return ''
    @staticmethod
    def geturl(guid='', lsp=''):
        if len(guid) > 8:
            adb = db.Query(APIKeys)
            adb.filter('guid = ', guid)
            item = adb.get()
            if item is not None:
                return item.url
            else:
                return ''
        elif len(lsp) > 0:
            adb = db.Query(APIKeys)
            adb.filter('username = ', lsp)
            item = adb.get()
            if item is not None:
                return item.url
            else:
                return ''
        else:
            return ''
    @staticmethod
    def request_translation(lsp, guid, sl, tl, st, domain, url, priority, username, pw):
        if len(lsp) > 0 and len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            adb = db.Query(APIKeys)
            adb.filter('username = ', lsp)
            item = adb.get()
            if item is not None:
                url = item.url
                return LSPQueue.add('translate', url, guid, sl, tl, st, '', domain, url, priority, username, pw)
            else:
                return False
        else:
            return False
    @staticmethod
    def request_score(lsp, guid, sl, tl, st, tt, domain, url, priority, username, pw):
        if len(lsp) > 0 and len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            adb = db.Query(APIKeys)
            adb.filter('username = ', lsp)
            item = adb.get()
            if item is not None:
                url = item.url
                return LSPQueue.add('score', url, guid, sl, tl, st, tt, domain, url, priority, username, pw)
            else:
                return False
        else:
            return False
    @staticmethod
    def verify(guid):
        if len(guid) > 8:
            adb = db.Query(APIKeys)
            adb.filter('guid = ', guid)
            item = adb.get()
            if item is not None:
                return True
            else:
                return False
        else:
            return False

class BlackList(db.Model):
    domain = db.StringProperty(default='')
    user = db.StringProperty(default='')
    requester = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    createdon = db.DateTimeProperty(auto_now_add = True)
    count = db.IntegerProperty(default=1)
    @staticmethod
    def getdomain(domain):
        if len(domain) < 1:
            domain = 'all'
        udb = db.Query(BlackList)
        udb.filter('domain = ', domain)
        udb.filter('requester = ', 'all')
        records = udb.fetch(limit=500)
        results = list()
        for r in records:
            row = r.user + ',' + str(r.count)
            if row not in results and r.count > 0:
                results.append(row)
        results.sort()
        return results
    @staticmethod
    def add(domain='', user='', requester='', remote_addr='', tl=''):
        if len(domain) > 0 and len(user) > 0 and len(remote_addr) > 0:
            newrecordall=False
            newrecorddomain=False
            if len(requester) < 1:
                requester = remote_addr
            udb = db.Query(BlackList)
            udb.filter('domain = ', domain)
            udb.filter('user = ', user)
            udb.filter('requester = ', requester)
            udb.filter('remote_addr = ', remote_addr)
            if len(tl) > 0:
                udb.filter('tl = ', tl)
            item = udb.get()
            if item is None:
                newrecorddomain = True
                item = BlackList()
                item.domain = domain
                item.user = user
                item.requester = requester
                item.remote_addr = remote_addr
                item.tl = tl
                item.put()
            udb = db.Query(BlackList)
            udb.filter('domain = ', 'all')
            udb.filter('user = ', user)
            udb.filter('requester = ', requester)
            udb.filter('remote_addr = ', remote_addr)
            udb.filter('tl = ', tl)
            item = udb.get()
            if item is None:
                newrecordall=True
                item = BlackList()
                item.domain = 'all'
                item.user = user
                item.requester = requester
                item.remote_addr = remote_addr
                item.tl = tl
                item.put()
            udb = db.Query(BlackList)
            udb.filter('domain = ', domain)
            udb.filter('user = ', user)
            udb.filter('requester = ', 'all')
            udb.filter('remote_addr = ', remote_addr)
            item = udb.get()
            if item is None:
                item = BlackList()
                item.domain = domain
                item.user = user
                item.requester = 'all'
                item.remote_addr = remote_addr
                item.count = 1
            else:
                if newrecorddomain:
                    item.count = item.count + 1
            item.put()
            udb = db.Query(BlackList)
            udb.filter('domain = ', 'all')
            udb.filter('user = ', user)
            udb.filter('requester = ', 'all')
            udb.filter('remote_addr = ', remote_addr)
            item = udb.get()
            if item is None:
                item = BlackList()
                item.domain = 'all'
                item.user = user
                item.requester = 'all'
                item.remote_addr = remote_addr
                item.count = 1
            else:
                if newrecordall:
                    item.count = item.count + 1
            item.put()
            if string.count(user,'.') > 1:
                UserScores.save(remote_addr = user, score = 0, domain = domain)
            else:
                UserScores.save(username = user, score = 0, domain = domain)
            return True
        else:
            return False
    @staticmethod
    def remove(domain='', user='', requester='', remote_addr='', tl=''):
        if len(domain) > 0 and len(user) > 0 and len(remote_addr) > 0:
            if len(requester) < 1:
                requester = remote_addr
            udb = db.Query(BlackList)
            udb.filter('domain = ', domain)
            udb.filter('user = ', user)
            udb.filter('requester = ', requester)
            udb.filter('remote_addr = ', remote_addr)
            udb.filter('tl = ', tl)
            item = udb.get()
            if item is not None:
                item.delete()
            udb = db.Query(BlackList)
            udb.filter('domain = ', 'all')
            udb.filter('user = ', user)
            udb.filter('requester = ', requester)
            udb.filter('remote_addr = ', remote_addr)
            udb.filter('tl = ', tl)
            item = udb.get()
            if item is not None:
                item.delete()
            udb = db.Query(BlackList)
            udb.filter('domain = ', 'all')
            udb.filter('user = ', user)
            udb.filter('requester = ', 'all')
            udb.filter('remote_addr = ', remote_addr)
            item = udb.get()
            if item is not None:
                if item.count > 1:
                    item.count = item.count - 1
                    item.put()
                else:
                    item.delete()
            udb = db.Query(BlackList)
            udb.filter('domain = ', domain)
            udb.filter('user = ', user)
            udb.filter('requester = ', 'all')
            udb.filter('remote_addr = ', remote_addr)
            item = udb.get()
            if item is not None:
                if item.count > 1:
                    item.count = item.count - 1
                    item.put()
                else:
                    item.delete()
            return True
        else:
            return False
    @staticmethod
    def my(domain='', requester=''):
        if len(domain) > 0 and len(requester) > 0:
            results = memcache.get('/blacklist/' + domain + '/' + requester)
            if results is not None:
                return results
            udb = db.Query(BlackList)
            udb.filter('domain = ', domain)
            if len(requester) > 0:
                udb.filter('requester = ', requester)
#            udb.order('-createdon')
            records = udb.fetch(limit=500)
            results = list()
            for r in records:
                if r.user not in results:
                    results.append(r.user)
            if len(results) > 0:
                memcache.set('/blacklist/' + domain + '/' + requester, results, 300)
                return results
            else:
                return None
        else:
            return None

class Cache(db.Model):
    """
    Persistent cache, implemented as a layer on top of memcache to
    improve performance. 
    """
    name = db.StringProperty(default='')
    value = db.TextProperty(default='')
    expirationdate = db.DateTimeProperty()
    @staticmethod
    def getitem(parm, ttl=7200):
        if len(parm) > 250:
            m = md5.new()
            m.update(parm)
            parm = str(m.hexdigest())
        text = memcache.get(parm)
        if text is not None:
            return text
        else:
            cdb = db.Query(Cache)
            cdb.filter('name = ', parm)
            item = cdb.get()
            if item is None:
                return
            else:
                if datetime.datetime.now() > item.expirationdate:
                    item.delete()
                    return
                memcache.set(parm, item.value, ttl)
                return item.value
    @staticmethod
    def setitem(parm, v, ttl=7200):
        td = datetime.timedelta(seconds=ttl)
        expirationdate = datetime.datetime.now() + td
        if len(parm) > 250:
            m = md5.new()
            m.update(parm)
            parm = str(m.hexdigest())
        memcache.set(parm, v, ttl)
        cdb = db.Query(Cache)
        cdb.filter('name = ', parm)
        item = cdb.get()
        if item is None:
            item = Cache()
            item.name = parm
        item.value = unicode(v, 'utf-8')
        item.expirationdate = expirationdate
        item.put()
        memcache.set(parm, v, ttl)
        return True
    @staticmethod
    def purge():
        cdb = db.Query(Cache)
        cdb.filter('expirationdate < ', datetime.datetime.now())
        results = cdb.fetch(limit=250)
        db.delete(results)
        return True

class Comment(db.Model):
    """
    Google Data Store for comments about translations, and related
    metadata. This class is accessed via methods defined in the
    comments() class. If you want to port this application to run
    on a system other than App Engine, you will need to adapt the
    comments() class to use another database and memcache service

    md5hash : md5 hash of source text being commented on
    guid : md5 hash or unique ID of translation being commented on
    username : username of person submitting the comment
    remote_addr : IP address of person submitting the comment
    country : country (via geolocation)
    state : state/province (via geolocation)
    city : city (via geolocation)
    latitude : latitude (via geolocation, floating point)
    longitude : longitude (via geolocation, floating point)
    comment : comment text
    tl : language translation was posted in
    cl : language comment about translation was posted in
    domain : web domain of source text (e.g. foo.com)
    url : URL or permalink of source text being commented on
    date : date/time comment as posted
    .
    """
    md5hash = db.StringProperty(default = '')
    guid = db.StringProperty(default = '')
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='127.0.0.1')
    country = db.StringProperty(default = '')
    state = db.StringProperty(default = '')
    city = db.StringProperty(default='')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    comment = db.TextProperty(default = '')
    tl = db.StringProperty(default='')
    cl = db.StringProperty(default='')
    domain= db.StringProperty(default='')
    url = db.StringProperty(default='')
    date = db.DateTimeProperty(auto_now_add=True)
    spam = db.BooleanProperty(default = False)
    spamchecked = db.BooleanProperty(default = False)
    title = db.StringProperty(default = '', multiline = True)
    thread = db.StringProperty(default = '')
    group = db.StringProperty(default = '')
    tags = db.ListProperty(str)
    year = db.IntegerProperty()
    month = db.IntegerProperty()
    day = db.IntegerProperty()
    hour = db.IntegerProperty()
    day = db.IntegerProperty()
    minute = db.IntegerProperty()
    @staticmethod
    def throttle(remote_addr, ttl=10):
        """
        Checks to see if a comment has been posted from the IP address (remote_addr) in the
        past (ttl) seconds. If yes, it returns True, otherwise it returns False. This is
        a simple rate limiter that is used to prevent users from accidentally reposting
        comments, and also to block robotic submissions. 
        """
        item = memcache.get('ratelimit=' + remote_addr)
        if item is not None:
            return True
        else:
            memcache.set('ratelimit=' + remote_addr, datetime.datetime.now(), ttl)
            return False
    @staticmethod
    def get(md5hash='', guid='', username='', tl='', cl='', output='xml', city=city, country=country, group='', thread=''):
        """
        Returns a recordset of comments in the desired output format. Users can filter
        search results by md5hash (for the original source text being commented on),
        guid (for comments about a specific translation), tl (for comments about translations
        into a specific language) and cl (to limit search results to comments written in a
        specific language).

        It returns results in the desired output format (xml by default).
        """
        if len(city) < 1 and len(country) < 1 and len(group) < 1 and len(thread) < 1:
            records = memcache.get('comments.' + md5hash + '.' + guid + '.' + username + '.' + tl + '.' + cl + '.' + output)
        else:
            records = None
        if records is not None:
            return records
        else:
            if len(md5hash) > 0 or len(guid) > 0 or len(username) > 0 or len(tl) > 0 or len(cl) > 0 or len(city) > 0 or len(country) > 0 or len(group) > 0 or len(thread) > 0:
                cdb = db.Query(Comment)
                if len(md5hash) > 0:
                    cdb.filter('md5hash = ', md5hash)
                if len(guid) > 0:
                    cdb.filter('guid = ', guid)
                if len(username) > 0:
                    cdb.filter('username = ', username)
                if len(tl) > 0:
                    cdb.filter('tl = ', tl)
                if len(cl) > 0:
                    cdb.filter('cl =', cl)
                if len(city) > 0:
                    cdb.filter('city = ', city)
                if len(country) > 0:
                    cdb.filter('country = ', country)
                if len(group) > 0:
                    cdb.filter('group = ', group)
                if len(thread) > 0:
                    cdb.filter('thread = ', thread)
                records = cdb.fetch(limit = 50)
                if records is not None:
                    messages = list()
                    for r in records:
                        if r.spam:
                            pass
                        else:
                            m = msg()
                            m.md5hash = r.md5hash
                            m.guid = r.guid
                            m.username = r.username
                            m.remote_addr = r.remote_addr
                            m.state = r.state
                            m.city = r.city
                            m.country = r.country
                            m.latitude = r.latitude
                            m.longitude = r.longitude
                            m.comment = codecs.encode(r.comment,'utf-8')
                            m.tl = r.tl
                            m.cl = r.cl
                            m.domain = r.domain
                            m.url = r.url
                            m.date = r.date
                            messages.append(m)
                    d = DeepPickle()
                    if output == 'html':
                        d.fields=['date', 'username', 'city', 'comment']
                    text = d.pickleTable(messages,output)
                    if len(city) < 1 and len(country) < 1 and len(group) < 1 and len(thread) < 1:
                        memcache.set('comments.' + md5hash + '.' + guid + '.' + username + '.' + tl + '.' + cl + '.' + output,text,300)
                    return text
                else:
                    return ''
    @staticmethod
    def save(guid,fields, url=''):
        """
        This method saves a record to the Comment database. It also calls the comments.throttle()
        method to check if a comment has been submitted from the same IP address within the past
        30 seconds (if so it blocks the request). 
        """
        if len(guid) > 0 or len(url) > 0:
            pass
        else:
            return False
        if type(fields) is dict:
            if len(fields.get('md5hash','')) > 0 and len(fields.get('comment','')) > 0:
                if Comment.throttle(fields.get('remote_addr','')):
                    return False
                else:
                    now = datetime.datetime.now()
                    year = now.year
                    month = now.month
                    day = now.day
                    hour = now.hour
                    minute = now.minute
                    if len(guid) < 1:
                        m = md5.new()
                        m.update(fields.get('tl', ''))
                        m.update(fields.get('url', ''))
                        guid = str(m.hexdigest())
                    c = Comment()
                    c.md5hash = fields.get('md5hash','')
                    c.guid = guid
                    c.username = fields.get('username','')
                    c.remote_addr = fields.get('remote_addr','')
                    c.state = fields.get('state','')
                    c.city = fields.get('city','')
                    c.country = fields.get('country','')
                    c.year = year
                    c.month = month
                    c.day = day
                    c.hour = hour
                    c.minute = minute
                    try:
                        c.latitude = fields.get('latitude')
                    except:
                        pass
                    try:
                        c.longitude = fields.get('longitude')
                    except:
                        pass
                    try:
                        c.spam = fields.get('spam')
                    except:
                        c.spam = False
                    try:
                        c.spamchecked = fields['spamchecked']
                    except:
                        c.spamchecked = False
                    c.comment = fields.get('comment','')
                    c.tl = fields.get('tl','')
                    c.cl = fields.get('cl','')
                    c.domain = fields.get('domain','')
                    c.url = fields.get('url','')
                    c.group = fields.get('group', '')
                    c.thread = fields.get('thread', '')
                    c.put()
                    Translation.comment(guid)
                    return True
            else:
                return False                                                     
        else:
            return False
    @staticmethod
    def stats(st='', md5hash='', guid='', username='', remote_addr='', city='', country=''):
        if len(st) > 0 or len(md5hash) > 0 or len(guid) > 0 or len(username) > 0 or len(remote_addr) > 0 or len(city) > 0 or len(country) > 0:
            tdb = db.Query(Comment)
            if len(st) > 0:
                m = md5.new()
                m.update(st)
                md5hash = str(m.hexdigest())
                tdb.filter('md5hash = ', md5hash)
            elif len(md5hash) > 0:
                tdb.filter('md5hash = ', md5hash)
            elif len(guid) > 0:
                tdb.filter('guid = ', guid)
            elif len(username) > 0:
                tdb.filter('username = ', username)
            elif len(remote_addr) > 0:
                tdb.filter('remote_addr = ', remote_addr)
            elif len(city) > 0:
                tdb.filter('city = ', city)
            elif len(country) > 0:
                tdb.filter('country = ', country)
            else:
                tdb.filter('country = ', 'XYZ')
            ctr = tdb.count(limit=1000)
            return ctr
        else:
            return 0

class DirectoryIP(db.Model):
    """
    This datastore maintains a map of IP addresses and the domains mapped to them.
    This is used to limit the number of domains that can be submitted to the page
    tracking system from a single IP address. We also use Akismet to detect and
    filter spam submissions, as well as rate limit submissions. 
    """
    remote_addr = db.StringProperty(default='')
    domains = db.ListProperty(str)
    apikey = db.StringProperty(default='')
    @staticmethod
    def verify(remote_addr,domain):
        if len(remote_addr) > 0 and len(domain) > 0:
            hdb = db.Query(DirectoryIP)
            hdb.filter('remote_addr = ', remote_addr)
            item = hdb.get()
            if item is not None:
                domains = item.domains
                if len(domains) > 5:
                    return False
                else:
                    if domain in domains:
                        return True
                    else:
                        domains.append(domain)
                        item.domains = domains
                        item.put()
                        return True
            else:
                item = DirectoryIP()
                item.remote_addr = remote_addr
                domains = list()
                domains.append(domain)
                item.domains = domains
                item.put()
                return True
        else:
            return False

class Directory(db.Model):
    guid = db.StringProperty(default='')
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    title = db.StringProperty(default='')
    ttitle = db.StringProperty(default='')
    description = db.TextProperty(default='')
    tdescription = db.TextProperty(default='')
    tags = db.ListProperty(str)
    views = db.IntegerProperty(default=0)
    lastupdated = db.DateTimeProperty(auto_now_add=True)
    hosttype = db.StringProperty(default='')
    indexed = db.BooleanProperty(default=False)
    words = db.ListProperty(str)
    @staticmethod
    def hostname(hostname, sl, tl, remote_addr=''):
        exists = memcache.get('/hosts/' + hostname)
        if exists is None:
            hdb = db.Query(Directory)
            hdb.filter('domain = ', hostname)
            hdb.filter('sl = ', sl)
            hdb.filter('tl = ', 'root')
            item = hdb.get()
            if item is None:
                item = Directory()
                m = md5.new()
                m.update(hostname)
                m.update('root')
                m.update(str(datetime.datetime.now()))
                guid = str(m.hexdigest())
                item.guid = guid
                item.domain = hostname
                item.sl = sl
                item.tl = 'root'
                item.lastupdated = datetime.datetime.now()
                item.put()
            memcache.set('/hosts/' + hostname, True, 7200)
        exists = memcache.get('/hosts/' + hostname + '/' + sl + '/' + tl)
        if exists is not None:
            return
        else:
            hdb = db.Query(Directory)
            hdb.filter('domain = ', hostname)
            if len(tl) > 0:
                hdb.filter('tl = ', tl)
            item = hdb.get()
            if item is None:
                m = md5.new()
                m.update(hostname)
                m.update(str(datetime.datetime.now()))
                m.update(tl)
                guid = str(m.hexdigest())
                item = Directory()
                item.guid = guid
                item.domain = string.replace(hostname, 'http://', '')
                item.url = item.domain
                item.tl = tl
                item.sl = sl
            item.lastupdated = datetime.datetime.now()
            item.put()
            memcache.set('/hosts/' + hostname + '/' + sl + '/' + tl, True, 7200)
            return
    @staticmethod
    def purge():
        td = datetime.timedelta(days=-30)
        lastdate = datetime.datetime.now() + td
        hdb = db.Query(Directory)
        hdb.filter('lastupdated < ', lastdate)
        results = hdb.fetch(limit=200)
        if len(results) > 0:
            db.delete(results)
            return True
        else:
            return False
    @staticmethod
    def save(remote_addr, domain, url, sl, tl, title, ttitle='', description='', tdescription='', tags='', hosttype='', user_agent=''):
        if len(domain) > 0 and len(url) > 0 and len(sl) > 0 and len(tl) > 0:
            # call Akismet to verify post is not spam
            akismetapi = Settings.get('akismet')
            if akismetapi is not None:
                if len(akismetapi) > 0:
                    a = Akismet()
                    a.setAPIKey(akismetapi)
                    try:
                        a.verify_key()
                        data = dict()
                        data['user_ip']= remote_addr
                        if len(user_agent) > 0:
                            data['user_agent'] = self.request.headers['User-Agent']
                        if a.comment_check(title + ' ' + description, data):
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
                valid = DirectoryIP.verify(remote_addr, domain)
                if valid:
                    m = md5.new()
                    m.update(url)
                    m.update(sl)
                    m.update(tl)
                    guid = str(m.hexdigest())
                    hdb = db.Query(Directory)
                    hdb.filter('guid = ', guid)
                    item = hdb.get()
                    if item is None:
                        item = Directory()
                        item.guid = guid
                        item.sl = sl
                        item.tl = tl
                        item.domain = domain
                        item.url = url
                        item.hosttype = hosttype
                    item.title = title
                    item.description = description
                    item.ttitle = ttitle
                    item.tdescription = tdescription
                    if len(tags) > 0:
                        tags = string.lower(tags)
                        tags = string.split(tags, ',')
                        if len(tags) > 0:
                            item.tags = tags
                    item.lastupdated = datetime.datetime.now()
                    item.put()
                    return True
                else:
                    return False
            else:
                return False
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

class languages():
    """
    This class implements several convenience methods for managing the list of supported languages on
    your translation memory server. The system recognizes a relatively large list of languages by default
    which are pre-defined in the method getlist(). 
    """
    @staticmethod
    def auto(text=''):
        if len(text) > 1:
            l = text[:2]
            return l
        else:
            return 'en'
    @staticmethod
    def header(text=''):
        langs=list()
        if len(text) > 0:
            langtext = string.split(text, ',')
            if len(langtext) > 0:
                for l in langtext:
                    loctext = string.split(l, ';')
                    if len(loctext) > 0:
                        locale = loctext[0]
                    else:
                        locale = ''
                    if len(locale) > 3:
                        locale = locale[0:2]
                        locale = string.replace(locale, '-', '')
                    if len(locale) > 1:
                        langs.append(locale)
            return langs
        else:
            return langs
    @staticmethod
    def getlist(languages='', english='n'):
        """
        Returns a list of languages, indexed by ISO language code in a dict() object.
        The optional languages argument is pass with a list of ISO codes to limit the
        list to a smaller pre-defined list of languages (if you only want to allow
        translations to a smaller group of languages on your site.
        """
        langs = memcache.get('/languages')
        if langs is not None:
            if len(languages) > 0:
                language = langs.get(languages,'')
                return language
            else:
                return langs
        else:
            results = Languages.find()
            if len(results) > 0:
                ln = dict()
                for r in results:
                    ln[r.code]=r.name
                memcache.set('/languages', ln, 300)
                if len(languages) > 0:
                    language = ln.get(languages,'')
                    return language
                else:
                    return ln
            else:
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
                memcache.set('/languages', l, 300)
                if len(languages) > 0:
                    language = l.get(languages,'')
                    return language
                else:
                    return l
    @staticmethod
    def select(selected='', filter=None):
        langlist = languages.getlist()
        langkeys = langlist.keys()
        langkeys.sort()
        t = ''
        if len(selected) > 0:
            t = t + '<option value="' + selected + '">' + langlist.get(selected, '') + '</option>'
        for l in langkeys:
            if type(filter) is list:
                if l in filter:
                    valid=True
                else:
                    valid=False
            else:
                valid = True
            if valid:
                t = t + '<option value="' + l + '">' + langlist.get(l, '') + '</option>'
        return t

class Log(db.Model):
    application = db.StringProperty(default='')
    date = db.DateTimeProperty(auto_now_add=True)
    text = db.TextProperty(default='')
    @staticmethod
    def log(application, text):
        item = Log()
        item.app = application
        item.text = text
        item.put()

class rec():
    sl = 'en'
                    
class Score(db.Model):
    """
    Google Data Store for translation quality scores.

    md5hash : md5 hash key derived from the source text (untranslated text)
    guid : md5 hash or GUID associated with a specific translation
    domain : web domain associated with texts (e.g foo.com)
    url : URL or permalink of source document
    score : quality score (integer: 0-5)
    username : username of person who created or edited the translation being scored
    scoredby : username of person who submitted score
    remote_addr : IP address of person who created the translation
    scoredby_remote_addr : IP address of person who scored the translation
    country : country of person who submitted score
    state : state/province of person who submitted score
    city : city of person who submitted score
    latitude : latitude of person who submitted score
    longitude : longitude of person who submitted score
    date : date/time score was created
    """
    md5hash = db.StringProperty(default='')
    guid = db.StringProperty(default='')
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    st = db.TextProperty(default='')
    tt = db.TextProperty(default='')
    score = db.IntegerProperty(default=0)
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='127.0.0.1')
    scoredby = db.StringProperty(default='')
    scoredby_remote_addr = db.StringProperty(default='127.0.0.1')
    country = db.StringProperty(default='')
    state = db.StringProperty(default='')
    city = db.StringProperty(default='')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    blocked = db.BooleanProperty(default = False)
    date = db.DateTimeProperty(auto_now_add=True)
    lsp = db.BooleanProperty(default=False)
    lspname = db.StringProperty(default='')
    jobid = db.StringProperty(default='')
    comment = db.TextProperty(default='')
    @staticmethod
    def get(remote_addr, username=''):
        data = memcache.get('/scores/' + remote_addr + '/' + username)
        if data is not None:
            return data
        elif len(username) > 0:
            sdb = db.Query(Score)
            sdb.filter('username = ', username)
        else:
            sdb = db.Query(Score)
            sdb.filter('remote_addr = ', remote_addr)
        results = sdb.fetch(limit=200)
        scores = 0
        rawscore = 0
        for r in results:
            if r.score is not None:
                rawscore = rawscore + 1
                scores = scores + 1
        data = dict()
        data['scores']=scores
        data['rawscore']=rawscore
        if scores > 0:
            data['avgscore']=float(rawscore/scores)
        else:
            data['avgscore']=float(0)
        memcache.set('/scores/' + remote_addr + '/' + username)
        return data            
    @staticmethod
    def batch(authors):
        pass
    @staticmethod
    def lsp(guid='', jobid='', fields=dict()):
        pass
    @staticmethod
    def exists(guid, remote_addr):
        if len(guid) > 0 and len(remote_addr) > 0:
            sdb = db.Query(Score)
            sdb.filter('guid = ', guid)
            sdb.filter('scoredby_remote_addr = ', remote_addr)
            item = sdb.get()
            if item is not None:
                return True
            else:
                return False
        else:
            return True
    @staticmethod
    def fetch(guid='', username='', url='', remote_addr=''):
        if len(guid) > 0 or len(username) > 0 or len(url) > 0 or len(remote_addr) > 0:
            records = memcache.get('/scores/records/' + guid + username + url + remote_addr)
            if records is not None:
                return records
            else:
                sdb = db.Query(Score)
                if len(guid) > 0:
                    sdb.filter('guid = ', guid)
                elif len(username) > 0:
                    sdb.filter('username = ', username)
                elif len(remote_addr) > 0:
                    sdb.filter('remote_addr = ', remote_addr)
                elif len(url) > 0:
                    sdb.filter('url = ', url)
                else:
                    return
                results = sdb.fetch(limit=500)
                records = list()
                for r in results:
                    score = rec()
                    score.guid = r.guid
                    if r.score == 5:
                        score.votetype = 'up'
                        score.score = 5
                    elif r.blocked:
                        score.votetype = 'block'
                        score.score = 0
                    else:
                        score.votetype = 'down'
                        score.score = 0
                    records.append(score)
                records = memcache.set('/scores/records/' + guid + username + url + remote_addr, records, 600)
                return records
        else:
            return
    @staticmethod
    def save(guid, sl='', tl='', st='', tt='', votetype='', username='', remote_addr='', score='', city='', state='', country='', latitude=None, longitude=None, domain='', url=''):
        """
        This method saves a score to the Score data store, after first checking to see if
        a score has already been recorded for this item (guid locator) from the user's IP
        address. If a score has already been recorded, it will update the existing record,
        and if not, will create a new record. 
        """
        tx = Translation.getbyguid(guid)
        if type(tx) is dict:
            if len(score) > 0 and int(score) < 1 and len(guid) > 0:
                Translation.spam(guid)
            author_username = tx.get('username', '')
            author_ip = tx.get('remote_addr', '')
            sl = tx.get('sl', '')
            tl = tx.get('tl', '')
            st = tx.get('st', '')
            tt = tx.get('tt', '')
            domain = tx.get('domain', '')
            url = tx.get('url', '')
            md5hash = tx.get('md5hash', '')
            sdb = db.Query(Score)
            sdb.filter('guid = ', guid)
            sdb.filter('scoredby_remote_addr = ', remote_addr)
            item = sdb.get()
            if item is None:
                item = Score()
                item.guid = guid
                item.scoredby_remote_addr = remote_addr
                item.scoredby = username
            item.md5hash = md5hash
            item.guid = guid
            item.username = author_username
            item.remote_addr = author_ip
            item.city = city
            item.state = state
            item.country = country
            item.sl = sl
            item.tl = tl
            item.st = clean(st)
            item.tt = clean(tt)
            item.domain = domain
            item.url = url
            try:
                item.latitude = float(latitude)
                item.longitude = float(longitude)
            except:
                pass
            if votetype == 'up':
                item.score = 5
            elif votetype == 'down':
                item.score = 2
            elif votetype == 'block':
                item.score = 0
                item.blocked = True
            elif len(score) > 0:
                try:
                    if int(score) >= 0 and int(score) <= 5:
                        item.score = int(score)
                        if int(score) == 0:
                            item.blocked = True
                except:
                    pass                    
            item.put()
            p = dict()
            p['guid']=guid
            return True
        else:
            return False
    @staticmethod
    def stats(guid='', md5hash='', username='', remote_addr ='', sl='', tl='', domain='', url='',city='', country=''):
        pass
    @staticmethod
    def updateuser(username, remote_addr):
        pass
        
class Search(db.Model):
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    rssurl = db.StringProperty(default='')
    rss = db.BooleanProperty(default = False)
    rssupdated = db.DateTimeProperty(auto_now_add = True)
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    title = db.StringProperty(default='', multiline=True)
    description = db.TextProperty(default='')
    ttitle = db.StringProperty(default='', multiline=True)
    tdescription = db.TextProperty(default='')
    keywords = db.ListProperty(str)
    tkeywords = db.ListProperty(str)
    views = db.IntegerProperty(default=0)
    translations = db.IntegerProperty(default=0)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    recommendedby = db.StringProperty(default='')
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    date = db.DateTimeProperty(auto_now_add=True)
    issite = db.BooleanProperty(default=False)
    islisting = db.BooleanProperty(default=False)
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    translationrequested = db.BooleanProperty(default=False)
    translationrequestedby = db.ListProperty(str)
    translationrequestedtimestamp = db.DateTimeProperty()
    @staticmethod
    def meta(url, tl=''):
        if len(url) > 0 and len(tl) > 0:
            sdb = db.Query(Search)
            sdb.filter('url = ', '')
            sdb.filter('tl = ', tt)
            item = sdb.get()
            if item is not None:
                items = list()
                i = tx()
                i.url = item.url
                i.domain = item.domain
                i.sl = item.sl
                i.tl = item.tl
                i.title = item.title
                i.description = item.description
                if item.title is not None:
                    i.ttitle = clean(item.ttitle)
                else:
                    i.ttitle = ''
                if i.tdescription is not None:
                    i.tdescription = clean(item.tdescription)
                else:
                    i.tdescription = ''
                if i.tkeywords is not None:
                    i.tkeywords = str(item.tkeywords)
                else:
                    i.tkeywords = ''
                items.append(i)
                return items
    @staticmethod
    def add(url, sl='en', title='', description='', keywords=None, recommendedby=None, rssurl=None):
        if string.count(url, 'https') > 0:
            url = ''
        url = string.replace(url, 'http://', '')
        urltexts = string.split(url, '/')
        if len(urltexts) > 0:
            domain = urltexts[0]
        if len(url) > 0:
            validrss=False
            if len(rssurl) > 0:
                if string.count(rssurl, 'feed://') > 0:
                    rssurl = string.replace(rssurl, 'feed://', 'http://')
                if string.count(rssurl, 'http://') < 1:
                    rssurl = 'http://' + rssurl
                try:
                    response = urlfetch.fetch(url = rssurl)
                    if response.status_code == 200:
                        rsstext = response.content
                    else:
                        rsstext = ''
                except:
                    rsstext = ''
                if len(rsstext) > 0:
                    try:
                        r = feedparse.parse(rsstext)
                        entries=r.entries
                        validrss = True
                    except:
                        validrss = False
            sdb = db.Query(Search)
            sdb.filter('url = ', url)
            sdb.filter('sl = ', sl)
            sdb.filter('islisting = ', True)
            item = sdb.get()
            if item is None:
                item = Search()
                item.url = url
                item.sl = sl
                item.islisting = True
            item.domain = domain
            item.title = title
            item.description = description
            item.issite = True
            if len(title) > 0:
                titlewords = string.split(string.lower(title), ' ')
            else:
                titlewords = list()
            if validrss:
                item.rssurl = rssurl
                item.rss = True
            else:
                item.rss = False
            if keywords is None:
                keywords=list()
            for t in titlewords:
                if len(t) < 400:
                    keywords.append(t)
            if keywords is not None:
                keytext = ''
                for k in keywords:
                    keytext = keytext + ' ' + k
                langs = ['en', 'fr', 'de', 'it', 'es', 'pt', 'ja', 'ko', 'zh', 'ar', 'fa']
                transtext = ''
                mt = MTWrapper()
                for l in langs:
                    if sl != l:
                        transtext = transtext + ' ' + mt.getTranslation(sl,l, keytext)
                keytext = keytext + transtext
                keywords = string.split(keytext, ' ')
                itemkeys = list()
                for k in keywords:
                    if len(k) < 400:
                        itemkeys.append(k)
                item.keywords = itemkeys
            item.islisting = True
            item.put()
            return True
        else:
            return False
    @staticmethod
    def log(url, sl='en', tl='', title='', description='', keywords=None, vote=None, recommendedby=None, action = '', remote_addr = '', city='', state='', country ='', latitude=None, longitude = None):
        ignore = ['google', 'gmail', 'hotmail', 'facebook', 'flickr', 'rentacoder']
        if string.count(url, 'https') > 0:
            url = ''
        if len(url) > 0:
            Stats.save(remote_addr, username = '', city=city, state=state, country=country, latitude=latitude, longitude=longitude)
            try:
                if string.count(url, 'http://') < 1:
                    turl = 'http://' + url
                else:
                    turl = url
                response = urlfetch.fetch(url = turl)
                if response.status_code == 200:
                    rawhtml = response.content
                    rawhtml = clean(rawhtml)
                else:
                    rawhtml = ''
                p = MyParser()
                p.feed(rawhtml)
                p.close()
                title = p.title
                if len(title) > 200:
                    title = title[0:200]
                description = p.description
                keywords = string.split(p.keywords, ',')
            except:
                pass
            url = string.replace(url, 'http://', '')
            urltexts = string.split(url, '/')
            domain = urltexts[0]
            dtexts = string.split(domain, '.')
            if len(dtexts) == 2:
                d = dtexts[0]
            elif len(dtexts) == 3:
                d = dtexts[1]
            else:
                d = ''
            if d in ignore:
                url = ''
        if len(url) > 0 and len(url) < 400:
            sdb = db.Query(Search)
            sdb.filter('url = ', url)
            sdb.filter('tl = ', tl)
            item = sdb.get()
            if item is None:
                item = Search()
                item.url = url
                item.sl = sl
                item.tl = tl
                item.title = title
                item.description = description
                item.city = city
                item.country = country
                if keywords is not None:
                    if type(keywords) is list:
                        item.keywords = keywords
                if recommendedby is not None:
                    item.recommendedby = recommendedby
                item.views = 0
            if action == 'translate':
                item.translations = item.translations + 1
            else:
                item.views = item.views + 1
            item.domain = domain
            if vote is not None:
                if vote == 'up':
                    item.upvotes = item.upvotes + 1
                elif vote == 'down':
                    item.downvotes = item.downvotes + 1
                else:
                    pass
            item.date = datetime.datetime.now()
            if len(urltexts) < 2:
                item.issite = True
            else:
                if len(urltexts[1]) < 1:
                    item.issite = True
            item.put()
            return True
        else:
            return False
    @staticmethod
    def purge():
        sdb = db.Query(Search)
        td = datetime.timedelta(days=-90)
        lastdate = datetime.datetime.now() + td
        sdb.filter('date < ', lastdate)
        results = sdb.fetch(limit=250)
        if len(results) > 0:
            db.delete(results)
            return True
        else:
            return False
    @staticmethod
    def query(tl='', q = ''):
        sdb = db.Query(Search)
        if len(tl) > 0:
            sdb.filter('tl = ', tl)
        if len(q) > 0:
            sdb.filter('keywords = ', q)
        sdb.order('-date')
        results = sdb.fetch(limit=50)
        return results
    @staticmethod
    def request(url, title = '', description = '', comment = '', sl = '', tl = '', username=''):
        if len(url) > 0:
            sdb = db.Query(Search)
            sdb.filter('url = ', url)
            sdb.filter('tl = ', tl)
            item = sdb.get()
            if item is None:
                item = Search()
                item.url = url
                item.title = clean(title)
                item.description = clean(description)
                item.comment = clean(comment)
                item.upvotes = 0
            users = item.translationrequestedby
            item.translationrequested = True
            if len(username) > 0:
                if username not in users:
                    users.append(username)
                    item.translationrequestedby = users
                    upvotes = item.upvotes
                    if type(upvotes) is int:
                        pass
                    else:
                        upvotes = 0
                    item.upvotes = upvotes + 1
            item.put()
            return True
    
class Settings(db.Model):
    website = db.StringProperty(default = '')
    name = db.StringProperty(default = '')
    value = db.TextProperty(default = '')
    created = db.DateTimeProperty(auto_now_add = True)
    modified = db.DateTimeProperty()
    modifiedby = db.StringProperty(default = '')
    @staticmethod
    def get(name, website=''):
#        value = memcache.get('settings|name=' + name + '|website=' + website)
        value = None
        if value is not None:
            return value
        else:
            sdb = db.Query(Settings)
            sdb.filter('name = ', name)
            item = sdb.get()
            if item is not None:
                v = item.value
#                memcache.set('settings|name=' + name + '|website=' + website, v, 600)
                return v
            else:
                return ''
    @staticmethod
    def heartbeat():
        sdb = db.Query(Settings)
        sdb.filter('name = ', 'heartbeat')
        item = sdb.get()
        timestamp = datetime.datetime.now()
        if item is None:
            item = Settings()
            item.name = 'heartbeat'
        item.value = str(timestamp)
        item.modified = timestamp
        item.modifiedby = 'cron'
        item.put()
        return str(timestamp)
    @staticmethod
    def save(name, v, website='', user=''):
        sdb = db.Query(Settings)
        sdb.filter('name = ', name)
        item = sdb.get()
        if item is None:
            item = Settings()
            item.name = name
        item.value = v
        item.modified = datetime.datetime.now()
        item.modifiedby = user
        item.put()
        memcache.set('settings|name=' + name + '|website=' + website, v, 600)
        return True
        
class Stats(db.Expando):
    date = db.DateTimeProperty(auto_now_add = True)
    year = db.IntegerProperty()
    month = db.IntegerProperty()
    day = db.IntegerProperty()
    hour = db.IntegerProperty()
    remote_addr = db.StringProperty(default = '')
    city = db.StringProperty(default = '')
    state = db.StringProperty(default = '')
    country = db.StringProperty(default = '')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    username = db.StringProperty(default = '')
    languages = db.ListProperty(str)
    views = db.IntegerProperty(default = 0)
    @staticmethod
    def purge():
        td = datetime.timedelta(days=-90)
        now = datetime.datetime.now()
        lastdate = now + td
        sdb = db.Query(Stats)
        sdb.filter('date < ', lastdate)
        results = sdb.fetch(limit=200)
        if len(results) > 0:
            db.delete(results)
            return True
        else:
            return False
    @staticmethod
    def save(remote_addr, username = '', city = '', state = '', country = '', latitude = None, longitude = None, languages=None):
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        sdb = db.Query(Stats)
        sdb.filter('remote_addr = ', remote_addr)
        sdb.filter('year = ', year)
        sdb.filter('month = ', month)
        sdb.filter('day = ', day)
        sdb.filter('hour = ', hour)
        item = sdb.get()
        if item is None:
            item = Stats()
            item.remote_addr = remote_addr
            item.year = year
            item.month = month
            item.day = day
            item.hour = hour
            item.city = city
            item.state = state
            item.country = country
            item.date = now
            if latitude is not None and longitude is not None:
                try:
                    item.latitude = latitude
                    item.longitude = longitude
                except:
                    pass
            item.username = username
            if languages is not None and type(languages) is list:
                item.languages = languages
        views = item.views
        if views is not None:
            views = views + 1
        else:
            views = 1
        item.views = views
        item.put()
        return True
        
class tx():
    sl = ''

class Translation(db.Model):
    """
    Google Data Store that is used to create and store translations
    to the translation log. The system logs every suggested translation
    so there may be many candidate human and machine translations for a given
    phrase or sentence. This data store also captures meta data about
    each translation, such as who created it (username or IP address),
    average score, etc.

    md5hash : md5 hash derived from source text
    guid : md5 hash or GUID for a specific translation
    domain : web domain assocated with translation (e.g. foo.com)
    url : URL or permalink associated with source text
    meta : tag or category
    sl : source language code (ISO code, 2 or 3 letters)
    tl : target language code (ISO code, 2 or 3 letters)
    st : source text
    tt : translation text
    swords : number of words in source text
    twords : number of words in target text
    username : username of person who created or edited translation
    remote_addr : IP address of person who created or edited translation
    country : country of person who submitted translation
    state : state/province
    city : city
    latitude : latitude (float)
    longitude : longitude (float)
    avgscore : average quality score (float)
    rawscore : raw score (total of all scores submitted, integer)
    scores : number of scores submitted, integer
    userapproved : marked as approved by other users
    userflagged : flagged for removal by other users
    editorapproved : marked as approved by editors
    editorflagged : flagged for removal by editors
    editorscore : quality score set by editors
    date : date/time translation was created
    machine : is a machine translation, true/false
    human : is a human translation, true/false
    geocoded : translation has been geocoded, true/false
    anonymous : this is an anonymous translation, true/false
    reviewed : this has been reviewed by an editor or translator, true/false
    """
    md5hash = db.StringProperty(default='')
    guid = db.StringProperty(default='')
    domain = db.StringProperty(default='dermundo.com')
    url = db.StringProperty(default='')
    meta = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    st = db.TextProperty(default='')
    tt = db.TextProperty(default='')
    swords = db.IntegerProperty()
    twords = db.IntegerProperty()
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='127.0.0.1')
    country = db.StringProperty(default='')
    state = db.StringProperty(default='')
    city = db.StringProperty(default='')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    avgscore=db.FloatProperty()
    score = db.IntegerProperty(default=0)
    rawscore = db.IntegerProperty(default=0)
    scores = db.IntegerProperty(default=0)
    userapproved = db.BooleanProperty(default=False)
    userflagged = db.BooleanProperty(default=False)
    editorapproved = db.BooleanProperty(default=False)
    editorflagged = db.BooleanProperty(default=False)
    editorscore = db.IntegerProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    machine = db.BooleanProperty(default=False)
    human = db.BooleanProperty(default=True)
    admin = db.BooleanProperty(default=False)
    geocoded = db.BooleanProperty(default=False)
    anonymous = db.BooleanProperty(default=True)
    reviewed = db.BooleanProperty(default=False)
    spam = db.BooleanProperty(default=False)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    blockedvotes = db.IntegerProperty(default=0)
    useravgscore = db.FloatProperty()
    userupvotes = db.IntegerProperty(default=0)
    userdownvotes = db.IntegerProperty(default=0)
    userblockedvotes = db.IntegerProperty(default=0)
    userscores = db.IntegerProperty(default=0)
    userrawscore = db.IntegerProperty(default=0)
    comments = db.IntegerProperty(default=0)
    professional = db.BooleanProperty(default=False)
    locked = db.BooleanProperty(default = True)
    indexed = db.BooleanProperty(default = False)
    ngrams = db.ListProperty(str)
    spamvotes = db.IntegerProperty(default = 0)
    expirationdate = db.DateTimeProperty()
    facebookid = db.StringProperty(default='')
    profile_url = db.StringProperty(default='')
    mirrored = db.BooleanProperty(default=False)
    @staticmethod
    def getusersbyurl(url, tl=''):
        url = string.replace(url, 'http://','')
        url = string.replace(url, 'https://','')
        tdb = db.Query(Translation)
        tdb.filter('url = ', url)
        tdb.order('-date')
        results = tdb.fetch(200)
        users=list()
        userlist=list()
        if results is not None:
            for r in results:
                if r.username not in users and len(r.username) > 0:
                    users.append(r.username)
                    u = dict(
                        username = r.username,
                        profile_url = r.profile_url,
                        tl = r.tl,
                        city = r.city,
                        country = r.country,
                        facebookid = r.facebookid,
                        id = r.facebookid,
                    )
                    userlist.append(u)
        return userlist
    @staticmethod
    def author(guid):
        if len(guid) > 0:
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                return item.username
            else:
                return ''
        else:
            return ''
    @staticmethod
    def authors(url, tl=''):
        if len(url) > 0:
            tdb = db.Query(Translation)
            tdb.filter('url = ', url)
            if len(tl) > 0:
                tdb.filter('tl = ', tl)
            results = tdb.fetch(limit=200)
            a = list()
            for r in results:
                if len(r.username) > 0:
                    a.append(r.username)
                else:
                    a.append(r.remote_addr)
            return a
        else:
            return
    @staticmethod
    def getfbuser(guid):
        tdb = db.Query(Translation)
        tdb.filter('guid = ', guid)
        item = tdb.get()
        if item is not None:
            facebookid = item.facebookid
            if facebookid is not None:
                return facebookid
    @staticmethod
    def comment(guid):
        if len(guid) < 1:
            return False
        else:
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                ctr = item.comments
                if type(ctr) is int:
                    ctr = ctr + 1
                else:
                    ctr = 1
                item.comments = ctr
                item.put()
                return True
            else:
                return False
    @staticmethod
    def getbyguid(guid):
        tdb = db.Query(Translation)
        tdb.filter('guid = ', guid)
        item = tdb.get()
        tx = dict()
        if item is not None:
            tx['guid'] = guid
            tx['md5hash']= item.md5hash
            tx['username']= item.username
            tx['remote_addr']=item.remote_addr
            tx['domain']=item.domain
            tx['url']=item.url
            tx['upvotes']=item.upvotes
            tx['downvotes']=item.downvotes
            tx['blockedvotes']=item.blockedvotes
            tx['avgscore']=item.avgscore
            tx['scores']=item.scores
            tx['city']=item.city
            tx['state']=item.state
            tx['country']=item.country
            tx['latitude']=item.latitude
            tx['longitude']=item.longitude
            tx['date']=item.date
            tx['spam']=item.spam
        return tx
    @staticmethod
    def lsp(sl, tl, st, domain='', url='', lsp='', lspusername='', lsppw=''):
        return ''
    @staticmethod
    def generatengrams(guid,limit=5):
        """
        This function is called as a background process to index new translations for full text
        search (breaks the words into ngrams).
        """
        tdb = db.Query(Translation)
        if len(guid) > 0:
            tdb.filter('guid = ', guid)
            results = tdb.fetch(limit=10)
        else:
            tdb.filter('userapproved = ', False)
            results = tdb.fetch(limit=limit)
        for r in results:
            st = string.lower(r.st)
            texts = st
            st = string.replace(st, '.', '')
            st = string.replace(st, '\'', '')
            st = string.replace(st, '\"', '')
            st = string.replace(st, '-','')
            swords = string.split(st, ' ')
            swordcount = len(swords)
            tt = string.lower(r.tt)
            texts = texts + tt
            tt = string.replace(tt, '.', '')
            tt = string.replace(tt, '\'', '')
            tt = string.replace(tt, '\"', '')
            tt = string.replace(tt, '-','')
            twords = string.split(tt, ' ')
            twordcount = len(twords)
            ngrams = list()
            for i in texts:
                if i not in ngrams:
                    ngrams.append(i)
            for s in swords:
                if len(s) < 30 and s not in ngrams:
                    ngrams.append(s)
            for t in twords:
                if len(t) < 30 and t not in ngrams:
                    ngrams.append(t)
            r.ngrams = ngrams
            r.swords = swordcount
            r.twords = twordcount
            r.indexed = True
            r.userapproved = True
            r.put()
    @staticmethod
    def seteditor(guid, editorscore='', approved='', rejected='', spam=''):
        if len(guid) > 0:
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                if len(editor_score) > 0:
                    try:
                        score = int(editorscore)
                        item.editorscore = score
                    except:
                        pass
                if approved == 'y':
                    item.editorapproved = True
                elif approved == 'n':
                    item.editorapproved = False
                else:
                    pass
                if rejected == 'y':
                    item.editorflagged = True
                elif rejected == 'n':
                    item.editorflagged = False
                else:
                    pass
                item.put()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def score(guid, votetype, score=''):
        if len(guid) > 0:
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                upvotes = item.upvotes
                downvotes = item.downvotes
                blockedvotes = item.blockedvotes
                rawscore = item.rawscore
                scores = item.scores
                if votetype == 'up':
                    upvotes = upvotes + 1
                    rawscore = rawscore + 5
                    scores = scores + 1
                elif votetype == 'down':
                    rawscore = rawscore + 2
                    downvotes = downvotes + 1
                    scores = scores + 1
                elif votetype == 'block':
                    blockedvotes = blockedvotes + 1
                    scores = scores + 1
                elif len(score) > 0:
                    if int(score) >=0 and int(score) <=5 :
                        rawscore = rawscore + int(score)
                        scores = scores + 1
                else:
                    pass
                if scores > 0:
                    avgscore = float(rawscore/scores)
                else:
                    avgscore = float(0)
                item.upvotes = upvotes
                item.downvotes = downvotes
                item.blockedvotes = blockedvotes
                item.rawscore = rawscore
                item.avgscore = avgscore
                item.put()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def markasspam(guid):
        if len(guid) > 0:
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                item.spam = True
                item.professional = False
                item.put()
                return True
        return False
    @staticmethod
    def stats(sl='', tl='', domain='', url='', username='', remote_addr='', startdate=None, enddate=None):
        tdb = db.Query(Translation)
        if len(sl) > 0:
            tdb.filter('sl = ', sl)
        if len(tl) > 0:
            tdb.filter('tl = ', tl)
        if len(domain) > 0:
            tdb.filter('domain = ', domain)
        if len(url) > 0:
            tdb.filter('url = ', url)
        if len(remote_addr) > 0:
            tdb.filter('remote_addr = ', remote_addr)
        if len(username) > 0:
            tdb.filter('username = ', username)
        records = tdb.fetch(limit=250)
        results = dict()
        results['swords']=0
        results['twords']=0
        results['translations']=len(records)
        results['users']=list()
        results['languages']=list()
        results['cities']=list()
        for r in records:
            if r.swords is not None:
                results['swords']=results['swords']+r.swords
            if r.twords is not None:
                results['twords']=results['twords']+r.twords
            if r.username not in results['users']:
                results['users'].append(r.username)
            if r.remote_addr not in results['users']:
                results['users'].append(r.remote_addr)
            if r.sl not in results['languages']:
                results['languages'].append(r.sl)
            if r.tl not in results['languages']:
                results['languages'].append(r.tl)
            if r.city not in results['cities']:
                results['cities'].append(r.city)
        return results
    @staticmethod
    def submit(guid = '', sl='', st='', tl='', tt='', username='', remote_addr='', domain='',\
               url='', city='', state='', country='', longitude=None, latitude=None,\
               professional=False, spam=False, lsp='', proxy='n', apikey='',\
               facebookid='', profile_url='', overwrite = False):
        if len(sl) > 0 and len(st) > 0 and len(tl) > 0 and len(tt) > 0:
            validquery = True
        else:
            validquery = False
        if validquery:
            #
            # look up scores for the submitter by username and IP address
            # if the user has a significant scoring history, we may mark
            # the submission as spam (e.g. > 10 scores, avgscore < 2.5)
            st = clean(st)
            tt = clean(tt)
            twords = string.split(tt)
            swords = string.split(st)
            if len(guid) < 1:
                m = md5.new()
                m.update(tt)
                m.update(str(datetime.datetime.now()))
                guid = str(m.hexdigest())
            n = md5.new()
            try:
                n.update(st.decode('utf-8'))
            except:
                n.update(st)
            md5hash = str(n.hexdigest())
            url = string.replace(url, 'http://','')
            url = string.replace(url, 'https://','')
            if overwrite:
                tdb = db.Query(Translation)
                tdb.filter('md5hash = ', md5hash)
                tdb.filter('tl = ', tl)
                item = tdb.get()
                if item is not None:
                    item.sl = sl
                    item.tl = tl
                    item.st = st
                    item.tt = tt
                    item.md5hash = md5hash
                    item.guid = guid
                    item.url = url
                    item.professional = professional
                    item.human = True
                    item.username = username
                    item.facebookid = facebookid
                    item.profile_url = profile_url
                    item.put()
                    return True
            tdb = Translation()
            tdb.md5hash = md5hash
            tdb.guid = guid
            tdb.sl = sl
            tdb.tl = tl
            tdb.st = st
            tdb.tt = tt
            #try:
            #    tdb.st = st.decode('utf-8')
            #except:
            #    try:
            #        tdb.st = clean(st)
            #    except:
            #        tdb.st = st
            #try:
            #    tdb.tt = tt.decode('utf-8')
            #except:
            #    try:
            #        tdb.tt = clean(tt)
            #    except:
            #        tdb.tt = tt
            tdb.domain = domain
            tdb.url = url
            tdb.username = username
            if len(username) > 0:
                tdb.anonymous = False
            tdb.remote_addr = remote_addr
            tdb.city = city
            tdb.state = state
            tdb.country = country
            tdb.professional = professional
            tdb.spam = spam
            tdb.facebookid = facebookid
            tdb.profile_url = profile_url
            if lsp == 'speaklike':
                tdb.professional = True
                tdb.reviewed = True
                tdb.spam = False
            if latitude is not None and longitude is not None:
                try:
                    tdb.latitude = latitude
                    tdb.longitude = longitude
                except:
                    try:
                        tdb.latitude = float(latitude)
                        tdb.longitude = float(longitude)
                    except:
                        pass
            try:
                tdb.twords = len(twords)
            except:
                tdb.twords = 0
            try:
                tdb.swords = len(swords)
            except:
                tdb.swords = 0
            # generate word list
            words = st + ' ' + tt
            words = string.replace(words, '.', '')
            words = string.replace(words, ',', '')
            words = string.replace(words, '!', '')
            words = string.replace(words, '?', '')
            words = string.replace(words, '\'', '')
            words = string.replace(words, '\"', '')
            ngrams = string.split(string.lower(words), ' ')
            try:
                tdb.ngrams = ngrams
            except:
                pass
            tdb.put()
            return guid
        else:
            return ''
    @staticmethod
    def updatescores(guid):
        pass
    @staticmethod
    def userscore(remote_addr, username, upvotes, downvotes, blockedvotes, rawscore, scores):
        pass
    @staticmethod
    def isnewtranslation(facebookid, url):
        if len(facebookid) > 6:
            url = string.replace(url, 'http://','')
            url = string.replace(url, 'https://','')
            tdb = db.Query(Translation)
            tdb.filter('facebookid = ', facebookid)
            tdb.filter('url = ', url)
            item = tdb.get()
            if item is None:
                return True
        return False
    @staticmethod
    def wordcount(username, tl='', startdate=None, enddate=None):
        if len(username) > 0:
            wc = memcache.get('wordcount|username=' + username + '|tl=' + tl)
            if wc is not None:
                return wc
            else:
                tdb = db.Query(Translation)
                tdb.filter('username = ', username)
                tdb.filter('tl = ', tl)
                results = tdb.fetch(limit=1000)
                total = 0
                for r in results:
                    if r.twords is not None:
                        if r.twords > 0:
                            total = total + r.twords
                memcache.set('wordcount|username=' + username + '|tl=' + tl, total, 900)
                return total
        else:
            return
    @staticmethod
    def translationcount(username, tl='', startdate=None, enddate=None):
        if len(username) > 0:
            tc = memcache.get('translationcount|username=' + username + '|tl=' + tl)
            if tc is not None:
                return tc
            else:
                tdb = db.Query(Translation)
                tdb.filter('username = ', username)
                tdb.filter('tl = ', tl)
                results = tdb.fetch(limit=1000)
                total = 0
                for r in results:
                    if r.twords is not None:
                        total = total + 1
                memcache.set('translationcount|username=' + username + '|tl=' + tl, total, 900)
                return total
        else:
            return
    @staticmethod
    def lucky(sl = '', tl = '', st = '', domain = '', url='', allow_anonymous='y', allow_machine ='y', min_score=0, userip='', hostname='', output='text', edit='y', lsp='', lspusername = '', lsppw='', professional=False, mtengine='', queue='', ip=''):
        text = ''
        response = ''
        st = clean(st)
        if sl == tl:
            return st
        m = md5.new()
        m.update(sl)
        m.update(tl)
        m.update(st)
        m.update(allow_anonymous)
        m.update(allow_machine)
        m.update(lsp)
        key = str(m.hexdigest())
        tt = memcache.get('/t/' + key)
        if tt is not None:
            return tt
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            # generate md5hash
            m = md5.new()
            m.update(st)
            md5hash = str(m.hexdigest())
            # add to WWL directory if hostname is provided
            if len(hostname) > 0:
                Directory.hostname(hostname, sl, tl, remote_addr=userip)
            # look for professional translation via old LSP API
            tdb = db.Query(Translation)
            tdb.filter('sl = ', sl)
            tdb.filter('tl = ', tl)
            tdb.filter('md5hash = ', md5hash)
            tdb.filter('professional = ', True)
            tt = ''
            item = tdb.get()
            if item is not None and len(clean(item.tt)) > 1:
                tt = clean(item.tt)
                memcache.set('/t/' + key, tt, 120)
                return tt
            else:
                if len(lsp) > 0 and lsp == 'speaklike':
                    response=Translation.lsp(sl, tl, st, domain=domain, url=url, lsp='speaklikeapi', lspusername=lspusername, lsppw=lsppw)
            # next look for user translations
            if len(tt) < 1:
                tdb = db.Query(Translation)
                tdb.filter('sl = ', sl)
                tdb.filter('tl = ', tl)
                tdb.filter('md5hash = ', md5hash)
                tdb.order('-date')
                item = tdb.get()
                if item is not None and len(clean(item.tt)) > 1:
                    tt = clean(item.tt)
                    memcache.set('/' + key, tt, 120)
                    return tt
            if len(tt) < 2 and allow_machine != 'n':
                mt = MTWrapper()
                tt = clean(mt.getTranslation(sl, tl, st, userip=userip))
            if len(tt) > 0:
                memcache.set('/t/' + key, tt)
                return tt
            else:
                return ''
    @staticmethod
    def fetch(sl='', tl='', st='', md5hash='', domain='', url='', userip='', allow_machine='y', allow_anonymous='', min_score=0, max_blocked_votes=0, fuzzy = 'n', mtengine='', lsp='', lspusername='', lsppw=''):
        if len(url) > 500:
            url = url[0:499]
        url = string.replace(url, 'http://', '')
        url = string.replace(url, 'https://','')
        if len(st) > 0 or len(md5hash) > 0:
            if len(st) > 0:
                m = md5.new()
                m.update(clean(st))
                md5hash = str(m.hexdigest())
            results = memcache.get('translations|fetch|sl=' + sl + '|tl=' + tl + '|md5hash=' + md5hash)
        else:
            results = memcache.get('translations|fetch|sl=' + sl + '|tl=' + tl + '|domain=' + domain + '|url=' + url)
        tt = ''
        if results is not None:
            return results
        if results is None and len(tt) < 1:
            sortdate = True
            tdb = db.Query(Translation)
            if len(sl) > 0:
                tdb.filter('sl = ', sl)
            if len(tl) > 0:
                tdb.filter('tl = ', tl)
            if fuzzy == 'y':
                pass
            if len(st) > 0 or len(md5hash) > 0:
                tdb.filter('md5hash = ', md5hash)
            else:
                if len(url) > 0:
                    tdb.filter('url = ', url)
            if sortdate:
                tdb.order('-date')
            results = tdb.fetch(limit=500)
        filtered_results = list()
        professional_translation_found = False
        for r in results:
            skiprecord = False
            if allow_anonymous == 'n' and r.anonymous:
                skiprecord=True
            if allow_anonymous == 'n' and r.username == '':
                skiprecord=True
            if min_score > 0 and r.avgscore < min_score:
                skiprecord=True
            try:
                if r.spam:
                    skiprecord=True
            except:
                pass
            if max_blocked_votes > 0 and r.blockedvotes > max_blocked_votes:
                skiprecord=True
            if r.professional:
                professional_translation_found = True
            if not skiprecord:
                t = tx()
                t.sl = r.sl
                t.tl = r.tl
                t.st = codecs.encode(r.st, 'utf-8')
                t.tt = codecs.encode(r.tt, 'utf-8')
                t.domain = r.domain
                t.url = r.url
                if string.count(r.username, 'proz') > 0:
                    t.avgscore = 5
                else:
                    t.avgscore = r.avgscore
                t.upvotes = r.upvotes
                t.downvotes = r.downvotes
                t.blockedvotes = r.blockedvotes
                t.scores = r.scores
                t.rawscore = r.rawscore
                t.date = r.date
                if len(r.username) < 3:
                    t.username = r.remote_addr + ' (' + r.city + ')'
                else:
                    t.username = r.username
                t.remote_addr = r.remote_addr
                t.guid = r.guid
                t.md5hash = r.md5hash
                filtered_results.append(t)
        if results is not None:
            if len(st) > 0:
                memcache.set('translations|fetch|sl=' + sl + '|tl=' + tl + '|md5hash=' + md5hash, results, 120)
            else:
                memcache.set('translations|fetch|sl=' + sl + '|tl=' + tl + '|domain=' + domain + '|url=' + url, results, 120)
        return filtered_results
    @staticmethod
    def getbyurl(url, tl):
        if len(url) > 0:
            url = string.replace(url, 'http://','')
            url = string.replace(url, 'https://','')
            tdb = db.Query(Translation)
            tdb.filter('url = ', url)
            if len(tl) > 0:
                tdb.filter('tl = ', tl)
            tdb.order('-date')
            results = tdb.fetch(500)
            if results is not None:
                return results
    @staticmethod
    def purgespam():
        threshold = Settings.get('min_spam_votes')
        if len(threshold) > 0:
            min_spam_votes = int(threshold)
        else:
            min_spam_votes = 1
        tdb = db.Query(Translation)
        tdb.filter('spam = ', False)
        tdb.filter('blockedvotes >= ', min_spam_votes)
        results = tdb.fetch(limit=10)
        if len(results) > 0:
            for r in results:
                r.spam = True
                r.put()
            return len(results)
        else:
            return 0
    @staticmethod
    def purgebadtranslations():
        tdb = db.Query(Translation)
        tdb.order('-date')
        results = tdb.fetch(limit = 500)
        flagged = 0
        for r in results:
            if not r.spam:
                if r.scores >= 3:
                    if r.avgscore < 2.5:
                        r.spam = True
                        r.put()
                        flagged = flagged + 1
        return flagged
    
class Users(db.Model):
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    anonymous = db.BooleanProperty(default=False)
    email = db.StringProperty(default='')
    pwhash = db.StringProperty(default='')
    session = db.StringProperty(default='')
    firstname = db.StringProperty(default='')
    lastname = db.StringProperty(default='')
    city = db.StringProperty(default='')
    state = db.StringProperty(default='')
    country = db.StringProperty(default='')
    latitude = db.StringProperty(default='')
    longitude = db.StringProperty(default='')
    title = db.StringProperty(default = '', multiline = True)
    description = db.TextProperty(default = '')
    skype = db.StringProperty(default = '')
    www = db.StringProperty(default = '')
    proz = db.StringProperty(default = '')
    linkedin = db.StringProperty(default = '')
    facebook = db.StringProperty(default = '')
    tags = db.ListProperty(str)
    geohash = db.StringProperty(default='')
    validated = db.BooleanProperty(default=False)
    validationkey = db.StringProperty(default='')
    blocked = db.BooleanProperty(default=False)
    languages = db.ListProperty(str)
    root = db.BooleanProperty(default=False)
    websites = db.ListProperty(str)
    admin = db.ListProperty(str)
    author = db.ListProperty(str)
    translator = db.ListProperty(str)
    trustedtranslator = db.ListProperty(str)
    avgscore = db.FloatProperty()
    rawscore = db.IntegerProperty(default=0)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    blockedvotes = db.IntegerProperty(default=0)
    scores = db.IntegerProperty(default=0)
    rawscores = db.ListProperty(int)
    stdev = db.FloatProperty()
    translations = db.IntegerProperty(default=0)
    twords = db.IntegerProperty(default=0)
    lasttranslation = db.DateTimeProperty(auto_now_add = True)
    created = db.DateTimeProperty(auto_now_add = True)
    lastlogin = db.DateTimeProperty(auto_now_add = True)
    lastloginyear = db.IntegerProperty()
    lastloginmonth = db.IntegerProperty()
    lastloginday = db.IntegerProperty()
    lastloginhour = db.IntegerProperty()
    @staticmethod
    def profile(username):
        if len(username) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                profile = dict()
                profile['username']=item.username
                profile['email']=item.email
                profile['firstname']=item.firstname
                profile['city']=item.city
                profile['state']=item.state
                profile['country']=item.country
                profile['latitude']=item.latitude
                profile['longitude']=item.longitude
                profile['languages']=item.languages
                profile['websites']=item.websites
                profile['avgscore']=item.avgscore
                profile['rawscore']=item.rawscore
                profile['upvotes']=item.upvotes
                profile['downvotes']=item.downvotes
                profile['blockedvotes']=item.blockedvotes
                return profile
    @staticmethod
    def addroot(username, pw):
        if len(username) > 0 and len(pw) > 0:
            m = md5.new()
            m.update(pw)
            pwhash = str(m.hexdigest())
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is None:
                item = Users()
            item.username = username
            item.pwhash = pwhash
            item.root = True
            item.put()
        else:
            return False
    @staticmethod
    def available(username):
        udb = db.Query(Users)
        udb.filter('username = ', username)
        item = udb.get()
        if item is None:
            return True
        else:
            return False
    @staticmethod
    def pw(username,pw):
        udb = db.Query(Users)
        udb.filter('username = ', username)
        item = udb.get()
        if item is not None:
            m = md5.new()
            m.update(pw)
            pwhash = str(m.hexdigest())
            if pwhash == item.pwhash:
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def auth(username, pw, session, remote_addr, city = '', state = '', country = '', latitude = None, longitude = None):
        if len(session) > 0:
            sessioninfo = memcache.get('sessions|' + session)
        else:
            sessioninfo = None
        if sessioninfo is not None:
            return sessioninfo
        elif sessioninfo is None and len(session) > 2:
            return
        else:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is None:
                return
            else:
                pwhash = item.pwhash
                m = md5.new()
                m.update(pw)
                pwhash2 = str(m.hexdigest())
                if pwhash == pwhash2:
                    m = md5.new()
                    m.update(str(datetime.datetime.now()))
                    m.update(username)
                    item.session = session 
                    if len(city) > 0:
                        item.city = city
                    if len(state) > 0:
                        item.state = state
                    if len(country) > 0:
                        item.country = country
                    if latitude is not None:
                        try:
                            item.latitude = str(latitude)
                        except:
                            pass
                    if longitude is not None:
                        try:
                            item.longitude = str(longitude)
                        except:
                            pass
                    now = datetime.datetime.now()
                    year = now.year
                    month = now.month
                    day = now.day
                    hour = now.hour
                    item.lastlogin = now
                    item.lastloginyear = year
                    item.lastloginmonth = month
                    item.lastloginday = day
                    item.lastloginhour = hour
                    item.put()
                    sessioninfo=dict()
                    sessioninfo['username']=username
                    sessioninfo['session']=session
                    memcache.set('sessions|' + session, sessioninfo, 900)
                    loggedin=memcache.get('login|' + username)
                    return sessioninfo
                else:
                    return
    @staticmethod
    def logout(username='', session=''):
        udb = db.Query(Users)
        if len(username) > 0:
            udb.filter('username = ', username)
        elif len(session) > 0:
            udb.filter('session = ', session)
        else:
            return False
        item = udb.get()
        if item is not None:
            item.session = ''
            item.put()
            if len(session) > 0:
                memcache.delete('sessions|' + session)
            return True
        else:
            return False
    @staticmethod
    def block(username, unblock=False):
        if len(username) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item.get()
            if item is not None:
                if unblock:
                    item.blocked = False
                else:
                    item.blocked = True
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def new(username, email, pw, remote_addr, firstname='', lastname = '', skype = '', facebook = '', linkedin = '', description = '', www = '', city = '', state = '', country = '', latitude = None, longitude = None):
        if len(username) > 0 and string.count(email, '@') > 0 and string.count(email, '.') > 0 and len(pw) > 5:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                return False
            else:
                # create user account
                m = md5.new()
                m.update(pw)
                pwhash = str(m.hexdigest())
                m = md5.new()
                m.update(username)
                m.update(pw)
                m.update(str(datetime.datetime.now()))
                validationkey = str(m.hexdigest())
                item = Users()
                try:
                    item.username = username.decode('utf-8')
                except:
                    try:
                        item.username = clean(username)
                    except:
                        item.username = username
                item.email = email
                item.pwhash = pwhash
                item.validationkey = validationkey
                item.firstname = firstname
                item.lastname = lastname
                item.skype = skype
                item.facebook = facebook
                item.linkedin = linkedin
                item.description = description
                item.www = www
                item.city = city
                item.state = state
                item.country = country
                if latitude is not None and longitude is not None:
                    try:
                        item.latitude = str(latitude)
                        item.longitude = str(longitude)
                    except:
                        pass
                item.put()
                # send validation email
                confirmation_url = 'http://worldwidelexicon.appspot.com/users/validate?key=' + validationkey
                sender_address = "Brian McConnell <bsmcconnell@gmail.com>"
                subject = "Welcome to the Worldwide Lexicon Translation Community"
                body = """
                Thank you for creating an account!  Please confirm your email address by
                clicking on the link below:

                %s
                """ % confirmation_url
                mail.send_mail(sender_address, email, subject, body)
                return True
        else:
            return False
    @staticmethod
    def permission(username, website, role):
        if len(username) > 0 and len(website) > 0 and len(role) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is None:
                return False
            else:
                if role == 'author' and website in item.author:
                    return True
                else:
                    return False
                if role == 'translator' and website in item.translator:
                    return True
                else:
                    return False
                if role == 'trustedtranslator' and website in item.trustedtranslator:
                    return True
                else:
                    return False
                if role == 'admin' and website in item.admin:
                    return True
                else:
                    return False
                return False
        else:
            return False
    @staticmethod
    def remove(username):
        if len(username) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                item.delete()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def save(username, parms):
        if len(username) > 0 and type(parms) is dict:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                pkeys = parms.keys()
                for p in pkeys:
                    if p == 'pw':
                        m = md5.new()
                        m.update(parms['pw'])
                        pwhash = str(m.hexdigest())
                        setattr(item, p, pwhash)
                    else:
                        setattr(item, p, parms[p])
                item.put()
                return True
            else:
                return False
    @staticmethod
    def savescore(remote_addr, username, votetype, score = ''):
        if len(votetype) > 0 and len(remote_addr) > 0:
            udb = db.Query(Users)
            if len(username) > 0:
                udb.filter('username = ', username)
            else:
                udb.filter('remote_addr = ', remote_addr)
            item = udb.get()
            if item is None:
                if len(username) < 1 and len(remote_addr) > 0:
                    item = Users()
                    item.remote_addr = remote_addr
                    item.scores = 0
                else:
                    return False
            else:
                upvotes = item.upvotes
                downvotes = item.downvotes
                blockedvotes = item.blockedvotes
                scores = item.scores
                rawscore = item.rawscore
                if votetype == 'up':
                    rawscore = rawscore + 5
                    scores = scores + 1
                elif votetype == 'down':
                    rawscore = rawscore + 2
                    scores = scores + 1
                elif votetype == 'block':
                    blockedvotes = blockedvotes + 1
                    scores = scores + 1
                elif len(score) > 0:
                    if int(score) >= 0 and int(score) <= 5:
                        rawscore = rawscore + int(score)
                        scores = scores + 1
                        if int(score) == 0:
                            blockedvotes = blockedvotes + 1
                if scores > 0:
                    avgscore = float(rawscore/scores)
                else:
                    avgscore = float(0)
                item.blockedvotes = blockedvotes
                item.scores = scores
                item.avgscore = avgscore
                item.put()
                Translation.userscore(username, upvotes, downvotes, blockedvotes, rawscore, scores)
                return True
        else:
            return False
    @staticmethod
    def setparm(username, pw, parm, value):
        if len(username) > 0 and len(pw) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is None:
                return False
            else:
                m = md5.new()
                m.update(pw)
                pwhash = str(m.hexdigest())
                if pwhash == item.pwhash:
                    try:
                        setattr(item, parm, value)
                        item.put()
                        return True
                    except:
                        return False
                else:
                    return False
        else:
            return False
    @staticmethod
    def getparm(username, parm):
        udb = db.Query(Users)
        udb.filter('username = ', username)
        item = udb.get()
        if item is not None:
            if parm == 'pwhash' or parm == 'validationkey':
                return ''
            else:
                try:
                    value = getattr(item, parm)
                    return value
                except:
                    return ''
        else:
            return ''
    @staticmethod
    def set(username, website, role, allow, language='all'):
        if len(username) > 0 and len(website) > 0 and len(role) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if role == 'author':
                sites = item.author
            elif role == 'translator':
                sites = item.translator
            elif role == 'trustedtranslator':
                sites = item.trustedtranslator
            elif role == 'admin':
                sites = item.admin
            else:
                return False
            w = website + '_' + language
            if allow:
                if website not in sites:
                    sites.append(w)
            else:
                if website in sites:
                    sites.remove(w)
            if role == 'author':
                item.author = sites
            elif role == 'translator':
                item.translator = sites
            elif role == 'trustedtranslator':
                item.trustedtranslator = sites
            elif role == 'admin':
                item.admin = sites
            else:
                pass
            return True
        else:
            return False
    @staticmethod
    def translate(username, twords, city = None, state = None, country=None, latitude=None, longitude=None):
        udb = db.Query(Users)
        udb.filter('username = ', username)
        item = udb.get()
        if item is not None:
            translations = item.translations
            if translations is not None:
                item.translations = translations + 1
            else:
                item.translations = 1
            words = item.twords
            if words is not None:
                item.twords = words + twords
            else:
                item.twords = twords
            if city is not None:
                item.city = city
            if state is not None:
                item.state = state
            if country is not None:
                item.country = country
            if latitude is not None:
                item.latitude = str(latitude)
            if longitude is not None:
                item.longitude = str(longitude)
            item.lasttranslation = datetime.datetime.now()
            item.put()
    @staticmethod
    def validate(key):
        if len(key) > 8:
            udb = db.Query(Users)
            udb.filter('validationkey = ', key)
            item = udb.get()
            if item is not None:
                item.validated = True
                item.put()
                return True
            else:
                return False
        else:
            return False

class UserScores(db.Model):
    guid = db.StringProperty(default='')
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    anonymous = db.BooleanProperty(default=True)
    city = db.StringProperty(default='')
    state = db.StringProperty(default='')
    country = db.StringProperty(default='')
    scores = db.IntegerProperty(default=0)
    avgscore = db.FloatProperty()
    rawscore = db.IntegerProperty(default=0)
    rawdata = db.ListProperty(int)
    stdev = db.FloatProperty()
    lspavgscore = db.FloatProperty()
    lspscores = db.IntegerProperty(default=0)
    lsprawscore = db.IntegerProperty(default=0)
    lsprawdata = db.ListProperty(int)
    lspstdev = db.FloatProperty()
    translations = db.IntegerProperty(default=0)
    translator = db.BooleanProperty(default=False)
    languages = db.ListProperty(str)
    domains = db.ListProperty(str)
    blockedvotes = db.IntegerProperty(default=0)
    createdon = db.DateTimeProperty(auto_now_add=True)
    updatedon = db.DateTimeProperty()
    @staticmethod
    def getscore(username='', remote_addr=''):
        udb = db.Query(UserScores)
        if len(username) > 0:
            udb.filter('username = ', username)
        else:
            udb.filter('remote_addr = ', remote_addr)
        item = udb.get()
        if item is not None:
            result = dict()
            result['guid']=item.guid
            result['translations']=item.translations
            result['scores']=item.scores
            result['rawscore']=item.rawscore
            result['avgscore']=item.avgscore
            result['stdev']=item.stdev
            result['rawdata']=item.rawdata
            result['languages']=item.languages
            result['domains']=item.domains
            result['createdon']=item.createdon
            result['updatedon']=item.updatedon
            return result
        else:
            return
    @staticmethod
    def peerreview(min_scores=20, sl='', tl='', domain='', limit=25):
        udb = db.Query(UserScores)
        udb.filter('translator = ', True)
        if min_scores > 0:
            udb.filter('scores <= ', min_scores)
        else:
            udb.filter('scores <= ', min_scores)
        if len(domain) > 0:
            udb.filter('domain = ', domain)
        if len(sl) > 0:
            udb.filter('languages = ', sl)
        if len(tl) > 0:
            udb.filter('languages = ', tl)
        udb.order('scores')
        results = udb.fetch(limit=limit)
        return results
    @staticmethod
    def score(username='', remote_addr='', sl='', tl='', score=None, domain='', lsp=False):
        if len(username) > 0 and string.count(username,'.') < 2:
            UserScores.save(username=username, remote_addr=remote_addr, sl=sl, tl=tl, score=score, domain=domain, lsp=lsp)
        if len(remote_addr) > 0:
            UserScores.save(username='', remote_addr=remote_addr, sl=sl, tl=tl, score=score, domain=domain, lsp=lsp)
    @staticmethod
    def save(username='', remote_addr='', sl='', tl = '', score=None, domain='', lsp=False):
        if len(username) > 0 or len(remote_addr) > 0 and score is not None:
            try:
                score = int(score)
            except:
                return False
            udb = db.Query(UserScores)
            if len(username) > 0:
                udb.filter('username = ', username)
            else:
                username = ''
                udb.filter('remote_addr = ', remote_addr)
            item = udb.get()
            if item is None:
                m = md5.new()
                m.update(remote_addr)
                m.update(str(datetime.datetime.now()))
                md5hash = str(m.hexdigest())
                item = UserScores()
                item.guid = md5hash
                item.username = username
                item.remote_addr = remote_addr
                if len(username) > 0:
                    item.anonymous = False
            languages = item.languages
            if len(sl) > 1 and len(sl) < 4 and sl not in languages:
                languages.append(sl)
            if len(tl) > 1 and len(tl) < 4 and tl not in languages:
                languages.append(tl)
            item.languages = languages
            item.translations = item.translations + 1
            item.translator = True
            scores = item.scores + 1
            item.scores = scores
            rawscore = item.rawscore + score
            item.rawscore = rawscore
            rawdata = item.rawdata
            rawdata.append(score)
            item.rawdata = rawdata
            avgscore = float(float(rawscore)/scores)
            item.avgscore = avgscore
            squares = 0
            for r in rawdata:
                squares = squares + pow(float(score) - avgscore, 2)
            stdev = pow(squares/float(scores),0.5)
            blockedvotes = item.blockedvotes
            if score < 1:
                if type(blockedvotes) is int:
                    item.blockedvotes = blockedvotes + 1
                else:
                    item.blockedvotes = 1
            item.stdev = stdev
            if lsp:
                lsprawscore = item.lsprawscore + score
                lspscores = item.lspscores + 1
                lsprawdata = item.lsprawdata
                lsprawdata.append(score)
                item.lsprawscore = lsprawscore
                item.lspscours = lspscores
                item.lspavgscore = float(float(lsprawscore)/scores)
                squares = o
                for r in lsprawdata:
                    squares = squares + pow(float(score) - avgscore, 2)
                stdev = pow(squares/float(scores),0.5)
                item.lspstdev = stdev                
            domains = item.domains
            if len(domain) > 0:
                if domain not in domains:
                    domains.append(domain)
                    item.domains = domains
            item.updatedon = datetime.datetime.now()
            item.put()
            return True
        else:
            return False
    @staticmethod
    def translate(username='', remote_addr='', sl='', tl='', domain=''):
        if len(username) > 0 or len(remote_addr) > 0:
            udb = db.Query(UserScores)
            if len(username) > 0 and string.count(username,'.') < 2:
                udb.filter('username = ', username)
            else:
                username = ''
                udb.filter('remote_addr = ', remote_addr)
            item = udb.get()
            if item is None:
                m = md5.new()
                m.update(remote_addr)
                m.update(str(datetime.datetime.now()))
                md5hash = str(m.hexdigest())                
                item = UserScores()
                item.guid = md5hash
                item.username = username
                item.remote_addr = remote_addr
                if len(username) > 0:
                    item.anonymous = False
            languages = item.languages
            if len(sl) > 1 and len(sl) < 4 and sl not in languages:
                languages.append(sl)
            if len(tl) > 1 and len(tl) < 4 and tl not in languages:
                languages.append(tl)
            item.languages = languages
            item.translations = item.translations + 1
            item.translator = True
            domains = item.domains
            if len(domain) > 0:
                if domain not in domains:
                    domains.append(domain)
                    item.domains = domains
            item.updatedon = datetime.datetime.now()
            item.put()
            return True
        else:
            return False

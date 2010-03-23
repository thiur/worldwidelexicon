# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Database Interface
Content Management System / Web Server (database.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module defines persistent datastores and the functions used to fetch and
submit data to them.

Copyright (c) 1998-2009, Worldwide Lexicon Inc, Brian S McConnell. 
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
from config import Config
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
    """
    This function is used to check character encodings and to encode
    texts in the UTF-8 encoding. It will convert from ASCII and ISO-Latin-1
    if the incoming text is not UTF-8. Support for detection and conversion
    of other encodings will be added in the future.
    """
    try:
        utext = text.encode('utf-8')
    except:
        try:
            utext = text.encode('iso-8859-1')
        except:
            try:
                utext = text.encode('ascii')
            except:
                utext = ''
    text = utext.decode('utf-8')
    return text

def smart_unicode(s, encoding='utf-8', errors='strict'):
    """
    This is a convenience function that verifies UTF-8 encoding for a text
    """
    if type(s) in (unicode, int, long, float, types.NoneType):
        return unicode(s)
    elif type(s) is str or hasattr(s, '__unicode__'):
        return unicode(s, encoding, errors)
    else:
        return unicode(str(s), encoding, errors)
        
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

class CSS(db.Model):
    """
    CSS()
    
    This datastore is used to store CSS stylesheets, which are accessed via
    the /css path on the WWL server. This is not currently used much in the
    system. 
    """
    name = db.StringProperty(default='')
    language = db.StringProperty(default='')
    description = db.TextProperty(default='')
    text = db.TextProperty(default='')
    owner = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def get(path, language=''):
        t = memcache.get('css|name=' + path + '|language=' + language)
        if t is not None:
            return t
        else:
            cdb = db.Query(CSS)
            cdb.filter('name = ', path)
            cdb.filter('language = ', language)
            item = cdb.get()
            if item is not None:
                t = codecs.encode(item.text, encoding)
                memcache.set('css|name=' + path + '|language=' + language, t, 300)
                return t
            else:
                return ''
    @staticmethod
    def edit(path, language=''):
        cdb = db.Query(CSS)
        cdb.filter('name = ', path)
        cdb.filter('language = ', language)
        item = cdb.get()
        if item is not None:
            object = dict()
            object['title'] = item.title
            object['description'] = codecs.encode(item.description, encoding)
            object['text'] = codecs.encode(item.text, encoding)
            object['owner'] = item.owner
            object['language'] = item.language
            return object
        else:
            return None
    @staticmethod
    def save(path, language='', object=None):
        cdb = db.Query(CSS)
        cdb.filter('name = ', path)
        cdb.filter('language = ', language)
        item= cdb.get()
        if item is None:
            item = CSS()
            item.name = path
            item.language = language
        if type(object) is dict:
            item.title = object.get('title', '')
            item.description = object.get('description','')
            item.text = object.get('text','')
            item.owner = object.get('owner','')
            item.edited = datetime.datetime.now()
            item.put()
            memcache.set('css|name=' + path + '|language=' + language, object.get('text',''), 300)
            return True
        else:
            return False
        
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
        
class Feeds(db.Model):
    website = db.StringProperty(default='')
    rssurl = db.StringProperty(default='')
    title = db.StringProperty(default='', multiline=True)
    description = db.TextProperty(default='')
    language = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    indexed = db.DateTimeProperty()
    autopublish = db.BooleanProperty(default=False)
    @staticmethod
    def add(website, rssurl, title='', description='', language='', autopublish=False):
        fdb = db.Query(Feeds)
        fdb.filter('website = ', website)
        fdb.filter('rssurl = ', rssurl)
        item = fdb.get()
        if item is None:
            item = Feeds()
            item.website = website
            item.rssurl = rssurl
            item.title = title
            item.description = description
            item.language = language
            item.autopublish = autopublish
            item.put()
        return True
    @staticmethod
    def delete(website, rssurl):
        if len(website) > 0 and len(rssurl) > 0:
            fdb = db.Query(Feeds)
            fdb.filter('website = ', website)
            fdb.filter('rssurl = ', rssurl)
            item = fdb.get()
            if item is not None:
                item.delete()
            return True
        else:
            return False
    @staticmethod
    def list(website=''):
        fdb = db.Query(Feeds)
        if len(website) > 0:
            fdb.filter('website = ', website)
        results = fdb.fetch(limit = 500)
        return results
    
class Groups(db.Model):
    """
    This data store is used to store information about affinity groups, their
    members, and basic statistics for a group (number of comments, number of
    articles recommended, etc)
    """
    name = db.StringProperty(default = '', multiline = True)
    title = db.StringProperty(default = '', multiline = True)
    description = db.TextProperty(default = '')
    created = db.DateTimeProperty(auto_now_add = True)
    lastpost = db.DateTimeProperty()
    members = db.ListProperty(str)
    editors = db.ListProperty(str)
    owner = db.StringProperty(default = '')
    posts = db.IntegerProperty(default = 0)
    articles = db.IntegerProperty(default = 0)
    language = db.StringProperty(default='')
    tags = db.ListProperty(str)
    @staticmethod
    def add(name, members=None, editors=None):
        """
        Add members or editors to an affinity group, can add members or editors
        one at a time (string) or in bulk (list)
        """
        if len(name) > 0 and (members is not None or editors is not None):
            gdb = db.Query(Groups)
            gdb.filter('name = ', name)
            item = gdb.get()
            if item is not None:
                if members is not None:
                    if type(members) is str:
                        gmembers = item.members
                        if members not in gmembers:
                            gmembers.append(members)
                            item.members = gmembers
                    elif type(members) is list:
                        gmembers = item.members
                        for m in members:
                            if m not in gmembers:
                                gmembers.append(m)
                        item.members = gmembers
                    else:
                        pass
                if editors is not None:
                    if type(editors) is str:
                        geditors = item.editors
                        if editors not in geditors:
                            geditors.append(editors)
                            item.editors = geditors
                    elif type(editors) is list:
                        geditors = item.editors
                        for m in editors:
                            if m not in geditors:
                                geditors.append(m)
                        item.editors = geditors
                    else:
                        pass
                item.put()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def new(name, title='', description='', owner='', language=''):
        if len(name) > 0 and len(title) > 0:
            gdb = db.Query(Groups)
            gdb.filter('name = ', name)
            item = gdb.get()
            titlewords = string.split(string.lower(title), ' ')
            dwords = string.split(string.lower(description), ' ')
            tags = list()
            if len(titlewords) > 0:
                for t in titlewords:
                    tags.append(t)
            if len(dwords) > 0:
                for t in dwords:
                    tags.append(t)
            if item is None:
                item = Groups()
                item.name = name
                item.title = title
                item.description = description
                item.owner = owner
                item.language = language
                item.tags = tags
                item.put()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def remove(name, members = None, editors = None):
        if len(name) > 0 and (members is not None or editors is not None):
            gdb = db.Query(Groups)
            gdb.filter('name = ', name)
            item = gdb.get()
            if item is not None:
                gmembers = item.members
                geditors = item.editors
                if members is not None:
                    if type(members) is str:
                        if members in gmembers:
                            gmembers.remove(members)
                    elif type(members) is list:
                        for m in members:
                            if m in gmembers:
                                gmembers.remove(m)
                    else:
                        pass
                    item.members = gmembers
                if editors is not None:
                    if type(editors) is str:
                        if editors in geditors:
                            geditors.remove(editors)
                    elif type(editors) is list:
                        for m in editors:
                            if m in geditors:
                                geditors.remove(m)
                    else:
                        pass
                    item.editors = geditors
                item.put()
                return True
            else:
                return False
        else:
            return False
        
class Images(db.Model):
    website = db.StringProperty(default='')
    name = db.StringProperty(default='', multiline=True)
    title = db.StringProperty(default='', multiline=True)
    image = db.BlobProperty()
    avatar = db.BlobProperty()
    tags = db.ListProperty(str)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now_add=True)
    @staticmethod
    def save(website, name, title, image):
        if len(website) > 0 and len(name) > 0 and len(title) > 0:
            idb = db.Query(Images)
            idb.filter('website = ', website)
            idb.filter('name = ', name)
            item = idb.get()
            if item is None:
                item = Images()
                item.website = website
                item.name = name
            item.title = title
            try:
                item.image = db.Blob(image)
            except:
                return False
            try:
                avatar = images.resize(image, 64, 64)
                item.avatar = avatar
            except:
                pass
            item.modified = datetime.datetime.now()
            item.put()
            return True
        else:
            return True
    @staticmethod
    def gallery(website, name=''):
        g=list()
        if len(website) > 0:
            idb = db.Query(Images)
            idb.filter('website = ', website)
            if len(name) > 0:
                idb.filter('name = ', name)
            results = idb.fetch(limit=200)
            for r in results:
                g.append(r.website + '/' + r.name)
            return g
        else:
            return g
    
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
        langs = memcache.get('languages|local|english=' + english)
        if len(languages) < 1 and langs is not None:
            return langs
        else:
            ln=dict()
            ln['en']=u'English'
            ln['es']=u'Spanish'
            ln['af']=u'Afrikaans'
            ln['ar']=u'Arabic'
            ln['bg']=u'Bulgarian'
            ln['da']=u'Danish'
            ln['de']=u'German'
            ln['fr']=u'French'
            ln['he']=u'Hebrew'
            ln['id']=u'Indonesian'
            ln['it']=u'Italian'
            ln['ja']=u'Japanese'
            ln['ko']=u'Korean'
            ln['ru']=u'Russian'
            ln['th']=u'Thai'
            ln['tl']=u'Tagalog'
            ln['zh']=u'Chinese'
            ln['ca']=u'Catalan'
            ln['cs']=u'Czech'
            ln['cy']=u'Welsh'
            ln['el']=u'Greek'
            ln['et']=u'Estonian'
            ln['eu']=u'Basque'
            ln['fa']=u'Farsi'
            ln['fi']=u'Finnish'
            ln['ga']=u'Gaelic'
            ln['gl']=u'Galician'
            ln['gu']=u'ગુજરાતી'
            ln['hi']=u'Hindi'
            ln['hr']=u'Croatian'
            ln['ht']=u'Haitian Creole'
            ln['hu']=u'Hungarian'
            ln['is']=u'Icelandic'
            ln['iu']=u'ᐃᓄᒃᑎᑐᑦ'
            ln['jv']=u'Basa Jawa'
            ln['ku']=u'كوردی'
            ln['la']=u'Latin'
            ln['lt']=u'Lithuanian'
            ln['lv']=u'Latvian'
            ln['mn']=u'Mongolian'
            ln['ms']=u'بهاس ملايو‎'
            ln['my']=u'Burmese'
            ln['ne']=u'Nepalese'
            ln['nl']=u'Dutch'
            ln['no']=u'Norwegian (Bokmal)'
            ln['nn']=u'Norwegian (Norsk)'
            ln['oc']=u'Occitan'
            ln['pa']=u'ਪੰਜਾਬੀ '
            ln['po']=u'Polish'
            ln['ps']=u'پښتو'
            ln['pt']=u'Portuguese'
            ln['ro']=u'Romanian'
            ln['sk']=u'Slovak'
            ln['sr']=u'српски језик'
            ln['sv']=u'Swedish'
            ln['sw']=u'Swahili'
            ln['tr']=u'Turkish'
            ln['uk']=u'Ukranian'
            ln['vi']=u'Vietnamese'
            ln['yi']=u'Yiddish'
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
            if type(languages) is list:
                if len(languages) < 1:
                    memcache.set('languages|local|english=' + english, l, 72000)
                    return l
                langs = dict()
                for k in languages:
                    lang = l.get(k)
                    if len(lang) > 0:
                        langs[k]=l[k]
                return langs
            elif len(languages) > 0:
                langname = l.get(languages, '')
                return langname
            else:
                if english == 'y':
                    return ln
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
    
class Objects(db.Model):
    website = db.StringProperty(default='', multiline=True)
    name = db.StringProperty(default='', multiline=True)
    title = db.StringProperty(default='', multiline=True)
    sl = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add=True)
    published = db.BooleanProperty(default=True)
    featured = db.BooleanProperty(default=False)
    news = db.BooleanProperty(default=False)
    author = db.StringProperty(default='')
    content = db.TextProperty(default='')
    description = db.TextProperty(default='')
    tags = db.ListProperty(str)
    divid = db.StringProperty(default='')
    divclass = db.StringProperty(default='')
    fromrss = db.BooleanProperty(default=False)
    link = db.StringProperty(default='')
    blog = db.BooleanProperty(default=True)
    page = db.BooleanProperty(default=False)
    guid = db.StringProperty(default='')
    rssurl = db.StringProperty(default='', multiline=True)
    @staticmethod
    def get(website, name, language=''):
        object = memcache.get('objects|website=' + website + '|name=' + name)
        if object is not None:
            return object
        else:
            odb = db.Query(Objects)
            odb.filter('name = ', name)
            odb.filter('website = ', website)
            item = odb.get()
            if item is None:
                odb = db.Query(Objects)
                odb.filter('guid = ', name)
                odb.filter('website = ', website)
                item = odb.get()
            if item is not None:
                object = dict()
                object['name'] = item.name
                object['title'] = item.title
                object['sl'] = item.sl
                object['created'] = item.created
                object['author'] = item.author
                object['tags'] = item.tags
                object['content']=item.content
                object['divid'] = item.divid
                object['divclass'] = item.divclass
                object['blog'] = item.blog
                object['page'] = item.page
                memcache.set('objects|website=' + website + '|name=' + name, object, 300)
                return object
            else:
                return
    @staticmethod
    def purge(website, rssurl):
        if len(website) > 0 and len(rssurl) > 0:
            odb = db.Query(Objects)
            odb.filter('website = ', website)
            odb.filter('rssurl = ', rssurl)
            results = odb.fetch(limit=500)
            if results is not None:
                db.delete(results)
            return True
        else:
            return False
    @staticmethod
    def query(website, order='-created', offset=0, published=True, blog=None, featured=None, tag='', language='', news=None, verbose=True, limit=20, q =''):
        if len(website) > 0:
            odb = db.Query(Objects)
            odb.filter('website = ', website)
            if len(q) > 0:
                odb.filter('tags = ', q)
            odb.order(order)
            results = odb.fetch(limit=100, offset=offset)
            ctr = 0
            if results is not None:
                t = ''
                for r in results:
                    skiprecord = False
                    if published and not r.published:
                        skiprecord = True
                    if blog is not None:
                        if r.blog != blog:
                            skiprecord = True
                    if featured is not None:
                        if r.featured != featured:
                            skiprecord = True
                    if news is not None:
                        if r.news != news:
                            skiprecord = True
                    if not skiprecord:
                        ctr = ctr + 1
                        if ctr < limit+1:
                            content = codecs.encode(r.content, 'utf-8')
                            if len(r.name) < 1:
                                name = r.guid
                            else:
                                name = r.name
                            t = t + '<h3><a wwlapi="tr" href=/' + r.website + '/' + name + '>' + r.title + '</a></h3>'
                            if verbose:
                                content = string.replace(content, '<div>', '')
                                content = string.replace(content, '</div>', '')
                                content = string.replace(content, '</p>', '<p>')
                                content = string.replace(content, '<br>', '<p>')
                                texts = string.split(content, '<p>')
                                if len(texts) > 0:
                                    try:
                                        content = string.replace(content[0:400], '<p>', '')
                                        content = string.replace(content, '<div>', '')
                                        content = string.replace(content, '</div>', '')
                                        if len(texts[0]) > 0:
                                            t = t + '<div wwlapi="tr">' + texts[0] + '</div>'
                                    except:
                                        pass
                return t
            else:
                return
        else:
            return
    @staticmethod
    def save(website, name, title='', author='', sl='', description='', content='', tags=None, divid='', divclass=''):
        # save the changes to the primary Objects() data store
        odb = db.Query(Objects)
        odb.filter('name = ', name)
        odb.filter('website = ', website)
        item = odb.get()
        if item is None:
            item = Objects()
            item.name = name
            item.website = website
        item.title = title
        item.author = author
        item.sl = sl
        item.description = description
        item.content = content
        item.divid = divid
        item.divclass = divclass
        if type(tags) is list:
            item.tags = tags
        item.put()
        object = dict()
        object['title]'] = title
        object['author'] = author
        object['sl']=sl
        object['description']=description
        object['content']=content
        object['divid']=divid
        object['divclass']=divclass
        object['tags']=tags
        memcache.set('objects|website=' + website + '|name=' + name, object, 300)
        # add this edit to the revision history, so changes are logged, and rollback features can
        # be implemented
        return True
    
class Queue(db.Model):
    """
    This data store is used to store a queue of jobs waiting to be processed. It catalogs
    entries by domain, url, source language, target language and a few other parameters,
    and is used to drive translation queues for services like The Extraordinaries and third
    party translation service bureaus. 
    """
    guid = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    st = db.TextProperty(default='')
    tt = db.TextProperty(default='')
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    translated = db.BooleanProperty(default=False)
    completed = db.BooleanProperty(default=False)
    createdon = db.DateTimeProperty(auto_now_add=True)
    completedon = db.DateTimeProperty()
    lsp = db.StringProperty(default='')
    username = db.StringProperty(default='')
    avgscore = db.FloatProperty()
    numscores = db.IntegerProperty(default=0)
    scoredby = db.ListProperty(str)
    scores = db.ListProperty(str)
    scored = db.BooleanProperty(default = False)
    @staticmethod
    def add(sl, tl, st, domain='', url='', lsp=''):
        st = clean(st)
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            m = md5.new()
            m.update(sl)
            m.update(tl)
            m.update(st)
            g = str(m.hexdigest())
            qdb = db.Query(Queue)
            qdb.filter('guid = ', g)
            item = qdb.get()
            if item is None:
                item = Queue()
                item.guid = g
                item.sl = sl
                item.tl = tl
                item.st = clean(st)
                item.domain = domain
                item.url
                item.lsp = lsp
                item.put()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def submit(guid, tt, username, pw, remote_addr):
        if len(guid) > 0 and len(tt) > 0:
            tdb = db.Query(Queue)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                sl = item.sl
                tl = item.tl
                st = item.st
                tt = item.tt
                domain = item.domain
                url = item.url
                m = md5.new()
                m.update(guid)
                m.update(str(datetime.datetime.now()))
                md5hash = str(m.hexdigest())
                tdb = db.Query(Queue)
                tdb.filter('guid = ', md5hash)
                item = tdb.get()
                if item is None:
                    item.sl = sl
                    item.tl = tl
                    item.st = st
                    item.tt = tt
                    item.translated = True
                    item.domain = domain
                    item.url = url
                    item.scored = False
                    item.put()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    @staticmethod
    def query(sl, tl, domain='', url='', lsp='', limit=20):
        jobs = list()
        if len(sl) > 0 and len(tl) > 0 and len(lsp) > 0:
            qdb = db.Query(Queue)
            qdb.filter('completed = ', False)
            qdb.filter('sl = ', sl)
            qdb.filter('tl = ', tl)
            if len(domain) > 0:
                qdb.filter('domain = ', domain)
            if len(lsp) > 0:
                qdb.filter('lsp = ', lsp)
            qdb.order('-createdon')
            results = qdb.fetch(limit=limit)
            if results is not None:
                for r in results:
                    job = rec()
                    job.sl = r.sl
                    job.tl = r.tl
                    job.st = clean(r.st)
                    job.domain = r.domain
                    job.url = r.url
                    job.createdon = r.createdon
                    job.lsp = r.lsp
                    jobs.append(job)
        return jobs
    @staticmethod
    def complete(guid):
        qdb = db.Query(Queue)
        qdb.filter('guid = ', guid)
        item = qdb.get()
        if item is not None:
            item.completed = True
            return True
        else:
            return False
    @staticmethod
    def getitemstoscore(guid='', domain='', url='', sl='', tl='', lsp='', limit=10):
        tdb = db.Query(Queue)
        if len(guid) > 0:
            tdb.filter('guid = ', guid)
        if len(domain) > 0:
            tdb.filter('domain = ', domain)
        if len(url) > 0:
            tdb.filter('url = ', url)
        if len(sl) > 1:
            tdb.filter('sl = ', sl)
        if len(tl) > 1:
            tdb.filter('tl = ', tl)
        if len(lsp) > 0:
            tdb.filter('lsp = ', lsp)
        tdb.filter('scored = ', False)
        tdb.filter('translated = ', True)
        results = tdb.fetch(limit = limit)
        return results
    @staticmethod
    def getitemstotranslate(guid = '', domain='', url='', sl='', tl='', lsp='', limit=10):
        tdb = db.Query(Queue)
        if len(guid) > 0:
            tdb.filter('guid = ', guid)
        if len(domain) > 0:
            tdb.filter('domain = ', domain)
        if len(url) > 0:
            tdb.filter('url = ', url)
        if len(sl) > 1:
            tdb.filter('sl = ', sl)
        if len(tl) > 1:
            tdb.filter('tl = ', tl)
        if len(lsp) > 0:
            tdb.filter('lsp = ', lsp)
        tdb.filter('translated = ', False)
        results = tdb.fetch(limit = limit)
        return results        
    @staticmethod
    def score(guid, username, pw, remote_addr, score):
        if len(guid) > 8 and len(remote_addr) > 0:
            if len(username) > 0:
                session = Users.auth(username, pw, remote_addr)
                validuser = True
                if not validuser:
                    return False
            else:
                validuser = True
                username = remote_addr
            tdb = db.Query(Queue)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                numscores = item.numscores
                if numscores is None:
                    numscores = 1
                else:
                    numscores = numscores + 1
                if username not in item.scoredby:
                    scoredby = item.scoredby
                    scoredby.append(username)
                    item.scoredby = scoredby
                    scores = item.scores
                    scores.append(score)
                    item.scores = scores
                    rawscore = 0
                    numscores = 0
                    for s in scores:
                        rawscore = rawscore + int(s)
                        numscores = numscores + 1
                    avgscore = float(rawscore/numscores)
                    item.avgscore = avgscore
                    item.put()
                    return True
                else:
                    return False
        else:
            return False
    @staticmethod
    def selectwinners(minimum_score, minimum_votes=1):
        tdb = db.Query(Queue)
        tdb.filter('translated = ', True)
        tdb.filter('numscores >= ', minimum_votes)
        results = tdb.fetch(limit=100)
        for r in results:
            if r.avgscore < minimum_score:
                r.delete()
            if r.avgscore > minimum_score:
                sl = r.sl
                tl = r.tl
                st = r.st
                tt = r.tt
                domain = r.domain
                url = r.url
                swords = string.split(string.lower(st))
                twords = string.split(string.lower(tt))
                username = r.username
                remote_addr = r.remote_addr
                item = Translation()
                item.sl = sl
                item.tl = tl
                item.st = st
                item.tt = tt
                item.domain = domain
                item.url = url
                item.username = username
                item.avgscore = avgscore
                item.scores = r.numscores
                item.locked = True
                item.put()
                r.delete()
        return True
    
class Revisions(db.Model):
    action = db.StringProperty(default = '')
    website = db.StringProperty(default = '')
    name = db.StringProperty(default = '')
    title = db.StringProperty(default = '', multiline = True)
    description = db.TextProperty(default = '')
    content = db.TextProperty(default = '')
    date = db.DateTimeProperty(auto_now_add = True)
    username = db.StringProperty(default = '')
    remote_addr = db.StringProperty(default = '')
    city = db.StringProperty(default = '')
    state = db.StringProperty(default = '')
    country = db.StringProperty(default = '')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    @staticmethod
    def get(website, name):
        results = memcache.get('revisions|website=' + website + '|name=' + name)
        if results is not None:
            return results
        else:
            rdb = db.Query(Revisions)
            rdb.filter('website = ', website)
            rdb.filter('name = ', name)
            rdb.order('-date')
            results = rdb.fetch(limit=100)
            if results is not None:
                memcache.set('revisions|website=' + website + '|name=' + name, results, 300)
            return results
    @staticmethod
    def save(website, name, object, username='', remote_addr='', action='edit'):
        if len(name) > 0 and type(object) is dict:
            if len(remote_addr) > 0:
                location = geo.get(remote_addr)
            else:
                location = None
            rdb = Revisions()
            rdb.action = action
            rdb.website = website
            rdb.name = name
            rdb.title = object.get('title', '')
            rdb.description = object.get('description', '')
            rdb.username = username
            rdb.remote_addr = remote_addr
            if type(location) is dict:
                rdb.city = location.get('city', '')
                rdb.state = location.get('state', '')
                rdb.country = location.get('country', '')
                try:
                    rdb.latitude = float(location.get('latitude', ''))
                    rdb.longitude = float(longitude.get('longitude', ''))
                except:
                    pass
            rdb.put()
            return True
        else:
            return False

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
    @staticmethod
    def batch(authors):
        if type(authors) is list:
            for a in authors:
                records = list()
                if string.count(a, '.') > 1:
                    sc = Score.stats(remote_addr = a)
                elif len(a) > 0:
                    sc = Score.stats(username = a)
                else:
                    sc = None
                if type(sc) is dict:
                    r = rec()
                    if string.count(a, '.') > 1:
                        r.remote_addr = a
                    else:
                        r.username = a
                    r.upvotes = sc.get('upvotes')
                    r.downvotes = sc.get('downvotes')
                    r.blockedvotes = sc.get('blockedvotes')
                    records.append(r)
                return records
    @staticmethod
    def lsp(guid='', jobid='', fields=dict()):
        if len(guid) > 0 and len(jobid) > 0 and type(fields) is dict:
            sdb = db.Query(Score)
            sdb.filter('guid = ', guid)
            sdb.filter('jobid = ',jobid)
            item = sdb.get()
            if item is None:
                item = Score()
                item.jobid = jobid
                item.guid = guid
                item.lsp = True
                item.lspname = fields.get('lsp','')
            item.scoredby = fields.get('translator','')
            item.scoredby_remote_addr = fields.get('remote_addr','')
            item.sl = fields.get('sl','')
            item.tl = fields.get('tl','')
            item.spam = fields.get('spam','')
            item.city = fields.get('city','')
            item.state = fields.get('state','')
            item.country = fields.get('country','')
            try:
                item.latitude = float(fields.get('latitude'))
                item.longitude = float(fields.get('longitude'))
            except:
                pass
            item.score = fields.get('score')
            item.put()
            return True
        else:
            return False
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
            results = sdb.fetch(limit=200)
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
            return records
        else:
            return
    @staticmethod
    def save(guid, votetype='', username='', remote_addr='', city='', state='', country='', latitude=None, longitude=None):
        """
        This method saves a score to the Score data store, after first checking to see if
        a score has already been recorded for this item (guid locator) from the user's IP
        address. If a score has already been recorded, it will update the existing record,
        and if not, will create a new record. 
        """
        tx = Translation.getbyguid(guid)
        if type(tx) is dict:
            author_username = tx.get('username', '')
            author_ip = tx.get('remote_addr', '')
            sl = tx.get('sl', '')
            tl = tx.get('tl', '')
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
            item.domain = domain
            item.url = url
            try:
                item.latitude = float(latitude)
                item.longitude = float(longitude)
            except:
                pass
            if votetype == 'up':
                item.score = 5
            else:
                item.score = 0
            if votetype == 'block':
                item.blocked = True
            item.put()
            p = dict()
            p['guid']=guid
            return True
        else:
            return False
    @staticmethod
    def stats(guid='', md5hash='', username='', remote_addr ='', sl='', tl='', domain='', url='',city='', country=''):
        if len(guid) > 0 or len(md5hash) > 0 or len(username) > 0 or len(remote_addr) > 0 or len(sl) > 0 or len(tl) > 0 or len(domain) > 0 or len(url) > 0 or len(city) > 0 or len(country) > 0:
            upvotes=0
            downvotes=0
            blockedvotes=0
            rawscore=0
            scores=0
            sdb = db.Query(Score)
            if len(guid) > 0:
                sdb.filter('guid = ', guid)
            elif len(md5hash) > 0:
                sdb.filter('md5hash = ', md5hash)
            elif len(username) > 0:
                sdb.filter('username = ', username)
            elif len(remote_addr) > 0:
                sdb.filter('remote_addr = ', remote_addr)
            elif len(sl) > 0:
                sdb.filter('sl = ', sl)
            elif len(tl) > 0:
                sdb.filter('tl = ', tl)
            elif len(domain) > 0:
                sdb.filter('domain = ', domain)
            elif len(url) > 0:
                sdb.filter('url = ', url)
            elif len(city) > 0:
                sdb.filter('city = ', city)
            elif len(country) > 0:
                sdb.filter('country = ', country)
            else:
                sdb.filter('sl = ', 'XYZ')
            results = sdb.fetch(limit=1000)
            for r in results:
                scores = scores + 1
                if r.score == 5:
                    upvotes = upvotes + 1
                elif r.blocked:
                    blockedvotes = blockedvotes + 1
                elif r.score == 0:
                    downvotes = downvotes + 1
                else:
                    pass
            rawscore = upvotes * 5
            if scores > 0:
                avgscore = float(rawscore/scores)
            else:
                avgscore = float(0)
            scorestats = dict()
            scorestats['upvotes']=upvotes
            scorestats['downvotes']=downvotes
            scorestats['blockedvotes']=blockedvotes
            scorestats['avgscore']=avgscore
            scorestats['rawscore']=rawscore
            scorestats['scores']=scores
            return scorestats
        else:
            return dict()
    @staticmethod
    def updateuser(username, remote_addr):
        if len(username) > 0 or len(remote_addr) > 0:
            return False
        else:
            return False
        
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
        value = memcache.get('settings|name=' + name + '|website=' + website)
        if value is not None:
            return value
        else:
            sdb = db.Query(Settings)
            sdb.filter('name = ', name)
            sdb.filter('website = ', website)
            item = sdb.get()
            if item is not None:
                v = codecs.encode(item.value, encoding)
                memcache.set('settings|name=' + name + '|website=' + website, v, 600)
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
    def save(name, v, website=''):
        sdb = db.Query(Settings)
        sdb.filter('name = ', name)
        sdb.filter('website = ', website)
        item = sdb.get()
        if item is None:
            item = Settings()
            item.name = name
            item.website = website
        item.value = v
        item.put
        memcache.set('settings|name=' + name + '|website=' + website, v, 600)
        return True
    
class SourceTexts(db.Expando):
    """
    SourceTexts() is the data store used to store source texts, as well as
    meta data and summary stats related to translations. 
    """
    sl = db.StringProperty(default='', multiline=True)
    st = db.TextProperty(default='')
    md5hash = db.StringProperty(default='')
    date = db.DateTimeProperty(auto_now_add = True)
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    @staticmethod
    def stats(sl, st):
        if len(sl) > 0 and len(st) > 0:
            m = md5.new()
            m.update(sl)
            m.update(st)
            md5hash = str(m.hexdigest())
            sdb = db.Query(SourceTexts)
            sdb.filter('md5hash = ', md5hash)
            item = sdb.get()
            if item is not None:
                return item
    @staticmethod
    def submit(sl, st, domain='', url=''):
        """
        Checks to see if a source text is already in the index, and if not
        creates a stub record. 
        """
        result = memcache.get('sourcetexts|sl=' + sl + '|st=' + st)
        if result is not None:
            return True
        else:
            m = md5.new()
            m.update(sl)
            m.update(st)
            md5hash = str(m.hexdigest())
            sdb = db.Query(SourceTexts)
            sdb.filter('md5hash = ', md5hash)
            item = sdb.get()
            if item is not None:
                memcache.set('sourcetexts|sl=' + sl + 'st=' + st)
                return True
            else:
                item = SourceTexts()
                item.sl = sl
                item.st = st
                item.md5hash = md5hash
                item.domain = domain
                item.url = url
                item.put()
                return True
    @staticmethod
    def translate(sl, st, tl, tt, domain='', url=''):
        if len(sl) > 0 and len(st) > 0 and len(tl) > 0 and len(tt) > 0:
            m = md5.new()
            m.update(sl)
            m.update(st)
            md5hash = str(m.hexdigest())
            sdb = db.Query(SourceTexts)
            sdb.filter('md5hash=', md5hash)
            item = sdb.get()
            if item is None:
                item = SourceTexts()
                item.sl = sl
                item.st = st
                item.md5hash = md5hash
                item.domain = domain
                item.url = url
            edits = getattr(item, 'edits.' + tl)
            if type(edits) is int:
                edits = edits + 1
                setattr(item, 'edits.' + tl, edits)
            else:
                setattr(item, 'edits.' + tl, 1)
            words = getattr(item, 'words.' + tl)
            twords = len(string.split(tt, ' '))
            if type(words) is int:
                words = words + twords
            else:
                words = twords
            setattr(item, 'words.' + tl, words)
            item.put()
            return True
        else:
            return False
        
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
        
class Permissions(db.Model):
    """
    This data store contains additional permissions information, and is
    used to keep track of fine grained access controls (e.g. UserX can
    translate to Spanish but not German). This is generally only used in
    closely managed sites.
    """
    website = db.StringProperty(default='')
    username = db.StringProperty(default='')
    allow_translations = db.ListProperty(str)
    allow_scores = db.ListProperty(str)
    @staticmethod
    def check(website, username, language):
        if len(username) < 1 or len(website) < 1:
            return False
        pdb = db.Query(Permissions)
        pdb.filter('website = ', website)
        pdb.filter('username = ', username)
        pdb.filter('allow_translations = ', language)
        item = pdb.get()
        if item is not None:
            return True
        else:
            return False
    @staticmethod
    def language(website, username, language, allow):
        if len(website) > 0 and len(username) > 0 and len(language) > 0:
            pdb = db.Query(Permissions)
            pdb.filter('website = ', website)
            pdb.filter('username = ', username)
            item = pdb.get()
            if item is None:
                item = Permissions()
            langlist = item.allow_translations
            if language not in langlist:
                langlist.append(language)
                item.allow_translations = langlist
            item.put()
            return True
        else:
            return False

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
    ngrams = db.ListProperty(str)
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
        sl = string.lower(sl)
        tl = string.lower(tl)
        allow_translation = False
        if lsp == 'speaklike' and sl != tl:
            if (tl in Config.speaklike_languages and sl in Config.speaklike_languages) and lspusername != 'bsmcconnell@gmail.com':
                allow_translation = True
            elif lspusername == 'bsmcconnell@gmail.com' and sl == 'en' and (tl == 'es' or tl == 'pt' or tl=='ja' or tl=='de' or tl=='zh' or tl=='ru'):
                allow_translation = True
            if allow_translation:
                st = clean(st)
                st = string.replace(st,'<','&lt;')
                st = string.replace(st,'>','&gt;')
                st = string.replace(st,'\"','&quot;')
                st = string.replace(st,'\'','&apos;')
                queued = memcache.get('lsp_queue|sl=' + sl + '|tl=' + tl + '|st=' + st)
                if queued is None:
                    memcache.set('lsp_queue|sl=' + sl + '|tl=' + tl + '|st=' + st, 'queued', 7200)
                    t = '<SLClientMsg><cmd type="Login" id="1"><u>' + lspusername + '</u><p>' + lsppw + '</p></cmd>'
                    t = t + '<cmd type="SubmitDocument" id="2"><document><originalLangId>' + sl + '</originalLangId>'
                    t = t + '<targetLanguages><langId>' + tl + '</langId></targetLanguages>'
                    t = t + '<mimeType>text/plain</mimeType><encoding>none</encoding>'
                    t = t + '<contents>' + st + '</contents></document>'
                    t = t + '<callback type="translationComplete" method="FORM">'
                    t = t + '<url>http://www.worldwidelexicon.org/submit</url>'
                    t = t + '<formParams>'
                    t = t + '<param name="sl" val="%SPEAKLIKE_SOURCE_LANG_ID%"/>'
                    t = t + '<param name="tl" val="%SPEAKLIKE_TARGET_LANG_IDS%"/>'
                    t = t + '<param name="st" val="%SPEAKLIKE_ORIGINAL_CONTENTS%"/>'
                    t = t + '<param name="tt" val="%SPEAKLIKE_TRANSLATED_CONTENTS_' + tl + '%"/>'
                    t = t + '<param name="username" val="speaklike"/>'
                    t = t + '<param name="domain" val="' + domain + '"/>'
                    t = t + '<param name="url" val="' + url + '"/>'
                    t = t + '<param name="output" val="text"/>'
                    t = t + '<param name="lsp" val="speaklike"/>'
                    t = t + '</formParams>'
                    t = t + '<expectedResponse>ok</expectedResponse>'
                    t = t + '</callback>'
                    t = t + '<affiliate>worldwidelexicon.org</affiliate>'
                    t = t + '</cmd></SLClientMsg>'
                    form_fields = {
                        "msg" : t
                    }
                    sl_url = 'http://www.speaklike.com/REST/controller/formSend'
                    form_data = urllib.urlencode(form_fields)
                    p = dict()
                    p['url'] = sl_url
                    p['form_data'] = form_data
                    p['lsp'] = 'speaklike'
                    taskqueue.add(url = '/queue/send', params = p)
                    return ''
                else:
                    return ''
            else:
                return ''
        elif len(lsp) > 0:
            lurl = Config.lspurl(lsp)
            if len(lurl) > 0:
                f = dict()
                f['sl']=sl
                f['tl']=tl
                f['st']=st
                f['domain']=domain
                f['url']=url
                f['username']=lspusername
                f['pw']=lsppw
                m = md5.new()
                m.update(sl)
                m.update(tl)
                m.update(st)
                f['guid'] = str(m.hexdigest())
                form_data = urllib.urlencode(f)
                p = dict()
                p['url'] = lurl
                p['form_data'] = form_data
                p['lsp'] = lsp
                taskqueue.add(url = '/queue/send', params=p)
            return ''
        else:
            return ''
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
    def score(guid, votetype):
        if len(guid) > 0 and len(votetype) > 0:
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                upvotes = item.upvotes
                downvotes = item.downvotes
                blockedvotes = item.blockedvotes
                scores = item.scores
                if votetype == 'up':
                    upvotes = upvotes + 1
                    scores = scores + 1
                elif votetype == 'down':
                    downvotes = downvotes + 1
                    scores = scores + 1
                elif votetype == 'block':
                    blockedvotes = blockedvotes + 1
                    scores = scores + 1
                else:
                    pass
                rawscore = upvotes * 5
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
    def submit(sl='', st='', tl='', tt='', username='', remote_addr='', domain='', url='', city='', state='', country='', longitude=None, latitude=None, professional=False, lsp='', proxy='n'):
        if len(sl) > 0 and len(st) > 0 and len(tl) > 0 and len(tt) > 0:
            validquery = True
        else:
            validquery = False
        if validquery:
            st = clean(st)
            tt = clean(tt)
            twords = string.split(tt)
            swords = string.split(st)
            m = md5.new()
            m.update(tt.encode('utf-8'))
            m.update(str(datetime.datetime.now()))
            guid = str(m.hexdigest())
            n = md5.new()
            n.update(st.encode('utf-8'))
            md5hash = str(n.hexdigest())
            tdb = Translation()
            tdb.md5hash = md5hash
            tdb.guid = guid
            tdb.sl = sl
            tdb.tl = tl
            tdb.st = st
            tdb.tt = tt
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
            if lsp == 'speaklike' or lsp == 'proz':
                tdb.professional = True
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
            # generate n-gram list
            numwords = len(ngrams)
            chars = 0
            if numwords > 0 and chars < 400:
                i = 0
                while i < numwords:
                    try:
                        ngrams.append(ngrams[i] + ' ' + ngrams[i+1])
                    except:
                        pass
                    try:
                        ngrams.append(ngrams[i] + ' ' + ngrams[i+1] + ' ' + ngrams[i+2])
                    except:
                        pass
                    try:
                        ngrams.append(ngrams[i] + ' ' + ngrams[i+1] + ' ' + ngrams[i+2] + ' ' + ngrams[i+3])
                    except:
                        pass
                    try:
                        ngrams.append(ngrams[1] + ' ' + ngrams[i+1] + ' ' + ngrams[i+2] + ' ' + ngrams[i+3] + ' ' + ngrams[i+4])
                    except:
                        pass
                    i = i + 1
            #tdb.ngrams = ngrams
            tdb.put()
            if len(username) > 0:
                if type(latitude) is float and type(longitude) is float:
                    Users.translate(username, len(twords), city=city, state=state, country=country, latitude=latitude, longitude=longitude)
                else:
                    try:
                        latitude = float(latitude)
                        longitude = float(longitude)
                    except:
                        latitude = None
                        longitude = None
                    Users.translate(username, len(twords), city=city, state=state, country=country, latitude=latitude, longitude=longitude)
            p = dict()
            return True
        else:
            return False
    @staticmethod
    def updatescores(guid):
        if len(guid) > 0:
            results = Score.fetch(guid=guid)
            upvotes = 0
            downvotes = 0
            blockedvotes = 0
            scores = 0
            for r in results:
                scores = scores + 1
                if r.blocked:
                    blockedvotes = blockedvotes + 1
                elif r.score == 0:
                    downvotes = downvotes + 1
                elif r.score == 5:
                    upvotes = upvotes + 1
                else:
                    pass
            rawscore = upvotes * 5
            avgscore = float(rawscore/scores)
            tdb = db.Query(Translation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                item.upvotes = upvotes
                item.downvotes = downvotes
                item.blockedvotes = blockedvotes
                item.scores = scores
                item.rawscore = rawscore
                item.avgscore = avgscore
                item.put()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def userscore(username, upvotes, downvotes, blockedvotes, rawscore, scores):
        if len(username) > 0 and scores > 0:
            avgscore = float(rawscore/scores)
            tdb = db.Query(Translation)
            tdb.filter('username = ', username)
            tdb.order('-date')
            results = tdb.fetch(limit=100)
            for r in results:
                r.userupvotes = upvotes
                r.userdownvotes = downvotes
                r.userblockedvotes = blockedvotes
                r.userrawscore = rawscore
                r.userscores = scores
                r.useravgscore = avgscore
                r.put()
            return True
        else:
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
    def lucky(sl = '', tl = '', st = '', domain = '', url='', allow_anonymous='y', allow_machine ='y', min_score=0, userip='', output='text', edit='y', lsp='', lspusername = '', lsppw='', professional=False, mtengine='', queue='', ip=''):
        text = ''
        response = ''
        st = clean(st)
        if sl == tl:
            return st
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            m = md5.new()
            st = codecs.encode(st, 'utf-8')
            m.update(st)
            md5hash = str(m.hexdigest())
            text = memcache.get('lucky|sl=' + sl + '|tl=' + tl + '|md5hash=' + md5hash + '|output=' + output)
            if text is not None:
                return text
            # look for professional translation
            tdb = db.Query(Translation)
            tdb.filter('sl = ', sl)
            tdb.filter('tl = ', tl)
            tdb.filter('md5hash = ', md5hash)
            tdb.filter('professional = ', True)
            tt = ''
            item = tdb.get()
            if item is not None:
                tt = clean(item.tt)
            else:
                if len(lsp) > 0:
                    response=Translation.lsp(sl, tl, st, domain=domain, url=url, lsp=lsp, lspusername=lspusername, lsppw=lsppw)
            # next look for user translations
            if len(tt) < 1:
                tdb = db.Query(Translation)
                tdb.filter('sl = ', sl)
                tdb.filter('tl = ', tl)
                tdb.filter('md5hash = ', md5hash)
                tdb.order('-date')
                item = tdb.get()
                if item is not None:
                    tt = clean(item.tt)
            if len(tt) < 1 and allow_machine != 'n':
                if len(queue) > 0:
                    Queue.add(sl, tl, st, domain=domain, url=url, lsp=queue)
                mt = MTWrapper()
                tt = mt.getTranslation(sl, tl, st, mtengine, userip=userip)
            if len(tt) > 0:
                if output == 'text':
                    text = tt
                elif output == 'test':
                    text = tt + '<p>' + response
                elif output == 'json':
                    text = tt
                elif output == 'xml' or output == 'rss':
                    text = tt
                else:
                    text = '<div class="translation">' + tt + '</div>'
            else:
                text = ''
            if len(text) > 0:
                memcache.set('lucky|sl=' + sl + '|tl=' + tl + '|md5hash=' + md5hash + '|output=' + output, text, 300)
        return text
    @staticmethod
    def fetch(sl='', tl='', st='', md5hash='', domain='', url='', userip='', allow_machine='y', allow_anonymous='', min_score=0, max_blocked_votes=0, fuzzy = 'n', mtengine=''):
        if len(url) > 500:
            url = url[0:499]
        if len(st) > 0 or len(md5hash) > 0:
            if len(st) > 0:
                m = md5.new()
                try:
                    m.update(st.encode('utf-8'))
                except:
                    m.update(smart_str(st))
                md5hash = str(m.hexdigest())
            results = memcache.get('translations|fetch|sl=' + sl + '|tl=' + tl + '|md5hash=' + md5hash)
        else:
            results = memcache.get('translations|fetch|sl=' + sl + '|tl=' + tl + '|domain=' + domain + '|url=' + url)
        if results is None:
            sortdate = True
            tdb = db.Query(Translation)
            tdb.filter('sl = ', sl)
            tdb.filter('tl = ', tl)
            if fuzzy == 'y':
                if len(st) < 500:
                    tdb.filter('ngrams = ', st)
                else:
                    st = st[0:400]
                    tdb.filter('ngrams = ', st)
            else:
                if len(st) > 0 or len(md5hash) > 0:
                    tdb.filter('md5hash = ', md5hash)
                else:
                    if len(domain) > 0:
                        tdb.filter('domain = ', domain)
                    if len(url) > 0:
                        tdb.filter('url = ', url)
            if sortdate:
                tdb.order('-date')
            results = tdb.fetch(limit=100)
        filtered_results = list()
        for r in results:
            skiprecord = False
            if allow_anonymous == 'n' and r.anonymous:
                skiprecord=True
            if allow_anonymous == 'n' and r.username == '':
                skiprecord=True
            if min_score > 0 and r.avgscore < min_score:
                skiprecord=True
            if r.spam:
                skiprecord=True
            if max_blocked_votes > 0 and r.blockedvotes > max_blocked_votes:
                skiprecord=True
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
    
class Presence(db.Model):
    username = db.StringProperty(default='')
    network = db.StringProperty(default='')
    timestamp = db.DateTimeProperty()
    status = db.StringProperty(default='')
    languages = db.ListProperty(str)
    @staticmethod
    def set(username, network, status, languages):
        if len(username) > 0 and len(network) > 0 and len(status) > 0 and type(languages) is list:
            pdb = db.Query(Presence)
            pdb.filter('username = ', username)
            pdb.filter('network = ', network)
            item = pdb.get()
            if item is None:
                item = Presence()
                item.username = username
                item.network = network
            item.languages = languages
            item.timestamp = datetime.datetime.now()
            item.status = status
            item.put()
            memcache.set('presence|username=' + username + '|network=' + network, languages, 300)
            return True
        else:
            return False
    @staticmethod
    def find(network, status, languages):
        records = list()
        if len(network) > 0 and len(status) > 0 and type(languages) is list:
            pdb = db.Query(Presence)
            pdb.filter('network = ', network)
            pdb.filter('status = ', status)
            if len(languages) > 0:
                for l in languages:
                    pdb.filter('languages = ', l)
            pdb.order('-timestamp')
            results = pdb.fetch(limit=100)
            for r in results:
                username = r.username
                records.append(r.username)
        return records
    
class Users(db.Model):
    username = db.StringProperty(default='')
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
            sessionname = memcache.get('sessions|' + session)
            sessioninfo = dict()
        else:
            sessionname = None
        if sessionname is not None:
            sessioninfo['username']=sessionname
            sessioninfo['session']=session
            return sessioninfo
        elif sessionname is None:
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
                    if loggedin is None:
                        p = dict()
                        p['username']=username
                        taskqueue.add(url = '/scores/user', params=p)
                        memcache.set('login|' + username, sessioninfo, 7200)
                    return sessioninfo
                else:
                    return
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
    def savescore(username, votetype, remote_addr):
        if len(username) > 0 and len(votetype) > 0 and len(remote_addr) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                upvotes = item.upvotes
                downvotes = item.downvotes
                blockedvotes = item.blockedvotes
                scores = item.scores
                if votetype == 'up':
                    upvotes = upvotes + 1
                    scores = scores + 1
                elif votetype == 'down':
                    downvotes = downvites + 1
                    scores = scores + 1
                elif votetype == 'block':
                    blockedvotes = blockedvotes + 1
                    scores = scores + 1
                else:
                    pass
                rawscore = upvotes * 5
                if scores > 0:
                    avgscore = float(rawscore/scores)
                else:
                    avgscore = float(0)
                item.upvotes = upvotes
                item.downvotes = downvotes
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

class Urls(db.Model):
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    turl = db.StringProperty(default='')
    timekey = db.StringProperty(default='')
    stitle = db.StringProperty(default='')
    ttitle = db.StringProperty(default='')
    author = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    st = db.TextProperty(default='')
    tl = db.StringProperty(default='')
    tt = db.TextProperty(default='')
    swords = db.ListProperty(str)
    twords = db.ListProperty(str)
    views = db.IntegerProperty(default=1)
    lastvisit = db.DateTimeProperty(auto_now_add = True)
    remote_addr = db.StringProperty(default = '')
    user_ip = db.StringProperty(default = '')
    @staticmethod
    def log(url, domain='', turl='', timekey='', stitle='', ttitle='', sl='', tl='', author='', st='', tt=''):
        if len(tl) > 0 and len(sl) > 0 and len(url) > 0:
            udb = db.Query(Urls)
            udb.filter('sl = ', sl)
            udb.filter('tl = ', tl)
            udb.filter('url = ', url)
            if len(turl) > 0:
                udb.filter('turl = ', turl)
            if len(timekey) > 0:
                udb.filter('timekey = ', timekey)
            item = udb.get()
            if item is None:
                item = Urls()
                item.sl = sl
                item.tl = tl
                item.url = url
                item.turl = turl
                item.timekey = timekey
            st = st.lower()
            tt = tt.lower()
            stitle = stitle.lower()
            ttitle = ttitle.lower()
            item.st = st
            item.tt = tt
            item.stitle = stitle
            item.ttitle = ttitle
            item.author = author
            sw = string.split(st, ' ')
            tw = string.split(tt, ' ')
            for w in sw:
                if len(w) < 3:
                    sw.remove(w)
            for w in tw:
                if len(w) < 3:
                    tw.remove(w)
            views = item.views
            views = views + 1
            item.views = views
            item.remote_addr = remote_addr
            item.user_ip = user_ip
            item.put()
            return True
        else:
            return False
    @staticmethod
    def popular(sl, tl):
        pass
        
class Websites(db.Expando):
    host = db.StringProperty(default='')
    title = db.StringProperty(default='', multiline=True)
    description = db.TextProperty(default='')
    owner = db.StringProperty(default='')
    created = db.DateTimeProperty(auto_now_add = True)
    modified = db.DateTimeProperty(auto_now_add = True)
    tags = db.ListProperty(str)
    alt = db.ListProperty(str)
    sl = db.StringProperty(default='')
    machine_translation = db.ListProperty(str)
    professional_translation = db.ListProperty(str)
    @staticmethod
    def create(host, title, description, sourcelanguages=None, targetlanguages=None):
        host = string.replace(host, 'http://', '')
        subdomains = string.split(host, '/')
        host = subdomains[0]
        subdomains = string.split(host, '.')
        altnames = list()
        for s in subdomains:
            skip=False
            if s == 'com' or s == 'net' or s == 'org' or s == 'co' or s == 'www' or s=='biz':
                skip=True
            if s == 'wordpress' or s == 'blogger' or s == 'typepad' or s == 'tumblr':
                skip=True
            if not skip:
                altnames.append(s)
        if len(host) > 0 and len(title) > 0 and len(description) > 0:
            wdb = db.Query(Websites)
            wdb.filter('host = ', host)
            item = wdb.get()
            if item is not None:
                return False
            else:
                item = Websites()
                item.host = host
                item.title = title
                item.description = description
                item.css = 'blueprint'
                item.alt = altnames
                if type(sourcelanguages) is list:
                    item.sourcelanguages = sourcelanguages
                if type(targetlanguages) is list:
                    item.targetlanguages = targetlanguages
                item.put()
                return True
        else:
            return False
    @staticmethod
    def parm(host, parm):
        value = memcache.get('parms|website=' + host + '|parm=' + parm)
        if value is not None:
            return value
        else:
            wdb = db.Query(Websites)
            wdb.filter('host = ', host)
            item = wdb.get()
            if item is not None:
                try:
                    value = getattr(item, parm)
                    memcache.set('parms|website=' + host + '|parm=' + parm, value, 240)
                    return value
                except:
                    return
            else:
                return
    @staticmethod
    def profile(host, parms):
        if len(host) > 0:
            result = dict()
            wdb = db.Query(Websites)
            wdb.filter('host = ', host)
            item = wdb.get()
            if item is not None:
                for p in parms:
                    try:
                        result[p] = getattr(item, p)
                    except:
                        pass
                return result
            else:
                return result
    @staticmethod
    def resolve(host):
        wdb = db.Query(Websites)
        wdb.filter('alt = ', host)
        item = wdb.get()
        if item is not None:
            return item.host
        else:
            wdb = db.Query(Websites)
            wdb.filter('host = ', host)
            item = wdb.get()
            if item is not None:
                return item.host
            else:
                return ''
    @staticmethod
    def set(host, parms, username='admin'):
        if len(host) > 0 and len(username) > 0 and type(parms) is dict:
            #permission = Users.permission(username, host, 'admin')
            permission = True
            if permission:
                wdb = db.Query(Websites)
                wdb.filter('host = ', host)
                item = wdb.get()
                if item is not None:
                    if type(parms) is dict:
                        pkeys = parms.keys()
                        for p in pkeys:
                            setattr(item, p, parms[p])
                    else:
                        setattr(item, parms, value)
                    item.put()
                    return True
                else:
                    return False
        else:
            return False


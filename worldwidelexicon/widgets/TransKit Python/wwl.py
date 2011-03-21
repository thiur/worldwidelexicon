"""
Worldwide Lexicon Wrapper Library
Brian S McConnell <bsmcconnell@gmail.com>

This library enables Python based applications to easily interact with Worldwide Lexicon translation servers.
Part of the TransKit suite of SDKs for popular programming languages, this library provides the following
features:

* open source, available under a BSD license
* request any blend of professional, volunteer and machine translations on demand
* filter translations based on translation type and quality
* works with public and private WWL servers
* caches translations in memory and/or disk to maximize performance
* allow user edited translations and scores
* simple API makes fetching and submitting translations easy

MEMCACHED SUPPORT: experimental pre-release. Works, but have not tested with memcached yet. If you have problems with it,
let me know. I will be posting incremental updates and will work with you to resolve remaining issues.

UTF-8/UNICODE: be sure to use utf-8 encoding only. WWL is based on utf-8 with fallback to ASCII character encoding. Do
NOT use region or language specific character sets. It will break. Convert to and from UTF-8 when communicating with
WWL services. We try our best to deal with conversions within WWL, but it works a lot better if you are careful to use
UTF-8 as your default character encoding.

PLANNED UPDATES: will be adding gettext() support in the near future, so it will then look for translations in the
following order: 1) memcached (if running), 2) gettext, 3) local disk cache (if enabled), 4) WWL translation server.
This will boost performance, and also allow you to leverage existing gettext localization tools and translation files.
The current release is a prototype, so caching is not fully implemented, so it's a bit slow, but you can get an idea
of how it all works. Have fun.

"""

appengine = False
#from google.appengine.api import memcache
    
import memcache    
import urllib
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
import md5
import string
import gettext
import demjson

server_address = 'http://worldwidelexicon2.appspot.com'

memcache= False
memcache_address = ['localhost:2020']
memcache_ttl = 600

gettext_application_domain = 'myapplication'
gettext_base_path = '/gettext/myapplication'

class WWLError(Exception):
    pass

def open_url(url, form_fields=None, method=None):
    """
    Convenience function which opens a URL (supports GET and POST), and submits form fields to
    the web service, then inspects the response. If the response is JSON, it decodes it using
    the demjson decoder and returns a dictionary, otherwise it returns plain text or raises a
    WWLError exception.
    """
    if type(form_fields) is dict:
        form_data = urllib.urlencode(form_fields)
    else:
        form_data = None
    try:
        if form_data is not None and method != 'get':
            result = urllib2.urlopen(url, form_data)
        elif method=='get' and form_data is not None:
            result = urllib2.urlopen(url + '?' + form_data)
        else:
            result = urllib2.urlopen(url)
        text = result.read()
    except HTTPError, e:
        raise WWLError(e.code)
    try:
        json = demjson.decode(text)
    except:
        json = None
    if json is not None:
        return json
    else:
        return text

def getCache(key):
    """
    Function to fetch an item from memcached, if running
    """
    if len(key) > 0 and len(memcache_address) > 0 and memcache:
        if appengine:
            item = memcache.get(key)
        else:
            mc = memcache.Client(memcache_address)
            item = mc.get(key)
        return item
    else:
        return None
    
def setCache(key, item, ttl=600):
    """
    Function to store an item in memcache, if running
    """
    if len(key) > 0 and len(memcache_address) > 0 and memcache:
        if appengine:
            memcache.set(key, item, ttl)
        else:
            mc = memcache.Client(memcache_address)
            tt = mc.set(key, item, ttl)
        return True
    else:
        return False

def acceptTranslation(guid):
    result = open_url(server_address + '/lsp/accept/' + str(guid))
    if string.count(result, 'ok') > 0:
        return True
    else:
        if type(result) is dict:
            try:
                return result.get('error')
            except:
                return 
        return False

def deleteTranslation(guid):
    result = open_url(server_address + '/lsp/delete/' + str(guid))
    if string.count(result,'ok') > 0:
        return True
    else:
        return False

def rejectTranslation(guid):
    result = open_url(server_address + '/lsp/reject/' + str(guid))
    if string.count(result,'ok') > 0:
        return True
    else:
        return False

def getTranslation(sl, tl, st, guid=None, url=None, lsp=None, username=None, pw=None, sla=None):
    if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
        m = md5.new()
        m.update(st)
        md5hash = str(m.hexdigest())
        result = getCache('/t/' + sl + '/' + tl + '/' + md5hash)
        if result is not None:
            return result
    form_fields = dict(
        sl = sl,
        tl = tl,
        st = st,
    )
    if guid is not None: form_fields['guid']=guid
    if url is not None: form_fields['url']=url
    if lsp is not None: form_fields['lsp']=lsp
    if username is not None: form_fields['lspusername']=username
    if pw is not None: form_fields['lsppw']=lsppw
    if sla is not None: form_fields['sla']=sla
    result = open_url(server_address + '/t', form_fields=form_fields)
    setCache('/t/' + sl + '/' + tl + '/' + md5hash, result)
    return result
    
def getByURL(url, tl=''):
    form_fields = dict(
        url = url,
        tl = tl,
    )
    result = open_url(server_address + '/u/' + tl + '/' + url)
    return result

def getRevisionHistory(st, tl=''):
    form_fields = dict(
        st = st,
        tl = tl,
    )
    result = open_url(server_address + '/r', form_fields=form_fields, method='get')
    return result

def submitTranslation(sl, tl, st, tt, guid=None, url=None, username=None, facebookid=None, profile_url=None):
    form_fields = dict(
        sl = sl,
        tl = tl,
        st = st,
        tt = tt,
    )
    if guid is not None: form_fields['guid']=guid
    if url is not None: form_fields['url']=url
    if username is not None: form_fields['username']=username
    if facebookid is not None: form_fields['facebookid']=facebookid
    if profile_url is not None: form_fields['profile_url']=profile_url
    result = open_url(server_address + '/submit', form_fields=form_fields)
    return result

def getScores(guid='', username=''):
    if len(guid) > 0:
        return open_url(server_address + '/scores/' + guid)
    elif len(username) > 0:
        return open_url(server_address + '/scores/user/' + username)
    else:
        return

def submitScore(guid, score, username='', message=''):
    form_fields = dict(
        guid = guid,
        score = score,
        username = username,
        message = message,
    )
    result= open_url(server_address + '/scores', form_fields=form_fields)
    if string.count(result,'ok') > 0:
        return True
    else:
        return False

def getComments(guid, language=''):
    form_fields = dict(
        guid = guid,
        language = language,
    )
    return open_url(server_address + '/comments', form_fields=form_fields, method='get')

def submitComment(guid, language='', text='', username='', name=''):
    form_fields = dict(
        guid = guid,
        language=language,
        text = text,
        username = username,
        name = name,
    )
    result = open_url(server_address + '/comments', form_fields=form_fields)
    if string.count(result, 'ok') > 0:
        return True
    else:
        return False

def getETA(jobtype,lsp, username, pw, sl='', tl='', sla='', words=''):
    form_fields = dict(
        jobtype = jobtype,
        lsp = lsp,
        lspusername = username,
        lsppw = pw,
        sl = sl,
        tl = tl,
        sla = sla,
        words = words,
    )
    return open_url(server_address + '/lsp/eta', form_fields=form_fields, method='get')

def getQuote(jobtype, sl, tl, sla='', username='', words=''):
    form_fields = dict(
        lsp = 'dummy',
        jobtype = jobtype,
        sl = sl,
        tl = tl,
        sla = sla,
        lspusername = username,
        words = words,
    )
    return open_url(server_address + '/lsp/quote', form_fields = form_fields, method='get')

"""
Worldwide Lexicon / SpeakLike Wrapper Library
Brian S McConnell <bsmcconnell@gmail.com>

This library makes it easy to incorporate hybrid translation into any Python application. The library enables
you to request any combination of machine, crowd (user generated) and professional translations on demand.
The library is tightly integrated with both the Worldwide Lexicon open translation platform, and SpeakLike, a
New York based professional translation network. Part of the TransKit suite of SDKs for popular programming
languages, this library provides the following features:

* open source, available under a BSD license
* request any blend of professional, volunteer and machine translations on demand
* filter translations based on translation type and quality
* caches translations in memory and/or disk to maximize performance
* allow user edited translations and scores
* simple API makes fetching and submitting translations easy
* support for direct calls to Google Translate and Apertium machine translation servers

MEMCACHED SUPPORT: experimental release. Works, but have not tested with memcached yet. If you have problems with it,
let me know. I will be posting incremental updates and will work with you to resolve remaining issues.

UTF-8/UNICODE: be sure to use utf-8 encoding only. WWL is based on utf-8 with fallback to ASCII character encoding. Do
NOT use region or language specific character sets. It will break. Convert to and from UTF-8 when communicating with
WWL services. We try our best to deal with conversions within WWL, but it works a lot better if you are careful to use
UTF-8 as your default character encoding.

GETTING TRANSLATIONS

Getting translations is very simple, just do the following:

    translations = getTranslation('en','es','Hello World')

You'll get the best available machine or user generated translation. To request a professional translation:

    translations = getTranslation('en','es','Hello World', username='youremail', pw='yourspeaklikepw')

You'll get a professional translation from SpeakLike if one is already cached, or a placeholder translation
(usually a machine translation). There's no need to implement a complicated sync algorithm, you can just use
this function to get the most recent translation from the translation memory. However, if you want to have
translations pushed to your system when they are completed by SpeakLike, you can include an optional
callback_url parameter to request asynchronous delivery. The getTranslation() function returns a list of
dictionaries with the translations and metadata. 

SUBMITTING USER GENERATED TRANSLATIONS

Just do the following:

    guid = submitTranslation(source_lang,target_lang,source_text,translated_text,username='your_email')

It will return a unique record locator if successful, or None if the submission failed.

GETTING SCORES FOR A TRANSLATION

    scores = getScores(guid=record_locator)

Returns a list of dictionaries containing individual scores and a composite score for the translation. You
can also request scores for a particular translator across all translations by including the username=....
parameter, or by IP address with ip_address=...

SUBMITTING A SCORE FOR A TRANSLATION

    success = submitScore(guid, score, username='scorer_name_or_email', message='optional message')

CHECKING STATUS OF A TRANSLATION REQUEST



CANCELING A PROFESSIONAL TRANSLATION

REJECTING A PROFESSIONAL TRANSLATION



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
    Fetch an item from memcached, if running
    """
    if len(key) > 0 and len(memcache_address) > 0 and memcache:
        if len(key) > 250:
            m = md5.new()
            m.update(key)
            key = str(m.hexdigest())
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
    Store an item in memcache, if running
    """
    if len(key) > 0 and len(memcache_address) > 0 and memcache:
        if len(key) > 250:
            m = md5.new()
            m.update(key)
            key = str(m.hexdigest())
        if appengine:
            memcache.set(key, item, ttl)
        else:
            mc = memcache.Client(memcache_address)
            tt = mc.set(key, item, ttl)
        return True
    else:
        return False

def googleTestLanguage(text):
    """
    Determine the language a text is written in (uses Google's Language API
    """
    try:
        encodedtext = urllib.quote_plus(text)
    except:
        try:
            encodedtext = urllib.urlencode(text)
        except:
            encodedtext = ''
    url = 'http://ajax.googleapis.com/ajax/services/language/detect?v=1.0&q=' + encodedtext
    result = open_url(url)
    try:
        sl = result['responseData']['language']
    except:
        sl = ''
    return sl

def googleTranslate(sl, tl, text):
    """
    Request a machine translation from Google Translate (we will also be adding
    support for Apertium, Systran, Language Weaver and Bing Translator in the next build)
    """ 
    url="http://ajax.googleapis.com/ajax/services/language/translate"
    form_fields = dict(
        langpair = sl + '|' + tl,
        v = "1.0",
        q = text,
        ie = "UTF8",
    )
    result = open_url(url, form_fields=form_fields)
    try:
        tt = result['responseData']['translatedText']
        return tt
    except:
        return ''

def deleteTransaction(guid, username, pw):
    """
    Delete a translation or score request from the LSP job queue
    """
    form_fields=dict(
        guid=guid,
        lspusername=username,
        lsppw=pw,
    )
    result = open_url(server_address + '/lsp/delete', form_fields=form_fields)
    if string.count(result,'ok') > 0:
        return True
    else:
        return False

def rejectTransaction(guid, username, pw):
    """
    Reject/redo a translation or score request
    """
    form_fields = dict(
        guid=guid,
        lspusername=username,
        lsppw=pw,
    )
    result = open_url(server_address + '/lsp/reject', form_fields=form_fields)
    if string.count(result,'ok') > 0:
        return True
    else:
        return False

def requestTranslation(sl, tl, st, username, pw, guid='', url='', sla='', callback_url='', apikey='', collection='', message=''):
    """
    Request a professional translation. Expects the following parameters:

    sl : source language code
    tl : target language code
    st : source text (utf-8 encoding)
    username : username/id for authentication with language service provider
    pw : password or key
    guid : record locator (optional, if omitted the LSP will assign one)
    url : URL source text came from (optional)
    sla : service level agreement code (optional)
    callback_url : callback URL to submit translation to (optional)
    apikey : secret key to include in callback request (optional)
    message : message for human translator (optional)
    """
    form_fields = dict(
        guid = guid,
        sl = sl,
        tl = tl,
        st = st,
        url = url,
        collection=collection,
        message = message,
        lspusername = username,
        lsppw = pw,
        sla = sla,
        callback_url = callback_url,
        apikey = apikey,
        ac = 'transkit-python',
    )
    result = open_url(server_address + '/lsp/translate', form_fields=form_fields)
    if string.count(result, 'ok') > 0:
        return True
    else:
        return False

def getTranslationStatus(guid, username, pw):
    """
    Returns the status of a professional translation task, possible return values are:

    IN_PROGRESS
    WAITING_FOR_TRANSLATORS
    WAITING_FOR_CREDITS
    COMPLETED
    FAILED
    EXPIRED
    CANCELLED
    REJECTED
    NO_TRANS_REQUIRED
    """
    form_fields = dict(
        guid = guid,
        lspusername = username,
        lsppw = pw,
    )
    result = open_url(server_address + '/lsp/status', form_fields=form_fields)
    return result

def requestScore(guid, sl, tl, st, tt, username, pw, url='', sla='', callback_url='', apikey='', message=''):
    """
    Request score for a crowd translation by professional translator. Expects the following parameters:

    guid : unique record locator
    sl : source language code
    tl : target language code
    st : source text (utf-8 encoding)
    tt : translated text (utf-8 encoding)
    username : username/account ID with language service provider
    pw : password/key
    url : URL source text came from (optional)
    sla : service level agreement code (optional)
    callback_url : callback URL to submit score to (optional)
    apikey : secret key to include in callback query (optional)
    message : optional message for translator
    """
    form_fields = dict(
        guid = guid,
        sl = sl,
        tl = tl,
        st = st,
        tt = tt,
        url = url,
        username = username,
        message = message,
        pw = pw,
        sla = sla,
        callback_url = callback_url,
        apikey = apikey,
        ac = 'transkit-python',
    )
    result = open_url(server_address + '/lsp/score', form_fields = form_fields)
    if string.count(result, 'ok') > 0:
        return True
    else:
        return False
    
def getTranslation(sl, tl, st, guid='', url='', username='', pw='', sla='', callback_url='', apikey='', collection='', message=''):
    """
    Get the best available translation for a text, includes option to request a professional
    translation. Returns a list of translations as dictionaries. Returns a list of dictionaries if successful.
    """
    if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
        result = getCache('/t/' + sl + '/' + tl + '/' + st)
        if result is not None:
            return result
    form_fields = dict(
        sl = sl,
        tl = tl,
        st = st,
        guid = guid,
        url = url,
        lspusername = username,
        lsppw = pw,
        sla = sla,
        callback_url = callback_url,
        apikey = apikey,
        collection = collection,
        message = message,
        ac = 'transkit-python',
    )
    result = open_url(server_address + '/t', form_fields=form_fields)
    setCache('/t/' + sl + '/' + tl + '/' + st, result)
    return result
    
def getByURL(url, tl=''):
    """
    Get all translations associated with a specific URL.
    """
    result = getCache('/u/' + tl + '/' + url)
    if result is not None:
        return result
    form_fields = dict(
        url = url,
        tl = tl,
    )
    result = open_url(server_address + '/u/' + tl + '/' + url)
    setCache('/u/' + tl + '/' + url, result)
    return result

def getRevisionHistory(st, tl=''):
    """
    Request the revision history for translations for a source text
    """
    result = getCache('/r/' + tl + '/' + st)
    if result is not None:
        return result
    form_fields = dict(
        st = st,
        tl = tl,
    )
    result = open_url(server_address + '/r', form_fields=form_fields, method='get')
    setCache('/r' + tl + '/' + st, result)
    return result

def submitTranslation(sl, tl, st, tt, guid='', url='', username='', facebookid='', profile_url='', apikey='', collection='', request_score=False, embargo=False):
    """
    Submit a translation, expects the following parameters:

    sl : source language code
    tl : target language code
    st : source text (utf-8 encoding)
    tt : translated text (utf-8 encoding)
    guid : globally unique ID (if omitted, the system will assign one)
    url : URL source text came from
    username : username/email of translator
    facebookid : Facebook ID number of translator (optional)
    profile_url : Facebook profile URL (optional)
    apikey : secret key (for callback requests)
    collection : collection text belongs to (optional)
    request_score : request professional translator to score text (default = False)
    embargo : embargo the translation until scored
    """
    if request_score:
        request_score = 'y'
    else:
        request_score = 'n'
    if embargo:
        embargo = 'y'
    else:
        embargo = 'n'
    form_fields = dict(
        sl = sl,
        tl = tl,
        st = st,
        tt = tt,
        guid = guid,
        url = url,
        username = username,
        facebookid = facebookid,
        profile_url = profile_url,
        apikey = apikey,
        collection = collection,
        request_score = request_score,
        embargo = embargo,
    )
    result = open_url(server_address + '/submit', form_fields=form_fields)
    if type(result) is dict:
        guid = result.get('guid','')
        return guid
    else:
        return

def getScores(guid='', username='', ip_address=''):
    """
    Get scores and stats for a specific translator, user or IP address
    """
    if len(guid) > 0:
        return open_url(server_address + '/scores/' + guid)
    elif len(username) > 0:
        return open_url(server_address + '/scores/user/' + username)
    elif len(ip_address) > 0:
        return open_url(server_address + '/scores/user/' + ip_address)
    else:
        return

def submitScore(guid, score, username='', message=''):
    """
    Submit a score for a translation
    """
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
    """
    Get comments about a translation
    """
    form_fields = dict(
        guid = guid,
        language = language,
    )
    return open_url(server_address + '/comments', form_fields=form_fields, method='get')

def submitComment(guid, language='', text='', username='', name=''):
    """
    Submit a comment about a translation
    """
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

def getQuote(jobtype, sl, tl, sla='', username='', words=''):
    """
    Get an instant quote for a translation project. Expects the following parameters:

    jobtype : translation, score or edit
    sl : source language code
    tl : target language code
    sla : service level agreement code
    username : username or ID
    words : word count
    """
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

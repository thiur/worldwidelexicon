"""
Worldwide Lexicon Wrapper Library
Google App Engine Version
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
* runs in the Google App Engine environment

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
from google.appengine.api import memcache
from google.appengine.api import urlfetch
import urllib
import urllib2
import datetime
import codecs
import md5
import string
from transcoder import transcoder
from lsp import LSP
from database import Translation
from mt import MTWrapper

def clean(text):
    return transcoder.clean(text)

memcache_ttl = 600

class wwl():
    """
    This class encapsulates calls to WWL services. It can be configured to interact with
    any public or private WWL server. It implements the following features in the WWL API:

    /t : request a translation
    /submit : submit a translation
    /scores/vote : submit a vote on a translation
    /users/new : create a new WWL account
    /users/auth : authenticate a WWL account and obtain a session key
    
    """
    wwl_servers = ['www.worldwidelexicon.org']
    secure_wwl_servers = ['worldwidelexicon.appspot.com']
    @staticmethod
    def test():
        return wwl.get('en','es','hello world')
    @staticmethod
    def auth(username='', pw='', session=''):
        """
        Use this to authenticate a username/pw pair or session key. Returns a MD5 hash key (session id)
        if successful, and empty string if not. 
        """
        if (len(username) > 0 and len(pw) > 0) or len(session) > 0:
            url = wwl.server(secure=True)
            f = dict()
            if len(username) > 0:
                f['username']=username
                f['pw']=pw
            else:
                f['session']=session
            form_data = urllib.urlencode(f)
            url = wwl.server() + '/users/auth'
            result = urllib2.urlopen(url, form_data)
            tt = result.read()
            return tt
        else:
            return ''
    @staticmethod
    def newuser(username,pw,email,firstname='',lastname='',city='', state='', country='', description=''):
        """
        Use this to create a new user account. Expects the following required parameters:

        username = WWL username
        pw = password
        email = email address

        And the following optional parameters:

        firstname
        lastname
        city
        state
        country
        description

        It returns True or False, and if successful, sends a welcome email to the user asking them to click
        on a link to validate their account. 
        """
        if len(username) > 5 and len(pw) > 5:
            url = wwl.server(secure=True) + '/users/new'
            f = dict()
            f['username']=username
            f['pw']=pw
            f['email']=email
            f['firstname']=firstname
            f['lastname']=lastname
            f['city']=city
            f['state']=state
            f['country']=country
            f['description']=description
            form_data = urllib.urlencode(f)
            result = urllib2.urlopen(url, form_data)
            tt = result.read()
            return tt
        else:
            return False
    @staticmethod
    def getparm(username, parm):
        """
        Gets a parameter for a user, expects the params username and parm, returns a string with the stored
        value
        """
        url = wwl.server() + '/users/get'
        f = dict()
        f['username']=username
        f['parm']=parm
        form_data = urllib.urlencode(f)
        result = urllib2.urlopen(url, form_data)
        tt = result.read()
        return tt
    @staticmethod
    def setparm(username, pw, parm, value):
        """
        Sets a parm=value pair for a user, requires the following params:

        username
        pw
        parm
        value

        Returns True/False on success or failure
        """
        url = wwl.server(secure=True) + '/users/set'
        f = dict()
        f['username']=username
        f['pw']=pw
        f['parm']=parm
        f['value']=value
        form_data = urllib.urlencode(f)
        result = urllib2.urlopen(url, form_data)
        tt = result.read()
        return tt        
    @staticmethod
    def server(secure=False, idx=0):
        """
        Returns a URL for a secure or non-secure WWL server, from the list defined in the library header
        """
        if secure:
            try:
                url = 'https://' + wwl.secure_wwl_servers[idx]
            except:
                url = ''
        else:
            try:
                url = 'http://' + wwl.wwl_servers[idx]
            except:
                url = ''
        return url
    @staticmethod
    def getcache(sl, tl, st):
        """
        Internal method to fetch an item from memcached, if running
        """
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            m = md5.new()
            m.update(sl)
            m.update(tl)
            m.update(st)
            md5hash = str(m.hexdigest())
            tt = memcache.get('wwl|' + md5hash)
            if tt is not None:
                return tt
            else:
                return ''
        else:
            return st
    @staticmethod
    def setcache(sl, tl, st, tt):
        """
        Internal method to store an item in memcache, if running
        """
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0 and len(tt) > 0:
            m = md5.new()
            m.update(sl)
            m.update(tl)
            m.update(st)
            md5hash = str(m.hexdigest())
            tt = memcache.set('wwl|' + md5hash, tt, memcache_ttl)
            return True
        else:
            return False
    @staticmethod
    def get(sl, tl, st, domain='', allow_machine='y', allow_anonymous='y', require_professional = 'n', ip_filter='', lsp='', lspusername='', lsppw='', mtengine=''):
        """
        This function is used to get the best available translation for a text. It expects the following parameters:

        sl = source language (ISO code)
        tl = target language (ISO code)
        st = source text (UTF-8 only!)
        domain = filter results to domain=foo.com
        allow_machine = y/n to allow or hide machine translations
        allow_anonymous = y/n to allow or hide translations from unregistered users
        require_professional = y/n to require professional translations
        ip_filter = limit results to submissions from trusted IP address or pattern
        lsp = language service provider name, if pro translations are desired
        lspusername = username w/ LSP
        lsppw = password or API key for LSP
        mtengine = force selection of specific machine translation engine (e.g. mtengine=google, apertium, moses, worldlingo), default is automatic selection
        """
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            st = clean(st)
            if sl == tl:
                return st
            if len(tl) < 2 or len(tl) > 3:
                return st
            # next query Translation() for cached professional translations
            # next query Translation() for any cached translations
            # store translation in memcache and return
            f = dict()
            f['sl']=sl
            f['tl']=tl
            f['st']=st
            f['domain']=domain
            f['allow_machine']=allow_machine
            f['allow_anonymous']=allow_anonymous
            f['require_professional']=require_professional
            f['ip']=ip_filter
            f['lsp']=lsp
            f['lspusername']=lspusername
            f['lsppw']=lsppw
            f['mtengine']=mtengine
            f['output']='text'
            form_data = urllib.urlencode(f)
            url = wwl.server() + '/t?' + form_data
            try:
                result = urlfetch.fetch(url=url, deadline=2)
                if result.status_code == 200:
                    tt = clean(result.content)
                    return tt
                else:
                    return ''
            except:
                return ''
        else:
            return ''
    @staticmethod
    def submit(sl, tl, st, tt, domain='', url='', username='', pw='', proxy='', share='y'):
        """
        submit()

        Use this to submit a translation to the translation memory. Expects the following params:

        sl = source language code
        tl = target language code
        st = source text (utf 8 encoding)
        tt = translated text (utf 8 encoding)
        domain = domain text is from (e.g. cnn.com)
        url = URL of source page text is from (optional)
        username = WWL username (optional)
        pw = WWL username (optional)
        proxy = y/n, set to y if submissions are being proxied from your web service or gateway
        share = y/n, if set to y, submission may be shared with other WWL translation memories
            (enabled by default)

        Returns True/False on success/failure
        """
        wwl.setcache(sl, tl, st, tt)
        f = dict()
        f['sl']=sl
        f['tl']=tl
        f['st']=st
        f['tt']=tt
        f['domain']=domain
        f['url']=url
        f['username']=username
        f['pw']=pw
        f['proxy']=proxy
        f['share']=share
        form_data = urllib.urlencode(f)
        url = wwl.server() + '/submit'
        result = urllib2.urlopen(url, form_data)
        text = result.read()
        if text == 'ok':
            return True
        else:
            return False
    @staticmethod
    def score(sl, tl, st, tt, votetype, username='', pw='', proxy='n'):
        """
        score()

        submit a score for a translation, expects the following params:

        required:

        sl = source language code
        tl = target language code
        st = source text (utf 8 encoding)
        tt = translated text (utf 8 encoding)
        votetype = up, down, block (to vote to ban user)
        username = WWL username of voter (optional)
        pw = WWL password of voter (optional)
        proxy = y/n (set to y if votes are being proxied via your gateway or service
        remote_addr = user's IP address (in proxy mode)
        """
        m = md5.new()
        m.update(sl)
        m.update(tl)
        m.update(st)
        m.update(tt)
        guid = str(m.hexdigest())
        f = dict()
        f['guid']=guid
        f['votetype']=votetype
        f['username']=username
        f['pw']=pw
        f['proxy']=proxy
        form_data = urllib.urlencode(f)
        url = wwl.server(secure=True) + '/scores/vote'
        result = urllib2.urlopen(url, form_data)
        text = result.read()
        if text == 'ok':
            return True
        else:
            return False

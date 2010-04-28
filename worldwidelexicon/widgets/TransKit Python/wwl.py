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

import urllib
import urllib2
import memcache
import md5
import string
import gettext

memcache_address = ['localhost:2020']
memcache_ttl = 600

gettext_application_domain = 'myapplication'
gettext_base_path = '/gettext/myapplication'

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
    def gt(sl, tl, st):
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            if len(gettext_base_path) > 0:
                gettext.bindtextdomain(gettext_application_domain, gettext_base_path + '/' + tl)
                gettext.textdomain(gettext_application_domain)
                tt = gettext.gettext(st)
                if tt != st:
                    wwl.setcache(sl, tl, st, tt)
                    return tt
                else:
                    return ''
            else:
                return ''
        else:
            return ''
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
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0 and len(memcache_address) > 0:
            m = md5.new()
            m.update(sl)
            m.update(tl)
            m.update(st)
            md5hash = str(m.hexdigest())
            tt = ''
            mc = memcache.Client(memcache_address)
            tt = mc.get(md5hash)
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
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0 and len(tt) > 0 and len(memcache_address) > 0:
            m = md5.new()
            m.update(sl)
            m.update(tl)
            m.update(st)
            md5hash = str(m.hexdigest())
            mc = memcache.Client(memcache_address)
            tt = mc.set(md5hash, tt, memcache_ttl)
            return True
        else:
            return False
    @staticmethod
    def setpresence(wwlusername, pw, username, network, status, languages):
        if len(wwlusername) > 0 and len(pw) > 0 and len(username) > 0 and len(network) > 0 and len(status) > 0:
            f = dict()
            f['wwlusername']=wwlusername
            f['pw']=pw
            f['username']=username
            f['network']=network
            f['status']=status
            if type(languages) is list:
                lt = ''
                for l in languages:
                    lt = lt + l + ','
                languages = lt
            f['languages']=languages
            form_data = urllib.urlencode(f)
            url = wwl.server(secure=True) + '/presence/set'
            result = urllib2.urlopen(url, form_data)
            tt = result.read()
            if tt == 'ok':
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def getpresence(username, network):
        url = wwl.server() + '/presence/get?username=' + username + '&network=' + network
        result = urllib2.urlopen(url)
        tt = result.read()
        return tt
    @staticmethod
    def findtranslators(network, status, languages):
        records = list()
        if type(languages) is list:
            lt = ''
            for l in languages:
                lt = lt + l + ','
            languages = lt
        if len(network) > 0 and len(languages) > 0:
            url = wwl.server() + '/presence/find?network=' + network + '&status=' + status + '&languages=' + languages
            result = urllib2.urlopen(url)
            tt = result.read()
            return string.split(tt, '\n')
        else:
            return ''
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
            # first check memcached, if running
            tt = wwl.getcache(sl, tl, st)
            if len(tt) > 0:
                return tt
            # next check gettext(), if configured
            tt = wwl.gt(sl, tl, st)
            if len(tt) > 0:
                return tt
            # next call out to WWL service, /t web API, to get best available translation
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
            result = urllib2.urlopen(url)
            tt = result.read()
            # if a translation is returned, save it in memcached, if running
            if len(tt) > 0:
                wwl.setcache(sl, tl, st, tt)
            return tt
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
    @staticmethod
    def translatepage(sl, tl, st, mode='html', boundary='\n', domain='', allow_machine='y', allow_anonymous='y', require_professional='n', lsp='', lspusername='', lsppw='', mtengine='', ip_filter=''):
        """
        This convenience function breaks a larger text down into many smaller units for translation.
        This has not been heavily tested, and will be improved to include better html and xml parsing,
        as well as support for other document formats. I generally recommend that you spend some time
        to wire the get() function into your web app rather than try to re-render pages in bulk, as this
        is more error prone.

        The function expects the following parameters:

        sl = source language code
        tl = target language code
        mode = text, html
        boundary = delimiter to use when chunking text
        """
        if len(sl) > 0 and len(tl) > 0 and len(st) > 0:
            texts = string.split(st, boundary)
            if len(texts) > 0:
                tt = ''
                for t in texts:
                    tt = tt + wwl.get(sl, tl, t, domain=domain, allow_machine=allow_machine, allow_anonymous=allow_anonymous, require_professional=require_professional, lsp=lsp, lspusername=lspusername, lsppw=lsppw, ip_filter=ip_filter, mtengine=mtengine)
                    tt = tt + boundary
                return tt
        else:
            return ''

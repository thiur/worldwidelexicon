# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Translations Module (translations.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements classes and data stores to retrieve and save translations and
metadata. This module also encapsulates all calls to translation related data stores.
It is designed to work with Google's App Engine platform, but can be ported relatively
easily to other databases and hosting environments. 

NOTE: this documentation is generated automatically, and directly from the current
version of the WWL source code, via the PyDoc service. Because of the way App
Engine works, the hyperlinks in these files will not work, so your best option
is to print the documentation for offline review.

Copyright (c) 1998-2009, Worldwide Lexicon Inc.
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
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
# import standard Python modules
import sys
import urllib
import string
import md5
import datetime
import codecs
from webappcookie import Cookies
# import WWL modules
from database import Users
from database import Urls

def clean(text):
    try:
        utext = text.encode('utf-8')
    except:
        try:
            utext = text.encode('iso-8859-1')
        except:
            utext = text
    text = utext.decode('utf-8')
    return text

class ProxyController(webapp.RequestHandler):
    """
    /proxy/*

    This web service is used by WWL proxy servers to find out what settings to use for a website.

    
    """
    def get(self, domain):
        self.requesthandler(domain)
    def post(self, domain):
        self.requesthandler(domain)
    def requesthandler(self, domain):
        self.response.headers['Content-Type']='text/plain'
        proxy_api_key = self.request.get('proxy_api_key')
        tl = self.request.get('tl')
        subdomains = string.split(domain,'.')
        if len(subdomains) == 3:
            targetdomain = 'www.' + subdomains[1] + '.' + subdomains[2]
        elif len(subdomains) == 4:
            targetdomain = subdomains[1] + '.' + subdomains[2] + '.' + subdomains[3]
        elif len(subdomains) == 5:
            targetdomain = subdomains[1] + '.' + subdomains[2] + '.' + subdomains[3] + '.' + subdomains[4]
        elif len(subdomains) == 2:
            targetdomain = subdomains[1]
        else:
            targetdomain = ''
        self.response.out.write('targetdomain=' + targetdomain + '\n')
        self.response.out.write('translate=y\n')
        self.response.out.write('languages=all\n')
        self.response.out.write('allow_machine=y\n')
        self.response.out.write('allow_edit=y\n')
        self.response.out.write('allow_anonymous=y\n')
        self.response.out.write('require_professional=n\n')
        if len(proxy_api_key) > -1:
            self.response.out.write('lsp=speaklike\n')
            self.response.out.write('lspusername=foo\n')
            self.response.out.write('lsppw=bar\n')

class ProxyRegister(webapp.RequestHandler):
    """
    /proxy/register

    This web service is used to register a new site with a WWL proxy server via a quick signup process.
    This lives behind a form that is used to submit registration data, and then redirects to an admin
    screen.

    To register, a user provides:

    * Their email address (used as their WWL username)
    * Password (an account is created if they do not already have one)
    * Their main URL (e.g. www.yoursite.com)
    * The language they publish in

    The web service will activate their account and then auto-enable machine translation for all
    subdomains, and will tell the user where to point their subdomains to.

    The user will go to www.worldwidelexicon.org/proxy/admin to manage their services, and will also
    be sent a verification email to unlock their WWL account.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        email = self.request.get('email')
        pw = self.request.get('pw')
        pw2 = self.request.get('pw2')
        domain = self.request.get('domain')
        sl = self.request.get('sl')
        remote_addr = self.request.remote_addr
        success_url = '/proxy/admin'
        error_url = '/proxy/error/login'
        if len(email) < 8 or len(pw) < 6 or len(domain) < 3 or len(sl) < 2:
            self.response.out.write('<form action=/proxy/register method=post>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Email</td><td><input type=text name=email></td></tr>')
            self.response.out.write('<tr><td>Password</td><td><input type=password name=pw></td></tr>')
            self.response.out.write('<tr><td>Confirm Password (For New Account)</td><td><input type=password name=pw2></td></tr>')
            self.response.out.write('<tr><td>Your Domain (www.yoursite.com)</td><td><input type=text name=domain></td></tr>')
            self.response.out.write('<tr><td>Primary Language (use 2/3 letter language code)</td><td><input type=text name=sl maxlength=3></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Signup"></td></tr></form></table>')
        else:
            if pw == pw2 and len(pw) > 5 and len(email) > 0:
                result = Users.new(username=email, email=email, pw=pw, remote_addr=remote_addr)
                if not result:
                    self.redirect(error_url)
                sessioninfo['session']=''
                sessioninfo['username']=''
            else:
                sessioninfo = Users.auth(username=email, pw=pw, session='', remote_addr=remote_addr)
                if sessioninfo is None:
                    self.redirect(error_url)
            cookies = Cookies(self)
            cookies['session']=sessioninfo.get('session')
            self.redirect('/proxy/admin')
        

class ProxyAdmin(webapp.RequestHandler):
    """
    /proxy/admin

    This web service is used to manage translation settings for WWL proxy servers. Website owners can use this tool to:

    * Enable/Disable languages
    * Control machine translation settings
    * Control community translation settings
    * Control professional translation settings

    The control panel provides a similar set of options as the Word Press translator addon. 
    
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        cookies = Cookies(self)
        try:
            session = cookies['session']
        except:
            session = ''
        email = self.request.get('email')
        pw = self.request.get('pw')
        remote_addr = self.request.remote_addr
        if len(session) < 8 and len(email) < 6 and len(pw) < 6:
            self.response.out.write('<h3>Worldwide Lexicon Translation Service</h3><hr>')
            self.response.out.write('<form action=/proxy/admin method=post>')
            self.response.out.write('Email: <input type=text name=email>  <input type=password name=pw> ')
            self.response.out.write('<input type=submit value="OK"></form>')
        elif len(session) < 8:
            sessioninfo = Users.auth(username=email, pw=pw, session='', remote_addr=remote_addr)
            if sessioninfo is not None:
                session = sessioninfo.get('session','')
                cookies['session']=session
            else:
                self.redirect('/proxy/admin')
        else:
            self.response.out.write('<h3>Worldwide Lexicon Translation Service</h3><hr>')
            self.response.out.write('Ipsum orum')

class ProxySubmit(webapp.RequestHandler):
    """
    /proxy/submit

    This API call is used to report to the global translation memory which URLs are being
    viewed in translation (for example on a Word Press site that is using the translation
    plugin). This enables WWL / Der Mundo to build a global picture of what posts are being
    read in various languages.

    It expects the following parameters:

    sl = source language
    tl = target language
    st = source text (can be partial)
    tt = translated text (can be partial)
    domain = main domain
    url = permalink (original)
    turl = permalink (translated)
    stitle = source title
    ttitle = translated title
    remote_addr = user IP address
    
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
        domain = self.request.get('domain')
        url = self.request.get('url')
        turl = self.request.get('turl')
        stitle = self.request.get('stitle')
        ttitle = self.request.get('ttitle')
        remote_addr = self.request.remote_addr
        user_ip = self.request.get('remote_addr')
        exists = memcache.get('/ratelimit/proxy/submit/' + user_ip)
        if exists is not None:
            self.response.out.write('ok')
        else:
            Urls.log(url, turl=turl, domain=domain, sl=sl, tl=tl, st=st, tt=tt, stitle=stitle, ttitle=ttitle, remote_addr = remote_addr, user_ip=user_ip)
            self.response.out.write('ok')
            memcache.set('/ratelimit/proxy/submit/' + user_ip, 'y', 1)

application = webapp.WSGIApplication([('/proxy/submit', ProxySubmit),
                                      ('/proxy/register', ProxyRegister),
                                      (r'/proxy/admin/(.*)', ProxyAdmin),
                                      ('/proxy/admin', ProxyAdmin),
                                      (r'/proxy/(.*)', ProxyController)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

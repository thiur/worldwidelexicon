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
from database import APIKeys
from database import Users
from transcoder import transcoder

def clean(text):
    return transcoder.clean(test)

class ProxyDomains(db.Model):
    domain = db.StringProperty(default='')
    owner = db.StringProperty(default='')
    verified = db.BooleanProperty(default=False)
    verificationcode = db.StringProperty(default='')
    blocked = db.BooleanProperty(default=False)
    createdon = db.DateTimeProperty(auto_now_add=True)
    sl = db.StringProperty(default='')
    description = db.TextProperty(default='')
    tags = db.ListProperty(str)
    lsp = db.StringProperty(default='speaklikeapi')
    lspusername = db.StringProperty(default='')
    lsppw = db.StringProperty(default='')
    @staticmethod
    def add(domain, owner, sl='en', description='', lsp='speaklikeapi', lspusername='', lsppw='', verificationcode=''):
        if len(domain) > 0 and len(owner) > 0:
            domain = string.replace(domain, 'http://', '')
            domain = string.replace(domain, 'https://', '')
            pdb = db.Query(ProxyDomains)
            pdb.filter('domain = ', domain)
            item = pdb.get()
            if item is None:
                if len(verificationcode) < 8:
                    m = md5.new()
                    m.update(str(datetime.datetime.now()))
                    m.update(domain)
                    m.update(owner)
                    verificationcode = str(m.hexdigest())
                item = ProxyDomains()
                item.domain = domain
                item.owner = owner
                item.verificationcode = verificationcode
                item.sl = sl
                item.description = description
                item.lsp = lsp
                item.lspusername = lspusername
                item.lsppw = lsppw
                item.put()
                return True
            else:
                return False
        else:
            return False
    @staticmethod
    def secretcode(domain):
        if len(domain) > 0:
            pdb = db.Query(ProxyDomains)
            pdb.filter('domain = ', domain)
            item = pdb.get()
            if item is not None:
                return item.verificationcode
        return ''
    @staticmethod
    def update(domain, parm, value):
        if len(domain) > 0 and len(parm) > 0 and len(value) > 0:
            pdb = db.Query(ProxyDomains)
            pdb.filter('domain = ', domain)
            item = pdb.get()
            if item is not None:
                if parm == 'lspusername':
                    item.lspusername = value
                if parm == 'lwppw':
                    item.lsppw = value
                if parm == 'description':
                    item.description = description
            else:
                return False
        else:
            return False
    
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
        apikey = self.request.get('apikey')
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
        if len(apikey) > 0:
            result = APIKeys.getusername(apikey)
            if len(result) > 0:
                pdb = db.Query(ProxyDomains)
                pdb.filter('domain = ', targetdomain)
                item = pdb.get()
                if item is not None:
                    self.response.out.write(item.lsp + '\n')
                    self.response.out.write(item.lspusername + '\n')
                    self.response.out.write(item.lsppw + '\n')

class ProxyVerify(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        pdb = db.Query(ProxyDomains)
        pdb.filter('verified = ', False)
        pdb.order('-createdon')
        results = pdb.fetch(limit = 20)
        for r in results:
            url = 'http://' + r.domain
            result = urlfetch.fetch(url = url)
            if result.status_code == 200:
                if string.count(clean(result.content), r.verificationcode) > 0:
                    r.verified = True
                    r.put()
        self.response.out.write('ok')

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
        verificationcode = self.request.get('verificationcode')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        remote_addr = self.request.remote_addr
        success_url = '/hostedtranslationwelcome'
        error_url = '/hostedtranslationerror'
        if pw == pw2 and len(pw) > 5 and len(email) > 0:
            result = Users.new(username=email, email=email, pw=pw, remote_addr=remote_addr)
            ProxyDomains.add(domain, email, sl=sl, lspusername=lspusername, lsppw=lsppw)
        else:
            self.redirect(error_url)
        self.redirect(success_url + '/' + domain)

application = webapp.WSGIApplication([('/proxy/register', ProxyRegister),
                                      ('/proxy/verify', ProxyVerify),
                                      (r'/proxy/(.*)', ProxyController)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

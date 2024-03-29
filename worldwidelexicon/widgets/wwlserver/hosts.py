# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Host Directory (hosts.py)
by Brian S McConnell <brian@worldwidelexicon.org>

OVERVIEW

This module is used in conjunction with the translation proxy server to keep track
of hosts, proxy settings, and subscriptions. This is currently implemented as a
dummy web service for testing purposes. It will implement the following services:

/hosts/auth : authenticates a domain and provides proxy server with settings to
              follow
/hosts/log : logs bandwidth usage, queries, etc for billing purposes

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
# import Google App Engine Modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
# import standard Python libraries
import string
import datetime
import codecs
import urllib
import md5
# import WWL and third party modules
from akismet import Akismet
import demjson
from database import Directory
from database import DirectoryIP
from database import Settings
from database import Users
from www import www

class HostsSubmit(webapp.RequestHandler):
    """
    /hosts/submit

    This request handler is used to process submissions from
    Word Press and other plugins, to build a directory of sites
    and recent publishing activity. It is called once per page
    load on the remote system. It expects the following parameters:

    domain = domain of your website
    url = permalink of the page being viewed
    sl = source language code
    tl = target language code
    title = page title
    ttitle = translated page title
    description = page description or initial block of body text
    tdescription = translated page description
    hosttype = type of host (e.g. wordpress, apache, etc)
    tags = tags (optional)
    apikey = API key (to unlock multiple domains per IP address
                otherwise, only allows one domain per IP address)

    Returns ok or error (if WWL APIKey is provided and is invalid)
    Submissions are also screened by Akismet and other spam filtering
    services. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        remote_addr = self.request.remote_addr
        domain = self.request.get('domain')
        url = self.request.get('url')
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        title = self.request.get('title')
        ttitle = self.request.get('ttitle')
        description = self.request.get('description')
        tdescription = self.request.get('tdescription')
        tags = self.request.get('tags')
        apikey = self.request.get('apikey')
        hosttype = self.request.get('hosttype')
        if len(domain) > 0 and len(url) > 0 and len(sl) > 0 and len(tl) > 0:
            if string.count(url, 'http://') < 1 and string.count(url, 'https://') < 1:
                url = 'http://' + url
            result=Directory.save(remote_addr,domain,url,sl,tl,title,ttitle=ttitle,description=description,tdescription=tdescription,tags=tags,hosttype=hosttype)
            self.response.out.write('ok')
        else:
            www.serve(self,self.__doc__)
            self.response.out.write('<table><form action=/hosts/submit method=get>')
            self.response.out.write('<tr><td>Domain</td><td><input type=text name=domain></td></tr>')
            self.response.out.write('<tr><td>URL</td><td><input type=text name=url></td></tr>')
            self.response.out.write('<tr><td>Source Language Code</td><td><input type=text name=sl></td></tr>')
            self.response.out.write('<tr><td>Target Language Code</td><td><input type=text name=tl></td></tr>')
            self.response.out.write('<tr><td>Title</td><td><input type=text name=title></td></tr>')
            self.response.out.write('<tr><td>Description</td><td><input type=text name=description></td></tr>')
            self.response.out.write('<tr><td>Translated Title</td><td><input type=text name=ttitle></td></tr>')
            self.response.out.write('<tr><td>Translated Description</td><td><input type=text name=tdescription></td></tr>')
            self.response.out.write('<tr><td>Tags</td><td><input type=text name=tags></td></tr>')
            self.response.out.write('<tr><td>Host Type (e.g. wordpress)</td><td><input type=text name=hosttype></td></tr>')
            self.response.out.write('<tr><td>API Key</td><td><input type=text name=apikey></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Submit"></td></tr></table></form>')

class HostsAuth(webapp.RequestHandler):
    """
    /hosts/auth/domain

    This request handler determines if a particular domain is
    valid for use by the proxy server. If yes, it returns the
    source URL to load from, as well as language settings (e.g. whether
    to use professional translation or not). If it is not a valid
    domain it returns an error message.
    """
    def get(self, domain):
        dtxts = string.split(domain, '.')
        if len(dtxts) == 3 and dtxts[0] != 'www':
            realdomain = 'www.' + dtxts[1] + '.' + dtxts[2]
        elif len(dtxts) == 3 and dtxts[0] == 'www':
            realdomain = 'www2.' + dtxts[1] + '.' + dtxts[2]
        elif len(dtxts) == 2:
            realdomain = 'www.' + dtxts[0] + '.' + dtxts[1]
        else:
            realdomain = domain
            
        self.response.headers['Content-Type']='text/plain'
        self.response.out.write('ok\n' + realdomain)

class HostsLog(webapp.RequestHandler):
    """
    /hosts/log

    Logs usage data for a website, including number of requests, and
    bandwidth usage. This is used to calculate monthly billing for websites
    on premium rate accounts, and to throttle free users who are
    overconsuming resources.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        self.response.headers['Content-Type']='text/plain'
        self.response.out.write('ok\n')

class HostsRegister(webapp.RequestHandler):
    """
    /hosts/register

    This request handler allows a new user to quickly register a website to
    use the translation proxy server. It asks the user to provide his WWL
    account credentials, and basic information about the website (e.g. domain,
    languages to support, etc). It then provisions the user with a free account
    which can be accessed at languagecode.sitenickname.worldwidelexicon.org.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        domain = self.request.get('domain')
        username = self.request.get('username')
        pw = self.request.get('pw')
        title = self.request.get('title')
        description = self.request.get('description')
        sl = self.request.get('sl')

class HostsUpdate(webapp.RequestHandler):
    """
    /hosts/update

    This request handler allows a website owner to update the translation
    settings for their domain (e.g. which languages to use professional
    translation for, etc). It accepts a list of parameters, and redirects
    the user to one of the defined callback URLs, so it can easily be placed
    behind any web form. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        pass
      
application = webapp.WSGIApplication([(r'/hosts/auth/(.*)', HostsAuth),
                                      ('/hosts/submit', HostsSubmit),
                                      ('/hosts/log', HostsLog)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()


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
#
# import Google App Engine modules
#
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
#
# import standard Python modules
#
import string
import md5
import datetime
import time
import pydoc
import codecs
import types
#
# import WWL and third party modules
#
from deeppickle import DeepPickle
from mt import MTWrapper
from webappcookie import Cookies
from www import www
from database import BlackList

def clean(text):
    return transcoder.clean(text)

class DomainBlackList(webapp.RequestHandler):
    """
    <h3>/blacklist/domain</h3>

    Returns a list of blacklisted users or IP addresses, in simple text file with one entry per
    line, separated by a new line. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        domain = self.request.get('domain')
        if len(domain) > 0:
            # placeholder for call to Blacklist() data store
            results = list()
            bl = list()
            for r in results:
                if r.authorip not in bl and len(r.authorip) > 0:
                    bl.append(authorip)
                if r.author not in bl and len(r.author) > 0:
                    bl.append(authorip)
            bl.sort()
            self.response.headers['Content-Type']='text/plain'
            for b in bl:
                self.response.out.write(b + '\n')
        else:
            t = '<table><form action=/blacklist/domain method=get>'
            t = t + '<tr><td>Domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'

class AddToBlackList(webapp.RequestHandler):
    """
    <h3>/blacklist/add</h3>'

    This web service is called to add someone to a user's personal blacklist. It
    expects the following parameters:<p>

    <ul>
    <li>domain (e.g. foo.com)</li>
    <li>user : username or IP to blacklist</li>
    <li>requester : username or IP of requester</li>
    </ul>

    It replies with ok or an error message.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        domain = self.request.get('domain')
        user = self.request.get('user')
        requester = self.request.get('requester')
        remote_addr = self.request.remote_addr
        if len(domain) > 0 and len(user) > 0:
            Blacklist.add(domain=domain, user=user, requester=requester, remote_addr=remote_addr)
            self.request.get('ok')
        else:
            t = '<table><form action=/blacklist/add method=get>'
            t = t + '<tr><td>Domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>Username or IP to block</td><td><input type=text name=user></td></tr>'
            t = t + '<tr><td>Username or IP of requester</td><td><input type=text name=requester></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar=self.__doc__, title = '/blacklist/remove')

class RemoveFromBlackList(webapp.RequestHandler):
    """
    <h3>/blacklist/remove</h3>'

    This web service is called to remove someone from a user's personal blacklist. It
    expects the following parameters:<p>

    <ul>
    <li>domain (e.g. foo.com)</li>
    <li>user : username or IP to blacklist</li>
    <li>requester : username or IP of requester</li>
    </ul>

    It replies with ok or an error message.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        domain = self.request.get('domain')
        user = self.request.get('user')
        requester = self.request.get('requester')
        remote_addr = self.request.get('remote_addr')
        if len(domain) > 0 and len(user) > 0:
            BlackList.remove(domain=domain, user=user, requester=requester, remote_addr=remote_addr, tl=tl)
            self.request.get('ok')
        else:
            t = '<table><form action=/blacklist/remove method=get>'
            t = t + '<tr><td>Domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>Username or IP to unblock</td><td><input type=text name=user></td></tr>'
            t = t + '<tr><td>Username or IP of requester</td><td><input type=text name=requester></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar=self.__doc__, title = '/blacklist/remove')

class MyBlackList(webapp.RequestHandler):
    """
    <h3>/blacklist/my</h3>

    This web service returns a list of blacklisted IPs and usernames that have been flagged
    by a specific username or IP address. This enables the system to remember who a specific
    user has blacklisted so their translations are knocked out of search results. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        domain = self.request.get('domain')
        requester = self.request.get('requester')
        if len(domain) > 0 and len(requester) > 0:
            results = BlackList.my(domain=domain,requester=requester)
            if results is not None:
                self.response.headers['Content-Type']='text/plain'
                for r in results:
                    self.response.out.write(r + '\n')
            else:
                self.response.out.write('')
        else:
            t = '<table><form action=/blacklist/my method=get>'
            t = t + '<tr><td>Domain</td><td><input type=text name=domain></td></tr>'
            t = t + '<tr><td>Username or IP</td><td><input type=text name=user></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar=self.__doc__, title='/blacklist/my')
        
application = webapp.WSGIApplication([('/blacklist/domain', DomainBlackList),
                                      ('/blacklist/my', MyBlackList),
                                      ('/blacklist/add', AddToBlackList),
                                      ('/blacklist/remove', RemoveFromBlackList)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Rate Limiting and IP Blocking Tools (ip.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements a number of rate limiting and IP address blocking rules.
This provides WWL request handlers with an easy way to screen, and if needed,
block requests. 

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
import datetime
import time
import pydoc

class ip(db.Model):
    """
    This library defines a data store that tracks blocked and trusted IP
    addresses, and provides a simple call to check to see if an IP address
    is either blocked or rate limited. This allows web service request
    handlers to block or throttle requests that are too frequent. For
    example, WWL does not rate limit reads from the /t and /q web services
    since these are often called by automated services, while calls to
    /submit and other request handlers are rate limited, on the assumption
    that if translations are being posted more than about once per second
    from the same IP address that this is likely to be robotic activity. 
    """
    remote_addr = db.StringProperty(default='')
    updated = db.DateTimeProperty(auto_now_add = True)
    blocked = db.BooleanProperty()
    trusted = db.BooleanProperty()
    @staticmethod
    def allow(remote_addr, action='', ttl=1):
        """
        Checks to see if a request from an IP address should be allowed or not.
        Expects remote_addr, and two optional parameters:
        action = label for the action or web service (e.g. submit_translation)
        ttl = time to live for rate limit (default = 1 second)

        Returns True (allow) or False (deny)
        """
        if len(remote_addr) > 0:
            if memcache.get('/ratelimit/' + remote_addr + '/' + action):
                return False
            else:
                memcache.set('/ratelimit/' + remote_addr + '/' + action, True, ttl)
                return True
            status = memcache.get('/blocked/' + remote_addr)
            if status is not None:
                return status
            else:
                idb = db.Query(ip)
                idb.filter('remote_addr = ', remote_addr)
                item = idb.get()
                if item is None:
                    memcache.set('/blocked/' + remote_addr, False, 3600)
                    return True
                elif item.blocked:
                    memcache.set('/blocked/' + remote_addr, True, 3600)
                    return False
                else:
                    memcache.set('/blocked/' + remote_addr, False, 3600)
                    return True
        else:
            return True
    @staticmethod
    def block(remote_addr):
        """
        Adds an IP address to the permanent blacklist
        """
        if len(remote_addr) > 0:
            idb = db.Query(ip)
            idb.filter('remote_addr = ', remote_addr)
            item = idb.get()
            if item is None:
                item = BlackList()
                item.remote_addr = remote_addr
            item.updated = datetime.datetime.now()
            item.blocked = True
            item.put()
            memcache.set('/blocked/' + remote_addr, True, 3600)
            return True
        else:
            return False

class RateLimit(webapp.RequestHandler):
    def get(self):
        remote_addr = self.request.remote_addr
        action = 'test'
        ttl = 10
        if ip.allow(remote_addr, action=action, ttl=ttl):
            self.response.out.write('ok')
        else:
            self.response.clear()
            self.response.set_status(500)

application = webapp.WSGIApplication([('/ratelimit', RateLimit)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

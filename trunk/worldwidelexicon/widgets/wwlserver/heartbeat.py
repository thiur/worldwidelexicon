# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
System Heartbeat (heartbeat.py)
by Brian S McConnell <brian@worldwidelexicon.org>

OVERVIEW

This module does a self-check on critical systems, and if it detects a fault
with either the memcache or data store subsystems, it sets a flag so that the
system can go into a repair/downtime mode. 

Copyright (c) 1998-2010, Worldwide Lexicon Inc.
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
# import WWL and third party modules
from database import Settings
from www import www

class SanityCheck(db.Model):
    timestamp = db.DateTimeProperty(auto_now_add = True)

class HeartBeat(webapp.RequestHandler):
    def get(self):
        test = self.request.get('test')
        if test != 'y':
            # first test memcache
            memcache_running = False
            text = memcache.get('/heartbeat/memcache')
            if text is None:
                try:
                    memcache.set('/heartbeat/memcache', True, 300)
                    text = memcache.get('/heartbeat/memcache')
                    if text is not None:
                        memcache_running = True
                except:
                    memcache_running = False
            else:
                memcache_running = True
            # next test a DB write
            try:
                item = SanityCheck()
                item.put()
                db_write = True
            except:
                db_write = False
            # next test a DB read
            try:
                tdb = db.Query(SanityCheck)
                tdb.order('-timestamp')
                item = tdb.get()
                db_read = True
            except:
                db_read = False
            # next test a UrlFetch
            try:
                urlfetch.fetch('http://www.google.com')
                url_fetch = True
            except:
                url_fetch = False
            # next update the heartbeat registry
            if memcache_running and db_write and db_read:
                memcache.set('/heartbeat/running', True, 300)
                self.response.out.write('ok')
            else:
                memcache.delete('/heartbeat/running')
                self.response.out.write('error')
        else:
            running = memcache.get('/heartbeat/running')
            if running is not None:
                self.response.out.write('ok')
            else:
                self.response.out.write('error')
        
application = webapp.WSGIApplication([('heartbeat', HeartBeat)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()


# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Translations Module (downtime.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module displays a system down message. 

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
class SystemDown(webapp.RequestHandler):
    def get(self, p1='', p2='', p3='', p4=''):
        self.requesthandler()
    def post(self, p1='', p2='', p3='', p4=''):
        self.requesthandler()
    def requesthandler(self):
        self.error(500)
        self.response.out.write('<h3>System Down</h3>')
        self.response.out.write('The Worldwide Lexicon will be offline for several hours today due to ')
        self.response.out.write('scheduled system maintenence at Google App Engine. During this time all ')
        self.response.out.write('services will return errors until App Engine scheduled maintenence is completed.')

application = webapp.WSGIApplication([('/', SystemDown),
                                       (r'/(.*)', SystemDown),
                                       (r'/(.*)/(.*)', SystemDown),
                                       (r'/(.*)/(.*)/(.*)', SystemDown)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

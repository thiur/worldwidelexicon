# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Multilingual Content Management System
Content Management System / Web Server (wwl.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module serves page and document requests, and is the primary module used to
render pages, blog posts, RSS feeds, etc. 

Copyright (c) 1998-2009, Worldwide Lexicon Inc, Brian S McConnell. 
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
# import standard Python modules
import codecs
import datetime
import md5
import string
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.labs import taskqueue
# import WWL modules
from database import languages
from database import Settings
from database import Users
# import third party modules
from webappcookie import Cookies

# Define default settings
encoding = 'utf-8'

class Login(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
                greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                            (user.nickname(), users.create_logout_url("/admin")))
            else:
                greeting = ("Sorry, %s, you must be an administrator to access this module. (<a href=\"%s\">sign out</a>)" %
                            (user.nickname(), users.create_logout_url("/admin")))
        else:
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/admin"))

        self.response.out.write("<html><body>" + greeting + "</body></html>")

class Variables(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            self.response.out.write('<h3>System Variables</h3>')
            self.response.out.write('Use this form to create, edit and delete persistent system or environment variables.')
            self.response.out.write('<table border=1>')
            self.response.out.write('<tr><td>Name</td><td>Value</td><td></td></tr>')
            sdb = db.Query(Settings)
            sdb.order('name')
            results = sdb.fetch(200)
            for r in results:
                self.response.out.write('<tr valign=top><td>' + r.name + '</td><td>')
                self.response.out.write('<form action=/admin/setvar method=get>')
                self.response.out.write('<input type=hidden name=name value="' + r.name + '">')
                self.response.out.write('<input type=text name=value value="' + r.value + '">')
                self.response.out.write('</td><td><input type=submit value=Save></form></td></tr>')
            self.response.out.write('<tr valign=top><td><form action=/admin/setvar method=get>New Row: <input type=text name=name></td>')
            self.response.out.write('<td><input type=text name=value></td>')
            self.response.out.write('<td><input type=submit value=Create></form></td></tr></table>')
        else:
            self.redirect('/admin')

class SetVariable(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            name = self.request.get('name')
            value = self.request.get('value')
            if len(name) > 0:
                Settings.save(name, value, user=user.nickname())
            self.redirect('/admin/vars')
        else:
            self.redirect('/admin')

class Robots(webapp.RequestHandler):
    def get(self):
        self.response.out.write('User-agent: *\n')
        self.response.out.write('Disallow: /cgi/')

class Headers(webapp.RequestHandler):
    def get(self):
        headers = self.request.headers
        headerkeys = headers.keys()
        headerkeys.sort()
        for h in headerkeys:
            self.response.out.write(h + ' : ' + headers[h] + '<br>')

application = webapp.WSGIApplication([('/admin', Login),
                                      ('/admin/vars', Variables),
                                      ('/admin/setvar', SetVariable),
                                      ('/headers', Headers),
                                      ('/robots.txt', Robots)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()

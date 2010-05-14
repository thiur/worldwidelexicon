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
from database import APIKeys
from database import languages
from database import Languages
from database import Settings
from database import Users
from mt import MT
# import third party modules
from webappcookie import Cookies

# Define default settings
encoding = 'utf-8'

def header():
    t = '<head><title>Worldwide Lexicon</title>'
    t = t + '<link rel="stylesheet" href="/static/2col.css" type="text/css">'
    t = t + '</head><body>'
    t = t + '<div class="header">'
    t = t + '<h1>Worldwide Lexicon Control Panel</h1>'
    t = t + '</div>'
    t = t + '<div class="colmask rightmenu"><div class="colleft">'
    return t

def footer():
    t = right_menu()
    t = t + '</div></div><div class="footer">'
    t = t + '(c) 1998-2010 Brian S McConnell, <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Inc</a></div>'
    return t

def is_admin():
    user = users.get_current_user()
    if users.is_current_user_admin():
        return True
    else:
        return False

def right_menu():
    t = '<div class="col2">'
    t = t + '<h4><a href=/admin/setup>Quick Install</a></h4>'
    t = t + '<h4><a href=/admin/keys>Manage API Keys</a></h4>'
    t = t + '<h4><a href=/admin/languages>Languages</a></h4>'
    t = t + '<h4><a href=/admin/mt>Machine Translation</a></h4>'
    t = t + '<h4><a href=/admin/vars>System Variables</a></h4>'
    t = t + '</div>'
    return t

class Login(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if is_admin():
            self.response.out.write(header())
            self.response.out.write('<div class="col1">')
            greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                            (user.nickname(), users.create_logout_url("/admin")))
            self.response.out.write(greeting)
            self.response.out.write('</div>')
            self.response.out.write(footer())
            return
        elif user:
            greeting = ("Sorry, %s, you must be an administrator to access this module. (<a href=\"%s\">sign out</a>)" %
                            (user.nickname(), users.create_logout_url("/admin")))
        else:
            greeting = ("<a href=\"%s\">Sign in or register</a>." %
                        users.create_login_url("/admin"))
        self.response.out.write("<html><body>" + greeting + "</body></html>")

class Variables(webapp.RequestHandler):
    def get(self):
        if is_admin():
            self.response.out.write(header())
            self.response.out.write('<div class="col1">')
            self.response.out.write('<h3>System Variables</h3>')
            self.response.out.write('Use this form to create, edit and delete persistent system or environment variables.')
            self.response.out.write('<br><br><table>')
            self.response.out.write('<tr><td><b>Name</b></td><td><b>Value</b></td><td></td></tr>')
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
            self.response.out.write('<td><input type=submit value=Create></form></td></tr></table></div>')
            self.response.out.write(footer())
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

class ViewAPIKeys(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            results = APIKeys.fetch()
            self.response.out.write(header())
            self.response.out.write('<div class="col1">')
            self.response.out.write('Use this interface to manage Language Service providers and their API keys.')
            self.response.out.write('<form action=/admin/makekey method=get><table>')
            self.response.out.write('<tr><td>Username or Nickname</td><td><input type=text name=username></td></tr>')
            self.response.out.write('<tr><td>Web Service URL</td><td><input type=text name=url></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Make Key"></td></tr></table></form>')
            self.response.out.write('<hr><table border=1>')
            self.response.out.write('<tr><td>Username</td><td>Hashkey</td><td>Web Service URL</td><td></td></tr>')
            for r in results:
                self.response.out.write('<tr><td>' + r.username + '</td><td>' + r.guid + '</td>')
                self.response.out.write('<td>' + r.url + '</td>')
                self.response.out.write('<td><a href=/admin/deletekey?guid=' + r.guid + '>Delete Key</a></td></tr>')
            self.response.out.write('</table></div>')
            self.response.out.write(footer())
        else:
            self.redirect('/admin')

class DeleteAPIKey(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            guid = self.request.get('guid')
            if len(guid) > 8:
                result = APIKeys.remove(guid)
            self.redirect('/admin/keys')
        else:
            self.redirect('/admin')

class MakeAPIKey(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin():
            username = self.request.get('username')
            url = self.request.get('url')
            if len(username) > 0:
                result = APIKeys.add(username, url=url)
            self.redirect('/admin/keys')
        else:
            self.redirect('/admin')

class ManageLanguages(webapp.RequestHandler):
    def get(self):
        if is_admin():
            self.response.out.write(header())
            self.response.out.write('<div class="col1">')
            self.response.out.write('<h2>Manage Languages</h2>')
            self.response.out.write('<table')
            results = Languages.find()
            for r in results:
                self.response.out.write('<tr><td>' + r.name + ' ('+ r.code + ')</td>')
                self.response.out.write('<td><a href=/admin/deletelanguage?code=' + r.code + '>Delete</a></td></tr>')
            self.response.out.write('</table>')
            self.response.out.write('<hr>')
            self.response.out.write('<h3>Add Language</h3>')
            self.response.out.write('<form action=/admin/addlanguage method=get>')
            self.response.out.write('<table><tr><td>Language Code (2-3 Letter ISO Code</td>')
            self.response.out.write('<td><input type=text name=code maxlength=3></td></tr>')
            self.response.out.write('<tr><td>Native Name</td><td><input type=text name=name></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Add Language"></td></tr>')
            self.response.out.write('</form></table>')
            self.response.out.write('</div>')
            self.response.out.write(footer())
        else:
            self.redirect('/admin')

class AddLanguage(webapp.RequestHandler):
    def get(self):
        if is_admin():
            code = self.request.get('code')
            name = self.request.get('name')
            Languages.add(code,name)
            self.redirect('/admin/languages')
        else:
            self.redirect('/admin')

class DeleteLanguage(webapp.RequestHandler):
    def get(self):
        if is_admin():
            code = self.request.get('code')
            Languages.remove(code)
            self.redirect('/admin/languages')
        else:
            self.redirect('/admin')

class ManageMachineTranslation(webapp.RequestHandler):
    def get(self):
        if is_admin:
            self.response.out.write(header())
            self.response.out.write('<div class="col1">')
            self.response.out.write('<h3>Machine Translation Settings</h3>')
            self.response.out.write('<table>')
            self.response.out.write('<form action=/admin/mt method=post>')
            self.response.out.write('<tr><td>Default Translation Engine</td>')
            self.response.out.write('<input type=hidden name=langpair value=default>')
            self.response.out.write('<td>' + MT.select() + '</td>')
            self.response.out.write('</td><td><input type=submit value="Save"></td></tr></form>')
            self.response.out.write('<tr><td>Google API Key (optional)</td><td>')
            self.response.out.write('<form action=/admin/mt method=post>')
            googleapikey = Settings.get('googleapikey')
            self.response.out.write('<input type=text name=googleapikey value="' + googleapikey + '"></td>')
            self.response.out.write('<td><input type=submit value="Save"></td></tr></form>')
            self.response.out.write('<tr><td>WorldLingo Subscription</td><td>')
            worldlingosubscription = Settings.get('worldlingosubscription')
            self.response.out.write('<form action=/admin/mt method=post>')
            self.response.out.write('<input type=text name=worldlingosubscription value="' + worldlingosubscription + '"></td>')
            self.response.out.write('<td></td></tr>')
            worldlingopw = Settings.get('worldlingopw')
            self.response.out.write('<tr><td>WorldLingo password</td>')
            self.response.out.write('<td><input type=text name=worldlingopw value="' + worldlingopw + '"></td>')
            self.response.out.write('<td><input type=submit value="Save"></td></tr></form>')
            self.response.out.write('</table>')
            self.response.out.write('<hr>')
            self.response.out.write('<h3>Language Settings</h3>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Language Pair</td><td>Translation Engine</td><td></td></tr>')
            results = MT.find()
            if len(results) > 0:
                for r in results:
                    self.response.out.write('<tr><td>' + r.langpair + '</td>')
                    self.response.out.write('<td>' + r.mtengine + '</td>')
                    self.response.out.write('<td><a href=/admin/deletemt?langpair=' + r.langpair + '>Delete</a></td></tr>')
            self.response.out.write('</table>')
            self.response.out.write('<h3>Add New Language Pair</h3>')
            self.response.out.write('<table><form action=/admin/mt method=post>')
            self.response.out.write('<tr><td>Source Language Code</td><td><input type=text name=sl></td></tr>')
            self.response.out.write('<tr><td>Target Language Code</td><td><input type=text name=tl></td></tr>')
            self.response.out.write('<tr><td>Translation Engine</td><td>' + MT.select() + '</td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Save"></td></tr></table></form>')
            self.response.out.write('</div>')
            self.response.out.write(footer())
        else:
            self.redirect('/admin')
    def post(self):
        if is_admin:
            googleapikey = self.request.get('googleapikey')
            worldlingosubscription = self.request.get('worldlingosubscription')
            worldlingopw = self.request.get('worldlingopw')
            sl = self.request.get('sl')
            tl = self.request.get('tl')
            langpair = self.request.get('langpair')
            mtengine = self.request.get('mtengine')
            if len(googleapikey) > 0:
                Settings.set('googleapikey', googleapikey)
            elif len(worldlingosubscription) > 0 and len(worldlingopw) > 0:
                Settings.set('worldlingosubscription', worldlingosubscription)
                Settings.set('worldlingopw', worldlingopw)
            elif len(sl) > 0 and len(tl) > 0 and len(mtengine) > 0:
                MT.add(sl, tl, mtengine)
            elif langpair == 'default':
                MT.add(langpair,langpair,mtengine)
            self.redirect('/admin/mt')
        else:
            self.redirect('/admin')

class DeleteMTEngine(webapp.RequestHandler):
    def get(self):
        if is_admin:
            langpair = self.request.get('langpair')
            if len(langpair) > 3:
                MT.remove(langpair)
            self.redirect('/admin/mt')
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

class Setup(webapp.RequestHandler):
    def get(self):
        if is_admin():
            self.response.out.write(header())
            self.response.out.write('<div class="col1">')
            self.response.out.write('<h2>Worldwide Lexicon Quick Setup</h2>')
            self.response.out.write('<table><form action=/admin/setup method=post>')
            title = Settings.get('title')
            if len(title) < 1:
                title = 'Worldwide Lexicon Server'
            self.response.out.write('<tr><td>Website Title</td><td><input type=text name=title value="' + title + '"></td></tr>')
            self.response.out.write('<tr><td>Root URL</td><td><input type=text name=root_url value="' + Settings.get('root_url') + '"></td></tr>')
            primary_language = Settings.get('primary_language')
            if len(primary_language) < 1:
                primary_language = 'en'
            self.response.out.write('<tr><td>Primary Language</td><td><select name=primary_language>' + languages.select(selected=primary_language) + '</select></td></tr>')
            self.response.out.write('<tr><td><a href=http://www.akismet.com>Akismet</a> Anti-Spam Key</td><td><input type=text name=akismet value="' + Settings.get('akismet') + '"></td></tr>')
            self.response.out.write('<tr><td><a href=http://www.maxmind.com>Maxmind Geolocation</a> Key</td><td><input type=text name=maxmind value="' + Settings.get('maxmind') + '"></td></tr>')
            self.response.out.write('<tr><td><a href=http://www.google.com/analytics>Google Analytics</a> Key</td><td><input type=text name=googleanalytics value="' + Settings.get('googleanalytics') + '"></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Save"></td></tr>')
            self.response.out.write('</table></form>')
            self.response.out.write('</div>')
            self.response.out.write(footer())
        else:
            self.redirect('/admin')
    def post(self):
        if is_admin():
            title = self.request.get('title')
            root_url = self.request.get('root_url')
            primary_language = self.request.get('primary_language')
            akismet = self.request.get('akismet')
            maxmind = self.request.get('maxmind')
            googleanalytics = self.request.get('googleanalytics')
            if len(title) > 0:
                Settings.save('title', title)
            if len(root_url) > 0:
                if string.count(root_url, 'http://') < 1:
                    root_url = 'http://' + root_url
                Settings.save('root_url', root_url)
            if len(primary_language) > 1:
                Settings.save('primary_language', primary_language)
            if len(akismet) > 1:
                Settings.save('akismet', akismet)
            if len(maxmind) > 1:
                Settings.save('maxmind', maxmind)
            if len(googleanalytics) > 1:
                Settings.save('googleanalytics', googleanalytics)
            self.redirect('/admin/setup')
        else:
            self.redirect('/admin')

class Status(webapp.RequestHandler):
    def get(self):
        self.response.out.write(Settings.get('status'))

application = webapp.WSGIApplication([('/admin', Login),
                                      ('/admin/addlanguage', AddLanguage),
                                      ('/admin/deletelanguage', DeleteLanguage),
                                      ('/admin/deletemt', DeleteMTEngine),
                                      ('/admin/keys', ViewAPIKeys),
                                      ('/admin/languages', ManageLanguages),
                                      ('/admin/makekey', MakeAPIKey),
                                      ('/admin/mt', ManageMachineTranslation),
                                      ('/admin/deletekey', DeleteAPIKey),
                                      ('/admin/vars', Variables),
                                      ('/admin/setup', Setup),
                                      ('/admin/setvar', SetVariable),
                                      ('/headers', Headers),
                                      ('/status', Status),
                                      ('/robots.txt', Robots)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()

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
from database import AccessControlList
from database import APIKeys
from database import languages
from database import Languages
from database import Settings
from database import Users
from ui import TextObjects
# import third party modules
from webappcookie import Cookies

# Define default settings
encoding = 'utf-8'

def header():
    t = '<head><title>Worldwide Lexicon</title>'
    t = t + '<link rel="stylesheet" href="/dermundocss/2col.css" type="text/css">'
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
    t = t + '<h4><a href=/admin/acl>Access Control Rules</a></h4>'
    t = t + '<h4><a href=/admin/languages>Languages</a></h4>'
    t = t + '<h4><a href=/admin/memcache>Memcache Statistics</a></h4>'
    t = t + '<h4><a href=/admin/vars>System Variables</a></h4>'
    t = t + '<h4><a href=/admin/texts>Texts and Blog Posts</a></h4>'
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
        
class DisplayTexts(webapp.RequestHandler):
    def get(self):
        if is_admin():
            self.response.out.write(header())
            stats = memcache.get_stats()
            self.response.out.write('<div class="col1">')
            self.response.out.write('<h3>Texts</h3>')
            results = TextObjects.getall()
            if results is not None:
                self.response.out.write('<table width=100% border=1>')
                self.response.out.write('<tr><td>Label/Title</td><td>Text</td><td>IsBlog</td><td></td></tr>')
                for r in results:
                    self.response.out.write('<tr><td>' + r.label + '</td>')
                    self.response.out.write('<td>' + r.text + '</td>')
                    if r.blog:
                        self.response.out.write('<td>y</td>')
                    else:
                        self.response.out.write('<td>n</td>')
                    self.response.out.write('<td></td></tr>')
                self.response.out.write('</table><hr>')
            self.response.out.write('<h3>Add/Update Text</h3>')
            self.response.out.write('<form action=/admin/savetext method=get>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Label/Title</td><td><input type=text name=label></td></tr>')
            self.response.out.write('<tr><td colspan=2>Text<br><textarea name=text rows=6 cols=60></textarea></td></tr>')
            self.response.out.write('<tr><td>Is This A Blog Post?</td><td>')
            self.response.out.write('<select name=blog><option selected value=n>No</option>')
            self.response.out.write('<option value=y>Yes</option></select></td></tr>')
            self.response.out.write('<tr><td>Language</td><td><input type=text name=language value=en></td></tr>')
            self.response.out.write('<tr><td></td><td><input type=submit value=Save></td></tr>')
            self.response.out.write('</table></form></div>')
            self.response.out.write(footer())
        else:
            self.redirect('/admin')

class SaveText(webapp.RequestHandler):
    def get(self):
        if is_admin():
            label = self.request.get('label')
            text = self.request.get('text')
            blog = self.request.get('blog')
            language = self.request.get('language')
            if blog == 'y':
                blog = True
            else:
                blog = False
            if len(label) > 0 and len(text) > 0:
                TextObjects.save(label, text, blog=blog)
                self.redirect('/admin/texts')
            else:
                self.redirect('/admin/texts')
        else:
            self.redirect('/admin')

class MemcacheStats(webapp.RequestHandler):
    def get(self):
        if is_admin():
            self.response.out.write(header())
            stats = memcache.get_stats()
            self.response.out.write('<div class="col1">')
            self.response.out.write('<h3>Memcache Statistics</h3>')
            self.response.out.write('<table>')            
            self.response.out.write('<tr><td>Number of Items</td><td>' + str(stats['items']) + '</td></tr>')
            self.response.out.write('<tr><td>Hits</td><td>' + str(stats['hits']) + '</td></tr>')
            self.response.out.write('<tr><td>Misses</td><td>' + str(stats['misses']) + '</td></tr>')
            self.response.out.write('<tr><td>Bytes</td><td>' + str(stats['bytes']) + '</td></tr>')
            self.response.out.write('<tr><td>Oldest Item</td><td>' + str(stats['oldest_item_age']) + ' seconds</td></tr>')
            self.response.out.write('<tr><td>Average Item Size</td><td>' + str(float(stats['bytes'])/stats['items']) + ' bytes</td></tr>')
            self.response.out.write('<tr><td colspan=2><a href=/admin/memcachereset>Clear and Reset Cache</a></td></tr>')
            self.response.out.write('</table></div>')
            self.response.out.write(footer())
        else:
            self.redirect('/admin')

class MemcacheReset(webapp.RequestHandler):
    def get(self):
        if is_admin:
            memcache.flush_all()
            self.redirect('/admin/memcache')
        else:
            self.redirect('/admin')

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

class ViewAccessControlList(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin:
            self.response.out.write(header())
            self.response.out.write('<div class="col1">')
            self.response.out.write('<h3>Create A Rule Or Filter</h3>')
            self.response.out.write('<table border=1><form action=/admin/acl/set method=get>')
            self.response.out.write('<tr><td>Filter By</td><td>Action</td><td>Value</td></tr>')
            self.response.out.write('<tr><td><select name=rule>')
            self.response.out.write('<option value=ipaddress>IP Address/Range</option>')
            self.response.out.write('<option value=language>Language</option>')
            self.response.out.write('<option value=username>Username/Email</option>')
            self.response.out.write('<option value=country>Country</option>')
            self.response.out.write('</select></td>')
            self.response.out.write('<td><select name=value>')
            self.response.out.write('<option value=allow>Allow</option>')
            self.response.out.write('<option value=deny>Deny</option>')
            self.response.out.write('</select></td>')
            self.response.out.write('<td><input type=text name=parm></td></tr>')
            self.response.out.write('<tr><td colspan=3><input type=submit value="Create Rule"></td></tr>')
            self.response.out.write('</form></table>')
            results = AccessControlList.viewrules()
            if len(results) > 0:
                self.response.out.write('<hr><h3>Existing Rules</h3>')
                self.response.out.write('<table border=1>')
                self.response.out.write('<tr><td>Filter By</td><td>Action</td><td>Value</td><td></td></tr>')
                for r in results:
                    self.response.out.write('<tr><td>' + r.rule + '</td>')
                    self.response.out.write('<td>' + r.value + '</td>')
                    self.response.out.write('<td>' + r.parm + '</td>')
                    self.response.out.write('<td><a href=/admin/acl/delete?guid=' + r.guid + '>delete rule</a></td></tr>')
                self.response.out.write('</table>')
            self.response.out.write('</div>')
            self.response.out.write(footer())
        else:
            self.redirect('/admin')

class SaveAccessControlList(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin:
            rule = self.request.get('rule')
            value = self.request.get('value')
            parm = self.request.get('parm')
            if len(rule) > 0 and len(value) > 0 and len(parm) > 0:
                AccessControlList.addrule(rule,value,parm)
            self.redirect('/admin/acl')
        else:
            self.redirect('/admin')

class DeleteAccessControlList(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user and users.is_current_user_admin:
            guid = self.request.get('guid')
            if len(guid) > 0:
                AccessControlList.deleterule(guid)
            self.redirect('/admin/acl')
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
                                      ('/admin/acl', ViewAccessControlList),
                                      ('/admin/acl/set', SaveAccessControlList),
                                      ('/admin/acl/delete', DeleteAccessControlList),
                                      ('/admin/addlanguage', AddLanguage),
                                      ('/admin/deletelanguage', DeleteLanguage),
                                      ('/admin/keys', ViewAPIKeys),
                                      ('/admin/languages', ManageLanguages),
                                      ('/admin/makekey', MakeAPIKey),
                                      ('/admin/memcache', MemcacheStats),
                                      ('/admin/memcachereset', MemcacheReset),
                                      ('/admin/texts', DisplayTexts),
                                      ('/admin/savetext', SaveText),
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

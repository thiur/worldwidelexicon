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
import sys
reload(sys); sys.setdefaultencoding('utf-8')
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
from google.appengine.api.labs import taskqueue
# import WWL modules
from database import CSS
from database import Feeds
from database import Images
from database import languages
from database import Objects
from database import Settings
from database import Users
from database import Websites
# import third party modules
import feedparser
from webappcookie import Cookies

# Define default settings

encoding = 'utf-8'

default_title = 'Welcome to the Worldwide Lexicon'

default_css = 'default'

standard_footer = 'Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2009 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  WWL multilingual CMS and translation memory is open source software published \
                  under a BSD style license.'

translation_server = 'http://www.dermundo.com'

nicedit = '<script src="http://js.nicedit.com/nicEdit-latest.js" type="text/javascript"></script>\
<script type="text/javascript">bkLib.onDomLoaded(nicEditors.allTextAreas);</script>'

default_css = 'blueprint'

# Define default settings for Blueprint CSS framework, included with this package as the default style sheet

blueprint_header='<link rel="stylesheet" href="/blueprint_overrides.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/screen.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/print.css" type="text/css" media="print">\
            <link rel="stylesheet" href="/blueprint/plugins/fancy-type/screen.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/plugins/link-icons/screen.css" type="text/css" media="screen, projection">\
            <!--[if IE]><link rel="stylesheet" href="/blueprint-css/blueprint/ie.css" type="text/css" media="screen, projection"><![endif]-->'

blueprint_container = '<div class="container"><hr class="space">'

blueprint_wide = '<div class="span-15 prepend-1 colborder">'

blueprint_sidebar = '<div class="span-7 last">'

class ControlPanel(webapp.RequestHandler):
    isroot = True
    admin = list()
    author = list()
    translator = list()
    trustedtranslator = list()
    loggedin = True
    username = 'worldwidelex'
    session = 'xyz123'
    def get(self, p1='', p2='', p3=''):
        headers=self.request.headers
        website = headers.get('Host','')
        if len(p2) > 0:
            website = p1
            page = p2
        else:
            if headers.get('Host','') != p1:
                website = p1
                page = ''
            else:
                page = p1
        referrer = self.request.referrer
        # validate user via session cookie, get user permissions
        cookies = Cookies(self)
        session = cookies.get('session','')
        username = ''
        if len(session) > 0:
            username = memcache.get('sessions|' + session)
            if username is None:
                username = ''
        if len(username) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                self.loggedin = True
                self.session = session
                self.username = username
                if item.root:
                    self.isroot = True
                if type(item.admin) is list:
                    self.admin = item.admin
                if type(item.author) is list:
                    self.author = item.author
                if type(item.translator) is list:
                    self.translator = item.translator
                if type(item.trustedtranslator) is list:
                    self.trustedtranslator = item.trustedtranslator
        self.response.out.write('<head><title>Control Panel</title>')
        self.response.out.write(blueprint_header)
        self.response.out.write('</head>')
        self.response.out.write(blueprint_container)
        self.response.out.write('<h1>' + website + ' : Control Panel</h1>')
        self.response.out.write(blueprint_wide)
        if not self.loggedin:
            self.login(website)
            return
        if len(page) < 1:
            self.indexpage(website)
            self.sidebar(website)
        elif page == 'write':
            self.write(website,page=p3)
            self.sidebar(website)
        elif page == 'domains':
            self.domains(website)
            self.sidebar(website)
        elif page == 'edit':
            self.write(website,page=p3)
            self.sidebar(website)
        elif page == 'feeds':
            self.feeds(website)
            self.sidebar(website)
        elif page == 'images':
            self.images(website)
            self.sidebar(website)
        elif page == 'news':
            self.news(website)
            self.sidebar(website)
        elif page == 'users':
            self.users(website)
            self.sidebar(website)
        elif page == 'posts':
            self.posts(website)
            self.sidebar(website)
        elif page == 'languages':
            prompt = 'Select Languages'
            strings = None
            texts = None
            langlist=languages.getlist()
            langkeys=langlist.keys()
            langkeys.sort()
            booleans=dict()
            for l in langkeys:
                booleans['language.' + l]=langlist[l]
            self.menu(website, strings, booleans, texts, prompt)
            self.sidebar(website)
        elif page == 'tools':
            strings = dict()
            strings['maxmindapi'] = 'Maxmind Geolocation Key'
            strings['googleanalytics'] = 'Google Analytics API Key'
            strings['bitlyusername'] = 'Bit.ly Username'
            strings['bitlyapi'] = 'Bit.ly API Key'
            strings['akismetapi'] = 'Akismet Spam Filter API Key'
            booleans=None
            texts=None
            self.menu(website,strings,booleans,texts)
            self.sidebar(website)
        elif page == 'socialmedia':
            strings = dict()
            strings['twitter'] = 'Twitter Username'
            strings['skype'] = 'Skype Username'
            strings['facebookurl'] = 'Facebook URL'
            booleans = None
            texts = None
            self.menu(website,strings,booleans,texts)
            self.sidebar(website)
        else:
            self.sidebar(website)
        self.response.out.write('<hr>')
        self.response.out.write(standard_footer)
        self.response.out.write('</div>')
    def create(self):
        self.response.out.write('<h2>Create A Website</h2>')
        self.response.out.write('<table><form action=/admin/create method=post>')
        self.response.out.write('<tr><td>Hostname (www.foo.com)</td><td><input type=text name=host size=20></td></tr>')
        self.response.out.write('<tr><td>Title</td><td><input type=text name=title size=20></td></tr>')
        self.response.out.write('<tr><td>Primary Language You Publish In</td><td><select name=language>')
        self.response.out.write(languages.select())
        self.response.out.write('</select></td></tr>')
        self.response.out.write('<tr><td colspan=2>Description<br><textarea name=description rows=4 cols=80></textarea></td></tr>')
        self.response.out.write('<tr><td colspan=2><input type=submit value="Create Website"></td></tr>')
        self.response.out.write('</form></table>')
    def domains(self, website):
        if len(website) > 0:
            self.response.out.write('<h3>Domain Mapping</h3>')
            wdb = db.Query(Websites)
            wdb.filter('host = ', website)
            item = wdb.get()
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Alt Domain or Subdomain</td><td>Action</td></tr>')
            if item is not None:
                altnames = item.alt
                for a in altnames:
                    self.response.out.write('<tr><td>' + a + '</td><td><form action=/domains/' + website + ' method=post>')
                    self.response.out.write('<input type=hidden name=domain value="' + a + '">')
                    self.response.out.write('<select name=action>')
                    self.response.out.write('<option value=""></option>')
                    self.response.out.write('<option value=delete>Delete Domain</option>')
                    self.response.out.write('</select>')
                    self.response.out.write('</td><td><input type=submit value=OK></form></td></tr>')
            self.response.out.write('<form action=/domains/' + website + ' method=post>')
            self.response.out.write('<input type=hidden name=action value=save>')
            self.response.out.write('<tr><td>Add Domain/Subdomain</td><td><input type=text name=domain></td>')
            self.response.out.write('<td><input type=submit value=OK></td></tr></form>')
            self.response.out.write('</table>')
    def images(self, website=''):
        idb = db.Query(Images)
        idb.filter('website = ', website)
        results = idb.fetch(limit=200)
        x = 0
        self.response.out.write('<table>')
        self.response.out.write('<form action=/upload/' + website + ' enctype="multipart/form-data" method=post>')
        self.response.out.write('<tr><td>Title</td><td><input type=text name=title></td></tr>')
        self.response.out.write('<tr><td>Upload File</td><td><input type=file name=image></td></tr>')
        self.response.out.write('<tr><td colspan=2><input type=submit value=OK></form></td></tr></table>')
        self.response.out.write('<table>')
        for r in results:
            x = x + 1
            if x == 1:
                self.response.out.write('<tr>')
            self.response.out.write('<td><img src=/images/' + website + '/' + r.name + '?thumbnail=y></td>')
            if x == 8:
                self.response.out.write('</tr>')
                x = 1
        self.response.out.write('</table>')
    def indexpage(self, host):
        self.websites()
    def login(self, website=''):
        self.response.out.write('<h3>Not Logged In</h3>')
        self.response.out.write('Please login to manage ' + website + '<p>')
        self.response.out.write('<table><form action=/admin/login method=post>')
        self.response.out.write('<input type=hidden name=website value="' + website + '">')
        self.response.out.write('<tr><td>Username</td><td><input type=text name=username></td></tr>')
        self.response.out.write('<tr><td>Password</td><td><input type=password name=pw></td></tr>')
        self.response.out.write('<tr><td colspan=2><input type=submit value="Login"></td></tr>')
        self.response.out.write('</table></form>')
    def feeds(self, website=''):
        if len(website) > 0:
            self.response.out.write('<h3>Add a News Feed</h3>')
            self.response.out.write('<table><form action=/admin/rss method=post>')
            self.response.out.write('<input type=hidden name=action value=addfeed>')
            self.response.out.write('<input type=hidden name=website value="' + website + '">')
            self.response.out.write('<tr><td>RSS Feed URL</td><td><input type=text name=rssurl></td></tr>')
            self.response.out.write('<tr><td>Title (optional)</td><td><input type=text name=title></td></tr>')
            self.response.out.write('<tr><td>Primary Language</td><td><select name=language>')
            self.response.out.write(languages.select())
            self.response.out.write('</select></td></tr>')
            self.response.out.write('<tr><td colspan=2>Description (optional)<br><textarea name=description></textarea></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Add Feed"></td></tr>')
            self.response.out.write('</form></table>')
            fdb = db.Query(Feeds)
            fdb.filter('website = ', website)
            results = fdb.fetch(limit=50)
            if results is not None:
                self.response.out.write('<h3>Manage Feeds</h3>')
                self.response.out.write('<table>')
                self.response.out.write('<tr><td>Title</td><td>Auto Publish</td><td>Actions</td></tr>')
                for r in results:
                    self.response.out.write('<tr><td>' + r.title + '</td>')
                    if r.autopublish:
                        self.response.out.write('<td>Yes</td>')
                    else:
                        self.response.out.write('<td>No</td>')
                    self.response.out.write('<td></td>')
                    self.response.out.write('</tr>')
                self.response.out.write('</table>')
            
    def menu(self, website='', strings=None, booleans=None, texts=None, prompt=''):
        if len(website) > 0:
            if len(prompt) > 0:
                self.response.out.write('<h2>' + prompt + '</h2>')
            if type(strings) is dict or type(booleans) is dict or type(texts) is dict:
                self.response.out.write('<table><form action=/admin/set/' + website + ' method=post>')
            if type(strings) is dict:
                fields = strings.keys()
                profile = Websites.profile(website,fields)
                fields.sort()
                for f in fields:
                    v = profile.get(f,'')
                    self.response.out.write('<tr><td>' + strings[f] + '</td><td><input type=text name="' + f + '" value="' + v + '"></td></tr>')
            if type(booleans) is dict:
                fields = booleans.keys()
                profile = Websites.profile(website,fields)
                fields.sort()
                for f in fields:
                    try:
                        v = profile[f]
                    except:
                        v = False
                    self.response.out.write('<tr><td>' + booleans[f] + '</td>')
                    self.response.out.write('<td><select name="' + f + '">')
                    if v:
                        self.response.out.write('<option selected value=y>Yes</option>')
                        self.response.out.write('<option value=n>No</option>')
                    else:
                        self.response.out.write('<option selected value=n>No</option>')
                        self.response.out.write('<option value=y>Yes</option>')
                    self.response.out.write('</select></td></tr>')
            if type(texts) is dict:
                fields = texts.keys()
                profile = Websites.website(fields)
                fields.sort()
                for f in fields:
                    self.response.out.write('<tr><td colspan=2>' + texts[f] + '<br>')
                    self.response.out.write('<textarea name="' + f + '">' + profile[f] + '</textarea></td></tr>')
            if type(strings) is dict or type(booleans) is dict or type(texts) is dict:
                self.response.out.write('<tr><td colspan=2><center><input type=submit value="Save Settings"></center></td></tr>')
                self.response.out.write('</form></table>')
    def news(self, website='', rssurl=''):
        if len(rssurl) < 1:
            rssurl = self.request.get('rssurl')
        odb = db.Query(Objects)
        odb.filter('website = ', website)
        if len(rssurl) > 0:
            odb.filter('rssurl = ', rssurl)
        odb.order('-created')
        results = odb.fetch(limit=100)
        if results is not None:
            self.response.out.write('<h3>Recent News Items</h3>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Source</td><td>Title</td><td>Actions</td></tr>')
            for r in results:
                if r.news:
                    source = r.rssurl
                    if source is not None:
                        source = string.replace(source, 'http://', '')
                        feedurl = string.split(source, '/')
                        source = feedurl[0]
                    else:
                        source = ''
                    self.response.out.write('<tr><td>' + source + '</td><td>' + r.title + '</td>')
                    self.response.out.write('<td><form action=/update/' + website + ' method=post>')
                    self.response.out.write('<input type=hidden name=guid value="' + r.guid + '">')
                    self.response.out.write('<select name=action>')
                    if r.published:
                        self.response.out.write('<option value=unpublish>Unpublish</option>')
                        self.response.out.write('<option value=feature>Feature Item</option>')
                        self.response.out.write('<option value=unfeatured>Unfeature Item</option>')
                    else:
                        self.response.out.write('<option value=publish>Publish Item</option>')
                        self.response.out.write('<option value=feature>Feature Item</option>')
                        self.response.out.write('<option value=unfeature>Unfeature Item</option>')
                    self.response.out.write('</select></td>')
                    self.response.out.write('<td><input type=submit value=OK></form></td></tr>')
            self.response.out.write('</table>')
    def post(self, p1='', p2=''):
        headers = self.request.headers
        website = headers.get('Host')
        if len(p2) > 0:
            website = p1
            page = p2
        else:
            page = p1
        if page == 'create':
            hostname = self.request.get('host')
            title = self.request.get('title')
            description = self.request.get('description')
            language = self.request.get('language')
            langs = list()
            if len(language) > 0:
                langs.append(language)
            result = Websites.create(hostname, title, description, langs)
            self.redirect('/' + hostname + '/' + language + '/')
    def posts(self, p1='', p2=''):
        headers = self.request.headers
        referrer = self.request.referrer
        website = headers.get('Host')
        if len(p2) > 0:
            website = p1
            page = p2
        else:
            website = p1
            page = ''
        if len(website) > 0:
            self.response.out.write('<h3>Your Posts</h3>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Title</td><td>Author</td><td></td><td>Published</td><td>Featured</td><td>Action</td></tr>')
            rdb = db.Query(Objects)
            rdb.filter('website = ', website)
            rdb.order('-created')
            results = rdb.fetch(limit=100)
            for r in results:
                skiprecord = False
                if r.news:
                    skiprecord = True
                if not skiprecord:
                    self.response.out.write('<tr><td>' + r.title + '</td><td>' + r.author + '</td>')
                    self.response.out.write('<td><a href=/admin/' + website + '/edit/' + r.name + '>Edit</a></td>')
                    self.response.out.write('<td>')
                    if r.published:
                        self.response.out.write('Yes')
                    else:
                        self.response.out.write('No')
                    self.response.out.write('</td><td>')
                    if r.featured:
                        self.response.out.write('Yes')
                    else:
                        self.response.out.write('No')
                    self.response.out.write('<td><table><tr><td><form action=/update/' + website + '/' + r.name + ' method=post>')
                    self.response.out.write('<select name=action><option selected value=""></option>')
                    self.response.out.write('<option value=delete>Delete</option>')
                    self.response.out.write('<option value=feature>Feature Post</option>')
                    self.response.out.write('<option value=publish>Publish </option>')
                    self.response.out.write('<option value=unfeature>Remove Feature</option>')
                    self.response.out.write('<option value=unpublish>Unpublish</option>')
                    self.response.out.write('</select></td><td>')
                    self.response.out.write('<input type=submit value=OK></form></td></tr></table></td></tr>')
            self.response.out.write('</table>')
        else:
            self.redirect(referrer)
    def sidebar(self, website='', pages=None):
        self.response.out.write('</div>')
        self.response.out.write(blueprint_sidebar)
        if pages is None:
            self.response.out.write('<h3><a href=/admin/' + website + '/>Main Control Panel</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/write>Write A Page Or Post</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/posts>Manage Your Posts</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/images>Manage Images</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/users>Manage Users</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/feeds>Manage News Feed Subscriptions</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/news>Manage Incoming News</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/domains>Domain Mapping</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/languages>Languages</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/socialmedia>Social Media</a></h3>')
            self.response.out.write('<h3><a href=/admin/' + website + '/tools>Website Tools and Analytics</a></h3>')
        elif type(pages) is dict:
            pkeys = pages.keys()
            pkeys.sort()
            for p in pkeys:
                self.response.out.write('<h3><a href=/admin/' + website + '/' + p + '>' + pages[p] + '</a></h3>')
        self.response.out.write('</div>')
    def users(self, website):
        if len(website) > 0:
            self.response.out.write('<h3>Add A User</h3>')
            self.response.out.write('<form action=/admin/saveuser/' + website + '/add method=post>')
            self.response.out.write('<input type=hidden name=action value=save>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Username</td><td>Password (if new account)</td><td>Author</td><td>Translator</td><td>Admin</td></tr>')
            self.response.out.write('<tr><td><input type=text name=username></td>')
            self.response.out.write('<td><input type=password name=pw></td>')
            self.response.out.write('<td><input type=checkbox name=author value=y checked></td>')
            self.response.out.write('<td><input type=checkbox name=translator value=y></td>')
            self.response.out.write('<td><input type=checkbox name=admin value=y></td>')
            self.response.out.write('<td><input type=submit value="OK"></td></tr>')
            self.response.out.write('</table></form>')
            self.response.out.write('<h3>Manage Users</h3>')
            self.response.out.write('<table>')
            self.response.out.write('<tr><td>Username</td><td>Author</td><td>Translator</td><td>Admin</td></tr>')
            udb = db.Query(Users)
            udb.filter('websites = ', website)
            results = udb.fetch(limit = 200)
            for r in results:
                if website in r.author:
                    author = 'Yes'
                else:
                    author = 'No'
                if website in r.translator:
                    translator = 'Yes'
                else:
                    translator = 'No'
                if website in r.admin:
                    admin = 'Yes'
                else:
                    admin = 'No'
                self.response.out.write('<tr><td><a href=/admin/' + website + '/users/' + r.username + '>' + r.username + '</a></td>')
                self.response.out.write('<td><form action=/admin/saveuser/' + website + '/' + r.username + ' method=post>')
                self.response.out.write('<input type=hidden name=action value=save>')
                self.response.out.write('<select name=author>')
                if author == 'Yes':
                    self.response.out.write('<option selected value=y>Yes</option>')
                    self.response.out.write('<option value=n>No</option>')
                else:
                    self.response.out.write('<option selected value=n>No</option>')
                    self.response.out.write('<option value=y>Yes</option>')
                self.response.out.write('</select></td>')
                self.response.out.write('<td><select name=translator>')
                if translator == 'Yes':
                    self.response.out.write('<option selected value=y>Yes</option>')
                    self.response.out.write('<option value=n>No</option>')
                else:
                    self.response.out.write('<option selected value=n>No</option>')
                    self.response.out.write('<option value=y>Yes</option>')
                self.response.out.write('</select></td>')
                self.response.out.write('<td><select name=admin>')
                if admin == 'Yes':
                    self.response.out.write('<option selected value=y>Yes</option>')
                    self.response.out.write('<option value=n>No</option>')
                else:
                    self.response.out.write('<option selected value=n>No</option>')
                    self.response.out.write('<option value=y>Yes</option>')
                self.response.out.write('</select></td>')
                self.response.out.write('<td><input type=submit value="Save"></form></td>')
                self.response.out.write('<td><form action=/admin/saveuser/' + website + '/' + r.username + ' method=post>')
                self.response.out.write('<input type=hidden name=action value=delete>')
                self.response.out.write('<input type=submit value="Delete"></form></td></tr>')
            self.response.out.write('</table>')
    def websites(self):
        self.response.out.write('<h2>Your Websites</h2>')
        wdb = db.Query(Websites)
        wdb.order('title')
        results = wdb.fetch(limit=100)
        for r in results:
            self.response.out.write('<h3><a href=/admin/' + r.host + '>' + r.title + '</a></h3>')
            self.response.out.write('<em>' + codecs.encode(r.description, encoding) + '</em>')
    def write(self, website='', page=''):
        self.response.out.write(nicedit)
        self.response.out.write('<h3>Create New Page or Post</h3>')
        title = ''
        name = ''
        author = ''
        sl = ''
        description = ''
        content = ''
        taglist = ''
        divid = ''
        divclass = ''
        if len(page) > 0:
            self.response.out.write('<form action=/update/' + website + '/' + page + ' method=post>')
            p = Objects.get(website, page)
            if p is not None:
                name = p.get('name', '')
                title = p.get('title', '')
                description = p.get('description','')
                content = p.get('content','')
                sl = p.get('sl','')
                tags = p.get('tags')
                author = p.get('author')
                divid = p.get('divid')
                divclass = p.get('divclass')
        else:
            self.response.out.write('<form action=/update/' + website + ' method=post>')
        self.response.out.write('<input type=hidden name=action value=save>')
        self.response.out.write('<table>')
        self.response.out.write('<tr><td>Name/Shortcut for Page</td><td><input type=text name=name value="' + name + '"></td></tr>')
        self.response.out.write('<tr><td>Title</td><td><input type=text name=title value="' + title + '"></td></tr>')
        self.response.out.write('<tr><td>Author</td><td><input type=text name=author value="' + author + '"></td></tr>')
        self.response.out.write('<tr><td>Language</td><td><select name=sl>')
        self.response.out.write(languages.select(sl))
        self.response.out.write('</select></td></tr>')
        self.response.out.write('<tr><td colspan=2><b>Body</b><br><textarea rows=10 cols=80 name=content>' + content + '</textarea></td></tr>')
        self.response.out.write('<tr><td>Tags</td><td><input type=text name=tags value="' + taglist + '"></td></tr>')
        self.response.out.write('<tr><td>Div ID (for custom styles)</td><td><input type=text name=divid></td></tr>')
        self.response.out.write('<tr><td>Div Class (for custom styles)</td><td><input type=text name=divclass></td></tr>')
        self.response.out.write('<tr><td>This is a blog post</td><td><input type=checkbox value=y checked></td></tr>')
        self.response.out.write('<tr><td>Feature this page</td><td><input type=checkbox value=y></td></tr>')
        self.response.out.write('<tr><td>Publish immediately</td><td><input type=checkbox checked value=y></td></tr>')
        self.response.out.write('<tr><td colspan=2><input type=submit value="Save Page"></td></tr>')
        self.response.out.write('</form></table>')
            
class EditCSS(webapp.RequestHandler):
    def get(self, page='', language=''):
        self.response.headers['Content-Type']='text/html'
        self.response.out.write('<head><title>Edit CSS : ' + page + '</title>')
        self.response.out.write('</head>')
        self.response.out.write('<h2>Edit : ' + page + '</h2>')
        object = CSS.edit(page, language)
        title = ''
        description = ''
        owner = ''
        text = ''
        divid = ''
        divclass = ''
        if type(object) is dict:
            title = object.get('title', '')
            description = object.get('description', '')
            owner = object.get('owner', '')
            text = object.get('text', '')
            divid = object.get('divid', '')
            divclass = object.get('divclass', '')
        self.response.out.write('<form action=/editcss/' + page + '/' + language + ' method=post>')
        self.response.out.write('<table>')
        self.response.out.write('<tr><td>Title</td><td><input type=text name=title></td></tr>')
        self.response.out.write('<tr><td>Owner</td><td><input type=text name=owner></td></tr>')
        self.response.out.write('<tr><td colspan=2>Description<br><textarea name=description rows=6 cols=80></textarea></td></tr>')
        self.response.out.write('<tr><td colspan=2>Text<br><textarea name=text rows=10 cols=80></textarea></td></tr>')
        self.response.out.write('<tr><td colspan=2><input type=submit value="Save CSS Stylesheet"></td></tr>')
        self.response.out.write('</table></form>')
    def post(self, page='', language=''):
        title = self.request.get('title')
        owner = self.request.get('owner')
        description = self.request.get('description')
        text = self.request.get('text')
        divid = self.request.get('divid')
        divclass = self.request.get('divclass')
        object = dict()
        object['title'] = title
        object['owner'] = owner
        object['description'] = description
        object['text'] = text
        object['divid'] = divid
        object['divclass'] = divclass
        result = CSS.save(page, language, object)
        if result:
            self.response.out.write('CSS updated, via the file at <a href=/css/' + page + '/' + language + '>/css/' + page + '/' + language + '</a>')
        else:
            self.response.out.write('Error')
            
class HeartBeat(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        result = Settings.heartbeat()
        self.response.out.write(result)
        
class Login(webapp.RequestHandler):
    def post(self):
        username = self.request.get('username')
        pw = self.request.get('pw')
        remote_addr = self.request.remote_addr
        if len(username) > 0 and len(pw) > 0:
            sessinfo = Users.auth(username, pw, '', remote_addr)
            if type(sessinfo) is dict:
                cookies = Cookies(self, max_age=15000)
                cookies['session'] = sessinfo.get('session','')
                memcache.set('sessions|' + sessinfo.get('session',''), sessinfo.get('username',''), 15000)
                self.redirect('/admin')
            else:
                self.redirect('/admin/login')
        else:
            self.redirect('/admin/login')
            
class RSSSave(webapp.RequestHandler):
    def post(self):
        referrer = self.request.referrer
        website = self.request.get('website')
        action = self.request.get('action')
        rssurl = self.request.get('rssurl')
        title = self.request.get('title')
        description = self.request.get('description')
        language = self.request.get('language')
        autopublish = self.request.get('autopublish')
        if action == 'addfeed':
            validfeed = False
            text = ''
            if autopublish == 'n':
                autopublish = False
            else:
                autopublish = True
            if len(rssurl) > 0:
                if string.count(rssurl, 'http://') < 1:
                    rssurl = 'http://' + rssurl
                response = urlfetch.fetch(url = rssurl)
                if response.status_code == 200:
                    text = response.content
            r = feedparser.parse(text)
            if r is not None:
                f = r.feed
                if len(f.get('title','')) > 0:
                    title = f.get('title', '')
                if len(f.get('description', '')) > 0:
                    description = f.get('description', '')
                if len(f.get('language', '')) > 0:
                    language = f.get('language', '')
                validfeed = True
            if validfeed:
                result = Feeds.add(website, rssurl, title = title, description = description, language=language, autopublish=autopublish)
        elif action == 'markitem':
            guid = self.request.get('guid')
            published = self.request.get('published')
            delete = self.request.get('delete')
            featured = self.request.get('featured')
            odb = db.Query(Objects)
            odb.filter('website = ', website)
            odb.filter('guid = ', guid)
            item = odb.get()
            if item is not None:
                if published == 'y':
                    item.published = True
                else:
                    item.published = False
                if featured == 'y':
                    item.featured = True
                else:
                    item.featured = False
                if delete == 'y':
                    item.delete()
                else:
                    item.put()
        elif action == 'deletefeed':
            if len(website) > 0 and len(rssurl) > 0:
                result = Feeds.delete(website, rssurl)
                result = Objects.purge(website, rssurl)
        else:
            pass
        self.redirect(referrer)
            
class SaveUserPrefs(webapp.RequestHandler):
    def post(self, website='', username=''):
        referrer = self.request.referrer
        action = self.request.get('action')
        if username == 'add':
            username = self.request.get('username')
            pw = self.request.get('pw')
        if len(website) > 0 and len(username) > 0:
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                if action == 'delete':
                    websites = item.websites
                    try:
                        websites.remove(website)
                    except:
                        pass
                    item.websites = websites
                    admin = item.admin
                    try:
                        admin.remove(website)
                    except:
                        pass
                    item.admin = admin
                    translator = item.translator
                    try:
                        translator.remove(website)
                    except:
                        pass
                    item.translator = translator
                    trustedtranslator = item.trustedtranslator
                    try:
                        trustedtranslator.remove(website)
                    except:
                        pass
                    item.trustedtranslator = trustedtranslator
                    item.put()
                elif action == 'save':
                    validquery=True
                    author = self.request.get('author')
                    translator = self.request.get('translator')
                    admin = self.request.get('admin')
                    udb = db.Query(Users)
                    udb.filter('username = ', username)
                    item = udb.get()
                    if item is None:
                        item = Users()
                        if len(pw) < 1:
                            validquery = False
                        m = md5.new()
                        m.update(pw)
                        pwhash = str(m.hexdigest())
                        item.username = username
                        item.pwhash = pwhash
                    websites = item.websites
                    if website not in websites:
                        websites.append(website)
                        item.websites = websites
                    websites = item.admin
                    if admin == 'y':
                        if website not in websites:
                            websites.append(website)
                            item.admin = websites
                    if admin == 'n':
                        if website in websites:
                            websites.remove(website)
                            item.admin = websites
                    websites = item.author
                    if author == 'y':
                        if website not in websites:
                            websites.append(website)
                            item.author = websites
                    if author == 'n':
                        if website in websites:
                            websites.remove(website)
                            item.author = websites
                    websites = item.translator
                    if translator == 'y':
                        if website not in websites:
                            websites.append(website)
                            item.translator = websites
                    if translator == 'n':
                        if website in websites:
                            websites.remove(website)
                            item.translator = websites
                    if validquery:
                        item.put()
                    self.redirect('/admin/' + website + '/users')
                elif action == 'languages':
                    pass
                    # save language permissions
            self.redirect(referrer)
        else:
            self.redirect(referrer)
        
class Setup(webapp.RequestHandler):
    def get(self):
        rootuser = Settings.get('rootuser', 'all')
        if len(rootuser) > 0:
            self.response.out.write('Root account already created. <a href=/admin>Login to the admin console</a> to update system settings.')
        else:
            self.response.out.write('<h3>Create A Root Account</h3>')
            self.response.out.write('<form action=/setup method=post>')
            self.response.out.write('Root Username: <input type=text name=username size=20><p>')
            self.response.out.write('Password: <input type=password name=pw size=20><p>')
            self.response.out.write('Confirm Password: <input type=password name=pw2 size=20><p>')
            self.response.out.write('<input type=submit value="Create Account"></form>')
    def post(self):
        username=self.request.get('username')
        pw = self.request.get('pw')
        pw2 = self.request.get('pw2')
        if len(username) > 5 and len(pw) > 5 and pw == pw2:
            m = md5.new()
            m.update(pw)
            pwhash = str(m.hexdigest())
            Settings.save('rootuser', username, 'all')
            Settings.save('rootpwhash', pw, 'all')
            Users.addroot(username, pw)
            self.response.out.write('<h3>Success!</h3>')
            self.response.out.write('You may now manage your system at <a href=/admin>the admin console</a>')
        else:
            self.response.out.write('<h3>Invalid Username or Password</h3>')
            self.response.out.write('The root username and password must be at least 6 characters long.')
            self.response.out.write('<a href=/setup>Try again</a>.')

class SetValue(webapp.RequestHandler):
    def get(self, p1='', p2=''):
        self.requesthandler(p1,p2)
    def post(self, p1='', p2=''):
        self.requesthandler(p1, p2)
    def requesthandler(self,p1='', p2=''):
        headers = self.request.headers
        website = headers.get('Host')
        referrer = self.request.referrer
        arguments = self.request.arguments()
        website = p1
        parms = dict()
        for a in arguments:
            parm = a
            value = self.request.get(a)
            if len(parm) > 0:
                if value == 'y' or value=='Y':
                    value=True
                if value == 'n' or value=='N':
                    value=False
            parms[a] = value
        result = Websites.set(website, parms)
        if len(referrer) > 0:
            self.redirect(referrer)
        else:
            self.redirect('/admin')
    
class TestHeaders(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        headers = self.request.headers
        self.response.headers['Content-Type']='text/html'
        headerfields = headers.keys()
        headerfields.sort()
        for h in headerfields:
            self.response.out.write(h + ' = ' + headers[h] + '<p>')
        self.response.out.write('\nRequest Object\n\n')
        self.response.out.write('Referrer = ' + self.request.referrer)
        self.response.out.write('<p>')
        parms = self.request.arguments()
        self.response.out.write(str(parms))
        self.response.out.write('<p>')
        self.response.out.write('<form action=/headers method=post>')
        self.response.out.write('<input type=text name=parm1><br>')
        self.response.out.write('<input type=text name=parm2><br>')
        self.response.out.write('<input type=checkbox name=checkbox1 value=y><br>')
        self.response.out.write('<input type=submit value="OK"></form>')
        
class UpdatePage(webapp.RequestHandler):
    def get(self, p1='', p2=''):
        self.requesthandler(p1,p2)
    def post(self, p1='', p2=''):
        self.requesthandler(p1,p2)
    def requesthandler(self, p1='', p2=''):
        headers = self.request.headers
        referrer = self.request.referrer
        host = headers.get('Host', '')
        remote_addr = self.request.remote_addr
        title = self.request.get('title')
        content = self.request.get('content')
        language = self.request.get('language')
        tags = self.request.get('tags')
        action = self.request.get('action')
        guid = self.request.get('guid')
        if len(p2) < 1:
            page = self.request.get('name')
        else:
            page = p2
        if len(p1) > 0:
            if action == 'save':
                headers = self.request.headers
                host = headers.get('Host','')
                referrer = self.request.referrer
                name = self.request.get('name')
                title = self.request.get('title')
                author = self.request.get('author')
                sl = self.request.get('sl')
                description = self.request.get('description')
                content = self.request.get('content')
                taglist = self.request.get('taglist')
                divid = self.request.get('divid')
                divclass = self.request.get('divclass')
                blog = self.request.get('blog')
                featured = self.request.get('featured')
                publishnow = self.request.get('publish')
                website = p1
                if len(page) < 1:
                    page = string.replace(title, ' ', '')
                    page = string.replace(page, '\'', '')
                    page = string.replace(page, '\"', '')
                    page = string.replace(page, '&', '')
                    page = string.replace(page, '.', '')
                    page = string.replace(page, ',', '')
                    page = string.replace(page, ':', '')
                    page = string.replace(page, ';', '')
                    page = string.lower(page)
                    timestamp = datetime.date.today()
                    page = str(timestamp) + page
                    page = string.replace(page,' ','')
                    page = string.replace(page,':','')
                tags = list()
                if len(taglist) > 0:
                    tags = string.split(taglist, ',')
                odb = db.Query(Objects)
                odb.filter('website = ', website)
                odb.filter('name = ', page)
                item = odb.get()
                if item is None:
                    item = Objects()
                    item.name = page
                    item.website = website
                    m = md5.new()
                    m.update(page)
                    m.update(str(datetime.datetime.now()))
                    guid = str(m.hexdigest())
                    item.guid = guid
                item.title = title
                item.sl = sl
                item.name = page
                item.description = description
                item.content = content
                item.tags = tags
                item.divid = divid
                item.divclass = divclass
                if publishnow == 'y':
                    item.published = True
                else:
                    item.published = False
                item.news = False
                if blog == 'y':
                    item.blog = True
                else:
                    item.blog = False
                if featured == 'y':
                    item.featured = True
                else:
                    item.featured = False
                item.put()
                result = True
                if result:
                    if len(host) > 0:
                        self.redirect('http://' + host + '/' + website + '/' + page)
                    else:
                        self.redirect('/' + website + '/'+ page)
            else:
                website = p1
                page = p2
                action = self.request.get('action')
                odb = db.Query(Objects)
                odb.filter('website = ', website)
                odb.filter('guid = ', page)
                item = odb.get()
                if item is None:
                    odb = db.Query(Objects)
                    odb.filter('website = ', website)
                    odb.filter('name = ', page)
                    item = odb.get()
                if item is not None:
                    if action == 'delete':
                        item.delete()
                    else:
                        if action == 'publish':
                            item.published=True
                        elif action == 'unpublish':
                            item.published=False
                        elif action == 'feature':
                            item.featured=True
                        elif action == 'unfeature':
                            item.featured=False
                        else:
                            pass
                        item.put()
                    self.redirect(referrer)
        else:
            self.redirect(referrer)

class UploadFile(webapp.RequestHandler):
    def post(self, p1='', p2=''):
        headers = self.request.headers
        website = headers.get('Host','')
        if len(p2) > 0:
            website = p1
            name = p2
        else:
            website = p1
            name = ''
        if len(name) < 1:
            name=self.request.get('name')
        title=self.request.get('title')
        if len(name) < 1:
            name = string.replace(title, ' ', '')
            name = string.replace(name, ':', '')
            name = string.replace(name, '&', '')
        image=self.request.get('image')
        result = Images.save(website, name, title, image)
        if result:
            self.redirect(self.request.referrer)
            
class MemberOf(webapp.RequestHandler):
    def get(self, username):
        udb = db.Query(Users)
        udb.filter('username = ', username)
        item = udb.get()
        self.response.out.write(str(item.websites))
        
class DomainMapping(webapp.RequestHandler):
    def get(self, website=''):
        self.requesthandler(website)
    def post(self, website=''):
        self.requesthandler(website)
    def requesthandler(self, website=''):
        referrer = self.request.referrer
        action = self.request.get('action')
        domain = self.request.get('domain')
        if len(website) > 0:
            wdb = db.Query(Websites)
            wdb.filter('host = ', website)
            item = wdb.get()
            if item is not None:
                altnames = item.alt
                if action == 'save':
                    if domain not in altnames:
                        altnames.append(domain)
                        item.alt = altnames
                        item.put()
                elif action == 'delete':
                    if domain in altnames:
                        altnames.remove(domain)
                        item.alt = altnames
                        item.put()
                else:
                    pass
        self.redirect(referrer)

application = webapp.WSGIApplication([(r'/editcss/(.*)/(.*)', EditCSS),
                                      (r'/editcss/(.*)', EditCSS),
                                      ('/headers', TestHeaders),
                                      ('/heartbeat', HeartBeat),
                                      ('/admin/rss', RSSSave),
                                      ('/admin/login', Login),
                                      ('/admin/saveuser/(.*)/(.*)', SaveUserPrefs),
                                      (r'/domains/(.*)', DomainMapping),
                                      (r'/admin/set/(.*)/(.*)', SetValue),
                                      (r'/admin/set/(.*)', SetValue),
                                      (r'/admin/(.*)/(.*)/(.*)', ControlPanel),
                                      (r'/admin/(.*)/(.*)', ControlPanel),
                                      (r'/admin/(.*)', ControlPanel),
                                      ('/setup', Setup),
                                      (r'/update/(.*)/(.*)', UpdatePage),
                                      (r'/update/(.*)', UpdatePage),
                                      (r'/upload/(.*)/(.*)', UploadFile),
                                      (r'/upload/(.*)', UploadFile),
                                      ('/create', ControlPanel),
                                      ('/admin', ControlPanel)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()

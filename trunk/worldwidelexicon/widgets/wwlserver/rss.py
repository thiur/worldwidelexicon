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
# import standard Python libraries
import datetime
import urllib
import urllib2
import string
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
# import Worldwide Lexicon modules
from database import Websites
from database import Objects
from database import Translation
from geo import geo
from database import languages
# import third party modules
import PyRSS2Gen as RSS2
import feedparser

# Define default settings

def clean(text):
    try:
        utext = text.encode('utf-8')
    except:
        try:
            utext = text.encode('iso-8859-1')
        except:
            utext = text
    text = utext.decode('utf-8')
    return text

encoding = 'utf-8'

default_language = 'en'

default_title = 'Welcome to the Worldwide Lexicon'

# standard footer and source code attribution, do not modify or hide
standard_footer = 'Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2009 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  WWL multilingual CMS and translation memory is open source software published \
                  under a BSD style license.'

class RSSServer(webapp.RequestHandler):
    def get(self, website='', language=''):
        headers = self.request.headers
        host = headers.get('Host','')
        remote_addr = self.request.remote_addr
        self.rss(website, language)
    def rss(self, website='', language=''):
        headers = self.request.headers
        host = headers.get('Host','')
        remote_addr = self.request.remote_addr
        #text = memcache.get('rss|website=' + website + '|language=' + language)
        text = None
        if text is not None:
            self.response.out.write(text)
        else:
            if len(language) < 2:
                language = 'en'
            wdb = db.Query(Websites)
            wdb.filter('host = ', website)
            w = wdb.get()
            if w is not None:
                title = w.title
                description = w.description
                sl = w.sl
            else:
                title = 'Sitemap'
                description = 'Sitemap'
                sl = 'en'
            if len(sl) < 2:
                sl = 'en'
            odb = db.Query(Objects)
            odb.filter('website = ', website)
            odb.order('-created')
            results = odb.fetch(limit=10)
            rss = RSS2.RSS2(title = title, description = description, link = 'http://' + host + '/rss/' + website + '/', lastBuildDate = datetime.datetime.now())
            if len(language) > 0:
                rss.language = language
            for r in results:
                if language != sl:
                    try:
                        title = clean(r.title)
                        ttitle = Translation.lucky(sl, language, title)
                    except:
                        title = ''
                        ttitle = ''
                    try:
                        st = clean(r.content)
                        tt = Translation.lucky(sl, language, st)
                    except:
                        st = ''
                        tt = ''
                    if len(title) > 0 and len(st) > 0:
                        item = RSS2.RSSItem(author = r.author, title = ttitle, description = tt, link = r.link)
                else:
                    item = RSS2.RSSItem(author = r.author, title = clean(r.title), description = clean(r.content), link = r.link)
                item.pubDate = r.created
                try:
                    item.categories = r.tags
                except:
                    pass
                item.guid = item.link
                rss.items.append(item)
            text = rss.to_xml(encoding)
            self.response.out.write(text)
            
class RSSRefresh(webapp.RequestHandler):
    """
    This web service schedules agents to reload RSS feeds to keep the Objects()
    data store in sync with the feeds. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        action = self.request.get('action')
        if action == 'load':
            self.load()
        else:
            wdb = db.Query(Websites)
            results = wdb.fetch(limit=200)
            if results is not None:
                for r in results:
                    p = dict()
                    p['action']='load'
                    p['website'] = r.host
                    p['rssurl'] = r.rssurl
                    taskqueue.add(url = '/rss', params=p)
    def load(self):
        website = self.request.get('website')
        rssurl = self.request.get('rssurl')
        if len(rssurl) > 0:
            if string.count(rssurl, 'http://') < 1:
                rssurl = 'http://' + rssurl
            try:
                result = urllib2.urlopen(url = rssurl)
                rsstext = result.read()
            except:
                rsstext = ''
            if len(rsstext) > 0:
                try:
                    fp = feedparser.parse(rsstext)
                    f = fp.feed
                    entries = fp.entries
                except:
                    fp = None
                    f = None
                    entries = None
                if entries is not None:
                    ctr = 0
                    for e in entries:
                        if ctr < 10:
                            ctr = ctr + 1
                            try:
                                title = clean(e.title)
                                content = clean(e.description)
                            except:
                                title = ''
                                content = ''
                            link = e.link
                            odb = db.Query(Objects)
                            odb.filter('link = ', link)
                            item = odb.get()
                            if item is None:
                                item = Objects()
                                item.website = website
                                item.link = link
                                item.title = title
                                item.content = content
                                item.author = e.author
                                item.put()
                                
class RegisterSite(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        host = self.request.headers['host']
        title = self.request.get('title')
        description = self.request.get('description')
        language = self.request.get('language')
        rssurl = self.request.get('rssurl')
        if len(title) > 0 and len(rssurl) > 0:
            wdb = db.Query(Websites)
            wdb.filter('rssurl = ', rssurl)
            item = wdb.get()
            if item is None:
                item = Websites()
                item.title = title
                item.description = description
                item.rssurl = rssurl
                l = 0
                while l < 50:
                    l = l + 1
                    tl = self.request.get('tl' + str(l))
                    if len(tl) > 0:
                        pro = self.request.get('pro' + str(l))
                        volunter = self.request.get('volunteer' + str(l))
                        machine = self.request.get('machine' + str(l))
                        setattr(item,'pro_' + tl,pro)
                        setattr(item,'volunteer_' + tl, volunteer)
                        setattr(item,'machine_' + tl, machine)
                speaklikeusername = self.request.get('speaklikeusername')
                speaklikepw = self.request.get('speaklikepw')
                item.speaklikeusername = speaklikeusername
                item.speaklikepw = speaklikepw
                item.put()
                txt = self.fetch('http://www.worldwidelexicon.org/s/rss_success.html')
            else:
                txt = self.fetch('http://www.worldwidelexicon.org/s/rss_error.html')
        else:
            txt = clean(self.fetch('http://www.worldwidelexicon.org/s/rss_register.html'))
            languagelist = clean(languages.select())
            langs = languages.getlist()
            lp = ''
            lkeys = langs.keys()
            lkeys.sort()
            lp = lp + '<table><tr><td>Language</td><td>Professional Translation</td><td>Volunteer Translation</td><td>Machine Translation</td></tr>'
            ctr = 0
            for l in lkeys:
                ctr = ctr + 1
                lp = lp + '<tr><td>' + langs.get(l, '') + '</td>'
                lp = lp + '<td><select name=pro' + str(ctr) + '><option selected value="">--</option>'
                lp = lp + '<option value=speaklike>SpeakLike</option></select>'
                lp = lp + '<td><select name=volunteer' + str(ctr) + '><option selected value=n>No</option><option value=y>Yes</option></select></td>'
                lp = lp + '<td><select name=machine' + str(str) + '><option selected value=n>No</option><option value=y>Yes</option></select></td>'
                lp = lp + '</tr>'
            lp = lp + '</table>'
            txt = string.replace(txt, '<!--language_list-->', languagelist)
            txt = string.replace(txt, '<!--language_preferences-->', lp)
        self.response.out.write(txt)
    def fetch(self,url):
        try:
            result = urllib2.urlopen(url)
            txt = result.read()
        except:
            txt = ''
        return txt
    
application = webapp.WSGIApplication([(r'/rss/(.*)/(.*)', RSSServer),
                                     ('/rss/register', RegisterSite),
                                     (r'/rss/(.*)', RSSServer),
                                     ('/rss', RSSServer)],
                                     debug=True)

def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
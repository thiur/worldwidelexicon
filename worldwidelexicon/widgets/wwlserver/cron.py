# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Cron Jobs for WWL CMS and Translation Server (cron.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements cron jobs that are used by the multilingual CMS.
Among the services implemented here are:

* A cron job to update incoming news feeds (RSS import service)
* A cron job to render static pages and outgoing RSS feeds (to boost performance)
* More coming soon

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
import types
import urllib
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
# import WWL modules
from database import Feeds
from database import Objects
# import third party modules
import feedparser

def smart_unicode(s, encoding='utf-8', errors='strict'):
    if type(s) in (unicode, int, long, float, types.NoneType):
        return unicode(s)
    elif type(s) is str or hasattr(s, '__unicode__'):
        return unicode(s, encoding, errors)
    else:
        return unicode(str(s), encoding, errors)

def smart_str(s, encoding='utf-8', errors='strict', from_encoding='utf-8'):
    if type(s) in (int, long, float, types.NoneType):
        return str(s)
    elif type(s) is str:
        if encoding != from_encoding:
            return s.decode(from_encoding, errors).encode(encoding, errors)
        else:
            return s
    elif type(s) is unicode:
        return s.encode(encoding, errors)
    elif hasattr(s, '__str__'):
        return smart_str(str(s), encoding, errors, from_encoding)
    elif hasattr(s, '__unicode__'):
        return smart_str(unicode(s), encoding, errors, from_encoding)
    else:
        return smart_str(str(s), encoding, errors, from_encoding)

class LoadRSSFeeds(webapp.RequestHandler):
    """
    /cron/rss
    
    Schedules tasks (via Task Queues) to reload RSS feeds being following by
    users on the system. It performs the following tasks:
    
    1. obtains a current list of active websites from the Websites() data store
    2. schedules a task for each website at /cron/rss/sitename

    """
    def get(self, website='', rssurl=''):
        self.requesthandler(website,rssurl)
    def post(self, website='', rssurl=''):
        self.requesthandler(website,rssurl)
    def requesthandler(self,website='', rssurl=''):
        action = self.request.get('action')
        if action == 'poll':
            website = self.request.get('website')
            rssurl = self.request.get('rssurl')
            self.poll(website, rssurl)
        else:
            results = Feeds.list(website)
            for r in results:
                p = dict()
                p['action'] = 'poll'
                p['website'] = r.website
                p['rssurl'] = r.rssurl
                if r.autopublish:
                    p['autopublish'] = 'y'
                else:
                    p['autopublish'] = 'n'
                if len(r.website) > 0 and len(r.rssurl) > 0:
                    taskqueue.add(url = '/cron/rss', params=p)
                self.response.out.write('Queued: ' + r.website + ' :' + r.rssurl + '<br>')
        self.response.out.write('ok')
    def poll(self, website, rssurl):
        ctr = 0
        if len(website) > 0 and len(rssurl) > 0:
            autopublish = self.request.get('autopublish')
            response = urlfetch.fetch(url = rssurl)
            if response.status_code == 200:
                text = response.content
                r = feedparser.parse(text)
                from_encoding = r.encoding
                if r is not None:
                    fdb = db.Query(Feeds)
                    fdb.filter('website = ', website)
                    fdb.filter('rssurl = ', rssurl)
                    item = fdb.get()
                    if item is not None:
                        autopublish = item.autopublish
                        item.indexed = datetime.datetime.now()
                        item.put()
                    else:
                        autopublish = False
                    f = r.feed
                    entries = r.entries
                    ctr = 0
                    for e in entries:
                        ctr = ctr + 1
                        if ctr < 10:
                            m = md5.new()
                            m.update(website)
                            m.update(e.link)
                            guid = str(m.hexdigest())
                            fdb = db.Query(Objects)
                            fdb.filter('website = ', website)
                            fdb.filter('guid = ', guid)
                            item = fdb.get()
                            if item is None:
                                title = e.title
                                ttags = string.split(string.lower(title), ' ')
                                try:
                                    ftags = e.tags
                                except:
                                    ftags = list()
                                try:
                                    content = e.content[0].value
                                except:
                                    content = e.description
                                link = e.link
                                item = Objects()
                                item.name = guid
                                item.title = title
                                item.website = website
                                item.rssurl = rssurl
                                item.link = link
                                item.guid = guid
                                item.news = True
                                item.blog = False
                                tags = ttags
                                for f in ftags:
                                    try:
                                        ft = string.lower(f.get('label',''))
                                        if len(ft) > 0:
                                            tags.append(ft)
                                    except:
                                        pass
                                item.tags = tags
                                #item.created = datetime(e.date_parsed)
                                if autopublish:
                                    item.published = True
                                else:
                                    item.published = False
                                try:
                                    item.content = smart_unicode(content, errors = 'ignore')
                                    item.put()
                                except:
                                    pass
        self.response.out.write('ok\n')
        self.response.out.write(str(ctr) + ' items parsed.')
        
application = webapp.WSGIApplication([(r'/cron/rss/(.*)/(.*)', LoadRSSFeeds),
                                    (r'/cron/rss/(.*)', LoadRSSFeeds),
                                    ('/cron/rss', LoadRSSFeeds)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Firefox Translator Support Utilities (firefox.py
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements some web services that are utilized by the Firefox Translator
such as to generate sidebars with translator statistics. 

NOTE: this documentation is generated automatically, and directly from the current
version of the WWL source code, via the PyDoc service. Because of the way App
Engine works, the hyperlinks in these files will not work, so your best option
is to print the documentation for offline review.

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
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
# import standard Python modules
import urllib
import string
import md5
import datetime
import time
import pydoc
import codecs
import types
# import WWL and third party modules
from webappcookie import Cookies
from geo import geo
from database import Comment
from database import Search
from database import Translation
from database import languages
from mt import MTWrapper
import feedparser

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

class Sidebar(webapp.RequestHandler):
    """
    /sidebar

    This request handler generates a sidebar that is displayed by the
    Firefox Translator when a page is being translated for a user. The
    sidebar highlights the most popular sites in a language, as well
    as recent community translation activity for a page or URL.
    """
    def post(self):
        self.requesthandler()
    def get(self):
        self.requesthandler()
    def requesthandler(self):
        self.response.out.write('<table border=0><tr><td>')
        self.response.out.write('<img src=/image/logo.png align=left valign=center>')
        self.response.out.write('<font size=+1>Worldwide<br>Lexicon</font></td></tr></table><hr>')
        cookies = Cookies(self)
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        if len(sl) < 2:
            sl = tl
        url = self.request.get('url')
        version = string.replace(self.request.get('v'), 'firefox.', '')
        if string.count(version, '.') > 0:
            version = float(version)
        else:
            version = float(0)
        url = string.replace(url, 'http://', '')
        try:
            session = cookies['session']
        except:
            session = ''
        username = ''
        if len(session) > 0:
            username = memcache.get('sessions|' + session)
            if username is None:
                username = ''
        comment = self.request.get('comment')
        if len(comment) > 0:
            guid = ''
            fields = dict()
            fields['tl'] = tl
            fields['cl'] = tl
            fields['comment']=comment
            fields['username']=username
            fields['remote_addr']=self.request.remote_addr
            Comment.save(guid, fields, url=url)
        urltexts = string.split(url, '/')
        if len(urltexts) > 0:
            domain = urltexts[0]
        else:
            domain = ''
        if tl == 'es':
            proz = 'esp'
        elif tl == 'fr':
            proz = 'fra'
        elif tl == 'de':
            proz = 'deu'
        else:
            proz = 'rus'
        google_analytics_header = '<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");\
        document.write(unescape("%3Cscript src=\'\" + gaJsHost + \"google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));\
        </script>\
        <script type="text/javascript">\
        try {\
        var pageTracker = _gat._getTracker("UA-7294247-1");\
        pageTracker._trackPageview();\
        } catch(err) {}</script>'
        self.response.out.write(google_analytics_header)
        prozurl = 'http://www.proz.com/connectapi?key=b60c3f792ed225efcc473fa8cfeb309b&version=0.4&pair=eng_' + proz + '&output=rss'
        f = memcache.get('proz|eng|' + proz)
        if f is None:
            response = urlfetch.fetch(url = prozurl)
            if response.status_code == 200:
                f = response.content
                memcache.set('proz|eng|' + proz, f, 900)
            else:
                f = ''
        mt = MTWrapper()
        if version < 1.000:
            prompt_upgrade = '<h4>Upgrade To The Newest Firefox Translator</h4>\
<font size=-1>Upgrade to the newest version of the <b><a href=http://www.worldwidelexicon.org target=_new>Firefox Translator</a></b>. This version \
includes several new features and improvements, including: faster page translation, more options for displaying translations, and new \
community features.</font><hr>'
            prompt_donate = '<h4>New Essay</h4>\
<font size=-1>Read this <b><a href=http://www.worldwidelexicon.org/s/essay.html target=_new>recently published essay, The End of the Language Barrier</a></b> by \
Brian McConnell. The essay describes his vision for the future, where people will be able to read any website in any language. If you think this \
is valuable work, consider <a href=http://www.worldwidelexicon.org target=_new>making a donation</a> to support ongoing software development.</font><hr>'
            if tl != 'en' and len(tl) > 1:
                prompt_upgrade = mt.getTranslation('en', tl, prompt_upgrade)
                prompt_donate = mt.getTranslation('en', tl, prompt_donate)
            self.response.out.write(prompt_upgrade)
            self.response.out.write(prompt_donate)
        if len(url) > 0:
            txt = memcache.get('recenttranslations|tl=' + tl + '|url=' + url)
            if txt is not None:
                self.response.out.write(txt)
            else:
                tdb = db.Query(Translation)
                if string.count(url, 'http://') > 0:
                    url = string.replace(url, 'http://', '')
                tdb.filter('url = ', url)
                if len(tl) > 0:
                    tdb.filter('tl = ', tl)
                tdb.order('-date')
                results = tdb.fetch(limit=200)
                authors = list()
                for r in results:
                    if r.anonymous:
                        if len(r.city) > 0:
                            t = r.remote_addr + ' (' + r.city + ')'
                        else:
                            t = r.remote_addr
                    else:
                        if len(r.city) > 0:
                            t = r.username + ' (' + r.city + ')'
                        else:
                            t = r.username
                        if string.count(t, 'proz.') > 0:
                            t = string.replace(t, 'proz.', '')
                            t = '[PRO] ' + t
                    if t not in authors:
                        authors.append(t)
                translator_heading = mt.getTranslation('en', tl, 'Translators')
                txt = '<h4 style="font-family: sans-serif">'+ translator_heading + '</h4>'
                if len(authors) > 0:
                    txt = txt + '<ul><font size=-2>'
                    for a in authors:
                        if string.count(a, '[PRO]') > 0:
                            link = string.replace(a, '[PRO] ', 'proz.')
                        else:
                            link = a
                        txt = txt + '<li><a target=_new href=/profiles/' + link + '>' + a + '</a></li>'
                    txt = txt + '</font></ul>'
                else:
                    no_mt = mt.getTranslation('en', tl, 'This page has not been translated by other users. Only machine translations are available at this time\
     To edit, score or replace a translation, hover over a translated text, and then a popup editor will appear.')
                    txt = txt + '<p style="font-family: sans-serif"><font size=-1>'
                    txt = txt + no_mt
                    txt = txt + '</font></p>'
                    memcache.set('recentranslations|tl=' + tl + '|url=' + url, txt, 240)
                self.response.out.write(txt)
            self.response.out.write('<hr>')
            txt = memcache.get('topsites|all')
            if txt is not None:
                self.response.out.write(txt)
            else:
                prompt_top_sites = 'Top Sites'
                prompt_worldwide = 'Worldwide'
                if sl != 'en' and len(sl) > 1:
                    prompt_top_sites = mt.getTranslation('en', tl, prompt_top_sites)
                    prompt_worldwide = mt.getTranslation('en', tl, prompt_worldwide)
                txt = '<h4>' + prompt_top_sites + '(' + prompt_worldwide + ')'
                sdb = db.Query(Search)
                sdb.order('-translations')
                results = sdb.fetch(limit=50)
                sitelist = list()
                if results is not None:
                    txt = txt + '<ul><font size=-2>'
                    ctr = 0
                    for r in results:
                        if r.domain not in sitelist and ctr < 15:
                            ctr = ctr + 1
                            sitelist.append(r.domain)
                            txt = txt + '<li><a target=_new href=http://' + r.domain + '>' + r.domain + '</a></li>'
                    txt = txt + '</font></ul>'
                    memcache.set('topsites|all', txt, 1800)
                    self.response.out.write(txt)
            self.response.out.write('<hr>')
            txt = memcache.get('topsites|sl=' + sl)
            if txt is not None:
                self.response.out.write(txt)
            else:
                prompt_top_sites = 'Top Sites'
                if sl != 'en' and len(sl) > 1:
                    prompt_top_sites = mt.getTranslation('en', tl, prompt_top_sites)
                txt = '<h4>' + prompt_top_sites + ' (' + languages.getlist(sl) + ')'
                sdb = db.Query(Search)
                sdb.filter('sl = ', sl)
                sdb.filter('issite = ', True)
                sdb.order('-views')
                results = sdb.fetch(limit=50)
                sitelist = list()
                if results is not None:
                    txt = txt + '<ul><font size=-2>'
                    for r in results:
                        if r.domain not in sitelist:
                            sitelist.append(r.domain)
                            title = clean(r.title)
                            if len(title) > 0:
                                txt = txt + '<li><a target=_new href=http://' + r.domain + '>' + title + '</a></li>'
                            else:
                                txt = txt + '<li><a target=_new href=http://' + r.domain + '>' + r.domain + '</a></li>'
                    txt = txt + '</font></ul>'
                    memcache.set('topsites|sl=' + sl, txt, 1800)
                    self.response.out.write(txt)
            self.response.out.write('<hr>')
            proz_heading = mt.getTranslation('en', tl, 'Find Professional Translators On ProZ.Com')
            self.response.out.write('<h4 style="font-family: sans-serif"><a href=http://www.proz.com>' + proz_heading + '</a></h4>')
            d = feedparser.parse(f)
            entries = d.entries
            if len(entries) > 0:
                self.response.out.write('<ul>')
                ctr = 0
                for e in entries:
                    ctr = ctr + 1
                    if ctr < 10:
                        self.response.out.write('<li style="font-family: sans-serif size: small"><a target=_new href=' + e.link + '>' + e.title + '</a></li>')
                self.response.out.write('</ul>')
        else:
            self.response.out.write('<form action=/sidebar method=get>')
            self.response.out.write('URL: <input type=text name=url size=30><p>')
            self.response.out.write('Language: <input type=text name=tl size=3><p>')
            self.response.out.write('<input type=submit value=OK></form>')

application = webapp.WSGIApplication([('/sidebar', Sidebar)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

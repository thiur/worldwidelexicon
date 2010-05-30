# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Social Translator (translate.py)
Brian S McConnell <brian@worldwidelexicon.org>

Copyright (c) 1998-2010, Worldwide Lexicon Inc, Brian S McConnell. 
All rights reserved. NOTE: this module is NOT open source and may not be
used for commercial purposes without the expressed written permission of
Worldwide Lexicon Inc.

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
import codecs
import urllib
import string
import md5
import datetime
import pydoc
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
# import Worldwide Lexicon modules
import feedparser
from excerpt_extractor import get_summary
from database import APIKeys
from database import Directory
from database import Languages
from database import Settings
from database import Translation
from database import UserScores
from language import TestLanguage
from proxy import ProxyDomains
from transcoder import transcoder
from webappcookie import Cookies
from wwlgae import wwl
from www import web
from www import www
from shorturl import UrlEncoder
import sgmllib

template = 'http://www.dermundo.com/css/template.css'

# Define convenience functions
            
def clean(text):
    return transcoder.clean(text)

def g(tl, text, professional=True):
    t = memcache.get('/g/' + tl + '/' + text)
    if t is not None:
        return t
    elif len(tl) < 2:
        return t
    else:
        text = clean(text)
        speaklikeusername = Settings.get('speaklikeusername')
        speaklikepw = Settings.get('speaklikepw')
        if professional:
            t = clean(wwl.get('en', tl, text, lsp='speaklikeapi', lspusername=speaklikeusername, lsppw=speaklikepw))
        else:
            t = clean(wwl.get('en', tl, text))
        if len(t) > 0:
            memcache.set('/g/' + tl + '/' + text, t, 300)
            return t
        else:
            return text

# Define default settings

sharethis_header = '<script type="text/javascript" src="http://w.sharethis.com/button/sharethis.js#publisher=902e01b2-5b17-45ca-9068-9bbeaf71ae2b&amp;type=website&amp;post_services=email%2Cfacebook%2Ctwitter%2Cgbuzz%2Cmyspace%2Cdigg%2Csms%2Cwindows_live%2Cdelicious%2Cstumbleupon%2Creddit%2Cgoogle_bmarks%2Clinkedin%2Cbebo%2Cybuzz%2Cblogger%2Cyahoo_bmarks%2Cmixx%2Ctechnorati%2Cfriendfeed%2Cpropeller%2Cwordpress%2Cnewsvine&amp;button=false"></script>\
<style type="text/css">\
body {font-family:helvetica,sans-serif;font-size:12px;}\
a.stbar.chicklet img {border:0;height:16px;width:16px;margin-right:3px;vertical-align:middle;}\
a.stbar.chicklet {height:16px;line-height:16px;}\
</style>'

sharethis_button = '<a id="ck_email" class="stbar chicklet" href="javascript:void(0);"><img src="http://w.sharethis.com/chicklets/email.gif" /></a>\
<a id="ck_facebook" class="stbar chicklet" href="javascript:void(0);"><img src="http://w.sharethis.com/chicklets/facebook.gif" /></a>\
<a id="ck_twitter" class="stbar chicklet" href="javascript:void(0);"><img src="http://w.sharethis.com/chicklets/twitter.gif" /></a>\
<a id="ck_sharethis" class="stbar chicklet" href="javascript:void(0);"><img src="http://w.sharethis.com/chicklets/sharethis.gif" />ShareThis</a>\
<script type="text/javascript">\
	var shared_object = SHARETHIS.addEntry({\
	title: document.title,\
	url: document.location.href\
});\
\
shared_object.attachButton(document.getElementById("ck_sharethis"));\
shared_object.attachChicklet("email", document.getElementById("ck_email"));\
shared_object.attachChicklet("facebook", document.getElementById("ck_facebook"));\
shared_object.attachChicklet("twitter", document.getElementById("ck_twitter"));\
</script>'

addthis_button = '<!-- AddThis Button BEGIN -->\
<a class="addthis_button" href="http://www.addthis.com/bookmark.php?v=250&amp;pub=worldwidelex">\
<img src="http://s7.addthis.com/static/btn/v2/lg-share-en.gif" width="125" height="16" alt="Bookmark and Share" style="border:0"/>\
</a><script type="text/javascript" src="http://s7.addthis.com/js/250/addthis_widget.js?pub=worldwidelex"></script>\
<!-- AddThis Button END -->\
'
encoding = 'utf-8'

default_language = 'en'

default_title = 'Worldwide Lexicon'

default_css = 'blueprint'

# Google Analytics Header
google_analytics_header = '<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");\
document.write(unescape("%3Cscript src=\'\" + gaJsHost + \"google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));\
</script>\
<script type="text/javascript">\
try {\
var pageTracker = _gat._getTracker("' + Settings.get('googleanalytics') + '");\
pageTracker._trackPageview();\
} catch(err) {}</script>'

# Define default settings for Blueprint CSS framework, included with this package as the default style sheet

template = 'http://www.worldwidelexicon.org/css/template.html'
template1col = 'http://3.latest.worldwidelexicon.appspot.com/css/template1col.html'
downloads = 'http://www.worldwidelexicon.org/static/downloads.html'

proxy_settings = '<meta name="allow_edit" content="y" />'

sidebar_about = 'The Worldwide Lexicon is an open source collaborative translation platform. It is similar to \
                systems like <a href=http://www.wikipedia.org>Wikipedia</a>, and combines machine translation \
                with submissions from volunteers and professional translators. WWL is a translation memory, \
                essentially a giant database of translations, which can be embedded in almost any website or \
                web application. \
                Our mission is to eliminate the language barrier for interesting websites and articles, by \
                enabling people to create translation communities around their favorite webites, topics or \
                groups.\
                <h1>Firefox Translator</h1>\
                <img src=/image/firefoxlogo.jpg align=left><a href=https://addons.mozilla.org/en-US/firefox/addon/13897>\
                Download our social translator for Firefox</a>. This free addon enables you to explore the \
                foreign language web. It translates web pages using the best available translations from \
                machines and from other users.<p>'

web_tools =    '<h1>Tools For Webmasters</h1>\
                Make your website, blog or service accessible in any language. The Worldwide Lexicon makes high quality, \
                open source translation tools for Word Press, Drupal and Firefox. You can also use the same software that \
                powers this website to translate your own website. Visit <a href=http://www.worldwidelexicon.org>\
                www.worldwidelexicon.org</a> to learn more.'

# standard footer and source code attribution, do not modify or hide
standard_footer = 'Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2010 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  WWL multilingual CMS and translation memory is open source software published \
                  under a BSD style license. Contact: bsmcconnell on skype or gmail.'

class MyParser(sgmllib.SGMLParser):
    """
    This class implements a basic HTML parser that is used to extract
    title, description and keywords from a page's HTML header. 
    """
    inside_title = False
    title = ''
    inside_meta = False
    keywords = ''
    description = ''

    def start_title(self, attrs):
        self.inside_title = True

    def end_title(self):
        self.inside_title = False

    def start_meta(self, attrs):
        self.inside_meta = True
        name = attrs[0]
        content = attrs[1]
        if string.lower(name[1]) == 'description':
            self.description = content[1]
        if string.lower(name[1]) == 'keywords':
            self.keywords = content[1]

    def end_meta(self, attrs):
        self.inside_meta = False

    def handle_data(self, data):
        if self.inside_title and data:
            self.title = self.title + data + ' '

class DerMundoProjects(db.Model):
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    id = db.StringProperty()
    shorturl = db.StringProperty(default='')
    createdon = db.DateTimeProperty(auto_now_add=True)
    title = db.StringProperty(default='', multiline=True)
    description = db.TextProperty(default='')
    indexed = db.BooleanProperty(default=False)
    sl = db.StringProperty(default='')
    tags = db.ListProperty(str)
    translators = db.ListProperty(str)
    createdby = db.StringProperty(default='')
    @staticmethod
    def add(url, email=''):
        url = urllib.unquote_plus(url)
        text = string.replace(url, 'http://', '')
        text = string.replace(text, 'https://', '')
        texts = string.split(text, '/')
        domain = texts[0]
        if len(domain) > 0 and len(url) > 0:
            tdb = db.Query(DerMundoProjects)
            tdb.filter('url = ', url)
            item = tdb.get()
            if item is None:
                item = DerMundoProjects()
                item.domain = domain
                item.url = url
                item.createdby = email
                ue = UrlEncoder()
                try:
                    obj_id = str(item.key().id())
                    shorturl = ue.encode_url(int(obj_id))
                    item.shorturl = shorturl
                    resave = False
                except db.NotSavedError:
                    # No key, hence no ID yet. This one hasn't been saved.
                    # We'll save it once without the ID field; this first
                    # save will cause GAE to assign it a key. Then, we can
                    # extract the ID, put it in our ID field, and resave
                    # the object.
                    resave = True
                item.put()
                if resave:
                    item.id = str(item.key().id())
                    shorturl = ue.encode_url(int(item.id))
                    item.shorturl = shorturl
                    item.put()
                p = dict()
                p['u']= url
                taskqueue.add(url = '/translate/crawl', params=p)
                return 'http://www.dermundo.com/' + shorturl
        return ''
    @staticmethod
    def find(url, email=''):
        url = urllib.unquote_plus(url)
        url = urllib.unquote_plus(url)
        text = string.replace(url, 'http://', '')
        text = string.replace(text, 'https://', '')
        texts = string.split(text, '/')
        domain = texts[0]
        if len(url) > 0:
            tdb = db.Query(DerMundoProjects)
            tdb.filter('url = ', url)
            item = tdb.get()
            if item is None:
                item = DerMundoProjects()
                item.url = url
                item.domain = domain
                ue = UrlEncoder()
                try:
                    obj_id = str(item.key().id())
                    shorturl = ue.encode_url(int(obj_id))
                    item.shorturl = shorturl
                    resave = False
                except db.NotSavedError:
                    # No key, hence no ID yet. This one hasn't been saved.
                    # We'll save it once without the ID field; this first
                    # save will cause GAE to assign it a key. Then, we can
                    # extract the ID, put it in our ID field, and resave
                    # the object.
                    resave = True
                item.put()
                if resave:
                    item.id = str(item.key().id())
                    shorturl = ue.encode_url(int(item.id))
                    item.shorturl = shorturl
                    item.put()
                return 'http://www.dermundo.com/' + shorturl
        return ''

class Translator(webapp.RequestHandler):
    def get(self, p1='', p2='', p3=''):
        slu = Settings.get('speaklikeusername')
        slp = Settings.get('speaklikepw')
        try:
            language = TestLanguage.browserlanguage(self.request.headers['Accept-Language'])
        except:
            language = 'en'
        if len(language) > 2:
            language = language[0:2]
        proxy_settings = '<meta name="allow_edit" content="y" />'        
        lsp = ''
        lspusername = ''
        lsppw = ''
        professional_translation_languages = ''
        #professional_translation_languages = Settings.get('professional_translation_languages')
        if len(lsp) > 0:
            proxy_settings = proxy_settings + '<meta name="lsp" content="'+ lsp + '" />'
        if len(lspusername) > 0:
            proxy_settings = proxy_settings + '<meta name="lspusername" content="' + lspusername + '" />'
        if len(lsppw) > 0:
            proxy_settings = proxy_settings + '<meta name="lsppw" content="' + lsppw + '" />'
        if len(professional_translation_languages) > 0:
            proxy_settings = proxy_settings + '<meta name="professional_translation_languages" content="' + professional_translation_languages + '" />'
        menus = '<ul><li><a href=http://blog.worldwidelexicon.org>Blog</a></li>\
<li><a href=http://www.worldwidelexicon.org>Worldwide Lexicon</a></li>\
</ul>'
        if p1 == 'blog':
            self.redirect('http://blog.worldwidelexicon.org')
        elif p1 == 's':
            self.error(404)
            self.response.out.write('<h2>Page Not Found</h2>')
        else:
            #t = '<h1>' + language + '</h1>'
            t = '<h1>' + g(language, 'Social Translation For The Web') + '</h1>'
            t = t + g(language, 'Machine translation is great, but we all know it often produces inaccurate (and sometimes funny) translations. ')
            t = t + g(language, 'Der Mundo is the worldwide web, translated by people. We use machine translation (from Google Translate and Apertium) to produce a "rough draft". ')
            t = t + g(language, 'Then users take over to edit the translations, score translations from other users, and make them better.<p>')
            t = t + '<p><table><form action=/translate/view method=get>'
            t = t + '<tr><td>' + g(language, 'Language') + '</td><td><select name=l>'
            t = t + clean(Languages.select(selected=language)) + '</td></tr>'
            t = t + '<tr><td></td><td><select name=allow_machine>'
            t = t + '<option selected value="y">' + g(language,'Display human and machine translations') + '</option>'
            t = t + '<option value="n">' + g(language, 'Only display human translations') + '</option>'
            t = t + '</select></td></tr>'
            t = t + '<tr><td>URL</td><td><input type=text name=u value="http://www.nytimes.com"></td></tr>'
            t = t + '<tr><td colspan=2>' + g(language, 'Create a social translation project and short URL') + ': '
            t = t + '<input type=checkbox name=makeproject checked></td></tr>'
            t = t + '<tr><td>' + g(language, 'Email Address') + '</td><td><input type=text name=email></td></tr>'
            t = t + '<tr><td colspan=2>' + g(language, 'Optional professional translation by <a href=http://www.speaklike.com>SpeakLike</a>') + '</td></tr>'
            t = t + '<tr><td>SpeakLike username</td><td><input type=text name=lspusername></td></tr>'
            t = t + '<tr><td>SpeakLike password</td><td><input type=password name=lsppw></td></tr>'
            t = t + '<tr><td></td><td>'
            t = t + ' ' + g(language,'Professional translations are usually completed within 24 hours.')
            t = t + ' ' + g(language,'We will provide a temporary machine translation until then.')
            t = t + ' ' + g(language,'When completed, professional translations will be visible to other users.')
            t = t + '</td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value="' + g(language,'Translate!') + '"></td></tr>'
            t = t + '</form></table><p>'
            w = web()
            w.get(template)
            w.replace(template,'[google_analytics]',google_analytics_header)
            w.replace(template,'[title]','Der Mundo')
            w.replace(template,'[meta]', proxy_settings)
            w.replace(template,'[footer]',standard_footer)
            w.replace(template,'[menu]',menus)
            w.replace(template,'[left_column]',t)
            r = '<h1>' + g(language, 'About') + '</h1>'
            r = r + g(language, sidebar_about)
            r = r + g(language, web_tools)
            w.replace(template,'[right_column]', r)
            self.response.out.write(w.out(template))
    def post(self, p1='', p2='', p3=''):
        self.redirect('http://blog.worldwidelexicon.org')

class TranslateReloader(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        try:
            tl = self.request.get('tl')
            if len(tl) > 0:
                try:
                    urlfetch.fetch(url='http://www.dermundo.com/translate', headers={'Accept-Language': tl})
                except:
                    self.error(500)
            else:
                languages = ['es', 'fr', 'de', 'it', 'pt', 'ja', 'ar', 'zh']
                for l in languages:
                    p = dict()
                    p['tl']=l
                    taskqueue.add(url='/translate/reload', params=p)
            self.response.out.write('ok')
        except:
            self.error(500)
            self.response.out.write('Oh my. Something bad happened')

class DisplayTranslators(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        tl = self.request.get('l')
        url = urllib.unquote_plus(self.request.get('u'))
        output = self.request.get('output')
        if len(tl) > 0:
            language=tl
        else:
            try:
                language=TestLanguage.browserlanguage(self.request.headers['Accept-Language'])
            except:
                language='en'
        if len(url) > 0:
            text = memcache.get('/translators/' + tl + '/' + url)
            if text is not None:
                self.response.out.write(text)
            else:
                tdb = db.Query(DerMundoProjects)
                tdb.filter('url = ', url)
                item = tdb.get()
                if item is not None:
                    shorturl = clean('http://www.dermundo.com/x' + item.shorturl)
                else:
                    shorturl = ''
                tdb = db.Query(Translation)
                tdb.filter('url = ', url)
                if len(tl) > 0:
                    tdb.filter('tl = ', tl)
                tdb.order('-date')
                results = tdb.fetch(limit = 500)
                translators = dict()
                translatorskeys = list()
                for r in results:
                    if len(r.username) > 0:
                        if r.username not in translatorskeys:
                            translatorskeys.append(r.username)
                            translators[r.username]=r.city
                    else:
                        if r.remote_addr not in translatorskeys:
                            translatorskeys.append(r.remote_addr)
                            translators[r.remote_addr]=r.city
                translatorskeys.sort()
                text = '<img src=/image/logo.png align=left>'
                text = text + g(language, 'This page has been translated by <a href=http://www.dermundo.com>Der Mundo</a>, using <a href=http://www.google.com/translate>Google Translate</a>, <a href=http://www.apertium.org>Apertium</a>, and by Internet users worldwide.')
                if len(shorturl) > 0:
                    text = text + ' ' + g(language, 'The shortcut for this social translation project is: ')
                    text = text + '<a href=' + shorturl + ' target=_new>' + string.replace(shorturl, 'http://', '') + '</a>'
                for t in translatorskeys:
                    text = text + '<a href=/profile/' + t + '>' + t + '</a>'
                    if len(translators.get(t)) > 0:
                        text = text + ' (' + translators.get(t) + ') '
                    else:
                        text = text + ' '
                memcache.set('/translators/' + tl + '/' + url, text, 300)
                self.response.out.write(text)

class TranslationFrame(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        l = self.request.get('l')
        u = urllib.quote_plus(self.request.get('u'))
        email = self.request.get('email')
        makeproject = self.request.get('makeproject')
        if makeproject == 'on':
            shorturl = DerMundoProjects.add(u, email=email)
        else:
            shorturl = DerMundoProjects.find(u, email=email)
        allow_machine = self.request.get('allow_machine')
        lspusername = self.request.get('lspusername')
        lsppw = self.request.get('lsppw')
        self.response.out.write('<frameset rows="8%, 92%">')
        self.response.out.write('<frame src=http://www.dermundo.com/translate/translators?l=' + l + '&u=' + u + '>')
        self.response.out.write('<frame src=http://proxy.worldwidelexicon.org?l=' + l + '&u=' + urllib.unquote_plus(u) + '>')
        self.response.out.write('</frameset>')

class CrawlPage(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        u = self.request.get('u')
        (title, description) = get_summary(u)
        tdb = db.Query(DerMundoProjects)
        tdb.filter('url = ', u)
        item = tdb.get()
        if item is not None:
            try:
                item.title = title.decode('utf-8')
            except:
                try:
                    item.title = clean(title)
                except:
                    item.title = title
            try:
                item.description = description.decode('utf-8')
            except:
                try:
                    item.description = clean(description)
                except:
                    item.description = description
            title = string.lower(title)
            description = string.lower(description)
            language = TestLanguage.language(text=description)
            if len(language) > 1 and len(language) < 4:
                item.sl = language
            words = string.split(title) + string.split(description)
            item.tags = words
            item.indexed = True
            item.put()
        self.response.out.write(title + '\n' + description)

class LandingPage(webapp.RequestHandler):
    def get(self, p1=''):
        self.requesthandler(p1)
    def post(self, p1=''):
        self.requesthandler(p1)
    def requesthandler(self, p1):
        cookies = Cookies(self)
        try:
            language = TestLanguage.browserlanguage(self.request.headers['Accept-Language'])
        except:
            language = 'en'
        if len(language) < 2 or len(language) > 3:
            language = 'en'
        u = p1
        tdb = db.Query(DerMundoProjects)
        tdb.filter('shorturl = ', u)
        item = tdb.get()
        if item is not None:
            title = clean(item.title)
            description = clean(item.description)
            description = '(<a href=http://' + item.domain + '>' + item.domain + '</a>) ' + description
            sl = item.sl
            url = item.url
            if string.count(url, 'http://') < 1:
                url = 'http://' + url
        else:
            title = u
            description = ''
            sl = ''
            url = ''
        dmenus = '<ul><li><a href=http://www.worldwidelexicon.org>Worldwide Lexicon</a></li>\
                <li><a href=http://blog.worldwidelexicon.org>' + g(language,'Blog') + '</a></li>\
                <li><a href=http://www.worldwidelexicon.org>' + g(language,'Tools For Webmasters') + '</a></li></ul>'
        t = '<h1>' + title
        t = t + '</h1>'
        t = t + description
        t = t + '<p><h2>Create Translations For This Page</h2>'
        t = t + '<form action=/translate/view method=get>'
        t = t + '<table><tr><td><select name=l>'
        t = t + Languages.select(selected=language)
        t = t + '</select></td><td><input type=submit value=OK></td></tr>'
        t = t + '<input type=hidden name=u value="' + url + '">'
        t = t + '</form></table>'
        t = t + '<br>'
        t = t + '<h2>Share This Page</h2>'
        t = t + '<blockquote>' + sharethis_button + '</blockquote>'
        r = '<h2>' + g(language,'Translators') + '</h2>'
        r = r + '<ul><li>Ipsum</li><li>Orum</li></ul>'
        r = r + '<h2>' + g(language,'Recent Translations') + '</h2>'
        r = r + 'Foo<blockquote>Bar</blockquote>'
        w = web()
        w.get(template)
        w.replace(template, '[title]', 'Der Mundo')
        w.replace(template, '[meta]', sharethis_header)
        w.replace(template, '[menu]', dmenus)
        w.replace(template, '[left_column]', t)
        w.replace(template, '[right_column]', r)
        w.replace(template, '[footer]', standard_footer)
        t = w.out(template)
        self.response.out.write(t)
                
application = webapp.WSGIApplication([('/translate', Translator),
                                      ('/translate/view', TranslationFrame),
                                      ('/translate/crawl', CrawlPage),
                                      ('/translate/translators', DisplayTranslators),
                                      ('/translate/reload', TranslateReloader)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

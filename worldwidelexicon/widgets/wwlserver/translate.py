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
import facebook
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
from database import Cache
from database import Directory
from database import Languages
from database import Settings
from database import Translation
from database import Users
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
usertemplate = 'http://www.dermundo.com/dermundocss/profile.html'
sidebar_url = 'http://www.dermundo.com/dermundocss/sidebar.html'

userip =''

# Define convenience functions
            
def clean(text):
    return transcoder.clean(text)

def g(tl, text, professional=True, server_side=True):
    text = clean(text)
    m = md5.new()
    m.update('en')
    m.update(tl)
    m.update(text)
    m.update('y')
    m.update('y')
    if professional:
        m.update('speaklikeapi')
    md5hash = str(m.hexdigest())
    t = Cache.getitem('/t/' + md5hash + '/text')
    if t is not None and len(t) > 1:
        return t
    else:
        speaklikeusername = Settings.get('speaklikeusername')
        speaklikepw = Settings.get('speaklikepw')
        speaklikelangs = ['pt', 'r', 'nl', 'de', 'cs', 'fr', 'it', 'ar', 'ja', 'es', 'zh', 'pl', 'el', 'da', 'pl']
        if tl not in speaklikelangs:
            professional = False
        if professional:
            t = Translation.lucky('en', tl, text, lsp='speaklike', lspusername=speaklikeusername, lsppw=speaklikepw, userip=userip)
        else:
            
            t = Translation.lucky('en', tl, text, userip=userip)
        return t

# Define default settings

snapshot_code = '<script type="text/javascript" src="http://shots.snap.com/ss/9bad968f87780aea459ecbeaecc6a753/snap_shots.js"></script>'

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

template = 'http://www.worldwidelexicon.org/dermundocss/translate.html'
dmtemplate = 'http://www.dermundo.com/dermundocss/index.html'
template1col = 'http://3.latest.worldwidelexicon.appspot.com/css/template1col.html'
downloads = 'http://www.worldwidelexicon.org/static/downloads.html'

proxy_settings = '<meta name="allow_edit" content="y" />'

sidebar_about = clean('The Worldwide Lexicon is an open source collaborative translation platform. It is similar to \
                systems like <a href=http://www.wikipedia.org>Wikipedia</a>, and combines machine translation \
                with submissions from volunteers and professional translators. WWL is a translation memory, \
                essentially a giant database of translations, which can be embedded in almost any website or \
                web application. \
                Our mission is to eliminate the language barrier for interesting websites and articles, by \
                enabling people to create translation communities around their favorite webites, topics or \
                groups.')

firefox_translator = clean('<h1>Firefox Translator</h1>')

firefox_translator_prompt = clean('<img src=/image/firefoxlogo.jpg align=left><a href=https://addons.mozilla.org/en-US/firefox/addon/13897>\
                Download our social translator for Firefox</a>. This free addon enables you to explore the \
                foreign language web. It translates web pages using the best available translations from \
                machines and from other users.<p>')

firefox_translator_prompt2 = clean('The Firefox Translator is an ideal way to view and contribute translations. \
                It automatically translates foreign language pages when it is needed, and when \
                you edit translations to make them better, these changes are automatically shared with \
                other users worldwide.<p>')

web_tools =    clean('Make your website, blog or service accessible in any language. The Worldwide Lexicon makes high quality, \
                open source translation tools for Word Press, Drupal and Firefox. You can also use the same software that \
                powers this website to translate your own website. Visit <a href=http://www.worldwidelexicon.org>\
                www.worldwidelexicon.org</a> to learn more.')

instructions =  clean('<ol><li>Complete the short form to start a translation project</li>\
                <li>DerMundo.com will assign a shortcut URL which you can share with your friends and other translators</li>\
                <li>You can also donate to pay to professionally translate a page and share it with the world.</li>\
                </ol>')

translator_instructions = clean('You can view and edit translations in two ways. If you have our Firefox Translator addon (highly recommended), \
                simply follow the link to the original web page, and turn on the Firefox Translator. It will translate \
                the page within your browser. You can edit translations by pointing at a section of text, and a popup editor \
                will appear. If you do not have the Firefox addon, you can view and edit translations \
                using our translation server. This will load the page, translate it, and send it to you. You can also edit \
                translations there. Translations submitted from both tools are shared with the worldwide user community.')

firefox_sidebar_intro = clean('Discover, translate and share interesting webpages with your friends and the world.')

firefox_sidebar_learn_more = clean('Learn more')

firefox_sidebar_instructions = clean('The Firefox Translator automatically translates foreign language pages using the \
                best available human and machine translations. You can edit translations simply by pointing at a section \
                of text. A popup editor will appear where you can edit the translation, which will be shared with the \
                user community worldwide.')

firefox_sidebar_shortcut = clean('Share this shortcut to <a href=http://www.facebook.com target=_new>Facebook</a>, \
                <a href=http://www.twitter.com target=_new>Twitter</a> and your friends. The shortcut address for this \
                translation project is<p>')

firefox_sidebar_no_shortcut = clean('No shortcut address has been created for this webpage yet. Visit <a target=_new href=http://www.dermundo.com/translate>www.dermundo.com/translate</a> \
                or simply start editing translations on this page to create a DerMundo shortcut.')

# standard footer and source code attribution, do not modify or hide
standard_footer = clean('Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2011 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  Professional translations for the Der Mundo interface and documentation produced \
                  by <a href=http://www.speaklike.com>SpeakLike</a>.')

class FBUser(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    @staticmethod
    def lookup(cookies):
        cookie = facebook.get_user_from_cookie(cookies, Settings.get('facebook_app_id'), Settings.get('facebook_app_secret'))
        if cookie:
            # Store a local instance of the user data so we don't need
            # a round-trip to Facebook on every request
            user = FBUser.get_by_key_name(cookie["uid"])
            if not user:
                graph = facebook.GraphAPI(cookie["access_token"])
                profile = graph.get_object("me")
                user = FBUser(key_name=str(profile["id"]),
                            id=str(profile["id"]),
                            name=profile["name"],
                            profile_url=profile["link"],
                            access_token=cookie["access_token"])
                user.put()
            elif user.access_token != cookie["access_token"]:
                user.access_token = cookie["access_token"]
                user.put()
            return profile
        else:
            return

class FBLocales():
    locales=dict()
    locales['ca']='ca_ES'
    locales['cs']='cs_CZ'
    locales['cy']='cy_GB'
    locales['da']='da_DK'
    locales['eu']='eu_ES'
    locales['ck']='ck_US'
    locales['en']='en_US'
    locales['es']='en_LA'
    locales['fi']='fi_FI'
    locales['fr']='fr_FR'
    locales['gl']='gl_ES'
    locales['hu']='hu_HU'
    locales['it']='it_IT'
    locales['ja']='ja_JP'
    locales['ko']='ko_KR'
    locales['nb']='nb_NO'
    locales['nn']='nn_NO'
    locales['nl']='nl_NL'
    locales['pl']='pl_PL'
    locales['pt']='pt_BR'
    locales['ro']='ro_RO'
    locales['ru']='ru_RU'
    locales['sk']='sk_SK'
    locales['sl']='sl_SL'
    locales['sv']='sv_SE'
    locales['th']='th_TH'
    locales['tr']='tr_TR'
    locales['ku']='ku_TR'
    locales['zh']='zh_CN'
    locales['ar']='ar_AR'
    def lookup(self,language):
        locale = self.locales.get(language,'')
        if len(locale) > 0:
            return locale

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
    def geturl(shorturl):
        udb = db.Query(DerMundoProjects)
        udb.filter('shorturl = ', shorturl)
        item = udb.get()
        if item is not None:
            return item.url
        else:
            return
    @staticmethod
    def add(url, email=''):
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
                p['']= url
                return item.shorturl
            else:
                return item.shorturl
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
        language = self.request.get('tl')
        try:
            language = TestLanguage.browserlanguage(self.request.headers['Accept-Language'])
        except:
            language = 'en'
        locales = string.split(self.request.headers['Accept-Language'],',')
        locale = locales[0]
        if len(locales[1]) < 2:
            f = FBLocales()
            locale=f.lookup(locales[0])
        else:
            locale=locales[0] + '_' + string.upper(locales[1])
        dmenus = '<ul><li><a href=http://www.worldwidelexicon.org>Worldwide Lexicon</a></li>\
                <li><a href=http://www.worldwidelexicon.org>' + g(language,clean('Tools For Webmasters')) + '</a></li></ul>'
        if len(language) > 2:
            language = language[0:2]
        proxy_settings = '<meta name="allow_edit" content="y" />'        
        lsp = ''
        lspusername = ''
        lsppw = ''
        userip = self.request.remote_addr
        headers = self.request.headers
        host = headers.get('host','')
        if p1 == 'blog':
            self.redirect('http://blog.worldwidelexicon.org')
        elif host == 'www.worldwidelexicon.org':
            self.redirect('http://www.worldwidelexicon.org/home')
        elif p1 == 's':
            self.error(404)
            self.response.out.write('<h2>Page Not Found</h2>')
        elif p1 == 'newpages':
            pdb = db.Query(DerMundoProjects)
            pdb.order('-createdon')
            results = pdb.fetch(limit=20)
            ctr = 0
            t = memcache.get('/dermundo/newpages/' + language)
            if t is None:
                t = ''
                for r in results:
                    if ctr < 10:
                        if r.indexed:
                            try:
                                title = codecs.encode(r.title,'utf-8')
                            except:
                                try:
                                    title = clean(r.title)
                                except:
                                    title = ''
                            try:
                                description = codecs.encode(r.description, 'utf-8')
                            except:
                                try:
                                    description = clean(r.description)
                                except:
                                    description = ''
                            try:
                                t = t + '<h4><a href=/x' + r.shorturl + '>' + title + '</a></h4>'
                                t = t + '<code>' + g(language, description, server_side = False, professional = False) + '</code>'
                                ctr = ctr + 1
                            except:
                               pass
                if len(t) > 0:
                    memcache.set('/dermundo/newpages/' + language, t, 240)
            self.response.out.write(t)
        else:
            #t = '<h1>' + language + '</h1>'
##            text = Cache.getitem('/dermundo/cache/' + language)
##            if text is not None:
##                self.response.out.write(text + '<p>This page is memcached</p>')
##                return
            w = web()
            w.get(template)
            w.replace(template,'[social_translation]', clean(g(language,'Social Translation')))
            t = ''
            t = t + clean(g(language, 'Machine translation is great, but we all know it often produces inaccurate (and sometimes funny) translations. '))
            t = t + clean(g(language, 'Der Mundo is the worldwide web, translated by people. We use machine translation (from Google Translate and Apertium) to produce a rough draft. '))
            t = t + clean(g(language, 'Then users take over to edit the translations, score translations from other users, and make them better.<p>'))
            w.replace(template, '[introduction]', t)
            # generate form
            t = '<p><table><form action=/translate/project method=get>'
            t = t + '<tr><td>' + clean(g(language, 'Language')) + '</td><td><select name=l>'
            t = t + clean(Languages.select(selected=language)) + '</td></tr>'
#            t = t + '<tr><td></td><td><select name=allow_machine>'
#            t = t + '<option selected value="y">' + g(language,'Display human and machine translations') + '</option>'
#            t = t + '<option value="n">' + g(language, 'Only display human translations') + '</option>'
            t = t + '</select></td></tr>'
            t = t + '<tr><td>URL</td><td><input type=text size=40 name=u value="http://www.aljazeera.net"></td></tr>'
            t = t + '<tr><td colspan=2>' + g(language, 'Optional professional translation by <a href=http://www.speaklike.com>SpeakLike</a>') + '</td></tr>'
            t = t + '<tr><td>SpeakLike username</td><td><input type=text name=lspusername></td></tr>'
            t = t + '<tr><td>SpeakLike password</td><td><input type=password name=lsppw></td></tr>'
            t = t + '<tr><td></td><td>'
            t = t + ' ' + g(language,'Professional translations are usually completed within 24 hours.')
            t = t + ' ' + g(language,'We will provide a temporary machine translation until then.')
            t = t + ' ' + g(language,'When completed, professional translations will be visible to other users.')
            t = t + '</td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value="' + g(language, 'Translate!', server_side=True) + '"></td></tr>'
            t = t + '</form></table><p>'
            w.replace(template,'[start_form]',t)
            w.replace(template,'[google_analytics]',google_analytics_header)
            w.replace(template,'[title]','Der Mundo : ' + g(language,'Translate the world with your friends', server_side=True))
            w.replace(template,'[meta]', sharethis_header + snapshot_code)
            w.replace(template,'[copyright]',standard_footer)
            w.replace(template,'[menu]',dmenus)
            w.replace(template,'[about]', g(language,'About'))
            w.replace(template,'[tagline]', g(language, 'Translate the world with your friends'))
            w.replace(template,'[share_this_page]', g(language, 'Share This Page'))
            w.replace(template,'[share_this_button]', sharethis_button)
            w.replace(template,'[instructions]', g(language, 'Instructions'))
            w.replace(template,'[instructions_prompt]', g(language, instructions))
            Cache.setitem('/dermundo/cache/' + language, w.out(template), 600)
            self.response.out.write(w.out(template))
    def post(self, p1='', p2='', p3=''):
        self.redirect('http://blog.worldwidelexicon.org')

class DisplayTranslators(webapp.RequestHandler):
    def get(self, shorturl=''):
        self.requesthandler(shorturl)
    def post(self, shorturl=''):
        self.requesthandler(shorturl)
    def requesthandler(self, shorturl=''):
        url = urllib.unquote_plus(self.request.get('u'))
        output = self.request.get('output')
        try:
            language=TestLanguage.browserlanguage(self.request.headers['Accept-Language'])
        except:
            language='en'
        locales = string.split(self.request.headers['Accept-Language'],',')
        found_locale = False
        for l in locales:
            locale=''
            if not found_locale:
                langloc = string.split(l, '-')
                if len(langloc) > 1:
                    locale = string.lower(langloc[0]) + '_' + string.upper(langloc[1])
                else:
                    f = FBLocales()
                    locale = f.lookup(langloc[0])
                if locale is not None:
                    if len(locale) > 1:
                        foundlocale=True
        if not foundlocale:
            locale = 'en_US'
        if len(shorturl) > 0:
            url = DerMundoProjects.geturl(shorturl)
            shorturl = clean('http://www.dermundo.com/x' + shorturl)
        else:
            tdb = db.Query(DerMundoProjects)
            tdb.filter('url = ', url)
            item = tdb.get()
            if item is not None:
                shorturl = clean('http://www.dermundo.com/x' + item.shorturl)
            elif len(url) > 0:
                shorturl = clean('http://www.dermundo.com/x' + DerMundoProjects.add(url))
            else:
                shorturl = ''
        if len(url) > 0:
            m = md5.new()
            m.update(language)
            m.update(url)
            md5hash = str(m.hexdigest())
            text = memcache.get('/dermundo/' + md5hash)
            if text is not None:
                self.response.out.write(text)
            else:
                tdb = db.Query(Translation)
                tdb.filter('url = ', url)
                if len(language) > 0:
                    tdb.filter('tl = ', language)
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
                proxy_template = 'http://www.dermundo.com/dermundocss/proxy.html'
                w = web()
                w.get(proxy_template)
                w.replace(proxy_template,'[title]', clean('Der Mundo'))
                w.replace(proxy_template,'[google_analytics]', google_analytics_header)
                w.replace(proxy_template,'[tagline]', g(language, clean('Translate the world with your friends')))
                text = '<table border=0 cellspacing=2><tr><td width=70%>'
                if len(shorturl) > 0:
                    text = text + ' ' + g(language, clean('The shortcut for this social translation project is: '))
                    text = text + '<a href=' + shorturl + ' target=_new>' + string.replace(shorturl, 'http://', '') + '</a><br>'
                text = text + g(language, clean('This page has been translated by <a href=http://www.dermundo.com>Der Mundo</a>, using <a href=http://www.google.com/translate>Google Translate</a>, <a href=http://www.apertium.org>Apertium</a>, and by Internet users worldwide.'))
                if len(translatorskeys) > 0:
                    text = text + '<hr>' + g(language,clean('Recent Translators')) + '<br>'
                for t in translatorskeys:
                    text = text + '<a href=/profile/' + t + '>' + t + '</a>'
                    if len(translators.get(t)) > 0:
                        text = text + ' (' + translators.get(t) + ') '
                    else:
                        text = text + ' '
                text = text + '</td><td width=30%>'
                text = text + """<div id="fb-root"></div>
    <script src="http://connect.facebook.net/""" + locale + """/all.js"></script>
    <script>
    FB.init({
    appId  : '140342715320',
    status : true, // check login status
    cookie : true, // enable cookies to allow the server to access the session
    xfbml  : true  // parse XFBML
    });
    </script>
    <fb:login-button autologoutlink="true"></fb:login-button>
    """
                user = FBUser.lookup(self.request.cookies)
                if user is not None:
                    text = text + '<p><a href=' + user.get('profile_url','') + '><img src=http://graph.facebook.com/' + user.get('id ','')+ '/picture?type=square/></a></p>'
                text = text + """
    <div id="fb-root"></div>
    <script>
    window.fbAsyncInit = function() {
    FB.init({appId: '140342715320', status: true, cookie: true,
             xfbml: true});
    FB.Event.subscribe('{% if current_user %}auth.logout{% else %}auth.login{% endif %}', function(response) {
      window.location.reload();
    });
    };
    (function() {
    var e = document.createElement('script');
    e.type = 'text/javascript';
    e.src = document.location.protocol + '//connect.facebook.net/""" + locale + """/all.js';
    e.async = true;
    document.getElementById('fb-root').appendChild(e);
    }());
    </script>
    """
                text = text + '</td></tr>'
                text = text + '<tr><td colspan=2><iframe width=1000 height=3000 scrolling=yes src=http://wwlapi.appspot.com/' + clean(string.replace(url,'http://','')) + '>'
                text = text + '</td></tr></table>'
                w.replace(proxy_template, '[meta]', '')
                w.replace(proxy_template, '[content]', text)
                w.replace(proxy_template, '[copyright]', standard_footer)
                memcache.set('/dermundo/' + md5hash, w.out(proxy_template), 300)
                self.response.out.write(w.out(proxy_template))

class GenerateShortCut(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = self.request.get('url')
        email = self.request.get('email')
        shorturl = DerMundoProjects.add(url, email=email)
        self.response.out.write('ok\n' + shorturl)

class CreateProject(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        url = urllib.unquote_plus(self.request.get('u'))
        shorturl = DerMundoProjects.add(url)
        self.redirect('http://www.dermundo.com/x' + shorturl)

class Sidebar(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        al = self.request.get('tl')
        if len(al) < 2 or len(al) > 3:
            al = 'en'
        url = self.request.get('url')
        language = TestLanguage.browserlanguage(al)
        t = memcache.get('/firefox/sidebar/' + language + '/' + url)
        if t is not None:
            self.response.out.write(t)
            return
        w = web()
        w.get(sidebar_url)
        w.replace(sidebar_url, '[google_analytics]', google_analytics_header)
        w.replace(sidebar_url, '[meta]', '<meta http-equiv=refresh content=30>')
        w.replace(sidebar_url, '[firefox_sidebar_intro]', '<img src=http://www.dermundo.com/image/logo.png align=left>' + g(language,firefox_sidebar_intro))
        w.replace(sidebar_url, '[shortcut]', g(language, 'Shortcut'))
        w.replace(sidebar_url, '[recent_translators]', g(language, 'Recent Translators'))
        w.replace(sidebar_url, '[statistics]', '')
        w.replace(sidebar_url, '[statistics_data]', '')
        shorturl = 'http://www.dermundo.com/x' + DerMundoProjects.add(url)
        if len(shorturl) > 0:
            w.replace(sidebar_url, '[firefox_sidebar_shortcut]', g(language, firefox_sidebar_shortcut))
            w.replace(sidebar_url, '[shorturl]', '<a target=_new href=' + shorturl + '>' + string.replace(shorturl, 'http://', '') + '</a>')
        else:
            w.replace(sidebar_url, '[firefox_sidebar_shortcut]', '')
            w.replace(sidebar_url, '[shorturl]', g(language, firefox_sidebar_no_shortcut))
        text = memcache.get('/firefox/sidebar/recenttranslators/' + url)
        if text is not None:
            w.replace(sidebar_url, '[recent_translator_list]', text)
        else:
            tdb = db.Query(Translation)
            if string.count(url, 'http://') > 0:
                url = string.replace(url, 'http://', '')
            if string.count(url, 'https://') > 0:
                url = string.replace(url, 'https://', '')
            translators = list()
            translatorcity = dict()
            translatorlang = dict()
            tdb.filter('url = ', url)
            tdb.order('-date')
            results = tdb.fetch(limit=50)
            if len(results) > 0:
                text = '<ul>'
                for r in results:
                    if len(r.username) > 0:
                        if r.username not in translators:
                            translators.append(r.username)
                            translatorcity[r.username]=r.city
                            translatorlang[r.username]=r.tl
                    else:
                        if r.remote_addr not in translators:
                            translators.append(r.remote_addr)
                            translatorcity[r.remote_addr] = r.city
                            translatorlang[r.remote_addr] = r.tl
                for tx in translators:
                    text = text + '<li>(&rarr; ' + Languages.getname(translatorlang[tx]) + ') <a href=http://www.dermundo.com/profile/' + tx + '>'
                    text = text + tx + ' (' + translatorcity[tx] + ')</a></li>'
                text = text + '</ul>'
                memcache.set('/firefox/sidebar/recenttranslators/' + url, text, 360)
            else:
                text = ''
            w.replace(sidebar_url, '[recent_translator_list]', text)
        t = w.out(sidebar_url)
        memcache.set('/firefox/sidebar/' + language + '/' + url, t, 120)
        self.response.out.write(t)

class Help(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        try:
            language = TestLanguage.browserlanguage(self.request.headers['Accept-Language'])
        except:
            language = 'en'
        dmenus = '<ul><li><a href=http://www.worldwidelexicon.org>Worldwide Lexicon</a></li>\
                <li><a href=http://blog.worldwidelexicon.org>' + g(language,'Blog') + '</a></li>\
                <li><a href=http://www.worldwidelexicon.org>' + g(language,'Tools For Webmasters') + '</a></li></ul>'
        intro = 'The <a href=https://addons.mozilla.org/en-US/firefox/addon/13897>Firefox Translator</a> enables you to browse the web in any language. \
        Simply open a URL, and if it is in a foreign language, it will translate it to your language. \
        You can also edit the translations to fix mistakes.'
        install = '<ol>\
        <li>Using Firefox, go to <a href=https://addons.mozilla.org/en-US/firefox/addon/>addons.mozilla.org/en-US/firefox/addon/13897</a></li>\
        <li>Install the addon</li>\
        <li>Restart Firefox</li>\
        <li>Go to a foreign language website. Try <a href=http://www.lemonde.fr>Le Monde</a> and <a href=http://www.elpais.es>El Pais</a></li>\
        </ol>'
        config1 = 'The Firefox Translator offers many options to display \
        translations. Go to the Options link (it is on the right side of \
        the toolbar). When you go there, you can adjust these settings:'
        config2 = '<ul>\
        <li>Display bilingual text (the original text and the translation)</li>\
        <li>Display machine translations</li>\
        <li>Display translations from anonymous users</li>\
        <li>Require a minimum quality score for translations</li>\
        <li>Automatic translations (the translator will translate any page that is in a foreign language)</li>\
        </ul>'
        privacy = 'The Firefox Translator communicates with several translation \
        services when it is active. You can disable the toolbar by clicking on the blue and green icon in the lower right corner \
        of the window. The toolbar is automatically disabled in these situations:'
        privacy2 = '<ul>\
        <li>Firefox is in "Private Browsing" mode</li>\
        <li>You visit a secure website</li>\
        <li>You have disabled the toolbar</li>\
        </ul>'
        text = memcache.get('/firefox/help/' + language)
        if text is None:
            t = g(language, intro)
            t = t + '<h3>' + g(language,'Installation') + '</h3>'
            t = t + g(language,install) + '<p>'
            t = t + '<h3>' + g(language,'Configuration') + '</h3>'
            t = t + g(language,config1) + '<p>'
            t = t + '<p>' + g(language,config2) + '</p>'
            t = t + '<h3>' + g(language, 'Privacy') + '</h3>'
            t = t + '<p>' + g(language, privacy) + '</p>'
            t = t + g(language, privacy2) + '<p>'
            w = web()
            w.get(template)
            w.replace(template, '[social_translation]', g(language, 'Firefox Translator (Help)'))
            w.replace(template, '[introduction]', t)
            w.replace(template, '[start_form]', '')
            w.replace(template, '[downloads_intro]','')
            w.replace(template, '[google_analytics]',google_analytics_header)
            w.replace(template, '[title]','Der Mundo : ' + g(language,'The World In Your Language'))
            w.replace(template, '[meta]', sharethis_header + snapshot_code)
            w.replace(template, '[copyright]',standard_footer)
            w.replace(template, '[menu]',dmenus)
            w.replace(template, '[about]', g(language,'About'))
            w.replace(template, '[about_worldwide_lexicon]', g(language, sidebar_about))
            w.replace(template, '[downloads_intro]', g(language, web_tools))
            w.replace(template, '[tagline]', g(language, 'The World In Your Language'))
            w.replace(template, '[share_this_page]', g(language, 'Share This Page'))
            w.replace(template, '[share_this_button]', sharethis_button)
            w.replace(template, '[instructions]', '')
            w.replace(template, '[instructions_prompt]', '')
            w.replace(template, '[firefox_translator]', g(language, 'Firefox Translator'))
            w.replace(template, '[about_firefox_translator]', g(language, firefox_translator_prompt) + g(language, firefox_translator_prompt2))
            w.replace(template, '[new_pages]', '')
            text = w.out(template)
            self.response.out.write(text)
                
application = webapp.WSGIApplication([('/', Translator),
                                      (r'/dermundo/(.*)', Translator),
                                      ('/translate/project', CreateProject),
                                      ('/translate/view', DisplayTranslators),
                                      ('/translate/shortcut', GenerateShortCut),
                                      (r'/x(.*)', DisplayTranslators),
                                      ('/translate/translators', DisplayTranslators),
                                      ('/sidebar', Sidebar),
                                      ('/help/firefox', Help)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A barebones AppEngine application that uses Facebook for login."""

import facebook
import os.path
import wsgiref.handlers
import string
import md5
import datetime
import urllib
import codecs
import logging

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.api import channel

from database import languages
from database import Languages
from database import Settings
from database import Translation
from webappcookie import Cookies
from lsp import LSP
from shorturl import UrlEncoder
from excerpt_extractor import get_summary
from transcoder import transcoder
import demjson
from BeautifulSoup import BeautifulSoup

from ui import TextObjects
from ui import TextTranslations

FACEBOOK_APP_ID = Settings.get('facebook_app_id')
FACEBOOK_APP_SECRET = Settings.get('facebook_app_secret')

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

sidebar_about = 'The Worldwide Lexicon is an open source collaborative translation platform. It is similar to \
                systems like <a href=http://www.wikipedia.org>Wikipedia</a>, and combines machine translation \
                with submissions from volunteers and professional translators. WWL is a translation memory, \
                essentially a giant database of translations, which can be embedded in almost any website or \
                web application. \
                Our mission is to eliminate the language barrier for interesting websites and articles, by \
                enabling people to create translation communities around their favorite webites, topics or \
                groups.'

webmasters = 'Webmasters'

facebook_login_prompt = 'Please login to Facebook. This is required to edit translations.'

facebook_login = 'Please login to Facebook and provide your email address to register for the beta.'

firefox_translator = 'Firefox Translator'

firefox = 'Firefox'

firefox_prompt = '<a href=https://addons.mozilla.org/en-US/firefox/addon/13897>\
                Download our social translator for Firefox</a>. This free addon enables you to explore the \
                foreign language web, edit translations and share them with other users worldwide. \
                It translates web pages using the best available translations from \
                machines and from other users.<p>'

wordpress_translator = 'Wordpress Translator'

wordpress = 'WordPress'

wordpress_prompt = '<a href=http://wordpress.org/extend/plugins/speaklike-worldwide-lexicon-translator/>\
                Download our social translator for WordPress</a>. This add-on translates your WordPress website \
                using machine translation, translations from your user community, and professional translators at \
                <a href=http://www.speaklike.com>SpeakLike</a>.'

web_tools =    'Make your website, blog or service accessible in any language. The Worldwide Lexicon makes high quality, \
                open source translation tools for Word Press, Drupal and Firefox. You can also use the same software that \
                powers this website to translate your own website. Visit <a href=http://www.worldwidelexicon.org>\
                www.worldwidelexicon.org</a> to learn more.'

share_this_page = 'Share This Page'

instructions = 'Instructions'

instructions_prompt =  '<ol><li>Complete the short form to start a translation project</li>\
                <li>DerMundo.com will assign a shortcut URL which you can share with your friends and other translators</li>\
                <li>You can also donate to pay to professionally translate a page and share it with the world.</li>\
                </ol>'

translator_instructions = 'You can view and edit translations in two ways. If you have our Firefox Translator addon (highly recommended), \
                simply follow the link to the original web page, and turn on the Firefox Translator. It will translate \
                the page within your browser. You can edit translations by pointing at a section of text, and a popup editor \
                will appear. If you do not have the Firefox addon, you can view and edit translations \
                using our translation server. This will load the page, translate it, and send it to you. You can also edit \
                translations there. Translations submitted from both tools are shared with the worldwide user community.'

# standard footer and source code attribution, do not modify or hide
copyright = 'Content management system and collaborative translation memory powered \
                  by the <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Project</a> \
                  (c) 1998-2011 Brian S McConnell and Worldwide Lexicon Inc. All rights reserved. \
                  Professional translations for the Der Mundo interface and documentation produced \
                  by <a href=http://www.speaklike.com>SpeakLike</a>.'

social_translation = 'Social Translation'

introduction = 'Machine translation is great, but we all know it often produces inaccurate (and sometimes funny) translations.\
                Der Mundo is the worldwide web, translated by people. We use machine translation (from Google Translate and Apertium) to produce a rough draft.\
                Then users take over to edit the translations, score translations from other users, and make them better.<p>'
encoding = 'utf-8'

default_language = 'en'

professional_translation = 'Optional professional translation by <a href=http://www.speaklike.com>SpeakLike</a>'

email_address = 'Email'

speaklike_password = 'SpeakLike Password'

translated_by = 'This page was translated by Google Translate, Apertium and people worldwide.'

translated_by_people = 'Translators: '

shorturl_prompt = 'The shortcut URL for this translation project is: '

reload = 'Reload this page'

tagline = 'Translate the world with your friends'

beta_thank_you = 'Thank you for registering for the Der Mundo beta. We will email you when the service is ready for testing.\
		 Please encourage your friends and colleagues to join the beta as well.'

translations = 'Translations'

words = 'Words'

languages_prompt = 'Languages'

for_publishers = 'For Publishers'

# Google Analytics Header
google_analytics_header = '''<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-7294247-5']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();

</script>'''

userip = ''

def clean(text):
    return transcoder.clean(text)
    #return transcoder.clean(text, charset='utf-8')

def pro(tl, text, ttl=600):
    m = md5.new()
    m.update('en')
    m.update(tl)
    m.update(text)
    md5hash = str(m.hexdigest())
    #t = memcache.get('/pro/' + md5hash)
    t = None
    if t is not None:
	if type(t) is str:
	    if len(t) > 0:
		return t
    else:
	rtl = ['ar','fa', 'he', 'ur']
	speaklikelangs = ['de', 'es', 'fr', 'pt']
        #speaklikelangs = ['pt', 'ru', 'ko', 'de', 'cs', 'fr', 'it', 'ar', 'ja', 'es', 'zh', 'el', 'fa', 'he']
        if tl in speaklikelangs:
            result = LSP.get('en', tl, text, url='www.dermundo.com', lsp='speaklike',\
			lspusername=Settings.get('speaklike_username'), \
			lsppw=Settings.get('speaklike_pw'), worker=True)
	    if type(result) is dict:
		t = result.get('tt','')
	    elif type(result) is str:
		t = result
	    else:
		t = ''
	else:
	    return text
	if t is not None:
	    if len(t) > 0:
		memcache.set('/pro/' + md5hash, t, ttl)
		return t
	else:
	    return text
    return text

def g(tl, text, professional=False, server_side=True):
    m = md5.new()
    m.update('en')
    m.update(tl)
    m.update(text)
    md5hash = str(m.hexdigest())
    t = memcache.get('/t/' + md5hash)
    if t is not None and len(t) > 1:
        return t
    else:
        t = Translation.lucky('en', tl, text, userip=userip)
	memcache.set('/t/' + md5hash, t)
        return t
    
def geolocate(ip):
    location = memcache.get('/geo/' + ip)
    if location is None:
	result = urlfetch.fetch(url='http://www.worldwidelexicon.org/geo?ip=' + ip)
	try:
	    text = result.content
	except:
	    text = ''
	if len(text) > 0:
	    data = string.split(text,'\n')
	    location = dict()
	    location['city']=data[0]
	    location['country']=data[1]
	    location['latitude']=data[2]
	    location['longitude']=data[3]
	else:
	    location = None
    return location

class DerMundoMetaData(db.Model):
    shorturl = db.StringProperty(default='')
    url = db.StringProperty(default='')
    encoding = db.StringProperty(default='')
    original = db.BooleanProperty(default=True)
    language = db.StringProperty(default='')
    title = db.TextProperty(default='')
    description = db.TextProperty(default='')
    keywords = db.ListProperty(str)
    createdon = db.DateTimeProperty(auto_now_add = True)
    updated = db.DateTimeProperty(auto_now = True)
    translatorid = db.StringProperty(default='')
    translatorname = db.StringProperty(default='')
    translatorprofile = db.StringProperty(default='')
    @staticmethod
    def crawl(url='', shorturl='', sl=''):
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'https://', '')
	if len(url) > 0:
	    tdb = db.Query(DerMundoMetaData)
	    tdb.filter('url = ', url)
	    tdb.filter('original = ', True)
	    item = tdb.get()
	    if item is None:
		item = DerMundoMetaData()
		item.url = url
		item.shorturl = shorturl
		item.original = True
		item.sl = sl
	else:
	    tdb = db.Query(DerMundoMetaData)
	    tdb.filter('shorturl = ', shorturl)
	    tdb.filter('original = ', True)
	    item = tdb.get()
	    if item is None:
		item = DerMundoMetaData()
		item.url = url
		item.shorturl = shorturl
		item.original = True
		item.sl = sl
	url = 'http://' + url
	try:
	    metadata = get_summary(url)
	    title = metadata.get('title','')
	    description = metadata.get('description','')
	    if title is not None: title = db.Text(title, encoding = 'utf-8')
	    if description is not None: description = db.Text(description, encoding = 'utf-8')
	    item.put()
	except:
	    pass
    @staticmethod
    def find(url='', shorturl='', language=''):
	url = string.replace(url, 'https://', '')
	url = string.replace(url, 'http://', '')
	tdb = db.Query(DerMundoMetaData)
	if len(url) > 0:
	    tdb.filter('url = ', url)
	else:
	    tdb.filter('shorturl = ', shorturl)
	tdb.filter('language = ', language)
	item = tdb.get()
	if item is None:
	    return None
	else:
	    metadata = dict(
		url = item.url,
		shorturl = item.shorturl,
		title = item.title,
		description = item.description,
		language = item.language,
		original = item.original,
		keywords = item.keywords,
		facebookid = item.translatorid,
		username = item.translatorname,
		profile_url = item.translatorprofile,
		
	    )
	    return metadata
    @staticmethod
    def submit(url, shorturl='', title='', description='', language='', keywords=None, translatorid='', translatorname='', translatorprofile=''):
	url = string.replace(url, 'https://', '')
	url = string.replace(url, 'http://', '')
	if len(url) > 0 and len(shorturl) < 1:
	    shorturl = DerMundoProjects.find(url)
	tdb = db.Query(DerMundoMetaData)
	if len(url) > 0 and len(shorturl) < 1:
	    tdb.filter('url = ', url)
	else:
	    tdb.filter('shorturl = ', shorturl)
	tdb.filter('language = ', language)
	item = tdb.get()
	if item is None:
	    item = DerMundoMetaData()
	    item.url = url
	    item.shorturl = shorturl
	    item.language = language
	    item.original = False
	if len(title) > 0: item.title = title
	if len(description) > 0: item.description = description
	if keywords is not None:
	    keylist = item.keywords
	    for k in keywords:
		if k not in keylist: keylist.append(k)
	    item.keywords = keylist
	if len(translatorid) > 0: item.translatorid = translatorid
	if len(translatorname) > 0: item.translatorname = translatorname
	if len(translatorprofile) > 0: item.translatorprofile = translatorprofile
	item.put()
	return True
    
class DerMundoGroups(db.Model):
    id = db.StringProperty(default='')
    name = db.StringProperty(default='')
    createdby = db.StringProperty(default='')
    createdbyname = db.StringProperty(default='')
    createdbyprofile = db.StringProperty(default='')
    description = db.TextProperty(default='')
    tags = db.ListProperty(str)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    members = db.IntegerProperty(default=0)
    languages = db.ListProperty(str)
    messages = db.IntegerProperty(default=0)
    discussionurl = db.StringProperty(default='')
    facebookurl = db.StringProperty(default='')
    rssfeed = db.StringProperty(default='')
    @staticmethod
    def find(label):
	gdb = db.Query(DerMundoGroups)
	gdb.filter('id = ', label)
	item = gdb.get()
	return item
    @staticmethod
    def search(tag=None, language=None, maxlen=10):
	gdb = db.Query(DerMundoGroups)
	if tag is not None:
	    gdb.filter('tags = ', tag)
	if language is not None:
	    gdb.filter('languages = ', language)
	gdb.order('-created')
	results = gdb.fetch(maxlen)
	if results is None:
	    return list()
	else:
	    return results
    @staticmethod
    def create(label, name, description, tags=None, languages=None, createdby='',\
	       createdbyname='', createdbyprofile='', email='', discussionurl='',\
	       facebookurl = '', rssfeed=''):
	label = string.replace(label,' ','')
	label = string.lower(label)
	if len(label) < 5:
	    return False
	gdb = db.Query(DerMundoGroups)
	gdb.filter('id = ', label)
	item = gdb.get()
	if item is not None:
	    return False
	else:
	    item = DerMundoGroups()
	    item.id = label
	    item.name = name
	    item.description = description
	    item.createdby = createdby
	    item.createdbyname = createdbyname
	    item.createdbyprofile = createdbyprofile
	    if len(discussionurl) > 0:
		discussionurl = string.replace(discussionurl, 'http://','')
		discussionurl = string.replace(discussionurl, 'https://', '')
		item.discussionurl = discussionurl
	    if len(facebookurl) > 0:
		facebookurl = string.replace(facebookurl, 'http://','')
		facebookurl = string.replace(facebookurl, 'https://','')
		item.facebookurl = facebookurl
	    if len(rssfeed) > 0:
		rssfeed = string.replace(rssfeed, 'http://','')
		rssfeed = string.replace(rssfeed, 'https://','')
		item.rssfeed = rssfeed
	    if tags is not None:
		if type(tags) is str:
		    tags = string.replace(tags,' ',',')
		    tags = string.split(tags,',')
		if type(tags) is list:
		    taglist = item.tags
		    for t in tags:
			if len(t) > 1:
			    if t not in taglist:
				taglist.append(t)
		    item.tags = taglist
	    if languages is not None:
		if type(languages) is str:
		    languages = string.split(languages,',')
		if type(languages) is list:
		    langs = item.languages
		    for l in languages:
			if l not in langs:
			    langs.append(l)
		    item.languages = langs
	    item.members = 1
	    item.put()
	    return True
    @staticmethod
    def join(label, id, language=None, city=None, country=None, name=None, \
	     profile_url=None, email=None):
	if DerMundoGroupMembers.join(label, id, language=language, city=city, country=country, \
				     email=email, profile_url=profile_url, name=name):
	    gdb = db.Query(DerMundoGroups)
	    gdb.filter('id = ', label)
	    item = gdb.get()
	    if item is not None:
		item.members = item.members + 1
		item.put()
		return True
	return False
    @staticmethod
    def leave(label, id):
	gdb = db.Query(DerMundoGroups)
	gdb.filter('id = ', label)
	item = gdb.get()
	if item is not None:
	    if item.createdby != id:
		if DerMundoGroupMembers.leave(label, id):
		    item.members = item.members - 1
		    item.put()
		    return True
	return False
    @staticmethod
    def savemessage(label, id, message, language = 'en', tags = None, city='', country='', name='', profile_url=''):
	if DerMundoMessages.sendmessage('group', label, id, message, tags=tags, language=language, name=name,\
					city=city, country=country, profile=profile_url):
	    gdb = db.Query(DerMundoGroups)
	    gdb.filter('label = ', label)
	    item = gdb.get()
	    if item is not None:
		item.messages = item.messages + 1
		item.put()
		return True
	return False
    @staticmethod
    def getmessages(label, language='', tag=''):
	return DerMundoMessages.search(msgtype='group', label=label, language=language, tag=tag)

class DerMundoGuideStats(db.Model):
    url = db.StringProperty(default='')
    rectype = db.StringProperty(default='')
    value = db.StringProperty(default='')
    datephrase = db.StringProperty(default='')
    views = db.IntegerProperty(default=0)
    @staticmethod
    def inc(url, rectype, value):
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://', '')
	timestamp=datetime.datetime.now()
	year=str(timestamp.year)
	month=str(timestamp.month)
	day=str(timestamp.day)
	if len(month) < 2: month='0' + month
	if len(day) < 2: day='0' + day
	dp = year + month + day
	gdb = db.Query(DerMundoGuideStats)
	gdb.filter('url = ', url)
	gdb.filter('rectype = ', rectype)
	gdb.filter('value = ', value)
	gdb.filter('datephrase = ', dp)
	item = gdb.get()
	if item is None:
	    item = DerMundoGuideStats()
	    item.url = url
	    item.rectype = rectype
	    item.value = value
	    item.datephrase = dp
	item.views = item.views + 1
	item.put()
	return True

class DerMundoGuide(db.Model):
    created = db.DateTimeProperty(auto_now_add = True)
    createdby = db.StringProperty(default='')
    createdbyname = db.StringProperty(default='')
    createdbyprofile = db.StringProperty(default='')
    updated = db.DateTimeProperty(auto_now = True)
    url = db.StringProperty(default='')
    title = db.StringProperty(default='')
    description = db.StringProperty(default='')
    tags = db.ListProperty(str)
    languages = db.ListProperty(str)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    score = db.IntegerProperty(default=0)
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    @staticmethod
    def submit(url, title, description, tags=None, languages=None,\
	       createdby = '', createdbyname = '', createdbyprofile = '',\
	       city = '', country=''):
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'https://', '')
	gdb = db.Query(DerMundoGuide)
	gdb.filter ('url = ', url)
	item = gdb.get()
	if item is None:
	    item = DerMundoGuide()
	    item.url = url
	    item.createdby = createdby
	    item.createdbyname = createdbyname
	    item.createdbyprofile = createdbyprofile
	if len(title) > 0: item.title = title
	if len(description) > 0: item.description = description[0:135]
	if type(tags) is list:
	    taglist = item.tags
	    for t in tags:
		if t not in taglist:
		    taglist.append(t)
	    item.tags = taglist
	if type(languages) is list:
	    langs = item.languages
	    for l in languages:
		if l not in langs:
		    langs.append(l)
	    item.languages = langs
	item.city = city
	item.country = country
	item.upvotes = item.upvotes + 1
	item.score = item.score + 1
	item.put()
	return True
    @staticmethod
    def vote(url, vote):
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'https://','')
	gdb = db.Query(DerMundoGuide)
	gdb.filter('url = ', url)
	item = gdb.get()
	if item is not None:
	    if vote == 'up':
		item.upvotes = item.upvotes + 1
		item.score = item.score + 1
	    else:
		item.downvotes = item.downvotes + 1
		item.score = item.score - 1
	    return True
	return False
    @staticmethod
    def search(tag='', language='', city='', minscore=0, sortorder='-score'):
	gdb = db.Query(DerMundoGuide)
	if len(tag) > 0: gdb.filter('tags = ', tag)
	if len(language) > 0: gdb.filter('languages = ', language)
	if len(city) > 0: gdb.filter('city = ', city)
	gdb.filter('score >= ', minscore)
	gdb.order(sortorder)
	results = gdb.fetch(50)
	return results
    
class DerMundoMessages(db.Model):
    guid = db.StringProperty(default='')
    msgtype = db.StringProperty(default='')
    label = db.StringProperty(default='')
    sender = db.StringProperty(default='')
    sendername = db.StringProperty(default='')
    senderprofile = db.StringProperty(default='')
    sendercity = db.StringProperty(default='')
    sendercountry = db.StringProperty(default='')
    timestamp = db.DateTimeProperty(auto_now_add=True)
    message = db.TextProperty(default='')
    tags = db.ListProperty(str)
    language = db.StringProperty(default='en')
    flagged = db.IntegerProperty(default=0)
    @staticmethod
    def sendmessage(msgtype, label, id, message, tags=None, language='en',\
		    name='', profile='', city='', country=''):
	if len(msgtype) > 0 and len(message) > 0:
	    m = md5.new()
	    m.update(message)
	    m.update(str(datetime.datetime.now()))
	    guid = str(m.hexdigest())
	    item = DerMundoMessages()
	    item.guid = guid
	    item.msgtype = msgtype
	    item.label = label
	    item.sender = id
	    item.sendername = name
	    item.senderprofile = profile
	    item.sendercity = city
	    item.sendercountry = country
	    item.message = message
	    if tags is not None:
		if type(tags) is str:
		    tags = string.replace(tags,' ',',')
		    tags = string.split(tags, ',')
		if type(tags) is list:
		    item.tags = tags
	    item.language = language
	    item.put()
	    return guid
	else:
	    return None
    @staticmethod
    def deletemessage(guid, sender):
	mdb = db.Query(DerMundoMessages)
	mdb.filter('guid = ', guid)
	item = mdb.get()
	if item is not None:
	    item.delete()
	    return True
	else:
	    return False
    @staticmethod
    def search(msgtype='', label='', sender='', tag='', language='', city='', country='', maxlen=20):
	m = md5.new()
	m.update(msgtype)
	m.update(label)
	m.update(sender)
	m.update(tag)
	m.update(language)
	m.update(city)
	m.update(country)
	md5hash = str(m.hexdigest())
	#results = memcache.get('/recent/messages/' + md5hash)
	#if results is not None:
	#    return results
	mdb = db.Query(DerMundoMessages)
	if len(msgtype) > 0: mdb.filter('msgtype = ', msgtype)
	if len(label) > 0: mdb.filter('label = ', label)
	if len(sender) > 0: mdb.filter('sender = ', sender)
	if len(tag) > 0: mdb.filter('tags = ', tag)
	if len(language) > 0: mdb.filter('language = ', language)
	if len(city) > 0: mdb.filter('sendercity = ', city)
	if len(country) > 0: mdb.filter('sendercountry = ', country)
	mdb.order('-timestamp')
	results = mdb.fetch(maxlen)
	if results is not None:
	    for r in results:
		r.sendercity = string.replace(r.sendercity,' ', '_')
	    memcache.set('/recent/messages/' + md5hash, results, 10)
	return results
    @staticmethod
    def flag(guid):
	mdb = db.Query(DerMundoMessages)
	mdb.filter('guid = ', guid)
	item = mdb.get()
	if item is not None:
	    item.flagged = item.flagged + 1
	    item.put()
	    return True
	else:
	    return False
    @staticmethod
    def purge():
	mdb = db.Query(DerMundoMessages)
	mdb.filter('flagged > ', 5)
	results = mdb.fetch(100)
	if results is not None:	db.delete(results)
	return True
    
class DerMundoGroupMembers(db.Model):
    label = db.StringProperty(default='')
    id = db.StringProperty(default='')
    name = db.StringProperty(default='')
    gender = db.StringProperty(default='')
    profile_url = db.StringProperty(default='')
    joined = db.DateTimeProperty(auto_now_add=True)
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    languages = db.ListProperty(str)
    email = db.StringProperty(default='')
    @staticmethod
    def belongsto(id):
	gdb = db.Query(DerMundoGroupMembers)
	gdb.filter('id = ', id)
	gdb.order('name')
	results = gdb.fetch(50)
    @staticmethod
    def search(label='', maxlen=20):
	gdb = db.Query(DerMundoGroupMembers)
	if len(label) > 0:
	    gdb.filter('label = ', label)
	gdb.order('-joined')
	results = gdb.fetch(maxlen)
	return results
    @staticmethod
    def ismember(label, id):
	gdb = db.Query(DerMundoGroupMembers)
	gdb.filter('label = ', label)
	gdb.filter('id = ', id)
	item = gdb.get()
	if item is not None:
	    return True
	else:
	    return False
    @staticmethod
    def join(label, id, city='', country='', name='', gender='',\
	     profile_url='', language='', email=''):
	if len(label) > 0 and len(id) > 0:
	    gdb = db.Query(DerMundoGroupMembers)
	    gdb.filter('label = ', label)
	    gdb.filter('id = ', id)
	    item = gdb.get()
	    if item is not None:
		return False
	    else:
		item = DerMundoGroupMembers()
		item.label = label
		item.id = id
		item.name = name
		if gender is not None: item.gender = gender
		if profile_url is not None: item.profile_url = profile_url
		if city is not None: item.city = city
		if country is not None: item.country = country
		if email is not None: item.email = email
		if len(language) > 0:
		    languages = item.languages
		    if language not in languages:
			languages.append(language)
			item.languages = languages
		item.put()
		return False
	else:
	    return False
    @staticmethod
    def leave(label, id):
	if len(label) > 0 and len(id) > 0:
	    gdb = db.Query(DerMundoGroupMembers)
	    gdb.filter('label = ', label)
	    gdb.filter('id = ', id)
	    item = gdb.get()
	    if item is not None:
		item.delete()
	    else:
		return False
	else:
	    return False
	
class DerMundoBookMarks(db.Model):
    domain = db.StringProperty(default='')
    url = db.StringProperty(default='')
    title = db.StringProperty(default='')
    description = db.StringProperty(default='')
    language = db.StringProperty(default='')
    tags = db.ListProperty(str)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    votes = db.IntegerProperty(default=0)
    score = db.IntegerProperty(default=0)
    completed = db.BooleanProperty(default=False)
    createdby = db.StringProperty(default='')
    createdbyname = db.StringProperty(default='')
    createdbyprofile = db.StringProperty(default='')
    createdbycity = db.StringProperty(default='')
    createdbycountry = db.StringProperty(default='')
    likedby = db.ListProperty(str)
    group = db.StringProperty(default='')
    @staticmethod
    def search(group='', tag='', language='', maxlen=25):
	bdb = db.Query(DerMundoBookMarks)
	if len(group) > 0:
	    bdb.filter('group = ', group)
	if len(tag) > 0:
	    bdb.filter('tags = ', tag)
	if len(language) > 0:
	    bdb.filter('language = ', language)
	bdb.order('-created')
	results = bdb.fetch(maxlen)
	return results
    @staticmethod
    def create(url='', title='', description='', language='', tags=None, createdby='',\
	       createdbyname='', createdbyprofile='', createdbycity='', createdbycountry='', group=''):
	if len(url) > 0 and len(createdby) > 0:
	    if string.count(url, 'http://') < 1:
		test_url = 'http://' + url
	    else:
		test_url = url
		url = string.replace(url, 'http://','')
	    success = False
	    try:
		result = urlfetch.fetch(url=test_url)
		if result.status_code == 200:
		    success=True
	    except:
		pass
	    if success:
		bdb = db.Query(DerMundoBookMarks)
		bdb.filter('url = ', url)
		if len(group) > 0:
		    bdb.filter('group = ', group)
		else:
		    bdb.filter('createdby = ', createdby)
		item = bdb.get()
		if item is None:
		    item = DerMundoBookMarks()
		    item.url = url
		    if len(group) > 0:
			item.group = group
			item.createdby = createdby
			item.createdbyname = createdbyname
			item.createdbyprofile = createdbyprofile
			item.createdbycity = createdbycity
			item.createdbycountry
		    else:
			item.createdby = createdby
			item.createdbyname = createdbyname
			item.createdbyprofile = createdbyprofile
			item.createdbycity = createdbycity
			item.createdbycountry
		    item.title = title
		    item.description = description
		    item.language = language
		taglist = item.tags
		if tags is not None:
		    if type(tags) is str:
			tags = string.replace(tags, ' ',',')
			tags = string.split(tags,',')
		    if type(tags) is list:
			for t in tags:
			    if len(t) > 1:
				if t not in taglist:
				    taglist.append(t)
		item.taglist = taglist
		item.upvotes = item.upvotes + 1
		item.put()
		return True
	return False
    @staticmethod
    def vote(url, group='', vote=''):
	if len(url) > 0:
	    url = string.replace(url, 'http://','')
	    url = string.replace(url, 'https://', '')
	    bdb = db.Query(DerMundoBookMarks)
	    bdb.filter('url = ', url)
	    if len(group) > 0:
		bdb.filter('group = ', group)
	    item = bdb.get()
	    if item is not None:
		if vote == 'up':
		    item.upvotes = item.upvotes + 1
		    item.votes = item.votes + 1
		    item.score = item.upvotes - item.downvotes
		else:
		    item.downvotes = item.downvotes + 1
		    item.votes = item.votes + 1
		    item.score = item.upvotes - item.downvotes
		item.put()
		return True
	return False

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
                p['url']=url
		p['shorturl']=shorturl
		p['sl']=''
		taskqueue.add(url='/wwl/meta/crawl', params=p, queue_name='spider')
                return item.shorturl
            else:
                return item.shorturl
        return ''
    @staticmethod
    def find(url, email=''):
        url = urllib.unquote_plus(url)
        url = urllib.unquote_plus(url)
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://','')
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
		p=dict()
		p['url']=url
		p['shorturl']=shorturl
		p['sl']=''
		taskqueue.add(url='/wwl/meta/crawl', params=p, queue_name='spider')
                return 'http://www.dermundo.com/x' + shorturl
	    else:
		return 'http://www.dermundo.com/x' + item.shorturl
        return ''
    
class TranslationStats(db.Model):
    datephrase = db.StringProperty(default='')
    url = db.StringProperty(default='')
    shorturl = db.StringProperty(default='')
    title = db.TextProperty(default='')
    description = db.TextProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    language = db.StringProperty(default='')
    translations = db.IntegerProperty(default=0)
    words = db.IntegerProperty(default=0)
    translators = db.ListProperty(str)
    wordlist = db.ListProperty(str)
    @staticmethod
    def search(sl='', tl='', startdate='', enddate='', url='', maxlen=20, tag=''):
	tags = string.split(string.lower(tag), ' ')
	tdb = db.Query(TranslationStats)
	if len(sl) > 0: tdb.filter('sl = ', sl)
	if len(tl) > 0: tdb.filter('tl = ', tl)
	tagcount = 0
	if len(tags) > 0:
	    for t in tags:
		if len(t) > 3:
		    tagcount = tagcount + 1
		    if tagcount < 4:
			tdb.filter('wordlist = ', t)
	if len(url) > 0: tdb.filter('url = ', url)
	if len(startdate) > 0: tdb.filter('datephrase >= ', startdate)
	if len(enddate) > 0: tdb.filter('datephrase <= ', enddate)
	tdb.order('-datephrase')
	translations = tdb.fetch(maxlen)
	return translations
    @staticmethod
    def getstats(url, language='', sl='', tl='', mode='json'):
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://','')
	tdb = db.Query(TranslationStats)
	tdb.filter('url = ', url)
	if len(language) > 0: tdb.filter('language = ', language)
	if len(sl) > 0: tdb.filter('sl = ', sl)
	if len(tl) > 0: tdb.filter('tl = ', tl)
	item = tdb.get()
	stats = dict(
	    translations = item.translations,
	    words = item.words,
	    translators = item.translators,
	    translatorids = item.translatorids,
	)
	if mode == 'json':
	    return demjson.encode(stats)
	else:
	    return stats
    @staticmethod
    def inc(url, shorturl = '', language='', sl='', tl='', wordlist=None, words=None, translator=None, translatorid=None, translatorprofile=None):
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://','')
	timestamp = datetime.datetime.now()
	year = str(timestamp.year)
	month = str(timestamp.month)
	day = str(timestamp.day)
	if len(month) < 2: month = '0' + month
	if len(day) < 2: day = '0' + day
	dp = year + month + day
	tdb = db.Query(TranslationStats)
	tdb.filter('url = ', url)
	tdb.filter('datephrase = ', dp)
	if len(language) > 0: tdb.filter('language = ', language)
	if len(sl) > 0: tdb.filter('sl = ', sl)
	if len(tl) > 0: tdb.filter('tl = ', tl)
	item = tdb.get()
	if item is None:
	    item = TranslationStats()
	    item.url = url
	    item.shorturl = shorturl
	    item.datephrase = dp
	    item.language = language
	    item.sl = sl
	    item.tl = tl
	    metadata = get_summary('http://' + url)
	    title = db.Text(metadata.get('title',''))
	    description = db.Text(metadata.get('description',''))
	    item.title = title
	    item.description = description
	if type(words) is int: item.words = item.words + words
	item.translations = item.translations + 1
	if translator is not None and translatorprofile is not None:
	    translators = item.translators
	    tx = '<a href=' + translatorprofile + '>' + translator + '</a>'
	    if tx not in translators:
		translators.append(tx)
		item.translators = translators
	wlist = item.wordlist
	if type(wordlist) is str:
	    wordlist = string.split(wordlist,' ')
	for w in wordlist:
	    w = db.Text(w, encoding = 'utf_8')
	    if w not in wlist and len(w) < 40 and len(w) > 4:
		wlist.append(string.lower(w))
	item.wordlist = wlist
	item.put()
	
class TrafficStats(db.Model):
    datephrase = db.StringProperty(default='')
    facebookid = db.StringProperty(default='')
    name = db.StringProperty(default='')
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    longitude = db.FloatProperty()
    latitude = db.FloatProperty()
    updated = db.DateTimeProperty(auto_now = True)
    views = db.IntegerProperty(default=0)
    @staticmethod
    def inc(facebookid, name='', city='', country='', latitude=None, longitude=None):
	timestamp = datetime.datetime.now()
	year = str(timestamp.year)
	month = str(timestamp.month)
	day = str(timestamp.day)
	if len(month) < 2:
	    month = '0' + month
	if len(day) < 2:
	    day = '0' + day
	dp = year + month + day
	tdb = db.Query(TrafficStats)
	tdb.filter('datephrase = ', dp)
	tdb.filter('facebookid = ', facebookid)
	item = tdb.get()
	newvisit = False
	if item is None:
	    newvisit = True
	    item = TrafficStats()
	    item.datephrase = dp
	    item.facebookid = facebookid
	    item.name = name
	item.city = city
	item.country = country
	if type(latitude) is float: item.latitude = latitude
	if type(longitude) is float: item.longitude = longitude
	item.views = item.views + 1
	item.put()
	if newvisit:
	    tdb = db.Query(TrafficStats)
	    tdb.filter('datephrase = ', dp)
	    tdb.filter('facebookid = ', 'all')
	    item = tdb.get()
	    if item is None:
		item = TrafficStats()
		item.datephrase = dp
		item.facebookid = 'all'
	    item.views = item.views + 1
	    item.put()
	return True

class UserStats(db.Model):
    globalcount = db.BooleanProperty(default=False)
    year = db.StringProperty()
    month = db.StringProperty()
    day = db.StringProperty()
    users = db.IntegerProperty(default = 0)
    @staticmethod
    def getstats():
	# get total count
	stats = dict()
	sdb = db.Query(UserStats)
	sdb.filter('globalcount = ', True)
	item = sdb.get()
	if item is not None:
	    stats['all']=item.users
	else:
	    stats['all']=0
	# get daily count for this month and last month
	timestamp=datetime.datetime.now()
	month = str(timestamp.month)
	last_month = str(timestamp.month - 1)
	if last_month == '0': last_month=12
	year = str(timestamp.year)
	# get this months records
	sdb = db.Query(UserStats)
	sdb.filter('year = ', year)
	sdb.filter('month = ', month)
	sdb.order('day')
	results = sdb.fetch(31)
	if results is not None:
	    for r in results:
		if len(month) < 2: month = '0' + month
		day = r.day
		if len(day) < 2: day = '0' + day
		stats[year + month + day] = r.users
	sdb = db.Query(UserStats)
	sdb.filter('year = ', year)
	sdb.filter('month = ', last_month)
	sdb.order('day')
	results = sdb.fetch(31)
	if results is not None:
	    for r in results:
		if len(last_month) < 2: last_month = '0' + last_month
		day = r.day
		if len(day) < 2: day = '0' + day
		stats[year + last_month + day] = r.users
	return stats
    @staticmethod
    def inc(country='', city='', locale=''):
	sdb = db.Query(UserStats)
	sdb.filter('globalcount = ', True)
	item = sdb.get()
	if item is None:
	    item = UserStats()
	item.globalcount = True
	item.users = item.users + 1
	item.put()
	timestamp = datetime.datetime.now()
	year = timestamp.year
	month = timestamp.month
	day = timestamp.day
	sdb = db.Query(UserStats)
	sdb.filter('year = ', str(year))
	sdb.filter('month = ', str(month))
	sdb.filter('day = ', str(day))
	sdb.filter('globalcount = ', False)
	item = sdb.get()
	if item is None:
	    item = UserStats()
	    item.year = str(year)
	    item.month = str(month)
	    item.day = str(day)
	item.users = item.users + 1
	item.put()
	LocaleStats.inc(country=country,locale=locale)
	CityStats.inc(city=city,locale=locale)
	return True
    
class LocaleStats(db.Model):
    country = db.StringProperty(default='')
    datephrase = db.StringProperty(default='')
    locale = db.StringProperty(default='')
    users = db.IntegerProperty(default=0)
    createdon = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    @staticmethod
    def inc(country='',locale=''):
	timestamp=datetime.datetime.now()
	dp = str(timestamp.year) + str(timestamp.month)
	ldb = db.Query(LocaleStats)
	ldb.filter('datephrase = ', dp)
	if len(country) > 0:
	    ldb.filter('country = ', country)
	if len(locale) > 0:
	    ldb.filter('locale = ', locale)
	item = ldb.get()
	if item is None:
	    item = LocaleStats()
	    item.datephrase = dp
	    item.country = country
	    item.locale = locale
	item.users = item.users + 1
	item.put()

class CityStats(db.Model):
    city = db.StringProperty(default='')
    datephrase = db.StringProperty(default='')
    locale = db.StringProperty(default='')
    users = db.IntegerProperty(default=0)
    createdon = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    @staticmethod
    def inc(city='',locale=''):
	timestamp=datetime.datetime.now()
	dp = str(timestamp.year) + str(timestamp.month)
	ldb = db.Query(CityStats)
	ldb.filter('datephrase = ', dp)
	if len(city) > 0:
	    ldb.filter('city = ', city)
	if len(locale) > 0:
	    ldb.filter('locale = ', locale)
	item = ldb.get()
	if item is None:
	    item = CityStats()
	    item.datephrase = dp
	    item.city = city
	    item.locale = locale
	item.users = item.users + 1
	item.put()
    
class UserStatsWorker(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	country = self.request.get('country')
	city = self.request.get('city')
	locale = self.request.get('locale')
	UserStats.inc(country=country, city=city, locale=locale)
	self.response.out.write('ok')

class FBLocales():
    locales=dict()
    locales['ca']='ca_ES'
    locales['cs']='cs_CZ'
    locales['cy']='cy_GB'
    locales['da']='da_DK'
    locales['de']='de_DE'
    locales['eu']='eu_ES'
    locales['ck']='ck_US'
    locales['en']='en_US'
    locales['es']='es_LA'
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
    locales['af']='af_ZA'
    locales['sq']='sq_AL'
    locales['hy']='hy_AM'
    locales['az']='az_AZ'
    locales['be']='be_BY'
    locales['bn']='bn_IN'
    locales['bs']='bs_BA'
    locales['bg']='bg_BG'
    locales['hr']='hr_HR'
    locales['eo']='eo_EO'
    locales['et']='et_EE'
    locales['fo']='fo_FO'
    locales['el']='el_GR'
    locales['gu']='gu_IN'
    locales['hi']='hi_IN'
    locales['is']='is_IS'
    locales['id']='id_ID'
    locales['jv']='jv_ID'
    locales['kn']='kn_ID'
    locales['kk']='kk_KZ'
    locales['la']='la_VA'
    locales['lv']='lv_LV'
    locales['it']='it_IT'
    locales['mk']='mk_MK'
    locales['ms']='ms_MY'
    locales['mt']='mt_MT'
    locales['mn']='mn_MN'
    locales['ne']='ne_NP'
    locales['pa']='pa_IN'
    locales['rm']='rm_CH'
    locales['sa']='sa_IN'
    locales['sr']='sr_RS'
    locales['so']='so_SO'
    locales['sw']='sw_KE'
    locales['tl']='tl_PH'
    locales['ta']='ta_IN'
    locales['tt']='tt_RU'
    locales['te']='te_IN'
    locales['ml']='ml_IN'
    locales['uk']='uk_UA'
    locales['uz']='uz_UZ'
    locales['vi']='vi_VN'
    locales['xh']='xh_ZA'
    locales['zu']='zu_ZA'
    locales['km']='km_KH'
    locales['tg']='tg_TJ'
    locales['he']='he_IL'
    locales['ur']='ur_PK'
    locales['fa']='fa_IR'
    locales['sy']='sy_SY'
    locales['yi']='yi_DE'
    locales['gn']='gn_PY'
    locales['qu']='qu_PE'
    locales['ay']='ay_BO'
    locales['se']='se_NO'
    locales['ps']='ps_AF'
    def lookup(self,language):
        locale = self.locales.get(language,'')
        if len(locale) > 0:
            return locale
	
class TranslationQueue(db.Model):
    url = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    languages = db.ListProperty(str)
    title = db.StringProperty(default='')
    description = db.TextProperty(default='')
    reason = db.TextProperty(default='')
    tags = db.ListProperty(str)
    created = db.DateTimeProperty(auto_now_add=True)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    votes = db.IntegerProperty(default=0)
    score = db.FloatProperty(default=0.0)
    createdbyid = db.StringProperty(default='')
    createdbyname = db.StringProperty(default='')
    createdbyprofile = db.StringProperty(default='')
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    translations = db.IntegerProperty(default=0)
    words = db.IntegerProperty(default=0)
    translatedto = db.ListProperty(str)
    @staticmethod
    def add(url='', sl='en', languages=None, title='', description='',\
	    reason='', tags=None, createdbyid='', createdbyname='',\
	    createdbyprofile = '', city='', country=''):
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'https://', '')
	tdb = db.Query(TranslationQueue)
	tdb.filter('url = ', url)
	item = tdb.get()
	if item is None:
	    item = TranslationQueue()
	    item.url = url
	item.sl = sl
	item.title = title
	item.description = description
	item.reason = reason
	item.createdbyid = createdbyid
	item.createdbyname = createdbyname
	item.createdbyprofule = createdbyprofile
	item.city = city
	item.country = country
	if languages is not None:
	    if type(languages) is str:
		languages = string.replace(languages, ' ',',')
		languages = string.split(languages,',')
	    if type(languages) is list:
		langs = item.languages
		for l in languages:
		    if l not in langs:
			langs.append(l)
		item.languages = langs
	if tags is not None:
	    if type(tags) is str:
		tags = string.replace(tags,' ',',')
		tags = string.split(tags,',')
	    if type(tags) is list:
		taglist = item.tags
		for t in tags:
		    if t not in taglist:
			taglist.append(t)
		item.tags = taglists
	item.put()
	return True
    @staticmethod
    def find(sl='', tl='', tag=''):
	tdb = db.Query(TranslationQueue)
	tdb.order('-created')
	results = tdb.fetch(10)
	return results
    @staticmethod
    def translate(url,language, words):
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://','')
	tdb = db.Query(TranslationQueue)
	tdb.filter('url = ', url)
	item = tdb.get()
	if item is None:
	    item = TranslationQueue()
	    item.url = url
	if type(words) is int:
	    item.words = item.words + words
	item.translations = item.translations + 1
	translatedto = item.translatedto
	if language not in translatedto:
	    translatedto.append(language)
	    item.translatedto = translatedto
	item.put()
	return True
    @staticmethod
    def vote(url, vote):
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://', '')
	tdb = db.Query(TranslationQueue)
	tdb.filter('url = ','')
	item = tdb.get()
	if item is not None:
	    upvotes = item.upvotes
	    downvotes = item.downvotes
	    votes = item.votes
	    score = item.score
	    if vote == 'up':
		upvotes = upvotes + 1
	    else:
		downvotes = downvotes + 1
	    votes = votes + 1
	    score = float((upvotes - downvotes) / votes)
	    item.upvotes = upvotes
	    item.downvotes = downvotes
	    item.votes = votes
	    item.score = score
	    item.put()
	    return True
	return False

class User(db.Model):
    id = db.StringProperty(required=True)
    service = db.StringProperty(default='facebook')
    email = db.StringProperty(default='')
    about_me = db.StringProperty(default='')
    beta = db.BooleanProperty(default=False)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    city = db.StringProperty(default='')
    country = db.StringProperty(default='')
    latitude = db.FloatProperty(default=None)
    longitude = db.FloatProperty(default=None)
    gender = db.StringProperty(default='')
    locale = db.StringProperty(default='')
    locales = db.ListProperty(str)
    following = db.ListProperty(str)
    followers = db.ListProperty(str)
    translations = db.IntegerProperty(default=0)
    words = db.IntegerProperty(default=0)
    languages = db.ListProperty(str)
    scores = db.IntegerProperty(default=1)
    avgscore = db.FloatProperty(default=5.0)
    rawscore = db.IntegerProperty(default=5)
    spam = db.IntegerProperty(default=0)
    blocked = db.BooleanProperty(default=False)
    scoredby = db.ListProperty(str)
    urlstranslated = db.ListProperty(str)
    @staticmethod
    def getscore(id):
	udb = db.Query(User)
	udb.filter('id = ', id)
	item = udb.get()
	if item is not None:
	    userscore=dict(
		score = item.avgscore,
		scores = item.scores,
		spam = item.spam,
	    )
	    return userscore
	else:
	    return
    @staticmethod
    def score(author, score, facebookid='', spam=False):
	udb = db.Query(User)
	udb.filter('id = ', author)
	item = udb.get()
	if item is not None:
	    if type(score) is int:
		item.rawscore = item.rawscore + score
		item.scores = item.scores + 1
		item.avgscore = float(float(item.rawscore) / item.scores)
	    if spam:
		item.spam = item.spam + 1
	    scoredby = item.scoredby
	    if len(facebookid) > 0:
		if facebookid not in scoredby:
		    scoredby.append(facebookid)
		    item.scoredby = scoredby
	    item.put()
	    return True
	return False
    @staticmethod
    def recent(city='', country='', maxlen=10):
	m = md5.new()
	m.update(city)
	m.update(country)
	md5hash = str(m.hexdigest())
	results = memcache.get('/recent/users/' + md5hash)
	if results is not None:
	    return results
	udb = db.Query(User)
	if len(city) > 0:
	    udb.filter('city = ', city)
	if len(country) > 0:
	    udb.filter('country = ', country)
	udb.order('-updated')
	results = udb.fetch(maxlen)
	if results is not None:
	    for r in results:
		r.city = string.replace(r.city, ' ', '_')
	    memcache.set('/recent/users/' + md5hash, results, 300)
	return results
    @staticmethod
    def translate(id, sl, tl, words, url=''):
	udb = db.Query(User)
	udb.filter('id = ', id)
	item = udb.get()
	if item is not None:
	    languages = item.languages
	    if sl not in languages:
		languages.append(sl)
	    if tl not in languages:
		languages.append(tl)
	    item.languages = languages
	    if len(url) > 0:
		url = string.replace(url,'http://','')
		url = string.replace(url, 'https://','')
		urlstranslated = item.urlstranslated
		if url not in urlstranslated:
		    urlstranslated.append(url)
		item.urlstranslated = urlstranslated
	    if type(words) is int:
		item.words = item.words + words
	    item.translations = item.translations + 1
	    item.put()
	    return True
	return False
    @staticmethod
    def fetch(id):
	udb = db.Query(User)
	udb.filter('id = ', id)
	item = udb.get()
	return item
    @staticmethod
    def update(id, email=None, city=None, country=None, latitude=None, longitude = None, locale=None, beta=True):
	udb = db.Query(User)
	udb.filter('id = ', id)
	item = udb.get()
	if item is not None:
	    if email: item.email = email
	    if city: item.city = city
	    if country: item.country = country
	    if latitude: item.latitude = latitude
	    if longitude: item.longitude = longitude
	    if locale: item.locale = locale
	    if beta: item.beta = True
	    item.put()
	    return True
	return False
    def follow(id, followid):
	udb = db.Query(User)
	udb.filter('id = ', id)
	item = udb.get()
	if item is not None:
	    followlist = item.following
	    if followid not in followlist:
		followlist.append(followid)
		item.following = followlist
		item.put()
	udb = db.Query(User)
	udb.filter('id = ', followid)
	item = udb.get()
	if item is not None:
	    followers = item.followers
	    if followid not in followers:
		followers.append(followid)
		item.followers = followers
	    item.put()
	    return True
	return False
    def unfollow(id, followid):
	udb = db.Query(User)
	udb.filter('id = ', id)
	item = udb.get()
	if item is not None:
	    followlist = item.following
	    if followid in followlist:
		followlist.remove(followid)
		item.following=followlist
		item.put()
	udb = db.Query(User)
	udb.filter('id = ', followid)
	item = udb.get()
	if item is not None:
	    followers = item.followers
	    if followid in followers:
		followers.remove(followid)
		item.followers = followers
		item.put()
		return True
	return False

class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

The property is lazy-loaded on first access, using the cookie saved
by the Facebook JavaScript SDK to determine the user ID of the active
user. See http://developers.facebook.com/docs/authentication/ for
more information.
"""
    ttl = int(Settings.get('memcache_ttl'))
    texts = dict()
    def localize(self, language):
	txts = TextObjects.getall(mode='dict')
	ttxts = TextTranslations.getall(language, mode='dict')
	txts.update(ttxts)
	return txts
    def direction(self, language):
	rtl = ['ar', 'fa', 'he', 'ur']
	if language in rtl:
	    return 'RTL'
	else:
	    return 'LTR'
    @property
    def language(self):
	if not hasattr(self, "_language"):
	    self._language = 'en'
	    user = self.current_user
	    if not user:
		try:
		    locales = string.split(self.request.headers['Accept-Language'],',')
		except:
		    locales = 'en-us'
		langloc = string.split(locales[0],'-')
		if len(langloc[0]) > 1:
		    self._language = langloc[0]
	    else:
		try:
		    locale = user.locale
		    langloc = string.split(locale, '_')
		    if len(langloc[0]) > 1:
			self._language = langloc[0]
		except:
		    pass
	return self._language
    @property
    def locale(self):
	if not hasattr(self, "_locale"):
	    self._locale = None
	    if not self.current_user:
		try:
		    locales = string.split(self.request.headers['Accept-Language'],',')
		except:
		    locales = 'en-us'
		found_locale = False
		language = ''
		locale = ''
		for l in locales:
		    langloc = string.split(l, '-')
		    if len(language) < 1:
			language = langloc[0]
		    if not found_locale:
			f = FBLocales()
			locale = f.lookup(langloc[0])
			if locale is not None:
			    if len(locale) > 1:
				found_locale=True
				self._locale = locale
		if not found_locale:
		    self._locale = 'en_US'
	    else:
		user = self.current_user
		self._locale = user.locale
	return self._locale
    @property
    def location(self):
	if not hasattr(self, "_location"):
	    self._location = None
	    remote_addr = self.request.remote_addr
	    self._location = geolocate(remote_addr)
	return self._location
    @property
    def current_user(self):
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = User.get_by_key_name(cookie["uid"])
		location = geolocate(self.request.remote_addr)
		if location is not None:
		    city = location.get('city','')
		    country = location.get('country','')
		    try:
			latitude = float(location.get('latitude',''))
			longitude = float(location.get('longitude',''))
		    except:
			latitude = None
			longitude = None
                if not user:
		    localelist = string.split(self.request.headers['Accept-Language'],',')
		    locales = list()
		    for l in localelist:
			langloc = string.split(l, ';')
			locales.append(langloc[0])
		    if location is not None:
			city = location.get('city','')
			country = location.get('country','')
			try:
			    latitude = float(location.get('latitude',''))
			    longitude = float(location.get('longitude',''))
			except:
			    latitude = None
			    longitude = None
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
		    email = profile.get('email')
		    locale = profile.get('locale')
		    try:
			langloc = string.split(locale, '_')
			lang = langloc[0]
			id = profile.get('id')
			text = TextTranslations.translate('joined_dermundo', lang)
			PublishToFeed(id, cookie["access_token"], language=lang, msg=text, link='http://www.dermundo.com')
		    except:
			pass
		    if latitude is not None:
			user = User(key_name=str(profile["id"]),
				    id=str(profile["id"]),
				    name=profile.get('name',''),
				    gender=profile.get('gender',''),
				    city=city,
				    country=country,
				    latitude=latitude,
				    longitude=longitude,
				    locale = profile["locale"],
				    locales = locales,
				    profile_url=profile.get('link',''),
				    email = profile.get('email',''),
				    about_me = profile.get('about_me',''),
				    access_token=cookie["access_token"])
		    else:
			user = User(key_name=str(profile["id"]),
				    id=str(profile["id"]),
				    name=profile.get('name',''),
				    gender=profile.get('gender',''),
				    city=city,
				    country=country,
				    locale = profile.get('locale',''),
				    locales = locales,
				    profile_url=profile.get('link',''),
				    email = profile.get('email',''),
				    about_me = profile.get('about_me',''),
				    access_token=cookie["access_token"])
                    user.put()
		    p=dict()
		    p['name']=profile['name']
		    p['city']=city
		    p['country']=country
		    p['locale']=profile['locale']
		    taskqueue.add(url='/wwl/userstatsworker', queue_name='counter', params=p)
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
		    user.city = city
		    user.country = country
                    user.put()
		p = dict()
		p['facebookid']= str(user.id)
		p['name']= user.name
		p['city']= user.city
		p['country']= user.country
		p['latitude']=str(user.latitude)
		p['longitude']=str(user.longitude)
		taskqueue.add(url='/wwl/trafficworker', params=p, queue_name='counter')
                self._current_user = user
        return self._current_user

class HomeHandler(BaseHandler):
    def get(self):
	url = self.request.get('u')
	if len(url) > 0:
	    url = string.replace(url, 'http://', '')
	    url = string.replace(url, 'https://', '')
	    self.redirect('http://www.dermundo.com/' + url)
	locale = self.locale
	language = self.language
	direction = self.direction(language)
	location = self.location
        userip = self.request.remote_addr
	texts = self.localize(language)
        template_values=dict(
            tagline = texts.get('tagline', ''),
            menu = '',
            sharethis_header = sharethis_header,
            sharethis_button = sharethis_button,
            social_translation = texts.get('social_translation',''),
            introduction = texts.get('introduction',''),
            google_analytics = google_analytics_header,
            copyright = pro(language,copyright),
            wordpress_prompt = texts.get('wordpress_prompt',''),
            firefox_prompt = texts.get('firefox_prompt',''),
            instructions = texts.get('instructions',''),
            instructions_prompt = texts.get('instructions_prompt',''),
            share_this_page = texts.get('share_this_page',''),
            share_this_button = sharethis_button,
            professional_translation = texts.get('professional_translation',''),
            email_address = texts.get('email_address',''),
            speaklike_password = texts.get('speaklike_password',''),
            translate_button = texts.get('translate',''),
            facebook_login_prompt = texts.get('facebook_login_prompt',''),
	    firefox_translator = texts.get('firefox_translator',''),
	    wordpress_translator = texts.get('wordpress_translator',''),
	    for_publishers = texts.get('for_publishers',''),
	    for_journalists = texts.get('for_journalists',''),
            locale = locale,
	    language = language,
	    direction = direction,
        )
        path = os.path.join(os.path.dirname(__file__), "home.html")
        args = dict(current_user=self.current_user,
                    facebook_app_id=FACEBOOK_APP_ID)
        args.update(template_values)
        self.response.out.write(template.render(path, args))
	
class translator():
    name = ''
    city = ''
    country = ''
	
class ProxyHandler(BaseHandler):
    def get(self, shorturl='', force_language=''):
	locale = self.locale
	language = self.language
	location = self.location
	userip = self.request.remote_addr
	current_user = self.current_user
	cookies = Cookies(self)
	if current_user:
	    cookies['wwl_login']='y'
	    cookies['wwl_name']=current_user.name
	    cookies['wwl_facebookid']=str(current_user.id)
	    cookies['wwl_city']=location.get('city')
	    cookies['wwl_country']=location.get('latitude')
	    try:
		cookies['wwl_latitude']=str(location['latitude'])
		cookies['wwl_longitude']=str(location['longitude'])
	    except:
		pass
	url = DerMundoProjects.geturl(shorturl)
	if url is not None:
	    if len(url) > 0:
		if string.count(url, 'http://') > 0:
		    url = string.replace(url,'http://','')
		self.redirect('http://www.dermundo.com/' + url)
	    else:
		self.redirect('http://www.dermundo.com/dermundo/notfound.html')
	else:
	    self.redirect('http://www.dermundo.com/dermundo/notfound.html')
	
class CreateProject(BaseHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
	url = urllib.unquote_plus(self.request.get('u'))
	if len(url) < 1:
	    url = urllib.unquote_plus(self.request.get('url'))
	if string.count(url, 'http://') < 1:
	    url = 'http://' + url
	shorturl = DerMundoProjects.add(url)
	url = string.replace(url, 'http://', '')
	self.redirect('http://www.dermundo.com/' + url)
			  
class LoginHandler(BaseHandler):
    def get(self):
	base_url = self.request.get('base_url')
	url = self.request.get('url')
	language = self.language
	locale = self.locale
        path = os.path.join(os.path.dirname(__file__), "proxylogin.html")
        args = dict(current_user=self.current_user,
                    facebook_app_id=FACEBOOK_APP_ID)
	template_values = dict(
	    copyright = copyright,
	    language = language,
	    locale = locale,
	)
        args.update(template_values)
        self.response.out.write(template.render(path, args))
	
class TrafficWorker(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	facebookid = self.request.get('facebookid')
	name = self.request.get('name')
	remote_addr = self.request.remote_addr
	city = self.request.get('city')
	country = self.request.get('country')
	try:
	    latitude = float(self.request.get('latitude'))
	    longitude = float(self.request.get('longitude'))
	except:
	    latitude = None
	    longitude = None
	TrafficStats.inc(facebookid, name=name, city=city, country=country, latitude=latitude, longitude=longitude)
	self.response.out.write('ok')
	
class BetaHandler(BaseHandler):
    def get(self):
	email = self.request.get('email')
	current_user = self.current_user
	language = self.language
	direction = self.direction(language)
	locale = self.locale
	url = self.request.get('u')
	texts = self.localize(language)
	language_select = dict(
	    language_select = languages.select(selected = language),
	)
	#if current_user is not None:
	q = self.request.get('q')
	translation = self.request.get('translation')
	city = string.replace(self.request.get('city'),'_',' ')
	country = self.request.get('country')
	path = os.path.join(os.path.dirname(__file__), "search.html")
	args = dict(current_user=self.current_user,
		    facebook_app_id=FACEBOOK_APP_ID)
	args.update(texts)
	if len(q) > 0:
	    issearch=True
	    translationview = False
	else:
	    translationview = True
	    issearch=False
	#if not translationview:
	#    messages = DerMundoMessages.search(msgtype='stream', tag=q, city=city, country=country)
	#else:
	#    messages = None
	messages = None
	grouplist = DerMundoGroups.search(maxlen=3)
	vistors = User.recent(city=city, country=country)
	if len(q) > 0:
	    translations_from = TranslationStats.search(sl=self.language, tag=q)
	    translations_to = TranslationStats.search(tl=self.language, tag=q)
	else:
	    translations_from = TranslationStats.search(sl=self.language)
	    translations_to = TranslationStats.search(tl=self.language)
	language_select = Languages.select(selected=self.language)
	template_values = dict(
	    issearch = issearch,
	    grouplist = grouplist,
	    language_select = language_select,
	    messages = messages,
	    visitors = vistors,
	    language = language,
	    locale = locale,
	    direction = direction,
	    translations_from = translations_from,
	    translations_to = translations_to,
	    google_analytics = google_analytics_header,
	)
	args.update(template_values)
	self.response.out.write(template.render(path, args))
	return
	    
class ProfileHandler(BaseHandler):
    def get(self, id):
	current_user = self.current_user
	locale = self.locale
	language = self.language
	direction = self.direction(language)
	profile = User.fetch(id)
	path = os.path.join(os.path.dirname(__file__), "profile.html")
	args = dict(current_user=self.current_user,
		    facebook_app_id=FACEBOOK_APP_ID)
	messages = DerMundoMessages.search(sender=id)
	groups = DerMundoGroupMembers.belongsto(id)
	texts = self.localize(language)
	args.update(texts)
	template_values = dict(
	    profile = profile,
	    messages = messages,
	    groups = groups,
	    locale = locale,
	    words = words,
	    word_count = User.words,
	    language = language,
	    direction = direction,
	)
	args.update(template_values)
	self.response.out.write(template.render(path, args))
	
class Tag(db.Model):
    date = db.DateTimeProperty()

class PurgeHandler(webapp.RequestHandler):
    def get(self):
	tdb = db.Query(Tag)
	results = tdb.fetch(100)
	if results is not None:
	    db.delete(results)
	self.response.out.write('ok')
	
class MetaDataCrawlHandler(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	url = self.request.get('url')
	shorturl = self.request.get('shorturl')
	sl = self.request.get('sl')
	DerMundoMetaData.crawl(url=url, shorturl=shorturl, sl=sl)
	self.response.out.write('ok')
	
class MetaDataFindHandler(webapp.RequestHandler):
    def get(self):
	url = self.request.get('url')
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'https://','')
	url = string.replace(url, 'www.dermundo.com/','')
	if len(url) > 0:
	    shorturl=DerMundoProjects.find(url)
	else:
	    shorturl=None
	if shorturl is not None:
	    self.response.out.write(shorturl)
	else:
	    self.error(404)
	    self.response.out.write('Not Found')

class MetaDataGetHandler(webapp.RequestHandler):
    def get(self):
	url = self.request.get('url')
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'https://','')
	url = string.replace(url, 'www.dermundo.com/','')
	language = self.request.get('language')
	text = ''
	if len(url) > 0:
	    metadata = DerMundoMetaData.find(url=url, language=language)
	    text = demjson.encode(metadata)
	self.response.out.write(text)
	    
class MetaDataSubmitHandler(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	facebookid = self.request.get('facebookid')
	name = self.request.get('name')
	profile_url = self.request.get('profile_url')
	url = self.request.get('url')
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://', '')
	url = string.replace(url, 'www.dermundo.com/','')
	language = self.request.get('language')
	title = self.request.get('title')
	description = self.request.get('description')
	keywords = self.request.get('keywords')
	keywords = string.replace(keywords, ' ',',')
	keywords = string.split(keywords, ',')
	DerMundoHeaders.submit(url=url, translatorid=facebookid, translatorname=name, translatorprofile=profile_url, \
			       language=language, title=title, description=description, keywords=keywords)
	self.response.out.write('ok')
	
class TranslationSubmitStats(webapp.RequestHandler):
    def post(self):
	url = self.request.get('url')
	translator = self.request.get('facebookid')
	language = self.request.get('language')
	title = self.request.get('title')
	words = int(self.request.get('words'))
	shorturl = self.request.get('shorturl')
	TranslationStats.inc(url, shorturl=shorturl, language=language, words=words, translator=translator)
	self.response.out.write('ok')
	
class TranslationStatsHandler(webapp.RequestHandler):
    def get(self):
	url = self.request.get('url')
	language = self.request.get('language')
	self.response.out.write(TranslationStats.getstats(url, language=language))
	
class FirefoxHelpHandler(BaseHandler):
    def get(self):
	current_user = self.current_user
	locale = self.locale
	language = self.language
	path = os.path.join(os.path.dirname(__file__), "help.html")
	args = dict(current_user=self.current_user,
		    facebook_app_id=FACEBOOK_APP_ID)
	template_values = dict(
	    tagline = pro(language, 'Translate the world with your friends'),
	    locale = locale,
	    firefox_translator = pro(language, firefox_translator),
	    wordpress_translator = pro(language, wordpress_translator),
	)
	args.update(template_values)
	self.response.out.write(template.render(path, args))
	
class SubmitTranslationHandler(BaseHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	current_user = self.current_user
	if current_user:
	    sl = self.request.get('sl')
	    tl = self.request.get('tl')
	    st = self.request.get('st')
	    st = clean(st)
	    tt = self.request.get('tt')
	    tt = clean(tt)
	    words = len(string.split(tt, ' '))
	    url = self.request.get('url')
	    url = string.replace(url, 'http://','')
	    facebookid = str(current_user.id)
	    access_token = current_user.access_token
	    username = current_user.name
	    locale = current_user.locale
	    langloc = string.split(locale, '_')
	    language = langloc[0]
	    location = self.location
	    city = location.get('city','')
	    country = location.get('country','')
	    profile_url = current_user.profile_url
	    remote_addr = self.request.remote_addr
	    translations = memcache.get('/translating/' + facebookid + '/' + url)
	    feed_posts = memcache.get('/feed_posts/' + facebookid)
	    if translations is None and feed_posts < 6:
		translations = 1
		if feed_posts is None:
		    feed_posts = 1
		else:
		    feed_posts = feed_posts + 1
		memcache.set('/translating/' + facebookid + '/' + url, translations, 15000)
		memcache.set('/feed_posts/' + facebookid, feed_posts, 10000)
		msg = pro(language, 'I started translating a new website using DerMundo. Help me translate and share this with the world.')
		PublishToFeed(facebookid, access_token, msg=msg, language=language, link='http://www.dermundo.com/' + url)
	    else:
		memcache.set('/translating/' + facebookid + '/' + url, 1, 15000)
		if feed_posts is None:
		    memcache.set('/feed_posts/' + facebookid, 1, 10000)
		else:
		    memcache.set('/feed_posts/' + facebookid, feed_posts + 1, 10000)
	    #tdb = Translation()
	    #tdb.sl=sl
	    #tdb.tl=tl
	    #tdb.city=city
	    #tdb.country=country
	    #tdb.username=username
	    #tdb.remote_addr=remote_addr
	    #tdb.facebookid=facebookid
	    #tdb.anonymous=False
	    #tdb.professional=False
	    #tdb.human=True
	    #tdb.st=st
	    #tdb.tt=tt
	    #tdb.put()
	    if len(tt) > 2:
		Translation.submit(sl=sl, tl=tl, st=st, tt=tt,\
				   username=username, facebookid=facebookid,\
				   remote_addr=remote_addr,\
				   profile_url=profile_url, city=city, country=country,\
				   url=url)
		User.translate(facebookid, sl, tl, words, url=url)
		TranslationStats.inc(url, shorturl='', sl=sl, tl=tl, words=words, wordlist = st + ' ' + tt, translator=username, translatorid=facebookid, translatorprofile = profile_url)
	    self.response.out.write('ok')
	else:
	    self.error(401)
	    self.response.out.write('Facebook login required to edit translations')
	    
class SubmitTranslationWorker(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	sl = self.request.get('sl')
	tl = self.request.get('tl')
	st = clean(self.request.get('st'))
	tt = clean(self.request.get('tt'))
	words = len(string.split(tt,' '))
	url = self.request.get('url')
	remote_addr = self.request.get('remote_addr')
	username = self.request.get('username')
	facebookid = self.request.get('facebookid')
	profile_url = self.request.get('profile_url')
	location = geolocate(remote_addr)
	city = location.get('city')
	country = location.get('country')
	latitude = float(location.get('latitude'))
	longitude = float(location.get('longitude'))
	userscore = User.getscore(facebookid)
	allow = True
	#if userscore is not None:
	#    scores = userscore['scores']
	#    avgscore = userscore['score']
	#    spam = userscore['spam']
	#    if scores > 10 and avgscore < 2.5: allow=False
	#if allow:
	Translation.submit(sl=sl, tl=tl, st=st, tt=tt,\
			   username=username, facebookid=facebookid,\
			   remote_addr=remote_addr,\
			   profile_url=profile_url, city=city, country=country,\
			   url=url)
	User.translate(facebookid, sl, tl, words, url=url)
	
class ScoreHandler(BaseHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	current_user = self.current_user
	guid = self.request.get('guid')
	score = self.request.get('score')
	spam = self.request.get('spam')
	if spam == 'y':
	    spam = True
	else:
	    spam = False
	try:
	    score = int(score)
	    validquery=True
	except:
	    validquery=False
	if len(guid) < 8:
	    validquery=False
	if not current_user:
	    self.error(401)
	    self.response.out.write('Facebook login required to score translations.')
	    return
	if not validquery:
	    self.error(400)
	    self.response.out.write('Invalid score')
	    return
	author = Translation.getfbuser(guid)
	if author is not None:
	    facebookid = str(current_user.id)
	    if User.score(author, score, facebookid=facebookid, spam=spam):
		self.response.out.write('ok')
	    else:
		self.error(400)
		self.response.out.write('Score failed')
	else:
	    self.error(400)
	    self.response.out.write('Translation not found.')
	    
class URLTranslationHandler(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	url = self.request.get('url')
	tl = self.request.get('tl')
	text = memcache.get('/urlhistory/' + tl + '/' + url)
	if text is not None:
	    return self.response.out.write(text)
	results = Translation.getbyurl(url, tl)
	translations = list()
	if results is not None:
	    for r in results:
		translation = dict(
		    guid = r.guid,
		    date = str(r.date),
		    sl = r.sl,
		    tl = r.tl,
		    st = r.st,
		    tt = r.tt,
		    url = r.url,
		    spam = r.spam,
		    professional = r.professional,
		    username = r.username,
		    facebookid = r.facebookid,
		    profile_url = r.profile_url,
		    anonymous = r.anonymous,
		    city = r.city,
		    country = r.country,
		    latitude = r.latitude,
		    longitude = r.longitude,
		    md5hash = r.md5hash,
		    machine = r.machine,
		    spamvotes = r.spamvotes,
		    useravgscore = r.useravgscore,
		    userrawscore = r.userrawscore,
		    userscores = r.userscores,
		)
		translations.append(translation)
	text = demjson.encode(translations)
	memcache.set('/urlhistory/' + tl + '/' + url, text, 60)
	return self.response.out.write(text)
	
class GetTranslationHandler(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	lsp='speaklike'
	sl = self.request.get('sl')
	tl = self.request.get('tl')
	st = clean(self.request.get('st'))
	url = self.request.get('url')
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'http://', '')
	lspusername = self.request.get('lspusername')
	lsppw = self.request.get('lsppw')
	output = self.request.get('output')
	if len(lsp) > 0:
	    result = LSP.get(sl=sl, tl=tl, st=st, url=url, lsp=lsp, lspusername=lspusername, lsppw=lsppw, worker=True)
	    if result is not None:
		if type(result) is dict:
		    tt = result.get('tt','')
		    guid = result.get('guid','')
		    username = 'speaklike'
		    if len(tt) > 0:
			Translation.submit(guid=guid, sl=sl, tl=tl, st=st, tt=tt, username=username, url=url, professional=True, overwrite=True)
			if output == 'json':
			    self.response.out.write(demjson.encode(result))
			else:
			    self.response.out.write(text)
	    else:
		self.response.out.write('')
	else:
	    self.response.out.write('')

class HTMLHandler(BaseHandler):
    def get(self, page):
	if page == 'notfound.html':
	    self.error(404)
	    self.response.out.write('Page Not Found')
	else:
	    email = self.request.get('email')
	    current_user = self.current_user
	    language = self.language
	    direction = self.direction(language)
	    locale = self.locale
	    url = self.request.get('u')
	    texts = self.localize(language)
	    path = os.path.join(os.path.dirname(__file__), page + '.html')
	    args = dict(current_user=self.current_user,
			facebook_app_id=FACEBOOK_APP_ID)
	    args.update(texts)
	    template_values = dict(
		sharethis_header = sharethis_header,
		sharethis_button = sharethis_button,
		google_analytics = google_analytics_header,
		share_this_button = sharethis_button,
		locale = locale,
		language = language,
		direction = direction,
	    )
	    args.update(template_values)
	    self.response.out.write(template.render(path, args))
	    
class GroupHandler(BaseHandler):
    def get(self, label=''):
	self.requesthandler(label)
    def post(self, label):
	self.requesthandler(label)
    def requesthandler(self, label):
	label = string.lower(label)
	if label == 'create':
	    user = self.current_user
	    locale = self.locale
	    location = self.location
	    langloc = string.split(locale,'_')
	    language = langloc[0]
	    city = location.get('city','')
	    country = location.get('country','')
	    label = self.request.get('label')
	    title = self.request.get('title')
	    description = self.request.get('description')
	    discussionurl = self.request.get('discussionurl')
	    facebookurl = self.request.get('facebookurl')
	    rssfeed = self.request.get('rssfeedurl')
	    tags = self.request.get('tags')
	    if user:
		name = user.name
		gender = user.gender
		city = user.city
		country = user.country
		email = user.email
		if email is None: email=''
		if DerMundoGroups.create(label, title, description, tags=tags , languages=language, \
					 createdby=user.id, createdbyname=user.name,\
					 createdbyprofile=user.profile_url, email=email,\
					 discussionurl=discussionurl, facebookurl=facebookurl,\
					 rssfeed=rssfeed):
		    DerMundoGroupMembers.join(label, user.id, language=language, city=user.city,\
					country=user.country, name=user.name, profile_url=user.profile_url)
		    self.redirect('/groups/' + label)
		else:
		    self.redirect('/')
	    else:
		self.redirect('/')
	elif label == 'savebookmark':
	    group = self.request.get('group')
	    url = self.request.get('url')
	    title = self.request.get('title')
	    description = self.request.get('description')
	    language = self.request.get('language')
	    tags = self.request.get('tags')
	    feed = self.request.get('feed')
	    current_user = self.current_user
	    if current_user:
		msg = 'Help me translate this website on Der Mundo.'
		createdby = current_user.id
		createdbyname = current_user.name
		createdbyprofile = current_user.profile_url
		createdbycity = current_user.city
		createdbycountry = current_user.country
		result = DerMundoBookMarks.create(url=url, group=group, title=title, description=description,\
						  language=language, tags=tags, createdby=createdby,\
						  createdbyname=createdbyname,\
						  createdbyprofile=createdbyprofile,\
						  createdbycity=createdbycity, createdbycountry=createdbycountry)
		if feed == 'y':
		    PublishToFeed(current_user.id, current_user.access_token, language=self.language,\
				  link = url, msg=msg)
	    self.redirect('/groups/'+ group)
	else:
	    current_user = self.current_user
	    locale = self.locale
	    language = self.language
	    join = self.request.get('join')
	    leave = self.request.get('leave')
	    if join == 'y':
		DerMundoGroups.join(label, current_user.id, city=current_user.city,\
				    country=current_user.country, language = locale, \
				    name=current_user.name, email=current_user.email, \
				    profile_url=current_user.profile_url)
		self.redirect('/groups/' + label)
	    if leave == 'y':
		if DerMundoGroups.leave(label, current_user.id):
		    self.redirect('/groups/')
		else:
		    self.redirect('/groups/' + label)
	    location = self.location
	    direction = self.direction
	    texts = self.localize(language)
	    q = self.request.get('q')
	    if len(q) > 0:
		issearch = True
		groups = DerMundoGroups.search(tag=q)
	    else:
		groups = DerMundoGroups.search()
		issearch = False
	    path = os.path.join(os.path.dirname(__file__), 'group.html')
	    args = dict(current_user=self.current_user,
			facebook_app_id=FACEBOOK_APP_ID)
	    if len(label) > 0:
		bookmarks = DerMundoBookMarks.search(group=label)
		messages = DerMundoMessages.search(msgtype='group', label=label)
		group = DerMundoGroups.find(label)
		members = DerMundoGroupMembers.search(label=label)
		memberlist = list()
		for m in members:
		    if m.id not in memberlist: memberlist.append(m.id)
	    else:
		bookmarks = None
		messages = None
		group = None
		members = None
		memberlist = None
	    try:
		ismember = DerMundoGroupMembers.ismember(label, current_user.id)
	    except:
		ismember = False
	    args.update(texts)
	    language_select = Languages.select(selected = self.language)
	    template_values = dict(
		ismember = ismember,
		issearch = issearch,
		bookmarks = bookmarks,
		messages = messages,
		members = members,
		memberlist = memberlist,
		group = group,
		groups = groups,
		sharethis_header = sharethis_header,
		sharethis_button = sharethis_button,
		google_analytics = google_analytics_header,
		share_this_button = sharethis_button,
		locale = locale,
		language = language,
		language_select = language_select,
		direction = direction,
	    )
	    
	    args.update(template_values)
	    self.response.out.write(template.render(path, args))

def PublishToFeed(facebookid, access_token, language='en', msg='', link=''):
    try:
	url="https://graph.facebook.com/" + facebookid + "/feed"
	form_fields = {
	    "access_token" : access_token,
	    "message" : msg,
	    "caption" : "Der Mundo : " + pro(language, "Translate the world with your friends"),
	    "link" : link
	}
	form_data = urllib.urlencode(form_fields)
	#try:
	result = urlfetch.fetch(url=url,
			  payload=form_data,
			  method=urlfetch.POST,
			  headers={'Content-Type': 'application/x-www-form-urlencoded'})
	results = result.content
    except:
	pass
    
class DerMundoGuideSubmitHandler(BaseHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	user = self.current_user
	if user:
	    url = self.request.get('url')
	    url = string.replace(url, 'http://','')
	    url = string.replace(url, 'https://', '')
	    try:
		result = urlfetch.fetch(url='http://' + url)
		content = result.content
		success = True
	    except:
		success = False
	    if success:
		title = self.request.get('title')
		description = self.request.get('description')
		tags = string.lower(self.request.get('tags'))
		language = string.lower(self.request.get('language'))
		city = self.request.get('city')
		if len(url) > 6 and len(title) > 0 and len(description) > 0:
		    tags = sting.split(tags,',')
		    for t in tags: string.replace(t,' ','')
		    if len(language) > 1 and len(language) < 3:
			language=[language]
		    else:
			language = None
		    DerMundoGuide.submit(url, title, description, tags=tags, languages=language, \
					 city=city, createdby=user.id, createdbyname=user.name, \
					 createdbyprofile=user.profile_url)
		    text = pro(self.language, 'I recommended a website for the DerMundo guide to the multilingual web. \"' + title + ' : ' + description + '\"')
		    PublishToFeed(user.id, user.access_token, self.language, msg=text, \
				  link = 'http://www.dermundo.com/' + url)
		    self.redirect('http://www.dermundo.com/' + url)
		else:
		    self.redirect(self.request.referrer)
	    else:
		self.redirect(self.request.referrer)
	else:
	    self.redirect(self.request.referrer)
	    
class SendMessageHandler(BaseHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	user = self.current_user
	language = self.language
	locale = self.locale
	label = self.request.get('label')
	msgtype = self.request.get('msgtype')
	msg = self.request.get('msg')
	feed = self.request.get('feed')
	if user:
	    words = string.split(msg, ' ')
	    tags = list()
	    text = ''
	    url = ''
	    shorturl = ''
	    for w in words:
		w = string.lower(w)
		if string.count(w, '#') > 0 or string.count(w, '@') > 0:
		    w = string.replace(w, '#','')
		    w = string.replace(w, '@','')
		    tags.append(w)
		    w = '<a href=/?q=' + w + '>' + w + '</a>'
		if string.count(w, 'http://') > 0:
		    if string.count(w, 'www.dermundo.com') < 1:
			title = string.replace(w, 'http://', '')
			url = string.replace(w, 'http://', 'http://www.dermundo.com/')
		    else:
			title = string.replace(w, 'http://','')
			url = w
		    if len(url) > 0:
			bitly_url='http://api.bitly.com/v3/shorten?login=dermundo&\
    apiKey=' + Settings.get('bitly_api_key') + '&\
    longUrl=' + urllib.quote_plus(url) + '&format=txt'
			try:
			    result = urlfetch.fetch(url=bitly_url)
			    shorturl = result.content
			except:
			    shorturl = url
		    else:
			shorturl = 'http://www.dermundo.com'
		    w = '<a href=' + shorturl + '>' + string.replace(shorturl, 'http://','') + '</a>'
		text = text + w + ' '
		if feed == 'y':
		    PublishToFeed(user.id, user.access_token, language=language, msg=msg, link=shorturl)
	    if DerMundoGroupMembers.ismember(label, user.id) or msgtype == 'stream':
		if msgtype != 'stream':
		    DerMundoGroups.savemessage(label, user.id, text, language=language, tags=tags,\
					   name = user.name, profile_url=user.profile_url,\
					   city = user.city, country=user.country)
		    self.redirect('/groups/' + label)
		else:
		    if len(msg) > 0:
			DerMundoMessages.sendmessage(msgtype, label, user.id, text, tags, language, \
						     name=user.name, profile=user.profile_url,\
						     city=user.city, country=user.country)
		    self.redirect('/')
	else:
	    self.redirect('/')
	    
class SubmitProjectHandler(BaseHandler):
    def get(self):
	current_user = self.current_user
	location = self.location
	city = location.get('city','')
	country = location.get('country','')
	if current_user:
	    createdbyid = current_user.id
	    createdbyname = current_user.name
	    createdbyprofile = current_user.profile_url
	else:
	    createdbyid = ''
	    createdbyname = ''
	    createdbyprofile = ''
	url = self.request.get('url')
	url = string.replace(url, 'http://','')
	url = string.replace(url, 'https://','')
	sl = self.request.get('sl')
	title = self.request.get('title')
	description = self.request.get('description')
	reason = self.request.get('reason')
	TranslationQueue.add(url=url, sl=sl, title=title, description=description,\
			     reason=reason, tags=None, createdbyid=createdbyid,\
			     createdbyname=createdbyname, createdbyprofile=createdbyprofile,\
			     city=city, country=country)
	self.redirect('/')
	
class DeleteMessageHandler(BaseHandler):
    def get(self, guid=''):
	self.requesthandler(guid)
    def post(self, guid=''):
	self.requesthandler(guid)
    def requesthandler(self, guid):
	current_user = self.current_user
	if current_user:
	    DerMundoMessages.deletemessage(guid, current_user.id)
	self.redirect(self.request.referrer)
	
class SidebarHandler(BaseHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	sl = self.request.get('sl')
	current_user = self.current_user
	language = self.language
	locale = self.locale
	direction = self.direction
	texts = self.localize(language)
	
	url = self.request.get('url')
	url = string.replace(url, 'http://', '')
	url = string.replace(url, 'https://','')
	
	shorturl = DerMundoProjects.find(url)
	
	path = os.path.join(os.path.dirname(__file__), 'sidebar.html')
	args = dict(current_user=self.current_user,
		    facebook_app_id=FACEBOOK_APP_ID)
	
	translators = Translation.getusersbyurl(url)
	
	args.update(texts)
	template_values = dict(
	    shorturl = shorturl, 
	    sharethis_header = sharethis_header,
	    sharethis_button = sharethis_button,
	    google_analytics = google_analytics_header,
	    share_this_button = sharethis_button,
	    locale = locale,
	    language = language,
	    direction = direction,
	    recent_translators = translators,
	)
	args.update(template_values)
	self.response.out.write(template.render(path, args))
	
class AnalyticsHandler(BaseHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	q = 'http://www.google-analytics.com/__utm.gif?\
	utmwv=4&utmn=769876874&utmhn=example.com&\
	utmcs=ISO-8859-1&utmsr=1280x1024&utmsc=32-bit&\
	utmul=en-us&utmje=1&utmfl=9.0%20%20r115&utmcn=1&\
	utmdt=GATC012%20setting%20variables&utmhid=2059107202&\
	utmr=0&utmp=/auto/GATC012.html?utm_source=www.gatc012.org&\
	utm_campaign=campaign+gatc012&utm_term=keywords+gatc012&\
	utm_content=content+gatc012&utm_medium=medium+gatc012&\
	utmac=UA-30138-1&utmcc=__utma%3D97315849.1774621898.1207701397.1207701397.1207701397.1%3B...' 
	
class Channels():
    @staticmethod
    def add(url, token):
	channel.create_channel(token)
	users = memcache.get('/channel/' + url)
	if users is None:
	    users = [token]
	    memcache.set('/channel/' + url, users)
	else:
	    if type(users) is list:
		if token not in users:
		    users.append(token)
		    memcache.set('/channel/' + url, users)
    @staticmethod
    def send_message(url, msg):
	users = memcache.get('/channel/' + url)
	if users is not None:
	    for u in users:
		channel.send_message(u, msg)
		
class FacebookIDHandler(BaseHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	user = self.current_user
	location = self.location
	language = self.language
	locale = self.locale
	city = location.get('city','')
	country = location.get('country','')
	if user:
	    userinfo = dict(
		id = user.id,
		name = user.name,
		city = city,
		country = country,
		language = language,
		locale = locale,
	    )
	else:
	    userinfo = dict()
	json = demjson.encode(userinfo)
	self.response.out.write(json)
	
class ProxyCounter(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	url = self.request.get('url')
	language = self.request.get('language')
	remote_addr = self.request.get('remote_addr')
	location = geolocate(remote_addr)
	city = location.get('city')
	country = location.get('country')
	DerMundoGuideStats.inc(url, 'language', language)
	DerMundoGuideStats.inc(url, 'city', city)
	DerMundoGuideStats.inc(url, 'city', 'all')
	self.response.out.write('ok')
		
class StreamHandler(webapp.RequestHandler):
    def get(self):
	self.requesthandler()
    def post(self):
	self.requesthandler()
    def requesthandler(self):
	self.response.out.write('')
		
def main():
    util.run_wsgi_app(webapp.WSGIApplication([("/secret1940", HomeHandler),
					      ("/wwl/login", LoginHandler),
					      ("/groups/(.*)", GroupHandler),
					      ("/stream", StreamHandler),
					      ("/wwl/facebook", FacebookIDHandler),
					      ("/wwl/guide", DerMundoGuideSubmitHandler),
					      ("/wwl/meta/crawl", MetaDataCrawlHandler),
					      (r"/wwl/deletemessage/(.*)", DeleteMessageHandler),
					      ("/wwl/meta/find", MetaDataFindHandler),
					      ("/wwl/meta/get", MetaDataGetHandler),
					      ("/wwl/meta/submit", MetaDataSubmitHandler),
					      ("/wwl/meta/stats", TranslationStatsHandler),
					      ("/wwl/meta/translation", TranslationSubmitStats),
					      ("/wwl.proxycounter", ProxyCounter),
					      ("/wwl/submit", SubmitTranslationHandler),
					      ("/wwl/sendmessage", SendMessageHandler),
					      ("/submit", SubmitTranslationHandler),
					      ("/sidebar", SidebarHandler),
					      ("/q", URLTranslationHandler),
					      ("/u", URLTranslationHandler),
					      ("/wwl/t", GetTranslationHandler),
					      ("/wwl/submitproject", SubmitProjectHandler),
					      ("/wwl/submitworker", SubmitTranslationWorker),
					      ("/wwl/scores/vote", ScoreHandler),
					      ("/dermundo/(.*)", HTMLHandler),
					      ("/wwl/u", URLTranslationHandler),
					      ("/help/firefox", FirefoxHelpHandler),
					      ("/", BetaHandler),
					      ("/beta/register", BetaHandler),
					      ("/wwl/userstatsworker", UserStatsWorker),
					      ("/wwl/trafficworker", TrafficWorker),
					      ("/wwl/purge", PurgeHandler),
					      ("/translate/project", CreateProject),
					      (r"/profile/(.*)", ProfileHandler),
					      (r"/x(.*)", ProxyHandler)], debug=True))


if __name__ == "__main__":
    main()
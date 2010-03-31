# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Main Module and Source Code Documentation (main.py)
by Brian S McConnell <brian@worldwidelexicon.org>

The Worldwide Lexicon Translation Memory is a collection of open source tools that enable you to build
and host your own collaborative translation applications and services. We will be publishing the full
open source release in June 2009 as a ready-to-use package for Google's App Engine cloud computing
environment. Advance copies of the source code documented here can be requested via email
(brian@worldwidelexicon.org), and will also be available for public use via Google Code next month.

This documentation is geared toward software developers, and is not for end users. If you are interested
in developing translation server applications based on the WWL platform, you should be familiar with
Python as well as Google's App Engine platform. Our goal is to make the documentation and source code
comments complete and easy to read, so that you can create customized services based on this platform
with relative ease.

Modules

The WWL package is distributed as a single ZIP archive that when installed creates a directory
tree that is ready to use with App Engine. The server side code is written in Python, and is ready
to run as-is on your App Engine account. The client side code is written in Javascript (AJAX widgets).
The package contains the following modules:

    * / : this directory contains the main Python source used to create the translation memory, define
      databases and other services
    * /ajax : this directory contains Alex Tolley's Javascript/AJAX translation viewer and
      in line editing tools. 
    * /blueprint : this directory tree contains CSS and image files used by the Blueprint based
      stylesheets.
    * /code : this URL will serve a current copy of the system source code (ZIP archive)
    * /docs : documentation (mostly Adobe Acrobat)
    * /html : sample static webpages to demostrate Javsascript/AJAX widgets
    * /images : images and icons used in web apps
    * /javascript : client-side Javascript/AJAX code
    * /translator : new version of Alex Tolley's Javascript transator (alpha test)

Installation (Translation Memory Server)

WWL is designed to run "out of the box" on Google App Engine. To install the Worldwide Lexicon translation memory:

   1. Create an App Engine account at appengine.google.com, and create an application (e.g. mywwlserver.appspot.com)
   2. Download the current source code from wwlapi.appspot.com/code
   3. Unpack the ZIP archive to a local directory tree on your computer
   4. Start the App Engine Launcher, click on the + icon to add your application, copy the source code and
      subdirectories into the folder App Engine launcher created for your new application
   5. Click Deploy to deploy your software
   6. Go to yoursite.appspot.com, you should see the home page for the translation server, web API and system
      documentation. Try yoursite.appspot.com/reader for the RSS feed reader and social translator.

If you encounter problems, it is most likely because you did not copy the source code and subdirectories properly.
The App Engine launcher will create a new directory for your application, and will insert some demo files into
the newly created directory. You should copy the contents of the main directory from the ZIP archive into this
directory (its OK to overwrite the sample files created by App Engine Launcher). The /code, /css and other
subdirectories should be copied as child directories of the main application directory.

If you plan to develop custom software based on WWL or to make substantial modifications to the software, we
recommend that you create two applications on App Engine, one for public use, and one for testing. This way you
can make frequent changes to the test system, and then copy code over to the public version when you are sure
everything is working OK.

Installation (Javascript Translation Viewer/Editor)

You can make almost any website translatable with our Javascript translation viewer/editor (created
by Alex Tolley). To use this tool, simply add the following line of code to your website's page
headers.

  <script language="javascript" src="http://yourwwlserver.com/ajax/com.wwl.Translator.nocache.js"></script>

Then, wherever you want to make a text translatable include bracket the text with the following div tags.

  <div wwlapi="tr" sl="{source language code}" edit="y|n">Hello World</div>

The sl=xx parameter tells it the source language the text was written in (English by default).
The edit=y|n parameter tells it whether to allow edits (yes by default if omitted)

Complete documentation for our translation web kit can be found at www.worldwidelexicon.org

Integrating WWL With Other Systems

WWL is a translation memory, essentially a giant database of translations along as associated utilities that
provide supporting services (such as connectivity to machine translation services). It is not a standalone
website, or is it a destination by itself. It is designed to be integrated into other systems using one of
several integration strategies.

Lightweight (Overlay) Integration Strategies

One strategy is to build lightweight applets or widgets that are loaded dynamically within another webpage,
and that call WWL to request and save translations as needed as the page is displayed. Javascript applets
that use a technique called AJAX are a good way to do this. The website owner pastes a few lines of Javascript
code in the page header. The AJAX widget, in turn, calls WWL as needed to fetch and display translations for
the texts it encounters in the web page. This strategy requires few or no changes to the underlying website
or content management system, which makes this an attractive way to add collaborative translation to a wide
variety of sites. See reader.py for an example of a RSS reader with social translation using an AJAX/Javascript
widget. Examples of these type of implementations include:

    * AJAX widgets that redraw and translate webpages on the fly, allow users to edit texts without leaving the page.
    * Adobe AIR applications designed for power translators and administrators (control panel applications).
    * Mobile applications, such as an iPhone app, that poll WWL to fetch small texts to be translated and sent back.

See Alex Tolley's AJAX translation viewer/editor for some ideas about how to do this.

RSS Reader and Social Translator (reader.py)

WWL ships with a pre-built RSS feed reader and social translator. This is a relatively simple demo
application that illustrates how to build collaborative translation services. You can go to
yoursite.appspot.com/reader It should load the popular Boing Boing (www.boingboing.net) RSS feed.
You can configure it to use the central translation server (api.worldwidelexicon.org, default) or
your local translation server to save and retrieve translations.

CMS (Content Management System) Integration

Another strategy is to integrate the WWL translation memory with a content management system, such as
Word Press or Drupal. The content management system calls WWL whenever an author saves or updates a new
document, blog post, etc, to request translations for the new text. The translations are stored and
catalogued inside the content management system, so the translations are loaded and served directly
from the CMS, not from the WWL translation memory. This strategy is harder to implement, but will give
publishers direct control both over how translations are stored and also how they are displayed. It also
protects the website from a disruption at WWL since the translations are stored locally, therefore if WWL
is offline for a period of time, it will not interrupt the delivery of translated pages. Examples of this
type of implementations include:

    * Batch programs that periodically generate translations for all new or recently edited documents
      in the content management systems document store.
    * Lightweight widgets that are implemented as tightly integrated plugins, to allow easy deployment
      on a CMS (e.g. Word Press plugin)

Language Service Provider Integration (lsp.py)

The WWL server also exposes a web interface for LSPs to use to fetch and submit translations and metadata,
where submissions from the LSP are treated as more trustworthy than public submissions and may bypass the
normal peer review and scoring process. The LSP interface, defined in lsp.py, can be easily modified to
implement whatever workflows or QA rules are needed when processing submissions from a known, trustworthy
service bureau.

Mobile Interface (mobile.py)

WWL ships with a simple mobile interface (implemented in mobile.py) that implements a simple machine
translation service, for looking up translations via Google Translate and other services, and a demo app
that prompts users to write translations for their favorite websites or RSS feeds.

Client Side (AJAX) Modules

    * Alex Tolley has contributed a Javascript/AJAX translation viewer and editor that can be embedded
      in almost any website. It is simple to deploy and use. The libraries and associated files are
      contained in the /ajax directory tree.

Server Side (Python) Modules

The code that defines the translation memory is sub-divided into a small number of Python modules by function:

    * comments.py : this module implements classes and methods to save and retrieve comments about translations
    * database.py : defines data stores, provides abstract interface for data store queries
      (you should be able to modify these functions to replace App Engine's data store with other
       resources such as MySQL, Amazon Simple DB, etc); note, this module is being phased out,
       as relevant functions are moved to comments.py, scores.py, sources.py, translations.py and users.py
    * deeppickle.py : this is a utility created by Brian McConnell to render a row/column recordset
      in multiple output formats (xml, rss, json, PO, csv, etc), and is used to render API responses
    * doc.py : embedded documentation server, this module uses PyDoc to display documentation for
      modules and classes, and generates documentation from the current version of the source code
      running on the system.
    * hosts.py : this module implements services to control and capture log information from translation
      proxy servers, this is currently a dummy library and will be updated as we deploy the translation
      proxy service (which will be available both as a hosted service from WWL, and as part of the open
      source toolset)
    * mt.py : machine translation proxy service, provides a simple interface to call multiple
      machine translation services (Google, Apertium, Systran and others)
    * rules.py : implements translation management rules (will be partially implemented in
      June release)
    * scores.py : defines API calls for fetching and saving scores about translations
    * search.py : translation search engine and multilingual portal (works in conjunction with our
      Firefox translation addon)
    * stats.py : defines API calls for fetching statistics, system counters and translation matrices
    * translations.py : this module implements classes and methods to save and retrieve translations
    * users.py : manages WWL users, authentication, etc (can be rewritten to act as proxy to
      external user management systems)
    * www.py : PyDoc documentation engine, generates web documentation for web API handlers and
      for Python source code modules and their classes

You can find live documentation online. WWL generates software documentation using PyDoc, Python's
built in documentation engine. Simply go to wwlapi.appspot.com to view documentation for the current
public release of the WWL software, or go to your translation server's home page. You should see a
welcome page, current system status and links to web API and source code documentation. You can
password protect this page by setting password protection options in the main.py module.

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
#
# -*- coding: utf-8 -*-
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from www import www
import feedparser
from webappcookie import Cookies

css_header='<link rel="stylesheet" href="/blueprint_overrides.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/screen.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/print.css" type="text/css" media="print">\
            <link rel="stylesheet" href="/blueprint/plugins/fancy-type/screen.css" type="text/css" media="screen, projection">\
            <link rel="stylesheet" href="/blueprint/plugins/link-icons/screen.css" type="text/css" media="screen, projection">\
            <!--[if IE]><link rel="stylesheet" href="/blueprint-css/blueprint/ie.css" type="text/css" media="screen, projection"><![endif]-->'

css_container = '<div class="container"><hr class="space">'

css_wide = '<div class="span-15 prepend-1 colborder">'

css_sidebar = '<div class="span-7 last">'

sidebar_about = '<h3>About WWL</h3>\
                The Worldwide Lexicon is an open source collaborative translation platform. It is similar to \
                systems like <a href=http://www.wikipedia.org>Wikipedia</a>, and combines machine translation \
                with submissions from volunteers and professional translators. WWL is a translation memory, \
                essentially a giant database of translations, which can be embedded in almost any website or \
                web application.<br><br>\
                Our mission is to eliminate the language barrier for interesting websites and articles, by \
                enabling people to create translation communities around their favorite webites, topics or \
                groups.<br><br>\
                WWL is open source software, published under the New BSD license, and can be adapted for \
                commercial and non-commercial use, and can be customized for a wide variety of applications, \
                from translating research journals, to creating translatable news portals for readers in \
                countries around the world.<br><br>'

sidebar_credits = '<h3>Credits</h3>\
                <ul><li>System Concept : <a href=http://www.google.com/profiles/bsmcconnell>Brian S McConnell</a> (1998-2009)</li>\
                <li>Translation Memory Server Software</li>\
                <ul><li><a href=http://www.google.com/profiles/bsmcconnell>Brian S McConnell</a> (Python/<a href=http://appengine.google.com>App Engine</a> Version)</li>\
                <li><a href=http://www.metalink.com>Alexey Gavrilov (PHP/Cake Version 2007-2008)</a></li>\
                </ul>\
                <li>User Interface Designs & CSS : <a href=http://www.unthinkingly.com>Chris Blow</a></li>\
                <li>Inline Javascript/AJAX Translation Viewer/Editor : Alex Tolley</li>\
                <li>System and Source Code Documentation : <a href=http://www.google.com/profiles/bsmcconnell>Brian S McConnell</a></li>\
                <ul>'

rss_feed_url = 'http://wwl.unthinkingly.com/?feed=rss2'

header_welcome = 'Welcome to the Worldwide Lexicon open translation memory server. This open web API enables you to add collaborative translation \
                to almost any website or web application. You can find the server source code, documentation and API documentation here on this \
                site. To learn about a specific web service, just click on the (doc) link adjacent to each service below. For more information \
                about WWL, visit <a href=http://www.worldwidelexicon.org>www.worldwidelexicon.org</a>. If you would like to deploy and manage your \
                own translation server, you can download the WWL source code (written in Python, runs on App Engine). Contact Brian McConnell \
                at bsmcconnell at gmail for more information (we will be publishing the source and documentation on Google Code shortly).<p>'

header_demo_applications = 'Demo Applications'

footer_copyright = 'Worldwide Lexicon hosted translation memory (c) 2007-2009 <a href=http://www.worldwidelexicon.org>Worldwide Lexicon Inc.</a><br>\
                Worldwide Lexicon concept and source code (c) 1998-2009 <a href=http://www.google.com/profiles/bsmcconnell>Brian S McConnell</a>,\
                published for commercial and non-commercial use under the New BSD license.'

javascript_header_init = '<script src="/translator/translator.nocache.js"></script>'
javascript_global_div = '<div id="wwlapi" sl="en" dermundo="http://worldwidelexicon.appspot.com/" allow_machine="y" allow_anonymous="y" allow_unscored="y" minimum_score="0"></div>'

class languages():
    """
    This class implements several convenience methods for managing the list of supported languages on
    your translation memory server. The system recognizes a relatively large list of languages by default
    which are pre-defined in the method getlist(). 
    """
    @staticmethod
    def getlist(languages=list()):
        """
        Returns a list of languages, indexed by ISO language code in a dict() object.
        The optional languages argument is pass with a list of ISO codes to limit the
        list to a smaller pre-defined list of languages (if you only want to allow
        translations to a smaller group of languages on your site.
        """
        langs = memcache.get('languages|local')
        if len(languages) < 1 and langs is not None:
            return langs
        else:
            l=dict()
            l['en']=u'English'
            l['es']=u'Español'
            l['af']=u'Afrikaans'
            l['ar']=u'العربية'
            l['bg']=u'български език'
            l['bo']=u'བོད་ཡིག'
            l['de']=u'Deutsch'
            l['fr']=u'Français'
            l['he']=u'עברית '
            l['id']=u'Indonesian'
            l['it']=u'Italiano'
            l['ja']=u'日本語'
            l['ko']=u'한국어'
            l['ru']=u'русский'
            l['th']=u'ไทย '
            l['tl']=u'Tagalog'
            l['zh']=u'中文 '
            l['ca']=u'Català'
            l['cs']=u'česky'
            l['cy']=u'Cymraeg'
            l['el']=u'Ελληνικά'
            l['et']=u'Eesti keel'
            l['eu']=u'Euskara'
            l['fa']=u'فارسی '
            l['fi']=u'suomen kieli'
            l['ga']=u'Gaeilge'
            l['gl']=u'Galego'
            l['gu']=u'ગુજરાતી'
            l['hi']=u'हिन्दी '
            l['hr']=u'Hrvatski'
            l['ht']=u'Kreyòl ayisyen'
            l['hu']=u'Magyar'
            l['is']=u'Íslenska'
            l['iu']=u'ᐃᓄᒃᑎᑐᑦ'
            l['jv']=u'basa Jawa'
            l['ku']=u'كوردی'
            l['la']=u'lingua latina'
            l['lt']=u'lietuvių'
            l['lv']=u'latviešu'
            l['mn']=u'Монгол '
            l['ms']=u'بهاس ملايو‎'
            l['my']=u'Burmese'
            l['ne']=u'नेपाली '
            l['nl']=u'Nederlands'
            l['no']=u'Norsk'
            l['oc']=u'Occitan'
            l['pa']=u'ਪੰਜਾਬੀ '
            l['po']=u'polski'
            l['ps']=u'پښتو'
            l['pt']=u'Português'
            l['ro']=u'română'
            l['sk']=u'slovenčina'
            l['sr']=u'српски језик'
            l['sv']=u'svenska'
            l['sw']=u'Kiswahili'
            l['tr']=u'Türkçe'
            l['uk']=u'Українська'
            l['vi']=u'Tiếng Việt'
            l['yi']=u'ייִדיש'
            if type(languages) is list:
                if len(languages) < 1:
                    memcache.set('languages|local', l, 72000)
                    return l
                langs = dict()
                for k in languages:
                    lang = l.get(k)
                    if len(lang) > 0:
                        langs[k]=l[k]
                return langs
            else:
                return l


class MainPage(webapp.RequestHandler):
  """
  This web request handler generates the home page for the WWL translation server. You should see a greeting,
  followed by a list of web API calls and source code documentation. The documentation is generated from
  the current source code running on the system, so it should always be in sync with the current version of
  the system. 
  """
  def get(self, url=''):
    """Generates the WWL translation server home page"""
    cookies = Cookies(self, max_age=72000)
    try:
      tl = cookies['tl']
    except:
      tl = ''
    response = urlfetch.fetch(url=rss_feed_url)
    if response.status_code == 200:
        r = response.content
    else:
        r = None
    self.response.headers['Content-Type']='text/html'
    self.response.out.write('<head><title>Worldwide Lexicon : Version 2 Web API (Test)</title>')
    self.response.out.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />')
    self.response.out.write(css_header)
    self.response.out.write(javascript_header_init)
    self.response.out.write(css_container)
    self.response.out.write(javascript_global_div)
    self.response.out.write('<h2>Worldwide Lexicon : Collaborative Translation Memory</h2>')
    langlist = languages.getlist()
    self.response.out.write('<form action=/users/setlanguage method=postt>')
    self.response.out.write('<input type=hidden name=callback value=/api>')
    self.response.out.write('<select name=tl>')
    langkeys = langlist.keys()
    langkeys.sort()
    if len(tl) > 0:
        try:
            self.response.out.write('<option selected value="' + tl + '">' + langlist[tl] + '</option>')
        except:
            pass
    for k in langkeys:
        self.response.out.write('<option value="' + k + '">' + langlist[k] + '</option>')
    self.response.out.write('</select>')
    self.response.out.write('<input type=submit value=Go></form>')
    self.response.out.write('<hr>')
    self.response.out.write(css_wide)
    self.response.out.write(header_welcome)
    self.response.out.write('<h3>Tutorials</h3>')
    self.response.out.write('<ul>')
    self.response.out.write('<li><a href=/s/api.html>Overview of WWL API</a></li>')
    self.response.out.write('<li><a href=http://www.worldwidelexicon.org/s/lsps.html>Language Service Providers API</a></li>')
    self.response.out.write('<li><a href=http://broadcast.oreilly.com/2009/10/adding-professional-translatio.html>(oreilly.com) Adding Professional Translation to Your Website</a></li>')
    self.response.out.write('</ul>')
    self.response.out.write('<h3>Source Code & Documentation (Sept 2009 Release)</h3>')
    self.response.out.write('<ul>')
    self.response.out.write('<li>comments.py : Save and retrieve comments about translations <a href=/doc?module=comments>(doc)</a></li>')
    self.response.out.write('<li>config.py : Editable configuration file for system settings</li>')
    self.response.out.write('<li>deeppickle.py : General purpose data format conversion module <a href=/doc?module=deeppickle>(doc)</a></li>')
    self.response.out.write('<li>feedparser.py : General purpose RSS feed parser (<a href=http://www.feedparser.org>www.feedparser.org</a>)</li>')
    self.response.out.write('<li>hosts.py : Implements host controller for translation proxy servers (<a href=/doc?module=hosts>doc</a>)</li>')
    self.response.out.write('<li>language.py : Language utilities and language detection <a href=/doc?module=language>(doc)</a>')
    self.response.out.write('<li>mt.py : Machine translation proxy server <a href=/doc?module=mt>(doc)</a></li>')
    self.response.out.write('<li>scores.py : Save and retrieve scores for translations <a href=/doc?module=scores>(doc)</a></li>')
    self.response.out.write('<li>search.py : Translation search engine and community platform <a href=/doc?module=search>(doc)</a></li>')
    self.response.out.write('<li>translations.py : Save translations, retrieve human and/or machine translations <a href=/doc?module=translations>(doc)</a></li>')
    self.response.out.write('<li>users.py : User related classes and methods <a href=/doc?module=users>(doc)</a></li>')
    self.response.out.write('<li>www.py : Embedded documentation server <a href=/doc?module=www>(doc)</a></li>')
    self.response.out.write('</ul>')
    self.response.out.write('<h3>Web API Documentation & Test Forms</h3>')
    self.response.out.write('<ul>')
    self.response.out.write('<li><a href=/comments/get>/comments/get</a> (fetch comments about a translation)</li>')
    self.response.out.write('<li><a href=/comments/submit>/comments/submit</a> (submit comment about a translation)</li>')
    self.response.out.write('<li><a href=/language>/language</a> (language utilities, and language detection)</li>')
    self.response.out.write('<li><a href=/mt>/mt</a> (machine translation proxy server)</li>')
    self.response.out.write('<li><a href=/q>/q</a> (search for translations</li>')
    self.response.out.write('<li><a href=/queue/add>/queue/add</a> (add text to translation queue)</li>')
    self.response.out.write('<li><a href=/queue/score>/queue/score</a> (submit a score for a community translation</li>')
    self.response.out.write('<li><a href=/queue/search>/queue/search</a> (search translation queue)</li>')
    self.response.out.write('<li><a href=/queue/submit>/queue/submit</a> (submit translation, remove item from queue)</li>')
    self.response.out.write('<li><a href=/request>/request</a> (request human translation for a URL, or view list of recommended URLs)</li>')
    self.response.out.write('<li><a href=/scores/get>/scores/get</a> (fetch raw score history)</li>')
    self.response.out.write('<li><a href=/scores/vote>/scores/vote</a> (submit score for a translation)</li>')
    self.response.out.write('<li><a href=/submit>/submit</a> (submit a translation)</li>')
    self.response.out.write('<li><a href=/t>/t</a> (simple translation request API)</li>')
    self.response.out.write('<li><a href=/users/auth?doc=y>/users/auth</a> (authenticate user)</li>')
    self.response.out.write('<li><a href=/users/check>/users/check</a> (check username available)</li>')
    self.response.out.write('<li><a href=/users/currentuser?doc=y>/users/currentuser</a> (get current username for session</li>')
    self.response.out.write('<li><a href=/users/count>/users/count</a> (get total edits and word count for current user)</li>')
    self.response.out.write('<li><a href=/users/logout?doc=y>/users/logout</a> (logout from system)</a></li>')
    self.response.out.write('<li><a href=/users/new>/users/new</a> (create new user account)</a></li>')
    self.response.out.write('<li><a href=/users/setlanguage>/users/setlanguage</a> (set language, options)</a></li>')
    self.response.out.write('<li><a href=/users/setoptions>/users/setoptions</a> (set language, options)</li>')
    self.response.out.write('<li><a href=/users/validate>/users/validate</a> (validate new user account)</li>')
    self.response.out.write('</ul>')
    self.response.out.write('</div>')
    self.response.out.write(css_sidebar)
    if r is not None:
      feed = feedparser.parse(r)
      items = feed.entries
      if len(items) > 0:
        self.response.out.write('<h3>News</h3>')
        ctr = 0
        for i in items:
          ctr = ctr + 1
          if ctr < 5:
            self.response.out.write('<h4><a href="' + i.link + '">' + i.title + '</a></h4>')
            description = i.description
            text = description[0:200]
            self.response.out.write(text)
            self.response.out.write('<br><br>')
    self.response.out.write('<div wwlapi="tr">')
    self.response.out.write(sidebar_about)
    self.response.out.write('</div>')
    self.response.out.write('<div wwlapi="tr">')
    self.response.out.write(sidebar_credits)
    self.response.out.write('</div>')
    self.response.out.write('</div></div>')
    self.response.out.write('<font size=-2><center>')
    self.response.out.write(footer_copyright)
    self.response.out.write('</font></center>')

class DocServer(webapp.RequestHandler):
  """
  Generates module and class documentation using the embedded PyDoc documentation service. 
  """
  def get(self):
    module = self.request.get('module')
    www.servedoc(self,module)

application = webapp.WSGIApplication([('/api', MainPage),
                                      ('/help', MainPage),
                                      ('/doc', DocServer),
                                      (r'/(.*)', MainPage),
                                      ('/', MainPage)],
                                     debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()

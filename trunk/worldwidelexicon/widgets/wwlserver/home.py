# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Main Module and Source Code Documentation (main.py)
by Brian S McConnell <brian@worldwidelexicon.org>

The Worldwide Lexicon Translation Memory is a collection of open source tools that enable you to build
and host your own collaborative translation applications and services. 

Modules

The WWL package is distributed as a single ZIP archive that when installed creates a directory
tree that is ready to use with App Engine. The server side code is written in Python, and is ready
to run as-is on your App Engine account. The client side code is written in Javascript (AJAX widgets).
The package contains the following modules:

    * / : this directory contains the main Python source used to create the translation memory, define
      databases and other services
    * /blueprint : this directory tree contains CSS and image files used by the Blueprint based
      stylesheets.
    * /docs : documentation (mostly Adobe Acrobat)
    * /images : images and icons used in web apps

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

Server Side (Python) Modules

The code that defines the translation memory is sub-divided into a small number of Python modules by function:

    * akismet.py : implements Akismet spam filtering service by WordPress
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
    * lsp.py : this module implements services to send requests out to professional translation service
      providers, and to process translations submitted by them, and also includes some test interfaces
      for developers.
    * mt.py : machine translation proxy service, provides a simple interface to call multiple
      machine translation services (Google, Apertium, Systran and others)
    * scores.py : defines API calls for fetching and saving scores about translations
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

Copyright (c) 1998-2010, Brian S McConnell, Worldwide Lexicon Inc.
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
from www import web
import feedparser
import string
from webappcookie import Cookies
from database import Settings

css_header='<link rel="stylesheet" href="/css/style.css">'

#css_header='<link rel="stylesheet" href="/blueprint_overrides.css" type="text/css" media="screen, projection">\
#            <link rel="stylesheet" href="/blueprint/screen.css" type="text/css" media="screen, projection">\
#            <link rel="stylesheet" href="/blueprint/print.css" type="text/css" media="print">\
#            <link rel="stylesheet" href="/blueprint/plugins/fancy-type/screen.css" type="text/css" media="screen, projection">\
#            <link rel="stylesheet" href="/blueprint/plugins/link-icons/screen.css" type="text/css" media="screen, projection">\
#<!--[if IE]><link rel="stylesheet" href="/blueprint-css/blueprint/ie.css" type="text/css" media="screen, projection"><![endif]-->'

css_main= '<div id="wrap">'
css_main_close = '</div>'

css_menu = '<div id="top">\
<h2><a href=http://blog.worldwidelexicon.org>Worldwide Lexicon</a></h2>\
<div id="menu">[list]\
</div>\
</div>'

css_content = '<div id="content">'
css_content_close = '</div>'

css_wide = '<div id="left">'
css_wide_close = '</div>'

css_sidebar = '<div id="right"><div class="box">'
css_sidebar_close = '</div></div>'

css_footer = '<div id="clear"></div></div><div id="footer">(c) 2008-2010 Worldwide Lexicon Inc, (c) 1998-2010, Brian S McConnell</div></div>'

# Google Analytics Header
google_analytics_header = '<script type="text/javascript">var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");\
document.write(unescape("%3Cscript src=\'\" + gaJsHost + \"google-analytics.com/ga.js\' type=\'text/javascript\'%3E%3C/script%3E"));\
</script>\
<script type="text/javascript">\
try {\
var pageTracker = _gat._getTracker("' + Settings.get('googleanalytics') + '");\
pageTracker._trackPageview();\
} catch(err) {}</script>'


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
    u = 'http://www.worldwidelexicon.org/css/template.html'
    w = web()
    valid = w.get(u)
    if valid:
        menus = '<ul><li><a href=http://www.worldwidelexicon.org/api>API</a></li>\
<li><a href=http://blog.worldwidelexicon.org>Blog</a></li>\
<li><a href=http://code.google.com/p/worldwidelexicon>Code</a></li></ul>'
        w.replace(u, '[menu]', menus)
        w.replace(u, '[google_analytics]', google_analytics_header)
        w.replace(u, '[title]', 'Worldwide Lexicon')
        w.get('http://www.worldwidelexicon.org/static/api_main.html')
        left = w.out('http://www.worldwidelexicon.org/static/api_main.html')
        w.replace(u, '[left_column]', left)
        w.replace(u, '[right_column]', sidebar_about + sidebar_credits)
        w.replace(u, '[footer]', 'Copyright 1998-2010, Brian S McConnell. Copyright 2008-2010, Worldwide Lexicon Inc')
        self.response.out.write(w.out(u))
    else:
        self.error(404)

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

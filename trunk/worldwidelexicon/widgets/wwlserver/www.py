"""
Copyright (c) 1998-2009, Worldwide Lexicon Inc.
All rights reserved.

Documentation Server (www.py)
Brian S McConnell

This module generates documentation for modules and classes/methods within them.

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

u = 'http://www.worldwidelexicon.org/css/template.html'

from google.appengine.api import memcache
from google.appengine.api import urlfetch
from pydoc import HTMLDoc
import string

class web():
    text = dict()
    def get(self, url):
        text = memcache.get('/url/' + url)
        if text is not None:
            self.text[url] = text
            return True
        else:
            result = urlfetch.fetch(url=url)
            if result.status_code == 200:
                memcache.set('/url/' + url, result.content, 300)
                self.text[url]=result.content
                return True
            else:
                return False
    def replace(self, url, tag, text):
        try:
            self.text[url]=string.replace(self.text[url], tag, text)
            return True
        except:
            return False
    def out(self, url):
        return self.text.get(url, '')

class www():
    """
    www()

    Embedded documentation server. Serves pydoc compatible
    docstrings. Used for self-documentation for web API server.
    """
    menus = '<ul><li><a href=http://www.worldwidelexicon.org/api>API</a></li>\
<li><a href=http://blog.worldwidelexicon.org>Blog</a></li>\
<li><a href=http://code.google.com/p/worldwidelexicon>Code</a></li></ul>'
    @staticmethod
    def serve(rh,text, title='', sidebar='', mode='text/html', css='/css/main.css', cssbody='overall', cssheader="header"):
        rh.response.headers['Content-Type']=mode
        w = web()
        w.get(u)
        if len(title) > 0:
            w.replace(u, '[title]', title)
        else:
            w.replace(u, '[title]', 'Worldwide Lexicon')
        w.replace(u, '[footer]', 'Copyright 1998-2010 Brian S McConnell, Copyright 2008-2010 Worldwide Lexicon Inc.')
        w.replace(u,'[left_column]',  text)
        w.replace(u,'[right_column]', sidebar)
        w.replace(u,'[menu]', www.menus)
        rh.response.out.write(w.out(u))
    @staticmethod
    def servedoc(rh, module, title = 'WWL Documentation Server', mode='text/html', css='/css/main.css', cssbody='overall', cssheader='header'):
        rh.response.headers['Content-Type']='text/html'
        w = web()
        w.get(u)
        w.replace(u, '[title]', title)
        w.replace(u, '[menu]', www.menus)
        try:
            m = __import__(module)
            t = HTMLDoc()
            text = t.docmodule(m)
            texts = string.split(text, '&nbsp;<br>')
            ttext = ''
        except:
            texts = list()
            ttext = ''
        ctr = 0
        for txt in texts:
            if ctr > 0:
                ttext = ttext + '<div wwlapi="tr"> ' + txt + '</div>&nbsp;<br>'
            else:
                ttext = ttext + txt + '&nbsp;<br>'
            ctr = ctr + 1
        w.replace(u, '[left_column]', ttext)
        rh.response.out.write(w.out(u))

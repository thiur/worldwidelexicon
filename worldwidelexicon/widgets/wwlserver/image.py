# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Multilingual Content Management System
Image Server (image.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module serves requests to the /images path to cache and transmit image files.
Image uploads and managements are done via the admin.py module. Images are
memcached where possible to maximize performance. 

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
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from database import Images

class ImageServer(webapp.RequestHandler):
    def get(self, p1='', p2=''):
        headers = self.request.headers
        thumbnail = self.request.get('thumbnail')
        website=p1
        name=p2
        if len(name) > 0:
            idb = db.Query(Images)
            idb.filter('website = ', website)
            idb.filter('name = ', name)
            item = idb.get()
            if item is not None:
                if len(thumbnail) > 0:
                    imagefile = item.avatar
                else:
                    imagefile = item.image
                self.response.headers['Content-Type']='image/png'
                self.response.out.write(imagefile)
            else:
                self.error(404)
        else:
            self.error(404)
            
class Gallery(webapp.RequestHandler):
    def get(self, p1='', p2=''):
        headers = self.request.headers
        website = headers.get('Host', '')
        if len(p2) > 0:
            website = p1
            name = p2
        else:
            website = p1
            name = ''
        gallery = Images.gallery(website, name)
        ctr = 0
        self.response.out.write('<table>')
        for g in gallery:
            if ctr == 0:
                self.response.out.write('<tr>')
            self.response.out.write('<td><a border=0 href=/images/' + g + '><img border=0 src=/images/' + g + '?thumbnail=y></a></td>')
            ctr = ctr + 1
            if ctr == 5:
                self.response.out.write('</tr>')
                ctr = 0
        self.response.out.write('</table>')

application = webapp.WSGIApplication([(r'/images/(.*)/(.*)', ImageServer),
                                      (r'/images/(.*)', ImageServer),
                                      (r'/gallery/(.*)/(.*)', Gallery),
                                      (r'/gallery/(.*)', Gallery)],
                                     debug=True)

def main():
    run_wsgi_app(application)
  
if __name__ == '__main__':
    main()

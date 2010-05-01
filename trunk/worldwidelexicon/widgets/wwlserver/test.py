# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Translation Search Engine (search.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module implements a search engine that enables users to see which sites and URLs
are being translated most actively, to do keyword searches for translations and the
documents they are related to. 

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
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
# import WWL modules
from database import Directory
from www import www

class Test(webapp.RequestHandler):
    """
    This web service is used to test Unicode/UTF-8 transcoding.   
    """
    def get(self):
        self.request.charset = 'utf8'
        sl = self.request.get('sl')
        tl = self.request.get('tl')
        st = self.request.get('st')
        if len(sl) < 1 and len(tl) < 1:
            www.serve(self,self.__doc__)
            self.response.out.write('<table><form action=/test method=get>')
            self.response.out.write('<tr><td>Source Language</td><td><input type=text name=sl></td></tr>')
            self.response.out.write('<tr><td>Target Language</td><td><input type=text name=tl></td></tr>')
            self.response.out.write('<tr><td>Source Text</td><td><input type=text name=st></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value="Submit"></td></tr>')
            self.response.out.write('</table></form>')
        else:
            sdb = db.Query(Directory)
            sdb.order('-date')
            results = sdb.fetch(limit=200)
            sites = list()
            for r in results:
                if r.domain not in sites:
                    sites.append(r.domain)
            self.response.out.write('<ul>')
            for s in sites:
                self.response.out.write('<li><a href=http://' + s + '>' + s + '</a></li>')
            self.response.out.write('</ul>')

application = webapp.WSGIApplication([(r'/test', Test)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

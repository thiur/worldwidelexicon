# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Trans Sense Server
Sensor Network For Multilingual Signage (transense.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module implements a simple service that can be used to drive multilingual
signs in public venues, using cellular and wifi network operators to provide
summary statistics on the countries and languages represented in zones throughout
the facility. 

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
# import Python standard modules
import datetime
import md5
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
# define constants
keys = ['xyz123', 'abc987']
ip_addresses = []
ttl = 120

class SensorNetwork(db.Model):
    guid = db.StringProperty(default='')
    timestamp = db.DateTimeProperty(auto_now_add = True)
    node = db.StringProperty(default='')
    text = db.TextProperty(default='')
    @staticmethod
    def save(node, text):
        if len(node) > 0 and len(text) > 0:
            m = md5.new()
            m.update(str(datetime.datetime.now()))
            m.update(node)
            guid = str(m.hexdigest())
            item = SensorNetwork()
            item.guid = guid
            item.node = node
            item.text = text
            item.put()
            return True
        else:
            return False

class WebQuery(webapp.RequestHandler):
    def get(self, zone=''):
        """
        /transense/zoneornetworkid

        This web service returns a row/comma separated list as follows:

        zone, parm, value, count
        wifi002, language, es, 8
        wifi002, language, fr, 4
        tmobile9201, country, us, 12
        tmobile9201, country, fr, 4

        Electronic signs in the venue can simply call this service by
        loading the URL:

        www.servername.com/zone

        And will receive the list in the format above. The signs can
        load lists for more than one zone or network base station, so they
        can watch a limited area, such as the seating area near a gate, or
        can cover a broader area.

        The counts are stored for a short period of time, the time to live
        can be adjusted in the constants at the top of this source file.
        The counts can be indexed by country or by user language preference
        depending on the reporting capabilities of the network.
        """
        text = ''
        if len(zone) > 0:
            t = memcache.get('/transense/' + zone)
            if t is not None:
                text = t
            self.response.headers['Content-Type']='text/plain'
            self.response.out.write(text)
        else:
            self.response.out.write('<table><form action=/transense method=post>')
            self.response.out.write('<tr><td>Key</td><td><input type=text name=key></td></tr>')
            self.response.out.write('<tr><td>Node</td><td><input type=text name=node></td></tr>')
            self.response.out.write('<tr><td colspan=2><textarea name=text></textarea></td></tr>')
            self.response.out.write('<tr><td colspan=2><input type=submit value=Update></td></tr>')
            self.response.out.write('</form></table>')            
    def post(self):
        """
        /transense

        Networks reporting statistics to the system will use HTTP POST to
        submit a form with the following fields:

        key = API key, to authenticate the sender (submissions can also
              be filtered by IP address range, see above)
        text = comma separated list of nodes, and counts in same format
              as the GET method above

        It returns ok or error
        """
        key = self.request.get('key')
        remote_addr = self.request.remote_addr
        node = self.request.get('node')
        text = self.request.get('text')
        valid_submission = True
        if len(keys) > 0 and key not in keys:
            valid_submission = False
        if len(ip_addresses) > 0 and remote_addr not in ip_addresses:
            valid_submission = False
        if valid_submission and len(node) > 0 and len(text) > 0:
            self.response.headers['Content-Type']='text/plain'                
            memcache.set('/transense/' + node, text, ttl)
            SensorNetwork.save(node, text)
            self.response.out.write('ok')
        else:
            self.response.headers['Content-Type']='text/plain'
            self.response.out.write('error')
            
application = webapp.WSGIApplication([('/transense', WebQuery),
                                      (r'/transense/(.*)', WebQuery)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

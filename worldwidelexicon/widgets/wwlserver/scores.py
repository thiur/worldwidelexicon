# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Scoring System (scores.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements web services and database calls to retrieve and save
scores for translations. This module defines two web API services:

/scores/get : to retrieve a score history for a translation, username or url
/scores/lsp : used by LSPs (language service providers) to submit trusted scores for a translator
/scores/vote : to submit an up/down/block:ban vote 

To submit scores:

* Call the /scores/vote request handler to record a score for a specific
  translation
  
To fetch a detailed score history for a url, translation, etc:

* Call the /scores/get request handler

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
# Import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
# import standard Python libraries
import md5
import string
import datetime
# import WWL and third party modules
from deeppickle import DeepPickle
from lsp import LSP
from www import www
from database import Score
from database import Settings
from database import Translation
from database import Users
from database import UserScores
from geo import geo
from transcoder import transcoder

def clean(text):
    return transcoder.clean(text)

class stat():
    sl = ''
    
class vote():
    favorite = ''
    
class GetScores(webapp.RequestHandler):
    """
    <h3>/scores/get</h3>
    
    This request handler returns a raw score history for a source text,
    translation or username. It expects the following parameters:<p>
    
    <ul><li>guid : the md5 hash or guid for the translation being scored</li>
    <li>url : the URL of the source document you want scores for<li>
    <li>username : the WWL or external username you want a score history for</li>
    <li>remote_addr : the IP address of the translator (for anonymous translations)</li>
    <li>output : output format (xml, json, with xml by default)</li></ul>
    
    It returns output in xml, json or text format.
    """
    def get(self):
        """Processes HTTP GET calls"""
        self.requesthandler()
    def post(self):
        """Processes HTTP POST calls"""
        self.requesthandler()
    def requesthandler(self):
        """Both GET and POST calls are handled in this combined method."""
        guid = self.request.get('guid')
        username = self.request.get('username')
        url = self.request.get('url')
        remote_addr = self.request.get('remote_addr')
        output = self.request.get('output')
        doc = self.request.get('doc')
        if len(output) < 1:
            output = 'xml'
        if len(guid) > 0 or len(username) > 7 or len(url) > 0:
            validquery=True
        else:
            validquery=False
        if validquery:
            results = Score.fetch(guid = guid, url = url, username = username, remote_addr = remote_addr)
            if output == 'xml' or output == 'rss':
                self.response.headers['Content-Type']='text/xml'
            elif output == 'json':
                self.response.headers['Content-Type']='text/plain'
            else:
                self.response.headers['Content-Type']='text/html'
            d = DeepPickle()
            text = d.pickleTable(results, output)
            self.response.out.write(text)
        else:
            t = '<table><form action=/scores/get method=get>'
            t = t + '<tr><td>GUID For Specific Translation</td><td><input type=text name=guid></td></tr>'
            t = t + '<tr><td>WWL Username To Request Scores For</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>User IP Address</td><td><input type=text name=remote_addr></td></tr>'
            t = t + '<tr><td>URL Of Source Document</td><td><input type=text name=url></td></tr>'
            t = t + '<tr><td>Output Format</td><td><input type=text name=output value=xml></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=SEARCH></td></tr>'
            t = t + '</table></form>'
            www.serve(self,t, sidebar=self.__doc__, title = '/scores/get')

class LSPScore(webapp.RequestHandler):
    """
    <h3>/scores/lsp</h3>

    This API is used by language service providers (LSPs), to submit trusted 
    peer review scores for new or unknown community translators. The system 
    uses this information to assess new contributors, and to decide how to 
    promote or filter their translations.<p>

    The API expects the following parameters:<p>

    <ul>
    <li>guid : the globally unique ID of the WWL translation being scored</li>
    <li>lspguid : a unique ID / record locator from the LSPs system (to avoid duplicate votes)</li>
    <li>score : quality score from 0 to 5 (0=spam, 5 = native speaker)</li>
    <li>apikey : LSP's API key</li>
    <li>comment : optional comment</li>
    </ul>

    The API returns 'ok' or an error message.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        guid = self.request.get('guid')
        score = self.request.get('score')
        apikey = self.request.get('apikey')
        comment = self.request.get('comment')
        if len(guid) > 0:
            username = APIKeys.getusername(apikey)
            if len(username) > 0:
                sdb = db.Query(Score)
                sdb.filter('lspguid = ', lspguid)
                item = sdb.get()
                if item is None:
                    try:
                        score = int(score)
                        tdb = db.Query(Translation)
                        tdb.filter('guid = ', guid)
                        item = tdb.get()
                        if item is not None:
                            username = item.username
                            remote_addr = item.remote_addr
                            rawscore = item.rawscore
                            scores = item.scores + 1
                            item.scores = scores
                            rawscore = item.rawscore + score
                            item.rawscore = rawscore
                            item.avgscore = float(float(rawscore)/scores)
                            item.put()
                        else:
                            username = ''
                            remote_addr = ''
                        if len(username) > 0 or len(remote_addr) > 0:
                            if len(remote_addr) > 0:
                                udb = db.Query(UserScores)
                                udb.filter('remote_addr = ', remote_addr)
                                item = udb.get()
                                if item is None:
                                    item.username = username
                                    item.remote_addr = remote_addr
                                rawscore = item.lsprawscore + score
                                scores = item.lspscores + 1
                                rawdata = item.lsprawdata
                                item.lspavgscore = float(float(rawscore)/scores)
                                if type(rawdata) is list:
                                    rawdata.append(score)
                                else:
                                    rawdata = list()
                                    rawdata.append(score)
                                squares = 0
                                for r in rawdata:
                                    squares = squares + pow(avgscore-r, 2)
                                stdev = pow(float(float(squares)/scores),0.5)
                                item.lspstdev = stdev
                                item.lsprawdata = rawdata
                                if score < 1:
                                    item.blockedvotes = item.blockedvotes + 1
                                item.put()
                            if len(username) > 0:
                                udb = db.Query(UserScores)
                                udb.filter('username = ', remote_addr)
                                item = udb.get()
                                if item is None:
                                    item.username = username
                                    item.remote_addr = remote_addr
                                rawscore = item.lsprawscore + score
                                scores = item.lspscores + 1
                                rawdata = item.lsprawdata
                                item.lspavgscore = float(float(rawscore)/scores)
                                if type(rawdata) is list:
                                    rawdata.append(score)
                                else:
                                    rawdata = list()
                                    rawdata.append(score)
                                squares = 0
                                for r in rawdata:
                                    squares = squares + pow(avgscore-r, 2)
                                stdev = pow(float(float(squares)/scores),0.5)
                                item.lsprawdata = rawdata
                                item.lspstdev = stdev
                                if score < 1:
                                    item.blockedvotes = item.blockedvotes + 1
                                item.put()
                            if len(username) > 0:
                                udb = db.Query(Users)
                                udb.filter('username = ', username)
                                item = udb.get()
                                if item is None:
                                    item.username = username
                                    item.remote_addr = remote_addr
                                item.rawscore = rawscore
                                item.avgscore = avgscore
                                item.scores = scores

                    except:
                        self.error(500)
                        self.response.out.write('error\ninvalid input')
            else:
                self.error(500)
                self.response.out.write('error\ninvalid API key')
        else:
            t = '<table><form action=/scores/lsp method=get>'
            t = t + '<tr><td>GUID (guid)</td><td><input type=text name=guid></td></tr>'
            t = t + '<tr><td>LSP GUID (lspguid), internal record locator from LSP</td><td><input type=text name=lspguid></td></tr>'
            t = t + '<tr><td>LSP API Key (apikey)</td><td><input type=text name=apikey></td></tr>'
            t = t + '<tr><td>Score (score=0..5)</td><td><input type=text name=score></td></tr>'
            t = t + '<tr><td>Comment (comment)</td><td><input type=text name=comment></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</form></table>'
            www.serve(self,t,sidebar=self.__doc__,title='/scores/lsp')

class SaveScore(webapp.RequestHandler):
    """
    <h3>/scores/vote</h3>

    This request handler processes scores submitted for translations. This is a fairly simple
    request handler that expects the following:<p>

    <ul><li>guid : unique ID of the translation being scored (required)</li>
    <li>score : the quality score (0..5, 0 = spam/flag)</li>
    <li>username : the scorer's username (optional)</li>
    <li>pw : the scorer's password (optional)</li)
    <li>comment : comment about the translation (optional)</li>
    </ul>

    It returns an ok or error message. 
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        guid = self.request.get('guid')
        score = self.request.get('score')
        username = self.request.get('username')
        pw = self.request.get('pw')
        comment = clean(self.request.get('comment'))
        remote_addr = self.request.remote_addr
        ip = self.request.get('ip')
        try:
            score = int(score)
            validquery = True
        except:
            validquery = False
        if len(ip) > 0:
            remote_addr = ip
        proxy = self.request.get('proxy')
        location = geo.get(remote_addr)
        if type(location) is dict:
            try:
                city = location['city']
                state = location['state']
                country = location['country']
            except:
                city = ''
                state = ''
                country = ''
            try:
                latitude = location['latitude']
                longitude = location['longitude']
            except:
                latitude = None
                longitude = None
        else:
            city = ''
            state = ''
            country = ''
            latitude = None
            longitude = None
        if len(guid) > 0 and validquery:
            if not Score.exists(guid, remote_addr):
                tdb = db.Query(Translation)
                tdb.filter('guid = ', guid)
                item = tdb.get()
                if item is not None:
                    author = item.username
                    authorip = item.remote_addr
                    professional = item.professional
                    sl = item.sl
                    tl = item.tl
                    st = item.st
                    tt = item.tt
                    domain = item.domain
                    url = item.url
                    rawscore = item.rawscore
                    spamvotes = item.spamvotes
                    scores = item.scores
                    scores = scores + 1
                    rawscore = rawscore + score
                    avgscore = float(float(rawscore)/scores)
                    item.scores = scores
                    item.rawscore = rawscore
                    item.avgscore = avgscore
                    if score < 1:
                        try:
                            spamvotes = spamvotes + 1
                            item.spamvotes = spamvotes
                        except:
                            item.spamvotes = 1
                    item.put()
                    if len(author) > 0:
                        username = author
                    else:
                        username = authorip
                    item = Score()
                    item.guid = guid
                    item.sl = sl
                    item.tl = tl
                    item.st = st
                    item.tt = tt
                    item.domain = domain
                    item.url = url
                    item.score = score
                    item.username = author
                    item.remote_addr = authorip
                    item.scoredby = remote_addr
                    item.scoredby_remote_addr = remote_addr
                    item.city = city
                    item.state = state
                    item.country = country
                    if latitude is not None and longitude is not None:
                        item.latitude = latitude
                        item.longitude = longitude
                    item.put()
                    if professional and len(author) > 0:
                        LSP.score(guid, score, lsp=author)
                    if not professional:
                        result = UserScores.score(username=username, remote_addr=authorip, sl=sl, tl=tl, score=score, domain=domain)
                    if professional and len(author) > 0:
                        if len(ip) > 0:
                            remote_addr = ip
                        LSP.score(guid, score, lsp=item.username, remote_addr=remote_addr)
                    self.response.out.write('ok')
                else:
                    self.response.out.write('error : translation not found')
            else:
                self.response.out.write('error : duplicate score')
        else:
            tdb = db.Query(Translation)
            tdb.order('-date')
            item = tdb.get()
            if item is not None:
                guid = item.guid
            else:
                guid = ''
            t = '<table><form action=/scores/vote method=get>'
            t = t + '<tr><td>GUID</td><td><input type=text name=guid value="' + guid + '"></td></tr>'
            t = t + '<tr><td>Score (0..5)</td><td><input type=text name=score></td></tr>'
            t = t + '<tr><td>Username (optional)</td><td><input type=text name=username></td></tr>'
            t = t + '<tr><td>Password (optional)</td><td><input type=text name=pw></td></tr>'
            t = t + '<tr><td>Comment (optional)</td><td><input type=text name=comment></td></tr>'
            t = t + '<tr><td>Submitter IP Address (proxy mode)</td><td><input type=text name=ip></td></tr>'
            t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
            t = t + '</table></form>'
            www.serve(self, t, sidebar=self.__doc__, title = '/scores/vote')

class SetUserScores(webapp.RequestHandler):
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        username = self.request.get('username')
        remote_addr = self.request.get('remote_addr')
        avgscore = self.request.get('avgscore')
        rawscore = self.request.get('rawscore')
        scores = self.request.get('scores')
        blockedvotes = self.request.get('blockedvotes')
        self.response.out.write('ok')

class ResetScores(webapp.RequestHandler):
    def get(self):
        udb = db.Query(Users)
        udb.filter('scores > ', 0)
        results = udb.fetch(limit=250)
        for r in results:
            r.scores = 0
            r.rawscores = list()
            r.rawscore = 0
            r.put()
        sdb = db.Query(Score)
        results = sdb.fetch(limit=250)
        if len(results) > 0:
            db.delete(results)
        tdb = db.Query(Translation)
        tdb.filter('scores > ', 0)
        results = tdb.fetch(limit=250)
        for r in results:
            r.scores = 0
            r.rawscore = 0
            r.userscores = 0
            r.userrawscore = 0
            r.put()
        self.response.out.write('ok')

debug_setting = Settings.get('debug')
if debug_setting == 'True':
    debug_setting = True
elif debug_setting == 'False':
    debug_setting = False
else:
    debug_setting = True            

application = webapp.WSGIApplication([('/scores/get', GetScores),
                                      ('/scores/lsp', LSPScore),
                                      ('/scores/reset', ResetScores),
                                      ('/scores/vote', SaveScore),
                                      ('/scores/user', SetUserScores)], 
                                     debug=debug_setting)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

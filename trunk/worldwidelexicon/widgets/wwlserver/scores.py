# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Project
Comments (comments.py)
by Brian S McConnell <brian@worldwidelexicon.org>

This module implements web services and database calls to retrieve and save
scores for translations. This module defines two web API services:

/scores/batch : to retrieve a batch of summary scores for all translators
                associated with a specific URL and optional target language
/scores/get : to retrieve a score history for a translation, username or url
/scores/vote : to submit an up/down/block:ban vote 
/scores/counter : to request a counter for the number of up/down votes a users has
                   received

To submit scores:

* Call the /scores/vote request handler to record a score for a specific
  translation
  
To fetch a detailed score history for a url, translation, etc:

* Call the /scores/get request handler

To fetch a batch of scores for all translators who have touched translations for
a specific URL

* Call the /scores/batch request handler for this (new)

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
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
# import standard Python libraries
import md5
import urllib
import string
import datetime
# import WWL and third party modules
from deeppickle import DeepPickle
from www import www
from webappcookie import Cookies
from database import Score
from database import Translation
from database import Users
from geo import geo

class stat():
    sl = ''
    
class vote():
    favorite = ''
    
class UserScores(webapp.RequestHandler):
    """
    This worker task recalculates the summary scores for a user. This part of the
    system will be upgraded with a background process that continually recalculates
    summary statistics for the system. It is best not to use this in production
    applications as the interface may change or be deprecated.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        username = self.request.get('username')
        if len(username) > 0:
            # find all scores for user
            sdb = db.Query(Score)
            sdb.filter('username = ', username)
            results = sdb.fetch(limit=100)
            upvotes = 0
            downvotes = 0
            blockedvotes = 0
            avgscore = float(0)
            scores = 0
            for r in results:
                scores = scores + 1
                if r.score == 5:
                    upvotes = upvotes + 1
                elif r.blocked:
                    blockedvotes = blockedvotes + 1
                else:
                    downvotes = downvotes + 1
            rawscore = upvotes * 5
            if scores > 0:
                avgscore = float(rawscore / scores)
            # update user profile
            udb = db.Query(Users)
            udb.filter('username = ', username)
            item = udb.get()
            if item is not None:
                item.upvotes = upvotes
                item.downvotes = downvotes
                item.blockedvotes = blockedvotes
                item.avgscore = avgscore
                item.rawscore = rawscore
                item.scores = scores
                item.put()
            # update userscore stats for translations edited by user
            tdb = db.Query(Translation)
            tdb.filter('username = ', username)
            results = tdb.fetch(limit = 100)
            for r in results:
                r.userupvotes = upvotes
                r.userdownvotes = downvotes
                r.userblockedvotes = blockedvotes
                r.useravgscore = avgscore
                r.userscores = scores
                r.put()
        self.response.out.write('ok"')

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

class Vote(webapp.RequestHandler):
    """
    <h3>/scores/vote</h3>

    This request handler implements the up/down/block voting system to complement the 5 star
    subjective scoring system. This request handler checks to see if the submitting IP address
    is rate limited, and if not, schedules a worker task to log the vote and recalculate
    associated user scores, etc.<p>

    You can submit scores using two methods. The best method is to use the GUID (globally unique
    indentifier) associated with a specific translation. You can also submit the source language,
    target language, text and translation, and the system will attempt to locate matching records
    and record the score for them. Where possible, you should key scores to the GUID as this will
    be more precise, because the system will know which version of which translation the score is
    for.<p>

    It expects the following parameters:<p>

    <ul><li>guid = the GUID of the translation being scored</li>
    <li>sl = source language code (if scoring without guid)</li>
    <li>tl = target language code (if scoring without guid)</li>
    <li>st = source text (if scoring without guid)</li>
    <li>tt = translated text (if scoring without guid)</li>
    <li>votetype = up, down or block</li>
    <li>score = integer score from 0..5 (0=bad/spam, 5 = excellent/native)</li>
    <li>session (cookie) = session cookie, sent automatically if user is logged in to WWL server</li>
    <li>proxy = y/n (y if vote is submitted via proxy server/agent</li>
    <li>ip = user IP address (if proxy=y)</li>
    <li>username = optional WWL username (can be used to authenticate user on submitting score)</li>
    <li>pw = WWL password</li></ul>

    It returns a simple 'ok' or 'error' message
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        rate_limited = memcache.get('ratelimit|vote|' + self.request.remote_addr)
        if rate_limited is None:
            memcache.set('ratelimit|vote|' + self.request.remote_addr, True, 5)
            guid = self.request.get('guid')
            votetype = self.request.get('votetype')
            score = self.request.get('score')
            remote_addr = self.request.remote_addr
            cookies = Cookies(self, max_age=7200)
            try:
                session = cookies['session']
            except:
                session = ''
            username = ''
            pw = ''
            loggedin = False
            if len(session) > 0:
                username = memcache.get('sessions|' + session)
                if username is None:
                    username = self.request.get('username')
                    pw = self.request.get('pw')
                else:
                    loggedin = True
            else:
                username = self.request.get('username')
                pw = self.request.get('pw')
            if not loggedin and len(username) > 0:
                sessinfo = Users.auth(username, pw, '', remote_addr)
                if type(sessinfo) is dict:
                    loggedin=True
                    cookies['session']=sessinfo['session']
                    memcache.set('sessions|' + sessinfo['session'], username, 7200)
                else:
                    username = ''
                    loggedin = False
            if len(guid) > 0:
                location = geo.get(remote_addr)
                p = dict()
                p['guid']=guid
                p['votetype']=votetype
                p['score']=score
                p['remote_addr']=self.request.remote_addr
                p['username']=username
                if type(location) is dict:
                    p['city'] = location['city']
                    p['state'] = location['state']
                    p['country'] = location['country']
                    p['latitude'] = str(location['latitude'])
                    p['longitude'] = str(location['longitude'])
                taskqueue.add(url='/scores/worker', params=p)
                self.response.out.write('ok')
            else:
                t = '<table><form action=/scores/vote method=get>'
                t = t + '<tr><td>GUID of translation</td><td><input type=text name=guid></td></tr>'
                t = t + '<tr><td>Source Language (optional)</td><td><input type=text name=sl></td></tr>'
                t = t + '<tr><td>Target Language (optional)</td><td><input type=text name=tl></td></tr>'
                t = t + '<tr><td>Source Text (optional)</td><td><input type=text name=st></td></tr>'
                t = t + '<tr><td>Translated Text (optional)</td><td><input type=text name=tt></td></tr>'
                t = t + '<tr><td>WWL Username (optional)</td><td><input type=text name=username></td></tr>'
                t = t + '<tr><td>WWL Password (optional)</td><td><input type=text name=pw></td></tr>'
                t = t + '<tr><td>Action (votetype)</td><td><select name=votetype>'
                t = t + '<option value=up>Vote Up (+1)</option>'
                t = t + '<option value=down>Vote Down (-1)</option>'
                t = t + '<option value=block>Block/Ban Translator</option>'
                t = t + '</select></td></tr>'
                t = t + '<tr><td>Integer Score (0..5)</td><td><input type=text name=score maxlength=1></td></tr>'
                t = t + '<tr><td colspan=2><input type=submit value=OK></td></tr>'
                t = t + '</table></form>'
                www.serve(self,t,sidebar=self.__doc__,title = '/scores/vote (Score a Translation)')
        else:
            self.response.out.write('error')

class ScoreSubmitWorker(webapp.RequestHandler):
    """
    /scores/worker

    This request handler is called via the task queue, which serializes votes to minimize
    issues with data store contention, record locking, etc. This task records and updates average
    scores for a translation, and for the user who created that translation.
    """
    def get(self):
        self.requesthandler()
    def post(self):
        self.requesthandler()
    def requesthandler(self):
        votetype = self.request.get('votetype')
        score = self.request.get('score')
        guid = self.request.get('guid')
        username = self.request.get('username')
        remote_addr = self.request.get('remote_addr')
        city = self.request.get('city')
        state = self.request.get('state')
        country = self.request.get('country')
        latitude = self.request.get('latitude')
        longitude = self.request.get('longitude')
        if len(guid) > 0:
            exists = Score.exists(guid, remote_addr)
            if not exists:
                try:
                    author = Translation.author(guid)
                except:
                    author = ''
                try:
                    result = Score.save(guid, votetype=votetype, score=score, username=username, remote_addr=remote_addr, city=city, state=state, country=country, latitude=latitude, longitude=longitude)
                except:
                    result = False
                try:
                    result = Users.savescore(author, votetype, remote_addr, score=score)
                except:
                    result = False
            else:
                result = False
        else:
            result = False
        if result:
            self.response.out.write('ok')
        else:
            self.response.out.write('error')

application = webapp.WSGIApplication([('/scores/get', GetScores),
                                      ('/scores/vote', Vote),
                                      ('/scores/worker', ScoreSubmitWorker),
                                      ('/scores/user', UserScores)], 
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

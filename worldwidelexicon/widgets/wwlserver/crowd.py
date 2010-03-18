# -*- coding: utf-8 -*-
"""
Worldwide Lexicon Database Interface
Community / Crowd Translation Management System (crowd.py)
Brian S McConnell <brian@worldwidelexicon.org>

This module implements several request handlers that are used to manage community
or crowdsourced translation via an open registration system. It implements the
following API calls:

/crowd/register : quick registration for new user
/crowd/add : add a translation task to the queue
/crowd/list : fetch a list of translation tasks from the queue
/crowd/submit : submit a translation
/crowd/score : score a translation

This module automates the process of queueing tasks, and also implements a blind
peer review process so the system learns which users have a good scoring history,
and can decide which translations to accept to the translation memory, which users
to ignore, and so on.

Copyright (c) 1998-2010, Worldwide Lexicon Inc, Brian S McConnell. 
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
# set constants
encoding = 'utf-8'
minimum_score = 2.5
akismet_key = 'foo'
# import Python standard modules
import codecs
import datetime
import md5
import string
import types
import urllib
# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from database import Users

class CrowdSource(db.Model):
    guid = db.StringProperty(default = '')
    sl = db.StringProperty(default = '')
    tl = db.StringProperty(default = '')
    st = db.TextProperty(default = '')
    timestamp = db.DateTimeProperty(auto_now_add = True)
    translated = db.BooleanProperty(default = False)
    domain = db.StringProperty(default='')
    tags = db.ListProperty(str)
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    @staticmethod
    def add(sl, tl, st, username, pw, domain='', tags=None, remote_addr=''):
        m = md5.new()
        m.update(sl)
        m.update(tl)
        m.update(st)
        if len(domain) > 0:
            m.update(domain)
        guid = str(m.hexdigest())
        cdb = db.Query(CrowdSource)
        cdb.filter('guid = ', guid)
        item = cdb.get()
        if item is None:
            item = CrowdSource()
            item.guid = guid
            item.sl = sl
            item.tl = tl
            item.st = st
            item.domain = domain
            if type(tags) is list:
                item.tags = tags
            item.remote_addr = remote_addr
            item.put()
            return True
        else:
            return False
    @staticmethod
    def get(sl, tl, username='', domain='', tag='', limit=10):
        cdb = db.Query(CrowdSource)
        cdb.filter('sl = ', sl)
        cdb.filter('tl = ', tl)
        if len(domain) > 0:
            cdb.filter('domain = ', domain)
        if len(tag) > 0:
            cdb.filter('tags = ', tag)
        cdb.order('timestamp')
        results = cdb.fetch(limit=limit)
        return results
    @staticmethod
    def delete(guid):
        cdb = db.Query(CrowdSource)
        cdb.filter('guid = ', guid)
        item = cdb.get()
        if item is not None:
            item.delete()
            return True
        return False
    @staticmethod
    def submit(guid, tt, username, pw, remote_addr):
        return CrowdTranslation.submit(guid, tt, username, pw, remote_addr)

class CrowdTranslation(db.Model):
    guid = db.StringProperty(default='')
    sl = db.StringProperty(default='')
    tl = db.StringProperty(default='')
    st = db.TextProperty(default='')
    tt = db.TextProperty(default='')
    timestamp = db.DateTimeProperty(auto_now_add = True)
    domain = db.StringProperty(default='')
    tags = db.ListProperty(str)
    username = db.StringProperty(default='')
    remote_addr = db.StringProperty(default='')
    scores = db.ListProperty(str)
    scoredby = db.ListProperty(str)
    avgscore = db.FloatProperty()
    numscores = db.IntegerProperty(default = 0)
    mirrored = db.BooleanProperty(default = False)
    @staticmethod
    def submit(guid, tt, username, pw, remote_addr):
        if len(guid) > 0 and len(tt) > 0:
            cdb = db.Query(CrowdSource)
            cdb.filter('guid = ', guid)
            item = cdb.get()
            if item is not None:
                sl = item.sl
                tl = item.tl
                st = item.st
                domain = item.domain
                tags = item.tags
                item.translated = True
                item.put()
                m = md5.new()
                m.update(sl)
                m.update(tl)
                m.update(st)
                m.update(tt)
                m.update(username)
                md5hash = str(m.hexdigest())
                tdb = db.Query(CrowdTranslation)
                tdb.filter('guid = ', md5hash)
                item = tdb.get()
                if item is None:
                    item = CrowdTranslation()
                    item.sl = sl
                    item.tl = tl
                    item.st = st
                    item.tt = tt
                    item.domain = domain
                    item.tags = tags
                    item.remote_addr = remote_addr)
                    item.put()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    @staticmethod
    def score(guid, score, username, pw):
        if len(guid) > 0:
            tdb = db.Query(CrowdTranslation)
            tdb.filter('guid = ', guid)
            item = tdb.get()
            if item is not None:
                scoredby = item.scoredby
                if username not in scoredby:
                    scoredby.append(username)
                    scores = item.scores
                    scores.append(str(score))
                    avgscore = float(0)
                    rawscore = 0
                    count = 0
                    for s in scores:
                        rawscore = rawscore + int(s)
                        count = count + 1
                    avgscore = float(rawscore / count)
                    item.avgscore = avgscore
                    item.numscores = count
                    item.put()
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    @staticmethod
    def selectwinners():
        """
        This function finds translations that have received the required number of scores and that meet the
        scoring criteria. These are then mirrored into the main translation memory and become visible to WWL
        client applications and tools. Translations that do not have enough scores are kept in queue, while
        translations that receive bad scores are deleted and are never mirrored into the main translation
        memory. 
        """
        tdb = db.Query(CrowdTranslation)
        tdb.filter('mirrored = ', False)
        tdb.filter('avgscore >=', minimum_score)
        results = tdb.fetch(limit=20)
        for r in results:
            if r.avgscore >= minimum_score and r.numscores >= minimum_votes:
                guid = r.guid
                sl = r.sl
                tl = r.tl
                st = r.st
                tt = r.tt
                domain = r.domain
                username = r.username
                remote_addr = r.remote_addr
                r.mirrored = True
                r.put()
                # mirror to Translation() data store
                item = Translation()
                item.sl = sl
                item.tl = tl
                item.st = st
                item.tt = tt
                item.username = username
                item.remote_addr = remote_addr
                item.domain = domain
                item.put()
        return True

"""
Geolocation Module
geo.py
by Brian S McConnell

This module encapsulates calls to geolocation services and maintains
a local cache of geolocated IP addresses, as well as an optional log
to record actions by location. The module calls the Maxmind
geolocation service.

OUTSTANDING ISSUES / TO DO LIST

* Restore transactional logging (currently disabled)

"""

# import Google App Engine modules
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue
# import standard Python libraries
import cgi
import urllib
import string
import datetime
# import WWL libraries
from database import Settings
from transcoder import transcoder

def clean(text):
    return transcoder.clean(text)

class GeoDB(db.Model):
    """
    This is the main data store where we memorize IP addresses and location information
    associated with them. The system currently uses Maxmind as its primary geolocation
    service, but this may be updated when new options become available for IP to lat/long
    geolocation. 
    """
    remote_addr = db.StringProperty(default = '')
    website = db.StringProperty(default = '')
    country = db.StringProperty(default = '')
    state = db.StringProperty(default = '')
    city = db.StringProperty(default = '')
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    lastupdated = db.DateTimeProperty(auto_now_add = True)

class geo():
    """
    This class encapsulates methods to provide a variety of location services, to call out to
    geolocation service providers, read or write to the geolocation data stores, and so on. 
    """
    @staticmethod
    def log(remote_addr, city, state, country, latitude, longitude, action='', username='', sl ='', tl = '', website=''):
        """
        Transactional logging is currently disabled, but will be restored soon.
        """
        return True
    @staticmethod
    def countries():
        clist = dict()
        return clist
    @staticmethod
    def query(remote_addr, website=''):
        """
        Queries the Maxmind geolocation service to obtain a location fix
        for an IP address.
        """
        license_key=Settings.get('maxmind')
        location = dict()
        geolist=list()
        location['country']=''
        location['state']=''
        location['city']=''
        location['latitude']=None
        location['longitude']=None
        if len(remote_addr) > 4 and license_key is not None:
            url = 'http://geoip1.maxmind.com/b?l=' + license_key + '&i=' + remote_addr
            try:
                result=urlfetch.fetch(url)
                if result.status_code == 200:
                    geo = result.content
            except:
                geo = ''
        else:
            geo = ''
        if len(geo) > 1:
            geolist = string.split(geo,',')
        if len(geolist) > 0:
            ctr=0
            for i in geolist:
                if ctr==0:
                    location['country']=i
                elif ctr==1:
                    location['state']=i
                elif ctr==2:
                    location['city']=i
                elif ctr==3:
                    if len(i) > 0:
                        location['latitude']=float(i)
                elif ctr==4:
                    if len(i) > 0:
                        location['longitude']=float(i)
                ctr=ctr+1
        return location
    @staticmethod
    def get(remote_addr, action='', username='', sl = '', tl = '', website = ''):
        """
        This is the main method called by other parts of the system to fetch a location
        for an IP address. It first looks in memcache for a recent result, then the
        persistent data store, and then calls out to the Maxmind geolocation service.
        Transactional logging is currently disabled, but will be restored in an update
        fairly soon.
        """
        username = clean(username)
        website = clean(website)
        location = memcache.get('geo|' + remote_addr)
        location = None
        if location is not None:
            return location
        else:
            gdb = db.Query(GeoDB)
            gdb.filter('remote_addr = ', remote_addr)
            item = gdb.get()
            location = dict()
            if item is not None:
                if len(location.get('country', '')) > 1:
                    location['city'] = clean(item.city)
                    location['state'] = clean(item.state)
                    location['country'] = clean(item.country)
                    location['latitude'] = item.latitude
                    location['longitude'] = item.longitude
                    memcache.set('geo|' + remote_addr, location, 1800)
                    geo.log(remote_addr, location['city'], location['state'], location['country'], location['latitude'], location['longitude'], action, username, sl, tl)
                    return location
            if len(location.get('country', '')) < 2:
                location = geo.query(remote_addr, website=website)
                if len(location.get('country','')) > 1:
                    gdb = db.Query(GeoDB)
                    gdb.filter('remote_addr = ', remote_addr)
                    item = gdb.get()
                    if item is None:
                        item = GeoDB()
                    try:
                        item.remote_addr = remote_addr
                        item.city = location['city']
                        item.state = location['state']
                        item.country = location['country']
                    except:
                        pass
                    try:
                        item.latitude = location['latitude']
                        item.longitude = location['longitude']
                    except:
                        pass
                    item.lastupdated = datetime.datetime.now()
                    item.website = website
                    try:
                        item.put()
                    except:
                        pass
                    memcache.set('geo|' + remote_addr, location, 1800)
                return location
            
class GetLocation(webapp.RequestHandler):
    def get(self):
        ip = self.request.get('ip')
        location = geo.get(ip)
        self.response.out.write(location.get('city','') + '\n')
        self.response.out.write(location.get('country','') + '\n')
        self.response.out.write(str(location.get('latitude','')) + '\n')
        self.response.out.write(str(location.get('longitude','')) + '\n')
            
application = webapp.WSGIApplication([('/geo', GetLocation)],
                                     debug=False)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

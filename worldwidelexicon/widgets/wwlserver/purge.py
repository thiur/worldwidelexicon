import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from geo import geo

class Translation(db.Model):
    sl = db.StringProperty(default='')
    
class Objects(db.Model):
    title = db.StringProperty(default='')
    
class GeoLog(db.Model):
    date = db.DateTimeProperty()

class GeoDB(db.Model):
    country = db.TextProperty()

class purge(webapp.RequestHandler):
    def get(self, name=""):
        if name == 'Objects':
            wdb = db.Query(Objects)
        elif name == 'GeoLog':
            result = geo.purge()
            self.response.out.write('ok')
            return
        elif name == 'GeoDB':
            wdb = db.Query(GeoDB)
            wdb.filter('country = ', '')
        else:
            wdb = db.Query(GeoLog)
            wdb.order('date')
        results = wdb.fetch(limit=500)
        if results is not None:
            db.delete(results)
        self.response.out.write('ok')

application = webapp.WSGIApplication([(r'/purge/(.*)', purge)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()

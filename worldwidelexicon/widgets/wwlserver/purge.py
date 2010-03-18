import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class Translation(db.Model):
    sl = db.StringProperty(default='')
    
class RSS(db.Model):
    title = db.StringProperty(default='')
    
class Tag(db.Model):
    text = db.StringProperty(default='')

class purge(webapp.RequestHandler):
    def get(self, name=""):
        if name == 'Translation':
            wdb = db.Query(Translation)
        elif name == 'RSS':
            wdb = db.Query(RSS)
        elif name == 'Tag':
            wdb = db.Query(Tag)
        else:
            wdb = db.Query(Translation)
        results = wdb.fetch(limit=100)
        if results is not None:
            db.delete(results)
        self.response.out.write('ok')

application = webapp.WSGIApplication([(r'/purge/(.*)', purge)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    
if __name__ == "__main__":
    main()
import urllib2
import string
import demjson

class Localize():
    wwlserver = 'http://www.dermundo.com/wwl/'
    domain = 'cnn.com'
    # define texts to translate (can also be loaded from a list, file or db call)
    texts = dict(
        hello = 'hello',
        goodbye = 'goodbye',
        flowers = 'flowers',
    )
    def translate(self, language):
        #try:
        result = urllib2.urlopen(self.wwlserver + '/u?tl=' + language + '&url=' + self.domain)
        json = result.read()
        print json
        translations = demjson.decode(json)
        print translations
        #except urllib2.URLError, e:
        #    translations = None
        if translations is not None:
            for t in translations:
                if t.get('st','') in self.texts:
                    self.texts[t.get('st','')]=t.get('tt','')
        return self.texts
    
import json
import httplib2
import functools

HOST = "http://api.geonames.org"
URL = "%s/findNearbyPlaceName?username=%%(user_name)s&type=json&lat=%%(lat)f&lng=%%(lon)f" % HOST

class lookup:
    def __init__ (self, user_name, lat, lon):
        self.user_name, self.lat, self.lon = user_name, lat, lon
    def __call__(self):
        if self.lat is not None and self.lon is not None:
            http = httplib2.Http('.cache')
            resp, body = http.request(URL % self.__dict__, 'GET')
            try: body = body.decode()
            except: pass
            geoname_id = json.loads(body).get('geonames')[0].get('geonameId')
            return "http://sws.geonames.org/%s" % geoname_id
    to_rdf = __call__
        
lookup_factory = lambda user_name: functools.partial(lookup, user_name)
        
if __name__ == '__main__':
    # USER_NAME needs to be provided by end user
    print(lookup(USER_NAME, 47.4, 9)())

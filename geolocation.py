import geopy
from geopy.geocoders import Nominatim

class Geolocation:
    def __init__(self, agent):
        self.geolocator = Nominatim(user_agent=agent)

    def get_address(self, location):
        geolocation = self.geolocator.reverse(location)

        try:
            road = geolocation.raw['address']['road']
        except:
            road = ""

        try:
            house =  " " + geolocation.raw['address']['house_number']
        except:
            house = ""

        try:
            city = ", " + geolocation.raw['address']['city']
        except:
            city = ""

        try:
            town = ", " + geolocation.raw['address']['town']
        except:
            town = ""

        try:
            village = ", " + geolocation.raw['address']['village']
        except:
            village = ""

        try:
            country = ", " + geolocation.raw['address']['country']
        except:
            country = ""

        try:
            postcode = ", " + geolocation.raw['address']['postcode']
        except:
            postcode = ""

        address = road + house + postcode + village + town + city + country

        return address


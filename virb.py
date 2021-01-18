import os
import simplejson
import requests

class Virb():
    """Class to interact with Garmin Virb cameras over wifi / http"""
    def __init__(self, host=('192.168.0.1', 80)):
        """Sets up the connection with the Virb device

        Accepts an ip and port which should be routable from the device running
        the code.

        host = ('192.168.0.1', 80)
        """
        self.host = host
        self.requestcount = 0

    def status(self):
        """Returns the current camera status"""
        command = 'status'
        data = {'command': command}
        return self._do_post(data=data)

    def live_preview(self, streamtype="rtp"):
        """Returns the cameras live preview url"""
        command = 'livePreview'
        data = {'command':command,
                'streamType':streamtype}
        return self._do_post(data=data)['url']

    def set_features(self, feature, value):
        """Update a features"""
        command = 'updateFeature'
        data = {'command': command,
                'feature': feature,
                'value': value}
        return self._do_post(data=data)['features']

    def start_recording(self):
        """Start recording"""
        command = "startRecording"
        data = {'command':command}
        return bool(int(self._do_post(data=data)['result']))

    def stop_recording(self):
        """Stop recording"""
        command = 'stopRecording'
        data = {'command':command}
        return bool(int(self._do_post(data=data)['result']))

    def get_speed(self):
        status = self.status()
        try:
            return status['speed']*3.6
        except:
            return -999

    def get_latitude(self):
        status = self.status()

        try:
            return status['gpsLatitude']
        except:
            return -999

    def get_longitude(self):
        status = self.status()

        try:
            return status['gpsLongitude']
        except:
            return -999

    def get_altitude(self):
        status = self.status()

        try:
            return status['altitude']
        except:
            return -999

    def get_batt_status(self):
        status = self.status()
        return status['batteryLevel']

    def _do_post(self, url='virb', data=None):
        url = 'http://%s:%d/%s' % (self.host[0], self.host[1], url)
        request = requests.post(url, data=simplejson.dumps(data))
        self.requestcount += 1
        try:
            return request.json()
        except simplejson.scanner.JSONDecodeError:
            return request.text


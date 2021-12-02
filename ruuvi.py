"""
Ruuvitag sensor data class
"""
class Ruuvi:
    """ Ruuvitag sensor class """
    def __init__(self):
        self.temperature = float('nan')
        self.humidity = float('nan')
        self.pressure = float('nan')
        self.vbatt = float('nan')

    def set_temperature(self, temp):
        """ set temperature """
        self.temperature = temp

    def set_humidity(self, humidity):
        """ set humidity """
        self.humidity = humidity

    def set_pressure(self, pressure):
        """ set pressure """
        self.pressure = pressure

    def set_vbat(self, vbatt):
        """ set battery voltage """
        self.vbatt = vbatt

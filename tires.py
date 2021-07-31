"""
Tire class for TPMS
"""
import math

class Tire:
    """ Single tire """
    def __init__(self):
        self.pressure = math.nan
        self.temperature = math.nan
        self.warn = 0

    def set_pressure(self, pressure):
        """ set tire pressure """
        self.pressure = pressure

    def set_temperature(self, temperature):
        """ set tire temperature """
        self.temperature = temperature

    def set_warn(self, warn):
        """ set tire pressure warn level """
        self.warn = warn

class Tires:
    """ Tire class """
    def __init__(self):
        self.FrontLeft = Tire()
        self.FrontRight = Tire()
        self.RearLeft = Tire()
        self.RearRight = Tire()
        self.warn_pressure = 0.0

    def setPressure(self, tire, pressure):
        if tire == 'FL':
            self.FrontLeft.set_pressure(pressure)
        elif tire == 'FR':
            self.FrontRight.set_pressure(pressure)
        elif tire == 'RL':
            self.RearLeft.set_pressure(pressure)
        elif tire == 'RR':
            self.RearRight.set_pressure(pressure)

    def setTemperature(self, tire, temperature):
        if tire == 'FL':
            self.FrontLeft.set_temperature(temperature)
        elif tire == 'FR':
            self.FrontRight.set_temperature(temperature)
        elif tire == 'RL':
            self.RearLeft.set_temperature(temperature)
        elif tire == 'RR':
            self.RearRight.set_temperature(temperature)

    def setWarn(self, tire, val):
        if tire == 'FL':
            self.FrontLeft.set_warn(val)
        elif tire == 'FR':
            self.FrontRight.set_warn(val)
        elif tire == 'RL':
            self.RearLeft.set_warn(val)
        elif tire == 'RR':
            self.RearRight.set_warn(val)

    def setWarnPressure(self, val):
        self.warn_pressure = val

    def getPressure(self, tire):
        if tire == 'FL':
            return self.FrontLeft.pressure
        elif tire == 'FR':
            return self.FrontRight.pressure
        elif tire == 'RL':
            return self.RearLeft.pressure
        elif tire == 'RR':
            return self.RearRight.pressure

    def getTemperature(self, tire):
        if tire == 'FL':
            return self.FrontLeft.temperature
        elif tire == 'FR':
            return self.FrontRight.temperature
        elif tire == 'RL':
            return self.RearLeft.temperature
        elif tire == 'RR':
            return self.RearRight.temperature

    def getWarnPressure(self):
        return self.warn_pressure

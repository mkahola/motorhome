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
        self.front_left = Tire()
        self.front_right = Tire()
        self.rear_left = Tire()
        self.rear_right = Tire()
        self.spear = Tire()
        self.warn_pressure = 0.0

    def set_pressure(self, tire, pressure):
        """ set tire pressure """
        if tire == 'FL':
            self.front_left.set_pressure(pressure)
        elif tire == 'FR':
            self.front_right.set_pressure(pressure)
        elif tire == 'RL':
            self.rear_left.set_pressure(pressure)
        elif tire == 'RR':
            self.rear_right.set_pressure(pressure)
        elif tire == "Spear":
            self.spear.set_pressure(pressure)

    def set_temperature(self, tire, temperature):
        """ set tire temperature """
        if tire == 'FL':
            self.front_left.set_temperature(temperature)
        elif tire == 'FR':
            self.front_right.set_temperature(temperature)
        elif tire == 'RL':
            self.rear_left.set_temperature(temperature)
        elif tire == 'RR':
            self.rear_right.set_temperature(temperature)
        elif tire == "Spear":
            self.spear.set_temperature(temperature)

    def set_warn(self, tire, val):
        """ set tire pressure warn level """
        if tire == 'FL':
            self.front_left.set_warn(val)
        elif tire == 'FR':
            self.front_right.set_warn(val)
        elif tire == 'RL':
            self.rear_left.set_warn(val)
        elif tire == 'RR':
            self.rear_right.set_warn(val)
        elif tire == "Spear":
            self.spear.set_warn(val)

    def set_warn_pressure(self, val):
        """ set tire pressure warn level """
        self.warn_pressure = val

    def get_pressure(self, tire):
        """ get tire pressure """

        pressure = 0.0

        if tire == 'FL':
            pressure = self.front_left.pressure
        elif tire == 'FR':
            pressure = self.front_right.pressure
        elif tire == 'RL':
            pressure = self.rear_left.pressure
        elif tire == 'RR':
            pressure = self.rear_right.pressure
        elif tire == "Spear":
            pressure = self.spear.pressure

        return pressure

    def get_temperature(self, tire):
        """ get tire temperature """

        temperature = 0.0

        if tire == 'FL':
            temperature = self.front_left.temperature
        elif tire == 'FR':
            temperature = self.front_right.temperature
        elif tire == 'RL':
            temperature = self.rear_left.temperature
        elif tire == 'RR':
            temperature = self.rear_right.temperature
        elif tire == "Spear":
            temperature = self.spear.temperature

        return temperature

    def get_warn_pressure(self):
        """ get tire pressure warn level """
        return self.warn_pressure

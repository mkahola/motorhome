import math

class Tires:
    def __init__(self):
        self.FrontLeftPressure = math.nan
        self.FrontLeftTemp = math.nan
        self.FrontRightPressure = math.nan
        self.FrontRightTemp = math.nan
        self.RearLeftPressure = math.nan
        self.RearLeftTemp = math.nan
        self.RearRightPressure = math.nan
        self.RearRightTemp = math.nan
        self.FrontLeftWarn = 0
        self.FrontRightWarn = 0
        self.RearLeftWarn = 0
        self.RearRightWarn = 0
        self.warnPressure = 0.0

    def setPressure(self, tire, pressure):
        if tire == 'FL':
            self.FrontLeftPressure = pressure
        elif tire == 'FR':
            self.FrontRightPressure = pressure
        elif tire == 'RL':
            self.RearLeftPressure = pressure
        elif tire == 'RR':
            self.RearRightPressure = pressure

    def setTemperature(self, tire, temperature):
        if tire == 'FL':
            self.FrontLeftTemp = temperature
        elif tire == 'FR':
            self.FrontRightTemp = temperature
        elif tire == 'RL':
            self.RearLeftTemp = temperature
        elif tire == 'RR':
            self.RearRightTemp = temperature

    def setWarn(self, tire, val):
        if tire == 'FL':
            self.FrontLeftWarn = val
        elif tire == 'FR':
            self.FrontRightWarn = val
        elif tire == 'RL':
            self.RearLeftWarn = val
        elif tire == 'RR':
            self.RearRightWarn = val

    def setWarnPressure(self, val):
        self.warnPressure = val

    def getPressure(self, tire):
        if tire == 'FL':
            return self.FrontLeftPressure
        elif tire == 'FR':
            return self.FrontRightPressure
        elif tire == 'RL':
            return self.RearLeftPressure
        elif tire == 'RR':
            return self.RearRightPressure

    def getTemperature(self, tire):
        if tire == 'FL':
            return self.FrontLeftTemp
        elif tire == 'FR':
            return self.FrontRightTemp
        elif tire == 'RL':
            return self.RearLeftTemp
        elif tire == 'RR':
            return self.RearRightTemp

    def getWarnPressure(self):
        return self.warnPressure

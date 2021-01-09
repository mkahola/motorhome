class Tires:
    def __init__(self):
        self.FrontLeftPressure = 0.0
        self.FrontLeftTemp = 0
        self.FrontRightPressure = 0.0
        self.FrontRightTemp = 0
        self.RearLeftPressure = 0.0
        self.RearLeftTemp = 0
        self.RearRightPressure = 0.0
        self.RearRightTemp = 0
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

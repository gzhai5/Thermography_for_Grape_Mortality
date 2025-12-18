class IRFormatType:
    LINEAR_10MK = 1
    LINEAR_100MK = 2
    RADIOMETRIC = 3

CHOSEN_IR_TYPE = IRFormatType.LINEAR_100MK


# alibration details
R = 5.92
A1 = 0.01
A2 = 0.21
B = 3115.42
F = 1
X = 0.91
B1 = 0
B2 = 0.01
J0 = 0
J1 = 0

# object parameters
Emiss = 0.97
TRefl = 293.15
TAtm = 293.15
TAtmC = TAtm - 273.15
Humidity = 0.55
Dist = 2
ExtOpticsTransmission = 1
ExtOpticsTemp = TAtm
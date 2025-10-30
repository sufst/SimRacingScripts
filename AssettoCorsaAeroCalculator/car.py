"""
This python file (car.py) is for the car (reads the car data and has the functions to interpret it)

main.py is for specifying what to do (i.e. what car to look at, whether to plot aero maps, limits for optimisaion, etc.)

To Do:
    - Add to optimiseAeroRHTelem():
        - Something to get the aero maps of all the wing angle combinations, then linearly interpolate to find the aero
            numbers - should be faster than calculating the aero for every ride height
        - An array argument that allows aero balance for that telemetry data point to be ignored if the array element is
            0 or something
            - Mostly to allow drag/efficiency to be quantified for weird tracks like ovals (considering ride heights in
                banked corners may not be the same as ride heights on the straights, and you don't care about aero balance
                when going down a straight)
            - Also since aero balance isn't hugely relevant for straight line braking
        - An argument that invalidates setups if they have a maximum aero balance shift greater than the value passed in
            - Probably would set this to like 10% or something for most cars

    - Add function to plot aero stuff against speed
        - Would require spring rates for:
            - Individual springs
            - Heave springs
            - Tyre
            - Bump stops (and bumpstop range)
                - Assume that hard stops aren't reached? (Otherwise would require BUMPSTOP_UP, ROD_LENGTH etc.)
        - Decide on speed resolution (probably 10 km/h)
        - Provide static ride height (i.e. from the pit lane)
        - Starting at 0 km/h (so ride heights are the static ride heights):
            - Do a few iterations of:
                - Using previous ride height, calculateAero() to get ClA and aeroBalance
                - Adjust ride heights accordingly based on front and rear downforce calculated from ClA, aeroBalance and
                    speed (using a constant air density - although this isn't exactly constant from track to track)
            - Append outputs of calculateAero() and the "final" ride heights at that speed to the appropriate arrays
            - Increment speed
        - Plot aero stuff calculated against speed

    - Add Fin class for dealing with fins in aero.ini
        - Would just assume yaw to be 0 atm though
"""
import math
import matplotlib.pyplot as plt
import numpy as np


def linearInterpolate(x, x1, x2, y1, y2):
    """Returns the linear interpolation between y for the given value of x"""
    return y1 + ((x - x1) * (y2 - y1) / (x2 - x1))


def readLUT(x, LUT):
    """Returns the LUT value of y for the supplied value of x, using linear interpolation between LUT entries
       LUT defined as [[x0, y1], [x1, y1], [x2, y2], ...], where x is in ascending order
       If the x value supplied is beyond the range of the LUT, y value of the nearest x value will be returned"""
    # Check if the x value is within the range of the LUT
    if x <= LUT[0][0]:
        return LUT[0][1]
    if x >= LUT[len(LUT) - 1][0]:
        return LUT[len(LUT) - 1][1]

    # Search for the indexes that surround the x value (search for upper index, but lowerIndex = upperIndex - 1)
    upperIndex = 0
    found = False
    while upperIndex < len(LUT) - 1 and not found:
        upperIndex += 1
        if LUT[upperIndex][0] >= x:
            found = True
    lowerIndex = upperIndex - 1

    # Return the linear interpolation between the lower and upper indexes
    return linearInterpolate(x, LUT[lowerIndex][0], LUT[upperIndex][0], LUT[lowerIndex][1], LUT[upperIndex][1])


def readLUTFile(LUTFilePath):
    """Reads the LUT file defined by LUTFilePath and returns the LUT in the form of a 2D array
        If passed an file path that doesn't end with ".lut", returns the unit LUT unitLUT = [[0, 1], [1, 1]]"""
    # Check if LUTFilePath is a LUT file
    if LUTFilePath.lower().endswith(".lut"):
        LUTFile = open(LUTFilePath, "r")
        LUT = []
        for line in LUTFile:
            dataString = line.replace("\n", "").replace("\t", "").replace(" ", "").split(";")[0]
            if not dataString == "":
                data = dataString.split("|")
                LUT.append([float(data[0]), float(data[1])])
        LUTFile.close()
        return LUT
    else:
        return [[0, 1], [1, 1]]


def clipArrayData(dataArray, lowerBound, upperBound):
    """Clips array data to between lowerBound and upperBound
        Also sets the 2nd last array value to lowerBound and last array value to upperBound for colour map reasons"""
    for i in range(len(dataArray)):
        if dataArray[i] < lowerBound:
            dataArray[i] = lowerBound
        elif dataArray[i] > upperBound:
            dataArray[i] = upperBound
    dataArray[-2] = lowerBound
    dataArray[-1] = upperBound
    return dataArray


def clipArrayData2D(dataArray2D, lowerBound, upperBound):
    """Clips array data to between lowerBound and upperBound
        Also sets the dataArray2D[-1][-2] to lowerBound and dataArray2D[-1][-1] to upperBound for colour map reasons"""
    for rowIndex in range(len(dataArray2D)):
        for columnIndex in range(len(dataArray2D[rowIndex])):
            if dataArray2D[rowIndex][columnIndex] < lowerBound:
                dataArray2D[rowIndex][columnIndex] = lowerBound
            elif dataArray2D[rowIndex][columnIndex] > upperBound:
                dataArray2D[rowIndex][columnIndex] = upperBound
    dataArray2D[-1][-2] = lowerBound
    dataArray2D[-1][-1] = upperBound
    return dataArray2D


def getRHEnvelope2D(frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, frontRHTelem, rearRHTelem):
    """Returns the 2D array RHEnvelope2D

        frontRHTelem and rearRHTelem must be 1D arrays of the same length, and in metres

        A ride height combination will be within the envelope if it rounds to the same mm as a telemetry ride height"""
    RHEnvelope2D = []

    # Round each value in frontRHTelem and rearRHTelem to the nearest integer
    frontRHTelem = [round(i, 3) for i in frontRHTelem]
    rearRHTelem = [round(i, 3) for i in rearRHTelem]

    # Create an array storing each (rounded) telemetry ride height combo - [[frontRH, rearRH], [frontRH2, rearRH2], ...]
    telemRHCombinations = []
    for i in range(len(frontRHTelem)):
        telemRHCombinations.append([frontRHTelem[i], rearRHTelem[i]])

    """# Turn telemRHCombinations into a set for faster searching
    telemRHCombinations = set(telemRHCombinations)"""

    # Floating point maths reasons
    RHMargin = RHStep / 2

    rearRH = rearRHMin
    while rearRH <= rearRHMax + RHMargin:
        # Add a new row to the 2D array to represent a new rear RH
        RHEnvelope2D.append([])

        frontRH = frontRHMin
        while frontRH <= frontRHMax + RHMargin:
            # If the ride height combination is in the telemRHCombinations set
            if [round(frontRH, 3), round(rearRH, 3)] in telemRHCombinations:
                RHEnvelope2D[-1].append(1)
            else:
                RHEnvelope2D[-1].append(0)
            frontRH += RHStep
        rearRH += RHStep

    return RHEnvelope2D


def GHTransform(position, CGHeight, rake):
    """Returns the ground height of the point (in metres), accounting for rake, assuming no roll"""
    return CGHeight + position[1] - (position[2] * math.sin(math.radians(rake)))


def posZTransform(position, rake):
    """Returns the z position of the point relative to the CG, accounting for rake, assuming no roll"""
    return position[2] * math.cos(math.radians(rake))


class Collider:
    def __init__(self, CENTRE, SIZE):
        self.CENTRE = CENTRE
        self.SIZE = SIZE

    def getPositionLowerEdges(self):
        """Returns a 2D array containing the y and z coordinates of the lower edges relative to the CG
           Assumes no rake and no roll"""
        frontY = self.CENTRE[1] - (self.SIZE[1] / 2)
        frontZ = self.CENTRE[2] + (self.SIZE[2] / 2)
        rearY = self.CENTRE[1] - (self.SIZE[1] / 2)
        rearZ = self.CENTRE[2] - (self.SIZE[2] / 2)

        return [[frontY, frontZ], [rearY, rearZ]]

    def isValid(self, CGHeight, rake, colliderMargin):
        """Returns true if there is a ground collision, for colliderMargin in metres"""
        positionLowerEdges = self.getPositionLowerEdges()
        frontCentrePos = [self.CENTRE[0], positionLowerEdges[0][0], positionLowerEdges[0][1]]
        rearCentrePos = [self.CENTRE[0], positionLowerEdges[1][0], positionLowerEdges[1][1]]

        return (GHTransform(frontCentrePos, CGHeight, rake) >= colliderMargin
                and GHTransform(rearCentrePos, CGHeight, rake) >= colliderMargin)


class Wing:
    def __init__(self, CHORD, SPAN, POSITION, LUT_AOA_CL, LUT_GH_CL, CL_GAIN, LUT_AOA_CD, LUT_GH_CD, CD_GAIN, ANGLE):
        # All arguments required from aero.ini to calculate aero at 0 yaw angle
        self.CHORD = CHORD
        self.SPAN = SPAN
        self.POSITION = POSITION
        self.LUT_AOA_CL = LUT_AOA_CL
        self.LUT_GH_CL = LUT_GH_CL
        self.CL_GAIN = CL_GAIN
        self.LUT_AOA_CD = LUT_AOA_CD
        self.LUT_GH_CD = LUT_GH_CD
        self.CD_GAIN = CD_GAIN
        self.ANGLE = ANGLE

    def calculateWing(self, car, CGHeight, rake):
        """Returns a tuple of (ClA, CdA, Effective Front ClA, Effective Rear ClA) given the CGHeight, rake and static
            AOA of the wing
            Includes the effect of the drag on the wing being at a height from the ground (shifts aero balance back)"""
        GH = GHTransform(self.POSITION, CGHeight, rake)
        posZ = posZTransform(self.POSITION, rake)
        ClA = (self.CHORD * self.SPAN * self.CL_GAIN * readLUT(rake + self.ANGLE, self.LUT_AOA_CL)
               * readLUT(GH, self.LUT_GH_CL))
        CdA = (self.CHORD * self.SPAN * self.CD_GAIN * readLUT(rake + self.ANGLE, self.LUT_AOA_CD)
               * readLUT(GH, self.LUT_GH_CD))

        # Account for the moment produced by the drag force being at a height
        effFrontClA = ((((car.WHEELBASE * car.CG_LOCATION + posZ) / car.WHEELBASE) * ClA)
                       - (CdA * GH / car.WHEELBASE))
        effRearClA = ClA - effFrontClA

        return ClA, CdA, effFrontClA, effRearClA


class Car:
    def __init__(self, carsDirectory, carName):
        """Reads car data from the data folder and assigns it to the relevant variables:
            - carName
            - PICKUP_FRONT_HEIGHT
            - PICKUP_REAR_HEIGHT
            - WHEELBASE
            - CG_LOCATION
            - colliders[Collider]
            - wings[Wing]
            - defaultWingAngles[]
            Also prints out general info about the car"""
        self.carName = carName
        carDataDirectory = carsDirectory + "\\" + carName + "\\data\\"

        # Read PICKUP_FRONT_HEIGHT and PICKUP_REAR_HEIGHT from car.ini
        self.PICKUP_FRONT_HEIGHT, self.PICKUP_REAR_HEIGHT = None, None
        carINIFile = open(carDataDirectory + "\\car.ini", "r")
        for line in carINIFile:
            dataString = line.replace("\n", "").replace("\t", "").replace(" ", "")
            if dataString.__contains__("PICKUP_FRONT_HEIGHT="):
                self.PICKUP_FRONT_HEIGHT = float(dataString.split("PICKUP_FRONT_HEIGHT=")[1].split(";")[0])
            elif dataString.__contains__("PICKUP_REAR_HEIGHT="):
                self.PICKUP_REAR_HEIGHT = float(dataString.split("PICKUP_REAR_HEIGHT=")[1].split(";")[0])
        carINIFile.close()

        # Read WHEELBASE and CG_LOCATION from suspensions.ini
        self.WHEELBASE, self.CG_LOCATION = None, None
        suspensionsINIFile = open(carDataDirectory + "\\suspensions.ini", "r")
        for line in suspensionsINIFile:
            dataString = line.replace("\n", "").replace("\t", "").replace(" ", "")
            if dataString.__contains__("WHEELBASE="):
                self.WHEELBASE = float(dataString.split("WHEELBASE=")[1].split(";")[0])
            elif dataString.__contains__("CG_LOCATION="):
                self.CG_LOCATION = float(dataString.split("CG_LOCATION=")[1].split(";")[0])
        suspensionsINIFile.close()

        # Read colliders from colliders.ini - Also only adds them to colliders[] if GROUND_ENABLE = 1
        self.colliders = []
        CENTRE, SIZE, GROUND_ENABLE = None, None, None
        collidersINIFile = open(carDataDirectory + "\\colliders.ini", "r")
        for line in collidersINIFile:
            dataString = line.replace("\n", "").replace("\t", "").replace(" ", "")
            if dataString.__contains__("CENTRE="):
                CENTRE = [float(i) for i in dataString.split("CENTRE=")[1].split(";")[0].split(",")]
            elif dataString.__contains__("SIZE="):
                SIZE = [float(i) for i in dataString.split("SIZE=")[1].split(";")[0].split(",")]
            elif dataString.__contains__("GROUND_ENABLE="):
                GROUND_ENABLE = dataString.split("GROUND_ENABLE=")[1].split(";")[0].split(",")[0]
            # If all the necessary data has been read for a Collider object to be initialised
            if CENTRE and SIZE and GROUND_ENABLE:
                if GROUND_ENABLE == "1":
                    self.colliders.append(Collider(CENTRE, SIZE))
                CENTRE, SIZE, GROUND_ENABLE = None, None, None
        collidersINIFile.close()

        # Read wings from aero.ini
        self.wings = []
        self.defaultWingAngles = []

        CHORD, SPAN, POSITION, LUT_AOA_CL, LUT_GH_CL, CL_GAIN, LUT_AOA_CD, LUT_GH_CD, CD_GAIN, ANGLE = None, None, None, None, None, None, None, None, None, None
        aeroINIFile = open(carDataDirectory + "\\aero.ini", "r")
        for line in aeroINIFile:
            dataString = line.replace("\n", "").replace("\t", "").replace(" ", "")
            if dataString.__contains__("CHORD="):
                CHORD = float(dataString.split("CHORD=")[1].split(";")[0])
            elif dataString.__contains__("SPAN="):
                SPAN = float(dataString.split("SPAN=")[1].split(";")[0])
            elif dataString.__contains__("POSITION="):
                POSITION = [float(i) for i in dataString.split("POSITION=")[1].split(";")[0].split(",")]
            elif dataString.__contains__("LUT_AOA_CL="):
                LUT_AOA_CL = readLUTFile(carDataDirectory + dataString.split("LUT_AOA_CL=")[1].split(";")[0])
            elif dataString.__contains__("LUT_GH_CL="):
                LUT_GH_CL = readLUTFile(carDataDirectory + dataString.split("LUT_GH_CL=")[1].split(";")[0])
            elif dataString.__contains__("CL_GAIN="):
                CL_GAIN = float(dataString.split("CL_GAIN=")[1].split(";")[0])
            elif dataString.__contains__("LUT_AOA_CD="):
                LUT_AOA_CD = readLUTFile(carDataDirectory + dataString.split("LUT_AOA_CD=")[1].split(";")[0])
            elif dataString.__contains__("LUT_GH_CD="):
                LUT_GH_CD = readLUTFile(carDataDirectory + dataString.split("LUT_GH_CD=")[1].split(";")[0])
            elif dataString.__contains__("CD_GAIN="):
                CD_GAIN = float(dataString.split("CD_GAIN=")[1].split(";")[0])
            elif dataString.__contains__("ANGLE="):
                ANGLE = float(dataString.split("ANGLE=")[1].split(";")[0])
            # If all the necessary data has been read for a Wing object to be initialised
            if CHORD is not None and SPAN is not None and POSITION is not None and LUT_AOA_CL is not None and LUT_GH_CL is not None and CL_GAIN is not None and LUT_AOA_CD is not None and LUT_GH_CD is not None and CD_GAIN is not None and ANGLE is not None:
                self.wings.append(Wing(CHORD, SPAN, POSITION, LUT_AOA_CL, LUT_GH_CL, CL_GAIN, LUT_AOA_CD, LUT_GH_CD, CD_GAIN, ANGLE))
                self.defaultWingAngles.append(ANGLE)
                CHORD, SPAN, POSITION, LUT_AOA_CL, LUT_GH_CL, CL_GAIN, LUT_AOA_CD, LUT_GH_CD, CD_GAIN, ANGLE = None, None, None, None, None, None, None, None, None, None
        aeroINIFile.close()

    def __str__(self):
        string = ""
        string += "           Car Name: " + self.carName + "\n"
        string += "PICKUP_FRONT_HEIGHT: " + str(self.PICKUP_FRONT_HEIGHT) + "\n"
        string += " PICKUP_REAR_HEIGHT: " + str(self.PICKUP_REAR_HEIGHT) + "\n"
        string += "          WHEELBASE: " + str(self.WHEELBASE) + "\n"
        string += "        CG_LOCATION: " + str(self.CG_LOCATION) + "\n"
        string += "Number of colliders: " + str(len(self.colliders)) + "\n"
        string += "    Number of wings: " + str(len(self.wings)) + "\n"
        string += "Default wing angles: " + str(self.defaultWingAngles) + "\n"

        currentWingAngles = []
        for wing in self.wings:
            currentWingAngles.append(wing.ANGLE)
        string += "Current wing angles: " + str(currentWingAngles)

        return string

    def setWingAngles(self, wingAngles):
        """Sets each wing to the angle specified by the wingAngles array passed in, where each index of the array
            corresponds to each wing (i.e. index 2 corresponds to wing 2)
            If a wing angle passed in is None, then it is left at the default angle specified in aero.ini"""
        if len(wingAngles) == len(self.wings):
            for i in range(len(wingAngles)):
                if wingAngles[i] is None:
                    self.wings[i].ANGLE = self.defaultWingAngles[i]
                else:
                    self.wings[i].ANGLE = float(wingAngles[i])
        else:
            raise Exception("wingAngles[] is not the same size as wings[]")

    def getWingAngles(self):
        """Returns an array of the wing angles of each wing"""
        wingAngles = []
        for wing in self.wings:
            wingAngles.append(wing.ANGLE)

        return wingAngles

    def isValidRideHeight(self, frontRH, rearRH, colliderMargin):
        """Returns True if the combination of frontRH and rearRH in metres is valid, otherwise returns False
            (Valid if lowest point of the collider > colliderMargin)
            All variables in SI units (i.e. metres)"""

        # Calculate CG heights and rake from front and rear ride heights
        frontCGHeight = frontRH - self.PICKUP_FRONT_HEIGHT
        rearCGHeight = rearRH - self.PICKUP_REAR_HEIGHT
        CGHeight = linearInterpolate(self.CG_LOCATION, 0, 1, frontCGHeight, rearCGHeight)
        rake = math.degrees(math.asin((rearCGHeight - frontCGHeight) / self.WHEELBASE))

        # Check if the ride heights are valid for the colliderMargin
        isValid = True
        for Collider in self.colliders:
            if not Collider.isValid(CGHeight, rake, colliderMargin):
                isValid = False

        return isValid

    def calculateAero(self, frontRH, rearRH):
        """Calculates aero for frontRH and rearRH in metres
            Returns (frontClA, rearClA, ClA, CdA, efficiency, aeroBalance)"""
        # Calculate CG heights and rake from front and rear ride heights
        frontCGHeight = frontRH - self.PICKUP_FRONT_HEIGHT
        rearCGHeight = rearRH - self.PICKUP_REAR_HEIGHT
        CGHeight = linearInterpolate(self.CG_LOCATION, 0, 1, frontCGHeight, rearCGHeight)
        rake = math.degrees(math.asin((rearCGHeight - frontCGHeight) / self.WHEELBASE))

        # Calculate aero
        totalClA = 0
        totalCdA = 0
        frontClA = 0
        for Wing in self.wings:
            wingClA, wingCdA, wingEffectiveFrontClA, wingEffectiveRearClA = Wing.calculateWing(self, CGHeight, rake)
            totalClA += wingClA
            totalCdA += wingCdA
            frontClA += wingEffectiveFrontClA
        rearClA = totalClA - frontClA
        efficiency = totalClA / totalCdA
        aeroBalance = (frontClA / totalClA) * 100

        return frontClA, rearClA, totalClA, totalCdA, efficiency, aeroBalance

    def getAeroMap(self, frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, colliderMargin):
        """Generates the aero map for the car in the form of 2D arrays - note that stuff like separate front ClA and
            rear ClA they can be calculated using ClA and aeroBalance, and it isn't considered useful, so arrays of that
            data are not returned

            Returns RHArray, frontClAArray2D, rearClAArray2D, ClAArray2D, CdAArray2D, efficiencyArray2D, aeroBalanceArray2D, isValid2D
            The 2D arrays are in the form array2D[RearRH][FrontRH] (rows as rear RH and columns as front RH)

            All units passed in and returned are SI units (i.e. metres), and aero balance is in % front aero balance"""

        RHArray = [[], []]  # in the form [[FrontRH], [RearRH]], and in metres

        # Rows are rear RH, columns are front RH, so it's array2D[RearRH][FrontRH]
        frontClAArray2D = []
        rearClAArray2D = []
        totalClAArray2D = []
        totalCdAArray2D = []
        efficiencyArray2D = []
        aeroBalanceArray2D = []
        isValid2D = []

        # Floating point maths reasons
        RHMargin = RHStep / 2

        # Generate front ride heights for RHArray
        frontRH = frontRHMin
        while frontRH <= frontRHMax + RHMargin:
            RHArray[0].append(frontRH)
            frontRH += RHStep
        # Generate rear ride heights for RHArray
        rearRH = rearRHMin
        while rearRH <= rearRHMax + RHMargin:
            RHArray[1].append(rearRH)
            rearRH += RHStep

        # Iterate through all ride heights and calculate aero
        rearRH = rearRHMin
        while rearRH <= rearRHMax + RHMargin:
            # Add a new row to the 2D array to represent a new rear RH
            frontClAArray2D.append([])
            rearClAArray2D.append([])
            totalClAArray2D.append([])
            totalCdAArray2D.append([])
            efficiencyArray2D.append([])
            aeroBalanceArray2D.append([])
            isValid2D.append([])

            frontRH = frontRHMin
            while frontRH <= frontRHMax + RHMargin:
                # Calculate aero
                frontClA, rearClA, totalClA, totalCdA, efficiency, aeroBalance = self.calculateAero(frontRH, rearRH)

                # Check if it's a valid ride height
                isValid = self.isValidRideHeight(frontRH, rearRH, colliderMargin)

                # Add the new values to the 2D arrays
                frontClAArray2D[-1].append(frontClA)
                rearClAArray2D[-1].append(rearClA)
                totalClAArray2D[-1].append(totalClA)
                totalCdAArray2D[-1].append(totalCdA)
                efficiencyArray2D[-1].append(efficiency)
                aeroBalanceArray2D[-1].append(aeroBalance)
                isValid2D[-1].append(isValid)

                frontRH += RHStep
            rearRH += RHStep

        return RHArray, frontClAArray2D, rearClAArray2D, totalClAArray2D, totalCdAArray2D, efficiencyArray2D, aeroBalanceArray2D, isValid2D

    def plotAeroMap(self, saveDirectory, fileName, RHArray, frontClAArray2D, rearClAArray2D, totalClAArray2D, totalCdAArray2D, efficiencyArray2D, aeroBalanceArray2D, isValid2D, RHEnvelope2D=None, boundsFrontClA=None, boundsRearClA=None, boundsTotalClA=None, boundsTotalCdA=None, boundsEfficiency=None, boundsAeroBalance=None):
        """Plots a figure with 6 subplots (front ClA, rear ClA, total ClA, total CdA, efficiency, aero balance), and
            saves it to saveDirectory as fileName

            If RHEnvelope2D is not None, then all points outside of those listed in RHEnvelope2D will be made
            semi-transparent

            If bounds is None, then the colour map is simply left to map from minimum to maximum of the data passed in
            If bounds isn't None, then it must be an array in the form [lowerBound, upperBound], and the colour map will
            be clipped to those bounds

            Still have no idea whether to include contours or not - and if so, whether to mix data sources for colours
            and contours (e.g. coloured efficiency but contours of aero balance)"""

        # Plot settings
        figDPI = 400
        plotArea = 80
        plotMarginX = 3.5
        colourBarSizeMult = 0.65
        colourMap = 'rainbow'     # magma, rainbow, gist_rainbow
        notRHEnvelopeAlpha = 0.3

        """figTitleFontSize = 12
        axisTitleFontSize = 10
        labelFontSize = 8
        tickFontSize = 7"""

        figTitleFontSize = 16
        axisTitleFontSize = 14
        labelFontSize = 12
        tickFontSize = 10

        contourPlotLineWidth = 0.1

        gridSpacingMinor = 5
        gridSpacingMajor = 20
        gridLineWidthMinor = 0.1
        gridLineWidthMajor = 0.2

        # Set figure DPI
        plt.rcParams['savefig.dpi'] = figDPI

        # Set font sizes
        plt.rc('axes', titlesize=axisTitleFontSize)  # fontsize of the axes title
        plt.rc('axes', labelsize=labelFontSize)  # fontsize of the x and y labels
        plt.rc('xtick', labelsize=tickFontSize)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=tickFontSize)  # fontsize of the tick labels
        plt.rc('figure', titlesize=figTitleFontSize)  # fontsize of the figure title

        # Create variables for the number of columns (number of front RHs) and the number of rows (number of rear RHs)
        numColumns = len(RHArray[0])
        numRows = len(RHArray[1])

        # Convert RHArray to be in mm
        RHArray[0] = [i * 1000 for i in RHArray[0]]
        RHArray[1] = [i * 1000 for i in RHArray[1]]

        # Get min and max ride heights for setting plot axis bounds
        frontRHMin = min(RHArray[0])
        frontRHMax = max(RHArray[0])
        rearRHMin = min(RHArray[1])
        rearRHMax = max(RHArray[1])

        # Create transparency (alpha) array for denoting the ride height envelope and whether the ride height is valid
        alphaArray2D = []
        for row in range(numRows):
            alphaArray2D.append([])
            for column in range(numColumns):
                if RHEnvelope2D is not None:
                    if RHEnvelope2D[row][column]:
                        alphaArray2D[row].append(1.0)
                    elif isValid2D[row][column]:
                            alphaArray2D[row].append(notRHEnvelopeAlpha)
                    else:
                        alphaArray2D[row].append(0.0)
                else:
                    if isValid2D[row][column]:
                        alphaArray2D[row].append(1.0)
                    else:
                        alphaArray2D[row].append(0.0)

        # For vmin and vmax to work properly in the colourmap plots
        if boundsFrontClA is None: boundsFrontClA = [None, None]
        if boundsRearClA is None: boundsRearClA = [None, None]
        if boundsTotalClA is None: boundsTotalClA = [None, None]
        if boundsTotalCdA is None: boundsTotalCdA = [None, None]
        if boundsEfficiency is None: boundsEfficiency = [None, None]
        if boundsAeroBalance is None: boundsAeroBalance = [None, None]

        # Set up figure and axes
        fig, axs = plt.subplots(2, 3, figsize=(plotArea ** 0.5 + plotMarginX, plotArea ** 0.5))
        fig.suptitle(self.carName + " " + fileName)
        majorTickArray = np.arange(round(min(frontRHMin, rearRHMin)), round(max(frontRHMax, rearRHMax)) + 1, gridSpacingMajor)
        minorTickArray = np.arange(round(min(frontRHMin, rearRHMin)), round(max(frontRHMax, rearRHMax)) + 1, gridSpacingMinor)
        for ax in axs.flat:
            ax.set(xlabel='Front ride height (mm)', ylabel='Rear ride height (mm)')
            ax.set_xticks(majorTickArray)
            ax.set_xticks(minorTickArray, minor=True)
            ax.set_yticks(majorTickArray)
            ax.set_yticks(minorTickArray, minor=True)
            ax.grid(which='minor', color='black', alpha=0.5, linewidth=gridLineWidthMinor)
            ax.grid(which='major', color='black', linewidth=gridLineWidthMajor)
            ax.set(xlim=(frontRHMin, frontRHMax), ylim=(rearRHMin, rearRHMax))
            ax.axis('scaled')

        axs[0, 0].set_title('Front ClA')
        axs[1, 0].set_title('Rear ClA')
        axs[0, 1].set_title('Total ClA')
        axs[1, 1].set_title('Total CdA')
        axs[0, 2].set_title('Efficiency (L/D Ratio)')
        axs[1, 2].set_title('Front Aero Balance %')

        # Colour map plots
        fig.colorbar(axs[0, 0].imshow(frontClAArray2D, extent=[frontRHMin, frontRHMax, rearRHMax, rearRHMin], vmin=boundsFrontClA[0], vmax=boundsRearClA[1], cmap=colourMap, alpha=alphaArray2D), orientation="vertical", shrink=colourBarSizeMult)
        fig.colorbar(axs[1, 0].imshow(rearClAArray2D, extent=[frontRHMin, frontRHMax, rearRHMax, rearRHMin], vmin=boundsRearClA[0], vmax=boundsRearClA[1], cmap=colourMap, alpha=alphaArray2D), orientation="vertical", shrink=colourBarSizeMult)
        fig.colorbar(axs[0, 1].imshow(totalClAArray2D, extent=[frontRHMin, frontRHMax, rearRHMax, rearRHMin], vmin=boundsTotalClA[0], vmax=boundsTotalClA[1], cmap=colourMap, alpha=alphaArray2D), orientation="vertical", shrink=colourBarSizeMult)
        fig.colorbar(axs[1, 1].imshow(totalCdAArray2D, extent=[frontRHMin, frontRHMax, rearRHMax, rearRHMin], vmin=boundsTotalCdA[0], vmax=boundsTotalCdA[1], cmap=colourMap, alpha=alphaArray2D), orientation="vertical", shrink=colourBarSizeMult)
        fig.colorbar(axs[0, 2].imshow(efficiencyArray2D, extent=[frontRHMin, frontRHMax, rearRHMax, rearRHMin], vmin=boundsEfficiency[0], vmax=boundsEfficiency[1], cmap=colourMap, alpha=alphaArray2D), orientation="vertical", shrink=colourBarSizeMult)
        fig.colorbar(axs[1, 2].imshow(aeroBalanceArray2D, extent=[frontRHMin, frontRHMax, rearRHMax, rearRHMin], vmin=boundsAeroBalance[0], vmax=boundsAeroBalance[1], cmap=colourMap, alpha=alphaArray2D), orientation="vertical", shrink=colourBarSizeMult)
        plt.tight_layout()

        # Contour lines (atm only for aero balance)
        totalClAContours = axs[0, 1].contour(RHArray[0], RHArray[1], totalClAArray2D, colors='black', levels=np.arange(0, 10 + 1, 0.1), linewidths=contourPlotLineWidth)
        axs[0, 1].clabel(totalClAContours, inline=True, fontsize=tickFontSize)

        totalCdAContours = axs[1, 1].contour(RHArray[0], RHArray[1], totalCdAArray2D, colors='black',levels=np.arange(0, 2 + 1, 0.01), linewidths=contourPlotLineWidth)
        axs[1, 1].clabel(totalCdAContours, inline=True, fontsize=tickFontSize)

        aeroBalanceContours = axs[1, 2].contour(RHArray[0], RHArray[1], aeroBalanceArray2D, colors='black', levels=np.arange(0, 100 + 1, 1), linewidths=contourPlotLineWidth)
        axs[1, 2].clabel(aeroBalanceContours, inline=True, fontsize=tickFontSize)

        efficiencyContours = axs[0, 2].contour(RHArray[0], RHArray[1], efficiencyArray2D, colors='black',levels=np.arange(0, 10 + 1, 0.1), linewidths=contourPlotLineWidth)
        axs[0, 2].clabel(efficiencyContours, inline=True, fontsize=tickFontSize)

        plt.savefig(saveDirectory + "\\" + fileName + ".png")

        plt.close()

    def plotAeroMaps(self, saveDirectory, frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, colliderMargin, wingAnglesArray, RHEnvelope2D=None, fileNames=None, boundsFrontClA=None, boundsRearClA=None, boundsTotalClA=None, boundsTotalCdA=None, boundsEfficiency=None, boundsAeroBalance=None):
        """Plots aero maps and saves them to saveDirectory

            fileNames is an array of names (as strings) that will be used as the plot file names (if it is None, then
            the wing angles will be used as names)

            If bounds are not passed, then they are set to the min and max values of all the aero maps calculated
            Note that in this case, the frontClA and rearClA plots will share the same bounds"""
        numMaps = len(wingAnglesArray)

        # Set up variables to get min and max values
        initMin = 999
        initMax = -999

        frontClAMin, frontClAMax = initMin, initMax
        rearClAMin, rearClAMax = initMin, initMax
        totalClAMin, totalClAMax = initMin, initMax
        totalCdAMin, totalCdAMax = initMin, initMax
        efficiencyMin, efficiencyMax = initMin, initMax
        aeroBalanceMin, aeroBalanceMax = initMin, initMax

        print("\nCalculating aero maps")

        RHMaps = []
        frontClAMaps = []
        rearClAMaps = []
        totalClAMaps = []
        totalCdAMaps = []
        efficiencyMaps = []
        aeroBalanceMaps = []
        isValidMaps = []
        for i in range(numMaps):
            self.setWingAngles(wingAnglesArray[i])

            # Get aero maps
            RHArray, frontClAArray2D, rearClAArray2D, totalClAArray2D, totalCdAArray2D, efficiencyArray2D, aeroBalanceArray2D, isValid2D = self.getAeroMap(frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, colliderMargin)

            # Append aero maps to their arrays
            RHMaps.append(RHArray)
            frontClAMaps.append(frontClAArray2D)
            rearClAMaps.append(rearClAArray2D)
            totalClAMaps.append(totalClAArray2D)
            totalCdAMaps.append(totalCdAArray2D)
            efficiencyMaps.append(efficiencyArray2D)
            aeroBalanceMaps.append(aeroBalanceArray2D)
            isValidMaps.append(isValid2D)

            # Update min values
            frontClAMin = min(np.min(frontClAArray2D), frontClAMin)
            rearClAMin = min(np.min(rearClAArray2D), rearClAMin)
            totalClAMin = min(np.min(totalClAArray2D), totalClAMin)
            totalCdAMin = min(np.min(totalCdAArray2D), totalCdAMin)
            efficiencyMin = min(np.min(efficiencyArray2D), efficiencyMin)
            aeroBalanceMin = min(np.min(aeroBalanceArray2D), aeroBalanceMin)

            # Update max values
            frontClAMax = max(np.max(frontClAArray2D), frontClAMax)
            rearClAMax = max(np.max(rearClAArray2D), rearClAMax)
            totalClAMax = max(np.max(totalClAArray2D), totalClAMax)
            totalCdAMax = max(np.max(totalCdAArray2D), totalCdAMax)
            efficiencyMax = max(np.max(efficiencyArray2D), efficiencyMax)
            aeroBalanceMax = max(np.max(aeroBalanceArray2D), aeroBalanceMax)

            print("Calculated", i + 1, "of", numMaps, wingAnglesArray[i])

        # Set the min and max values of frontClA and rearClA to the same thing
        frontClAMin = min(frontClAMin, rearClAMin)
        frontClAMax = max(frontClAMax, rearClAMax)
        rearClAMin = frontClAMin
        rearClAMax = frontClAMax

        # Check if bounds were specified - if not, set them to the min and max values of the aero maps
        if boundsFrontClA is None: boundsFrontClA = [frontClAMin, frontClAMax]
        if boundsRearClA is None: boundsRearClA = [rearClAMin, rearClAMax]
        if boundsTotalClA is None: boundsTotalClA = [totalClAMin, totalClAMax]
        if boundsTotalCdA is None: boundsTotalCdA = [totalCdAMin, totalCdAMax]
        if boundsEfficiency is None: boundsEfficiency = [efficiencyMin, efficiencyMax]
        if boundsAeroBalance is None: boundsAeroBalance = [aeroBalanceMin, aeroBalanceMax]

        # Plot aero maps
        print("\nPlotting aero maps")
        for i in range(len(wingAnglesArray)):
            if fileNames is not None:
                fileName = fileNames[i]
            else:
                fileName = str(wingAnglesArray[i])

            # If RHEnvelope2D is a 2D array of the ride height envelope
            if RHEnvelope2D is not None:
                if type(RHEnvelope2D[0][0]) is not list:
                    self.plotAeroMap(saveDirectory, fileName, RHMaps[i], frontClAMaps[i], rearClAMaps[i], totalClAMaps[i], totalCdAMaps[i], efficiencyMaps[i], aeroBalanceMaps[i], isValidMaps[i], RHEnvelope2D, boundsFrontClA, boundsRearClA, boundsTotalClA, boundsTotalCdA, boundsEfficiency, boundsAeroBalance)
                else:
                    # If RHEnvelope2D is an array containing the RHEnvelope2D arrays (where the index corresponds to the
                    # wing angle)
                    self.plotAeroMap(saveDirectory, fileName, RHMaps[i], frontClAMaps[i], rearClAMaps[i], totalClAMaps[i], totalCdAMaps[i], efficiencyMaps[i], aeroBalanceMaps[i], isValidMaps[i], RHEnvelope2D[i], boundsFrontClA, boundsRearClA, boundsTotalClA, boundsTotalCdA, boundsEfficiency, boundsAeroBalance)
            else:
                self.plotAeroMap(saveDirectory, fileName, RHMaps[i], frontClAMaps[i], rearClAMaps[i], totalClAMaps[i], totalCdAMaps[i], efficiencyMaps[i], aeroBalanceMaps[i], isValidMaps[i], RHEnvelope2D, boundsFrontClA, boundsRearClA, boundsTotalClA, boundsTotalCdA, boundsEfficiency, boundsAeroBalance)
            print("Plotted", i + 1, "of", numMaps)

    def calculateAeroRHTelem(self, velocityPower, frontRHTelem, rearRHTelem, groundSpeedTelem):
        """Returns frontClAWeightedAverage, rearClAWeightedAverage, totalClAWeightedAverage, totalCdAWeightedAverage, efficiencyWeightedAverage, aeroBalanceWeightedAverage

            Calculates the weighted average of aero numbers over the telemetry ride heights, where the weighting is
            speed^(velocity power)"""
        numTelemPoints = len(groundSpeedTelem)

        velocityWeightingSum = 0

        frontClAWeightedAverage = 0
        rearClAWeightedAverage = 0
        totalClAWeightedAverage = 0
        totalCdAWeightedAverage = 0
        efficiencyWeightedAverage = 0
        aeroBalanceWeightedAverage = 0

        # Calculate the weighted average of the aero numbers, for the telemetry passed in
        for i in range(numTelemPoints):
            velocityWeighting = pow(groundSpeedTelem[i], velocityPower)
            velocityWeightingSum += velocityWeighting

            frontClA, rearClA, totalClA, totalCdA, efficiency, aeroBalance = self.calculateAero(frontRHTelem[i], rearRHTelem[i])

            frontClAWeightedAverage += frontClA * velocityWeighting
            rearClAWeightedAverage += rearClA * velocityWeighting
            totalClAWeightedAverage += totalClA * velocityWeighting
            totalCdAWeightedAverage += totalCdA * velocityWeighting
            efficiencyWeightedAverage += efficiency * velocityWeighting
            aeroBalanceWeightedAverage += aeroBalance * velocityWeighting

        frontClAWeightedAverage /= velocityWeightingSum
        rearClAWeightedAverage /= velocityWeightingSum
        totalClAWeightedAverage /= velocityWeightingSum
        totalCdAWeightedAverage /= velocityWeightingSum
        efficiencyWeightedAverage /= velocityWeightingSum
        aeroBalanceWeightedAverage /= velocityWeightingSum

        return frontClAWeightedAverage, rearClAWeightedAverage, totalClAWeightedAverage, totalCdAWeightedAverage, efficiencyWeightedAverage, aeroBalanceWeightedAverage

    def optimiseAeroRHTelem(self, frontRHOffsetMin, frontRHOffsetMax, rearRHOffsetMin, rearRHOffsetMax, wingAnglesArray, aeroBalanceTarget, aeroBalanceTolerance, velocityPower, frontRHTelem, rearRHTelem, groundSpeedTelem):
        """Returns validSetups, maxTotalClASetup, minTotalCdASetup, maxEfficiencySetup

            Where the setups are in the form [frontRHOffset (metres), rearRHOffset (metres), wingAngles], and
            validSetups is an array containing all the valid setups (within the aero balance tolerances)

            RHOffsets in metres - defines how the optimiser is allowed to shift the ride height envelope

            Uses the ride height and ground speed telemetry arrays passed in to calculate aero numbers, as described in
            calculateAeroRHTelem()

            Prints out all valid setups"""
        minAllowedAeroBalance = aeroBalanceTarget - aeroBalanceTolerance
        maxAllowedAeroBalance = aeroBalanceTarget + aeroBalanceTolerance

        RHOffsetStep = 0.001                # RH increments of 1mm
        RHOffsetMargin = RHOffsetStep / 2   # Floating point maths reasons

        # Performances of best setups
        maxTotalClA = -999
        minTotalCdA = 999
        maxEfficiency = -999

        # Setups with the best performances in the form [frontRHOffset, rearRHOffset, wingAngles] (RHOffsets in metres)
        baselineSetup = [0, 0, self.defaultWingAngles]
        maxTotalClASetup = baselineSetup
        minTotalCdASetup = baselineSetup
        maxEfficiencySetup = baselineSetup

        validSetups = []    # Will contain all valid setups (see above for the form)

        print("Total setup combinations:", len(wingAnglesArray) * (round((frontRHOffsetMax - frontRHOffsetMin) / RHOffsetStep) + 1) * (round((rearRHOffsetMax - rearRHOffsetMin) / RHOffsetStep) + 1))
        print("Valid setups:")
        # Iterate through all wing angle combinations
        for wingAngles in wingAnglesArray:
            self.setWingAngles(wingAngles)

            # Iterate through all rear ride height offsets
            rearRHOffset = rearRHOffsetMin
            while rearRHOffset <= rearRHOffsetMax + RHOffsetMargin:
                # Iterate through all front ride height offsets
                frontRHOffset = frontRHOffsetMin
                while frontRHOffset <= frontRHOffsetMax + RHOffsetMargin:
                    setup = [frontRHOffset, rearRHOffset, wingAngles]
                    #print("\tWing angles:", wingAngles, "  \tRH offsets [F, R] (mm):", [round(frontRHOffset * 1000), round(rearRHOffset * 1000)])

                    # Get the weighted average of the aero numbers, for the telemetry passed in - accounting for the RH
                    # offsets
                    frontRHTelemAdjusted = [frontRH + frontRHOffset for frontRH in frontRHTelem]
                    rearRHTelemAdjusted = [rearRH + rearRHOffset for rearRH in rearRHTelem]
                    frontClAWeightedAverage, rearClAWeightedAverage, totalClAWeightedAverage, totalCdAWeightedAverage, efficiencyWeightedAverage, aeroBalanceWeightedAverage = self.calculateAeroRHTelem(velocityPower, frontRHTelemAdjusted, rearRHTelemAdjusted, groundSpeedTelem)

                    # Check if the aero balance weighted average is within tolerances
                    if minAllowedAeroBalance <= aeroBalanceWeightedAverage <= maxAllowedAeroBalance:
                        # If aero balance is within tolerances, print the setup and its numbers
                        #print("\tWing angles:", wingAngles, "  \tRH offsets [F, R] (mm):", [round(frontRHOffset * 1000), round(rearRHOffset * 1000)], "\t\tClA:", round(totalClAWeightedAverage, 3), "\tCdA:", round(totalCdAWeightedAverage, 3), "\tEfficiency:", round(efficiencyWeightedAverage, 3), "\tAero balance %:", round(aeroBalanceWeightedAverage, 3))
                        print(str(wingAngles[0]) + "," + str(wingAngles[1]) + "," + str(round(frontRHOffset * 1000)) + "," + str(round(rearRHOffset * 1000)) + "," + str(frontClAWeightedAverage) + "," + str(rearClAWeightedAverage) + "," + str(totalClAWeightedAverage) + "," + str(totalCdAWeightedAverage) + "," + str(efficiencyWeightedAverage) + "," + str(aeroBalanceWeightedAverage))

                        # Add the setup to validSetups
                        validSetups.append(setup)

                        # Update best performing aero numbers and setups
                        if totalClAWeightedAverage > maxTotalClA:
                            maxTotalClA = totalClAWeightedAverage
                            maxTotalClASetup = setup
                        if totalCdAWeightedAverage < minTotalCdA:
                            minTotalCdA = totalCdAWeightedAverage
                            minTotalCdASetup = setup
                        if efficiencyWeightedAverage > maxEfficiency:
                            maxEfficiency = efficiencyWeightedAverage
                            maxEfficiencySetup = setup
                    frontRHOffset += RHOffsetStep
                rearRHOffset += RHOffsetStep

        # Print stats for the max total ClA setup
        self.setWingAngles(maxTotalClASetup[2])
        frontRHTelemAdjusted = [frontRH + maxTotalClASetup[0] for frontRH in frontRHTelem]
        rearRHTelemAdjusted = [rearRH + maxTotalClASetup[1] for rearRH in rearRHTelem]
        frontClAWeightedAverage, rearClAWeightedAverage, totalClAWeightedAverage, totalCdAWeightedAverage, efficiencyWeightedAverage, aeroBalanceWeightedAverage = self.calculateAeroRHTelem(velocityPower, frontRHTelemAdjusted, rearRHTelemAdjusted, groundSpeedTelem)
        print("\nMax total ClA:", "\n\tWing angles:", maxTotalClASetup[2], "\n\tRH offsets [F, R] (mm):",
              [round(maxTotalClASetup[0] * 1000), round(maxTotalClASetup[1] * 1000)], "\n\tClA:",
              round(totalClAWeightedAverage, 3), "\n\tCdA:", round(totalCdAWeightedAverage, 3), "\n\tEfficiency:",
              round(efficiencyWeightedAverage, 3), "\n\tAero balance %:", round(aeroBalanceWeightedAverage, 3))

        # Print stats for the min total CdA setup
        self.setWingAngles(minTotalCdASetup[2])
        frontRHTelemAdjusted = [frontRH + minTotalCdASetup[0] for frontRH in frontRHTelem]
        rearRHTelemAdjusted = [rearRH + minTotalCdASetup[1] for rearRH in rearRHTelem]
        frontClAWeightedAverage, rearClAWeightedAverage, totalClAWeightedAverage, totalCdAWeightedAverage, efficiencyWeightedAverage, aeroBalanceWeightedAverage = self.calculateAeroRHTelem(
            velocityPower, frontRHTelemAdjusted, rearRHTelemAdjusted, groundSpeedTelem)
        print("\nMin total CdA:", "\n\tWing angles:", minTotalCdASetup[2], "\n\tRH offsets [F, R] (mm):",
              [round(minTotalCdASetup[0] * 1000), round(minTotalCdASetup[1] * 1000)], "\n\tClA:",
              round(totalClAWeightedAverage, 3), "\n\tCdA:", round(totalCdAWeightedAverage, 3), "\n\tEfficiency:",
              round(efficiencyWeightedAverage, 3), "\n\tAero balance %:", round(aeroBalanceWeightedAverage, 3))

        # Print stats for the max efficiency setup
        self.setWingAngles(maxEfficiencySetup[2])
        frontRHTelemAdjusted = [frontRH + maxEfficiencySetup[0] for frontRH in frontRHTelem]
        rearRHTelemAdjusted = [rearRH + maxEfficiencySetup[1] for rearRH in rearRHTelem]
        frontClAWeightedAverage, rearClAWeightedAverage, totalClAWeightedAverage, totalCdAWeightedAverage, efficiencyWeightedAverage, aeroBalanceWeightedAverage = self.calculateAeroRHTelem(
            velocityPower, frontRHTelemAdjusted, rearRHTelemAdjusted, groundSpeedTelem)
        print("\nMax efficiency:", "\n\tWing angles:", maxEfficiencySetup[2], "\n\tRH offsets [F, R] (mm):",
              [round(maxEfficiencySetup[0] * 1000), round(maxEfficiencySetup[1] * 1000)], "\n\tClA:",
              round(totalClAWeightedAverage, 3), "\n\tCdA:", round(totalCdAWeightedAverage, 3), "\n\tEfficiency:",
              round(efficiencyWeightedAverage, 3), "\n\tAero balance %:", round(aeroBalanceWeightedAverage, 3))

        return validSetups, maxTotalClASetup, minTotalCdASetup, maxEfficiencySetup

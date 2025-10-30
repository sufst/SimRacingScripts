"""
Generates aero map plots for all wing combinations in wingAnglesArray, with a smoothed telemetry RH envelope overlay
"""

import math
from car import Car, getRHEnvelope2D

"""INPUTS"""
carName = "rss_formula_americas_2020_oval"
carsDirectory = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\content\\cars"

telemFileName = "indy race.csv"
telemDirectory = "C:\\Users\\Willow\\Downloads"

smoothingPoints = 2         # Set to 0 to disable smoothing, set to 2 to use 5 points for the moving average
telemDataFiltering = "all"  # Currently only options are "all" or "cornering"
is2WD = True

RHMin = 0.001 * 0
RHMax = 0.001 * 100

RHStep = 0.001 * 1
colliderMargin = 0

wingAnglesArray = [[1, 1, 0.186, 0.186, 0.186, 0.186, 0.186, 0.186, 0.186, 0]]
"""END OF INPUTS"""


def smooth(telemArray, smoothingPoints):
    """Returns an array containing the moving average (of smoothingPoints * 2 + 1 points) of telemArray, where the first
        smoothingPoints elements are simply the first moving average data point repeated, and similar for the last
        smoothingPoints elements"""
    # Generate array of the moving average of telemArray
    smoothedTelemArray = []
    for index in range(smoothingPoints, len(telemArray) - smoothingPoints):
        movingSum = telemArray[index]
        for i in range(smoothingPoints):
            movingSum += telemArray[index - i - 1] + telemArray[index + i + 1]
        smoothedTelemArray.append(movingSum / (smoothingPoints * 2 + 1))
    # Repeat the first moving average data point and last moving average data point until smoothedTelemArray is the same
    # length as the original telem array
    for i in range(smoothingPoints):
        smoothedTelemArray.insert(0, smoothedTelemArray[0])
        smoothedTelemArray.insert(-1, smoothedTelemArray[-1])
    return smoothedTelemArray


car = Car(carsDirectory, carName)
print(car)
print()

groundSpeedTelem = []   # in km/h
frontRHTelem = []       # in metres
rearRHTelem = []        # in metres
longGTelem = []         # in G
combinedGTelem = []     # in G
combinedG2WDTelem = []  # in G, multiplies longitudinal G by 2 if it's positive (accelerating)

# Read raw telemetry data
channelNameLine = 14
channelUnitsLine = 15
dataLineStart = 18
csvFile = open(telemDirectory + "\\" + telemFileName, "r")
lineCounter = 1
rawDataPoints = 0
for line in csvFile:
    data = line.replace("\n", "").replace("\"", "")

    if lineCounter >= dataLineStart:
        data = [float(i) for i in data.split(",")]
        rawDataPoints += 1
        # Ground speed
        groundSpeedTelem.append(data[63])
        # Ride heights
        frontRHTelem.append((data[90] + data[91]) / 2 / 1000)
        rearRHTelem.append((data[92] + data[93]) / 2 / 1000)
        # Longitudinal G
        longGTelem.append(data[23])
        # Combined G
        combinedGTelem.append(math.sqrt(pow(data[22], 2) + pow(data[23], 2)))
        # Combined G 2WD
        if data[23] > 0:
            combinedG2WDTelem.append(math.sqrt(pow(data[22], 2) + pow(data[23] * 2, 2)))
        else:
            combinedG2WDTelem.append(math.sqrt(pow(data[22], 2) + pow(data[23], 2)))
    lineCounter += 1
csvFile.close()

smoothedFrontRHTelem = smooth(frontRHTelem, smoothingPoints)
smoothedRearRHTelem = smooth(rearRHTelem, smoothingPoints)
smoothedLongGTelem = smooth(longGTelem, smoothingPoints)
smoothedCombinedGTelem = smooth(combinedGTelem, smoothingPoints)
smoothedCombinedG2WDTelem = smooth(combinedG2WDTelem, smoothingPoints)

# Filtering for cornering but not braking
processedGroundSpeedTelem = []
processedFrontRHTelem = []
processedRearRHTelem = []
processedCombinedG2WDTelem = []
for i in range(rawDataPoints):
    if telemDataFiltering == "all":
        processedFrontRHTelem.append(smoothedFrontRHTelem[i])
        processedRearRHTelem.append(smoothedRearRHTelem[i])
    elif telemDataFiltering == "cornering":
        if is2WD:
            if smoothedCombinedG2WDTelem[i] > 1 and abs(smoothedLongGTelem[i]) < 0.25 * smoothedCombinedG2WDTelem[i]:
                processedFrontRHTelem.append(smoothedFrontRHTelem[i])
                processedRearRHTelem.append(smoothedRearRHTelem[i])
        else:
            if smoothedCombinedGTelem[i] > 1 and abs(smoothedLongGTelem[i]) < 0.25 * smoothedCombinedGTelem[i]:
                processedFrontRHTelem.append(smoothedFrontRHTelem[i])
                processedRearRHTelem.append(smoothedRearRHTelem[i])

RHEnvelope2D = getRHEnvelope2D(RHMin, RHMax, RHMin, RHMax, RHStep, processedFrontRHTelem, processedRearRHTelem)
car.plotAeroMaps("plots", RHMin, RHMax, RHMin, RHMax, RHStep, colliderMargin, wingAnglesArray, RHEnvelope2D)

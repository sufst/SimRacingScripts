import math

directory = "C:\\Users\\Willow\\Downloads"
fileName = "911 gt1 silvo.csv"  # Select the range in MoTeC, then export visible data as CSV
                                         # (don't include maths channels)


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


groundSpeedTelem = []  # in km/h
frontRHTelem = []  # in metres
rearRHTelem = []  # in metres
longGTelem = []  # in G
combinedG2WDTelem = []  # in G, multiplies longitudinal G by 2 if it's positive (accelerating)

# Read raw telemetry data
channelNameLine = 14
channelUnitsLine = 15
dataLineStart = 18
csvFile = open(directory + "\\" + fileName, "r")
lineCounter = 1
rawDataPoints = 0
for line in csvFile:
    data = line.replace("\n", "").replace("\"", "")

    if lineCounter >= dataLineStart:
        data = [float(i) for i in data.split(",")]
        rawDataPoints += 1
        """
        To get channel indexes:
            if lineCounter == channelNameLine:
                data = data.split(",")
                for i in range(len(data)):
                    print(i, data[i])

        Indexes for the important telemetry channels:
        16 Brake Bias
        17 Brake Pos
        22 CG Accel Lateral
        23 CG Accel Longitudinal
        24 CG Accel Vertical
        62 Gear
        63 Ground Speed
        90 Ride Height FL
        91 Ride Height FR
        92 Ride Height RL
        93 Ride Height RR
        101 Steering Angle
        103 Suspension Travel FL
        104 Suspension Travel FR
        105 Suspension Travel RL
        106 Suspension Travel RR
        109 Throttle Pos
        114 Tire Load FL
        115 Tire Load FR
        116 Tire Load RL
        117 Tire Load RR
        """
        # Ground speed
        groundSpeedTelem.append(data[63])
        # Ride heights
        frontRHTelem.append((data[90] + data[91]) / 2 / 1000)
        rearRHTelem.append((data[92] + data[93]) / 2 / 1000)
        # Longitudinal G
        longGTelem.append(data[23])
        # Combined G 2WD
        if data[23] > 0:
            combinedG2WDTelem.append(math.sqrt(pow(data[22], 2) + pow(data[23] * 2, 2)))
        else:
            combinedG2WDTelem.append(math.sqrt(pow(data[22], 2) + pow(data[23], 2)))
    lineCounter += 1
csvFile.close()

# Smooth telemetry channels
smoothingPoints = 2

smoothedFrontRHTelem = smooth(frontRHTelem, smoothingPoints)
smoothedRearRHTelem = smooth(rearRHTelem, smoothingPoints)
smoothedLongGTelem = smooth(longGTelem, smoothingPoints)
smoothedCombinedG2WDTelem = smooth(combinedG2WDTelem, smoothingPoints)

# Filtering for cornering but not braking
processedGroundSpeedTelem = []
processedFrontRHTelem = []
processedRearRHTelem = []
processedCombinedG2WDTelem = []
for i in range(rawDataPoints):
    if True:#smoothedCombinedG2WDTelem[i] > 1.5 and abs(smoothedLongGTelem[i]) < 0.5 * smoothedCombinedG2WDTelem[i]:
        processedGroundSpeedTelem.append(groundSpeedTelem[i])
        processedFrontRHTelem.append(smoothedFrontRHTelem[i])
        processedRearRHTelem.append(smoothedRearRHTelem[i])
        processedCombinedG2WDTelem.append(smoothedCombinedG2WDTelem[i])

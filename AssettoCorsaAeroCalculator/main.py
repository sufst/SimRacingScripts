from car import Car, getRHEnvelope2D
import processingMoTeCData

"""
GT3 Cars:
    - ks_porsche_911_gt3_r_2016
    - ks_mclaren_650_gt3
"""
carName = "ks_porsche_911_gt1"
carsDirectory = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\content\\cars"

car = Car(carsDirectory, carName)
print(car)
print()

frontRHMin = 0.001 * 0
frontRHMax = 0.001 * 100
rearRHMin = 0.001 * 0
rearRHMax = 0.001 * 100

RHStep = 0.001 * 1
colliderMargin = 0

RHArray, frontClAArray2D, rearClAArray2D, totalClAArray2D, totalCdAArray2D, efficiencyArray2D, aeroBalanceArray2D, isValid2D = car.getAeroMap(frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, colliderMargin)

# Generate all combinations of wing angles
"""wingAnglesArray = []
for RW in range(0, 1 + 8):        # RW from 0 to 8
    wingAnglesArray.append([0, 2, RW, 11])"""

# If you don't want to wait forever for the aero to be optimised for ride heights, change these to arrays with only a
# few elements
frontRHTelem = processingMoTeCData.processedFrontRHTelem
rearRHTelem = processingMoTeCData.processedRearRHTelem
groundSpeedTelem = processingMoTeCData.processedGroundSpeedTelem

wingAnglesArray = [[0, 2, 6, 1]]
RHEnvelope2D = getRHEnvelope2D(frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, frontRHTelem, rearRHTelem)
#RHEnvelope2D = None

car.plotAeroMaps("plots", frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, colliderMargin, wingAnglesArray, RHEnvelope2D)
exit()

optimisationStart = time.time()

aeroBalanceTarget = 43.2
aeroBalanceTolerance = 0.5

velocityPower = 1

frontRHOffsetMin = 0.001 * 0    # -1, From baseline (but telem is min RH all round)
frontRHOffsetMax = 0.001 * 2    # 7
rearRHOffsetMin = 0.001 * 0    # -4
rearRHOffsetMax = 0.001 * 2    # 4

"""frontRHOffsetMin = 0.001 * 0 # No ride height adjustment
frontRHOffsetMax = 0.001 * 0
rearRHOffsetMin = 0.001 * 0
rearRHOffsetMax = 0.001 * 0"""

validSetups, maxTotalClASetup, minTotalCdASetup, maxEfficiencySetup = car.optimiseAeroRHTelem(frontRHOffsetMin, frontRHOffsetMax, rearRHOffsetMin, rearRHOffsetMax, wingAnglesArray, aeroBalanceTarget, aeroBalanceTolerance, velocityPower, frontRHTelem, rearRHTelem, groundSpeedTelem)

print("\nOptimisation time (s):", round(time.time() - optimisationStart, 3))

wingAnglesArray = []
RHEnvelope2D = []
fileNames = []
print("\nValid setups:")
for setup in validSetups:
    print("Wing angles:", setup[2], "\t\tFront RH offset (mm):", round(setup[0] * 1000), "\tRear RH offset(mm)", round(setup[1] * 1000))
    wingAnglesArray.append(setup[2])

    RHEnvelope2D.append(getRHEnvelope2D(frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, [frontRH + setup[0] for frontRH in frontRHTelem], [rearRH + setup[1] for rearRH in rearRHTelem]))
    fileNames.append("FW-RW " + str(setup[2][1]) + "-" + str(setup[2][2]) + "  F Offset " + str(round(setup[0] * 1000)) + "  R Offset " + str(round(setup[1] * 1000)))

# Generate the ride height envelope and plot aero maps for only the valid wing angle combinations
#car.plotAeroMaps("plots", frontRHMin, frontRHMax, rearRHMin, rearRHMax, RHStep, colliderMargin, wingAnglesArray, RHEnvelope2D, fileNames)

print()
print("Valid setups:")
for setup in validSetups:
    print(str(setup) + ",")

"""Car data, grip functions"""
import math

telemFileName = "indy 1.3.1b.csv"
telemDirectory = "C:\\Users\\Willow\\Downloads"

"""Lateral G must be above this threshold to be considered in the telem analysis for the axle grip"""
latGThreshold = 1

"""Load sensitivity tyre data - Note that this only considers lateral grip"""
front_FZ0 = 2500
front_LS_EXPY = 0.7285
front_DY_REF = 1.7910774

rear_FZ0 = 2500
rear_LS_EXPY = 0.775
rear_DY_REF = 1.8522

"""Camber tyre data"""
front_DCAMBER_0 = 1.14591559026165
front_DCAMBER_1 = -8.20701587502936

rear_DCAMBER_0 = 1.14591559026165
rear_DCAMBER_1 = -8.20701587502936


"""Tyre grip function"""
def tyreLatD(Fz, camberDeg, FZ0, LS_EXPY, DY_REF, DCAMBER_0, DCAMBER_1):
    # If the tyre load is 0 (or less than 0), simply return 0 (the force is going to be 0 anyway)
    if Fz <= 0:
        return 0
    else:
        # Converts camber to radians
        camberRad = camberDeg * math.pi / 180
        # D from tyre load sensitivity
        D = DY_REF * pow(Fz, LS_EXPY - 1) * pow(FZ0, 1 - LS_EXPY)

        # Multiplies D by the camber multiplier
        D /= 1 + (DCAMBER_0 * camberRad) - (DCAMBER_1 * pow(camberRad, 2))

        return D


"""Telem analysis axle grip functions"""
def frontAxleAvgLatD(latG, FL_Fz, FL_camberDeg, FR_Fz, FR_camberDeg):
    frontAxleLatDArray = []
    for i in range(len(latG)):
        # Checks if it's a left or right corner
        if latG[i] > 0:
            # Left corner, FL camber is opposite
            FL_latD = tyreLatD(FL_Fz[i], -FL_camberDeg[i], front_FZ0, front_LS_EXPY, front_DY_REF, front_DCAMBER_0, front_DCAMBER_1)
            FR_latD = tyreLatD(FR_Fz[i], FR_camberDeg[i], front_FZ0, front_LS_EXPY, front_DY_REF, front_DCAMBER_0, front_DCAMBER_1)
        else:
            # Right corner, FR camber is opposite
            FL_latD = tyreLatD(FL_Fz[i], FL_camberDeg[i], front_FZ0, front_LS_EXPY, front_DY_REF, front_DCAMBER_0, front_DCAMBER_1)
            FR_latD = tyreLatD(FR_Fz[i], -FR_camberDeg[i], front_FZ0, front_LS_EXPY, front_DY_REF, front_DCAMBER_0, front_DCAMBER_1)

        # If the total tyre load is 0 (or less than 0), simply append 0 (the force is going to be 0 anyway)
        if FL_Fz[i] + FR_Fz[i] <= 0:
            frontAxleLatDArray.append(0)
        else:
            frontAxleLatDArray.append((FL_Fz[i] * FL_latD + FR_Fz[i] * FR_latD) / (FL_Fz[i] + FR_Fz[i]))

    frontAxleAvgLatD = sum(frontAxleLatDArray) / len(frontAxleLatDArray)

    return frontAxleAvgLatD


def rearAxleAvgLatD(latG, RL_Fz, RL_camberDeg, RR_Fz, RR_camberDeg):
    rearAxleLatDArray = []
    for i in range(len(latG)):
        # Checks if it's a left or right corner
        if latG[i] > 0:
            # Left corner, FL camber is opposite
            RL_latD = tyreLatD(RL_Fz[i], -RL_camberDeg[i], rear_FZ0, rear_LS_EXPY, rear_DY_REF, rear_DCAMBER_0, rear_DCAMBER_1)
            RR_latD = tyreLatD(RR_Fz[i], RR_camberDeg[i], rear_FZ0, rear_LS_EXPY, rear_DY_REF, rear_DCAMBER_0, rear_DCAMBER_1)
        else:
            # Right corner, FR camber is opposite
            RL_latD = tyreLatD(RL_Fz[i], RL_camberDeg[i], rear_FZ0, rear_LS_EXPY, rear_DY_REF, rear_DCAMBER_0, rear_DCAMBER_1)
            RR_latD = tyreLatD(RR_Fz[i], -RR_camberDeg[i], rear_FZ0, rear_LS_EXPY, rear_DY_REF, rear_DCAMBER_0, rear_DCAMBER_1)

        # If the total tyre load is 0 (or less than 0), simply append 0 (the force is going to be 0 anyway)
        if RL_Fz[i] + RR_Fz[i] <= 0:
            rearAxleLatDArray.append(0)
        else:
            rearAxleLatDArray.append((RL_Fz[i] * RL_latD + RR_Fz[i] * RR_latD) / (RL_Fz[i] + RR_Fz[i]))

    rearAxleAvgLatD = sum(rearAxleLatDArray) / len(rearAxleLatDArray)

    return rearAxleAvgLatD


"""READING TELEM"""
# Channels
latGTelem = []
FL_tyreLoad = []
FR_tyreLoad = []
RL_tyreLoad = []
RR_tyreLoad = []
FL_camberDeg = []
FR_camberDeg = []
RL_camberDeg = []
RR_camberDeg = []

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

        # Filtering for lateral G threshold
        if abs(data[22]) >= latGThreshold:
            latGTelem.append(data[22])
            FL_tyreLoad.append(data[114])
            FR_tyreLoad.append(data[115])
            RL_tyreLoad.append(data[116])
            RR_tyreLoad.append(data[117])
            FL_camberDeg.append(data[26])
            FR_camberDeg.append(data[27])
            RL_camberDeg.append(data[28])
            RR_camberDeg.append(data[29])
    lineCounter += 1
csvFile.close()

# Channel indexes
"""
0 ABS Active
1 ABS Enabled
2 AID Allow Tire Blankets
3 AID Auto Blip
4 AID Auto Clutch
5 AID Auto Shift
6 AID Fuel Rate
7 AID Ideal Line
8 AID Mech Damage
9 AID Stability
10 AID Tire Wear Rate
11 Air Density
12 Air Temp
13 Ballast
14 Best Lap Delta
15 Best Lap Time
16 Brake Bias
17 Brake Pos
18 Brake Temp FL
19 Brake Temp FR
20 Brake Temp RL
21 Brake Temp RR
22 CG Accel Lateral
23 CG Accel Longitudinal
24 CG Accel Vertical
25 CG Height
26 Camber FL
27 Camber FR
28 Camber RL
29 Camber RR
30 Car Coord X
31 Car Coord Y
32 Car Coord Z
33 Car Damage Front
34 Car Damage Left
35 Car Damage Rear
36 Car Damage Right
37 Car Pos Norm
38 Caster FL
39 Caster FR
40 Chassis Pitch Angle
41 Chassis Pitch Rate
42 Chassis Roll Angle
43 Chassis Roll Rate
44 Chassis Velocity X
45 Chassis Velocity Y
46 Chassis Velocity Z
47 Chassis Yaw Rate
48 Clutch Pos
49 DRS Active
50 DRS Available
51 Drive Train Speed
52 ERS Heat Charging
53 ERS Is Charging
54 ERS Max Energy
55 ERS Power Level
56 ERS Recovery Level
57 Engine Brake Setting
58 Engine Limiter
59 Engine RPM
60 Flags
61 Fuel Level
62 Gear
63 Ground Speed
64 HR Sample Clock
65 In Pit
66 KERS Charge
67 KERS Deployed Energy
68 KERS Input
69 KERS Max Energy
70 LR Sample Clock
71 Lap Invalidated
72 Lap Time
73 Lap Time2
74 Last Lap Time
75 Last Sector Time
76 MR Sample Clock
77 Max Fuel
78 Max Power
79 Max RPM
80 Max Sus Travel FL
81 Max Sus Travel FR
82 Max Sus Travel RL
83 Max Sus Travel RR
84 Max Torque
85 Max Turbo Boost
86 Num Tires Off Track
87 Penalties Enabled
88 Position
89 Raw Data Sample Rate
90 Ride Height FL
91 Ride Height FR
92 Ride Height RL
93 Ride Height RR
94 Road Temp
95 Self Align Torque FL
96 Self Align Torque FR
97 Self Align Torque RL
98 Self Align Torque RR
99 Session Lap Count
100 Session Time Left
101 Steering Angle
102 Surface Grip
103 Suspension Travel FL
104 Suspension Travel FR
105 Suspension Travel RL
106 Suspension Travel RR
107 TC Active
108 TC Enabled
109 Throttle Pos
110 Tire Dirt Level FL
111 Tire Dirt Level FR
112 Tire Dirt Level RL
113 Tire Dirt Level RR
114 Tire Load FL
115 Tire Load FR
116 Tire Load RL
117 Tire Load RR
118 Tire Loaded Radius FL
119 Tire Loaded Radius FR
120 Tire Loaded Radius RL
121 Tire Loaded Radius RR
122 Tire Pressure FL
123 Tire Pressure FR
124 Tire Pressure RL
125 Tire Pressure RR
126 Tire Radius FL
127 Tire Radius FR
128 Tire Radius RL
129 Tire Radius RR
130 Tire Rubber Grip FL
131 Tire Rubber Grip FR
132 Tire Rubber Grip RL
133 Tire Rubber Grip RR
134 Tire Slip Angle FL
135 Tire Slip Angle FR
136 Tire Slip Angle RL
137 Tire Slip Angle RR
138 Tire Slip Ratio FL
139 Tire Slip Ratio FR
140 Tire Slip Ratio RL
141 Tire Slip Ratio RR
142 Tire Temp Core FL
143 Tire Temp Core FR
144 Tire Temp Core RL
145 Tire Temp Core RR
146 Tire Temp Inner FL
147 Tire Temp Inner FR
148 Tire Temp Inner RL
149 Tire Temp Inner RR
150 Tire Temp Middle FL
151 Tire Temp Middle FR
152 Tire Temp Middle RL
153 Tire Temp Middle RR
154 Tire Temp Outer FL
155 Tire Temp Outer FR
156 Tire Temp Outer RL
157 Tire Temp Outer RR
158 Toe In FL
159 Toe In FR
160 Toe In RL
161 Toe In RR
162 Turbo Boost
163 Wheel Angular Speed FL
164 Wheel Angular Speed FR
165 Wheel Angular Speed RL
166 Wheel Angular Speed RR
167 Wind Direction
168 Wind Speed
"""

originalFrontAxleAvgLatD = frontAxleAvgLatD(latGTelem, FL_tyreLoad, FL_camberDeg, FR_tyreLoad, FR_camberDeg)
originalRearAxleAvgLatD = rearAxleAvgLatD(latGTelem, RL_tyreLoad, RL_camberDeg, RR_tyreLoad, RR_camberDeg)
print("Original front axle avg lat D:", originalFrontAxleAvgLatD)
print(" Original rear axle avg lat D:", originalRearAxleAvgLatD)

front_bestCamberOffset = 0
front_bestAvgLatD = 0
rear_bestCamberOffset = 0
rear_bestAvgLatD = 0

camberOffsetMin = -5
camberOffsetMax = 5
camberOffsetStep = 0.1

camberOffset = camberOffsetMin
while camberOffset < camberOffsetMax + camberOffsetStep:
    # Offsetting the camber telemetry arrays
    FL_camberDegTrial = [i + camberOffset for i in FL_camberDeg]
    FR_camberDegTrial = [i + camberOffset for i in FR_camberDeg]
    RL_camberDegTrial = [i + camberOffset for i in RL_camberDeg]
    RR_camberDegTrial = [i + camberOffset for i in RR_camberDeg]

    # Calculate axle average lateral D for the camber offset
    frontAxleAvgLatDTrial = frontAxleAvgLatD(latGTelem, FL_tyreLoad, FL_camberDegTrial, FR_tyreLoad, FR_camberDegTrial)
    rearAxleAvgLatDTrial = rearAxleAvgLatD(latGTelem, RL_tyreLoad, RL_camberDegTrial, RR_tyreLoad, RR_camberDegTrial)

    # Update best camber offset and best average lateral D
    if frontAxleAvgLatDTrial > front_bestAvgLatD:
        front_bestCamberOffset = camberOffset
        front_bestAvgLatD = frontAxleAvgLatDTrial
    if rearAxleAvgLatDTrial > rear_bestAvgLatD:
        rear_bestCamberOffset = camberOffset
        rear_bestAvgLatD = rearAxleAvgLatDTrial

    camberOffset = round(camberOffset + camberOffsetStep, 1)


originalFrontAxleAvgLatD = frontAxleAvgLatD(latGTelem, FL_tyreLoad, FL_camberDeg, FR_tyreLoad, FR_camberDeg)
originalRearAxleAvgLatD = rearAxleAvgLatD(latGTelem, RL_tyreLoad, RL_camberDeg, RR_tyreLoad, RR_camberDeg)
print("\nOptimum front camber offset (deg):", front_bestCamberOffset)
print("             Grip improvement (%):", round((front_bestAvgLatD - originalFrontAxleAvgLatD) / originalFrontAxleAvgLatD * 100, 3))
print()
print("Optimum rear camber offset (deg):", rear_bestCamberOffset)
print("            Grip improvement (%):", round((rear_bestAvgLatD - originalRearAxleAvgLatD) / originalRearAxleAvgLatD * 100, 3))

print()
print(front_bestAvgLatD)
print(rear_bestAvgLatD)

import math


class Tyre:
    def __init__(self, type, SHORT_NAME, FZ0, LS_EXPY, DY_REF, DCAMBER_0, DCAMBER_1):
        self.type = type
        self.SHORT_NAME = SHORT_NAME
        self.FZ0 = FZ0
        self.LS_EXPY = LS_EXPY
        self.DY_REF = DY_REF
        self.DCAMBER_0 = DCAMBER_0
        self.DCAMBER_1 = DCAMBER_1

    def __str__(self):
        string = "       Type: " + self.type + " " + self.SHORT_NAME + "\n"
        string += "        FZ0: " + str(self.FZ0) + "\n"
        string += "    LS_EXPY: " + str(self.LS_EXPY) + "\n"
        string += "     DY_REF: " + str(self.DY_REF) + "\n"
        string += "  DCAMBER_0: " + str(self.DCAMBER_0) + "\n"
        string += "  DCAMBER_1: " + str(self.DCAMBER_1) + "\n"
        string += "Opt. camber: " + str(round(self.DCAMBER_0 / self.DCAMBER_1 / 2 * 180 / math.pi, 3)) + " deg"
        return string

    def tyreLatD(self, Fz, camberDeg):
        """Tyre grip function"""
        # If the tyre load is 0 (or less than 0), simply return 0 (the force is going to be 0 anyway)
        if Fz <= 0:
            return 0
        else:
            camberRad = camberDeg * math.pi / 180
            # D from tyre load sensitivity
            D = self.DY_REF * pow(Fz, self.LS_EXPY - 1) * pow(self.FZ0, 1 - self.LS_EXPY)
            # Multiplies D by the camber multiplier
            D /= 1 + (self.DCAMBER_0 * camberRad) - (self.DCAMBER_1 * pow(camberRad, 2))
            return D


class Car:
    def __init__(self, carsDirectory, carName, tyreIndex, telemFileName, telemDirectory, telemLatGThreshold):
        """Reads tyre data from the data folder and initialises front and rear tyre objects:
            - tyreFront
            - tyreRear
            Also prints out the relevant car and tyre info
            Then reads telem data"""
        self.carName = carName
        carDataDirectory = carsDirectory + "\\" + carName + "\\data\\"

        # Tyre index headers
        if tyreIndex == 0:
            frontTyreHeader = "[FRONT]"
            rearTyreHeader = "[REAR]"
        else:
            frontTyreHeader = "[FRONT_" + str(tyreIndex) + "]"
            rearTyreHeader = "[REAR_" + str(tyreIndex) + "]"

        # Read tyre data from tyres.ini (Note: Assumes that the front tyre appears before the rear tyre in tyres.ini)
        tyresINIFile = open(carDataDirectory + "\\tyres.ini", "r")

        SHORT_NAME, FZ0, LS_EXPY, DY_REF, DCAMBER_0, DCAMBER_1 = None, None, None, None, None, None
        isFrontDataSection = False
        isRearDataSection = False
        for line in tyresINIFile:
            dataString = line.replace("\n", "").replace("\t", "").replace(" ", "").split(";")[0]

            # Read front tyre data
            if dataString == frontTyreHeader:
                isFrontDataSection = True
            if isFrontDataSection:
                if dataString.__contains__("SHORT_NAME="):
                    SHORT_NAME = dataString.split("SHORT_NAME=")[1]
                if dataString.__contains__("FZ0="):
                    FZ0 = float(dataString.split("FZ0=")[1])
                if dataString.__contains__("LS_EXPY="):
                    LS_EXPY = float(dataString.split("LS_EXPY=")[1])
                if dataString.__contains__("DY_REF="):
                    DY_REF = float(dataString.split("DY_REF=")[1])
                if dataString.__contains__("DCAMBER_0="):
                    DCAMBER_0 = float(dataString.split("DCAMBER_0=")[1])
                if dataString.__contains__("DCAMBER_1="):
                    DCAMBER_1 = float(dataString.split("DCAMBER_1=")[1])
                # If all the necessary data has been read for a Tyre object to be initialised
                if SHORT_NAME is not None and FZ0 is not None and LS_EXPY is not None and DY_REF is not None and DCAMBER_0 is not None and DCAMBER_1:
                    self.frontTyre = Tyre("Front", SHORT_NAME, FZ0, LS_EXPY, DY_REF, DCAMBER_0, DCAMBER_1)
                    isFrontDataSection = False
                    SHORT_NAME, FZ0, LS_EXPY, DY_REF, DCAMBER_0, DCAMBER_1 = None, None, None, None, None, None

            # Read rear tyre data
            if dataString == rearTyreHeader:
                isRearDataSection = True
            if isRearDataSection:
                if dataString.__contains__("SHORT_NAME="):
                    SHORT_NAME = dataString.split("SHORT_NAME=")[1]
                if dataString.__contains__("FZ0="):
                    FZ0 = float(dataString.split("FZ0=")[1])
                if dataString.__contains__("LS_EXPY="):
                    LS_EXPY = float(dataString.split("LS_EXPY=")[1])
                if dataString.__contains__("DY_REF="):
                    DY_REF = float(dataString.split("DY_REF=")[1])
                if dataString.__contains__("DCAMBER_0="):
                    DCAMBER_0 = float(dataString.split("DCAMBER_0=")[1])
                if dataString.__contains__("DCAMBER_1="):
                    DCAMBER_1 = float(dataString.split("DCAMBER_1=")[1])
                # If all the necessary data has been read for a Tyre object to be initialised
                if SHORT_NAME is not None and FZ0 is not None and LS_EXPY is not None and DY_REF is not None and DCAMBER_0 is not None and DCAMBER_1:
                    self.rearTyre = Tyre("Rear", SHORT_NAME, FZ0, LS_EXPY, DY_REF, DCAMBER_0, DCAMBER_1)
                    isRearDataSection = False

        # Unfiltered telemetry channels
        self.carPosNormTelem = []
        self.groundSpeedTelem = []

        # Filtered telemetry channels
        self.carPosNormTelemFiltered = []
        self.latGTelem = []
        self.FL_tyreLoadTelem = []
        self.FR_tyreLoadTelem = []
        self.RL_tyreLoadTelem = []
        self.RR_tyreLoadTelem = []
        self.FL_camberDegTelem = []
        self.FR_camberDegTelem = []
        self.RL_camberDegTelem = []
        self.RR_camberDegTelem = []

        # Read telemetry data
        dataLineStart = 18
        telemFile = open(telemDirectory + "\\" + telemFileName, "r")
        lineCounter = 1
        for line in telemFile:
            data = line.replace("\n", "").replace("\"", "")

            if lineCounter >= dataLineStart:
                data = [float(i) for i in data.split(",")]

                # For graphs
                self.carPosNormTelem.append(data[37])
                self.groundSpeedTelem.append(data[63])

                # For optimisation (filter for lateral G threshold)
                if abs(data[22]) >= telemLatGThreshold:
                    self.carPosNormTelemFiltered.append(data[37])
                    self.latGTelem.append(data[22])
                    self.FL_tyreLoadTelem.append(data[114])
                    self.FR_tyreLoadTelem.append(data[115])
                    self.RL_tyreLoadTelem.append(data[116])
                    self.RR_tyreLoadTelem.append(data[117])
                    self.FL_camberDegTelem.append(data[26])
                    self.FR_camberDegTelem.append(data[27])
                    self.RL_camberDegTelem.append(data[28])
                    self.RR_camberDegTelem.append(data[29])
            lineCounter += 1
        telemFile.close()

    def frontAxleAvgLatD(self, FL_camberOffset, FR_camberOffset):
        """Average front axle lateral D (friction coefficient) from telemetry filtered to only include loaded data
            points (absolute lat G >= threshold)"""
        FL_camberDegTrial = [i + FL_camberOffset for i in self.FL_camberDegTelem]
        FR_camberDegTrial = [i + FR_camberOffset for i in self.FR_camberDegTelem]

        frontAxleLatDArray = []
        for i in range(len(self.latGTelem)):
            # Checks if it's a left or right corner
            if self.latGTelem[i] > 0:
                # Left corner, FL camber is opposite
                FL_latD = self.frontTyre.tyreLatD(self.FL_tyreLoadTelem[i], -FL_camberDegTrial[i])
                FR_latD = self.frontTyre.tyreLatD(self.FR_tyreLoadTelem[i], FR_camberDegTrial[i])
            else:
                # Right corner, FR camber is opposite
                FL_latD = self.frontTyre.tyreLatD(self.FL_tyreLoadTelem[i], FL_camberDegTrial[i])
                FR_latD = self.frontTyre.tyreLatD(self.FR_tyreLoadTelem[i], -FR_camberDegTrial[i])

            # If the total axle tyre load is 0 (or less than 0), simply append 0 (the force is going to be 0 anyway)
            axleTyreLoad = self.FL_tyreLoadTelem[i] + self.FR_tyreLoadTelem[i]
            if axleTyreLoad <= 0:
                frontAxleLatDArray.append(0)
            else:
                frontAxleLatDArray.append((self.FL_tyreLoadTelem[i] * FL_latD + self.FR_tyreLoadTelem[i] * FR_latD) / axleTyreLoad)

        return sum(frontAxleLatDArray) / len(frontAxleLatDArray)

    def rearAxleAvgLatD(self, RL_camberOffset, RR_camberOffset):
        """Average rear axle lateral D (friction coefficient) from telemetry - which should be filtered to only include
            loaded data points (absolute lat G >= threshold)"""
        RL_camberDegTrial = [i + RL_camberOffset for i in self.RL_camberDegTelem]
        RR_camberDegTrial = [i + RR_camberOffset for i in self.RR_camberDegTelem]

        rearAxleLatDArray = []
        for i in range(len(self.latGTelem)):
            # Checks if it's a left or right corner
            if self.latGTelem[i] > 0:
                # Left corner, FL camber is opposite
                RL_latD = self.rearTyre.tyreLatD(self.RL_tyreLoadTelem[i], -RL_camberDegTrial[i])
                RR_latD = self.rearTyre.tyreLatD(self.RR_tyreLoadTelem[i], RR_camberDegTrial[i])
            else:
                # Right corner, FR camber is opposite
                RL_latD = self.rearTyre.tyreLatD(self.RL_tyreLoadTelem[i], RL_camberDegTrial[i])
                RR_latD = self.rearTyre.tyreLatD(self.RR_tyreLoadTelem[i], -RR_camberDegTrial[i])

            # If the total axle tyre load is 0 (or less than 0), simply append 0 (the force is going to be 0 anyway)
            axleTyreLoad = self.RL_tyreLoadTelem[i] + self.RR_tyreLoadTelem[i]
            if axleTyreLoad <= 0:
                rearAxleLatDArray.append(0)
            else:
                rearAxleLatDArray.append((self.RL_tyreLoadTelem[i] * RL_latD + self.RR_tyreLoadTelem[i] * RR_latD) / axleTyreLoad)

        return sum(rearAxleLatDArray) / len(rearAxleLatDArray)

    def optimiseFrontCamberSymmetric(self, camberStep=0.1, camberMinOffset=-1000, camberMaxOffset=1000):
        """Finds the optimum symmetric front camber offset to maximise average front axle lateral D (friction
            coefficient) from telemetry filtered to only include loaded data points (absolute lat G >= threshold)"""
        # Current setup avg lat D
        currentAvgLatD = self.frontAxleAvgLatD(0, 0)
        # Set best to the current setup
        bestCamberOffset = 0
        bestAvgLatD = currentAvgLatD

        # Test positive camber offset by 1 step (and check if the max offset allows this)
        trialAvgLatD = 0
        prevTrialAvgLatD = 0
        if camberStep <= camberMaxOffset:
            trialAvgLatD = self.frontAxleAvgLatD(camberStep, camberStep)

        # If avg lat D improves from the positive step test
        if trialAvgLatD > bestAvgLatD:
            bestCamberOffset = camberStep
            bestAvgLatD = trialAvgLatD
            # Iterate positive camber offsets until average lat D stops improving
            camberOffset = round(2 * camberStep, 10)
            while camberOffset <= camberMaxOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.frontAxleAvgLatD(camberOffset, camberOffset)
                if trialAvgLatD > bestAvgLatD:
                    bestCamberOffset = camberOffset
                    bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset + camberStep, 10)
        else:
            trialAvgLatD = currentAvgLatD
            # Iterate negative camber offsets until average lat D stops improving
            camberOffset = -camberStep
            while camberOffset >= camberMinOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.frontAxleAvgLatD(camberOffset, camberOffset)
                if trialAvgLatD > bestAvgLatD:
                    bestCamberOffset = camberOffset
                    bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset - camberStep, 10)

        print("Optimum front camber offset (deg):", bestCamberOffset)
        print("             Grip improvement (%):", round((bestAvgLatD - currentAvgLatD) / currentAvgLatD * 100, 3))

    def optimiseRearCamberSymmetric(self, camberStep=0.1, camberMinOffset=-1000, camberMaxOffset=1000):
        """Finds the optimum symmetric rear camber offset to maximise average rear axle lateral D (friction
            coefficient) from telemetry filtered to only include loaded data points (absolute lat G >= threshold)"""
        # Current setup avg lat D
        currentAvgLatD = self.rearAxleAvgLatD(0, 0)
        # Set best to the current setup
        bestCamberOffset = 0
        bestAvgLatD = currentAvgLatD

        # Test positive camber offset by 1 step (and check if the max offset allows this)
        trialAvgLatD = 0
        prevTrialAvgLatD = 0
        if camberStep <= camberMaxOffset:
            trialAvgLatD = self.rearAxleAvgLatD(camberStep, camberStep)

        # If avg lat D improves from the positive step test
        if trialAvgLatD > bestAvgLatD:
            bestCamberOffset = camberStep
            bestAvgLatD = trialAvgLatD
            # Iterate positive camber offsets until average lat D stops improving
            camberOffset = round(2 * camberStep, 10)
            while camberOffset <= camberMaxOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.rearAxleAvgLatD(camberOffset, camberOffset)
                if trialAvgLatD > bestAvgLatD:
                    bestCamberOffset = camberOffset
                    bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset + camberStep, 10)
        else:
            trialAvgLatD = currentAvgLatD
            # Iterate negative camber offsets until average lat D stops improving
            camberOffset = -camberStep
            while camberOffset >= camberMinOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.rearAxleAvgLatD(camberOffset, camberOffset)
                if trialAvgLatD > bestAvgLatD:
                    bestCamberOffset = camberOffset
                    bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset - camberStep, 10)

        print("Optimum rear camber offset (deg):", bestCamberOffset)
        print("            Grip improvement (%):", round((bestAvgLatD - currentAvgLatD) / currentAvgLatD * 100, 3))

    def optimiseFrontCamberAsymmetric(self, camberStep=0.1, FL_camberMinOffset=-1000, FL_camberMaxOffset=1000, FR_camberMinOffset=-1000, FR_camberMaxOffset=1000):
        """Finds the optimum FL and FR camber offset to maximise average front axle lateral D (friction coefficient)
            from telemetry filtered to only include loaded data points (absolute lat G >= threshold)
            Note that the camber offsets are allowed to be asymmetric for this optimisation"""
        # Current setup avg lat D
        currentAvgLatD = self.frontAxleAvgLatD(0, 0)

        """Optimise FL camber, keeping FR camber the same"""
        # Set best to the current setup
        FL_bestCamberOffset = 0
        FL_bestAvgLatD = currentAvgLatD

        # Test positive camber offset by 1 step (and check if the max offset allows this)
        trialAvgLatD = 0
        prevTrialAvgLatD = 0
        if camberStep <= FL_camberMaxOffset:
            trialAvgLatD = self.frontAxleAvgLatD(camberStep, 0)

        # If avg lat D improves from the positive step test
        if trialAvgLatD > FL_bestAvgLatD:
            FL_bestCamberOffset = camberStep
            FL_bestAvgLatD = trialAvgLatD
            # Iterate positive camber offsets until average lat D stops improving
            camberOffset = round(2 * camberStep, 10)
            while camberOffset <= FL_camberMaxOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.frontAxleAvgLatD(camberOffset, 0)
                if trialAvgLatD > FL_bestAvgLatD:
                    FL_bestCamberOffset = camberOffset
                    FL_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset + camberStep, 10)
        else:
            trialAvgLatD = currentAvgLatD
            # Iterate negative camber offsets until average lat D stops improving
            camberOffset = -camberStep
            while camberOffset >= FL_camberMinOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.frontAxleAvgLatD(camberOffset, 0)
                if trialAvgLatD > FL_bestAvgLatD:
                    FL_bestCamberOffset = camberOffset
                    FL_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset - camberStep, 10)

        """Optimise FR camber, keeping FL camber the same"""
        # Set best to the current setup
        FR_bestCamberOffset = 0
        FR_bestAvgLatD = currentAvgLatD

        # Test positive camber offset by 1 step (and check if the max offset allows this)
        trialAvgLatD = 0
        prevTrialAvgLatD = 0
        if camberStep <= FR_camberMaxOffset:
            trialAvgLatD = self.frontAxleAvgLatD(0, camberStep)

        # If avg lat D improves from the positive step test
        if trialAvgLatD > FR_bestAvgLatD:
            FR_bestCamberOffset = camberStep
            FR_bestAvgLatD = trialAvgLatD
            # Iterate positive camber offsets until average lat D stops improving
            camberOffset = round(2 * camberStep, 10)
            while camberOffset <= FR_camberMaxOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.frontAxleAvgLatD(0, camberOffset)
                if trialAvgLatD > FR_bestAvgLatD:
                    FR_bestCamberOffset = camberOffset
                    FR_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset + camberStep, 10)
        else:
            trialAvgLatD = currentAvgLatD
            # Iterate negative camber offsets until average lat D stops improving
            camberOffset = -camberStep
            while camberOffset >= FR_camberMinOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.frontAxleAvgLatD(0, camberOffset)
                if trialAvgLatD > FR_bestAvgLatD:
                    FR_bestCamberOffset = camberOffset
                    FR_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset - camberStep, 10)

        print("Optimum FL camber offset (deg):", FL_bestCamberOffset)
        print("Optimum FR camber offset (deg):", FR_bestCamberOffset)
        print("          Grip improvement (%):", round((self.frontAxleAvgLatD(FL_bestCamberOffset, FR_bestCamberOffset) - currentAvgLatD) / currentAvgLatD * 100, 3))

    def optimiseRearCamberAsymmetric(self, camberStep=0.1, RL_camberMinOffset=-1000, RL_camberMaxOffset=1000, RR_camberMinOffset=-1000, RR_camberMaxOffset=1000):
        """Finds the optimum RL and RR camber offset to maximise average front axle lateral D (friction coefficient)
            from telemetry filtered to only include loaded data points (absolute lat G >= threshold)
            Note that the camber offsets are allowed to be asymmetric for this optimisation"""
        # Current setup avg lat D
        currentAvgLatD = self.rearAxleAvgLatD(0, 0)

        """Optimise RL camber, keeping RR camber the same"""
        # Set best to the current setup
        RL_bestCamberOffset = 0
        RL_bestAvgLatD = currentAvgLatD

        # Test positive camber offset by 1 step (and check if the max offset allows this)
        trialAvgLatD = 0
        prevTrialAvgLatD = 0
        if camberStep <= RL_camberMaxOffset:
            trialAvgLatD = self.rearAxleAvgLatD(camberStep, 0)

        # If avg lat D improves from the positive step test
        if trialAvgLatD > RL_bestAvgLatD:
            RL_bestCamberOffset = camberStep
            RL_bestAvgLatD = trialAvgLatD
            # Iterate positive camber offsets until average lat D stops improving
            camberOffset = round(2 * camberStep, 10)
            while camberOffset <= RL_camberMaxOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.rearAxleAvgLatD(camberOffset, 0)
                if trialAvgLatD > RL_bestAvgLatD:
                    RL_bestCamberOffset = camberOffset
                    RL_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset + camberStep, 10)
        else:
            trialAvgLatD = currentAvgLatD
            # Iterate negative camber offsets until average lat D stops improving
            camberOffset = -camberStep
            while camberOffset >= RL_camberMinOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.rearAxleAvgLatD(camberOffset, 0)
                if trialAvgLatD > RL_bestAvgLatD:
                    RL_bestCamberOffset = camberOffset
                    RL_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset - camberStep, 10)

        """Optimise RR camber, keeping RL camber the same"""
        # Set best to the current setup
        RR_bestCamberOffset = 0
        RR_bestAvgLatD = currentAvgLatD

        # Test positive camber offset by 1 step (and check if the max offset allows this)
        trialAvgLatD = 0
        prevTrialAvgLatD = 0
        if camberStep <= RR_camberMaxOffset:
            trialAvgLatD = self.rearAxleAvgLatD(0, camberStep)

        # If avg lat D improves from the positive step test
        if trialAvgLatD > RR_bestAvgLatD:
            RR_bestCamberOffset = camberStep
            RR_bestAvgLatD = trialAvgLatD
            # Iterate positive camber offsets until average lat D stops improving
            camberOffset = round(2 * camberStep, 10)
            while camberOffset <= RR_camberMaxOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.rearAxleAvgLatD(0, camberOffset)
                if trialAvgLatD > RR_bestAvgLatD:
                    RR_bestCamberOffset = camberOffset
                    RR_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset + camberStep, 10)
        else:
            trialAvgLatD = currentAvgLatD
            # Iterate negative camber offsets until average lat D stops improving
            camberOffset = -camberStep
            while camberOffset >= RR_camberMinOffset and trialAvgLatD > prevTrialAvgLatD:
                prevTrialAvgLatD = trialAvgLatD
                trialAvgLatD = self.rearAxleAvgLatD(0, camberOffset)
                if trialAvgLatD > RR_bestAvgLatD:
                    RR_bestCamberOffset = camberOffset
                    RR_bestAvgLatD = trialAvgLatD
                camberOffset = round(camberOffset - camberStep, 10)

        print("Optimum RL camber offset (deg):", RL_bestCamberOffset)
        print("Optimum RR camber offset (deg):", RR_bestCamberOffset)
        print("          Grip improvement (%):", round((self.rearAxleAvgLatD(RL_bestCamberOffset, RR_bestCamberOffset) - currentAvgLatD) / currentAvgLatD * 100, 3))

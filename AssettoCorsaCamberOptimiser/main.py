from car import Car

# rss_formula_americas_2020_oval
# indy 1.3.1b.csv

# ks_audi_r8_lms_2016
# audi portimao.csv or audi portimao 2.csv

# bmw_m3_e30_dtm
# ks_mercedes_190_evo2

"""INPUTS"""
carName = "bmw_z4_gt3"
carsDirectory = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\content\\cars"

# If AttributeError: 'Car' object has no attribute 'frontTyre', double-check the tyre index
tyreIndex = 1   # Remember to check the tyre type (compound)

telemFileName = "bmw daytona.csv"
telemDirectory = "C:\\Users\\Willow\\Downloads"

telemLatGThreshold = 1
optimiseSymmetric = True
"""END OF INPUTS"""


car = Car(carsDirectory, carName, tyreIndex, telemFileName, telemDirectory, telemLatGThreshold)
print(car.frontTyre)
print()
print(car.rearTyre)
print()

if optimiseSymmetric:
    car.optimiseFrontCamberSymmetric()
    print()
    car.optimiseRearCamberSymmetric()
else:
    car.optimiseFrontCamberAsymmetric()
    print()
    car.optimiseRearCamberAsymmetric()

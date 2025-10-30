"""
Generates aero map plots for all wing combinations given in wingAnglesArray (without RH envelope overlay)
"""

from car import Car

"""INPUTS"""
carName = "rss_formula_americas_2020_oval"
carsDirectory = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\assettocorsa\\content\\cars"

RHMin = 0.001 * -20
RHMax = 0.001 * 20

RHStep = 0.001 * 1
colliderMargin = 0

wingAnglesArray = [[1, 1, 0.186, 0.186, 0.186, 0.186, 0.186, 0.186, 0.186, 0]]
"""END OF INPUTS"""

car = Car(carsDirectory, carName)
print(car)
print()

car.plotAeroMaps("plots", RHMin, RHMax, RHMin, RHMax, RHStep, colliderMargin, wingAnglesArray)

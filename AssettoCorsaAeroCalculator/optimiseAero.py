"""
Finds all valid setups (wing angles and ride heights) which achieve the aero balance target within a tolerance for the
ride height envelope given by telemetry

Provides the aero numbers of the valid setups, as well as the best performing setups (in terms of max ClA, min CdA and
max efficiency)

Note that:
- ClA is only calculated for the telemetry data points where the car is loaded (above a combined G threshold)
- CdA is only calculated for the telemetry data points where the car is not loaded (below a combined G threshold)
- Efficiency is the loaded ClA divided by the unloaded CdA to make it more relevant
"""
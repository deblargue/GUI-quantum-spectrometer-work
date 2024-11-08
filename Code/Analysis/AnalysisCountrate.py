#------IMPORTS-----
#Packages for ETA backend
import json
import etabackend.eta #Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/
import etabackend.tk as etatk

#Packages used for analysis
import numpy as np
import numpy.ma as ma
from pathlib import Path
import os
import time as t

from matplotlib import pyplot as plt

def load_eta(**kwargs):
    print(f'Starting ETA correlation analysis on file: {timetag_file}')

    # Load the recipe from seperate ETA file
    with open(recipe_file, 'r') as filehandle:
        recipe_obj = json.load(filehandle)

    eta_engine = etabackend.eta.ETA()
    eta_engine.load_recipe(recipe_obj)

    # Set parameters in the recipe
    for arg in kwargs:
        eta_engine.recipe.set_parameter(arg, str(kwargs[arg]))

    eta_engine.load_recipe()

    return eta_engine


# ETA Settings
timetag_file = '/Users/juliawollter/Desktop/GUI Spectro/Data/240614/Spectrometer_test_1s_(2ch_6_7)_240614.timeres'
#timetag_file = '/Users/juliawollter/Desktop/GUI Spectro/Data/240614/Spectrometer_test_1s_(3ch_5_6_7)_240614.timeres'
timetag_file = '/Users/juliawollter/Desktop/GUI Spectro/Data/240614/Spectrometer_test_4s_(2ch_6_7)_240614.timeres'
timetag_file = '/Users/juliawollter/Desktop/GUI Spectro/Data/240614/Spectrometer_test_4s_(3ch_5_6_7)_240614.timeres'


recipe_file = '/Users/juliawollter/Desktop/GUI Spectro/Code/ETARecipes/Countrate-swabian_spectrometer.eta'  #'/Code/ETARecipes/Countrate-swabian_spectrometer.eta'
#recipe_file = '/Users/juliawollter/Desktop/GUI Spectro/Code/ETARecipes/Countrate-swabian_spectrometer_2.eta'  #'/Code/ETARecipes/Countrate-swabian_spectrometer.eta'
#recipe_file = '/Code/ETARecipes/Countrate-swabian_spectrometer.eta'
scantime = 4

binsize = 10 * (10**10)
bins = (scantime * 0.1) * (10**2)

#binsize = 5 * (10**10)
#bins = (scantime * 0.2) * (10**2)

time_axis_s = np.arange(0, bins) * binsize / (10**12)
engine = load_eta(bins=bins, binsize=binsize, file=timetag_file)

# --------
print(f"Starting ETA analysis \nFile: {timetag_file}")
file = Path(timetag_file)
cutfile = engine.clips(filename=Path(file), format=1)
result = engine.run({"timetagger1": cutfile}, group='swabian')  # Runs the time tagging analysis and generates histograms
print('Finished ETA analysis')

print(result.keys())
plt.figure()
plt.title("Countrate")
plt.plot(time_axis_s, result['h1'])
plt.plot(time_axis_s, result['h2'], label='h2')
plt.plot(time_axis_s, result['h3'], label='h3')
plt.plot(time_axis_s, result['h4'], label='h4')
plt.grid()
plt.legend()
plt.show()


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


def eta_analyzer(timetag_file, recipe_file, **kwargs):
    #Load the recipe from seperate ETA file
    with open(recipe_file, 'r') as filehandle:
        recipe_obj = json.load(filehandle)


    eta_engine = etabackend.eta.ETA()
    eta_engine.load_recipe(recipe_obj)

    #Set parameters in the recipe
    for arg in kwargs:
        eta_engine.recipe.set_parameter(arg, str(kwargs[arg]))


    eta_engine.load_recipe()

    print(f"Starting ETA analysis \nFile: {timetag_file}")
    
    file = Path(timetag_file)
    cutfile = eta_engine.clips(filename = file, format = 1)
    result = eta_engine.run({"timetagger1":cutfile}, group='swabian') #Runs the time tagging analysis and generates histograms

    return result


file = 'Spectrometer_test_4s_(3ch_5_6_7)_240614.timeres'

binsize = 20
bins = 125*5

recipe_file = 'Lifetime-swabian_spectrometer.eta'

r = eta_analyzer(file, recipe_file, bins = bins, binsize = binsize, det_delay = 12500)
print(r.keys())

time_axis = np.arange(bins)*binsize

fig, ax = plt.subplots()

ax.set_title("Lifetime")
ax.plot(time_axis, r['t2'], label = 'ch 5')
ax.plot(time_axis, r['t3'], label = 'ch 6')
ax.plot(time_axis, r['t4'], label = 'ch 7')
ax.set_xlabel("time")

ax.legend()
plt.show()

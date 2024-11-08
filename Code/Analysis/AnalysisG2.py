# ------IMPORTS-----
# Packages for ETA backend
import json
import etabackend.eta as eta  # Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/
import etabackend.tk as etatk

import os
import time as t
from pathlib import Path

from matplotlib import pyplot as plt
import numpy as np
from scipy.constants import c


# ------- ETA analysis ----------
def load_eta(recipe, **kwargs):
    print('Loading ETA')
    with open(recipe, 'r') as filehandle:
        recipe_obj = json.load(filehandle)

    eta_engine = eta.ETA()
    eta_engine.load_recipe(recipe_obj)

    # Set parameters in the recipe
    for arg in kwargs:
        eta_engine.recipe.set_parameter(arg, str(kwargs[arg]))

    eta_engine.load_recipe()

    return eta_engine

def eta_analysis(file, eta_engine):
    print('Starting ETA analysis')
    cut = eta_engine.clips(Path(file), format=1)
    result = eta_engine.run({"timetagger1": cut}, group='swabian')
    print('Finished ETA analysis')

    return result

def second_correleation(timetag_file, eta_engine, bins, binsisize):
    # ETA analys
    result_1 = eta_analysis(timetag_file, eta_engine)
    #print("Result keys:", result_1.keys())

    # Result keys: dict_keys(['timetagger1', 'h23', 'h32', 'h24', 'h42', 'h43', 'h34'])

    # extract result
    h1p = result_1['h32']   # ['h3']
    h1n = result_1['h23']   # ['h4']
    g2 = np.concatenate((h1n, h1p))

    delta_t = np.arange(-bins, bins) * binsize * 1e-3

    plot_g2(delta_t, np.concatenate((result_1['h23'], result_1['h32'])))
    plot_g2(delta_t, np.concatenate((result_1['h24'], result_1['h42'])))
    plot_g2(delta_t, np.concatenate((result_1['h34'], result_1['h43'])))

    return g2, delta_t

def plot_g2(delta_t, g2):
    # Plot the results
    fig, ax = plt.subplots()
    ax.plot(delta_t, g2)
    ax.set_xlabel('time [ns]', fontsize=10)
    ax.set_ylabel('coincidence', fontsize=10)
    # plt.subplots_adjust(left = 0.448, top = 0.556)


#eta_recipe = 'C:/Users/staff/Documents/Lidar LF/ETA_recipes/Swabian/Correlation-swabian_#2.eta'
eta_recipe = 'Correlation-swabian_spectrometer.eta'
folder = f"K:\\Stephane\\1dlidarspectrometer\\240614\\"
timetag_file = 'C:/Users/vLab/Desktop/Spec Lidar/data/Spectrometer_test_3ch_4s_240614.timeres'

#ETA Settings
binsize = 20
bins = 10000
time_axis = np.arange(0,bins)*binsize
eta_engine = load_eta(eta_recipe, bins=bins, binsize=binsize)

g2, delta_t = second_correleation(timetag_file, eta_engine, bins, binsize)

plt.show()


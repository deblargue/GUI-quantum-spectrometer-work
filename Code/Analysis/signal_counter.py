#------IMPORTS-----
#Packages for ETA backend
import json
import etabackend.eta #Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/
import etabackend.tk as etatk

#Packages used for analysis
#import numpy as np
from pathlib import Path
import os
#from matplotlib import pyplot as plt



def eta_counter(timetag_file, recipe_file,  **kwargs):

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
    result = eta_engine.run({"timetagger1":cutfile}, group='qutag') #Runs the time tagging analysis and generates histograms

    signals = {0:'c0', 1:'c1', 2:'c2', 3:'c3', 4:'c4', 5:'c5' , 6:'c6', 7:'c7', 8:'c8'}
    
    print(f"Signals counts:")
    for s in signals:
        print(f"{s} : {result[signals[s]]}")



if __name__ == '__main__': 
    #file = 'K:/Microscope/Data/231103/nr_6_dup_marker_sineFreq(1.0)_numFrames(2)_sineAmp(0.3)_stepAmp(0.3)_stepDim(100)_date(231103)_time(14h48m42s).timeres'
    #recipe = 'signal_counter.eta'
    #eta_counter(file, recipe)
    print("This does not do anything")


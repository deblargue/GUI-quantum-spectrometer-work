
import time
import numpy as np
from datetime import date
import TimeTagger
import os

def get_date():
    '''Returns todays date in the format yymmdd'''
    """r = ''
    d = date.today()
    day = d.day
    if int(day) >= 10:
        day = str(day)
    else:
        day = str(0) + str(day)
    month = d.month
    if int(month) >= 10:
        month = str(month)
    else:
        month = str(0) + str(month)
    year = str(d.year)[2:4]
    r = year + month + day"""
    d = time.strftime("%y%m%d", time.localtime())
    t = time.strftime("%Hh%Mm%Ss", time.localtime())
    return d, t

def check_dir(folder_path):
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
        print(f"new folder '{folder_path}' created")
    else:
        print(f"folder '{folder_path}' already exists, ya idiot")

def start_tt(file):
    # Setup the TimeTaggerX
    tagger = TimeTagger.createTimeTagger()

    # Starts the qutag
    ch1 = 1   # sync ch
    ch2 = -2  # det ch
    ch3 = -3  # det ch
    ch4 = -4  # det ch

    tagger.setTriggerLevel(ch1, 0.3)   # sync channel
    tagger.setTriggerLevel(ch2, -0.125)   # det channel
    tagger.setTriggerLevel(ch3, -0.125)   # det channel
    tagger.setTriggerLevel(ch4, -0.125)   # det channel

    sync_ch = [ch1]
    trigger_chs = [ch2, ch3, ch4]

    # ToF measurements
    tagger.setConditionalFilter(trigger=trigger_chs, filtered=sync_ch)  # filter, take away
    # ------------------------------------
    # Start dump
    tagger_dump = TimeTagger.Dump(tagger=tagger, filename=file, max_tags=-1, channels=sync_ch+trigger_chs)

    return tagger, tagger_dump


# ------------------------
# NOTE/TODO: set trigger levels for timetagger config

todaydate, todaytime = get_date()

scan_time = int(10)

scan_name = f"Spectrometer_test_3ch"
#scan_name = f'spectrometer_(sync_ch_1)_(det_ch_2_3_4)_(scantime_{scan_time}s)'

"""
#folder_path = f"K:\\Stephane\\1dlidarspectrometer\\{todaydate}"
#check_dir(folder_path)  # create a folder is it doesn't exist"""

folder_path = "C:\\Users\\vLab\\Desktop\\SpectrometerData\\code\\"

file_name = f"{scan_name}_(scantime{scan_time}s)_(date_{todaydate})_(time_{todaytime}).timeres"

file_path = folder_path + file_name


# CREATING TIMETAGGER
t_tagger, t_dump = start_tt(file_path)
time.sleep(2)

# START TIMETAGGER
t_dump.start()

# DO MEASUREMENT...
time.sleep(scan_time)

# STOP TIMETAGGER
t_dump.stop()
print('Done with dumping Timetag measurement!')
time.sleep(2)
TimeTagger.freeTimeTagger(t_tagger)   # Note: very important, don't remove



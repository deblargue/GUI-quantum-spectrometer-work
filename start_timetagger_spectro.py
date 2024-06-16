
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

def start_tt(file, tagger):
    # Starts the qutag
    ch1 = 1   # sync
    ch2 = -2
    ch3 = -3
    ch4 = -4

    # ------ DO ANY ADDITIONAL SETUPS -----
    # TODO: check and look into
    tagger.setTriggerLevel(ch1, 0.3)   # sync channel
    tagger.setTriggerLevel(ch2, -0.125)   # det channel
    tagger.setTriggerLevel(ch3, -0.125)   # det channel
    tagger.setTriggerLevel(ch4, -0.125)   # det channel

    sync_ch = [ch1]
    trigger_chs = [ch2, ch3, ch4]

    # ToF measurements
    tagger.setConditionalFilter(trigger=trigger_chs, filtered=sync_ch)  # filter, take away
    # ------------------------------------
    time.sleep(1)
    # Start dump
    tagger_dump = TimeTagger.Dump(tagger=tagger, filename=file, max_tags=-1, channels=sync_ch+trigger_chs)

    return tagger_dump


def stop_tt(tagger_dump):
    time.sleep(0.5)



# ------------------------
# NOTE/TODO: set trigger levels for timetagger config

scan_time = 15
scan_name = f'Theo_ToF_output_to_spectrometer_input_(sync_ch_1)_(det_ch_2_3_4)_(scantime_{scan_time}s)'

todaydate, todaytime = get_date()
folder_path = f"K:\\Stephane\\1dlidarspectrometer\\{todaydate}"
folder_path = "C:\\Users\\vLab\\Desktop\\SpectrometerData\\code"

check_dir(folder_path)

file_name = f"{scan_name}_(date_{todaydate})_(time_{todaytime})"
file_path = folder_path + '\\' + file_name + ".timeres"

# Setup the TimeTaggerX
tagger = TimeTagger.createTimeTagger()

# START TIMETAGGER
t_dump = start_tt(file_path, tagger)
t_dump.start()
time.sleep(2)

# DO MEASUREMENT.....
time.sleep(scan_time)

# STOP TIMETAGGER
t_dump.stop()
print('Done with dumping Timetag measurement!')
TimeTagger.freeTimeTagger(tagger)


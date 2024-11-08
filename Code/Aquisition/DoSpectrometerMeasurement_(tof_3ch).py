import time
import TimeTagger
from datetime import date
import signal_checker
import os

def flip_neg_channels(old_file, new_file, bad_ch):
    if old_file == new_file:
        print("\n*ERROR*\nProvided file names are the same:\n"
              f"   -->  {old_file}\n"
              "Please give two separate file names (old and new)")
        exit()

    # find out how many 16-byte entries there are in the 'input file'
    temp_file = open(old_file, "rb")
    temp_read = temp_file.read()        # read 16 bytes at a time
    temp_file.close()
    n_entries = int(len(temp_read)/16)

    # opening read/write data files:
    #print("\nInitializing datafile manipulation\nUsing data file:", old_file)
    print('\nFixing Data ')
    input_file = open(old_file, "rb")
    output_file = open(new_file, "wb")

    t = 0
    # loop through all the data entries, extracting and potentially fixing channel value
    for i in range(n_entries):

        # read 16 bytes at a time (size of each record by timetagger)
        binary_line = input_file.read(16)

        # read off current channel number (before any changes)
        channel_int = int.from_bytes(binary_line[4:8], 'little', signed=True)

        # If channel int is in undesired list --> change it. otherwise write unchanged bytes
        if channel_int in bad_ch:
            t += 1

            # Change channel number. Example: channel -1 --> 101
            int_new = abs(channel_int)# + 100

            # Convert new channel number to bytestring (4bytes)
            bytes_new_ch = int_new.to_bytes(4, 'little', signed=True)

            # Write new file entry (with changed data)
            new_binary_line = binary_line[:4] + bytes_new_ch + binary_line[8:]
            output_file.write(new_binary_line)
        else:
            output_file.write(binary_line)

    # close files when done
    input_file.close()
    output_file.close()

    print(f"--> Done fixing data!\n")

def get_date():
    '''Returns todays date in the format yymmdd'''
    r = ''
    d = date.today()
    
    day = d.day
    if int(day) >= 10:
        day = str(day)
    else:
        day = str(0)+str(day)

    month = d.month
    if int(month) >= 10:
        month = str(month)
    else:
        month = str(0)+str(month)

    year = str(d.year)[2:4]

    r = year+month+day

    return r

#Folder to save data in
folder = "C:/Users/vLab/Desktop/Spec Lidar/data/"

#Scanning variables
integration_time = int(1)

name = f"Spectrometer_test_3ch_{integration_time}s"

date = get_date()
temp_file = folder+name+f'temp_{date}.timeres'
file = folder+name+f'_{date}.timeres'


sync_ch = 1
det_ch2 = -2
det_ch3 = -3
det_ch4 = -4


#Setup the TimeTaggerX
tagger = TimeTagger.createTimeTagger()

tagger.setTriggerLevel(det_ch2, -0.125)
tagger.setTriggerLevel(det_ch3, -0.125)
tagger.setTriggerLevel(det_ch4, -0.125)
tagger.setTriggerLevel(sync_ch, 0.3)


tagger.setConditionalFilter(trigger=[det_ch2, det_ch3, det_ch4], filtered=[sync_ch])

d = TimeTagger.Dump(tagger=tagger, filename = temp_file, max_tags=-1, channels=[det_ch2, det_ch4, sync_ch, det_ch3])

time.sleep(0.5)
print(f'Starting measurement \nSaving to file: {name}')
d.start()
time.sleep(integration_time)
d.stop()

time.sleep(1.5) # Arbitrary Value
TimeTagger.freeTimeTagger(tagger)

print('Done')
flip_neg_channels(temp_file, file, bad_ch = [-1,-2,-3,-4])
os.remove(temp_file)

signal_checker.eta_counter(file)

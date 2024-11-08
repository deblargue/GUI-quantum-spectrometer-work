# >> DebuggingFunctions() Imports:
# None
# >> TT() Imports:
import time
import TimeTagger
import os
import Code.Analysis.signal_counter as signal_counter

# >> ETA() Imports:
import json
from pathlib import Path
import etabackend.eta       # Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/
import numpy as np
from matplotlib import pyplot as plt
# >> LiveCounts() Imports:
from Code.RetinaFiles.src.WebSQSocketController import websocket_client
import asyncio


class DebuggingFunctions:

    @staticmethod
    def get_children(parent):
        return parent.winfo_children()

    @staticmethod
    def remove_child(parent, idx):
        try:
            parent.winfo_children()[idx].destroy()
            return True
        except:
            return False

    @staticmethod
    def print_children(parent, parentname="", info=""):
        print(f"------------\n"
              f"DEBUGGING: 'print_children()'\n"
              f"# Info=\n"
              f"  --> {info}\n"
              f"# Parent=\n"
              f"  --> {parentname}\n"
              f"# Children=")
        for widget in parent.winfo_children():
            print(f"  --> {widget}")
        print("------------")


class TT:
    # TODO: TEST BOTH SCRIPTS, likely correct one is 'start_tt_neg()'

    @staticmethod
    def start_tt_pos(scan_time=10, scan_name="", folder_path=""):

        if scan_name == "":
            # >> Fetch current time and date for data file name
            todaydate = time.strftime("%y%m%d", time.localtime())
            todaytime = time.strftime("%Hh%Mm%Ss", time.localtime())
            # ------------------------

            # >> Define file names and save locations
            scan_name = f'spectrometer_test_(sync_ch_1)_(det_ch_2_3_4)'
            file_name = f"{scan_name}_(scantime{scan_time}s)_(date_{todaydate})_(time_{todaytime}).timeres"

        # >> CHECK IF FOLDER ALREADY EXISTS, OTHERWISE CREATE ONE
        if folder_path != "":
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
                print(f"new folder '{folder_path}' created")
            else:
                print(f"folder '{folder_path}' already exists")
        # ------------------------

        # >> COMBINING FOLDER AND FILENAME
        file_path = folder_path + file_name

        # >> CREATING TIMETAGGER

        # Create a new TimeTaggerX object
        tagger = TimeTagger.createTimeTagger()

        # Define channels of each
        sync_ch = 1
        det_ch2 = -2
        det_ch3 = -3
        det_ch4 = -4

        # Define trigger levels per channel on TT
        tagger.setTriggerLevel(sync_ch, 0.3)     # sync channel
        tagger.setTriggerLevel(det_ch2, -0.125)  # det channel
        tagger.setTriggerLevel(det_ch3, -0.125)  # det channel
        tagger.setTriggerLevel(det_ch4, -0.125)  # det channel

        remove_chs = [sync_ch]
        trigger_chs = [det_ch2, det_ch3, det_ch4]
        all_chs = remove_chs + trigger_chs  # combine channels lists to include all of them

        # ToF measurements
        tagger.setConditionalFilter(trigger=trigger_chs, filtered=remove_chs)  # declare which TT channels we want to record

        # Create a dump that will later "dump" data into file
        t_dump = TimeTagger.Dump(tagger=tagger, filename=file_path, max_tags=-1, channels=all_chs)
        time.sleep(1)
        # ------------------------

        # >> START TIMETAGGER, i.e. start recording data
        t_dump.start()
        # ------------------------

        # >> WAITING FOR MEASUREMENT TIME TO END
        time.sleep(scan_time)
        # ------------------------

        # >> STOP TIMETAGGER
        t_dump.stop()
        # ------------------------

        # >> FREE TIMETAGGER
        print('Done with dumping Timetag measurement!')
        time.sleep(2)
        TimeTagger.freeTimeTagger(tagger)  # Note: very important, don't remove
        # ------------------------

    @staticmethod
    def start_tt_neg(scan_time=10, scan_name="", folder_path=""):

        def flip_neg_channels(old_file, new_file, bad_ch):
            if old_file == new_file:
                print("\n*ERROR*\nProvided file names are the same:\n"
                      f"   -->  {old_file}\n"
                      "Please give two separate file names (old and new)")
                exit()

            # find out how many 16-byte entries there are in the 'input file'
            temp_file = open(old_file, "rb")
            temp_read = temp_file.read()  # read 16 bytes at a time
            temp_file.close()
            n_entries = int(len(temp_read) / 16)

            # opening read/write data files:
            # print("\nInitializing datafile manipulation\nUsing data file:", old_file)
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
                    int_new = abs(channel_int)  # + 100

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

        if scan_name == "":  # if filename not given, create a new one
            todaydate = time.strftime("%y%m%d", time.localtime())
            todaytime = time.strftime("%Hh%Mm%Ss", time.localtime())
            scan_name = f"Spectrometer_no_name_{scan_time}s_({todaydate}_{todaytime})"

        temp_file = folder_path + scan_name + f'temp.timeres'   # This file is used to take the initial data with negative channels
        file = folder_path + scan_name + '.timeres'             # This file will contain converted channel labels (from negative to positive channel names needed for ETA analysis)

        sync_ch = 1
        det_ch2 = -2
        det_ch3 = -3
        det_ch4 = -4

        # Setup the TimeTaggerX
        tagger = TimeTagger.createTimeTagger()

        tagger.setTriggerLevel(sync_ch, 0.3)
        tagger.setTriggerLevel(det_ch2, -0.125)
        tagger.setTriggerLevel(det_ch3, -0.125)
        tagger.setTriggerLevel(det_ch4, -0.125)

        tagger.setConditionalFilter(trigger=[det_ch2, det_ch3, det_ch4], filtered=[sync_ch])

        d = TimeTagger.Dump(tagger=tagger, filename=temp_file, max_tags=-1, channels=[det_ch2, det_ch4, sync_ch, det_ch3])

        time.sleep(0.5)
        print(f'Starting measurement \nSaving to file: {scan_name}')
        d.start()
        time.sleep(scan_time)
        d.stop()

        time.sleep(1.5)  # Arbitrary Value
        TimeTagger.freeTimeTagger(tagger)

        print('Done')
        flip_neg_channels(temp_file, file, bad_ch=[-1, -2, -3, -4])
        os.remove(temp_file)

        signal_counter.eta_counter(file, recipe_file='Code/ETARecipes/signal_counter.ETA')  # This will check the file and print which channels are found


class ETA:

    def __init__(self, parent, gui_class):
        # TODO:  maybe make bins and binsize variable in code? or have txt file that we read/write from in settings (along with other defaults)
        self.parent = parent
        self.gui_class = gui_class
        self.const = {
            'eta_format':    1,      # swabian = 1
            'eta_recipe':   '',
            'eta_recipe_corr':       'Code/ETARecipes/Correlation-swabian_spectrometer.eta',
            'eta_recipe_lifetime':   'Code/ETARecipes/Lifetime-swabian_spectrometer.eta',
            'eta_recipe_spectrum':   'Code/ETARecipes/Countrate-swabian_spectrometer.eta',
            'timetag_file': '',          #'Data/ToF_Duck_10MHz_det1_det2_5.0ms_[2.1, 3.9, -3.2, -4.8]_100x100_231220.timeres',
            'bins':          5000,
            'binsize':       20,     # bin width in ps
            }
        self.folded_countrate_pulses = {}
        self.ch_colors = ['tab:purple', 'tab:pink', 'tab:orange']

        self.pix_dict = {
            # EXAMPLE:
            # 'h1' : {
            #    'name'          : 'ch1',
            #    'wavelength'    : 600,
            #    'color'         : 'tab:red',
            #    'counts'        : 6958,
            #    'lifetime'      : 57.4,
            # }
        }
        self.binsize_dict = {}
        self.bins_dict = {}
        self.lifetime_bins_ns = []
        self.correlation_bins_ns = []
        self.countrate_bins_ns = []
        self.eta_engine = None
        self.eta_engine_corr = None
        self.eta_engine_lifetime = None
        self.eta_engine_spectrum = None

        #self.load_all_engines()

    def load_eta(self, recipe, **kwargs):
        print("LOADING ETA")

        with open(recipe, 'r') as filehandle:
            recipe_obj = json.load(filehandle)

        eta_engine = etabackend.eta.ETA()
        eta_engine.load_recipe(recipe_obj)

        # Set parameters in the recipe
        for arg in kwargs:
            eta_engine.recipe.set_parameter(arg, str(kwargs[arg]))
        eta_engine.load_recipe()

        #self.parent.write_log(f"Recipe loaded!")

        return eta_engine

    def load_all_engines(self, scantime = 1):
        #bins = 10000
        #binsize = 20

        #self.eta_engine_corr = self.load_eta(self.const["eta_recipe_corr"], bins=self.const["bins"], binsize=self.const["binsize"])  # NOTE: removed for test
        #self.eta_engine_lifetime = self.load_eta(self.const["eta_recipe_lifetime"], bins=self.const["bins"], binsize=self.const["binsize"])  # NOTE: removed for test
        #self.eta_engine_spectrum = self.load_eta(self.const["eta_recipe_spectrum"], bins=self.const["bins"], binsize=self.const["binsize"])  # NOTE: removed for test
        print("LOADING ALL ETA ENGINES")

        self.binsize_dict['counts'] = 10 * (10 ** 10)
        self.bins_dict['counts'] = (scantime * 0.1) * (10 ** 2)

        self.eta_engine_corr = self.load_eta(self.const["eta_recipe_corr"], bins=10000, binsize=20)
        self.eta_engine_lifetime = self.load_eta(self.const["eta_recipe_lifetime"], bins=125*5, binsize=20, det_delay = 12500)
        self.eta_engine = self.load_eta(self.const["eta_recipe_lifetime"], bins=125*5, binsize=20, det_delay = 12500)
        self.eta_engine_spectrum = self.load_eta(self.const["eta_recipe_spectrum"], bins=self.bins_dict['counts'], binsize=self.binsize_dict['counts'])

    # ---------------------------------

    def new_lifetime_analysis(self, ax=None, file=None):
        print("STARTING NEW LIFETIME ANALYSIS")

        bins = 125*5
        binsize = 20

        #bins_i = np.linspace(0, bins + 1, bins + 2)  # starting with 8 channels for now
        #self.lifetime_bins_ns = list(np.array(bins_i * binsize) / 1000)  # changing values from picoseconds to nanoseconds

        if not file:
            file = self.parent.params['file_name']['var'].get()

        cutfile = self.eta_engine_lifetime.clips(filename=file, format=1)
        result = self.eta_engine_lifetime.run({"timetagger1": cutfile}, group='swabian')  # Runs the time tagging analysis and generates histograms

        self.lifetime_bins_ns = np.arange(bins) * binsize

        channels = ['h4', 'h2', 'h3']

        self.folded_countrate_pulses = dict([(c, result[c]) for c in channels])

        # --TODO CHECK BELOW--
        wavelens = self.get_wavelengths()

        for c, channel in enumerate(self.folded_countrate_pulses.keys()):
            peak_idx = self.find_peak_idx(self.folded_countrate_pulses[channel])
            self.pix_dict[channel] = {
                'name': 'c' + channel,
                'wavelength': wavelens[c],  # computed
                # 'color': self.ch_colors[c % len(self.ch_colors)],
                'color': self.gui_class.CIE_colors.get_rgb(wavelens[c]),
                'counts': sum(self.folded_countrate_pulses[channel]),  # sum of channel
                'peak idx': peak_idx,
                'lifetime': self.lifetime_bins_ns[peak_idx],  # calculated max value
            }

        #return ax

    def new_countrate_analysis(self, file=None):
        # ETA Settings
        #binsize = 200   # 20
        #bins = 1000
        print("STARTING COUNTRATE ANALYSIS")

        time_axis = np.arange(0, self.bins_dict['counts']) * self.binsize_dict['counts']

        if not file:
            file = self.parent.params['file_name']['var'].get()

        print(f'Starting ETA countrate analysis on file: {file}')
        cut = self.eta_engine_spectrum.clips(Path(file), format=1)
        result = self.eta_engine_spectrum.run({"timetagger1": cut}, group='swabian')
        print('Finished ETA analysis')

        print(result.keys())

        return time_axis / (10**12), result

    def new_correlation_analysis(self, ax=None, file=None):  # correlation
        print("STARTING CORRELATION ANALYSIS")

        # ETA Settings
        binsize = 20
        bins = 10000
        #time_axis = np.arange(0, bins) * binsize
        delta_t = np.arange(-bins, bins) * binsize * 1e-3
        #channels = ['h1', 'h2', 'h3', 'h4']

        if not file:
            file = self.parent.params['file_name']['var'].get()

        print(f'Starting ETA correlation analysis on file: {file}')
        cut = self.eta_engine_corr.clips(Path(file), format=1)
        result = self.eta_engine_corr.run({"timetagger1": cut}, group='swabian')
        print('Finished ETA analysis')
        # Result keys: dict_keys(['timetagger1', 'h23', 'h32', 'h24', 'h42', 'h43', 'h34'])

        g2_23 = np.concatenate((result['h23'], result['h32']))
        g2_24 = np.concatenate((result['h24'], result['h42']))
        g2_34 = np.concatenate((result['h34'], result['h43']))

        """
        ax.set_title(f"G2 measurement")
        ax.plot(delta_t, g2_23, label="chs: 5, 6")
        ax.plot(delta_t, g2_24, label="chs: 5, 7")
        ax.plot(delta_t, g2_34, label="chs: 6, 7")
        # TODO: PLOT SEPARATELY
        ax.legend()
        ax.set_xlabel('time [ns]', fontsize=10)
        ax.set_ylabel('coincidence', fontsize=10)
        """

        # TODO: RETURN FIGURES!!! OR SOMETHING TO PUT IN GUI
        return delta_t, {'h23' : g2_23, 'h24' : g2_24, 'h34' : g2_34}

    def signal_count(self, file):
        # help function to check how many counts each channel has in the timeres file
        print("STARTING SIGNAL COUNT ANALYSIS???")

        def eta_counter_swab(recipe_file, timetag_file, **kwargs):
            # Load the recipe from seperate ETA file
            with open(recipe_file, 'r') as filehandle:
                recipe_obj = json.load(filehandle)

            eta_engine = etabackend.eta.ETA()
            eta_engine.load_recipe(recipe_obj)

            # Set parameters in the recipe
            for arg in kwargs:
                self.parent.write_log(f"Setting {kwargs[arg]} = {arg}")
                eta_engine.recipe.set_parameter(arg, str(kwargs[arg]))

            eta_engine.load_recipe()

            file = Path(timetag_file)
            cutfile = eta_engine.clips(filename=file, format=1)
            result = eta_engine.run({"timetagger1": cutfile}, group='qutag')  # Runs the time tagging analysis and generates histograms

            # self.parent.write_log(f"{2} : {result['c2']}")
            # self.parent.write_log(f"{3} : {result['c3']}")

            if recipe != 'signal_counter.eta':

                plt.figure('(marker) h3 swabian')
                plt.plot(result['h3'])
                plt.title("swab histo: markers")

                plt.figure("both qutag")
                plt.plot(result['h2'], 'b')
                plt.plot(result['h3'], 'r*')
                plt.title("qutag histo: both ")
            else:
                signals = {0: 'c0', 1: 'c1', 2: 'c2', 3: 'c3', 4: 'c4',
                           # 5: 'c5', 6: 'c6', 7: 'c7', 8: 'c8',
                           # 100: 'c100', 101: 'c101', 102: 'c102', 103: 'c103',
                           # 1001: 'c1001', 1002: 'c1002',
                           }

                self.parent.write_log(f"\n# : counts\n-------")
                for s in signals:
                    self.parent.write_log(f"{s} : {result[signals[s]]}")

        recipe = 'signal_counter.eta'

        freq = 1
        bins = 20000
        binsize = int(round((1 / (freq * 1e-12)) / bins))
        eta_counter_swab(recipe, file, binsize=binsize, bins=bins)

        plt.show()

        self.parent.write_log(f"done!")

    def get_wavelengths(self):

        #nr_pix = self.parent.params['nr_pixels']['var'].get()
        nr_pix = len(self.parent.eta_class.folded_countrate_pulses.keys())   # TODO FIXME: what happens if we define more channels than we have data on?
        pixel_width = self.parent.params['width_nm']['var'].get()   # TODO: maybe make this different depending on which
        center_pix = self.parent.params['nm']['var'].get()

        left_pix_bound = center_pix - (nr_pix * pixel_width / 2)
        right_pix_bound = center_pix + (nr_pix * pixel_width / 2)

        bins = np.linspace(start=left_pix_bound, stop=right_pix_bound, num=nr_pix+1, endpoint=True)  # , dtype=)

        x_centers = [(bins[i - 1] + bins[i]) / 2 for i in range(1, len(bins))]

        # Trying with calibrated values: TODO FIX
        x_centers = [wl.get() for wl in self.gui_class.calibrationclass.wavelengths.values()]
        print("WLLL", x_centers)
        return x_centers

    def find_peak_idx(self, data):
        return np.where(data == np.max(data))[0][0]


class LiveCounts:
    def __init__(self, base_url=None):
        if base_url:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(websocket_client(base_url, self.get_active_channels, n=1))  # finds which channels we collect from Retina setup
            self.nr_chs = self.found_channels.shape[0]   # self.nr_chs = 24
            self.ch_numbers = self.found_channels.copy()
            self.active_chs = {}
            for i in self.found_channels:
                self.active_chs[i] = True
            print(self.active_chs)

    def get_active_channels(self, payload):
        """
            message['mcuId']        # this is the retina driver number (e.g. mcuId = 1 or 2, if we have 2 retinas)
            message['cuId']         # for each driver, which channel number (cuId is between 1-12)
            message['cuStatus']     # ????
            message['rank']         # channel number in total (e.g. with 2 retinas and 12 channels each: rank is between 1-24)
            message = {'mcuId': 1, 'cuId': 10, 'cuStatus': 0, 'monitorV': -0.0006128550739958882, 'biasI': 0.0, 'inttime': 100, 'counts': 0, 'rank': 10, 'time': 1729066371.8}
        """
        self.payload = payload

        found_channels = []
        self.nr_chs = 0
        for message in payload:  # for every channel
            #if len(found_channels) > 15:
            #    continue
            found_channels.append(message['rank'])
            print(message)

        found_channels.sort()
        self.found_channels = np.array(found_channels)



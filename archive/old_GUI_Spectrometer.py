import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory
import serial
from serial.tools import list_ports
from datetime import date
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from matplotlib import style
# from matplotlib.backend_bases import key_press_handler

from WebSQControl import WebSQControl

from test_data import example_data_blue, example_data_red

# Packages for ETA backend
import json
import etabackend.eta  # Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/
import time

import os
from pathlib import Path

# TODO NOW:
#       - Define wavelengths for each detector (display on x axis plot, display next to channel?)
#  - Have Stephan show (on the WebSQ interface) how he wants the bias to be measured
#           --> execute the same using code below
#  - Simplify your current code to control the spectrometer
#  - Disable the ability to configure spectrometer (grating and so on) while running a scan (maybe?)

# TODO LATER:
#  - look into exceptions, plan for window crashing
#  - add settings and specs to datafile (create a separator to know at what row data starts!)
#  - Display the detection rates from the different pixels in a histrogram that will have an energy/wavelength scale
#  - Separate or remove demo mode
#  - live graph for all plots
#  - OBS: PLOTS SHOULD BE HISTOGRAMS
#  - Fix __exit__ method (find out how and why and what)
#  - search for available ports and ask to connect to correct one
#       --> make a "connection tab" to connect device first...
#       --> find out how to list available/active ports as options (dropdown list)
#  - fix "check device" layout
#  - add a tab with one button per command to read to device one by one, and display response??
#  - maybe add a thing (when pressing start scan button) that checks (reads) current device configs and
#           compares to desired. if not a match then abort scan
#  - make a print tab to the right where "progress" is being shown :)"
#  - ETA data saving and reading
#  - Display counts
#  - Add buttons for "setting" configurations (and indication/display of what is set)
#  - Add scrollbar for counts display (for when we have many)
#  - Add integration time
#  - self.params (defaults)  -->  Create config file where defaults can be saved and read from

class SQControl:
    """Class to control detector via WebSQ"""
    def __init__(self):
        # -------------- ARGUMENTS: --------------
        self.websq_handle = None

        # The control port (default 12000)
        self.control_port = 12000
        # The port emitting the photon Counts (default 12345)
        self.counts_port = 12345

        # Number of measurements, used when reading counts,  type=int
        self.N = 5

        self.websq_connect(nr_det=8)

        # OPTIONS TO IMPLEMENT IN GUI:
        # self.set_curr_bias()
        # self.set_trigger_lvl()
        # self.read_back()               # reads and prints: periode, bias, trigger
        # counts = self.get_counts(N=10)  # this returns both timestamps and counts per detector for N measurements

    def websq_connect(self, nr_det):
        if demo:
            self.websq_handle = True
            self.number_of_detectors = nr_det
            return
        try:
            # TCP IP Address of the detector (default 192.168.1.1)
            if nr_det == 4:
                self.tcp_ip_address = '192.168.35.236'  # for big lab wifi (4 channels that others use)
                self.number_of_detectors = 4
            else:
                self.tcp_ip_address = '192.168.120.119'  # for tiny lab wifi (8 channels for our spectrometer)
                self.number_of_detectors = 8
                if nr_det != 8:
                    print("ERROR: Other channel amount not available. Default set to 8.")

            self.websq_handle = WebSQControl(TCP_IP_ADR=self.tcp_ip_address, CONTROL_PORT=self.control_port, COUNTS_PORT=self.counts_port)
            self.websq_handle.connect()
            print(f"Connected to WebSQ on IP {self.tcp_ip_address}! Server with {self.number_of_detectors} detectors!")

            self.number_of_detectors = self.get_number_of_detectors()  # Returns how many channels/detectors we have in the system  # NOTE: required other functions!!
            self.set_integration_time(dt=100)  # Sets the integration time to collect counts in bin

            self.read_back()
        except:
            print("Connection error with WebSQ")
            self.websq_disconnect()
            raise

    def get_number_of_detectors(self):
        """Acquire number of detectors in the system"""
        n = self.websq_handle.get_number_of_detectors()
        print(f"     System as {n} detectors")
        return n

    def set_integration_time(self, dt=100):
        print(f"     Set integration time to {dt} ms")
        self.websq_handle.set_measurement_periode(dt)  # Time in ms

    def set_curr_bias(self):
        # Set the bias current
        # TODO: scan bias of detectors?
        bias = 0
        curr = []
        for n in range(self.number_of_detectors):
            curr.append(bias)
        print(f"Set bias to: {curr}")
        self.websq_handle.set_bias_current(current_in_uA=curr)

    def set_trigger_lvl(self):
        # Set the trigger level
        # TODO set some value (or a list of values)
        trigger = -150  # mV
        trig = []
        for n in range(self.number_of_detectors):
            trig.append(trigger)
        print(f"Set trigger levels to: {trig}")
        self.websq_handle.set_trigger_level(trigger_level_mV=trig)

    def get_counts(self, N=10):
        # Acquire N counts measurements:
        #   Returns an array filled with N numpy arrays each containing as first element a time stamp and then the detector counts ascending order

        #print(f"Acquiring {N} counts measurements...")
        all_counts = self.websq_handle.acquire_cnts(N)   # note: this includes the time stamp as well
        return all_counts

    def read_back(self):
        """
        Example:
            Measurement Periode (ms): 	 100
            Bias Currents in uA: 		 [-14.5, -16, -17.7, -12.4]
            Trigger Levels in mV: 		 [-150, -150, -150, -150]
        """
        print("\nRead back set values\n====================")
        print(f"Measurement Periode (ms):    {self.websq_handle.get_measurement_periode()}")
        print(f"Bias Currents in uA:         {self.websq_handle.get_bias_current()}")
        print(f"Trigger Levels in mV:        {self.websq_handle.get_trigger_level()}")

    def get_curr_bias(self):
        return self.websq_handle.get_bias_current()

    def get_curr_trigger(self):
        return self.websq_handle.get_trigger_level()

    def websq_disconnect(self):
        if demo:
            #self.websq_handle = None
            return
        try:
            self.websq_handle.close()
            self.websq_handle = None
            print("Connection closed with WebSQ")
        except:
            print("Failed close connection with WebSQ")
            raise

class SP2750:

    def __init__(self):

        # Serial connection settings:
        self.sp_handle = None
        self.acton_serial = 'FT5Z6FVRA'  # NOTE: this is for our device, and we use it to compare and find the port
        self.port = self.find_ports()    # USB PORT "COM4"
        self.dict = {
            'gratings list': {
                'value type': None,
                'cmd': "?GRATINGS",
                'access': ['read']
            },
            'grating' : {
                'value type': 'discrete',
                'values' : [1, 2, 3],
                'cmd' : "?GRATING",
                'access': ['read', 'write']
            },
            'nm': {
                'value type': 'range',
                'min': 300,
                'max': 900,                 # FIXME
                'cmd': "?NM",
                'access': ['read', 'write']

            },
            'nm/min': {
                'value type': 'range',
                'min': 100,                 # FIXME
                'max': 600,                 # FIXME
                'cmd': "?NM/MIN",           # FIXME
                'access': ['read', '']      # FIXME, NOTE: not fully implemented yet
            },
        }

        if demo:
            self.device_grating = 1
            self.device_wavelength = 600
        else:
            self.acton_connect()
            print(f"     Grating:    {self.read_cmd(param='grating', fb=False)}")
            print(f"     Wavelength: {self.read_cmd(param='nm', fb=False)}")

    def find_ports(self):  # TODO: find our device port and connect automatically
        """
        device:          COM4
        name:            COM4
        description:     USB Serial Port (COM4)
        hwid:            USB VID:PID=0403:6015 SER=FT5Z6FVRA
        vid:             1027
        pid:             24597
        serial_number:   FT5Z6FVRA
        location:        None
        manufacturer:    FTDI
        product:         None
        interface:       None
        """

        for port in serial.tools.list_ports.comports():
            if (port.serial_number == self.acton_serial) and (port.manufacturer == 'FTDI'):
                #print(f"FOUND ACTON DEVICE ON PORT {port.device}")
                return port.device
            """print(f'---------\n'
                  f'  device:          {port.device       }'
                  f'\nname:            {port.name         }'
                  f'\ndescription:     {port.description  }'
                  f'\nhwid:            {port.hwid         }'
                  f'\nvid:             {port.vid          }'
                  f'\npid:             {port.pid          }'
                  f'\nserial_number:   {port.serial_number}'
                  f'\nlocation:        {port.location     }'
                  f'\nmanufacturer:    {port.manufacturer }'
                  f'\nproduct:         {port.product      }'
                  f'\ninterface:       {port.interface    }'
                  f'\n---------')"""

    def acton_connect(self):
        if demo:   # TODO: i don't think this is needed
            self.sp_handle = True
            return

        try:
            self.sp_handle = serial.Serial(port=self.port, baudrate=9600, parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)  # , timeout=self.serial_timeout)
            if self.sp_handle.isOpen():
                print(f"Successfully connected Acton Spectrometer on UBS port '{self.port}'!")
                self.sp_handle.write(b'NO-ECHO\r')
                self.wait_for_read(fb=False)  # returns: b'  ok\r\n'
            else:
                print("ERROR: handle still None")
                raise serial.SerialException
        except serial.SerialException:
            print(f"ERROR: could not connect to PORT: {self.port}")
            if self.sp_handle:
                self.acton_disconnect()
            raise

    def acton_disconnect(self):
        if demo:
            return

        if self.sp_handle is None:
            print("Not connected to device --> don't need to disconnect")
            return

        self.sp_handle.close()
        self.sp_handle = None
        print("Connection closed with Acton Spectrometer!")

    def check_cmd(self, access, param, value=None):
        #print('checking cmd')
        # Check if parameter is correctly defined
        if param not in self.dict.keys():
            print(f"ERROR: unknown {access} param ({param})")
            return False

        if access not in self.dict[param]['access']:
            print(f"ERROR: MISSING {access} PRIVILEGES for {param}")
            return False

        if access == 'write':
            # Checks if desired value is ok to WRITE
            if self.dict[param]['value type'] == 'discrete':
                if int(value) not in self.dict[param]['values']:
                    print(f"ERROR: VALUE {value} NOT ALLOWED")
                    return False

            elif self.dict[param]['value type'] == 'range':
                if not (self.dict[param]['min'] <= float(value) <= self.dict[param]['max']):
                    print(f"ERROR: VALUE {value} NOT IN ALLOWED RANGE")
                    return False
            else:
                print(f"ERROR: UNKNOWN VALUE TYPE FOR {param}")
                return False

        return True

    def check_handle(self):
        #print('checking handle')

        if self.sp_handle is None:
            print("ERROR: Not connected to device!")
            return False
        elif not self.sp_handle.isOpen():
            print("ERROR: Device not open!")
            return False
        return True

    def read_cmd(self, param, fb=True):
        #print('read cmd')

        # Checks if desired command and value is ok to send
        if not self.check_cmd('read', param):
            return

        if demo:
            return Demo.d_read(param)

        if not self.check_handle():  # check if handle is ok
            return

        # print(f"\nReading {param}...")
        res = self.query(cmd=self.dict[param]['cmd'], fb=fb)

        # Extract value from response
        res_num = ''
        for char in res[1:].decode('ASCII'):
            if (char == ' ' and len(res_num) > 0) or (char == 'o'):
                return eval(res_num)
            res_num += char

        print("NOTE FOR JULIA! DIDN'T RETURN EARLY. CHECK WHY. ", res, ", ", res_num)  # remove later
        return eval(res_num)   # remove later

    def write_cmd(self, param, value):
        #print('write cmd')

        # Checks if desired command and value is ok to send
        if not self.check_cmd('write', param, value):
            return False

        if demo:
            Demo.d_write(param, value)
            return True

        if not self.check_handle():  # check if handle is ok
            return False

        res = self.query(cmd=f"{value} {self.dict[param]['cmd'][1:]}")

        if b'ok' in res:
            return True

        print('ERROR: bad response...')
        return False

    def query(self, cmd, fb=True):
        #print('query cmd')

        cmd_bytes = cmd.encode("ASCII") + b'\r'
        self.sp_handle.write(cmd_bytes)
        return self.wait_for_read(fb)

    def wait_for_read(self, fb=True):
        # print('wait for read')

        # reads response every second and waits until request is complete.
        res = b''
        for i in range(60):
            if b'ok' in res:
                if fb:
                    print('done reading')
                return res
            else:
                time.sleep(0.5)
                res_r = self.sp_handle.readline()
                # print(res_r)
                res += res_r
        print('failed wait to read')

class GUI:

    def __init__(self):
        self.temp_counter = 0   # REMOVE LATER USED TO TEST HISTO PLOTTING WITH SAMPLE DATA

        # FIXME TEMP HERE BUT HAVE IT UPDATE LIVE MAYBE OR CALL WITH BUTTON
        self.bins_ps, self.folded_countrate_pulses = eta.eta_lifetime_analysis()
        self.bins_ns = list(np.array(self.bins_ps) / 1000)  # changing values from picoseconds to nanoseconds

        print('------')
        self.sq = SQControl()

        # initialize communication class with spectrometer
        self.sp = SP2750()
        print('------')

        # Create and configure the main GUI window
        self.init_window()

        # define global variables
        self.init_parameters()

        # Create and place tabs frame on window grid
        self.init_fill_tabs()
        self.live_mode = True  # FIXME: add button to change this
        #if demo:
        #    self.root.after(100, lambda: _show('Title', 'Demo Version'))

    def init_parameters(self):
        # TODO: CHECK WHAT WE CAN REMOVE!!!
        self.data = []
        self.running = False  # this tracks if we are running a scan (collecting counts from detector)
        self.demo_connect = False  # temp for demo to check if we've actually connected to device
        self.current_file_name = None
        self.current_file_type = None
        self.current_file_path = None
        self.device_grating = 1
        self.device_wavelength = 600
        self.config_success = None   # None if not tried to configure yet
        self.checked_configs = False
        self.ok_to_send_list = []
        self.widgets = {}
        self.buttons = {}  # TODO: save all buttons here with key
        self.button_color = 'grey'  # default button colors
        self.port = tk.StringVar()     # note maybe change later when implemented
        self.x_label = tk.StringVar(value='λ [nm]')
        self.grating_lvl = {   # TODO: make this configurable?   # TODO fill in correct width (based on grating)
            1: {'grating': 600,  'blz': '750 nm', 'width': 8},
            2: {'grating': 150,  'blz': '800 nm', 'width': 4},
            3: {'grating': 1800, 'blz': 'H-VIS',  'width': 2},
        }
        self.params = {
            'grating':     {'var': tk.IntVar(value=1),   'type': 'radio',     'default': 1,   'value': [1, 2, 3]},
            'nm':          {'var': tk.IntVar(value=600), 'type': 'int entry', 'default': 350, 'value': [350, 650, 750]},
            'width_nm':    {'var': tk.IntVar(value=1),   'type': 'int entry', 'default': 10,  'value': [5, 15, 30]},
            'slit':        {'var': tk.IntVar(value=10),  'type': 'int entry', 'default': 10,  'value': [10, 20, 30]},
            'nr_pixels':   {'var': tk.IntVar(value=8),   'type': 'int entry', 'default': 8,   'value': [3, 8, 12]},
            'file_name':   {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},
            'folder_name': {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['~/Desktop/GUI/Data1', '~/Desktop/GUI/Data2', '~/Desktop/GUI/Data3']},
            'eta_recipe':  {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }
        self.load_params = {
            'grating':     {'var': tk.IntVar(value=1),   'type': 'radio',     'default': 1,   'value': [1, 2, 3]},
            'nm':          {'var': tk.IntVar(value=600), 'type': 'int entry', 'default': 350, 'value': [350, 650, 750]},
            'width_nm':    {'var': tk.IntVar(value=1),   'type': 'int entry', 'default': 10,  'value': [5, 15, 30]},
            'slit':        {'var': tk.IntVar(value=10),  'type': 'int entry', 'default': 10,  'value': [10, 20, 30]},
            'nr_pixels':   {'var': tk.IntVar(value=8),   'type': 'int entry', 'default': 8,   'value': [3, 8, 12]},
            'file_name':   {'var': tk.StringVar(value="..."), 'type': 'str entry', 'default': '...',  'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},
            'eta_recipe':  {'var': tk.StringVar(value="..."), 'type': 'str entry', 'default': '...',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }
        self.ch_bias_list = []
        self.ch_trig_list = []
        self.ch_nm_bin_edges = []  # TODO
        self.calculate_nm_bins()

    def init_window(self):
        self.root = tk.Tk()
        self.root.title("Quantum Spectrometer GUI - Ghostly matters")   # *Ghostly matters*
        # self.root.resizable(True, True)
        # self.root.config(background='#0a50f5')   # TODO figure out why colors don't work
        # self.root.geometry('1800x1200')

    def init_fill_tabs(self):

        def scan_tab(new_scan_tab):
            #new_scan_tab = ttk.Frame(tab)

            # ---- Start new scan TAB ----  NOTE this should include settings and prep
            start_tab = tk.Frame(new_scan_tab, relief=tk.RAISED, bd=2)   # frame to gather things to communicate with devices

            self.widgets['param_config'] = self.choose_param_configs_widget(new_scan_tab)
            self.widgets['live_spectrum'], button_frame = self.plot_live_histo(new_scan_tab)

            # sub frame:
            self.widgets['file_config'] = self.choose_file_configs_widget(start_tab)
            self.widgets['send_conf_button'] = self.send_param_configs_widget(start_tab)  # button to send cofigs
            self.widgets['start_scan_button'] = self.start_scan_widget(start_tab)  # button to send cofigs

            self.widgets['param_config'].grid(row=0, column=0, rowspan=100, sticky="news", padx=0, pady=0)
            start_tab.grid(row=0, column=1, columnspan=1, sticky="news", padx=0, pady=0)
            self.widgets['live_spectrum'].grid(row=2, column=1, columnspan=1, sticky="news", padx=0, pady=0)
            button_frame.grid(row=2, column=2, columnspan=1, sticky="news", padx=0, pady=0)

            tk.Label(start_tab, text='Device Communication', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news", padx=0, pady=0)
            self.widgets['file_config'].grid(row=1, column=0, sticky="news", padx=0, pady=0)  # in sub frame
            self.widgets['send_conf_button'].grid(row=1, column=1, sticky="news", padx=0, pady=0)  # in sub frame
            self.widgets['start_scan_button'].grid(row=1, column=2, sticky="news", padx=0, pady=0)  # in sub frame

            #tabControl.add(new_scan_tab, text='New Scan')

        def loadscan_tab(new_scan_tab):

            # ---- Start new scan TAB ----  NOTE this should include settings and prep
            start_tab = tk.Frame(new_scan_tab, relief=tk.RAISED, bd=2)   # frame to gather things to communicate with devices
            start_tab.grid(row=0, column=1, columnspan=1, sticky="news", padx=0, pady=0)

            self.widgets['load_live_spectrum'], button_frame = self.plot_live_histo(new_scan_tab)
            self.widgets['load_live_spectrum'].grid(row=2, column=1, columnspan=1, sticky="news", padx=0, pady=0)
            button_frame.grid(row=2, column=2, columnspan=1, sticky="news", padx=0, pady=0)

            # sub frame:
            self.widgets['load_file_config'] = self.choose_file_load_configs_widget(start_tab)
            self.widgets['load_file_config'].grid(row=1, column=0, sticky="news", padx=0, pady=0)  # in sub frame

            self.widgets['load_start_scan_button'] = self.start_scan_widget(start_tab)  # button to send cofigs
            self.widgets['load_start_scan_button'].grid(row=1, column=2, sticky="news", padx=0, pady=0)  # in sub frame

            tk.Label(start_tab, text='Settings', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news", padx=0, pady=0)


        def plot_spectrum_tab(tab):
            plots_spectrum = ttk.Frame(tab)

            plt_frame, button_frame = self.plot_spectrum_widget(plots_spectrum)
            self.widgets['plot_spectrum_1'] = plt_frame
            self.widgets['plot_spectrum_1'].grid(row=0, rowspan=4, column=0, sticky="nsew", padx=0, pady=0)

            self.widgets['info_spectrum'] = self.plot_display_info_widget(plots_spectrum, "Spectrum plot info")
            self.widgets['info_spectrum'].grid(row=0, rowspan=3, column=1, sticky="nsew" , padx=0, pady=0)

            self.widgets['button_spectrum_1'] = button_frame
            self.widgets['button_spectrum_1'].grid(row=3, column=1, sticky="nsew", padx=0, pady=0)

            tabControl.add(plots_spectrum, text='Spectrum Plot')

        def plot_correlation_tab(plots_correlation):
            #plots_correlation = ttk.Frame(tab)
            # TODO: add widgets
            pass
            #tabControl.add(plots_correlation, text='Correlation Plot')

        def plot_lifetime_tab(plots_lifetime):
            #plots_lifetime = ttk.Frame(tab)
            #tabControl.add(plots_lifetime, text='Lifetime Plot')
            # TODO: add widgets

            #plt_frame = self.plot_lifetime_widget(plots_lifetime)
            #plt_frame = self.plot_seaborn(plots_lifetime)
            plt_frame, butt_frame = self.plot_lifetime_widget(plots_lifetime)
            plt_frame.grid(row=2, column=1, columnspan=1, sticky="news", padx=0, pady=0)
            butt_frame.grid(row=2, column=2, columnspan=1, sticky="news", padx=0, pady=0)

        def plot_3d_lifetime_tab(plots_3d_lifetime):
            #plots_3d_lifetime = ttk.Frame(tab)
            #tabControl.add(plots_3d_lifetime, text='3D Lifetime Plot')
            # TODO: add widgets

            plt_frame = self.plot_3D_lifetime_widget(plots_3d_lifetime)
            plt_frame.grid(row=2, column=1, columnspan=1, sticky="news", padx=0, pady=0)

        def try_newscan():
            term = ttk.Frame(tabControl)  # create frame widget to go in program nb
            tabControl.add(term, text='New Scan')  # add the newly created frame widget to the program notebook
            nbName = ttk.Notebook(term)  # Create the notebooks to go in each of the terms frames
            nbName.pack(anchor='w')  # pack the notebook

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'  Acquisition')

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'  Lifetime')

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'  3D Lifetime')

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'  Correlation')

        def try_loadscan():

            term = ttk.Frame(tabControl)  # create frame widget to go in program nb
            tabControl.add(term, text='Load Scan')  # add the newly created frame widget to the program notebook
            nbName = ttk.Notebook(term)  # Create the notebooks to go in each of the terms frames
            nbName.pack(anchor='w')  # pack the notebook

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'Acquisition')
            loadscan_tab(course)

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'Lifetime')
            plot_lifetime_tab(course)   # note: temp moved to front for testing

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'3D Lifetime')
            plot_3d_lifetime_tab(course)

            course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            nbName.add(course, text=f'Correlation')
            plot_correlation_tab(course)

            #course = ttk.Frame(nbName)  # Create a course frame for the newly created term frame for each iter
            #nbName.add(course, text=f'* Spectrum')
            #plot_spectrum_tab(course)   # note: currently hiding this unless we want to being it back

        def settings_tab():  # FIXME
            settings_tab = ttk.Frame(tabControl)
            # TODO: add widgets
            tabControl.add(settings_tab, text='Settings')

        #col_not_selected = '#cedfe8'
        #col_selected = "#6da0bb"

        white = '#e7e7e9'
        lilac = '#bebed6'
        coral = '#ecdedb'
        skyblue = '#d5ddea'

        style1 = ttk.Style()
        style1.theme_create("style1", parent="alt", settings={
            "TNotebook":
                {"configure": {"tabmargins": [0, 0, 0, 0]}},

            "TNotebook.Tab":
                {
                    "configure": {
                        "padding": [10, 10],
                        "background": white,
                        "font": ('garamond', '11', 'bold')},
                    "map":  {
                        "background": [("selected", lilac), ('!active', white), ('active', coral)],
                        "expand": [("selected", [1, 1, 1, 0])]}}})

        style1.theme_use("style1")

        # Create notebook for multi tab window:
        tabControl = ttk.Notebook(self.root)
        tabControl.pack(expand=1, fill="both")

        try_loadscan()
        try_newscan()
        settings_tab()

        # NOTE: TEMP LIDAR:
        #plots_lidar_3d, plots_lidar = lid.plot_lidar_tab(tab=tabControl)
        #tabControl.add(plots_lidar_3d, text='3D Lidar Plot')
        #tabControl.add(plots_lidar, text='Lidar Plots')

        # ---- END TEMP LIDAR-----
    @staticmethod
    def add_to_grid(widg, rows, cols, sticky, columnspan=None):
        for i in range(len(widg)):
            if columnspan:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], padx=0, pady=0, columnspan=columnspan[i])
            else:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], padx=0, pady=0)

    @staticmethod
    def mark_done(widget, highlight="white", text_color='black', type='button'):   # light green = #82CC6C
        if type == 'text':
            widget.config(foreground=text_color)  # green
        elif type == 'button':
            widget.config(highlightbackground=highlight)  # green
            widget.config(foreground=text_color)  # green
            widget.config(activeforeground='blue')   #maybe only reset for send btn ???

    # NOTE TODO: make sure that we use the actual device grating and not the selected one.
    def calculate_nm_bins(self):
        self.ch_nm_bin_edges = []   # clear list of bins

        #print("device grating", self.device_grating)
        width_nm = self.grating_lvl[self.device_grating]['width']   # total width/range of all channels
        delta_nm = width_nm/self.sq.number_of_detectors
        center_nm = self.params['nm']['var'].get()
        n = self.sq.number_of_detectors

        for i in range(int(-n/2), int(n/2)+1):
            self.ch_nm_bin_edges.append(center_nm + (i*delta_nm))
        #print(self.ch_nm_bin_edges)

    def choose_param_configs_widget(self, tab):

        def press_connect():  # TODO
            #self.running = False  # TODO CHECK: need to stop scanning i think???

            if demo:
                Demo.d_connect(port_parts[2])
                self.sp.sp_handle = True
                return
                
            self.sp.acton_disconnect()
            self.sp.acton_connect()
            self.sp.sp_handle.write(b'NO-ECHO\r')
            self.sp.wait_for_read()  # b'  ok\r\n'
            port_parts[1].config(text=f'{self.sp.port}')

            if self.sp.sp_handle.isOpen():
                self.mark_done(port_parts[2], highlight="green", text_color='black', type='button')
            else:
                self.mark_done(port_parts[2], highlight="red", text_color='black', type='button')

        def reset_button_col():
            for button in default_but_parts[1:]:
                self.mark_done(button, highlight=self.button_color, type='button')

        def default_press(n=0):

            reset_button_col()
            if n == 0:
                for key in self.params.keys():
                    self.params[key]['var'].set(self.params[key]['default'])        # Clear all
            else:
                self.mark_done(default_but_parts[n], highlight='green', type='button')   # set one of the defaults
                for key in self.params.keys():
                    self.params[key]['var'].set(self.params[key]['value'][n-1])
                self.suggest_filename(self.name_entry)

            update_ch(self.sq.number_of_detectors)

        def select_grating():
            # FIXME OR REMOVE
            #self.calculate_nm_bins()
            # TODO: auto update plot axis
            pass

        def update_ch(nr_pixels):
            if nr_pixels not in [4, 8]:
                print("ERROR: other pixel amounts not available yet")
                return

            self.params['nr_pixels']['var'].set(nr_pixels)

            # removes previously shown channels (in case we want to decrease in amount)
            for j, widget in enumerate(frm['ch'].winfo_children()):   # FIXME NOTE TODO: USE THIS LATER TO ACCESS BUTTONS FOR MARKING DONE
                if j > 2:
                    widget.destroy()

            # Connecting to other/new WebSQ server
            self.sq.websq_disconnect()
            self.sq.websq_connect(nr_pixels)
            self.reset_histo_bins()
            fill_ch()

        def fill_ch():
            self.ch_bias_list = []
            self.pix_counts_list = []

            if demo:
                return

            device_bias = self.sq.get_curr_bias()
            device_trigger = self.sq.get_curr_trigger()

            for pix in range(self.params['nr_pixels']['var'].get()):
                self.ch_bias_list.append(tk.IntVar(value=device_bias[pix]))  # FIXME we are only displaying, not setting anything
                self.ch_trig_list.append(tk.IntVar(value=device_trigger[pix]))  # FIXME we are only displaying, not setting anything

                tk.Label(frm['ch'], text=f"{pix + 1}").grid(row=pix + 2, column=0, sticky="ew", padx=0, pady=0)
                tk.Entry(frm['ch'], bd=2, textvariable=self.ch_bias_list[pix], width=6).grid(row=pix + 2, column=1, sticky="ew", padx=0, pady=0)
                tk.Entry(frm['ch'], bd=2, textvariable=self.ch_trig_list[pix], width=6).grid(row=pix + 2, column=2, sticky="ew", padx=0, pady=0)

                #tk.Label(frm['ch'], text=f"0").grid(row=pix + 2, column=3, sticky="ew", padx=0, pady=0)  # counts
                c_temp = tk.Label(frm['ch'], text=f"0")
                c_temp.grid(row=pix + 2, column=3, sticky="ew", padx=0, pady=0)  # counts
                self.pix_counts_list.append(c_temp)

        # ---------------
        self.port.set(self.sp.port)  # note maybe change later when implemented

        # FRAMES
        frm_test = tk.Frame(tab, relief=tk.RAISED, bd=2)
        frm = {}
        for name in ['default', 'port', 'slit', 'grating', 'detect', 'ch']:
            frm[name] = tk.Frame(frm_test, relief=tk.RAISED, bd=2)

        # WIDGETS
        
        #  -- Default:
        default_but_parts = [
            tk.Button(frm['default'], text="Clear all", command=lambda: default_press(0), activeforeground='red', highlightbackground=self.button_color),
            tk.Button(frm['default'], text="Default 1", command=lambda: default_press(1), activeforeground='blue', highlightbackground=self.button_color),
            tk.Button(frm['default'], text="Default 2", command=lambda: default_press(2), activeforeground='blue', highlightbackground=self.button_color),
            tk.Button(frm['default'], text="Default 3", command=lambda: default_press(3), activeforeground='blue', highlightbackground=self.button_color),]

        #  -- Port:
        port_parts = [tk.Label(frm['port'], text='USB Port'),   # port_entry = tk.Entry(frm_port, bd=2, textvariable=self.port, width=5)   # FIXME later
                      tk.Label(frm['port'], text=f'{self.port.get()}'),
                      tk.Button(frm['port'], text="Connect Device", command=press_connect, activeforeground='blue', highlightbackground=self.button_color)]
        
        #  -- Slit:
        slt_parts = [tk.Label(frm['slit'], text='Slit width'),
                     tk.Entry(frm['slit'], bd=2, textvariable=self.params['slit']['var'], width=5),
                     tk.Label(frm['slit'], text='[um]')]

        #  -- Grating:
        grating_widget_dict = {
            'radio_b' : [],
            'grt_txt': [tk.Label(frm['grating'], text='Grating')],
            'blz_txt': [tk.Label(frm['grating'], text='Blaze')],
            'wid_txt': [tk.Label(frm['grating'], text='Width')],
        }
        for c in range(3):
            #grating_widget_dict['radio_b'].append(tk.Radiobutton(frm['grating'], text=f"{self.grating_lvl[i+1]['grating']}  [gr/mm]", variable=self.params['grating']['var'], value=i+1, command=select_grating))
            grating_widget_dict['radio_b'].append(tk.Radiobutton(frm['grating'], text="", variable=self.params['grating']['var'], value=c+1, command=select_grating))
            grating_widget_dict['grt_txt'].append(tk.Label(frm['grating'], text=f"  {self.grating_lvl[c+1]['grating']}  [gr/mm]"))
            grating_widget_dict['blz_txt'].append(tk.Label(frm['grating'], text=f"  {self.grating_lvl[c+1]['blz']}"))
            grating_widget_dict['wid_txt'].append(tk.Label(frm['grating'], text=f"  {self.grating_lvl[c+1]['width']}"))

        #  -- Detector:
        det_parts = [tk.Label(frm['detect'], text="Center λ"),
                     tk.Entry(frm['detect'], bd=2, textvariable=self.params['nm']['var'], width=4),
                     tk.Label(frm['detect'], text='[nm]', width=4)]

        wid_parts = [tk.Label(frm['detect'], text="Pixel width"),
                     tk.Entry(frm['detect'], bd=2, textvariable=self.params['width_nm']['var'], width=6),
                     tk.Label(frm['detect'], text='[nm]')]

        """det_no_parts = [tk.Label(frm['detect'], text="Nr. of pixels"),
                        tk.Entry(frm['detect'], bd=2, textvariable=self.params['nr_pixels']['var'], width=6),
                        tk.Button(frm['detect'], text="Update", command=update_ch, activeforeground='blue', highlightbackground=self.button_color)]"""

        det_no_parts = [tk.Label(frm['detect'], text="Nr. of pixels"),
                        tk.Button(frm['detect'], text="4", command=lambda : update_ch(4), activeforeground='blue', highlightbackground=self.button_color),
                        tk.Button(frm['detect'], text="8", command=lambda : update_ch(8), activeforeground='blue', highlightbackground=self.button_color)]

        # -- Channels:
        ch_parts = [
            tk.Label(frm['ch'], text='Pixel'),
            tk.Label(frm['ch'], text='Bias (uA)'),
            tk.Label(frm['ch'], text='Trigger (mV)'),
            tk.Label(frm['ch'], text='Counts')]

        # GRID
        # -- Default
        self.add_to_grid(widg=default_but_parts, rows=[0,0,0,0], cols=[0,1,2,3], sticky=["ew", "ew", "ew", "ew"])
        # -- Port
        self.add_to_grid(widg=port_parts, rows=[0,0,0], cols=[0,1,2], sticky=["", "", ""])
        # -- Slit
        self.add_to_grid(widg=slt_parts, rows=[0,0,0], cols=[0,1,2], sticky=["", "", ""])
        # -- Grating
        self.add_to_grid(widg=grating_widget_dict['radio_b'], rows=[3,4,5], cols=[0,0,0], sticky=["", "s", "s", "s"])
        self.add_to_grid(widg=grating_widget_dict['grt_txt'], rows=[2,3,4,5], cols=[1,1,1,1], sticky=["", "s", "s", "s"])
        self.add_to_grid(widg=grating_widget_dict['blz_txt'], rows=[2,3,4,5], cols=[2,2,2,2], sticky=["", "s", "s", "s"])
        self.add_to_grid(widg=grating_widget_dict['wid_txt'], rows=[2,3,4,5], cols=[3,3,3,3], sticky=["", "s", "s", "s"])

        # -- Detector
        self.add_to_grid(widg=[tk.Label(frm['detect'], text="Detector")], rows=[0], cols=[0], sticky=["ew"])  # , columnspan=[2])
        self.add_to_grid(widg=det_parts, rows=[1,1,1], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        # self.add_to_grid(widg=wid_parts, rows=[2,2,2], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        self.add_to_grid(widg=det_no_parts, rows=[3,3,3], cols=[0,1,2], sticky=["ew", "ew", "ew"])

        # -- Channels
        self.add_to_grid(widg=ch_parts, rows=[0,0,0,0,0], cols=[0,1,2,3,4], sticky=["ew", "ew", "ew", "ew"])
        fill_ch()  # Updates channels displayed

        # ------------- COMBINING INTO TEST FRAME --------------

        tk.Label(frm_test, text='Settings', font=('', 15)).grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.add_to_grid(widg=[frm['default'], frm['port'], frm['slit'], frm['grating'], frm['detect']], rows=[1,2,3,4,5], cols=[0,0,0,0,0], sticky=["ew", "ew", "ew", "ew", "ew"])
        frm['ch'].grid(row=6, column=0, rowspan=100, sticky="ew", padx=0, pady=0)

        return frm_test

    def suggest_filename(self, entry):
        entry.delete(0, tk.END)
        currDate = date.today().strftime("%y%m%d")
        currTime = time.strftime("%Hh%Mm%Ss", time.localtime())
        temp = f"slit({self.params['slit']['var'].get()})_" \
               f"grating({self.params['grating']['var'].get()})_" \
               f"lamda({self.params['nm']['var'].get()})_" \
               f"pixels({self.params['nr_pixels']['var'].get()})_" \
               f"date({currDate})_time({currTime}).timeres"
        self.params['file_name']['var'].set(temp)
        entry.insert(0, temp)

    def choose_file_configs_widget(self, tab):

        def suggest_name():
            self.suggest_filename(file_entry[0])

        def get_folder():
            file_entry[1].delete(0, tk.END)
            self.params['folder_name']['var'].set(askdirectory())
            file_entry[1].insert(0, self.params['folder_name']['var'].get())

        def get_recipe():
            file_entry[2].delete(0, tk.END)
            self.params['eta_recipe']['var'].set(askopenfilename(filetypes=[("ETA recipe", "*.eta")]) )
            file_entry[2].insert(0, self.params['eta_recipe']['var'].get())

        frm_misc = tk.Frame(tab, relief=tk.RAISED, bd=2)

        file_lab_parts = []
        file_entry = []
        for i, label in enumerate(["New File Name", "New File Location", "ETA recipe"]):
            file_lab_parts.append(tk.Label(frm_misc, text=label))
            file_entry.append(tk.Entry(frm_misc, bd=2, textvariable=self.params[['file_name', 'folder_name', 'eta_recipe'][i]]['var'], width=20))

        file_buts = [tk.Button(frm_misc, text="Suggest...", command=suggest_name, activeforeground='blue', highlightbackground=self.button_color),
                     tk.Button(frm_misc, text="Open Folder", command=get_folder, activeforeground='blue', highlightbackground=self.button_color),
                     tk.Button(frm_misc, text="Choose File", command=get_recipe, activeforeground='blue', highlightbackground=self.button_color)]

        self.name_entry = file_entry[0]
        tk.Label(frm_misc, text="Analysis Configs").grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        self.add_to_grid(widg=[tk.Label(frm_misc, text="(optional)")], rows=[0], cols=[2], sticky=["ew"])
        self.add_to_grid(widg=file_lab_parts, rows=[1,2,3], cols=[0,0,0], sticky=["ew","ew","ew","ew"])
        self.add_to_grid(widg=file_entry, rows=[1,2,3], cols=[1,1,1], sticky=["ew", "ew", "ew"])
        self.add_to_grid(widg=file_buts, rows=[1,2,3], cols=[2,2,2], sticky=["ew", "ew", "ew"])

        return frm_misc

    def choose_file_load_configs_widget(self, tab):

        def get_file():
            file_entry.delete(0, tk.END)
            self.load_params['file_name']['var'].set(askopenfilename(filetypes=[("Timeres datafile", "*.timeres")]))
            file_entry.insert(0, self.load_params['file_name']['var'].get())

        def get_recipe():
            recipe_entry.delete(0, tk.END)
            self.load_params['eta_recipe']['var'].set(askopenfilename(filetypes=[("ETA recipe", "*.eta")]))
            recipe_entry.insert(0, self.load_params['eta_recipe']['var'].get())

        frm_misc = tk.Frame(tab, relief=tk.RAISED, bd=2)

        file_lab_parts = [
            tk.Label(frm_misc, text='Datafile'),
            tk.Label(frm_misc, text='ETA recipe')]

        file_entry = tk.Entry(frm_misc, bd=2, textvariable=self.load_params['file_name']['var'], width=20)
        recipe_entry = tk.Entry(frm_misc, bd=2, textvariable=self.load_params['eta_recipe']['var'], width=20)

        file_buts = [
            tk.Button(frm_misc, text="Choose File", command=get_file, activeforeground='blue', highlightbackground=self.button_color),
            tk.Button(frm_misc, text="Choose File", command=get_recipe, activeforeground='blue', highlightbackground=self.button_color)]

        tk.Label(frm_misc, text="Analysis Configs").grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        self.add_to_grid(widg=file_lab_parts, rows=[1,2], cols=[0,0], sticky=["ew","ew"])
        self.add_to_grid(widg=[file_entry, recipe_entry], rows=[1,2], cols=[1,1], sticky=["ew", "ew"])
        self.add_to_grid(widg=file_buts, rows=[1,2], cols=[2,2], sticky=["ew", "ew"])

        return frm_misc

    def send_param_configs_widget(self, tab):

        def nothing():
            print("WARNING: CHECK YOUR VALUES BEFORE SENDING TO DEVICE")

        def get_str():
            temp2 = f"grating = {self.device_grating} --> {self.params['grating']['var'].get()} [gr/mm]"
            temp3 = f"center λ = {self.device_wavelength} --> {self.params['nm']['var'].get()} [nm]"
            return ['', temp2, temp3]

        def show_configs():
            temp = get_str()
            for i, widget in enumerate(send_txt):
                widget.config(text=temp[i], foreground='black')   # make green for passed tests!

        def check():
            print('check device')
            show_configs()
            self.ok_to_send_list = []  # reset
            # todo: maybe should also check connection and values on device (if active/correct)
            check_list = [
                    ['grating', 0, send_txt[1], 'grating', self.device_grating],
                    ['nm',      0, send_txt[2], 'center λ', self.device_wavelength],
                ]
            for check_thing in check_list:

                if demo and (not self.demo_connect):
                    print('not demo connect')
                    tempi = ''
                    check_thing[2].config(text=tempi, foreground='black')  # make green for passed tests!
                    self.mark_done(check_thing[2], text_color='red', type='text')  # ????
                    continue  # skip rest of loop iteration

                res = self.sp.read_cmd(param=check_thing[0])  # returns true if correctly configured
                print(" value =", res)

                tempi = f"{check_thing[3]} = {res}  -->  {self.params[check_thing[0]]['var'].get()}"

                check_thing[2].config(text=tempi, foreground='black')  # make green for passed tests!

                if res is None:
                    self.mark_done(check_thing[2], text_color='red', type='text')  # ????

                elif self.params[check_thing[0]]['var'].get() is None:  # note: checks if right value is set
                    self.mark_done(check_thing[2], text_color='blue', type='text')  # passed test (temp)
                    self.ok_to_send_list.append(check_thing)

                elif round(float(res)) == round(float(self.params[check_thing[0]]['var'].get())):  # note: checks if right value is set
                    self.mark_done(check_thing[2], text_color='green', type='text')  # passed test (temp)

                else:
                    # note: new value available!!
                    #print('res:', round(float(res)), '==', round(float(check_thing[1])), ':val')
                    self.mark_done(check_thing[2], text_color='blue', type='text')  # failed test (temp)
                    self.ok_to_send_list.append(check_thing)

                check_thing[4] = res  # TODO CHECK!!

            self.checked_configs = True
            self.suggest_filename(self.name_entry)

            if not self.demo_connect:  # TODO CHECK
                self.mark_done(btn_send_conf, highlight='red', type='button')
            elif len(self.ok_to_send_list) > 0:
                self.mark_done(btn_send_conf, text_color='black', highlight='blue', type='button')
            else:
                self.mark_done(btn_send_conf, text_color='black', highlight='green', type='button')

            btn_send_conf.config(command=send)   # ACTIVATES SEND OPTION

        def send():
            self.suggest_filename(self.name_entry)
            if demo:
                if not self.demo_connect:
                    self.mark_done(btn_send_conf, highlight='red', type='button')
                    # return ???
                else:
                    time.sleep(1)

            if self.running:
                print("can not config during scan")
                return

            print("Attempting to send configs to device...")
            if self.checked_configs:  # if we've double-checked currently set values      
                self.mark_done(btn_send_conf, highlight=self.button_color, type='button')

                #try:   # woking parts will be marked green
                self.config_success = True

                if len(self.ok_to_send_list) == 0:
                    print("No values need updating!")
                    return

                for thing in self.ok_to_send_list:
                    success = self.sp.write_cmd(param=thing[0], value=self.params[thing[0]]['var'].get())   # returns true if correctly configured

                    if success:   # true or false
                        self.mark_done(thing[2], text_color='green', type='text')  # passed test (temp)

                    else:
                        self.mark_done(thing[2], text_color='red', type='text')   # failed test (temp)
                        self.config_success = False

                if self.config_success:  # if all succeed to be configured
                    self.mark_done(btn_send_conf, highlight='green', type='button')
                else:
                    self.mark_done(btn_send_conf, highlight='red', type='button')
            else:
                self.mark_done(btn_send_conf, highlight='red', type='button')

            check()
            self.reset_histo_bins()
            print('done')

        temp = get_str()

        frm_send = tk.Frame(tab, relief=tk.RAISED, bd=2)
        frm_send_values = tk.Frame(frm_send, relief=tk.RAISED, bd=2)

        send_txt = [
            tk.Label(frm_send_values, text=temp[0], foreground='white', justify="left"),
            tk.Label(frm_send_values, text=temp[0], foreground='white', justify="left"),
            tk.Label(frm_send_values, text=temp[1], foreground='white', justify="right")]

        btn_check_conf = tk.Button(frm_send, text="Check values..", command=check, activeforeground='blue', highlightbackground=self.button_color)
        btn_send_conf = tk.Button(frm_send,  text="Send to Device", command=nothing, foreground='white', activeforeground='white')  # , highlightbackground=self.button_color)

        self.add_to_grid(widg=[btn_check_conf, frm_send_values, btn_send_conf], rows=[0,1,2], cols=[0,0,0], sticky=["new", "new", "new"])
        self.add_to_grid(widg=send_txt, rows=[0,1,2], cols=[0,0,0], sticky=["new", "new", "new"])

        return frm_send

    def get_counts(self):
        if demo:
            counts = Demo.d_get_counts()
        else:
            n = 1
            counts = self.sq.get_counts(n)   # TODO: make number of measurements a variable?

        # TODO: do something with timestamps  #timestamps = []   # resetting here means we are only getting the timestamps for current measurement of size N
        if self.live_mode:
            self.cumulative_ch_counts = np.zeros(self.sq.number_of_detectors)

        for row in counts:
            # timestamps.append(row[0])
            self.data.append(row[1:])
            self.cumulative_ch_counts += np.array(row[1:])

        # Displaying current counts next to bias configs
        for idx, val in enumerate(self.cumulative_ch_counts):
            self.pix_counts_list[idx].config(text=f"{int(val)}")

    def scanning(self):

        if self.running:   # if start button is active
            self.get_counts()  # saves data to self.data. note that live graph updates every second using self.data
            self.save_data(mode="a")
        self.root.after(500, self.scanning)  # After 1 second, call scanning

    def save_data(self, mode):
        data_str = []
        for row in self.data:
            vals = [str(int(x)) for x in row]
            data_str.append(' '.join(vals)+' \n')
        with open("counts_file.txt", mode) as file:   # FIXME need to make sure that new scan => new/empty file
            file.writelines(data_str)  # TODO maybe add time of each
        self.data = []  # removing data that is now saved in file

    def start_scan_widget(self, tab):

        def press_start():
            print(self.sp.sp_handle)
            print(self.sq.websq_handle)
            if (not self.sp.sp_handle) or (not self.sq.websq_handle):
                print("Can not start scan if we are not connected")
                self.running = False
                return

            self.save_data(mode="w")   # TODO: maybe only have this once per new measurement (so that we can pause and start again)
            # True:     if we have successfully configured the device
            # False:    failed to do all configs to device, should not start scan
            # None:     did not send new configs, will check but can start scan anyway (maybe??)
            outcome = {True : 'green', False : 'red', None : 'grey'}
            self.mark_done(btn_start, highlight=outcome[self.config_success], type='button')
            self.mark_done(btn_stop, highlight=self.button_color, type='button')
            self.running = True

        def press_stop():
            self.running = False
            self.mark_done(btn_start, highlight=self.button_color, type='button')
            self.mark_done(btn_stop, highlight='red', type='button')

        frm_send = tk.Frame(tab, relief=tk.RAISED, bd=2)
        btn_start = tk.Button(frm_send, text="Start\nScan", command=press_start, activeforeground='blue', highlightbackground=self.button_color, height=5, width=12)
        btn_stop = tk.Button(frm_send, text="Stop", command=press_stop, activeforeground='blue', highlightbackground=self.button_color, height=7, width=8)
        btn_start.grid(row=0, rowspan=4, column=0, sticky="nsew", padx=0, pady=1.5)
        btn_stop.grid(row=0, rowspan=4, column=1, sticky="nsew", padx=0, pady=1.5)

        return frm_send

    @staticmethod
    def pack_plot(tab, fig):

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)
        canvas = FigureCanvasTkAgg(fig, master=plt_frame)  # self.root)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        # creating the Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, plt_frame)  # self.root)
        toolbar.update()

        # placing the toolbar on the Tkinter window
        canvas.get_tk_widget().pack()

        return plt_frame, canvas

    def reset_histo_bins(self):
        self.calculate_nm_bins()
        self.cumulative_ch_counts = np.zeros(self.sq.number_of_detectors)
        self.temp_counter = 0
        self.y_max.set(value=1000)

    def plot_live_histo(self, tab):

        def press_live():
            if self.live_mode == True:
                # change to cumulative mode
                self.live_mode = False
                #live_button.config(text='Change to Live mode      ')

            else:
                # change to live mode
                self.live_mode = True
                #live_button.config(text='Change to Cumulative mode')
        def press_set_y_max():

            if self.y_max_entry.get() == "":
                self.y_max.set(value=50)

                # Check if we need to rescale y axis
                thresh = int(np.ceil(1.2*max(self.cumulative_ch_counts) / 100.0)) * 100
                if self.y_max.get() < thresh:
                    self.y_max.set(value=thresh)
            else:
                self.y_max.set(value=eval(self.y_max_entry.get()))

        def make_buttons():
            # BUTTONS:
            butt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)

            tk.Label(butt_frame, text=f'Change X-axis to:').grid(row=0, column=0, sticky="e")
            tk.Radiobutton(butt_frame, text="wavelength     [nm]  ", anchor="w", value='λ [nm]',    variable=self.x_label, command=pressed_xlabel_h).grid(row=1, column=0, sticky="e", padx=0, pady=0)
            tk.Radiobutton(butt_frame, text="frequency      [Hz]  ", anchor="w", value='f [Hz]',    variable=self.x_label, command=pressed_xlabel_h).grid(row=2, column=0, sticky="e", padx=0, pady=0)
            tk.Radiobutton(butt_frame, text="photon energy  [eV]  ", anchor="w", value='E [eV]',    variable=self.x_label, command=pressed_xlabel_h).grid(row=3, column=0, sticky="e", padx=0, pady=0)
            tk.Radiobutton(butt_frame, text="wave number    [1/cm]", anchor="w", value='v [1/cm]', variable=self.x_label, command=pressed_xlabel_h).grid(row=4, column=0, sticky="e", padx=0, pady=0)

            #live_butt = tk.Button(butt_frame, text="Live plot", command=press_live, activeforeground='blue', highlightbackground=self.button_color)
            #live_butt.grid(row=5, column=0, sticky="ew", padx=0, pady=0)
            tk.Label(butt_frame, text=f'Ceiling', anchor="w").grid(row=6, column=0, sticky="e")
            tk.Entry(butt_frame, bd=2, textvariable=self.y_max_entry, width=6).grid(row=6, column=1, sticky="e", padx=0, pady=0)
            tk.Button(butt_frame, text="Set y max", command=press_set_y_max).grid(row=6, column=2, sticky="ew", padx=0, pady=0)

            tk.Button(butt_frame, text="reset plot", command=clear_histo).grid(row=7, column=0, sticky="ew", padx=0, pady=0)

            return butt_frame#, live_butt

        def clear_histo():
            self.reset_histo_bins()
            x = np.array(self.ch_nm_bin_edges[:self.sq.number_of_detectors])  # todo:  change this to re a list of the wavelengths note the last channel is fake

            N, bins, bars = plot_histo(x_i=x, bins_i=self.ch_nm_bin_edges, weights_i=self.cumulative_ch_counts)

            return N, bins, bars

        def plot_histo(x_i, bins_i, weights_i):
            if self.y_max_entry.get() == "":
                press_set_y_max()

            fig.clear()
            plot1 = fig.add_subplot(111)
            plot1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%1.0f'))
            plot1.set_xlabel(self.x_label.get())
            plot1.set_ylabel('photon count')
            plot1.set_title("Intensity")
            plot1.set_ylim([0, self.y_max.get()])

            N, bins, bars = plot1.hist(x_i, bins=bins_i, weights=weights_i, rwidth=0.9, align='mid')
            plot1.bar_label(bars)
            canvas.draw()
            return N, bins, bars

        def update_histo():

            # fixme: reset x to match device grating
            #x = np.array(self.ch_nm_bin_edges[:self.sq.number_of_detectors])  # todo:  change this to re a list of the wavelengths note the last channel is fake

            bins_temp = convert_values_h(self.ch_nm_bin_edges)
            weight_temp = list(self.cumulative_ch_counts)

            if bins_temp[1]-bins_temp[0] < 0:  # decreasing order
                #print("reversed")
                bins_temp.reverse()
                weight_temp.reverse()

            x_temp = bins_temp[:-1]

            N, bins, bars = plot_histo(x_i=x_temp, bins_i=bins_temp, weights_i=weight_temp)

            # go to idle state if we are not running a scan (reading counts)
            if not self.running:
                self.root.after(1000, idle)   # updates every second todo: maybe change
            else:
                self.root.after(500, update_histo)   # updates every second todo: maybe change

        def idle():
            # go back to plotting counts when running scan (from idle state)
            if self.running:
                self.root.after(500, update_histo)  # updates every second todo: maybe change
            else:
                self.root.after(1000, idle)  # updates every second todo: maybe change

        def pressed_xlabel_h():  # TODO: add data conversion for respective unit
            update_histo()

        def convert_values_h(bins_in):
            unit = self.x_label.get()

            if unit == "λ [nm]":
                bins_temp = [value for value in bins_in]

            elif unit == "f [Hz]":
                c = 2.99792458e9
                bins_temp = [c/(value*1e-9) for value in bins_in]  #

            elif unit == "E [eV]":
                bins_temp = [1240/value for value in bins_in]

            elif unit == "v [1/cm]":
                bins_temp = [1 / (value_nm * 1e-7) for value_nm in bins_in]

            else:
                print("ERROR: UNKNOWN LABELS")
                bins_temp = [value for value in bins_in]

            return bins_temp

        # --------
        self.y_max_entry = tk.StringVar(value="")
        self.y_max = tk.IntVar(value=1000)

        x = np.array(self.ch_nm_bin_edges[:self.sq.number_of_detectors])   # todo:  change this to re a list of the wavelengths note the last channel is fake
        self.cumulative_ch_counts = np.zeros(self.sq.number_of_detectors)  # starting with 8 channels for now

        fig = plt.Figure(figsize=(9, 5), dpi=100)
        plt_frame, canvas = self.pack_plot(tab, fig)  # FIXME: or maybe after plotting histo?

        # N, bins, bars = plot_histo(x_i=x, bins_i=self.ch_nm_bin_edges, weights_i=self.cumulative_ch_counts)  # placeholder??? # TODO CHECK IF WE NEED PLACEHOLDER
        N, bins, bar = clear_histo()
        update_histo()

        # butt_frame, live_button = make_buttons()
        butt_frame = make_buttons()

        return plt_frame, butt_frame

    def plot_spectrum_widget(self, tab):
        # TODO: make it live? live graph???

        def convert_values():
            unit = self.x_label.get()

            if unit == "λ [nm]":
                x = [value for value in xar_b]

            elif unit == "f [Hz]":
                c = 2.99792458e9
                x = [c/(value*1e-9) for value in xar_b]

            elif unit == "E [eV]":
                x = [1240/value for value in xar_b]

            elif unit == "v [1/cm]":
                x = [1/(value_nm*1e-7) for value_nm in xar_b]

            else:
                print("ERROR NOT FOUND")
                x = []

            return x

        def pressed_xlabel():  # TODO: add data conversion for respective unit
            fig.clear()
            plot1 = fig.add_subplot(111)

            x = convert_values()

            plot1.plot(x, yar_b, 'b')
            #plot1.plot(xar_r, yar_r, 'r')
            plot1.set_xlabel(self.x_label.get())
            plot1.set_ylabel("counts")
            plot1.set_title("Spectrum")
            canvas.draw()

        self.x_label.set('λ [nm]')
        # the figure that will contain the plot
        fig = plt.Figure(figsize=(10, 6), dpi=50)
        xar_b = []
        yar_b = []
        xar_r = []
        yar_r = []

        len_b = len(example_data_blue)
        len_r = len(example_data_red)
        # ---temp
        for i in range(len_b):
            xar_b.append(example_data_blue[i][0])
            yar_b.append(example_data_blue[i][1])
        for i in range(len_r):
            xar_r.append(example_data_red[i][0])
            yar_r.append(example_data_red[i][1])
        # ---

        # style.use('ggplot')
        fig = plt.Figure(figsize=(9, 5), dpi=100)
        plot1 = fig.add_subplot(111)
        plot1.set_xlim(1545, 1565)
        plot1.set_ylim(0, 5000)
        line_b, = plot1.plot(xar_b, yar_b, 'b')  # , marker='o')
        plot1.set_xlabel(self.x_label.get())
        plot1.set_ylabel("counts")
        plot1.set_title("Spectrum")

        plt_frame, canvas = self.pack_plot(tab, fig)

        # BUTTONS:
        butt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(butt_frame, text=f'Change X-axis to:').grid(row=0, column=0, sticky="nsew")
        tk.Radiobutton(butt_frame, text="wavelength [nm]", value='λ [nm]', variable=self.x_label, command=pressed_xlabel).grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="frequency [Hz]", value='f [Hz]', variable=self.x_label, command=pressed_xlabel).grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="photon energy [eV]", value='E [eV]', variable=self.x_label, command=pressed_xlabel).grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="wave number [cm^{-1}]", value='v [1/cm]', variable=self.x_label, command=pressed_xlabel).grid(row=4, column=0, sticky="ew", padx=0, pady=0)

        return plt_frame, butt_frame

    def plot_correlation_widget(self, tab):
        # TODO:
        # the figure that will contain the plot
        fig = plt.Figure(figsize=(10, 3), dpi=100)
        # data list
        y = []
        # adding the subplot
        plot1 = fig.add_subplot(111)
        # plotting the graph
        plot1.plot(y)

        plt_frame, canvas = self.pack_plot(tab, fig)
        return plt_frame

    def plot_lifetime_widget(self, tab):

        def make_time_scale_button():
            butt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)

            butt_frame_t = tk.Frame(butt_frame, bd=2)

            tk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            tk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")

            tk.Label(butt_frame_t, text=f'X').grid(row=2, column=0, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew", padx=0, pady=0)
            tk.Entry(butt_frame_t, bd=2, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew", padx=0, pady=0)

            tk.Label(butt_frame_t, text=f'Y').grid(row=3, column=0, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=cnt_min, width=6).grid(row=3, column=1, sticky="ew", padx=0, pady=0)
            tk.Entry(butt_frame_t, bd=2, textvariable=cnt_max, width=6).grid(row=3, column=2, sticky="ew", padx=0, pady=0)

            tk.Button(butt_frame_t, text="Update", command=update_plot).grid(row=4, column=0, columnspan=3, sticky="ew", padx=0,  pady=0)

            butt_frame_s = tk.Frame(butt_frame, relief=tk.RAISED, bd=2)

            tk.Label(butt_frame_s, text="Show Channels:").grid(row=2, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
            tk.Entry(butt_frame_s, bd=2, textvariable=range_list, width=6).grid(row=3, column=0, columnspan=1, sticky="ew", padx=0, pady=0)
            tk.Button(butt_frame_s, text=f"Update range", highlightbackground='white', command=range_show).grid(row=3, column=1, columnspan=1, sticky="ew", padx=0, pady=0)

            butt_frame_p = tk.Frame(butt_frame, relief=tk.RAISED, bd=2)
            tk.Label(butt_frame_p, text=f'Plot scale').grid(row=0, column=0, columnspan=2, sticky="ew")
            self.scale_buttons = {
                'linear':       tk.Button(butt_frame_p, text="Linear", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                'histo':        tk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                'log':          tk.Button(butt_frame_p, text="Semi-Log", command=lambda: press_scale_plot('log')),
            }

            for i, thing in enumerate(self.scale_buttons.values()):
                if i == 3:  # filtered semilog
                    thing.grid(row=i + 1, column=0, sticky="ew", padx=0, pady=0)
                else:
                    thing.grid(row=i+1, column=0, columnspan=2, sticky="ew", padx=0,  pady=0)

            butt_frame_t.grid(row=0, column=0, sticky="news")
            butt_frame_s.grid(row=1, column=0, sticky="news")
            butt_frame_p.grid(row=2, column=0, sticky="news")

            return butt_frame

        def range_show():

            range_is_ok_bool = True

            range_str = range_list.get()
            range_str_list = range_str.split(sep=',')
            range_str_list_list = [x.split('-') for x in range_str_list]
            range_list_int = [[eval(x.strip(' ')) for x in pair] for pair in range_str_list_list]
            print("final range list", range_list_int)

            for i in range(len(range_list_int)-1):

                if len(range_list_int[i]) < 2:
                    print("note single value")
                    continue
                # check if ranges overlap:    1-6, 4-8, 9-99
                elif range_list_int[i][1] >= range_list_int[i+1][0]:
                    print(f"Error: overlap, {range_list_int[i][1]} >= {range_list_int[i + 1][0]}")
                    range_is_ok_bool = False
                else:
                    pass
                    #print(f"OK i={i}, {range_list_int[i][1]} < {range_list_int[i + 1][0]}")

            # check if any channels are invalid
            min_ch = 1
            max_ch = 4
            for i in range(len(range_list_int)):
                if len(range_list_int[i]) == 0:
                    range_is_ok_bool = False
                elif len(range_list_int[i]) < 2:
                    print("note single value")
                    if (range_list_int[i][0] < min_ch) or (range_list_int[i][0] > max_ch):
                        range_is_ok_bool = False
                elif range_list_int[i][0] >= range_list_int[i][1]:
                    print("error: not increasing range")
                    range_is_ok_bool = False
                elif (range_list_int[i][0] < min_ch) or (range_list_int[i][1] > max_ch):
                    print("error: channel in range is out of range")
                    range_is_ok_bool = False

            if range_is_ok_bool:  # if not errors!
                print("Range if good, ok to plot")

                # start by setting all to false
                for key in self.ch_show.keys():
                    self.ch_show[key] = False

                # set true for channels given in range
                for pair in range_list_int:
                    if len(pair) == 1:
                        self.ch_show[f'h{pair[0]}'] = True
                    elif len(pair) == 2:
                        for idx in range(pair[0], pair[1]+1):
                            self.ch_show[f'h{idx}'] = True
                print("SHOW DICT: ", self.ch_show)
                update_plot()

        def press_scale_plot(scale):
            for type in self.scale_buttons.keys():
                if type == scale:
                    c = 'green'
                else:
                    c = 'white'
                self.scale_buttons[type].config(highlightbackground=c)

            update_plot(scale)

        def update_plot(scale=''):

            if scale == '':
                scale = plot_mode.get()
            else:
                plot_mode.set(scale)

            fig.clear()
            plot1 = fig.add_subplot(111)
            plot_all = False   # note plotting too many value and trying to interact causes lag

            b = self.bins_ns
            x = b[:-2]

            if time_min.get() >= time_max.get():
                time_min.set(time_max.get() - 1)  # note: to ensure the min < max

            if plot_all:
                idx_min = 0
                idx_max = -1
            else:
                # convert time to index??
                idx_min = int(1000*time_min.get()/eta.const['binsize'])
                idx_max = int(1000*time_max.get()/eta.const['binsize'])+1   # note: round in case int would have rounded down

                if idx_min >= idx_max:
                    time_min.set(time_max.get() - 1)  # note: to ensure the min < max
                    idx_min = int(1000*time_min.get() / eta.const['binsize'])

            for i, thing in enumerate(self.ch_show.keys()):
                if self.ch_show[thing] is False:
                    continue   # doesn't plot when hidden

                y = self.folded_countrate_pulses[thing]

                if scale == 'linear':
                    line_b, = plot1.plot(x[idx_min:idx_max], y[idx_min:idx_max], label='c' + thing, c=['red', 'orange', 'green', 'blue'][i%4])
                elif scale == 'log':
                    line_b, = plot1.semilogy(x[idx_min:idx_max], y[idx_min:idx_max], label='c' + thing, c=['red', 'orange', 'green', 'blue'][i%4])
                elif scale == 'filtered log':
                    #y[y < 0] = np.nan  # bumping up all 0's to avoid negative inf at 0 counts
                    #y = list(y)
                    cnt_min.set(1.0)
                    line_b, = plot1.semilogy(x[idx_min:idx_max], y[idx_min:idx_max], label='c' + thing, c=['red', 'orange', 'green', 'blue'][i%4])
                elif scale == 'histo':
                    N, bins, bars = plot1.hist(x[idx_min:idx_max], bins=b[idx_min:idx_max], weights=y[idx_min:idx_max], rwidth=1, align='left')

            plot1.set_xlim([time_min.get(), time_max.get()])
            plot1.set_ylim([cnt_min.get(), cnt_max.get()])
            plot1.set_xlabel("lifetime [ns]")
            plot1.set_title("Lifetime")

            plot1.legend()
            fig.canvas.draw_idle()   # updates the canvas immediately?

        self.ch_show = {'h1': True, 'h2': True, 'h3': True, 'h4': True}
        time_min = tk.DoubleVar(value=30.0)
        time_max = tk.DoubleVar(value=100.0)
        cnt_min = tk.DoubleVar(value=0.0)
        cnt_max = tk.DoubleVar(value=6000.0)

        range_list = tk.StringVar(value="2, 3")
        plot_mode = tk.StringVar(value="linear")
        self.show_buttons = []

        fig = plt.figure(figsize=(12, 5), dpi=100)   #??? todo check difference
        update_plot()
        plt_frame, canvas = self.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()

        return plt_frame, butt_frm

    def old_plot_3D_lifetime_widget(self, tab):
        # TODO:
        # the figure that will contain the plot
        #fig = plt.Figure(figsize=(10, 3), dpi=100)
        #y = []  # data list
        #plot1 = fig.add_subplot(111)  # adding the subplot
        #plot1.plot(y)  # plotting the graph

        from mpl_toolkits.mplot3d import axes3d

        fig, ax1 = plt.subplots(1, 1, figsize=(14, 7), subplot_kw={'projection': '3d'})

        #fig = plt.Figure(figsize=(9, 5), dpi=100)
        #plot1 = fig.add_subplot(111)

        #ax1.set_xlim(1545, 1565)
        #ax1.set_ylim(0, 5000)
        ax1.set_xlabel("x")
        ax1.set_ylabel("y")
        ax1.set_title("Spectrum")

        #X = np.array([[0.5*i for i in range(10)]]*10)   # x grid
        #Y = np.array([[0.5*i for i in range(10)]]*10)   # y grid
        #Z = np.array([[5 for i in range(10)]]*10)       # amplitude

        X = np.array([[0, 1, 2, 3, 4, 5, 6, 7],
                      [0, 1, 2, 3, 4, 5, 6, 7],
                      [0, 1, 2, 3, 4, 5, 6, 7],
                      [0, 1, 2, 3, 4, 5, 6, 7],
                      [0, 1, 2, 3, 4, 5, 6, 7],
                      [0, 1, 2, 3, 4, 5, 6, 7],
                      [0, 1, 2, 3, 4, 5, 6, 7],
                      [0, 1, 2, 3, 4, 5, 6, 7]])

        Y = X.transpose()    # Y_row_i = X_col_i  for all i

        Z = np.array([[0, 1, 0, 0, 2, 0, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 0],
                      [0, 1, 0, 0, 2, 0, 0, 0]])

        print("x", X, type(X))
        print("y", Y, type(Y))
        print("z", Z, type(Z))

        # Give the second plot only wireframes of the type x = c
        #ax1.plot_wireframe(X, Y, Z, rstride=10, cstride=10)
        #ax1.plot_wireframe(X, Y, Z, rstride=0, cstride=10)  # only wireframes of the type x = c
        ax1.plot_wireframe(X, Y, Z, rstride=10, cstride=0)  # only wireframes of the type y = c

        ax1.set_title("3d lifetime")

        plt_frame, canvas = self.pack_plot(tab, fig)
        return plt_frame

    def plot_3D_lifetime_widget(self, tab):

        from mpl_toolkits.mplot3d import axes3d

        min_idx = 1000
        max_idx = 3000

        fig, ax1 = plt.subplots(1, 1, figsize=(14, 7), subplot_kw={'projection': '3d'})

        ax1.set_xlabel("time [ns]")
        #ax1.set_ylabel("channel")
        ax1.set_zlabel("counts")
        ax1.set_title("Spectrum")

        # x, bins shared data for all channels
        b = self.bins_ns
        x = b[:-2]

        X = x[min_idx:max_idx]   # note: dividing to get in nanoseconds
        N = len(X)  # number of data points per lifetime line   # FIXME to equal how many bins we have

        chs = ['h1', 'h2', 'h3', 'h4']
        nr_ch = len(chs)

        Y = np.ones(N) * int(N / nr_ch)

        for i, ch in enumerate(chs):   # NOTE: TEMP SOLUTION
            Z = self.folded_countrate_pulses[ch][min_idx:max_idx]
            ax1.plot(X, Y*i, Z, label='c'+ch)  # ax1.plot3D(X, Y, Z)

        ax1.set_yticks([int(N/nr_ch)*i for i in range(nr_ch)])
        ax1.set_yticklabels([f'ch.{j[1:]}' for j in chs])  # note: this will be the amount of channels we are displaying

        ax1.legend()

        ax1.set_title("3d lifetime")

        plt_frame, canvas = self.pack_plot(tab, fig)
        return plt_frame

    def plot_display_info_widget(self, tab, tab_str):

        frm_info = tk.Frame(tab, relief=tk.RAISED, bd=2)

        # TODO: add text or variables depending on which graph tab we have
        if tab_str == "tab 1 plots":
            pass

        elif tab_str == "tab 2 plots":
            pass
        elif tab_str == "tab 3 plots":
            pass

        elif tab_str == "tab all plots":
            pass

        tk.Label(frm_info, text=f'{tab_str}').grid(row=0, column=0, sticky="nsew")
        tk.Label(frm_info, text=f'                    ').grid(row=0, column=1, sticky="nsew")

        tk.Label(frm_info, text=f'info').grid(row=1, column=0, sticky="nsew")
        tk.Label(frm_info, text=f'info').grid(row=2, column=0, sticky="nsew")
        tk.Label(frm_info, text=f'info').grid(row=3, column=0, sticky="nsew")
        tk.Label(frm_info, text=f'info').grid(row=4, column=0, sticky="nsew")

        tk.Label(frm_info, text=f'.......').grid(row=1, column=1, sticky="nsew")
        tk.Label(frm_info, text=f'.......').grid(row=2, column=1, sticky="nsew")
        tk.Label(frm_info, text=f'.......').grid(row=3, column=1, sticky="nsew")
        tk.Label(frm_info, text=f'.......').grid(row=4, column=1, sticky="nsew")

        return frm_info

    def close(self):
        time.sleep(0.3)
        self.sp.acton_disconnect()  # closes connection with spectrometer
        self.sq.websq_disconnect()  # close SQWeb connection

class Demo:
    @staticmethod
    def d_read(param):
        if param == 'nm':
            return gui.device_wavelength
        elif param == 'grating':
            return gui.device_grating
        else:
            return

    @staticmethod
    def d_write(param, value):
        if param == 'nm':
            gui.device_wavelength = value - 0.003
        elif param == 'grating':
            gui.device_grating = value
        return True

    @staticmethod
    def d_connect(port_connect):
        gui.mark_done(port_connect, highlight="green", text_color='black', type='button')
        gui.demo_connect = True

    @staticmethod
    def d_get_counts():
        if gui.sq.number_of_detectors == 4:
            # below is duplicate of a N=10 sized measurement
            raw_counts = [[1700723885.6048694, 0.0, 0.0, 17.0, 162.0], [1700723885.8363566, 0.0, 1.0, 11.0, 161.0],
                          [1700723886.042608, 1.0, 1.0, 18.0, 146.0], [1700723886.3765514, 0.0, 0.0, 23.0, 161.0],
                          [1700723886.5506241, 0.0, 0.0, 21.0, 163.0], [1700723886.7209494, 0.0, 1.0, 30.0, 148.0],
                          [1700723886.89586, 0.0, 0.0, 11.0, 133.0], [1700723887.0686586, 0.0, 0.0, 16.0, 147.0],
                          [1700723887.3816106, 1.0, 0.0, 18.0, 150.0], [1700723887.551227, 1.0, 0.0, 10.0, 154.0],
                          [1700723885.6048694, 0.0, 0.0, 17.0, 162.0], [1700723885.8363566, 0.0, 1.0, 11.0, 161.0],
                          [1700723886.042608, 1.0, 1.0, 18.0, 146.0], [1700723886.3765514, 0.0, 0.0, 23.0, 161.0],
                          [1700723886.5506241, 0.0, 0.0, 21.0, 163.0], [1700723886.7209494, 0.0, 1.0, 30.0, 148.0],
                          [1700723886.89586, 0.0, 0.0, 11.0, 133.0], [1700723887.0686586, 0.0, 0.0, 16.0, 147.0],
                          [1700723887.3816106, 1.0, 0.0, 18.0, 150.0], [1700723887.551227, 1.0, 0.0, 10.0, 154.0]
                          ]
        else:  # self.sq.number_of_detectors == 8:
            # below is duplicate of a N=10 sized measurement    (altered from N=4 measurement)
            raw_counts = [[1700723885.6048694, 0.0, 0.0, 17.0, 22.0, 0.0, 0.0, 7.0, 22.0],
                          [1700723885.8363566, 0.0, 1.0, 11.0, 21.0, 0.0, 1.0, 1.0, 21.0],
                          [1700723886.042608, 1.0, 1.0, 18.0, 26.0, 1.0, 1.0, 8.0, 26.0],
                          [1700723886.3765514, 0.0, 3.0, 13.0, 21.0, 0.0, 0.0, 3.0, 11.0],
                          [1700723886.5506241, 5.0, 0.0, 11.0, 23.0, 0.0, 0.0, 1.0, 13.0],
                          [1700723886.7209494, 0.0, 1.0, 10.0, 28.0, 0.0, 1.0, 0.0, 18.0],
                          [1700723886.89586, 0.0, 0.0, 11.0, 23.0, 0.0, 0.0, 1.0, 13.0],
                          [1700723887.0686586, 0.0, 0.0, 16.0, 27.0, 0.0, 7.0, 6.0, 17.0],
                          [1700723887.3816106, 1.0, 0.0, 18.0, 20.0, 1.0, 0.0, 8.0, 10.0],
                          [1700723887.551227, 1.0, 0.0, 10.0, 24.0, 1.0, 0.0, 0.0, 24.0],
                          [1700723888.6048694, 0.0, 0.0, 17.0, 22.0, 2.0, 0.0, 7.0, 22.0],
                          [1700723888.8363566, 6.0, 1.0, 11.0, 21.0, 0.0, 1.0, 1.0, 21.0],
                          [1700723889.042608, 1.0, 1.0, 18.0, 26.0, 1.0, 1.0, 8.0, 26.0],
                          [1700723889.3765514, 0.0, 0.0, 23.0, 21.0, 0.0, 0.0, 3.0, 21.0],
                          [1700723889.5506241, 0.0, 0.0, 21.0, 23.0, 0.0, 0.0, 1.0, 23.0],
                          [1700723889.7209494, 0.0, 1.0, 30.0, 28.0, 0.0, 1.0, 0.0, 18.0],
                          [1700723889.89586, 0.0, 0.0, 11.0, 23.0, 0.0, 0.0, 1.0, 13.0],
                          [1700723890.0686586, 0.0, 0.0, 16.0, 27.0, 2.0, 0.0, 6.0, 17.0],
                          [1700723890.3816106, 1.0, 0.0, 18.0, 20.0, 1.0, 0.0, 8.0, 10.0],
                          [1700723890.551227, 1.0, 0.0, 10.0, 24.0, 1.0, 0.0, 0.0, 14.0]
                          ]
        if gui.temp_counter == len(raw_counts) - 1:
            return []
        gui.temp_counter += 1
        counts = [raw_counts[gui.temp_counter]]
        return counts

class ETA:

    def __init__(self):
        self.const = {
            'eta_format':    1,      # swabian = 1
            'eta_recipe':   '3D_2_channels_tof_swabian_marker_ch4.eta',   # 'lifetime_new_spectrometer_4_ch_lifetime.eta',
            'timetag_file': 'Data/ToF_Duck_10MHz_det1_det2_5.0ms_[2.1, 3.9, -3.2, -4.8]_100x100_231220.timeres',
            'bins':          5000,
            'binsize':       20,     # bin width in ps
            }

    def load_eta(self, recipe, **kwargs):
        with open(recipe, 'r') as filehandle:
            recipe_obj = json.load(filehandle)

        eta_engine = etabackend.eta.ETA()
        eta_engine.load_recipe(recipe_obj)

        # Set parameters in the recipe
        for arg in kwargs:
            eta_engine.recipe.set_parameter(arg, str(kwargs[arg]))
        eta_engine.load_recipe()

        print("\nRecipe loaded!")
        return eta_engine

    def eta_lifetime_analysis(self):  # , const):

        # --- LOAD RECIPE ---
        eta_engine = self.load_eta(self.const["eta_recipe"], bins=self.const["bins"], binsize=self.const["binsize"])  # NOTE: removed for test

        # note: bins will be the same for all data channels
        bins_i = np.linspace(0, self.const['bins']+1, self.const['bins']+2)  # starting with 8 channels for now
        times_i = bins_i * self.const['binsize']   # time list in ps  (for one histogram)

        channels = ['h1', 'h2', 'h3', 'h4']
        # fixme: we need to make sure that the channels matches what we have in the result dict
        folded_countrate_pulses = dict([(c, np.zeros(self.const['bins'])) for c in channels])

        # ------ETA PROCESSING OF ONE TIMERES FILE-----

        pulse_nr = 0
        pos = 0  # 0  # internal ETA tracker (-> maybe tracks position in data list?)
        context = None  # tracks info about ETA logic, so we can extract and process data with breaks (i.e. in parts)
        eta_format = self.const["eta_format"]   # eta_engine.FORMAT_SI_16bytes   # swabian = 1
        file = Path(self.const['timetag_file'])

        while True:
            # Extract histograms from eta
            file_clips = eta_engine.clips(filename=file, seek_event=pos, format=eta_format)
            result, context = eta_engine.run({"timetagger1": file_clips}, resume_task=context, return_task=True, group='quTAG', max_autofeed=1)

            # Check if we've run out of data, otherwise update position
            if result['timetagger1'].get_pos() == pos:  # or (pos is None):
                break
            else:
                pulse_nr += 1
                pos = result['timetagger1'].get_pos()

            # Folding histogram counts for each channel:
            for c in channels:
                folded_countrate_pulses[c] += np.array(result[c])

        return times_i, folded_countrate_pulses

    # help function to check how many counts each channel has in the timeres file
    def signal_count(self):
        # ------IMPORTS-----
        # Packages for ETA backend
        import json
        import etabackend.eta  # Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/
        from pathlib import Path

        def eta_counter_swab(recipe_file, timetag_file, **kwargs):
            # Load the recipe from seperate ETA file
            with open(recipe_file, 'r') as filehandle:
                recipe_obj = json.load(filehandle)

            eta_engine = etabackend.eta.ETA()
            eta_engine.load_recipe(recipe_obj)

            # Set parameters in the recipe
            for arg in kwargs:
                print("Setting", str(kwargs[arg]), "= ", arg)
                eta_engine.recipe.set_parameter(arg, str(kwargs[arg]))

            eta_engine.load_recipe()

            file = Path(timetag_file)
            cutfile = eta_engine.clips(filename=file, format=1)
            result = eta_engine.run({"timetagger1": cutfile},
                                    group='qutag')  # Runs the time tagging analysis and generates histograms

            # print(f"{2} : {result['c2']}")
            # print(f"{3} : {result['c3']}")

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

                print(f"\n# : counts\n-------")
                for s in signals:
                    print(f"{s} : {result[signals[s]]}")

        recipe = 'signal_counter.eta'
        # recipe = 'temp2_signal_counter.eta'
        file = 'Data/231102/nr_6_sineFreq(1)_numFrames(3)_sineAmp(0.3)_stepAmp(0.3)_stepDim(100)_date(231102)_time(10h36m17s).timeres'  # not changed
        # file = 'Data/231102/nr_6_sineFreq(5)_numFrames(3)_sineAmp(0.3)_stepAmp(0.3)_stepDim(100)_date(231102)_time(10h42m27s).timeres'  # not changed
        # file = 'Data/231102/nr_6_sineFreq(10)_numFrames(3)_sineAmp(0.3)_stepAmp(0.3)_stepDim(100)_date(231102)_time(10h44m15s).timeres'  # not changed
        file = 'ToF_terra_10MHz_det2_10.0ms_[2.1, 2.5, -3.2, -4.8]_100x100_231030.timeres'

        freq = 1
        bins = 20000
        binsize = int(round((1 / (freq * 1e-12)) / bins))
        eta_counter_swab(recipe, file, binsize=binsize, bins=bins)

        # recipe = 'temp2_signal_counter.eta'
        # file = 'Data/230927/digit_6_liquid_lens_20mA_steps_5mm_df_sineFreq(10)_numFrames(10)_sineAmp(0.3)_stepAmp(0.3)_stepDim(100)_date(230927)_time(13h15m26s).timeres'  # not changed
        # eta_counter_qutag(recipe, file)

        plt.show()

        print("\ndone!")

#-----

demo = True
gui = None

try:
    eta = ETA()

    gui = GUI()
    gui.root.after(500, gui.scanning)  # After 1 second, call scanning
    gui.root.mainloop()

except KeyboardInterrupt:
    print("ERROR: PROGRAM INTERRUPTED EARLY.")
    # gui.close()  # Close all external connections
    raise

except SystemExit:
    print("system exit")
    raise

except tk.EXCEPTION:
    print("tkinter exception")
    raise

except serial.SerialException:
    print("serial exception")
    raise

finally:
    print('------\nExiting...')
    if gui:
        gui.close()  # Close all external connections



"""
    Value   |   ETA Constant/Name        |      Format for Device
    -----------------------------------------------------------------
    0           eta.FORMAT_PQ                   PicoQuant
    1           eta.FORMAT_SI_16bytes           Swabian Instrument binary
    2           eta.FORMAT_QT_COMPRESSED        compressed qutools quTAG binary
    3           eta.FORMAT_QT_RAW               raw qutools quTAG (?)
    4           eta.FORMAT_QT_BINARY            qutools quTAG 10-byte Binary
    5           eta.FORMAT_BH_spc_4bytes        Becker & Hickl SPC-134/144/154/830
    6           eta.FORMAT_ET_A033              Eventech ET A033
"""




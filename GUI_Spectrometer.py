import random
import tkinter
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import time
import serial
from serial.tools import list_ports
from datetime import date
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backend_bases import key_press_handler

from test_data import *
from tkinter.messagebox import _show
from WebSQControl import WebSQControl


# TODO NOW:
#  - Display the count rate of several detectors as a histogram     (email from Val)
#       - Read counts from detector
#       - Define wavelengths for each detector
#       - Create conversion to different units
#  - Simplify your current code to control the spectrometer         (email from Val)


# TODO LATER:
#  - add settings and specs to datafile (create a separator to know at what row data starts!)
#  - Display the detection rates from the different pixels in a histrogram that will have an energy/wavelength scale  (email from Val)
#  - Separate or remove demo mode
#  - live graph for all plots
#  - OBS: PLOTS SHOULD BE HISTOGRAMS
#  - Fix __exit__ method (find out how and why and what)
#  - search for available ports and ask to connect to correct one
#       --> make a "connection tab" to connect device first...
#       --> find out how to list available/active ports as options (dropdown list)
#  - fix "check device" layout
#  - add a tab with one button per command to read to device one by one, and display response??
#  - maybe add a thing (when pressing start scan button) that checks (reads) current device configs and compares to desired. if not a match then abort scan
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

        self.tinyLab = True
        # TCP IP Address of the detector (default 192.168.1.1)
        if self.tinyLab:
            self.tcp_ip_address = '192.168.120.119'    # for tiny lab wifi (8 channels for our spectrometer)
            self.number_of_detectors = 8
        else:
            self.tcp_ip_address = '192.168.35.236'     # for big lab wifi (4 channels that others use)
            self.number_of_detectors = 4

        # The control port (default 12000)
        self.control_port = 12000
        # The port emitting the photon Counts (default 12345)
        self.counts_port = 12345

        # Number of measurements, used when reading counts,  type=int
        self.N = 10

        if not demo:
            # test
            self.open_connection()
            self.number_of_detectors = self.get_number_of_detectors()  # Returns how many channels/detectors we have in the system  # NOTE: required other functions!!
            self.set_integration_time(dt=100)                             # Sets the integration time to collect counts in bin
            #self.test()  # NOTE: OPTIONAL TEST
            self.close_connection()  # close SQWeb connection   # note, we should close it later when we're done instead

        # OPTIONS TO IMPLEMENT IN GUI:
        # self.set_curr_bias()
        # self.set_trigger_lvl()
        # self.read_back()               # reads and prints: periode, bias, trigger
        # counts = self.get_counts(N=10)  # this returns both timestamps and counts per detector for N measurements

    def open_connection(self):
        if demo:
            return
        try:
            print("Attempting connection to WebSQ...")
            self.websq = WebSQControl(TCP_IP_ADR=self.tcp_ip_address, CONTROL_PORT=self.control_port, COUNTS_PORT=self.counts_port)
            self.websq.connect()
            print("Connected to WebSQ!")
        except:
            print("Connection error with WebSQ")
            raise

    def get_number_of_detectors(self):
        """Acquire number of detectors in the system"""
        n = self.websq.get_number_of_detectors()
        print(f"System as {n} detectors")
        return n

    def set_integration_time(self, dt=100):
        print(f"Set integration time to {dt} ms")
        self.websq.set_measurement_periode(dt)  # Time in ms

    def set_curr_bias(self):
        # Set the bias current
        # TODO: scan bias of detectors?
        bias = 0
        curr = []
        for n in range(self.number_of_detectors):
            curr.append(bias)
        print(f"Set bias to: {curr}")
        self.websq.set_bias_current(current_in_uA=curr)

    def set_trigger_lvl(self):
        # Set the trigger level
        # TODO set some value (or a list of values)
        trigger = -150  # mV
        trig = []
        for n in range(self.number_of_detectors):
            trig.append(trigger)
        print(f"Set trigger levels to: {trig}")
        self.websq.set_trigger_level(trigger_level_mV=trig)

    def get_counts(self, N=10):
        # Acquire N counts measurements:
        #   Returns an array filled with N numpy arrays each containing as first element a time stamp and then the detector counts ascending order
        print(f"Acquiring {N} counts measurements...")
        all_counts = self.websq.acquire_cnts(N)   # note: this includes the time stamp as well
        return all_counts

    def read_back(self):
        """
        Example:
            Measurement Periode (ms): 	 100
            Bias Currents in uA: 		 [-14.5, -16, -17.7, -12.4]
            Trigger Levels in mV: 		 [-150, -150, -150, -150]
        """
        print("\nRead back set values\n====================")
        print(f"Measurement Periode (ms):    {self.websq.get_measurement_periode()}")
        print(f"Bias Currents in uA:         {self.websq.get_bias_current()}")
        print(f"Trigger Levels in mV:        {self.websq.get_trigger_level()}")

    def close_connection(self):
        if demo:
            return
        try:
            self.websq.close()
            print("Connection closed with WebSQ")
        except:
            print("Failed close connection with WebSQ")
            raise

class SP2750:

    def __init__(self):
        #self.find_ports()  

        # Serial connection settings:
        self.handle = None
        self.port = "COM4"          # USB port

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

    def find_ports(self):  # TODO: find our device port and connect automatically
        print("---------")
        for port in serial.tools.list_ports.comports():
            print(f"\ndevice:          {port.device       }"
                  f"\nname:            {port.name         }"
                  f"\ndescription:     {port.description  }"
                  f"\nhwid:            {port.hwid         }"
                  f"\nvid:             {port.vid          }"
                  f"\npid:             {port.pid          }"
                  f"\nserial_number:   {port.serial_number}"
                  f"\nlocation:        {port.location     }"
                  f"\nmanufacturer:    {port.manufacturer }"
                  f"\nproduct:         {port.product      }"
                  f"\ninterface:       {port.interface    }")
            print("---------")

    def connect(self):
        if demo:
            return

        try:
            self.handle = serial.Serial(port=self.port, baudrate=9600, parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)  # , timeout=self.serial_timeout)
            if self.handle.isOpen():
                print(f"Successfully connected to PORT: {self.port}\nSerial handle:", self.handle)
            else:
                print("ERROR: handle still None")
                raise serial.SerialException
        except serial.SerialException:
            print(f"ERROR: could not connect to PORT: {self.port}")
            if self.handle:
                self.disconnect()
            raise

    def disconnect(self):
        if demo:
            return

        if self.handle is None:
            print("Not connected to device --> don't need to disconnect")
            return

        self.handle.close()
        self.handle = None
        print("Connection Closed!")

    def check_cmd(self, access, param, value=None):

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
        if self.handle is None:
            print("ERROR: Not connected to device!")
            return False
        elif not self.handle.isOpen():
            print("ERROR: Device not open!")
            return False
        return True

    def read_cmd(self, param):

        # Checks if desired command and value is ok to send
        if not self.check_cmd('read', param):
            return

        if demo:
            return Demo.d_read(param)

        if not self.check_handle():  # check if handle is ok
            return

        #print(f"\nReading {param}...")
        res = self.query(cmd=self.dict[param]['cmd'])

        # Extract value from response
        res_num = ''
        for char in res[1:].decode('ASCII'):
            if (char == ' ' and len(res_num) > 0) or (char == 'o'):
                return eval(res_num)
            res_num += char

        print("NOTE FOR JULIA! DIDN'T RETURN EARLY. CHECK WHY. ", res, ", ", res_num)  # remove later
        return eval(res_num)   # remove later

    def write_cmd(self, param, value):
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

    def query(self, cmd):
        cmd_bytes = cmd.encode("ASCII") + b'\r'
        self.handle.write(cmd_bytes)
        return self.wait_for_read()

    def wait_for_read(self):

        # reads response every second and waits until request is complete.
        res = b''
        for i in range(60):
            if b'ok' in res:
                print('done')
                return res
            else:
                time.sleep(0.5)
                res_r = self.handle.readline()
                print(res_r)
                res += res_r
        print('failed wait to read')


class GUI:

    def __init__(self):
        self.temp_counter = 0   # REMOVE LATER  USED TO TEST HISTO PLOTTING WITH SAMPLE DATA

        self.sq = SQControl()

        # initialize communication class with spectrometer
        self.sp = SP2750()

        # Create and configure the main GUI window
        self.init_window()
        # define global variables
        self.init_parameters()
        # Create and place tabs frame on window grid
        self.init_fill_tabs()
        #if demo:
        #    self.root.after(100, lambda: _show('Title', 'Demo Version'))

    def init_parameters(self):
        self.data = []
        self.running = False  # this tracks if we are running a scan (collecting counts from detector)
        self.demo_connect = False  # temp for demo to check if we've actually connected to device
        self.current_file_name = None
        self.current_file_type = None
        self.current_file_path = None
        self.device_grating = 0
        self.device_wavelength = 0
        self.config_success = None   # None if not tried to configure yet
        self.checked_configs = False
        self.ok_to_send_list = []
        self.widgets = {}
        self.buttons = {}  # todo, do we need or use these?
        self.button_color = 'grey'  # default button colors
        self.port = tk.StringVar()     # note maybe change later when implemented
        self.x_label = tk.StringVar(value='λ [nm]')
        self.grating_levels = {   # TODO: make this configurable?
            1: {'grating': 600,  'blz': '750 nm'},
            2: {'grating': 150,  'blz': '800 nm'},
            3: {'grating': 1800, 'blz': 'H-VIS'},
        }
        self.params = {
            'grating':           {'var': tk.IntVar(value=1),    'type': 'radio',     'default' : 1, 'value': [1, 2, 3]},
            'nm':                {'var': tk.IntVar(value=600),  'type': 'int entry', 'default' : 350, 'value': [350, 650, 750]},
            'width_nm' :         {'var': tk.IntVar(),           'type': 'int entry', 'default' : 10, 'value': [5, 15, 30]},
            'slit':              {'var': tk.IntVar(value=10),   'type': 'int entry', 'default' : 10, 'value': [10, 20, 30]},
            'nr_pixels':         {'var': tk.IntVar(value=8),    'type': 'int entry', 'default' : 8, 'value': [3, 8, 12]},
            'file_name':         {'var': tk.StringVar(),        'type': 'str entry', 'default' : '', 'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},
            'folder_name':       {'var': tk.StringVar(),        'type': 'str entry', 'default' : '', 'value': ['~/Desktop/GUI/Data1', '~/Desktop/GUI/Data2', '~/Desktop/GUI/Data3']},
            'eta_recipe':        {'var': tk.StringVar(),        'type': 'str entry', 'default' : '', 'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }

    def init_window(self):
        self.root = tk.Tk()
        self.root.title("Quantum Spectrometer GUI - Ghostly matters")   # *Ghostly matters*
        self.root.resizable(True, True)
        self.root.config(background='#fafafa')
        #self.root.rowconfigure(0, minsize=30, weight=1)   # TODO: check if we need this
        #self.root.columnconfigure(0, minsize=50, weight=1)  # TODO: check if we need this
        #self.root.geometry('1200x700+200+100')
        #self.root.state('zoomed')   # TODO: check if we need this

    def init_fill_tabs(self):

        def scan_tab():
            new_scan_tab = ttk.Frame(tabControl)

            # ---- Start new scan TAB ----  NOTE this should include settings and prep
            start_tab = tk.Frame(new_scan_tab, relief=tk.RAISED, bd=2)   # frame to gather things to communicate with devices

            self.widgets['param_config'] = self.choose_param_configs_widget(new_scan_tab)
            self.widgets['live_spectrum'] = self.plot_live_histo(new_scan_tab)

            # sub frame:
            self.widgets['file_config'] = self.choose_file_configs_widget(start_tab)
            self.widgets['send_conf_button'] = self.send_param_configs_widget(start_tab)  # button to send cofigs
            self.widgets['start_scan_button'] = self.start_scan_widget(start_tab)  # button to send cofigs

            self.widgets['param_config'].grid(row=0, column=0, rowspan=100, sticky="news", padx=0, pady=0)
            start_tab.grid(row=0, column=1, columnspan=1, sticky="news", padx=0, pady=0)
            self.widgets['live_spectrum'].grid(row=2, column=1, columnspan=1, sticky="news", padx=0, pady=0)

            tk.Label(start_tab, text='Device Communication', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news", padx=0, pady=0)
            self.widgets['file_config'].grid(row=1, column=0, sticky="news", padx=0, pady=0)  # in sub frame
            self.widgets['send_conf_button'].grid(row=1, column=1, sticky="news", padx=0, pady=0)  # in sub frame
            self.widgets['start_scan_button'].grid(row=1, column=2, sticky="news", padx=0, pady=0)  # in sub frame

            tabControl.add(new_scan_tab, text='New Scan')

        def plot_spectrum_tab():
            plots_spectrum = ttk.Frame(tabControl)

            plt_frame, button_frame = self.plot_spectrum_widget(plots_spectrum)
            self.widgets['plot_spectrum_1'] = plt_frame
            self.widgets['plot_spectrum_1'].grid(row=0, rowspan=4, column=0, sticky="nsew", padx=0, pady=0)

            self.widgets['info_spectrum'] = self.plot_display_info_widget(plots_spectrum, "Spectrum plot info")
            self.widgets['info_spectrum'].grid(row=0, rowspan=3, column=1, sticky="nsew" , padx=0, pady=0)

            self.widgets['button_spectrum_1'] = button_frame
            self.widgets['button_spectrum_1'].grid(row=3, column=1, sticky="nsew", padx=0, pady=0)

            tabControl.add(plots_spectrum, text='Spectrum Plot')

        def plot_correlation_tab():
            plots_correlation = ttk.Frame(tabControl)
            # TODO: add widgets
            tabControl.add(plots_correlation, text='Correlation Plot')

        def plot_lifetime_tab():
            plots_lifetime = ttk.Frame(tabControl)
            # TODO: add widgets
            tabControl.add(plots_lifetime, text='Lifetime Plot')

        def plot_3d_lifetime_tab():
            plots_3d_lifetime = ttk.Frame(tabControl)
            # TODO: add widgets
            tabControl.add(plots_3d_lifetime, text='3D Lifetime Plot')

        def settings_tab():  # FIXME
            settings_tab = ttk.Frame(tabControl)
            # TODO: add widgets
            tabControl.add(settings_tab, text='Settings')

        # Create notebook for multi tab window:
        tabControl = ttk.Notebook(self.root)
        # Create and add tabs to notebook:
        scan_tab()
        plot_spectrum_tab()
        plot_correlation_tab()
        plot_lifetime_tab()
        plot_3d_lifetime_tab()
        settings_tab()
        # Pack all tabs in notebook to window:
        tabControl.pack(expand=1, fill="both")

    @staticmethod
    def add_to_grid(widg, rows, cols, sticky, columnspan=None):
        # EXAMPLE: self.add_to_grid(widg=[name_entry, folder_entry, recipe_entry], rows=[1,2,3], cols=[1,1,1], sticky=["ew", "ew", "ew"])
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

    def choose_param_configs_widget(self, tab):

        def press_connect():  # TODO
            if demo:
                Demo.d_connect(port_connect)
                return
                
            self.sp.disconnect()
            self.sp.connect()
            self.sp.handle.write(b'NO-ECHO\r')
            self.sp.wait_for_read()  # b'  ok\r\n'
            port_entry.config(text=f'{self.sp.port}')

            if self.sp.handle.isOpen():
                self.mark_done(port_connect, highlight="green", text_color='black', type='button')
            else:
                self.mark_done(port_connect, highlight="red", text_color='black', type='button')

        def reset_button_col():
            for button in [btn_def_1, btn_def_2, btn_def_3]:
                self.mark_done(button, highlight=self.button_color, type='button')

        def default_press(n=0):

            reset_button_col()
            if n == 0:
                for key in self.params.keys():
                    self.params[key]['var'].set(self.params[key]['default'])        # Clear all
            else:
                self.mark_done(default_btns[n], highlight='green', type='button')   # set one of the defaults
                for key in self.params.keys():
                    self.params[key]['var'].set(self.params[key]['value'][n-1])
                self.suggest_filename(self.name_entry)

            update_ch()

        def select_grating():
            # FIXME OR REMOVE
            pass

        def update_ch():
            # removes previously shown channels (in case we want to decrease in amount)
            for j, widget in enumerate(frm_ch.winfo_children()):   # FIXME NOTE TODO: USE THIS LATER TO ACCESS BUTTONS FOR MARKING DONE
                if j > 2:
                    widget.destroy()
            fill_ch()

        def fill_ch():
            self.channels = []
            for i in range(self.params['nr_pixels']['var'].get()):
                self.channels.append(tk.IntVar())  #
                tk.Label(frm_ch, text=f"Pixel {i + 1}").grid(row=i + 2, column=0, sticky="ew", padx=0, pady=0)
                tk.Entry(frm_ch, bd=2, textvariable=self.channels[i], width=6).grid(row=i + 2, column=1, sticky="ew", padx=0, pady=0)

        # ---------------
        self.port.set(self.sp.port)  # note maybe change later when implemented

        # FRAMES
        frm_test = tk.Frame(tab, relief=tk.RAISED, bd=2)
        frm_default = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_port = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_slit = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_grating = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_detect = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_ch = tk.Frame(frm_test, relief=tk.RAISED, bd=2)

        # WIDGETS
        #  -- Default:
        btn_clear = tk.Button(frm_default, text="Clear all", command=lambda : default_press(0), activeforeground='red', highlightbackground=self.button_color)
        btn_def_1 = tk.Button(frm_default, text="Default 1", command=lambda : default_press(1), activeforeground='blue', highlightbackground=self.button_color)
        btn_def_2 = tk.Button(frm_default, text="Default 2", command=lambda : default_press(2), activeforeground='blue', highlightbackground=self.button_color)
        btn_def_3 = tk.Button(frm_default, text="Default 3", command=lambda : default_press(3), activeforeground='blue', highlightbackground=self.button_color)
        default_btns = [btn_clear, btn_def_1, btn_def_2, btn_def_3]

        #  -- Port:
        port_txt = tk.Label(frm_port, text='USB Port')    # port_entry = tk.Entry(frm_port, bd=2, textvariable=self.port, width=5)   # FIXME later
        port_entry = tk.Label(frm_port, text=f'{self.port.get()}')
        port_connect = tk.Button(frm_port, text="Connect Device", command=press_connect, activeforeground='blue', highlightbackground=self.button_color)

        #  -- Slit:
        slt_txt = tk.Label(frm_slit, text='Slit width')
        slt_entry = tk.Entry(frm_slit, bd=2, textvariable=self.params['slit']['var'], width=5)
        slt_unit = tk.Label(frm_slit, text='[um]')

        #  -- Grating:
        grt_txt = tk.Label(frm_grating, text='Grating')
        grt_txt_blz = tk.Label(frm_grating, text='Blaze')

        grt_rad_1 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[1]['grating'])+"  [gr/mm]", variable=self.params['grating']['var'], value=1, command=select_grating)
        grt_rad_2 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[2]['grating'])+"  [gr/mm]", variable=self.params['grating']['var'], value=2, command=select_grating)
        grt_rad_3 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[3]['grating'])+"  [gr/mm]", variable=self.params['grating']['var'], value=3, command=select_grating)

        grt_txt_1_blz = tk.Label(frm_grating, text="   "+self.grating_levels[1]['blz'])
        grt_txt_2_blz = tk.Label(frm_grating, text="   "+self.grating_levels[2]['blz'])
        grt_txt_3_blz = tk.Label(frm_grating, text="   "+self.grating_levels[3]['blz'])

        #  -- Detector:
        det_txt = tk.Label(frm_detect, text="Detector")

        det_wave_txt = tk.Label(frm_detect, text="Center λ")
        det_wave_val = tk.Entry(frm_detect, bd=2, textvariable=self.params['nm']['var'], width=6)
        det_wave_unit = tk.Label(frm_detect, text='[nm]')

        det_width_txt = tk.Label(frm_detect, text="Pixel width")
        det_width_val = tk.Entry(frm_detect, bd=2, textvariable=self.params['width_nm']['var'], width=6)
        det_width_unit = tk.Label(frm_detect, text='[nm]')

        det_no_txt = tk.Label(frm_detect, text="Nr. of pixels")
        det_no_val = tk.Entry(frm_detect, bd=2, textvariable=self.params['nr_pixels']['var'], width=6)
        ch_butt0 = tk.Button(frm_detect, text="Update", command=update_ch, activeforeground='blue', highlightbackground=self.button_color)  # NOTE: previously in channel frame below

        # -- Channels:
        ch_txt_ch = tk.Label(frm_ch, text='Pixel')
        ch_txt_bias = tk.Label(frm_ch, text='Bias')
        ch_txt_cnts = tk.Label(frm_ch, text='Counts')

        # GRID
        # -- Default
        self.add_to_grid(widg=[btn_clear, btn_def_1, btn_def_2, btn_def_3], rows=[0,0,0,0], cols=[0,1,2,3], sticky=["ew", "ew", "ew", "ew"])
        # -- Port
        self.add_to_grid(widg=[port_txt, port_entry, port_connect], rows=[0,0,0], cols=[0,1,2], sticky=["", "", ""])
        # -- Slit
        self.add_to_grid(widg=[slt_txt, slt_entry, slt_unit], rows=[0,0,0], cols=[0,1,2], sticky=["", "", ""])
        # -- Grating
        self.add_to_grid(widg=[grt_txt, grt_rad_1, grt_rad_2, grt_rad_3], rows=[2,3,4,5], cols=[0,0,0,0], sticky=["", "s", "s", "s"])
        self.add_to_grid(widg=[grt_txt_blz, grt_txt_1_blz, grt_txt_2_blz, grt_txt_3_blz], rows=[2,3,4,5], cols=[1,1,1,1], sticky=["", "s", "s", "s"])
        # -- Detector
        self.add_to_grid(widg=[det_txt], rows=[0], cols=[0], sticky=["ew"], columnspan=[2])
        self.add_to_grid(widg=[det_wave_txt, det_wave_val, det_wave_unit], rows=[1,1,1], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        self.add_to_grid(widg=[det_width_txt, det_width_val, det_width_unit], rows=[2,2,2], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        self.add_to_grid(widg=[det_no_txt, det_no_val, ch_butt0], rows=[3,3,3], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        # -- Channels
        self.add_to_grid(widg=[ch_txt_ch, ch_txt_bias, ch_txt_cnts], rows=[0,0,0], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        fill_ch()  # Updates channels displayed

        # ------------- COMBINING INTO TEST FRAME --------------
        tk.Label(frm_test, text='Settings', font=('', 15)).grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.add_to_grid(widg=[frm_default, frm_port, frm_slit, frm_grating, frm_detect], rows=[1,2,3,4,5], cols=[0,0,0,0,0], sticky=["ew", "ew", "ew", "ew", "ew"])
        frm_ch.grid(row=6, column=0, rowspan=100, sticky="ew", padx=0, pady=0)

        return frm_test

    def suggest_filename(self, entry):
        currDate = date.today().strftime("%y%m%d")
        currTime = time.strftime("%Hh%Mm%Ss", time.localtime())

        temp = f"slit({self.params['slit']['var'].get()})_" \
               f"grating({self.params['grating']['var'].get()})_" \
               f"lamda({self.params['nm']['var'].get()})_" \
               f"pixels({self.params['nr_pixels']['var'].get()})_" \
               f"date({currDate})_time({currTime}).timeres"
        self.params['file_name']['var'].set(temp)
        entry.delete(0, tk.END)
        entry.insert(0, temp)

    def choose_file_configs_widget(self, tab):

        def get_recipe():
            self.params['eta_recipe']['var'].set(askopenfilename(filetypes=[("ETA recipe", "*.eta")]) )
            recipe_entry.delete(0, tk.END)
            recipe_entry.insert(0, self.params['eta_recipe']['var'].get())

        def get_folder():
            self.params['folder_name']['var'].set(askdirectory())
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, self.params['folder_name']['var'].get())

        def suggest_name():
            self.suggest_filename(self.name_entry)

        frm_misc = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(frm_misc, text="Analysis Configs").grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="(optional)").grid(row=0, column=2, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="New File Name").grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="New File Location").grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="ETA recipe").grid(row=3, column=0, sticky="ew", padx=0, pady=0)

        # TODO: fix accessibility
        self.name_entry = tk.Entry(frm_misc, bd=2, textvariable=self.params['file_name']['var'], width=20)
        folder_entry = tk.Entry(frm_misc, bd=2, textvariable=self.params['folder_name']['var'], width=20)
        recipe_entry = tk.Entry(frm_misc, bd=2, textvariable=self.params['eta_recipe']['var'], width=40)

        butt0 = tk.Button(frm_misc, text="Suggest...", command=suggest_name, activeforeground='blue', highlightbackground=self.button_color)
        butt1 = tk.Button(frm_misc, text="Open Folder", command=get_folder, activeforeground='blue', highlightbackground=self.button_color)
        butt2 = tk.Button(frm_misc, text="Choose File", command=get_recipe, activeforeground='blue', highlightbackground=self.button_color)

        self.add_to_grid(widg=[self.name_entry, folder_entry, recipe_entry], rows=[1,2,3], cols=[1,1,1], sticky=["ew", "ew", "ew"])
        self.add_to_grid(widg=[butt0, butt1, butt2], rows=[1,2,3], cols=[2,2,2], sticky=["ew", "ew", "ew"])

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
            for i, widget in enumerate([send_txt_1, send_txt_2, send_txt_3]):
                widget.config(text=temp[i], foreground='black')   # make green for passed tests!

        def check():
            show_configs()
            self.ok_to_send_list = [] #reset
            # todo: maybe should also check connection and values on device (if active/correct)
            check_list = [
                    ['grating',     0, send_txt_2, 'grating', self.device_grating],
                    ['nm',   0, send_txt_3, 'center λ', self.device_wavelength],
                ]
            for check_thing in check_list:

                if not self.demo_connect:
                    tempi = ''
                    check_thing[2].config(text=tempi, foreground='black')  # make green for passed tests!
                    self.mark_done(check_thing[2], text_color='red', type='text')  # ????
                    continue  # skip rest of loop iteration

                res = self.sp.read_cmd(param=check_thing[0])  # returns true if correctly configured
                print(" value =", res)

                tempi = f"{check_thing[3]} = {res}  -->  {self.params[check_thing[0]]['var'].get()}"

                check_thing[2].config(text=tempi, foreground='black')  # make green for passed tests!

                print(res)
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

            if not self.demo_connect:
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
                    #return
                else:
                    time.sleep(1)

            print("\n--- SEND VALUES ---")

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

            # DOUBLE CHECK AFTER
            check()
            print('done')

        temp = get_str()

        frm_send = tk.Frame(tab, relief=tk.RAISED, bd=2)
        frm_send_values = tk.Frame(frm_send, relief=tk.RAISED, bd=2)

        send_txt_1 = tk.Label(frm_send_values, text=temp[0], foreground='white', justify="left")
        send_txt_2 = tk.Label(frm_send_values, text=temp[0], foreground='white', justify="left")
        send_txt_3 = tk.Label(frm_send_values, text=temp[1], foreground='white', justify="right")

        btn_check_conf = tk.Button(frm_send, text="Check values..", command=check, activeforeground='blue', highlightbackground=self.button_color)
        btn_send_conf = tk.Button(frm_send,  text="Send to Device", command=nothing, foreground='white', activeforeground='white') #, highlightbackground=self.button_color)

        self.add_to_grid(widg=[btn_check_conf, frm_send_values, btn_send_conf], rows=[0,1,2], cols=[0,0,0], sticky=["new", "new", "new"])
        self.add_to_grid(widg=[send_txt_1, send_txt_2, send_txt_3], rows=[0,1,2], cols=[0,0,0], sticky=["new", "new", "new"])

        return frm_send

    def get_counts(self):  # TODO: make general for self.sq.nr_of_detectors

        rando = False   # uses
        if rando:   # testing with random data
            # note: below is pretend data
            #----------------------
            bias = [1, 0.3, 0.7, 1.2, 0.1, 0.1, 0.1, 0.1]
            self.data = []
            for i in range(self.sq.N):  # number of measurements
                self.data.append([])
                for j in range(self.sq.number_of_detectors):
                    val = random.randrange(0, 100)
                    self.data[-1].append(int(val*bias[j]))
                #self.data[-1].append(0)  # note: empty channel to display histogram correctly

            print(self.cumulative_ch_counts)
            print("generated data:", self.data)
            for row in np.array(self.data):
                self.cumulative_ch_counts += row  # (note self.data is now smaller than other
            print("cumulative:", self.cumulative_ch_counts)
            # NOTE: data should be a list of lists (one list per integration time with 4 channel bins)
        else:
            if demo:
                if self.sq.number_of_detectors == 4:
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
                                  [1700723886.042608,  1.0, 1.0, 18.0, 26.0, 1.0, 1.0, 8.0, 26.0],
                                  [1700723886.3765514, 0.0, 3.0, 13.0, 21.0, 0.0, 0.0, 3.0, 11.0],
                                  [1700723886.5506241, 5.0, 0.0, 11.0, 23.0, 0.0, 0.0, 1.0, 13.0],
                                  [1700723886.7209494, 0.0, 1.0, 10.0, 28.0, 0.0, 1.0, 0.0, 18.0],
                                  [1700723886.89586,   0.0, 0.0, 11.0, 23.0, 0.0, 0.0, 1.0, 13.0],
                                  [1700723887.0686586, 0.0, 0.0, 16.0, 27.0, 0.0, 7.0, 6.0, 17.0],
                                  [1700723887.3816106, 1.0, 0.0, 18.0, 20.0, 1.0, 0.0, 8.0, 10.0],
                                  [1700723887.551227,  1.0, 0.0, 10.0, 24.0, 1.0, 0.0, 0.0, 24.0],
                                  [1700723888.6048694, 0.0, 0.0, 17.0, 22.0, 2.0, 0.0, 7.0, 22.0],
                                  [1700723888.8363566, 6.0, 1.0, 11.0, 21.0, 0.0, 1.0, 1.0, 21.0],
                                  [1700723889.042608,  1.0, 1.0, 18.0, 26.0, 1.0, 1.0, 8.0, 26.0],
                                  [1700723889.3765514, 0.0, 0.0, 23.0, 21.0, 0.0, 0.0, 3.0, 21.0],
                                  [1700723889.5506241, 0.0, 0.0, 21.0, 23.0, 0.0, 0.0, 1.0, 23.0],
                                  [1700723889.7209494, 0.0, 1.0, 30.0, 28.0, 0.0, 1.0, 0.0, 18.0],
                                  [1700723889.89586,   0.0, 0.0, 11.0, 23.0, 0.0, 0.0, 1.0, 13.0],
                                  [1700723890.0686586, 0.0, 0.0, 16.0, 27.0, 2.0, 0.0, 6.0, 17.0],
                                  [1700723890.3816106, 1.0, 0.0, 18.0, 20.0, 1.0, 0.0, 8.0, 10.0],
                                  [1700723890.551227,  1.0, 0.0, 10.0, 24.0, 1.0, 0.0, 0.0, 14.0]
                                  ]
                if self.temp_counter == len(raw_counts) - 1:
                    return
                self.temp_counter += 1
                counts = [raw_counts[self.temp_counter]]

            else:
                counts = self.sq.get_counts(self.sq.N)

            # TODO: do something with timestamps
            #timestamps = []   # resetting here means we are only getting the timestamps for current measurement of size N
            for row in counts:
                #timestamps.append(row[0])
                self.data.append(row[1:])
                self.cumulative_ch_counts += np.array(row[1:])

    def scanning(self):
        if self.running:   # if start button is active
            self.get_counts()  # saves data to self.data. note that live graph updates every second using self.data
            self.save_data(mode="a")
        self.root.after(1000, self.scanning)  # After 1 second, call scanning

    def save_data(self, mode):
        #print("saving data")
        data_str = []
        for row in self.data:
            vals = [str(int(x)) for x in row]
            data_str.append(' '.join(vals)+' \n')
        with open("counts_file.txt", mode) as file:   # FIXME need to make sure that new scan => new/empty file
            file.writelines(data_str)  # TODO maybe add time of each
        self.data = []  # removing data that is now saved in file

    def start_scan_widget(self, tab):

        def press_start():
            self.save_data(mode="w")   # TODO: maybe only have this once per new measurement (so that we can pause and start again)
            # True:     if we have successfully configured the device
            # False:    failed to do all configs to device, should not start scan
            # None:     did not send new configs, will check but can start scan anyway (maybe??)
            outcome = {True : 'green', False : 'red', None : 'grey'}
            self.mark_done(btn_start, highlight=outcome[self.config_success], type='button')
            self.mark_done(btn_stop, highlight=self.button_color, type='button')
            self.running = True
            #print(f"START: RUNNING SCAN IS {self.running}")

        def press_stop():
            self.running = False
            #print(f"STOP: RUNNING SCAN IS {self.running}")
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

    def plot_live_histo(self, tab):

        def update_histo():  # TODO: add data conversion for respective unit
            if self.y_max < 1.2*max(self.cumulative_ch_counts):
                self.y_max = self.y_max*2

            fig.clear()
            plot1 = fig.add_subplot(111)
            plot1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%1.0f'))
            plot1.set_xlabel('λ (nm)')
            plot1.set_ylabel('photon count')
            plot1.set_title("Intensity")
            plot1.set_ylim([0, self.y_max])
            N, bins, bars = plot1.hist(x, bins=b, weights=self.cumulative_ch_counts, rwidth=0.9, align='left')
            plot1.bar_label(bars)
            canvas.draw()

            # go to idle state if we are not running a scan (reading counts)
            if not self.running:
                self.root.after(1000, idle)   # updates every second todo: maybe change
            else:
                self.root.after(1000, update_histo)   # updates every second todo: maybe change

        def idle():
            # go back to plotting counts when running scan (from idle state)
            if self.running:
                self.root.after(1000, update_histo)  # updates every second todo: maybe change
            else:
                self.root.after(1000, idle)  # updates every second todo: maybe change

        # --------
        self.y_max = 1000  # initial value??

        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9][:self.sq.number_of_detectors])   # todo:  change this to re a list of the wavelengths note the last channel is fake
        self.cumulative_ch_counts = np.zeros(self.sq.number_of_detectors)  # starting with 8 channels for now

        fig = plt.Figure(figsize=(9, 5), dpi=100)
        plot1 = fig.add_subplot(111)

        plot1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%1.0f'))

        plot1.set_xlabel('λ (nm)')
        plot1.set_ylabel('photon count')
        plot1.set_title("Intensity")
        plot1.set_ylim([0, self.y_max])
        b = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5]

        N, bins, bars = plot1.hist(x, bins=b,  weights=self.cumulative_ch_counts, rwidth=0.9, align='left')
        # maybe if data is a dict --> use counted_data.keys(), weights = counted_data.values()

        plt_frame, canvas = self.pack_plot(tab, fig)

        update_histo()

        return plt_frame

    def plot_spectrum_widget(self, tab):
        # TODO: make it live? live graph???

        def pressed_xlabel():  # TODO: add data conversion for respective unit
            fig.clear()
            plot1 = fig.add_subplot(111)
            plot1.plot(xar_b, yar_b, 'b')
            plot1.plot(xar_r, yar_r, 'r')
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
        line_r, = plot1.plot(xar_r, yar_r, 'r')  # , marker='.')
        plot1.set_xlabel(self.x_label.get())
        plot1.set_ylabel("counts")
        plot1.set_title("Spectrum")

        plt_frame, canvas = self.pack_plot(tab, fig)

        # BUTTONS:
        butt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(butt_frame, text=f'Change X-axis to:').grid(row=0, column=0, sticky="nsew")
        tk.Radiobutton(butt_frame, text="wavelength", value='λ [nm]', variable=self.x_label, command=pressed_xlabel).grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="frequency", value='f [Hz]', variable=self.x_label, command=pressed_xlabel).grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="photon energy", value='E [eV]', variable=self.x_label, command=pressed_xlabel).grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="spectroscopic wave number", value='v [cm^-1]', variable=self.x_label, command=pressed_xlabel).grid(row=4, column=0, sticky="ew", padx=0, pady=0)

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

    def plot_3D_lifetime_widget(self, tab):
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
        time.sleep(1)
        print("Closing SP AND WebSQ connections!")
        self.sp.disconnect()  # closes connection with spectrometer
        self.sq.close_connection()  # close SQWeb connection

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


# TODO: look into exceptions, plan for window crashing

#-----
demo = True
gui = GUI()
try:
    gui.root.after(1000, gui.scanning)  # After 1 second, call scanning
    gui.root.mainloop()

except KeyboardInterrupt:
    print("ERROR: PROGRAM INTERRUPTED EARLY.")
    #gui.close()  # Close all external connections
    raise

except SystemExit:
    print("system exit")
    raise

except tkinter.EXCEPTION:
    print("tkinter exception")
    raise

except serial.SerialException:
    print("serial exception")
    raise

finally:
    print("Finally:")
    gui.close()  # Close all external connections



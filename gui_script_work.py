import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import time
import serial
from datetime import date
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backend_bases import key_press_handler

from test_data import *


# TODO:
#  - Separate or remove demo mode
#  - live graph for all plots
#       - NOTE PLOTS SHOULD BE HISTOGRAMS
#  - Fix __exit__ method (find out how and why and what)
#  - search for available ports and ask to connect to correct one
#       --> make a "connection tab" to connect device first...
#       --> find out how to list available/active ports as options (dropdown list)
#  - fix "check device" layout
#  - add a tab with one button per command to read to device one by one, and display response??
#  - maybe add a thing (when pressing start scan button) that checks (reads) current device configs and compares to desired. if not a match then abort scan
#  - make a print tab to the right where "progress" is being shown :)"
#  - plots
#  - ETA data saving and reading
#  - Display counts
#  - Add buttons for "setting" configurations (and indication/display of what is set)
#  - Add scrollbar for counts display (for when we have many)
#  - Add integration time
#  - self.defaults  -->  Create config file where defaults can be saved and read from


# grating levels: 150, 300, 600   gr/mm
# blaze: 1.6, 1.7, 1.6 microns

# settings: (things not easily configurable)
# nr of pixels (12)
# pixel width  (about 10-20 microns)
# spectral width (total wavelength range/width ) -->

class Demo:
    def __init__(self):
        self.device_grating = 2
        self.device_wavelength = 749.997

class SP2750:

    def __init__(self):
        # Serial connection settings:
        self.handle = None
        self.port = "COM4"        # usb port
        self.demo = True            # NOTE: use this for testing program without connecting to spectrometer

        if self.demo:
            self.device_grating = 2
            self.device_wavelength = 749.997

        # TODO fill out list!!
        self.dict = {
            'gratings list': {
                'value type': None,
                'cmd': "?GRATINGS",
                'info': '',
                'access': ['read']
            },
            'grating' : {
                'value type': 'discrete',
                'values' : [1, 2, 3],
                'cmd' : "?GRATING",
                'info' : '',
                'access': ['read', 'write']
            },
            'nm': {
                'value type': 'range',
                'min': 300,
                'max': 800,   # FIXME
                'cmd': "?NM",
                'info': '',
                'access': ['read', 'write']

            },
            'nm/min': {
                'value type': 'range',
                'min': 90,  # FIXME
                'max': 100, # FIXME
                'cmd': "?NM/MIN",   # FIXME
                'info': '',
                'access': ['read', '']   # FIXME, NOTE: not fully implemented yet
            },
            'slit': {    # TODO CHECK FIXME; UNSURE IF IT'S EVEN AUTOMATED BY THE SPECTROMETER
                'value type': None,
                'min': 000,
                'max': 000,
                'cmd': None,  # FIXME
                'info': '',
                'access': ['', '']   # NOTE: not fully implemented yet

            }
        }

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("__EXIT__  method called")
        pass   # FIXME

    def connect(self):
        if self.demo:
            return

        try:
            print("Establishing connection...")
            self.handle = serial.Serial(port=self.port, baudrate=9600, parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)  # , timeout=self.serial_timeout)
            if self.handle:
                print(f"Successfully connected to PORT: {self.port}\nSerial handle:", self.handle)
            else:
                print("ERROR: handle still None")

        except serial.SerialException:
            print(f"ERROR: could not connect to PORT: {self.port}")
            if self.handle:
                self.disconnect()
            raise

    def disconnect(self):
        if self.demo:
            return

        if self.handle is None:
            print("Not connected to device --> don't need to disconnect")
            return

        time.sleep(1)
        self.handle.close()
        self.handle = None
        print("Connection Closed!")

    def strip_response(self, res):
        if self.demo:
            res = b'?NM ok\r\n'
        res_s = res.decode("ASCII")
        return res_s

    def wait_for_read(self):
        #print('wait for read')
        if self.demo:
            return None

        elif self.handle is None:
            print("ERROR: Not connected to device!")
            return

        elif not self.handle.isOpen():
            print("ERROR: Device not open!")
            return None

        # reads response every second and waits until request is complete.
        res = b''
        for i in range(60):
            if b'ok' in res:
                print('done')
                return res
            else:
                time.sleep(0.1)
                res_r = self.handle.readline()
                #res_r = self.handle.read()
                print(res_r)
                res += res_r
        print('fail')

    def read_cmd(self, param):

        if param not in self.dict.keys():
            print("ERROR: UNKNOWN READ param")
            return None

        if 'read' not in self.dict[param]['access']:
            print(f"ERROR: MISSING READ PRIVILEGES for {param}")
            return None

        if self.demo:
            print(f"DEMO: SUCCESS READ FOR {param} ")
            if param == 'nm':
                return self.device_wavelength
            elif param == 'grating':
                return self.device_grating
            else:
                return None

        if self.handle is None:
            print("ERROR: Not connected to device!")
            return None

        elif not self.handle.isOpen():
            print("ERROR: Device not open!")
            return None

        print(f"\nReading {param}...")
        cmd = self.dict[param]['cmd']
        cmd_bytes = cmd.encode("ASCII") + b'\r'
        self.handle.write(cmd_bytes)
        res = self.wait_for_read()
        print("Read Response =", res)

        res_num = ''
        res = res[1:].decode('ASCII')

        for i in range(len(res)):
            if res[i] == ' ' and len(res_num) > 0:
                break
            elif res[i] == 'o':
                print('break at o in ok')
                break
            else:
                res_num += res[i]
        #b' 699.995 nm  ok\r\n'
        val = eval(res_num)
        return val

    def write_cmd(self, param, value):
        # Check if parameter is correctly defined
        if param not in self.dict.keys():
            print(f"ERROR: BAD WRITE param ({param})")
            return False

        if 'write' not in self.dict[param]['access']:
            print(f"ERROR: MISSING WRITE PRIVILEGES for {param}")
            return False

        # Checks if desired value is ok
        if self.dict[param]['value type'] == 'discrete':
            value = int(value)
            if value not in self.dict[param]['values']:
                print(f"ERROR: VALUE {value} NOT ALLOWED")
                return False


        elif self.dict[param]['value type'] == 'range':
            value = float(value)
            if not (self.dict[param]['min'] <= value <= self.dict[param]['max']):
                print(f"ERROR: VALUE {value} NOT IN ALLOWED RANGE")
                return False

        else:
            print(f"ERROR: UNKNOWN VALUE TYPE FOR {param}")
            return False

        if self.demo:
            print(f"DEMO: SUCCESS WRITE FOR {param} --> {value}")

            if param == 'nm':
                self.device_wavelength = value - 0.003
            elif param == 'grating':
                self.device_grating = value

            return True

        if self.handle is None:
            print("ERROR: Not connected to device!")
            return None

        elif not self.handle.isOpen():
            print("ERROR: Device not open!")
            return None

        print(f"\nWriting {param} --> {value}")

        cmd = f"{value} {self.dict[param]['cmd'][1:]}"
        cmd_bytes = cmd.encode("ASCII") + b'\r'
        #print('cmd=', cmd_bytes)

        #ask = input(f"QUESTION: Is cmd {cmd_bytes} good? __(y/n)__")
        #if ask in ['y', 'yes', 'Y', 'YES']:
        self.handle.write(cmd_bytes)
        res = self.wait_for_read()
        #print("Write Response =", res)
        #else:
        #    res = b""
        #    print('rejected cmd by user')
        #    return False

        if b'ok' in res:
            return True

        print('ERROR: bad response...')
        return False


class GUI:

    def __init__(self):

        # initialize communication class with spectrometer
        self.sp = SP2750()

        # Create and configure the main GUI window
        self.init_window()

        # define global variables
        self.init_parameters()

        # Create and place tabs frame on window grid
        self.init_fill_tabs()

    def init_parameters(self):
        self.demo_connect = False  # temp for demo to check if we've actually connected to device

        self.current_file_name = None
        self.current_file_type = None
        self.current_file_path = None

        self.widgets = {}
        self.buttons = {}  # todo, do we need or use these?
        self.defaults = {}
        self.button_color = 'grey'  # default button colors

        # Variables:
        self.port = tk.StringVar()     # note maybe change later when implemented

        self.slit = tk.IntVar(value=10)
        self.grating = tk.IntVar(value=1)
        self.center_wavelength = tk.IntVar(value=600)
        self.width_wavelength = tk.IntVar()  # TODO fill in value
        self.nr_pixels = tk.IntVar(value=8)
        self.channels = []

        self.file_name = tk.StringVar()
        self.file_folder = tk.StringVar()
        self.eta_recipe = tk.StringVar()

        self.x_label = tk.StringVar(value='λ [nm]')

        self.device_slit = None
        self.device_grating = None
        self.device_wavelength = None

        self.config_success = None   # None if not tried to configure yet
        self.checked_configs = False
        self.ok_to_send_list = []

        self.grating_levels = {    # FIXME
            1: {'grating': 600, 'blz': '750 nm'},
            2: {'grating': 150, 'blz': '800 nm'},
            3: {'grating': 1800, 'blz': 'H-VIS'},
        }
        self.defaults = {
            'grating':           {
                'variable': self.grating,
                'type':     'radio',
                'value':    [1, 2, 3]
            },

            'center_wavelength': {
                'variable': self.center_wavelength,
                'type':     'int entry',
                'value':    [350, 650, 750]},

            'width_wavelength':  {
                'variable': self.width_wavelength,
                'type':     'int entry',
                'value':    [5, 15, 30]},

            'slit':              {
                'variable': self.slit,
                'type':     'int entry',
                'value':    [10, 20, 30]},

            'nr_pixels':         {
                'variable': self.nr_pixels,
                'type':     'int entry',
                'value':    [3, 8, 12]},

            'new_file_name':     {
                'variable': self.file_name,
                'type':     'str entry',
                'value':    ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},

            'new_folder_name':   {
                'variable': self.file_folder,
                'type':     'str entry',
                'value':    ['~/Desktop/GUI/Data1', '~/Desktop/GUI/Data2', '~/Desktop/GUI/Data3']},

            'eta_recipe':        {
                'variable': self.eta_recipe,
                'type':     'str entry',
                'value':    ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }

    def init_window(self):
        self.window = tk.Tk()
        self.window.title("Quantum Spectrometer GUI - Ghostly matters")   # *Ghostly matters*
        self.window.rowconfigure(0, minsize=30, weight=1)   # TODO: check if we need this
        self.window.columnconfigure(0, minsize=50, weight=1)  # TODO: check if we need this
        #self.window.geometry('1200x700+200+100')
        #self.window.state('zoomed')   # TODO: check if we need this
        self.window.config(background='#fafafa')

    def init_fill_tabs(self):

        def scan_tab():
            new_scan_tab = ttk.Frame(tabControl)

            # ---- Start new scan TAB ----  NOTE this should include settings and prep
            start_tab = tk.Frame(new_scan_tab, relief=tk.RAISED, bd=2)   # frame to gather things to communicate with devices

            self.widgets['param_config'] = self.choose_param_configs_widget(new_scan_tab)
            #self.widgets['live_spectrum'] = self.plot_live_spectrum_widget(new_scan_tab)
            self.widgets['live_spectrum'] = self.plot_histo(new_scan_tab)  # TRYING HISTO

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

            plt_frame, butt_frame = self.plot_spectrum_widget(plots_spectrum)
            self.widgets['plot_spectrum_1'] = plt_frame
            self.widgets['plot_spectrum_1'].grid(row=0, rowspan=4, column=0, sticky="nsew", padx=0, pady=0)

            self.widgets['info_spectrum'] = self.plot_display_info_widget(plots_spectrum, "Spectrum plot info")
            self.widgets['info_spectrum'].grid(row=0, rowspan=3, column=1, sticky="nsew" , padx=0, pady=0)

            self.widgets['butt_spectrum_1'] = butt_frame
            self.widgets['butt_spectrum_1'].grid(row=3, column=1, sticky="nsew", padx=0, pady=0)

            tabControl.add(plots_spectrum, text='Spectrum Plot')

        def plot_correlation_tab():
            plots_correlation = ttk.Frame(tabControl)

            #self.widgets['plot_correlation_1'] = self.plot_correlation_widget(plots_correlation)
            #self.widgets['plot_correlation_1'].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            #self.widgets['info_correlation'] = self.plot_display_info_widget(plots_correlation, "Correlation plot info")
            #self.widgets['info_correlation'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=0, pady=0)

            tabControl.add(plots_correlation, text='Correlation Plot')

        def plot_lifetime_tab():
            plots_lifetime = ttk.Frame(tabControl)

            #self.widgets['plot_lifetime_1'] = self.plot_lifetime_widget(plots_lifetime)
            #self.widgets['plot_lifetime_1'].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            #self.widgets['info_lifetime'] = self.plot_display_info_widget(plots_lifetime, "Lifetime plot info")
            #self.widgets['info_lifetime'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=0, pady=0)

            tabControl.add(plots_lifetime, text='Lifetime Plot')

        def plot_3d_lifetime_tab():
            plots_3d_lifetime = ttk.Frame(tabControl)

            #self.widgets['plot_3D_lifetime_1'] = self.plot_3D_lifetime_widget(plots_3d_lifetime)
            #self.widgets['plot_3D_lifetime_1'].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            #self.widgets['info_3D_lifetime'] = self.plot_display_info_widget(plots_3d_lifetime, "3D Lifetime plot info")
            #self.widgets['info_3D_lifetime'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=0, pady=0)

            tabControl.add(plots_3d_lifetime, text='3D Lifetime Plot')

        def settings_tab():  # FIXME
            settings_tab = ttk.Frame(tabControl)

            tabControl.add(settings_tab, text='Settings')

        # Create notebook for multi tab window:
        tabControl = ttk.Notebook(self.window)

        # Create and add tabs to notebook:
        scan_tab()
        plot_spectrum_tab()
        plot_correlation_tab()
        plot_lifetime_tab()
        plot_3d_lifetime_tab()
        settings_tab()

        # Pack all tabs in notebook to window:
        tabControl.pack(expand=1, fill="both")

    # GENERIC
    def add_to_grid(self, widg, rows, cols, sticky, columnspan=None):
        # EXAMPLE: self.add_to_grid(widg=[name_entry, folder_entry, recipe_entry], rows=[1,2,3], cols=[1,1,1], sticky=["ew", "ew", "ew"])
        for i in range(len(widg)):
            if columnspan:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], padx=0, pady=0, columnspan=columnspan[i])
            else:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], padx=0, pady=0)

    # GENERIC
    def mark_done(self, widget, highlight="white", text_color='black', type='button'):   # light green = #82CC6C
        if type == 'text':
            widget.config(foreground=text_color)  # green
        elif type == 'button':
            widget.config(highlightbackground=highlight)  # green
            widget.config(foreground=text_color)  # green
            widget.config(activeforeground='blue')   #maybe only reset for send btn ???

    def choose_param_configs_widget(self, tab):

        def press_connect():  # TODO
            if self.sp.demo:
                print("Demo: can't connect")
                self.mark_done(port_connect, highlight="green", text_color='black', type='button')
                self.demo_connect = True
                return

            self.sp.disconnect()
            self.sp.connect()
            self.sp.handle.write(b'NO-ECHO\r')
            res = self.sp.wait_for_read()  # b'  ok\r\n'
            print(res)
            port_entry.config(text=f'{self.sp.port}')

            if self.sp.handle is None:   # TODO: check if this ever happens
                self.mark_done(port_connect, highlight="red", text_color='black', type='button')
            elif self.sp.handle.isOpen():
                self.mark_done(port_connect, highlight="green", text_color='black', type='button')
            else:
                self.mark_done(port_connect, highlight="red", text_color='black', type='button')

        def reset_button_col():
            for button in [btn_def_1, btn_def_2, btn_def_3]:
                self.mark_done(button, highlight=self.button_color, type='button')

        def default_press(n=0):
            reset_button_col()
            if n == 0:
                print("Clear all")

                for key in self.defaults.keys():
                    if self.defaults[key]['type'] == 'radio':
                        self.defaults[key]['variable'].set(0)
                    elif self.defaults[key]['type'] == 'int entry':
                        self.defaults[key]['variable'].set(0)
                    elif self.defaults[key]['type'] == 'str entry':
                        self.defaults[key]['variable'].set('')
            else:
                self.mark_done(default_btns[n], highlight='green', type='button')
                for key in self.defaults.keys():
                    self.defaults[key]['variable'].set(self.defaults[key]['value'][n-1])     # note there can be several saved default sets

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
            for i in range(self.nr_pixels.get()):
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
        slt_entry = tk.Entry(frm_slit, bd=2, textvariable=self.slit, width=5)
        slt_unit = tk.Label(frm_slit, text='[um]')

        #  -- Grating:
        grt_txt = tk.Label(frm_grating, text='Grating')
        grt_txt_blz = tk.Label(frm_grating, text='Blaze')

        grt_rad_1 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[1]['grating'])+"  [gr/mm]", variable=self.grating, value=1, command=select_grating)
        grt_rad_2 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[2]['grating'])+"  [gr/mm]", variable=self.grating, value=2, command=select_grating)
        grt_rad_3 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[3]['grating'])+"  [gr/mm]", variable=self.grating, value=3, command=select_grating)

        grt_txt_1_blz = tk.Label(frm_grating, text="   "+self.grating_levels[1]['blz'])
        grt_txt_2_blz = tk.Label(frm_grating, text="   "+self.grating_levels[2]['blz'])
        grt_txt_3_blz = tk.Label(frm_grating, text="   "+self.grating_levels[3]['blz'])

        #  -- Detector:
        det_txt = tk.Label(frm_detect, text="Detector")

        det_wave_txt = tk.Label(frm_detect, text="Center λ")
        det_wave_val = tk.Entry(frm_detect, bd=2, textvariable=self.center_wavelength, width=6)
        det_wave_unit = tk.Label(frm_detect, text='[nm]')

        det_width_txt = tk.Label(frm_detect, text="Pixel width")
        det_width_val = tk.Entry(frm_detect, bd=2, textvariable=self.width_wavelength, width=6)
        det_width_unit = tk.Label(frm_detect, text='[nm]')

        det_no_txt = tk.Label(frm_detect, text="Nr. of pixels")
        det_no_val = tk.Entry(frm_detect, bd=2, textvariable=self.nr_pixels, width=6)
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
        #self.add_to_grid(widg=[det_width_txt, det_width_val, det_width_unit], rows=[2,2,2], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        self.add_to_grid(widg=[det_no_txt, det_no_val, ch_butt0], rows=[3,3,3], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        # -- Channels
        self.add_to_grid(widg=[ch_txt_ch, ch_txt_bias, ch_txt_cnts], rows=[0,0,0], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        fill_ch()  # Updates channels displayed

        # ------------- COMBINING INTO TEST FRAME --------------
        tk.Label(frm_test, text='Settings', font=('', 15)).grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.add_to_grid(widg=[frm_default, frm_port, frm_slit, frm_grating, frm_detect], rows=[1,2,3,4,5], cols=[0,0,0,0,0], sticky=["ew", "ew", "ew", "ew", "ew"])
        frm_ch.grid(row=6, column=0, rowspan=100, sticky="ew", padx=0, pady=0)

        return frm_test

    def choose_file_configs_widget(self, tab):

        def get_date():
            # returns date and time
            return date.today().strftime("%y%m%d"), time.strftime("%Hh%Mm%Ss", time.localtime())

        def get_recipe():
            self.eta_recipe = askopenfilename(filetypes=[("ETA recipe", "*.eta")])
            recipe_entry.delete(0, tk.END)
            recipe_entry.insert(0, self.eta_recipe)

        def get_folder():
            self.file_folder = askdirectory()
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, self.file_folder)

        def suggest_filename():
            currDate, currTime = get_date()
            temp = f"slit({self.slit.get()})_" \
                   f"grating({self.grating.get()})_" \
                   f"lamda({self.center_wavelength.get()})_" \
                   f"pixels({self.nr_pixels.get()})_" \
                   f"date({currDate})_time({currTime}).timeres"
            name_entry.delete(0, tk.END)
            name_entry.insert(0, temp)

        frm_misc = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(frm_misc, text="Analysis Configs").grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="(optional)").grid(row=0, column=2, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="New File Name").grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="New File Location").grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="ETA recipe").grid(row=3, column=0, sticky="ew", padx=0, pady=0)

        name_entry = tk.Entry(frm_misc, bd=2, textvariable=self.file_name, width=20)
        folder_entry = tk.Entry(frm_misc, bd=2, textvariable=self.file_folder, width=20)
        recipe_entry = tk.Entry(frm_misc, bd=2, textvariable=self.eta_recipe, width=40)

        butt0 = tk.Button(frm_misc, text="Suggest...", command=suggest_filename, activeforeground='blue', highlightbackground=self.button_color)
        butt1 = tk.Button(frm_misc, text="Open Folder", command=get_folder, activeforeground='blue', highlightbackground=self.button_color)
        butt2 = tk.Button(frm_misc, text="Choose File", command=get_recipe, activeforeground='blue', highlightbackground=self.button_color)

        self.add_to_grid(widg=[name_entry, folder_entry, recipe_entry], rows=[1,2,3], cols=[1,1,1], sticky=["ew", "ew", "ew"])
        self.add_to_grid(widg=[butt0, butt1, butt2], rows=[1,2,3], cols=[2,2,2], sticky=["ew", "ew", "ew"])

        return frm_misc

    def send_param_configs_widget(self, tab):

        def nothing():
            print("WARNING: CHECK YOUR VALUES BEFORE SENDING TO DEVICE")

        def get_str():
            temp1 = f"slit width = {self.device_slit} --> {self.slit.get()} [um]"
            temp2 = f"grating = {self.device_grating} --> {self.grating.get()} [gr/mm]"
            temp3 = f"center λ = {self.device_wavelength} --> {self.center_wavelength.get()} [nm]"
            return [temp1, temp2, temp3]

        def show_configs():
            temp = get_str()
            for i, widget in enumerate([send_txt_1, send_txt_2, send_txt_3]):
                widget.config(text=temp[i], foreground='black')   # make green for passed tests!

        def check():

            show_configs()

            self.ok_to_send_list = [] #reset
            print("\n--- CHECK VALUES ---")

            # todo: maybe should also check connection and values on device (if active/correct)

            check_list = [
                    ['slit', self.slit, send_txt_1, 'slit width'],   # todo: implement later
                    ['grating', self.grating, send_txt_2, 'grating', self.device_grating],
                    ['nm', self.center_wavelength, send_txt_3, 'center λ', self.device_wavelength],
                ]

            for check_thing in check_list:

                if not self.demo_connect:
                    if check_thing[0] == 'slit':
                        #tempi = f"{check_thing[3]} = {res}  -->  {check_thing[1].get()}"
                        tempi = "Device not connected"
                        self.mark_done(btn_send_conf, highlight='red', type='button')
                    else:
                        tempi = ''
                    check_thing[2].config(text=tempi, foreground='black')  # make green for passed tests!
                    self.mark_done(check_thing[2], text_color='red', type='text')  # ????
                    continue  # skip rest of loop iteration

                if check_thing[0] == 'slit':
                    continue  # not inplemented yet

                res = self.sp.read_cmd(param=check_thing[0])  # returns true if correctly configured
                print(" value =", res)

                """if check_thing[0] == 'grating':
                    res = self.grating_levels[res]['grating']
                    new = self.grating_levels[check_thing[1].get()]['grating']
                    tempi = f"{check_thing[3]} = {res}  -->  {new}"
                else:"""
                tempi = f"{check_thing[3]} = {res}  -->  {check_thing[1].get()}"

                check_thing[2].config(text=tempi, foreground='black')  # make green for passed tests!

                if res is None:
                    self.mark_done(check_thing[2], text_color='red', type='text')  # ????

                elif check_thing[1].get() is None:  # note: checks if right value is set
                    self.mark_done(check_thing[2], text_color='blue', type='text')  # passed test (temp)
                    self.ok_to_send_list.append(check_thing)

                elif round(float(res)) == round(float(check_thing[1].get())):  # note: checks if right value is set
                    self.mark_done(check_thing[2], text_color='green', type='text')  # passed test (temp)

                else:
                    # note: new value available!!
                    #print('res:', round(float(res)), '==', round(float(check_thing[1])), ':val')
                    self.mark_done(check_thing[2], text_color='blue', type='text')  # failed test (temp)
                    self.ok_to_send_list.append(check_thing)

                check_thing[4] = res  # TODO CHECK!!

            self.checked_configs = True

            if not self.demo_connect:
                self.mark_done(btn_send_conf, highlight='red', type='button')
            elif len(self.ok_to_send_list) > 0:
                self.mark_done(btn_send_conf, text_color='black', highlight='blue', type='button')
            else:
                self.mark_done(btn_send_conf, text_color='black', highlight='green', type='button')

            btn_send_conf.config(command=send)   # ACTIVATES SEND OPTION

        def send():
            if self.sp.demo:
                if not self.demo_connect:
                    self.mark_done(btn_send_conf, highlight='red', type='button')
                    return
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
                    '''self.ok_to_send_list = [
                        #['slit', self.slit.get(), send_txt_1],   # todo: implement later
                        ['grating', self.grating.get(), send_txt_2],
                        ['nm', self.center_wavelength.get(), send_txt_3], ]'''
                    return

                for thing in self.ok_to_send_list:
                    success = self.sp.write_cmd(param=thing[0], value=thing[1].get())   # returns true if correctly configured

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
        send_txt_2 = tk.Label(frm_send_values, text=temp[1], foreground='white', justify="left")
        send_txt_3 = tk.Label(frm_send_values, text=temp[2], foreground='white', justify="right")

        btn_check_conf = tk.Button(frm_send, text="Check values..", command=check, activeforeground='blue', highlightbackground=self.button_color)
        btn_send_conf = tk.Button(frm_send,  text="Send to Device", command=nothing, foreground='white', activeforeground='white') #, highlightbackground=self.button_color)

        self.add_to_grid(widg=[btn_check_conf, frm_send_values, btn_send_conf], rows=[0,1,2], cols=[0,0,0], sticky=["new", "new", "new"])
        self.add_to_grid(widg=[send_txt_1, send_txt_2, send_txt_3], rows=[0,1,2], cols=[0,0,0], sticky=["new", "new", "new"])

        return frm_send

    def start_scan_widget(self, tab):

        # Todo: add width to string
        def get_str():
            temp1 = f"slit = {self.slit.get()} [um]"
            temp2 = f"grating = {self.grating_levels[self.grating.get()]['grating']}"
            temp3 = f"center = {self.center_wavelength.get()} [nm]"
            #temp4 = f"width = {self.width_wavelength.get()} [nm]"
            #return [temp1, temp2, temp3, temp4]
            return [temp1, temp2, temp3]

        def start():
            # True:     if we have successfully configured the device
            # False:    failed to do all configs to device, should not start scan
            # None:     did not send new configs, will check but can start scan anyway (maybe??)
            outcome = {True:'green', False:'red', None:'grey'}
            self.mark_done(btn_start, highlight=outcome[self.config_success], type='button')
            self.mark_done(btn_stop, highlight=self.button_color, type='button')

        def stop():
            self.mark_done(btn_start, highlight=self.button_color, type='button')
            self.mark_done(btn_stop, highlight='red', type='button')

        temp = get_str()   # TODO: need to check if string has ok values!!! should nto send bad values!

        frm_send = tk.Frame(tab, relief=tk.RAISED, bd=2)

        btn_start = tk.Button(frm_send, text="Start\nScan", command=start, activeforeground='blue', highlightbackground=self.button_color, height=5, width=12)
        btn_stop = tk.Button(frm_send, text="Stop", command=stop, activeforeground='blue', highlightbackground=self.button_color, height=7, width=8)

        btn_start.grid(row=0, rowspan=4, column=0, sticky="nsew", padx=0, pady=1.5)
        btn_stop.grid(row=0, rowspan=4, column=1, sticky="nsew", padx=0, pady=1.5)

        return frm_send

    def plot_histo(self, tab):

        def test_data():
            yar_b = []
            yar_r = []
            for i in range(len(example_data_blue)):
                yar_b.append(example_data_blue[i][1])
            for i in range(len(example_data_red)):
                yar_r.append(example_data_red[i][1])
            return yar_b, yar_r
            # ---

        # creating the Tkinter canvas containing the Matplotlib figure
        temp_plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)
        plt_frame = tk.Frame(temp_plt_frame, relief=tk.RAISED, bd=2)

        # TEMP TEST VALUES FOR PLOTTING: ------------
        dx = 50
        start_x = self.center_wavelength.get() - ((self.nr_pixels.get()-1)/2)*dx
        histo_data_x = [start_x, start_x+(1*dx), start_x+(2*dx), start_x+(3*dx), start_x+(4*dx), start_x+(5*dx), start_x+(6*dx), start_x+(7*dx)]

        yar_b, yar_r = test_data()
        x = yar_b
        # --------------------------------------------

        fig = plt.Figure(figsize=(9, 5), dpi=100)
        plot1 = fig.add_subplot(111)

        plot1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%1.0f'))

        plot1.set_xlabel('λ (nm)')
        plot1.set_ylabel('photon count')
        plot1.set_title("Intensity")
        N, bins, bars = plot1.hist(x, bins=histo_data_x, rwidth=0.9)
        plot1.bar_label(bars)

        plotcanvas = FigureCanvasTkAgg(fig, master=plt_frame)
        plotcanvas.draw()   # <-- for static plotting??
        plotcanvas.get_tk_widget().grid(column=1, row=1)

        plt_frame.grid(row=1, column=0, padx=0, pady=0)
        return temp_plt_frame

    def plot_live_spectrum_widget(self, tab):

        def animate(i):
            if i < len(xar_b):
                xar_b.append(example_data_blue[i][0])
                yar_b.append(example_data_blue[i][1])
                line_b.set_data(xar_b, yar_b)
            if i < len(xar_r):
                xar_r.append(example_data_red[i][0])
                yar_r.append(example_data_red[i][1])
                line_r.set_data(xar_r, yar_r)
            if i > len(xar_b) and i > len(xar_r):
                print("DONE ANIMATING")

        # ----- LIVE -----
        xar_b = []
        yar_b = []
        xar_r = []
        yar_r = []

        #---
        #style.use('ggplot')
        fig = plt.Figure(figsize=(9, 5), dpi=100)
        plot1 = fig.add_subplot(111)
        plot1.set_xlim(1545, 1565)
        plot1.set_ylim(0, 5000)
        plot1.set_xlabel('λ (nm)')
        plot1.set_ylabel('photon count')
        plot1.set_title("Photoluminescence Intensity")
        line_b, = plot1.plot(xar_b, yar_b, 'b')
        line_r, = plot1.plot(xar_r, yar_r, 'r')

        # creating the Tkinter canvas containing the Matplotlib figure
        temp_plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)
        plt_frame = tk.Frame(temp_plt_frame, relief=tk.RAISED, bd=2)

        plotcanvas = FigureCanvasTkAgg(fig, master=plt_frame)
        plotcanvas.draw()   # <-- for static plotting??
        plotcanvas.get_tk_widget().grid(column=1, row=1)
        # ani = animation.FuncAnimation(fig, animate, interval=1000, blit=False)  # FIXME

        #toolbar = NavigationToolbar2Tk(plotcanvas, plt_frame)  # self.window)  # creating the Matplotlib toolbar
        #toolbar.update()
        #plotcanvas.get_tk_widget().pack()  # FIXME  # placing the canvas on the Tkinter window
        #tk.Label(temp_plt_frame, text="Live measurement plot", font=('', 18)).grid(row=0, column=0, padx=0, pady=0)

        plt_frame.grid(row=1, column=0, padx=0, pady=0)
        return temp_plt_frame

    def plot_spectrum_widget(self, tab):
        # TODO: create live graph???

        def pressed_xlabel():  # TODO: add data conversion for respective unit
            # x = ...
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

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)

        # TODO: Grid canvas as well???
        canvas = FigureCanvasTkAgg(fig, master=plt_frame)  # self.window)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(canvas, plt_frame)  # self.window)  # creating the Matplotlib toolbar
        toolbar.update()
        canvas.get_tk_widget().pack()  # placing the toolbar on the Tkinter window

        # BUTTONS:
        butt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(butt_frame, text=f'Change X-axis to:').grid(row=0, column=0, sticky="nsew")
        tk.Radiobutton(butt_frame, text="wavelength", value='λ [nm]', variable=self.x_label, command=pressed_xlabel).grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="frequency", value='f [Hz]', variable=self.x_label, command=pressed_xlabel).grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="photon energy", value='E [eV]', variable=self.x_label, command=pressed_xlabel).grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="spectroscopic wave number", value='v [cm^-1]', variable=self.x_label, command=pressed_xlabel).grid(row=4, column=0, sticky="ew", padx=0, pady=0)

        return plt_frame, butt_frame

    def plot_correlation_widget(self, tab):
        # TODO: incorporate real plot

        # the figure that will contain the plot
        fig = plt.Figure(figsize=(10, 3), dpi=100)

        # data list
        y = []

        # adding the subplot
        plot1 = fig.add_subplot(111)

        # plotting the graph
        plot1.plot(y)

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)
        canvas = FigureCanvasTkAgg(fig, master=plt_frame)  # self.window)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        # creating the Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, plt_frame)  # self.window)
        toolbar.update()

        # placing the toolbar on the Tkinter window
        canvas.get_tk_widget().pack()

        return plt_frame

    def plot_lifetime_widget(self, tab):
        # TODO: incorporate real plot

        # the figure that will contain the plot
        fig = plt.Figure(figsize=(10, 3), dpi=100)

        # data list
        y = []

        # adding the subplot
        plot1 = fig.add_subplot(111)

        # plotting the graph
        plot1.plot(y)

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)
        canvas = FigureCanvasTkAgg(fig, master=plt_frame)  # self.window)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        # creating the Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, plt_frame)  # self.window)
        toolbar.update()

        # placing the toolbar on the Tkinter window
        canvas.get_tk_widget().pack()

        return plt_frame

    def plot_3D_lifetime_widget(self, tab):
        # TODO: incorporate real plot

        # the figure that will contain the plot
        fig = plt.Figure(figsize=(10, 3), dpi=100)

        # data list
        y = []

        # adding the subplot
        plot1 = fig.add_subplot(111)

        # plotting the graph
        plot1.plot(y)

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)
        canvas = FigureCanvasTkAgg(fig, master=plt_frame)  # self.window)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        # creating the Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, plt_frame)  # self.window)
        toolbar.update()

        # placing the toolbar on the Tkinter window
        canvas.get_tk_widget().pack()

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


# real
gui = GUI()  # starts GUI
gui.window.mainloop()
gui.sp.disconnect()   # closes connection with spectrometer

print("Closing program!")


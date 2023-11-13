import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import time
import serial
from datetime import date
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler


# TODO:
#  - add port as option ---> or make a "connection tab" to connect device first... --> and find out how to list available/active ports as options (dropdown list)
#  - strip and extract values from real read response  (and write confirmation with 'ok'??)
#  - fix "check device" layout
#  - add a tab with one button per co mand to read to device one by one, and display response
#  -
#  - maybe add a thing (when pressing start scan button) that checks (reads) current device configs and compares to desired. if not a match then abort scan
#  - make a print tab to the right where "progress" is being shown :)"
#  - plots
#  - ETA data saving and reading
#  - Display counts
#  - Add buttons for "setting" configurations (and indication/display of what is set)
#  - Add scrollbar for counts display (for when we have many)
#  - Add integration time
#

# grating levels: 150, 300, 600   gr/mm
# blaze: 1.6, 1.7, 1.6 microns

# settings: (things not easily configurable)
# nr of pixels (12)
# pixel width  (about 10-20 microns)
# spectral width (total wavelength range/width ) -->

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
                'cmd': 'GRATINGS\r',
                'info': '',
                'access': ['read']
            },
            'grating' : {
                'value type': 'discrete',
                'values' : [1, 2, 3],
                'cmd' : 'GRATING\r',
                'info' : '',
                'access': ['read', 'write']
            },
            'nm': {
                'value type': 'range',
                'min': 0,
                'max': 2000,   # FIXME
                'cmd': 'NM\r',
                'info': '',
                'access': ['read', 'write']

            },
            'nm/min': {
                'value type': 'range',
                'min': 000,
                'max': 000,
                'cmd': 'NM/MIN\r',   # FIXME
                'info': '',
                'access': ['read', '']   # NOTE: not fully implemented yet
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
        pass   # TODO!!! FIXME

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

    def strip_response(self, res=''):
        if self.demo:
            res = b'?NM ok\r\n'
        res = res[:-2]  # removing carriage return and line feed
        res_s = res.decode("ASCII")
        #print(f"({res}) ({res_s}), ({len(res_s)})")
        return res_s

    def wait_for_read(self):

        if self.demo:
            return

        elif self.handle is None:
            print("ERROR: Not connected to device!")
            return

        elif not self.handle.isOpen():
            print("ERROR: Device not open!")
            return

        # reads response every second and waits until request is complete.
        for i in range(30):

            res_r = self.handle.readall()

            res = self.strip_response(res_r)   #res = res_r.decode("ASCII")

            if len(res) > 0:   # todo maybe increase idk?
                print(f"got response: '{res}'")
                return res

            print("waiting", i)
            time.sleep(1)

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
            print("ERROR: Not connected to device!")
            return None

        print(f"\nReading {param}...")
        cmd = f"?{self.dict[param]['cmd']}"
        self.handle.write(cmd.encode("ASCII"))
        res = self.wait_for_read()
        print("Read Response =", res)
        return res

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
            print("ERROR: Not connected to device!")
            return None

        print(f"\nWriting {param}... to: {value}")
        cmd = f"{value} {self.dict[param]['cmd']}"
        self.handle.write(cmd.encode("ASCII"))
        res = self.wait_for_read()
        print("Write Response =", res)

        if res == "":   # FIXME: check for actual confirmation
            return False
        return True


class GUI:

    def __init__(self):

        self.sp = SP2750()  # initial communication class with spectrometer
        #self.sp.connect()   # --> we are using a button instead to connect!

        # --- MAIN ----
        self.current_file_name = None
        self.current_file_type = None
        self.current_file_path = None

        self.widgets = {}

        self.buttons = {}  # todo ????

        self.defaults = {}

        self.button_color = 'grey'  # default button colors TODO DECIDE!

        # INIT WINDOW
        self.window = tk.Tk()
        self.window.title("Quantum Spectrometer GUI - Ghostly matters")   # *Ghostly matters*
        self.window.rowconfigure(0, minsize=30, weight=1)   # TODO: check if we need this
        self.window.columnconfigure(0, minsize=50, weight=1)  # TODO: check if we need this
        #self.window.geometry('1200x700+200+100')
        #self.window.state('zoomed')   # TODO: check if we need this
        self.window.config(background='#fafafa')

        # create and place tabs frame on window grid
        self.fill_tabs()

        self.define_default_settings()  # TODO: later save to and from file

    def define_default_settings(self):
        # TODO: Create config file where defaults can be saved and read from

        # EXAMPLE:
        # self.defaults = {'grating': {'variable': self.grating, 'type': 'radio', 'value': 1}}
        # self.defaults['grating']['variable'] = self.grating
        # self.defaults['grating']['type'] = 'radio'
        # self.defaults['grating']['value'] = 1

        self.defaults = {
            'grating': {
                'variable': self.grating,
                'type': 'radio',
                'value': [1, 2, 3]  # [150, 300, 600]
            },

            #'blaze': {   # connected to grating
            #    150: 1.6,
            #    300: 1.7,
            #    600: 1.6,
            #    'type': 'hardware'},

            'center_wavelength': {
                'variable': self.center_wavelength,
                'type': 'int entry',
                'value': [350, 650, 750]},

            'width_wavelength': {
                'variable': self.width_wavelength,
                'type': 'int entry',
                'value': [5, 15, 30]},

            'slit': {
                'variable': self.slit,
                'type': 'int entry',
                'value': [10, 20, 30]},

            'nr_pixels': {
                'variable': self.nr_pixels,
                'type': 'int entry',
                'value': [3, 8, 12]},

            'new_file_name': {
                'variable': self.file_name,
                'type': 'str entry',
                'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},

            'new_folder_name': {
                'variable': self.file_folder,
                'type': 'str entry',
                'value': ['~/Desktop/GUI/Data1', '~/Desktop/GUI/Data2', '~/Desktop/GUI/Data3']},

            'eta_recipe': {
                'variable': self.eta_recipe,
                'type': 'str entry',
                'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }

    def fill_tabs(self):

        def scan_tab():
            new_scan_tab = ttk.Frame(tabControl)

            # ---- Start new scan TAB ----  NOTE this should include settings and prep
            start_tab = tk.Frame(new_scan_tab, relief=tk.RAISED, bd=2)   # frame to gather things to communicate with devices

            self.widgets['param_config'] = self.choose_param_configs_widget(new_scan_tab)
            self.widgets['live_spectrum'] = self.plot_live_spectrum_widget(new_scan_tab)

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

            # ---- 1 Plots  TAB ----

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

            # ---- 2 Plots  TAB ----

            #self.widgets['plot_correlation_1'] = self.plot_correlation_widget(plots_correlation)
            #self.widgets['plot_correlation_1'].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            #self.widgets['info_correlation'] = self.plot_display_info_widget(plots_correlation, "Correlation plot info")
            #self.widgets['info_correlation'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=0, pady=0)

            tabControl.add(plots_correlation, text='Correlation Plot')

        def plot_lifetime_tab():
            plots_lifetime = ttk.Frame(tabControl)

            # ---- 3 Plots  TAB ----

            #self.widgets['plot_lifetime_1'] = self.plot_lifetime_widget(plots_lifetime)
            #self.widgets['plot_lifetime_1'].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            #self.widgets['info_lifetime'] = self.plot_display_info_widget(plots_lifetime, "Lifetime plot info")
            #self.widgets['info_lifetime'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=0, pady=0)

            tabControl.add(plots_lifetime, text='Lifetime Plot')

        def plot_3d_lifetime_tab():
            plots_3d_lifetime = ttk.Frame(tabControl)

            # ---- All Plots  TAB ----

            #self.widgets['plot_3D_lifetime_1'] = self.plot_3D_lifetime_widget(plots_3d_lifetime)
            #self.widgets['plot_3D_lifetime_1'].grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            #self.widgets['info_3D_lifetime'] = self.plot_display_info_widget(plots_3d_lifetime, "3D Lifetime plot info")
            #self.widgets['info_3D_lifetime'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=0, pady=0)

            tabControl.add(plots_3d_lifetime, text='3D Lifetime Plot')

        def settings_tab():
            settings_tab = ttk.Frame(tabControl)

            # ---- Settings and configurations  TAB ----
            # ... TODO

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

    def mark_done(self, widget, highlight="white", text_color='black', type='button'):   # light green = #82CC6C
        if type == 'text':
            widget.config(foreground=text_color)  # green
        elif type == 'button':
            widget.config(highlightbackground=highlight)  # green
            widget.config(foreground=text_color)  # green
            widget.config(activeforeground='blue')   #maybe only reset for send btn ???

    def choose_param_configs_widget(self, tab):

        def press_connect(): # TODO
            if self.sp.demo:
                print("Demo: can't connect")
                self.mark_done(port_connect, highlight="green", text_color='black', type='button')
                return

            self.sp.disconnect()
            #self.sp.port = self.port.get()
            self.sp.connect()
            port_entry.config(text=f'{self.sp.port}')

            if self.sp.handle is None:   # TODO: check if this ever happens
                self.mark_done(port_connect, highlight="red", text_color='black', type='button')
            elif self.sp.handle.isOpen():
                self.mark_done(port_connect, highlight="green", text_color='black', type='button')
            else:
                self.mark_done(port_connect, highlight="red", text_color='black', type='button')

        def reset_button_col():
            self.mark_done(btn_def_1, highlight=self.button_color, type='button')
            self.mark_done(btn_def_2, highlight=self.button_color, type='button')
            self.mark_done(btn_def_3, highlight=self.button_color, type='button')

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

        def select_grating():  # TODO?
            pass
            # selection = "\nChosen: " + str(self.grating.get())
            # label_choice.config(text=selection)
            # print("Updated grating to", str(self.grating.get()))

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
                tk.Label(frm_ch, text=f"Ch {i + 1}").grid(row=i + 2, column=0, sticky="ew", padx=0, pady=0)
                tk.Entry(frm_ch, bd=2, textvariable=self.channels[i], width=6).grid(row=i + 2, column=1, sticky="ew", padx=0, pady=0)

        # GLOBALS -----
        self.slit = tk.IntVar()
        self.grating = tk.IntVar()  # for choice of grating
        self.grating_levels = {    # FIXME
            0: {'grating': '', 'blz': ''},
            1: {'grating': 150, 'blz': 1.6},
            2: {'grating': 300, 'blz': 1.7},
            3: {'grating': 600, 'blz': 1.6},
        }
        self.port = tk.StringVar()     # note maybe change later when implemented
        self.port.set(self.sp.port)  # note maybe change later when implemented
        self.center_wavelength = tk.IntVar()
        self.width_wavelength = tk.IntVar()
        self.nr_pixels = tk.IntVar(value=8)
        self.channels = []
        # ---------------

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
        port_txt = tk.Label(frm_port, text='USB Port')
        #port_entry = tk.Entry(frm_port, bd=2, textvariable=self.port, width=5)   # FIXME later
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

        grt_txt_1_blz = tk.Label(frm_grating, text="   "+str(self.grating_levels[1]['blz'])+"  [um]")
        grt_txt_2_blz = tk.Label(frm_grating, text="   "+str(self.grating_levels[2]['blz'])+"  [um]")
        grt_txt_3_blz = tk.Label(frm_grating, text="   "+str(self.grating_levels[3]['blz'])+"  [um]")

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
        #det_no_unit = tk.Label(frm_detect, text='')
        ch_butt0 = tk.Button(frm_detect, text="Update", command=update_ch, activeforeground='blue', highlightbackground=self.button_color)  # NOTE: previously in channel frame below

        # -- Channels:
        ch_txt_ch = tk.Label(frm_ch, text='Channel')
        ch_txt_bias = tk.Label(frm_ch, text='Bias')
        ch_txt_cnts = tk.Label(frm_ch, text='Counts')

        # GRID
        # -- Default
        btn_clear.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        btn_def_1.grid(row=0, column=1, sticky="ew", padx=0, pady=0)
        btn_def_2.grid(row=0, column=2, sticky="ew", padx=0, pady=0)
        btn_def_3.grid(row=0, column=3, sticky="ew", padx=0, pady=0)

        # -- Port
        port_txt.grid(row=0, column=0, sticky="", padx=0, pady=0)
        port_entry.grid(row=0, column=1, sticky="", padx=0, pady=0)
        port_connect.grid(row=0, column=2, sticky="", padx=0, pady=0)

        # -- Slit
        slt_txt.grid(row=0, column=0, sticky="", padx=0, pady=0)
        slt_entry.grid(row=0, column=1, sticky="", padx=0, pady=0)
        slt_unit.grid(row=0, column=2, sticky="", padx=0, pady=0)

        # -- Grating
        grt_txt.grid(row=2, column=0, sticky="", padx=0, pady=0)
        grt_rad_1.grid(row=3, column=0, sticky="s", padx=0, pady=0)
        grt_rad_2.grid(row=4, column=0, sticky="s", padx=0, pady=0)
        grt_rad_3.grid(row=5, column=0, sticky="s", padx=0, pady=0)

        grt_txt_blz.grid(row=2, column=1, sticky="", padx=0, pady=0)
        grt_txt_1_blz.grid(row=3, column=1, sticky="s", padx=0, pady=0)
        grt_txt_2_blz.grid(row=4, column=1, sticky="s", padx=0, pady=0)
        grt_txt_3_blz.grid(row=5, column=1, sticky="s", padx=0, pady=0)

        # -- Detector
        det_txt.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)

        det_wave_txt.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        det_wave_val.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        det_wave_unit.grid(row=1, column=2, sticky="ew", padx=0, pady=0)

        #det_width_txt.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        #det_width_val.grid(row=2, column=1, sticky="ew", padx=0, pady=0)
        #det_width_unit.grid(row=2, column=2, sticky="ew", padx=0, pady=0)

        det_no_txt.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        det_no_val.grid(row=3, column=1, sticky="ew", padx=0, pady=0)
        #det_no_unit.grid(row=3, column=2, sticky="ew", padx=0, pady=0)   # there is no unit for number of channels
        #ch_butt0.grid(row=3, column=2, sticky="ew", padx=0, pady=0)   # updates the channels displayed

        # -- Channels
        ch_txt_ch.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        ch_txt_bias.grid(row=0, column=1, sticky="ew", padx=0, pady=0)
        ch_txt_cnts.grid(row=0, column=2, sticky="ew", padx=0, pady=0)
        fill_ch()

        # ------------- COMBINING INTO TEST FRAME --------------
        tk.Label(frm_test, text='Settings', font=('', 15)).grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        frm_default.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        frm_port.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        frm_slit.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        frm_grating.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        frm_detect.grid(row=5, column=0, sticky="ew", padx=0, pady=0)
        frm_ch.grid(row=6, column=0, rowspan=100, sticky="ew", padx=0, pady=0)

        return frm_test

    def choose_file_configs_widget(self, tab):

        def get_date():
            currDate = date.today().strftime("%y%m%d")
            currTime = time.strftime("%Hh%Mm%Ss", time.localtime())
            return currDate, currTime

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

        self.file_name = tk.StringVar()
        self.file_folder = tk.StringVar()
        self.eta_recipe = tk.StringVar()
        #self.misc4 = tk.IntVar()

        frm_misc = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(frm_misc, text="Analysis Configs").grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        tk.Label(frm_misc, text="(optional)").grid(row=0, column=2, sticky="ew", padx=0, pady=0)

        tk.Label(frm_misc, text="New File Name").grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        name_entry = tk.Entry(frm_misc, bd=2, textvariable=self.file_name, width=20)
        name_entry.grid(row=1, column=1, sticky="ew", padx=0, pady=0)
        butt0 = tk.Button(frm_misc, text="Suggest...", command=suggest_filename, activeforeground='blue', highlightbackground=self.button_color)
        butt0.grid(row=1, column=2, sticky="ew", padx=0, pady=0)

        tk.Label(frm_misc, text="New File Location").grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        folder_entry = tk.Entry(frm_misc, bd=2, textvariable=self.file_folder, width=20)
        folder_entry.grid(row=2, column=1, sticky="ew", padx=0, pady=0)
        butt1 = tk.Button(frm_misc, text="Open Folder", command=get_folder, activeforeground='blue', highlightbackground=self.button_color)
        butt1.grid(row=2, column=2, sticky="ew", padx=0, pady=0)

        tk.Label(frm_misc, text="ETA recipe").grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        recipe_entry = tk.Entry(frm_misc, bd=2, textvariable=self.eta_recipe, width=40)
        recipe_entry.grid(row=3, column=1, sticky="ew", padx=0, pady=0)
        butt2 = tk.Button(frm_misc, text="Choose File", command=get_recipe, activeforeground='blue', highlightbackground=self.button_color)
        butt2.grid(row=3, column=2, sticky="ew", padx=0, pady=0)

        #tk.Label(frm_misc, text="...?").grid(row=4, column=0, sticky="ew", padx=0, pady=0)
        #tk.Entry(frm_misc, bd=2, textvariable=self.misc4, width=40).grid(row=4, column=1, sticky="ew", padx=0, pady=0)

        return frm_misc

    def send_param_configs_widget(self, tab):

        def nothing():
            print("WARNING: CHECK YOUR VALUES BEFORE SENDING TO DEVICE")

        def get_str():
            temp1 = f"slit width = {self.device_slit} --> {self.slit.get()} [um]"
            temp2 = f"grating = {self.device_grating} --> {self.grating_levels[self.grating.get()]['grating']} [gr/mm]"
            temp3 = f"center λ = {self.device_wavelength} --> {self.center_wavelength.get()} [nm]"
            return [temp1, temp2, temp3]  # , temp4]

        def show_configs():
            temp = get_str()
            send_txt_1.config(text=temp[0], foreground='black')   # make green for passed tests!
            send_txt_2.config(text=temp[1], foreground='black')   # make green for passed tests!
            send_txt_3.config(text=temp[2], foreground='black')   # make green for passed tests!
            #send_txt_4.config(text=temp[3], foreground='black')   # make green for passed tests!

        def check():
            show_configs()

            self.ok_to_send_list = [] #reset
            print("\n--- CHECK VALUES ---")

            # todo: maybe should also check connection and values on device (if active/correct)

            check_list = [
                    #['slit', self.slit.get(), send_txt_1, 'slit width = '],   # todo: implement later
                    ['grating', self.grating.get(), send_txt_2, 'grating = '],
                    ['nm', self.center_wavelength.get(), send_txt_3, 'center λ = '],
                ]

            for check_thing in check_list:

                res = self.sp.read_cmd(param=check_thing[0])  # returns true if correctly configured
                print("    -->", res)
                tempi = check_thing[3]+str(res)+" --> "+str(check_thing[1])
                check_thing[2].config(text=tempi, foreground='black')  # make green for passed tests!

                if res is None:
                    self.mark_done(check_thing[2], text_color='red', type='text')  # ????

                elif round(float(res)) == round(float(check_thing[1])):  # note: checks if right value is set
                    self.mark_done(check_thing[2], text_color='green', type='text')  # passed test (temp)
                else:
                    # note: new value available!!
                    #print('res:', round(float(res)), '==', round(float(check_thing[1])), ':val')
                    self.mark_done(check_thing[2], text_color='blue', type='text')  # failed test (temp)
                    self.ok_to_send_list.append(check_thing)

            self.checked_configs = True
            self.mark_done(btn_send_conf, text_color='black', highlight='yellow', type='button')

            btn_send_conf.config(command=send)   # ACTIVATES SEND OPTION

        def send():
            print("\n--- SEND VALUES ---")

            #show_configs()

            print("Attempting to send configs to device...")
            if self.checked_configs:  # if we've double-checked currently set values
                self.mark_done(btn_send_conf, highlight=self.button_color, type='button')

                #try:   # woking parts will be marked green
                self.config_success = True

                """self.ok_to_send_list = [
                    ['slit', self.slit.get(), send_txt_1],   # todo: implement later
                    ['grating', self.grating.get(), send_txt_2],
                    ['nm', self.center_wavelength.get(), send_txt_3],
                ]"""

                for thing in self.ok_to_send_list:

                    success = self.sp.write_cmd(param=thing[0], value=thing[1])   # returns true if correctly configured

                    if success:   # true or false
                        #print(thing[0])
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

        def read_val():
            #self.sp.read_cmd('grating')
            #self.sp.read_cmd('nm')
            #self.sp.read_cmd('gratings list')  # all gratings
            pass

        self.device_slit = 0
        self.device_grating = 0
        self.device_wavelength = 0

        self.config_success = None   # None if not tried to configure yet
        self.checked_configs = False
        temp = get_str()
        self.ok_to_send_list = []

        frm_send = tk.Frame(tab, relief=tk.RAISED, bd=2)
        frm_send_values = tk.Frame(frm_send, relief=tk.RAISED, bd=2)

        send_txt_1 = tk.Label(frm_send_values, text=temp[0], foreground='white', justify="left")
        send_txt_2 = tk.Label(frm_send_values, text=temp[1], foreground='white', justify="left")
        send_txt_3 = tk.Label(frm_send_values, text=temp[2], foreground='white', justify="right")
        #send_txt_4 = tk.Label(frm_send_values, text=temp[3], foreground='white', justify="right")

        # NOTE: below is temp for testing success of failure
        #self.ok_to_send_list = [[send_txt_1, True], [send_txt_2, True], [send_txt_3, True]]  # , [send_txt_3, True]]
        #self.ok_to_send_list = [[send_txt_1, True], [send_txt_2, True], [send_txt_3, True]]  # , [send_txt_3, True]]

        btn_check_conf = tk.Button(frm_send, text="Check values..", command=check, activeforeground='blue', highlightbackground=self.button_color)
        btn_send_conf = tk.Button(frm_send,  text="Send to Device", command=nothing, foreground='white', activeforeground='white') #, highlightbackground=self.button_color)

        btn_check_conf.grid(row=0, column=0, sticky="new", padx=0, pady=0)
        frm_send_values.grid(row=1, column=0, sticky="new", padx=0, pady=0)
        btn_send_conf.grid(row=2, column=0, sticky="new", padx=0, pady=0)

        send_txt_1.grid(row=0, column=0, sticky="new", padx=0, pady=0)
        send_txt_2.grid(row=1, column=0, sticky="new", padx=0, pady=0)
        send_txt_3.grid(row=2, column=0, sticky="new", padx=0, pady=0)
        #send_txt_4.grid(row=3, column=0, sticky="new", padx=0, pady=0)

        return frm_send

    def start_scan_widget(self, tab):

        def get_str():
            temp1 = f"slit = {self.slit.get()} [um]"
            temp2 = f"grating = {self.grating.get()} "
            temp3 = f"center = {self.center_wavelength.get()} [nm]"
            temp4 = f"width = {self.width_wavelength.get()} [nm]"
            return [temp1, temp2, temp3, temp4]

        def start():
            self.mark_done(btn_stop, highlight=self.button_color, type='button')

            if self.config_success is True:
                self.mark_done(btn_start, highlight='green', type='button')           # if we have successfully configured the device

            elif self.config_success is False:
                self.mark_done(btn_start, highlight='red', type='button')    # failed to do all configs to device, should not start scan

            elif self.config_success is None:
                self.mark_done(btn_start, highlight='grey', type='button')  # did not send new configs, will check but can start scan anyway (maybe??)

            else:
                self.mark_done(btn_start, highlight='black', type='button')   # UNKNOWN ERROR

        def stop():
            self.mark_done(btn_stop, highlight='red', type='button')
            self.mark_done(btn_start, highlight=self.button_color, type='button')

        temp = get_str()   # TODO: need to check if string has ok values!!! should nto send bad values!

        frm_send = tk.Frame(tab, relief=tk.RAISED, bd=2)

        #send_txt_1 = tk.Label(frm_send, text=temp[0], foreground='white', justify="right")
        #send_txt_2 = tk.Label(frm_send, text=temp[1], foreground='white', justify="right")
        #send_txt_3 = tk.Label(frm_send, text=temp[2], foreground='white', justify="right")
        #send_txt_4 = tk.Label(frm_send, text=temp[3], foreground='white', justify="right")

        # TODO: make bigger!!
        btn_start = tk.Button(frm_send, text="Start\nScan", command=start, activeforeground='blue', highlightbackground=self.button_color, height=5, width=12)
        btn_stop = tk.Button(frm_send, text="Stop", command=stop, activeforeground='blue', highlightbackground=self.button_color, height=7, width=8)

        #send_txt_1.grid(row=0, column=0, sticky="new", padx=0, pady=0)
        #send_txt_2.grid(row=1, column=0, sticky="new", padx=0, pady=0)
        #send_txt_3.grid(row=2, column=0, sticky="new", padx=0, pady=0)
        #send_txt_4.grid(row=3, column=0, sticky="new", padx=0, pady=0)

        btn_start.grid(row=0, rowspan=4, column=0, sticky="nsew", padx=0, pady=1.5)
        btn_stop.grid(row=0, rowspan=4, column=1, sticky="nsew", padx=0, pady=1.5)

        return frm_send

    def plot_live_spectrum_widget(self, tab):

        """def animate(i):
            if i < len_b:
                xar_b.append(example_data_blue[i][0])
                yar_b.append(example_data_blue[i][1])
                line_b.set_data(xar_b, yar_b)
            if i < len_r:
                xar_r.append(example_data_red[i][0])
                yar_r.append(example_data_red[i][1])
                line_r.set_data(xar_r, yar_r)
            if i > len_r and i > len_b:
                print("DONE ANIMATING")"""

        # ----- LIVE -----
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

        #line_b, = plot1.plot(xar_b, yar_b, 'b') #, marker='o')
        #line_r, = plot1.plot(xar_r, yar_r, 'r') #, marker='.')

        # creating the Tkinter canvas containing the Matplotlib figure
        temp_plt_frame = tk.Frame(tab, relief=tk.RAISED, bd=2)
        plt_frame = tk.Frame(temp_plt_frame, relief=tk.RAISED, bd=2)

        plotcanvas = FigureCanvasTkAgg(fig, master=plt_frame)
        plotcanvas.draw()   # <-- for static plotting??
        plotcanvas.get_tk_widget().grid(column=1, row=1)
        #ani = animation.FuncAnimation(fig, animate, interval=1000, blit=False)

        # TODO: fix bug when clicking
        #toolbar = NavigationToolbar2Tk(canvas, plt_frame)  # self.window)  # creating the Matplotlib toolbar
        #toolbar.update()
        #canvas.get_tk_widget().pack()  # FIXME  # placing the canvas on the Tkinter window

        #tk.Label(temp_plt_frame, text="Live measurement plot", font=('', 18)).grid(row=0, column=0, padx=0, pady=0)
        plt_frame.grid(row=1, column=0, padx=0, pady=0)
        return temp_plt_frame

    def plot_spectrum_widget(self, tab):

        # TODO: create live graph???

        def pressed_xlabel():
            # TODO: add data conversion for respective unit
            # x = ...
            fig.clear()
            plot1 = fig.add_subplot(111)
            plot1.plot(xar_b, yar_b, 'b')  # , marker='o')
            plot1.plot(xar_r, yar_r, 'r')  # , marker='.')
            plot1.set_xlabel(x_label.get())
            plot1.set_ylabel("counts")
            plot1.set_title("Spectrum")
            canvas.draw()

        x_label = tk.StringVar()
        x_label.set('λ [nm]')

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
        plot1.set_xlabel('λ (nm)')
        plot1.set_ylabel('Intensity (arb. counts)')
        plot1.set_title("Photoluminescence Intensity")
        line_b, = plot1.plot(xar_b, yar_b, 'b')  # , marker='o')
        line_r, = plot1.plot(xar_r, yar_r, 'r')  # , marker='.')

        # adding the subplot
        #plot1 = fig.add_subplot(111)
        #plot1.plot(y)
        plot1.set_xlabel(x_label.get())
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
        tk.Radiobutton(butt_frame, text="wavelength", value='wavelength    λ [nm]', variable=x_label, command=pressed_xlabel).grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="frequency", value='frequency    f [Hz]', variable=x_label, command=pressed_xlabel).grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="photon energy", value='photon energy    E [eV]', variable=x_label, command=pressed_xlabel).grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        tk.Radiobutton(butt_frame, text="spectroscopic wave number", value='spectroscopic wave number    v [cm^-1]', variable=x_label, command=pressed_xlabel).grid(row=4, column=0, sticky="ew", padx=0, pady=0)

        return plt_frame, butt_frame


    def plot_correlation_widget(self, tab):
        # TODO: incorporate real plot

        # the figure that will contain the plot
        fig = plt.Figure(figsize=(10, 3), dpi=100)

        # list of squares
        y = [i ** 2 for i in range(101)]

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

        # list of squares
        y = [i ** 2 for i in range(101)]

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

        # list of squares
        y = [i ** 2 for i in range(101)]

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


example_data_blue = [
    [1544.9919761652648, 157.59214793177762   ],
    [1545.063993370471, 153.82742942957884    ],
    [1545.0960010172294, 178.9255527775722    ],
    [1545.1360105756773, 229.1217994735589    ],
    [1545.1840220458148, 266.76898449554847   ],
    [1545.256039251021, 251.71011048675246    ],
    [1545.28004498609, 225.3570809713592      ],
    [1545.3760679263648, 199.00405145596687   ],
    [1545.47209086664, 176.4157404427724      ],
    [1545.5681138069149, 168.88630343837485   ],
    [1545.66413674719, 157.59214793177762     ],
    [1545.7601596874651, 176.4157404427724    ],
    [1545.85618262774, 180.18045894497118     ],
    [1545.9522055680152, 183.94517744717086   ],
    [1546.04822850829, 195.2393329537672      ],
    [1546.0962399784278, 225.3570809713592    ],
    [1546.1442514485652, 259.2395474911509    ],
    [1546.2402743888404, 285.59257700654416   ],
    [1546.3362973291153, 274.2984214999469    ],
    [1546.4323202693904, 244.1806734823549    ],
    [1546.576354679803, 229.1217994735589     ],
    [1546.672377620078, 225.3570809713592     ],
    [1546.768400560353, 199.00405145596687    ],
    [1546.8164120304905, 165.12158493617517   ],
    [1546.9124349707656, 161.3568664339764    ],
    [1547.0084579110408, 150.06271092737916   ],
    [1547.1044808513157, 150.06271092737916   ],
    [1547.2005037915908, 153.82742942957884   ],
    [1547.296526731866, 153.82742942957884    ],
    [1547.3925496721408, 161.3568664339764    ],
    [1547.4165554072097, 138.76855542078283   ],
    [1547.4645668773471, 161.3568664339764    ],
    [1547.488572612416, 191.4746144515684     ],
    [1547.5605898176223, 183.94517744717086   ],
    [1547.5845955526909, 206.53348846036442   ],
    [1547.680618492966, 183.94517744717086    ],
    [1547.7766414332411, 176.4157404427724    ],
    [1547.872664373516, 161.3568664339764     ],
    [1547.9446815787223, 153.82742942957884   ],
    [1547.9686873137912, 180.18045894497118   ],
    [1547.9926930488598, 206.53348846036442   ],
    [1548.0166987839286, 240.41595498015522   ],
    [1548.0407045189975, 266.76898449554847   ],
    [1548.0727121657558, 299.3965448479403    ],
    [1548.088715989135, 342.0633545395285     ],
    [1548.1607331943412, 372.18110255712054   ],
    [1548.2327503995475, 357.12222854832453   ],
    [1548.2567561346164, 319.47504352633496   ],
    [1548.3047676047538, 274.2984214999469    ],
    [1548.3047676047538, 244.1806734823549    ],
    [1548.3527790748913, 210.2982069625632    ],
    [1548.400790545029, 183.94517744717086    ],
    [1548.4968134853038, 187.70989594936964   ],
    [1548.5688306905101, 168.88630343837485   ],
    [1548.592836425579, 183.94517744717086    ],
    [1548.688859365854, 153.82742942957884    ],
    [1548.784882306129, 146.29799242518038    ],
    [1548.8809052464042, 165.12158493617517   ],
    [1548.9289167165416, 191.4746144515684    ],
    [1548.9529224516104, 251.71011048675246   ],
    [1548.9529224516104, 221.59236246916043   ],
    [1548.976928186679, 289.35729550874294    ],
    [1549.0249396568167, 327.0044805307325    ],
    [1549.0729511269542, 308.1808880197377    ],
    [1549.1209625970916, 281.8278585043445    ],
    [1549.1689740672293, 244.1806734823549    ],
    [1549.2649970075042, 214.06292546476288   ],
    [1549.3610199477794, 199.00405145596687   ],
    [1549.4570428880543, 199.00405145596687   ],
    [1549.5530658283294, 199.00405145596687   ],
    [1549.6490887686045, 168.88630343837485   ],
    [1549.7451117088794, 176.4157404427724    ],
    [1549.8411346491546, 176.4157404427724    ],
    [1549.9371575894295, 183.94517744717086   ],
    [1550.0331805297046, 214.06292546476288   ],
    [1550.105197734911, 229.1217994735589     ],
    [1550.1292034699798, 259.2395474911509    ],
    [1550.1772149401172, 327.0044805307325    ],
    [1550.1772149401172, 296.8867325131405    ],
    [1550.201220675186, 477.5932206186935     ],
    [1550.201220675186, 447.4754726011015     ],
    [1550.201220675186, 417.35772458350857    ],
    [1550.201220675186, 387.23997656591655    ],
    [1550.201220675186, 357.12222854832453    ],
    [1550.2252264102547, 503.94625013408586   ],
    [1550.2332283219444, 537.8287166538776    ],
    [1550.2492321453235, 643.2408347154496    ],
    [1550.2492321453235, 613.1230866978576    ],
    [1550.2492321453235, 583.0053386802656    ],
    [1550.2732378803923, 823.9473228210018    ],
    [1550.2732378803923, 793.8295748034097    ],
    [1550.2732378803923, 763.7118267858177    ],
    [1550.2732378803923, 733.5940787682257    ],
    [1550.2732378803923, 703.4763307506337    ],
    [1550.2732378803923, 677.1233012352404    ],
    [1550.3212493505298, 1034.771558944146    ],
    [1550.3212493505298, 1004.6538109265539   ],
    [1550.3212493505298, 974.5360629089619    ],
    [1550.3212493505298, 944.4183148913698    ],
    [1550.3212493505298, 914.3005668737778    ],
    [1550.3212493505298, 884.1828188561858    ],
    [1550.3212493505298, 854.0650708385938    ],
    [1550.3452550855986, 823.9473228210018    ],
    [1550.3452550855986, 793.8295748034097    ],
    [1550.3452550855986, 763.7118267858177    ],
    [1550.3452550855986, 733.5940787682257    ],
    [1550.3452550855986, 703.4763307506337    ],
    [1550.3692608206673, 673.3585827330417    ],
    [1550.393266555736, 643.2408347154496     ],
    [1550.393266555736, 613.1230866978576     ],
    [1550.393266555736, 583.0053386802656     ],
    [1550.393266555736, 552.8875906626736     ],
    [1550.393266555736, 379.710539561519      ],
    [1550.417272290805, 515.2404056406831     ],
    [1550.417272290805, 485.1226576230911     ],
    [1550.417272290805, 455.00490960549905    ],
    [1550.417272290805, 424.88716158790703    ],
    [1550.417272290805, 394.769413570315      ],
    [1550.4412780258735, 357.12222854832453   ],
    [1550.4652837609424, 319.47504352633496   ],
    [1550.5132952310798, 281.8278585043445    ],
    [1550.5613067012173, 244.1806734823549    ],
    [1550.6573296414924, 229.1217994735589    ],
    [1550.7053411116299, 255.47482898895123   ],
    [1550.801364051905, 274.2984214999469     ],
    [1550.8493755220425, 319.47504352633496   ],
    [1550.953400374007, 329.5142928655323     ],
    [1551.017415667524, 349.592791543927      ],
    [1551.0414214025927, 372.18110255712054   ],
    [1551.1134386077988, 379.710539561519     ],
    [1551.1374443428676, 409.828287579111     ],
    [1551.185455813005, 447.4754726011015     ],
    [1551.2814787532802, 439.94603559670304   ],
    [1551.3534959584865, 432.4165985923046    ],
    [1551.3775016935554, 406.06356907691224   ],
    [1551.48152654552, 389.74978890071634     ],
    [1551.5455418390366, 409.828287579111     ],
    [1551.5695475741054, 436.18131709450427   ],
    [1551.6175590442429, 470.06378361429506   ],
    [1551.713581984518, 477.5932206186935     ],
    [1551.7855991897243, 470.06378361429506   ],
    [1551.809604924793, 500.1815316318871     ],
    [1551.905627865068, 500.1815316318871     ],
    [1552.0016508053432, 488.88737612528985   ],
    [1552.097673745618, 507.71096863628554    ],
    [1552.1696909508244, 492.65209462748953   ],
    [1552.2417081560307, 466.2990651120963    ],
    [1552.3377310963058, 439.94603559670304   ],
    [1552.3857425664432, 406.06356907691224   ],
    [1552.409748301512, 372.18110255712054    ],
    [1552.4337540365807, 345.8280730417282    ],
    [1552.5297769768558, 349.592791543927     ],
    [1552.5777884469933, 394.769413570315     ],
    [1552.681813298958, 417.35772458350857    ],
    [1552.7218228574059, 522.7698426450816    ],
    [1552.7218228574059, 492.65209462748953   ],
    [1552.7218228574059, 462.5343466098975    ],
    [1552.7458285924747, 733.5940787682257    ],
    [1552.7458285924747, 703.4763307506337    ],
    [1552.7458285924747, 673.3585827330417    ],
    [1552.7458285924747, 643.2408347154496    ],
    [1552.7458285924747, 613.1230866978576    ],
    [1552.7458285924747, 583.0053386802656    ],
    [1552.7458285924747, 552.8875906626736    ],
    [1552.7458285924747, 432.4165985923046    ],
    [1552.7698343275435, 967.0066259045643    ],
    [1552.7698343275435, 936.8888778869723    ],
    [1552.7698343275435, 906.7711298693803    ],
    [1552.7698343275435, 876.6533818517883    ],
    [1552.7698343275435, 846.5356338341962    ],
    [1552.7698343275435, 816.4178858166042    ],
    [1552.7698343275435, 786.3001377990122    ],
    [1552.7698343275435, 759.947108283619     ],
    [1552.777836239233, 1004.6538109265539    ],
    [1552.7938400626122, 1411.243409164047    ],
    [1552.7938400626122, 1381.125661146455    ],
    [1552.7938400626122, 1351.007913128863    ],
    [1552.7938400626122, 1320.890165111271    ],
    [1552.7938400626122, 1290.772417093679    ],
    [1552.7938400626122, 1260.654669076087    ],
    [1552.7938400626122, 1230.5369210584945   ],
    [1552.7938400626122, 1200.4191730409025   ],
    [1552.7938400626122, 1170.3014250233105   ],
    [1552.7938400626122, 1140.183677005719    ],
    [1552.7938400626122, 1110.0659289881269   ],
    [1552.7938400626122, 1079.9481809705348   ],
    [1552.7938400626122, 1049.830432952942    ],
    [1552.817845797681, 1915.7156884587143    ],
    [1552.817845797681, 1885.5979404411223    ],
    [1552.817845797681, 1855.4801924235298    ],
    [1552.817845797681, 1825.3624444059378    ],
    [1552.817845797681, 1795.2446963883458    ],
    [1552.817845797681, 1765.1269483707538    ],
    [1552.817845797681, 1735.0092003531618    ],
    [1552.817845797681, 1704.8914523355697    ],
    [1552.817845797681, 1674.7737043179777    ],
    [1552.817845797681, 1644.6559563003857    ],
    [1552.817845797681, 1614.5382082827937    ],
    [1552.817845797681, 1584.4204602652017    ],
    [1552.817845797681, 1554.3027122476092    ],
    [1552.817845797681, 1524.1849642300172    ],
    [1552.817845797681, 1494.0672162124251    ],
    [1552.817845797681, 1463.9494681948331    ],
    [1552.817845797681, 1437.5964386794403    ],
    [1552.8258477093705, 1953.3628734807044   ],
    [1552.8658572678185, 2450.305715770973    ],
    [1552.8658572678185, 2420.187967753381    ],
    [1552.8658572678185, 2390.070219735789    ],
    [1552.8658572678185, 2359.952471718197    ],
    [1552.8658572678185, 2329.834723700605    ],
    [1552.8658572678185, 2299.716975683013    ],
    [1552.8658572678185, 2269.599227665421    ],
    [1552.8658572678185, 2239.481479647829    ],
    [1552.8658572678185, 2209.363731630237    ],
    [1552.8658572678185, 2179.2459836126445   ],
    [1552.8658572678185, 2149.1282355950525   ],
    [1552.8658572678185, 2119.0104875774605   ],
    [1552.8658572678185, 2088.8927395598685   ],
    [1552.8658572678185, 2058.7749915422764   ],
    [1552.8658572678185, 2028.6572435246844   ],
    [1552.8658572678185, 1998.5394955070924   ],
    [1552.8898630028873, 1968.4217474895004   ],
    [1552.8898630028873, 1938.3039994719084   ],
    [1552.8898630028873, 1908.1862514543163   ],
    [1552.8898630028873, 1878.0685034367243   ],
    [1552.8898630028873, 1847.9507554191318   ],
    [1552.8898630028873, 1817.8330074015398   ],
    [1552.8898630028873, 1787.7152593839478   ],
    [1552.8898630028873, 1757.5975113663558   ],
    [1552.8898630028873, 1727.4797633487638   ],
    [1552.8898630028873, 1697.3620153311717   ],
    [1552.8898630028873, 1667.2442673135797   ],
    [1552.8898630028873, 1637.1265192959877   ],
    [1552.8898630028873, 1607.0087712783957   ],
    [1552.8898630028873, 1576.8910232608036   ],
    [1552.8898630028873, 1546.7732752432112   ],
    [1552.8898630028873, 1516.6555272256192   ],
    [1552.8898630028873, 1486.5377792080271   ],
    [1552.8898630028873, 1456.420031190435    ],
    [1552.8898630028873, 1426.302283172843    ],
    [1552.8898630028873, 1396.184535155251    ],
    [1552.8898630028873, 1366.066787137659    ],
    [1552.8898630028873, 1335.949039120067    ],
    [1552.8898630028873, 1305.831291102475    ],
    [1552.8898630028873, 1275.713543084883    ],
    [1552.8898630028873, 1245.595795067291    ],
    [1552.8898630028873, 1215.4780470496985   ],
    [1552.8898630028873, 1185.3602990321065   ],
    [1552.8898630028873, 1155.242551014515    ],
    [1552.8898630028873, 1125.1248029969229   ],
    [1552.8898630028873, 1095.0070549793309   ],
    [1552.8898630028873, 1064.889306961738    ],
    [1552.8898630028873, 1034.771558944146    ],
    [1552.9138687379561, 1004.6538109265539   ],
    [1552.9138687379561, 974.5360629089619    ],
    [1552.9138687379561, 944.4183148913698    ],
    [1552.9138687379561, 914.3005668737778    ],
    [1552.9138687379561, 884.1828188561858    ],
    [1552.9138687379561, 854.0650708385938    ],
    [1552.9138687379561, 823.9473228210018    ],
    [1552.9138687379561, 793.8295748034097    ],
    [1552.9138687379561, 763.7118267858177    ],
    [1552.9138687379561, 733.5940787682257    ],
    [1552.9138687379561, 703.4763307506337    ],
    [1552.9138687379561, 673.3585827330417    ],
    [1552.9138687379561, 643.2408347154496    ],
    [1552.9138687379561, 616.8878052000564    ],
    [1552.9618802080936, 575.4759016758671    ],
    [1552.9618802080936, 545.3581536582751    ],
    [1552.9618802080936, 515.2404056406831    ],
    [1553.0178935899207, 477.5932206186935    ],
    [1553.0579031483685, 545.3581536582751    ],
    [1553.0579031483685, 515.2404056406831    ],
    [1553.0819088834373, 477.5932206186935    ],
    [1553.0819088834373, 447.4754726011015    ],
    [1553.0819088834373, 417.35772458350857   ],
    [1553.1059146185062, 391.00469506811623   ],
    [1553.1779318237125, 379.710539561519     ],
    [1553.201937558781, 402.29885057471256    ],
    [1553.22594329385, 462.5343466098975      ],
    [1553.22594329385, 432.4165985923046      ],
    [1553.2579509406082, 495.1619069622884    ],
    [1553.2739547639874, 537.8287166538776    ],
    [1553.2979604990562, 564.1817461692699    ],
    [1553.305962410746, 598.0642126890616     ],
    [1553.3459719691937, 635.7113977110512    ],
    [1553.3699777042625, 598.0642126890616    ],
    [1553.3699777042625, 515.2404056406831    ],
    [1553.3939834393314, 560.4170276670711    ],
    [1553.3939834393314, 530.2992796494791    ],
    [1553.4179891744, 492.65209462748953      ],
    [1553.4179891744, 439.94603559670304      ],
    [1553.4419949094688, 455.00490960549905   ],
    [1553.4660006445376, 417.35772458350857   ],
    [1553.4900063796063, 379.710539561519     ],
    [1553.5460197614334, 347.0829792091272    ],
    [1553.6340407900188, 327.0044805307325    ],
    [1553.7060579952251, 334.53391753513097   ],
    [1553.730063730294, 364.651665552723      ],
    [1553.7780752004314, 402.29885057471256   ],
    [1553.8260866705689, 436.18131709450427   ],
    [1553.922109610844, 451.2401911033003     ],
    [1553.9461153459129, 477.5932206186935    ],
    [1553.9701210809815, 515.2404056406831    ],
    [1554.0661440212566, 515.2404056406831    ],
    [1554.1221574030837, 540.3385289886764    ],
    [1554.1861726966004, 545.3581536582751    ],
    [1554.2101784316692, 560.4170276670711    ],
    [1554.234184166738, 522.7698426450816     ],
    [1554.2581899018066, 485.1226576230911    ],
    [1554.2821956368755, 447.4754726011015    ],
    [1554.306201371944, 421.12244308570826    ],
    [1554.3782185771504, 417.35772458350857   ],
    [1554.4022243122192, 379.710539561519     ],
    [1554.4502357823567, 342.0633545395285    ],
    [1554.4982472524944, 327.0044805307325    ],
    [1554.5462587226318, 364.651665552723     ],
    [1554.602272104459, 402.29885057471256    ],
    [1554.618275927838, 447.4754726011015     ],
    [1554.642281662907, 481.3579391208923     ],
    [1554.6902931330444, 507.71096863628554   ],
    [1554.7383046031819, 477.5932206186935    ],
    [1554.7383046031819, 447.4754726011015    ],
    [1554.834327543457, 477.5932206186935     ],
    [1554.834327543457, 455.00490960549905    ],
    [1554.8823390135944, 507.71096863628554   ],
    [1554.9063447486633, 567.9464646714696    ],
    [1554.9063447486633, 537.8287166538776    ],
    [1554.930350483732, 601.8289311912604     ],
    [1554.9783619538696, 631.9466792088524    ],
    [1555.026373424007, 658.2997087242456     ],
    [1555.0743848941445, 639.4761162132509    ],
    [1555.1303982759716, 675.8683950678414    ],
    [1555.218419304557, 680.8880197374392     ],
    [1555.3144422448322, 650.7702717198472    ],
    [1555.3624537149697, 605.5936496934592    ],
    [1555.3624537149697, 583.0053386802656    ],
    [1555.434470920176, 567.9464646714696     ],
    [1555.434470920176, 537.8287166538776     ],
    [1555.4584766552448, 511.4756871384843    ],
    [1555.5064881253822, 477.5932206186935    ],
    [1555.530493860451, 455.00490960549905    ],
    [1555.6025110656574, 477.5932206186935    ],
    [1555.6745282708637, 522.7698426450816    ],
    [1555.6745282708637, 492.65209462748953   ],
    [1555.6985340059323, 552.8875906626736    ],
    [1555.74654547607, 586.7700571824644      ],
    [1555.8425684163449, 601.8289311912604    ],
    [1555.8665741514137, 748.6529527770217    ],
    [1555.8665741514137, 718.5352047594297    ],
    [1555.8665741514137, 688.4174567418377    ],
    [1555.8665741514137, 658.2997087242456    ],
    [1555.8665741514137, 628.1819607066536    ],
    [1555.8905798864826, 771.2412637902162    ],
    [1555.898581798172, 808.8884488122058     ],
    [1555.9145856215512, 1908.1862514543163   ],
    [1555.9145856215512, 1878.0685034367243   ],
    [1555.9145856215512, 1847.9507554191318   ],
    [1555.9145856215512, 1817.8330074015398   ],
    [1555.9145856215512, 1787.7152593839478   ],
    [1555.9145856215512, 1757.5975113663558   ],
    [1555.9145856215512, 1727.4797633487638   ],
    [1555.9145856215512, 1697.3620153311717   ],
    [1555.9145856215512, 1667.2442673135797   ],
    [1555.9145856215512, 1637.1265192959877   ],
    [1555.9145856215512, 1607.0087712783957   ],
    [1555.9145856215512, 1576.8910232608036   ],
    [1555.9145856215512, 1546.7732752432112   ],
    [1555.9145856215512, 1516.6555272256192   ],
    [1555.9145856215512, 1486.5377792080271   ],
    [1555.9145856215512, 1456.420031190435    ],
    [1555.9145856215512, 1426.302283172843    ],
    [1555.9145856215512, 1396.184535155251    ],
    [1555.9145856215512, 1366.066787137659    ],
    [1555.9145856215512, 1335.949039120067    ],
    [1555.9145856215512, 1305.831291102475    ],
    [1555.9145856215512, 1275.713543084883    ],
    [1555.9145856215512, 1245.595795067291    ],
    [1555.9145856215512, 1215.4780470496985   ],
    [1555.9145856215512, 1185.3602990321065   ],
    [1555.9145856215512, 1155.242551014515    ],
    [1555.9145856215512, 1125.1248029969229   ],
    [1555.9145856215512, 1095.0070549793309   ],
    [1555.9145856215512, 1064.889306961738    ],
    [1555.9145856215512, 1034.771558944146    ],
    [1555.9145856215512, 1004.6538109265539   ],
    [1555.9145856215512, 974.5360629089619    ],
    [1555.9145856215512, 944.4183148913698    ],
    [1555.9145856215512, 914.3005668737778    ],
    [1555.9145856215512, 884.1828188561858    ],
    [1555.9145856215512, 854.0650708385938    ],
    [1555.93859135662, 2051.2455545378784     ],
    [1555.93859135662, 2021.1278065202864     ],
    [1555.93859135662, 1991.0100585026944     ],
    [1555.93859135662, 1960.8923104851024     ],
    [1555.93859135662, 1934.5392809697091     ],
    [1555.9465932683097, 2088.8927395598685   ],
    [1555.9866028267575, 2495.482337797361    ],
    [1555.9866028267575, 2465.364589779769    ],
    [1555.9866028267575, 2435.246841762177    ],
    [1555.9866028267575, 2405.129093744585    ],
    [1555.9866028267575, 2375.011345726993    ],
    [1555.9866028267575, 2344.893597709401    ],
    [1555.9866028267575, 2314.775849691809    ],
    [1555.9866028267575, 2284.658101674217    ],
    [1555.9866028267575, 2254.540353656625    ],
    [1555.9866028267575, 2224.422605639033    ],
    [1555.9866028267575, 2194.3048576214405   ],
    [1555.9866028267575, 2164.1871096038485   ],
    [1555.9866028267575, 2134.0693615862565   ],
    [1556.0106085618263, 2585.8355818501377   ],
    [1556.0106085618263, 2555.7178338325457   ],
    [1556.0106085618263, 2525.6000858149537   ],
    [1556.0346142968951, 2103.9516135686645   ],
    [1556.0346142968951, 2073.8338655510724   ],
    [1556.0346142968951, 2043.7161175334804   ],
    [1556.0346142968951, 2013.5983695158884   ],
    [1556.0346142968951, 1983.4806214982964   ],
    [1556.0346142968951, 1953.3628734807044   ],
    [1556.0346142968951, 1923.2451254631123   ],
    [1556.0346142968951, 1893.1273774455203   ],
    [1556.0346142968951, 1863.0096294279278   ],
    [1556.0586200319638, 2134.0693615862565   ],
    [1556.0586200319638, 1832.8918814103358   ],
    [1556.0586200319638, 1802.7741333927438   ],
    [1556.0586200319638, 1772.6563853751518   ],
    [1556.0586200319638, 1742.5386373575598   ],
    [1556.0586200319638, 1712.4208893399677   ],
    [1556.0586200319638, 1682.3031413223757   ],
    [1556.0586200319638, 1652.1853933047837   ],
    [1556.0586200319638, 1622.0676452871917   ],
    [1556.0586200319638, 1591.9498972695997   ],
    [1556.0586200319638, 1561.8321492520076   ],
    [1556.0586200319638, 1531.7144012344152   ],
    [1556.0586200319638, 1501.5966532168231   ],
    [1556.0586200319638, 1471.4789051992311   ],
    [1556.0586200319638, 1441.361157181639    ],
    [1556.0586200319638, 1411.243409164047    ],
    [1556.0586200319638, 1381.125661146455    ],
    [1556.0586200319638, 1351.007913128863    ],
    [1556.0586200319638, 1320.890165111271    ],
    [1556.0586200319638, 1290.772417093679    ],
    [1556.0586200319638, 1260.654669076087    ],
    [1556.0826257670326, 1230.5369210584945   ],
    [1556.0826257670326, 1200.4191730409025   ],
    [1556.0826257670326, 1170.3014250233105   ],
    [1556.0826257670326, 1140.183677005719    ],
    [1556.0826257670326, 1110.0659289881269   ],
    [1556.0826257670326, 1079.9481809705348   ],
    [1556.0826257670326, 1049.830432952942    ],
    [1556.1066315021014, 1019.7126849353499   ],
    [1556.1066315021014, 989.5949369177579    ],
    [1556.1066315021014, 959.4771889001659    ],
    [1556.1066315021014, 929.3594408825738    ],
    [1556.1066315021014, 899.2416928649818    ],
    [1556.1066315021014, 869.1239448473898    ],
    [1556.1066315021014, 839.0061968297978     ],
    [1556.1066315021014, 808.8884488122058     ],
    [1556.13063723717, 778.7707007946137       ],
    [1556.1866506189972, 751.1627651118215     ],
    [1556.2266601774452, 786.3001377990122     ],
    [1556.2346620891346, 823.9473228210018     ],
    [1556.2506659125138, 748.6529527770217     ],
    [1556.2746716475826, 711.0057677550312     ],
    [1556.2746716475826, 680.8880197374392     ],
    [1556.2986773826515, 643.2408347154496     ],
    [1556.32268311772, 616.8878052000564       ],
    [1556.3706945878578, 594.2994941868628     ],
    [1556.4187060579952, 575.4759016758671     ],
    [1556.4667175281327, 613.1230866978576     ],
    [1556.5627404684078, 590.5347756846631     ],
    [1556.634757673614, 613.1230866978576      ],
    [1556.634757673614, 590.5347756846631      ],
    [1556.658763408683, 673.3585827330417      ],
    [1556.658763408683, 643.2408347154496      ],
    [1556.7067748788204, 695.9468937462352     ],
    [1556.7547863489579, 658.2997087242456     ],
    [1556.8027978190953, 684.6527382396389     ],
    [1556.810799730785, 718.5352047594297      ],
    [1556.8268035541641, 914.3005668737778     ],
    [1556.8268035541641, 884.1828188561858     ],
    [1556.8268035541641, 854.0650708385938     ],
    [1556.8268035541641, 823.9473228210018     ],
    [1556.8268035541641, 793.8295748034097     ],
    [1556.8268035541641, 763.7118267858177     ],
    [1556.850809289233, 1034.771558944146      ],
    [1556.850809289233, 1004.6538109265539     ],
    [1556.850809289233, 974.5360629089619      ],
    [1556.850809289233, 944.4183148913698      ],
    [1556.8748150243016, 1215.4780470496985    ],
    [1556.8748150243016, 1185.3602990321065    ],
    [1556.8748150243016, 1155.242551014515     ],
    [1556.8748150243016, 1125.1248029969229    ],
    [1556.8748150243016, 1095.0070549793309    ],
    [1556.8748150243016, 1064.889306961738     ],
    [1556.8988207593704, 1328.419602115669     ],
    [1556.8988207593704, 1298.301854098077     ],
    [1556.8988207593704, 1268.184106080485     ],
    [1556.8988207593704, 1238.066358062893     ],
    [1556.9068226710601, 1366.066787137659     ],
    [1556.9708379645767, 1381.125661146455     ],
    [1556.9708379645767, 1351.007913128863     ],
    [1556.9708379645767, 1320.890165111271     ],
    [1556.9708379645767, 1290.772417093679     ],
    [1556.9948436996456, 1253.125232071689     ],
    [1556.9948436996456, 1223.0074840540965    ],
    [1556.9948436996456, 1192.8897360365045    ],
    [1556.9948436996456, 1162.7719880189125    ],
    [1556.9948436996456, 1132.6542400013204    ],
    [1556.9948436996456, 1102.5364919837284    ],
    [1556.9948436996456, 1072.4187439661364    ],
    [1556.9948436996456, 1042.3009959485444    ],
    [1556.9948436996456, 1012.1832479309523    ],
    [1556.9948436996456, 982.0654999133603     ],
    [1556.9948436996456, 951.9477518957683     ],
    [1556.9948436996456, 921.8300038781763     ],
    [1557.0188494347142, 884.1828188561858     ],
    [1557.0188494347142, 861.5945078429922     ],
    [1557.0668609048519, 1516.6555272256192    ],
    [1557.0668609048519, 1486.5377792080271    ],
    [1557.0668609048519, 1456.420031190435     ],
    [1557.0668609048519, 1426.302283172843     ],
    [1557.0668609048519, 1396.184535155251     ],
    [1557.0668609048519, 1366.066787137659     ],
    [1557.0668609048519, 1335.949039120067     ],
    [1557.0668609048519, 1305.831291102475     ],
    [1557.0668609048519, 1275.713543084883     ],
    [1557.0668609048519, 1245.595795067291     ],
    [1557.0668609048519, 1215.4780470496985    ],
    [1557.0668609048519, 1185.3602990321065    ],
    [1557.0668609048519, 1155.242551014515     ],
    [1557.0668609048519, 1125.1248029969229    ],
    [1557.0668609048519, 1095.0070549793309    ],
    [1557.0668609048519, 1064.889306961738     ],
    [1557.0668609048519, 1034.771558944146     ],
    [1557.0908666399205, 1998.5394955070924    ],
    [1557.0908666399205, 1968.4217474895004    ],
    [1557.0908666399205, 1938.3039994719084    ],
    [1557.0908666399205, 1908.1862514543163    ],
    [1557.0908666399205, 1878.0685034367243    ],
    [1557.0908666399205, 1847.9507554191318    ],
    [1557.0908666399205, 1817.8330074015398    ],
    [1557.0908666399205, 1787.7152593839478    ],
    [1557.0908666399205, 1757.5975113663558    ],
    [1557.0908666399205, 1727.4797633487638    ],
    [1557.0908666399205, 1697.3620153311717    ],
    [1557.0908666399205, 1667.2442673135797    ],
    [1557.0908666399205, 1637.1265192959877    ],
    [1557.0908666399205, 1607.0087712783957    ],
    [1557.0908666399205, 1576.8910232608036    ],
    [1557.0908666399205, 1546.7732752432112    ],
    [1557.1148723749893, 2269.599227665421     ],
    [1557.1388781100582, 2231.952042643431     ],
    [1557.1388781100582, 2201.834294625839     ],
    [1557.1388781100582, 2171.7165466082465    ],
    [1557.1388781100582, 2141.5987985906545    ],
    [1557.1388781100582, 2111.4810505730625    ],
    [1557.1388781100582, 2081.3633025554705    ],
    [1557.1388781100582, 2051.2455545378784    ],
    [1557.1388781100582, 2021.1278065202864    ],
    [1557.1628838451268, 1983.4806214982964    ],
    [1557.1628838451268, 1953.3628734807044    ],
    [1557.1628838451268, 1923.2451254631123    ],
    [1557.1628838451268, 1893.1273774455203    ],
    [1557.1628838451268, 1863.0096294279278    ],
    [1557.1628838451268, 1832.8918814103358    ],
    [1557.1628838451268, 1802.7741333927438    ],
    [1557.1628838451268, 1772.6563853751518    ],
    [1557.1628838451268, 1742.5386373575598    ],
    [1557.1628838451268, 1712.4208893399677    ],
    [1557.1628838451268, 1682.3031413223757    ],
    [1557.1628838451268, 1652.1853933047837    ],
    [1557.1628838451268, 1622.0676452871917    ],
    [1557.1628838451268, 1591.9498972695997    ],
    [1557.1628838451268, 1561.8321492520076    ],
    [1557.1628838451268, 1531.7144012344152    ],
    [1557.1628838451268, 1501.5966532168231    ],
    [1557.1628838451268, 1471.4789051992311    ],
    [1557.1628838451268, 1441.361157181639     ],
    [1557.1628838451268, 1411.243409164047     ],
    [1557.1628838451268, 1381.125661146455     ],
    [1557.1628838451268, 1351.007913128863     ],
    [1557.1628838451268, 1320.890165111271     ],
    [1557.1628838451268, 1290.772417093679     ],
    [1557.1628838451268, 1260.654669076087     ],
    [1557.1628838451268, 1230.5369210584945    ],
    [1557.1628838451268, 1200.4191730409025    ],
    [1557.1628838451268, 1170.3014250233105    ],
    [1557.1868895801956, 1140.183677005719     ],
    [1557.1868895801956, 1110.0659289881269    ],
    [1557.1868895801956, 1079.9481809705348    ],
    [1557.1868895801956, 1049.830432952942     ],
    [1557.2108953152645, 1019.7126849353499    ],
    [1557.2108953152645, 989.5949369177579     ],
    [1557.2108953152645, 959.4771889001659     ],
    [1557.2108953152645, 929.3594408825738     ],
    [1557.2108953152645, 899.2416928649818     ],
    [1557.2108953152645, 869.1239448473898     ],
    [1557.2108953152645, 839.0061968297978     ],
    [1557.2108953152645, 726.0646417638272     ],
    [1557.234901050333, 801.3590118078082      ],
    [1557.234901050333, 771.2412637902162      ],
    [1557.234901050333, 741.1235157726233      ],
    [1557.258906785402, 703.4763307506337      ],
    [1557.258906785402, 673.3585827330417      ],
    [1557.2829125204707, 643.2408347154496     ],
    [1557.3789354607457, 650.7702717198472     ],
    [1557.4029411958145, 688.4174567418377     ],
    [1557.4269469308833, 718.5352047594297     ],
    [1557.4749584010208, 748.6529527770217     ],
    [1557.4989641360894, 808.8884488122058     ],
    [1557.4989641360894, 778.7707007946137     ],
    [1557.5229698711582, 929.3594408825738     ],
    [1557.5229698711582, 899.2416928649818     ],
    [1557.5229698711582, 869.1239448473898     ],
    [1557.5229698711582, 842.7709153319965     ],
    [1557.546975606227, 1079.9481809705348     ],
    [1557.546975606227, 1049.830432952942      ],
    [1557.546975606227, 1019.7126849353499     ],
    [1557.546975606227, 989.5949369177579      ],
    [1557.546975606227, 959.4771889001659      ],
    [1557.5709813412957, 1170.3014250233105    ],
    [1557.5709813412957, 1140.183677005719     ],
    [1557.5709813412957, 1113.8306474903256    ],
    [1557.5949870763645, 1200.4191730409025    ],
    [1557.6189928114334, 1260.654669076087     ],
    [1557.6189928114334, 1234.3016395606937    ],
    [1557.6670042815708, 1320.890165111271     ],
    [1557.6670042815708, 1290.772417093679     ],
    [1557.6910100166397, 1260.654669076087     ],
    [1557.6910100166397, 1230.5369210584945    ],
    [1557.6910100166397, 1200.4191730409025    ],
    [1557.7150157517083, 1170.3014250233105    ],
    [1557.7150157517083, 1140.183677005719     ],
    [1557.7150157517083, 1110.0659289881269    ],
    [1557.7150157517083, 1087.4776179749324    ],
    [1557.7390214867771, 1049.830432952942     ],
    [1557.7390214867771, 1019.7126849353499    ],
    [1557.7390214867771, 997.1243739221563     ],
    [1557.7390214867771, 914.3005668737778     ],
    [1557.7390214867771, 884.1828188561858     ],
    [1557.7390214867771, 823.9473228210018     ],
    [1557.7390214867771, 793.8295748034097     ],
    [1557.7390214867771, 763.7118267858177     ],
    [1557.763027221846, 850.300352336395       ],
    [1557.763027221846, 733.5940787682257      ],
    [1557.763027221846, 707.2410492528325      ],
    [1557.7870329569146, 673.3585827330417     ],
    [1557.8830558971897, 567.9464646714696     ],
    [1557.9070616322585, 537.8287166538776     ],
    [1557.9070616322585, 511.4756871384843     ],
    [1557.955073102396, 477.5932206186935      ],
    [1558.0270903076023, 485.1226576230911     ],
    [1558.0590979543606, 510.2207809710844     ],
    [1558.0751017777397, 613.1230866978576     ],
    [1558.0751017777397, 583.0053386802656     ],
    [1558.0751017777397, 552.8875906626736     ],
    [1558.0991075128086, 673.3585827330417     ],
    [1558.0991075128086, 647.0055532176484     ],
    [1558.1231132478772, 1396.184535155251     ],
    [1558.1231132478772, 1366.066787137659     ],
    [1558.1231132478772, 1335.949039120067     ],
    [1558.1231132478772, 1305.831291102475     ],
    [1558.1231132478772, 1275.713543084883     ],
    [1558.1231132478772, 1245.595795067291     ],
    [1558.1231132478772, 1215.4780470496985    ],
    [1558.1231132478772, 1185.3602990321065    ],
    [1558.1231132478772, 1155.242551014515     ],
    [1558.1231132478772, 1125.1248029969229    ],
    [1558.1231132478772, 1095.0070549793309    ],
    [1558.1231132478772, 1064.889306961738     ],
    [1558.1231132478772, 1034.771558944146     ],
    [1558.1231132478772, 1004.6538109265539    ],
    [1558.1231132478772, 974.5360629089619     ],
    [1558.1231132478772, 944.4183148913698     ],
    [1558.1231132478772, 914.3005668737778     ],
    [1558.1231132478772, 884.1828188561858     ],
    [1558.1231132478772, 854.0650708385938     ],
    [1558.1231132478772, 823.9473228210018     ],
    [1558.1231132478772, 793.8295748034097     ],
    [1558.1231132478772, 763.7118267858177     ],
    [1558.1231132478772, 733.5940787682257     ],
    [1558.1231132478772, 703.4763307506337     ],
    [1558.147118982946, 1847.9507554191318     ],
    [1558.147118982946, 1817.8330074015398     ],
    [1558.147118982946, 1787.7152593839478     ],
    [1558.147118982946, 1757.5975113663558     ],
    [1558.147118982946, 1727.4797633487638     ],
    [1558.147118982946, 1697.3620153311717     ],
    [1558.147118982946, 1667.2442673135797     ],
    [1558.147118982946, 1637.1265192959877     ],
    [1558.147118982946, 1607.0087712783957     ],
    [1558.147118982946, 1576.8910232608036     ],
    [1558.147118982946, 1546.7732752432112     ],
    [1558.147118982946, 1516.6555272256192     ],
    [1558.147118982946, 1486.5377792080271     ],
    [1558.147118982946, 1456.420031190435      ],
    [1558.147118982946, 1430.0670016750423     ],
    [1558.1711247180149, 2871.9541880172624    ],
    [1558.1711247180149, 2841.83643999967      ],
    [1558.1711247180149, 2811.718691982078     ],
    [1558.1711247180149, 2781.600943964486     ],
    [1558.1711247180149, 2751.483195946894     ],
    [1558.1711247180149, 2721.365447929302     ],
    [1558.1711247180149, 2691.24769991171      ],
    [1558.1711247180149, 2661.1299518941178    ],
    [1558.1711247180149, 2631.0122038765257    ],
    [1558.1711247180149, 2600.8944558589337    ],
    [1558.1711247180149, 2570.7767078413417    ],
    [1558.1711247180149, 2540.6589598237497    ],
    [1558.1711247180149, 2510.541211806157     ],
    [1558.1711247180149, 2480.423463788565     ],
    [1558.1711247180149, 2450.305715770973     ],
    [1558.1711247180149, 2420.187967753381     ],
    [1558.1711247180149, 2390.070219735789     ],
    [1558.1711247180149, 2359.952471718197     ],
    [1558.1711247180149, 2329.834723700605     ],
    [1558.1711247180149, 2299.716975683013     ],
    [1558.1711247180149, 2269.599227665421     ],
    [1558.1711247180149, 2239.481479647829     ],
    [1558.1711247180149, 2209.363731630237     ],
    [1558.1711247180149, 2179.2459836126445    ],
    [1558.1711247180149, 2149.1282355950525    ],
    [1558.1711247180149, 2119.0104875774605    ],
    [1558.1711247180149, 2088.8927395598685    ],
    [1558.1711247180149, 2058.7749915422764    ],
    [1558.1711247180149, 2028.6572435246844    ],
    [1558.1711247180149, 1998.5394955070924    ],
    [1558.1711247180149, 1968.4217474895004    ],
    [1558.1711247180149, 1938.3039994719084    ],
    [1558.1711247180149, 1908.1862514543163    ],
    [1558.1711247180149, 1878.0685034367243    ],
    [1558.1951304530835, 3436.6619633471137    ],
    [1558.1951304530835, 3406.5442153295216    ],
    [1558.1951304530835, 3376.426467311929     ],
    [1558.1951304530835, 3346.308719294337     ],
    [1558.1951304530835, 3316.190971276745     ],
    [1558.1951304530835, 3286.073223259153     ],
    [1558.1951304530835, 3255.955475241561     ],
    [1558.1951304530835, 3225.8377272239686    ],
    [1558.1951304530835, 3195.719979206377     ],
    [1558.1951304530835, 3165.602231188785     ],
    [1558.1951304530835, 3135.4844831711926    ],
    [1558.1951304530835, 3105.3667351536005    ],
    [1558.1951304530835, 3075.2489871360085    ],
    [1558.1951304530835, 3045.1312391184165    ],
    [1558.1951304530835, 3015.0134911008245    ],
    [1558.1951304530835, 2984.8957430832324    ],
    [1558.1951304530835, 2954.7779950656404    ],
    [1558.1951304530835, 2924.6602470480484    ],
    [1558.1951304530835, 2894.5424990304564    ],
    [1558.2031323647732, 3474.3091483691032    ],
    [1558.2191361881523, 4965.137675239911     ],
    [1558.2191361881523, 4935.019927222318     ],
    [1558.2191361881523, 4904.902179204726     ],
    [1558.2191361881523, 4874.784431187134     ],
    [1558.2191361881523, 4844.666683169542     ],
    [1558.2191361881523, 4814.54893515195      ],
    [1558.2191361881523, 4784.431187134358     ],
    [1558.2191361881523, 4754.313439116766     ],
    [1558.2191361881523, 4724.195691099174     ],
    [1558.2191361881523, 4694.077943081582     ],
    [1558.2191361881523, 4663.96019506399      ],
    [1558.2191361881523, 4633.842447046398     ],
    [1558.2191361881523, 4603.724699028806     ],
    [1558.2191361881523, 4573.606951011214     ],
    [1558.2191361881523, 4543.489202993622     ],
    [1558.2191361881523, 4513.37145497603      ],
    [1558.2431419232212, 4483.253706958438     ],
    [1558.2431419232212, 4453.135958940846     ],
    [1558.2431419232212, 4423.018210923254     ],
    [1558.2431419232212, 4392.900462905662     ],
    [1558.2431419232212, 4362.78271488807      ],
    [1558.2431419232212, 4332.664966870478     ],
    [1558.2431419232212, 4302.547218852886     ],
    [1558.2431419232212, 4272.429470835294     ],
    [1558.2431419232212, 4242.311722817701     ],
    [1558.2431419232212, 4212.19397480011      ],
    [1558.2431419232212, 4182.076226782517     ],
    [1558.2431419232212, 4151.958478764925     ],
    [1558.2431419232212, 4121.840730747333     ],
    [1558.2431419232212, 4091.7229827297406    ],
    [1558.2431419232212, 4061.6052347121486    ],
    [1558.2431419232212, 4031.4874866945565    ],
    [1558.2431419232212, 4001.3697386769645    ],
    [1558.2431419232212, 3971.2519906593725    ],
    [1558.2431419232212, 3941.1342426417805    ],
    [1558.2431419232212, 3911.0164946241885    ],
    [1558.2431419232212, 3880.8987466065964    ],
    [1558.2431419232212, 3850.7809985890044    ],
    [1558.2431419232212, 3820.6632505714124    ],
    [1558.2431419232212, 3790.5455025538204    ],
    [1558.2431419232212, 3760.4277545362283    ],
    [1558.2431419232212, 3730.3100065186363    ],
    [1558.2431419232212, 3700.192258501044     ],
    [1558.2431419232212, 3670.074510483452     ],
    [1558.2431419232212, 3639.95676246586      ],
    [1558.2431419232212, 3609.839014448268     ],
    [1558.2431419232212, 3579.7212664306758    ],
    [1558.2431419232212, 3549.6035184130833    ],
    [1558.2431419232212, 3519.4857703954913    ],
    [1558.2671476582898, 3489.3680223778993    ],
    [1558.2671476582898, 3459.2502743603072    ],
    [1558.2671476582898, 3429.132526342715     ],
    [1558.2671476582898, 3399.014778325123     ],
    [1558.2671476582898, 3368.897030307531     ],
    [1558.2671476582898, 3338.779282289939     ],
    [1558.2671476582898, 3308.661534272347     ],
    [1558.2671476582898, 3278.543786254755     ],
    [1558.2671476582898, 3248.426038237163     ],
    [1558.2671476582898, 3218.308290219571     ],
    [1558.2671476582898, 3188.190542201979     ],
    [1558.2671476582898, 3158.0727941843866    ],
    [1558.2671476582898, 3127.9550461667945    ],
    [1558.2671476582898, 3097.8372981492025    ],
    [1558.2671476582898, 3067.7195501316105    ],
    [1558.2671476582898, 3037.6018021140185    ],
    [1558.2671476582898, 3007.4840540964265    ],
    [1558.2671476582898, 2977.3663060788344    ],
    [1558.2671476582898, 2947.2485580612424    ],
    [1558.2671476582898, 2917.1308100436504    ],
    [1558.2671476582898, 2887.0130620260584    ],
    [1558.2671476582898, 2856.8953140084664    ],
    [1558.2671476582898, 2826.777565990874     ],
    [1558.2671476582898, 2796.659817973282     ],
    [1558.2671476582898, 2766.54206995569      ],
    [1558.2671476582898, 2736.424321938098     ],
    [1558.2671476582898, 2706.306573920506     ],
    [1558.2911533933586, 2668.6593888985158    ],
    [1558.2911533933586, 2638.5416408809238    ],
    [1558.2911533933586, 2608.4238928633317    ],
    [1558.2911533933586, 2578.3061448457397    ],
    [1558.2911533933586, 2548.1883968281477    ],
    [1558.2911533933586, 2518.070648810555     ],
    [1558.2911533933586, 2487.952900792963     ],
    [1558.2911533933586, 2457.835152775371     ],
    [1558.3151591284275, 2420.187967753381     ],
    [1558.3151591284275, 2390.070219735789     ],
    [1558.3151591284275, 2359.952471718197     ],
    [1558.3151591284275, 2329.834723700605     ],
    [1558.3151591284275, 2299.716975683013     ],
    [1558.3151591284275, 2269.599227665421     ],
    [1558.3151591284275, 2239.481479647829     ],
    [1558.3151591284275, 2209.363731630237     ],
    [1558.3151591284275, 2179.2459836126445    ],
    [1558.3151591284275, 2149.1282355950525    ],
    [1558.3151591284275, 2119.0104875774605    ],
    [1558.3151591284275, 2088.8927395598685    ],
    [1558.3151591284275, 2058.7749915422764    ],
    [1558.3151591284275, 2028.6572435246844    ],
    [1558.3151591284275, 1998.5394955070924    ],
    [1558.3151591284275, 1968.4217474895004    ],
    [1558.3151591284275, 1938.3039994719084    ],
    [1558.3151591284275, 1908.1862514543163    ],
    [1558.3151591284275, 1878.0685034367243    ],
    [1558.3151591284275, 1847.9507554191318    ],
    [1558.3151591284275, 1817.8330074015398    ],
    [1558.3151591284275, 1787.7152593839478    ],
    [1558.3151591284275, 1757.5975113663558    ],
    [1558.3151591284275, 1727.4797633487638    ],
    [1558.3151591284275, 1697.3620153311717    ],
    [1558.3151591284275, 1667.2442673135797    ],
    [1558.3151591284275, 1637.1265192959877    ],
    [1558.3151591284275, 1607.0087712783957    ],
    [1558.3151591284275, 1576.8910232608036    ],
    [1558.3151591284275, 1546.7732752432112    ],
    [1558.3151591284275, 1516.6555272256192    ],
    [1558.3151591284275, 1486.5377792080271    ],
    [1558.3151591284275, 1456.420031190435     ],
    [1558.3151591284275, 1426.302283172843     ],
    [1558.3151591284275, 1396.184535155251     ],
    [1558.3151591284275, 1366.066787137659     ],
    [1558.3151591284275, 1335.949039120067     ],
    [1558.3151591284275, 1305.831291102475     ],
    [1558.3151591284275, 1275.713543084883     ],
    [1558.3151591284275, 1245.595795067291     ],
    [1558.3151591284275, 1215.4780470496985    ],
    [1558.3151591284275, 1185.3602990321065    ],
    [1558.3151591284275, 1155.242551014515     ],
    [1558.3151591284275, 1125.1248029969229    ],
    [1558.3151591284275, 1012.1832479309523    ],
    [1558.339164863496, 1087.4776179749324     ],
    [1558.339164863496, 1057.3598699573404     ],
    [1558.339164863496, 1027.2421219397484     ],
    [1558.363170598565, 989.5949369177579      ],
    [1558.363170598565, 959.4771889001659      ],
    [1558.363170598565, 929.3594408825738      ],
    [1558.3871763336338, 899.2416928649818     ],
    [1558.3871763336338, 876.6533818517883     ],
    [1558.4831992739087, 891.7122558605843     ],
    [1558.5312107440463, 921.8300038781763     ],
    [1558.5392126557358, 959.4771889001659     ],
    [1558.555216479115, 1004.6538109265539     ],
    [1558.555216479115, 884.1828188561858      ],
    [1558.5792222141838, 854.0650708385938     ],
    [1558.5792222141838, 823.9473228210018     ],
    [1558.5792222141838, 797.5942933056085     ],
    [1558.6032279492526, 763.7118267858177     ],
    [1558.6032279492526, 733.5940787682257     ],
    [1558.6032279492526, 703.4763307506337     ],
    [1558.6272336843213, 665.8291457286432     ],
    [1558.6272336843213, 635.7113977110512     ],
    [1558.65123941939, 598.0642126890616       ],
    [1558.675245154459, 571.7111831736684      ],
    [1558.7232566245964, 541.5934351560763     ],
    [1558.7712680947338, 500.1815316318871     ],
    [1558.8192795648713, 466.2990651120963     ],
    [1558.8912967700776, 522.7698426450816     ],
    [1558.8912967700776, 492.65209462748953    ],
    [1558.8912967700776, 470.06378361429506    ],
    [1558.9153025051464, 552.8875906626736     ],
    [1558.9393082402153, 793.8295748034097     ],
    [1558.9393082402153, 763.7118267858177     ],
    [1558.9393082402153, 733.5940787682257     ],
    [1558.9393082402153, 703.4763307506337     ],
    [1558.9393082402153, 673.3585827330417     ],
    [1558.9393082402153, 643.2408347154496     ],
    [1558.9393082402153, 613.1230866978576     ],
    [1558.9393082402153, 583.0053386802656     ],
    [1558.9633139752839, 997.1243739221563     ],
    [1558.9633139752839, 967.0066259045643     ],
    [1558.9633139752839, 936.8888778869723     ],
    [1558.9633139752839, 906.7711298693803     ],
    [1558.9633139752839, 876.6533818517883     ],
    [1558.9633139752839, 846.5356338341962     ],
    [1558.9633139752839, 816.4178858166042     ],
    [1558.9713158869736, 1034.771558944146     ],
    [1558.9873197103527, 1712.4208893399677    ],
    [1558.9873197103527, 1652.1853933047837    ],
    [1558.9873197103527, 1622.0676452871917    ],
    [1558.9873197103527, 1591.9498972695997    ],
    [1558.9873197103527, 1561.8321492520076    ],
    [1558.9873197103527, 1531.7144012344152    ],
    [1558.9873197103527, 1501.5966532168231    ],
    [1558.9873197103527, 1471.4789051992311    ],
    [1558.9873197103527, 1441.361157181639     ],
    [1558.9873197103527, 1411.243409164047     ],
    [1558.9873197103527, 1381.125661146455     ],
    [1558.9873197103527, 1351.007913128863     ],
    [1558.9873197103527, 1320.890165111271     ],
    [1558.9873197103527, 1290.772417093679     ],
    [1558.9873197103527, 1260.654669076087     ],
    [1558.9873197103527, 1230.5369210584945    ],
    [1558.9873197103527, 1200.4191730409025    ],
    [1558.9873197103527, 1170.3014250233105    ],
    [1558.9873197103527, 1140.183677005719     ],
    [1558.9873197103527, 1110.0659289881269    ],
    [1558.9873197103527, 1079.9481809705348    ],
    [1559.0113254454216, 2036.1866805290824    ],
    [1559.0113254454216, 2006.0689325114904    ],
    [1559.0113254454216, 1975.9511844938984    ],
    [1559.0113254454216, 1945.8334364763064    ],
    [1559.0113254454216, 1915.7156884587143    ],
    [1559.0113254454216, 1885.5979404411223    ],
    [1559.0113254454216, 1855.4801924235298    ],
    [1559.0113254454216, 1825.3624444059378    ],
    [1559.0113254454216, 1795.2446963883458    ],
    [1559.0113254454216, 1765.1269483707538    ],
    [1559.0113254454216, 1738.773918855361     ],
    [1559.0113254454216, 1682.3031413223757    ],
    [1559.019327357111, 2073.8338655510724     ],
    [1559.0353311804902, 2962.3074320700384    ],
    [1559.0353311804902, 2932.1896840524464    ],
    [1559.0353311804902, 2902.0719360348544    ],
    [1559.0353311804902, 2871.9541880172624    ],
    [1559.0353311804902, 2841.83643999967      ],
    [1559.0353311804902, 2811.718691982078     ],
    [1559.059336915559, 2781.600943964486      ],
    [1559.059336915559, 2751.483195946894      ],
    [1559.059336915559, 2721.365447929302      ],
    [1559.059336915559, 2691.24769991171       ],
    [1559.059336915559, 2661.1299518941178     ],
    [1559.059336915559, 2631.0122038765257     ],
    [1559.059336915559, 2600.8944558589337     ],
    [1559.059336915559, 2570.7767078413417     ],
    [1559.059336915559, 2540.6589598237497     ],
    [1559.059336915559, 2510.541211806157      ],
    [1559.059336915559, 2480.423463788565      ],
    [1559.059336915559, 2450.305715770973      ],
    [1559.059336915559, 2420.187967753381      ],
    [1559.059336915559, 2390.070219735789      ],
    [1559.059336915559, 2359.952471718197      ],
    [1559.059336915559, 2329.834723700605      ],
    [1559.059336915559, 2299.716975683013      ],
    [1559.059336915559, 2269.599227665421      ],
    [1559.059336915559, 2239.481479647829      ],
    [1559.059336915559, 2209.363731630237      ],
    [1559.059336915559, 2179.2459836126445     ],
    [1559.059336915559, 2149.1282355950525     ],
    [1559.059336915559, 2119.0104875774605     ],
    [1559.1073483856965, 2081.3633025554705    ],
    [1559.1073483856965, 2051.2455545378784    ],
    [1559.1073483856965, 2021.1278065202864    ],
    [1559.1073483856965, 1991.0100585026944    ],
    [1559.1073483856965, 1960.8923104851024    ],
    [1559.1073483856965, 1930.7745624675103    ],
    [1559.1073483856965, 1900.6568144499183    ],
    [1559.1073483856965, 1870.5390664323259    ],
    [1559.1073483856965, 1840.4213184147338    ],
    [1559.1073483856965, 1810.3035703971418    ],
    [1559.1073483856965, 1780.1858223795498    ],
    [1559.1073483856965, 1750.0680743619578    ],
    [1559.1073483856965, 1719.9503263443657    ],
    [1559.1073483856965, 1689.8325783267737    ],
    [1559.1073483856965, 1659.7148303091817    ],
    [1559.1313541207653, 1622.0676452871917    ],
    [1559.1313541207653, 1591.9498972695997    ],
    [1559.1313541207653, 1561.8321492520076    ],
    [1559.1313541207653, 1531.7144012344152    ],
    [1559.1313541207653, 1501.5966532168231    ],
    [1559.1313541207653, 1471.4789051992311    ],
    [1559.1313541207653, 1441.361157181639     ],
    [1559.1313541207653, 1411.243409164047     ],
    [1559.1313541207653, 1381.125661146455     ],
    [1559.1313541207653, 1351.007913128863     ],
    [1559.1313541207653, 1320.890165111271     ],
    [1559.1313541207653, 1290.772417093679     ],
    [1559.1313541207653, 1260.654669076087     ],
    [1559.1313541207653, 1230.5369210584945    ],
    [1559.1313541207653, 1200.4191730409025    ],
    [1559.1313541207653, 1170.3014250233105    ],
    [1559.1313541207653, 1140.183677005719     ],
    [1559.1313541207653, 1110.0659289881269    ],
    [1559.1313541207653, 1079.9481809705348    ],
    [1559.1313541207653, 1049.830432952942     ],
    [1559.1313541207653, 1019.7126849353499    ],
    [1559.1313541207653, 876.6533818517883     ],
    [1559.1553598558341, 982.0654999133603     ],
    [1559.1553598558341, 951.9477518957683     ],
    [1559.1553598558341, 921.8300038781763     ],
    [1559.1553598558341, 891.7122558605843     ],
    [1559.1793655909028, 854.0650708385938     ],
    [1559.1793655909028, 823.9473228210018     ],
    [1559.1793655909028, 793.8295748034097     ],
    [1559.1793655909028, 763.7118267858177     ],
    [1559.2033713259716, 733.5940787682257     ],
    [1559.2033713259716, 703.4763307506337     ],
    [1559.2033713259716, 673.3585827330417     ],
    [1559.251382796109, 643.2408347154496      ],
    [1559.251382796109, 620.6525237022552      ],
    [1559.3234000013153, 613.1230866978576     ],
    [1559.3234000013153, 560.4170276670711     ],
    [1559.3474057363842, 575.4759016758671     ],
    [1559.3714114714528, 537.8287166538776     ],
    [1559.3954172065216, 500.1815316318871     ],
    [1559.443428676659, 455.00490960549905     ],
    [1559.4914401467968, 421.12244308570826    ],
    [1559.5394516169342, 379.710539561519      ],
    [1559.6354745572094, 372.18110255712054    ],
    [1559.739499409174, 359.6320408831243      ],
    [1559.779508967622, 402.29885057471256     ],
    [1559.8035147026906, 492.65209462748953  ],
    [1559.8035147026906, 462.5343466098975   ],
    [1559.8035147026906, 432.4165985923046   ],
    [1559.8035147026906, 379.710539561519    ],
    [1559.8275204377594, 575.4759016758671   ],
    [1559.8275204377594, 545.3581536582751   ],
    [1559.8275204377594, 519.0051241428819   ],
    [1559.8355223494489, 613.1230866978576   ],
    [1559.8515261728282, 718.5352047594297   ],
    [1559.8515261728282, 688.4174567418377   ],
    [1559.8515261728282, 658.2997087242456   ],
    [1559.8755319078969, 982.0654999133603   ],
    [1559.8755319078969, 951.9477518957683   ],
    [1559.8755319078969, 921.8300038781763   ],
    [1559.8755319078969, 891.7122558605843   ],
    [1559.8755319078969, 861.5945078429922   ],
    [1559.8755319078969, 831.4767598254002   ],
    [1559.8755319078969, 801.3590118078082   ],
    [1559.8755319078969, 771.2412637902162   ],
    [1559.8755319078969, 741.1235157726233   ],
    [1559.9475491131032, 808.8884488122058   ],
    [1559.9475491131032, 778.7707007946137   ],
    [1559.9475491131032, 748.6529527770217   ],
    [1559.9475491131032, 718.5352047594297   ],
    [1559.9475491131032, 688.4174567418377   ],
    [1559.9475491131032, 658.2997087242456   ],
    [1559.9475491131032, 628.1819607066536   ],
    [1559.9475491131032, 598.0642126890616   ],
    [1559.9475491131032, 567.9464646714696   ],
    [1559.9475491131032, 485.1226576230911   ],
    [1559.971554848172, 530.2992796494791    ],
    [1559.971554848172, 500.1815316318871    ],
    [1559.9955605832406, 462.5343466098975   ],
    [1560.0195663183094, 424.88716158790703  ],
    [1560.0195663183094, 394.769413570315    ],
    [1560.067577788447, 360.8869470505242    ],
    [1560.163600728722, 375.9458210593202    ],
    [1560.2596236689972, 379.710539561519    ],
    [1560.3076351391346, 402.29885057471256  ],
    [1560.379652344341, 387.23997656591655   ],
    [1560.4036580794098, 424.88716158790703  ],
    [1560.4276638144784, 462.5343466098975   ],
    [1560.4516695495472, 496.4168131296883   ],
    [1560.475675284616, 583.0053386802656    ],
    [1560.475675284616, 552.8875906626736    ],
    [1560.475675284616, 522.7698426450816    ],
    [1560.4996810196847, 665.8291457286432   ],
    [1560.4996810196847, 635.7113977110512   ],
    [1560.4996810196847, 609.3583681956588   ],
    [1560.5076829313743, 703.4763307506337   ],
    [1560.5476924898223, 808.8884488122058   ],
    [1560.5476924898223, 778.7707007946137   ],
    [1560.5476924898223, 752.4176712792205   ],
    [1560.6197096950284, 793.8295748034097   ],
    [1560.6197096950284, 763.7118267858177   ],
    [1560.6197096950284, 733.5940787682257   ],
    [1560.6197096950284, 703.4763307506337   ],
    [1560.6437154300972, 673.3585827330417   ],
    [1560.6437154300972, 643.2408347154496   ],
    [1560.6437154300972, 616.8878052000564   ],
    [1560.7397383703724, 801.3590118078082   ],
    [1560.7397383703724, 771.2412637902162   ],
    [1560.7397383703724, 741.1235157726233   ],
    [1560.7397383703724, 711.0057677550312   ],
    [1560.7397383703724, 680.8880197374392   ],
    [1560.7397383703724, 650.7702717198472   ],
    [1560.7397383703724, 620.6525237022552   ],
    [1560.7477402820618, 839.0061968297978   ],
    [1560.7877498405098, 586.7700571824644   ],
    [1560.8117555755787, 643.2408347154496   ],
    [1560.8117555755787, 613.1230866978576   ],
    [1560.8117555755787, 552.8875906626736   ],
    [1560.8117555755787, 522.7698426450816   ],
    [1560.8357613106473, 485.1226576230911   ],
    [1560.8357613106473, 455.00490960549905  ],
    [1560.883772780785, 417.35772458350857   ],
    [1560.9797957210599, 406.06356907691224  ],
    [1561.075818661335, 387.23997656591655   ],
    [1561.1718416016101, 409.828287579111    ],
    [1561.2198530717476, 455.00490960549905  ],
    [1561.2438588068162, 613.1230866978576   ],
    [1561.2438588068162, 583.0053386802656   ],
    [1561.2438588068162, 552.8875906626736   ],
    [1561.2438588068162, 522.7698426450816   ],
    [1561.2438588068162, 492.65209462748953  ],
    [1561.267864541885, 733.5940787682257    ],
    [1561.267864541885, 703.4763307506337    ],
    [1561.267864541885, 673.3585827330417    ],
    [1561.267864541885, 647.0055532176484    ],
    [1561.3158760120225, 823.9473228210018   ],
    [1561.3158760120225, 793.8295748034097   ],
    [1561.3158760120225, 763.7118267858177   ],
    [1561.3398817470913, 854.0650708385938   ],
    [1561.3398817470913, 680.8880197374392   ],
    [1561.3638874821602, 695.9468937462352   ],
    [1561.3718893938496, 733.5940787682257   ],
    [1561.3878932172288, 778.7707007946137   ],
    [1561.3878932172288, 658.2997087242456   ],
    [1561.3878932172288, 628.1819607066536   ],
    [1561.3878932172288, 598.0642126890616   ],
    [1561.3878932172288, 567.9464646714696   ],
    [1561.3878932172288, 537.8287166538776   ],
    [1561.3878932172288, 455.00490960549905  ],
    [1561.4118989522976, 500.1815316318871   ],
    [1561.4118989522976, 470.06378361429506  ],
    [1561.4359046873665, 432.4165985923046   ],
    [1561.5079218925728, 402.29885057471256  ],
    [1561.579939097779, 492.65209462748953   ],
    [1561.579939097779, 462.5343466098975    ],
    [1561.579939097779, 432.4165985923046    ],
    [1561.579939097779, 409.828287579111     ],
    [1561.6039448328477, 552.8875906626736   ],
    [1561.6039448328477, 526.5345611472803   ],
    [1561.6519563029854, 613.1230866978576   ],
    [1561.6519563029854, 583.0053386802656   ],
    [1561.675962038054, 643.2408347154496    ],
    [1561.6999677731228, 552.8875906626736   ],
    [1561.7479792432603, 575.4759016758671   ],
    [1561.7479792432603, 488.88737612528985  ],
    [1561.75598115495, 522.7698426450816     ],
    [1561.8199964484666, 613.1230866978576   ],
    [1561.8199964484666, 583.0053386802656   ],
    [1561.8199964484666, 552.8875906626736   ],
    [1561.8199964484666, 522.7698426450816   ],
    [1561.8440021835354, 793.8295748034097   ],
    [1561.8440021835354, 763.7118267858177   ],
    [1561.8440021835354, 733.5940787682257   ],
    [1561.8440021835354, 703.4763307506337   ],
    [1561.8440021835354, 673.3585827330417   ],
    [1561.8440021835354, 647.0055532176484   ],
    [1561.9160193887417, 688.4174567418377   ],
    [1561.9160193887417, 658.2997087242456   ],
    [1561.9160193887417, 628.1819607066536   ],
    [1561.9400251238103, 590.5347756846631   ],
    [1562.0120423290166, 567.9464646714696   ],
    [1562.0120423290166, 537.8287166538776   ],
    [1562.0120423290166, 485.1226576230911   ],
    [1562.0360480640854, 500.1815316318871   ],
    [1562.0600537991543, 462.5343466098975   ],
    [1562.084059534223, 428.6518800901058    ],
    [1562.1560767394292, 447.4754726011015   ],
    [1562.1560767394292, 424.88716158790703  ],
    [1562.2280939446355, 507.71096863628554  ],
    [1562.2280939446355, 481.3579391208923   ],
    [1562.3001111498418, 477.5932206186935   ],
    [1562.3241168849106, 439.94603559670304  ],
    [1562.3241168849106, 417.35772458350857  ],
    [1562.4201398251857, 424.88716158790703  ],
    [1562.5241646771503, 437.43622326190325  ],
    [1562.588179970667, 492.65209462748953   ],
    [1562.588179970667, 462.5343466098975    ],
    [1562.588179970667, 432.4165985923046    ],
    [1562.6121857057358, 522.7698426450816   ],
    [1562.6361914408044, 643.2408347154496   ],
    [1562.6361914408044, 613.1230866978576   ],
    [1562.6361914408044, 583.0053386802656   ],
    [1562.6361914408044, 552.8875906626736   ],
    [1562.6601971758732, 673.3585827330417   ],
    [1562.7082086460107, 703.4763307506337   ],
    [1562.7322143810795, 673.3585827330417   ],
    [1562.7322143810795, 643.2408347154496   ],
    [1562.7322143810795, 613.1230866978576   ],
    [1562.7562201161484, 583.0053386802656   ],
    [1562.7562201161484, 552.8875906626736   ],
    [1562.780225851217, 522.7698426450816    ],
    [1562.780225851217, 470.06378361429506   ],
    [1562.8042315862858, 485.1226576230911   ],
    [1562.8522430564233, 443.7107540989018   ],
    [1562.9242602616296, 432.4165985923046   ],
    [1562.9482659966984, 406.06356907691224  ],
    [1562.9962774668359, 379.710539561519    ],
    [1563.0442889369735, 409.828287579111    ],
    [1563.1403118772485, 421.12244308570826  ],
    [1563.1643176123173, 447.4754726011015   ],
    [1563.188323347386, 507.71096863628554   ],
    [1563.188323347386, 481.3579391208923    ],
    [1563.2123290824547, 567.9464646714696   ],
    [1563.2123290824547, 537.8287166538776   ],
    [1563.2363348175236, 601.8289311912604   ],
    [1563.2603405525922, 628.1819607066536   ],
    [1563.284346287661, 658.2997087242456    ],
    [1563.3083520227299, 688.4174567418377   ],
    [1563.3403596694882, 718.5352047594297   ],
    [1563.3803692279362, 793.8295748034097   ],
    [1563.3803692279362, 763.7118267858177   ],
    [1563.4043749630048, 733.5940787682257   ],
    [1563.4043749630048, 703.4763307506337   ],
    [1563.4043749630048, 673.3585827330417   ],
    [1563.4043749630048, 643.2408347154496   ],
    [1563.4043749630048, 613.1230866978576   ],
    [1563.4043749630048, 583.0053386802656   ],
    [1563.4283806980736, 552.8875906626736   ],
    [1563.4523864331425, 522.7698426450816   ],
    [1563.4523864331425, 492.65209462748953  ],
    [1563.476392168211, 455.00490960549905   ],
    [1563.476392168211, 424.88716158790703   ],
    [1563.5484093734174, 402.29885057471256  ],
    [1563.5724151084862, 432.4165985923046   ],
    [1563.596420843555, 462.5343466098975    ],
    [1563.6204265786237, 522.7698426450816   ],
    [1563.6204265786237, 492.65209462748953  ],
    [1563.6444323136925, 703.4763307506337   ],
    [1563.6444323136925, 673.3585827330417   ],
    [1563.6444323136925, 643.2408347154496   ],
    [1563.6444323136925, 613.1230866978576   ],
    [1563.6444323136925, 583.0053386802656   ],
    [1563.6444323136925, 552.8875906626736   ],
    [1563.6684380487613, 823.9473228210018   ],
    [1563.6684380487613, 793.8295748034097   ],
    [1563.6684380487613, 763.7118267858177   ],
    [1563.6684380487613, 733.5940787682257   ],
    [1563.69244378383, 1155.242551014515     ],
    [1563.7164495188988, 1117.5953659925244  ],
    [1563.7164495188988, 1087.4776179749324  ],
    [1563.7164495188988, 1057.3598699573404  ],
    [1563.7164495188988, 1027.2421219397484  ],
    [1563.7164495188988, 997.1243739221563   ],
    [1563.7164495188988, 967.0066259045643   ],
    [1563.7164495188988, 936.8888778869723   ],
    [1563.7164495188988, 906.7711298693803   ],
    [1563.7164495188988, 876.6533818517883   ],
    [1563.7164495188988, 846.5356338341962   ],
    [1563.7644609890363, 812.6531673144045   ],
    [1563.788466724105, 869.1239448473898    ],
    [1563.788466724105, 839.0061968297978    ],
    [1563.788466724105, 778.7707007946137    ],
    [1563.788466724105, 748.6529527770217    ],
    [1563.788466724105, 718.5352047594297    ],
    [1563.788466724105, 688.4174567418377    ],
    [1563.8124724591737, 658.2997087242456   ],
    [1563.8604839293114, 631.9466792088524   ],
    [1563.88448966438, 598.0642126890616     ],
    [1563.88448966438, 545.3581536582751     ],
    [1563.9084953994488, 560.4170276670711   ],
    [1563.9325011345177, 522.7698426450816   ],
    [1563.9565068695863, 492.65209462748953  ],
    [1563.9805126046551, 462.5343466098975   ],
    [1564.004518339724, 436.18131709450427   ],
    [1564.0525298098614, 406.06356907691224  ]

    ]
example_data_red = [
    [1545.9522055680152, 108.6508074031899   ],
    [1546.0562304199798, 118.69005674238815  ],
    [1546.1202457134964, 93.59193339439389   ],
    [1546.1442514485652, 108.6508074031899   ],
    [1546.2882858589778, 123.70968141198682  ],
    [1546.360303064184, 116.18024440758836   ],
    [1546.384308799253, 138.76855542078283   ],
    [1546.3923107109424, 176.4157404427724   ],
    [1546.4083145343216, 274.2984214999469   ],
    [1546.4323202693904, 289.35729550874294  ],
    [1546.44032218108, 327.0044805307325     ],
    [1546.4883336512175, 251.71011048675246  ],
    [1546.5043374745967, 342.0633545395285   ],
    [1546.5043374745967, 319.47504352633496  ],
    [1546.5283432096655, 206.53348846036442  ],
    [1546.5283432096655, 180.18045894497118  ],
    [1546.5523489447341, 236.65123647795645  ],
    [1546.6003604148718, 176.4157404427724   ],
    [1546.7203890902156, 112.41552590538959  ],
    [1546.7924062954219, 108.6508074031899   ],
    [1546.8164120304905, 131.23911841638437  ],
    [1546.9204368824553, 118.69005674238815  ],
    [1546.984452175972, 123.70968141198682   ],
    [1547.0084579110408, 142.5332739229816   ],
    [1547.2485152617282, 108.6508074031899   ],
    [1547.3445382020034, 101.12137039879235  ],
    [1547.3925496721408, 78.53305938559788   ],
    [1547.448563053968, 103.63118273359214   ],
    [1547.5125783474846, 108.6508074031899   ],
    [1547.6886204046557, 151.31761709477905  ],
    [1547.7526356981723, 123.70968141198682  ],
    [1547.7766414332411, 138.76855542078283  ],
    [1547.872664373516, 116.18024440758836   ],
    [1547.9446815787223, 123.70968141198682  ],
    [1548.088715989135, 153.82742942957884   ],
    [1548.1127217242038, 176.4157404427724   ],
    [1548.18473892941, 153.82742942957884    ],
    [1548.2087446644787, 168.88630343837485  ],
    [1548.3047676047538, 161.3568664339764   ],
    [1548.552826867131, 106.14099506839102   ],
    [1548.6408478957164, 116.18024440758836  ],
    [1548.7368708359916, 116.18024440758836  ],
    [1548.8328937762665, 112.41552590538959  ],
    [1549.000933921748, 153.82742942957884   ],
    [1549.0329415685062, 178.9255527775722   ],
    [1549.096956862023, 183.94517744717086   ],
    [1549.1209625970916, 199.00405145596687  ],
    [1549.1769759789188, 163.86667876877618  ],
    [1549.3610199477794, 101.12137039879235  ],
    [1549.4090314179168, 82.29777788779757   ],
    [1549.505054358192, 71.00362238120033    ],
    [1549.6010772984669, 71.00362238120033   ],
    [1549.889146119292, 86.06249638999634    ],
    [1549.9371575894295, 116.18024440758836  ],
    [1549.9851690595672, 93.59193339439389   ],
    [1550.0331805297046, 108.6508074031899   ],
    [1550.105197734911, 108.6508074031899    ],
    [1550.2732378803923, 131.23911841638437  ],
    [1550.2732378803923, 108.6508074031899   ],
    [1550.3452550855986, 108.6508074031899   ],
    [1550.3692608206673, 131.23911841638437  ],
    [1550.4652837609424, 123.70968141198682  ],
    [1550.5373009661487, 123.70968141198682  ],
    [1550.801364051905, 116.18024440758836   ],
    [1550.8493755220425, 93.59193339439389   ],
    [1550.8973869921801, 116.18024440758836  ],
    [1550.953400374007, 91.08212105959501    ],
    [1551.185455813005, 93.59193339439389    ],
    [1551.2814787532802, 86.06249638999634   ],
    [1551.3775016935554, 78.53305938559788   ],
    [1551.4735246338303, 71.00362238120033   ],
    [1551.713581984518, 82.29777788779757    ],
    [1551.7855991897243, 78.53305938559788   ],
    [1551.809604924793, 101.12137039879235   ],
    [1551.8576163949306, 131.23911841638437  ],
    [1551.9296336001369, 131.23911841638437  ],
    [1552.1456852157557, 116.18024440758836  ],
    [1552.217702420962, 108.6508074031899    ],
    [1552.2497100677203, 133.74893075118416  ],
    [1552.313725361237, 123.70968141198682   ],
    [1552.3377310963058, 142.5332739229816   ],
    [1552.5777884469933, 127.4743999141856   ],
    [1552.6738113872684, 127.4743999141856   ],
    [1552.7698343275435, 127.4743999141856   ],
    [1552.8658572678185, 131.23911841638437  ],
    [1552.9378744730247, 123.70968141198682  ],
    [1553.1059146185062, 146.29799242518038  ],
    [1553.1539260886436, 127.4743999141856   ],
    [1553.2499490289188, 131.23911841638437  ],
    [1553.3459719691937, 127.4743999141856   ],
    [1553.4179891744, 131.23911841638437     ],
    [1553.6820522601563, 131.23911841638437  ],
    [1553.7540694653626, 123.70968141198682  ],
    [1553.7780752004314, 146.29799242518038  ],
    [1553.8500924056377, 123.70968141198682  ],
    [1553.8740981407066, 138.76855542078283  ],
    [1553.9461153459129, 123.70968141198682  ],
    [1554.114155491394, 127.4743999141856    ],
    [1554.1861726966004, 108.6508074031899   ],
    [1554.2101784316692, 123.70968141198682  ],
    [1554.2821956368755, 108.6508074031899   ],
    [1554.306201371944, 131.23911841638437   ],
    [1554.5462587226318, 131.23911841638437  ],
    [1554.642281662907, 131.23911841638437   ],
    [1554.7383046031819, 131.23911841638437  ],
    [1554.8103218083882, 116.18024440758836  ],
    [1554.930350483732, 135.00383691858315   ],
    [1554.9783619538696, 108.6508074031899   ],
    [1555.026373424007, 123.70968141198682   ],
    [1555.1223963642822, 123.70968141198682  ],
    [1555.1944135694885, 123.70968141198682  ],
    [1555.3144422448322, 150.06271092737916  ],
    [1555.3864594500385, 123.70968141198682  ],
    [1555.4104651851073, 138.76855542078283  ],
    [1555.5064881253822, 131.23911841638437  ],
    [1555.5785053305885, 123.70968141198682  ],
    [1555.6025110656574, 146.29799242518038  ],
    [1555.74654547607, 112.41552590538959    ],
    [1555.802558857897, 148.80780475998017   ],
    [1555.8905798864826, 161.3568664339764   ],
    [1555.9866028267575, 150.06271092737916  ],
    [1556.2266601774452, 131.23911841638437  ],
    [1556.32268311772, 165.12158493617517    ],
    [1556.32268311772, 135.00383691858315    ],
    [1556.3947003229264, 138.76855542078283  ],
    [1556.426707969685, 163.86667876877618   ],
    [1556.5147289982704, 176.4157404427724   ],
    [1556.5867462034767, 153.82742942957884  ],
    [1556.6107519385453, 168.88630343837485  ],
    [1556.6827691437516, 146.29799242518038  ],
    [1556.8027978190953, 146.29799242518038  ],
    [1556.850809289233, 127.4743999141856    ],
    [1556.946832229508, 116.18024440758836   ],
    [1557.0188494347142, 116.18024440758836  ],
    [1557.042855169783, 146.29799242518038   ],
    [1557.2909144321602, 118.69005674238815  ],
    [1557.3789354607457, 146.29799242518038  ],
    [1557.4269469308833, 127.4743999141856   ],
    [1557.5949870763645, 168.88630343837485  ],
    [1557.6189928114334, 214.06292546476288  ],
    [1557.6189928114334, 183.94517744717086  ],
    [1557.6269947231228, 251.71011048675246  ],
    [1557.642998546502, 530.2992796494791    ],
    [1557.6670042815708, 575.4759016758671   ],
    [1557.6670042815708, 545.3581536582751   ],
    [1557.6670042815708, 432.4165985923046   ],
    [1557.6670042815708, 402.29885057471256  ],
    [1557.6670042815708, 372.18110255712054  ],
    [1557.6670042815708, 349.592791543927    ],
    [1557.6750061932605, 613.1230866978576   ],
    [1557.6910100166397, 891.7122558605843   ],
    [1557.6910100166397, 703.4763307506337   ],
    [1557.7150157517083, 936.8888778869723   ],
    [1557.7150157517083, 906.7711298693803   ],
    [1557.7150157517083, 756.1823897814202   ],
    [1557.7150157517083, 726.0646417638272   ],
    [1557.723017663398, 974.5360629089619    ],
    [1557.723017663398, 793.8295748034097    ],
    [1557.763027221846, 1125.1248029969229   ],
    [1557.763027221846, 1095.0070549793309   ],
    [1557.763027221846, 1068.6540254639376   ],
    [1557.7870329569146, 1019.7126849353499  ],
    [1557.7870329569146, 989.5949369177579   ],
    [1557.7870329569146, 959.4771889001659   ],
    [1557.7870329569146, 929.3594408825738   ],
    [1557.8110386919834, 831.4767598254002   ],
    [1557.8110386919834, 801.3590118078082   ],
    [1557.8110386919834, 771.2412637902162   ],
    [1557.8110386919834, 744.8882342748229   ],
    [1557.8110386919834, 658.2997087242456   ],
    [1557.8110386919834, 628.1819607066536   ],
    [1557.8110386919834, 598.0642126890616   ],
    [1557.8110386919834, 567.9464646714696   ],
    [1557.8110386919834, 473.82850211649384  ],
    [1557.8590501621209, 409.828287579111    ],
    [1557.8590501621209, 383.4752580637178   ],
    [1557.8590501621209, 296.8867325131405   ],
    [1557.8590501621209, 266.76898449554847  ],
    [1557.8670520738106, 447.4754726011015   ],
    [1557.9070616322585, 236.65123647795645  ],
    [1557.9790788374648, 229.1217994735589   ],
    [1558.0991075128086, 206.53348846036442  ],
    [1558.147118982946, 176.4157404427724    ],
    [1558.1951304530835, 157.59214793177762  ],
    [1558.2511438349106, 133.74893075118416  ],
    [1558.339164863496, 202.76876995816565   ],
    [1558.4351878037712, 199.00405145596687  ],
    [1558.4351878037712, 168.88630343837485  ],
    [1558.4831992739087, 142.5332739229816   ],
    [1558.7232566245964, 131.23911841638437  ],
    [1558.7712680947338, 112.41552590538959  ],
    [1558.8192795648713, 146.29799242518038  ],
    [1558.867291035009, 127.4743999141856    ],
    [1559.1553598558341, 123.70968141198682  ],
    [1559.1553598558341, 101.12137039879235  ],
    [1559.251382796109, 108.6508074031899    ],
    [1559.3474057363842, 131.23911841638437  ],
    [1559.4194229415905, 138.76855542078283  ],
    [1559.6354745572094, 135.00383691858315  ],
    [1559.7314974974843, 116.18024440758836  ],
    [1559.8275204377594, 119.94496290978714  ],
    [1559.8755319078969, 146.29799242518038  ],
    [1560.0195663183094, 150.06271092737916  ],
    [1560.1155892585846, 176.4157404427724   ],
    [1560.1155892585846, 150.06271092737916  ],
    [1560.2116121988595, 157.59214793177762  ],
    [1560.475675284616, 168.88630343837485   ],
    [1560.4996810196847, 183.94517744717086  ],
    [1560.5076829313743, 221.59236246916043  ],
    [1560.5236867547535, 349.592791543927    ],
    [1560.5236867547535, 266.76898449554847  ],
    [1560.5476924898223, 394.769413570315    ],
    [1560.5476924898223, 364.651665552723    ],
    [1560.5556944015118, 432.4165985923046   ],
    [1560.5957039599598, 534.0639981516779   ],
    [1560.6037058716493, 567.9464646714696   ],
    [1560.6437154300972, 462.5343466098975   ],
    [1560.6437154300972, 432.4165985923046   ],
    [1560.6437154300972, 402.29885057471256  ],
    [1560.6437154300972, 379.710539561519    ],
    [1560.6437154300972, 293.1220140109417   ],
    [1560.667721165166, 567.9464646714696    ],
    [1560.667721165166, 266.76898449554847   ],
    [1560.6917269002347, 229.1217994735589   ],
    [1560.6917269002347, 202.76876995816565  ],
    [1560.7877498405098, 176.4157404427724   ],
    [1560.8357613106473, 236.65123647795645  ],
    [1560.8357613106473, 206.53348846036442  ],
    [1560.8597670457161, 183.94517744717086  ],
    [1560.883772780785, 263.0042659933497    ],
    [1560.9797957210599, 304.41616951753895  ],
    [1561.035809102887, 266.76898449554847   ],
    [1561.0838205730245, 224.10217480396022  ],
    [1561.2198530717476, 138.76855542078283  ],
    [1561.3158760120225, 150.06271092737916  ],
    [1561.3718893938496, 178.9255527775722   ],
    [1561.6039448328477, 176.4157404427724   ],
    [1561.6039448328477, 153.82742942957884  ],
    [1561.6519563029854, 206.53348846036442  ],
    [1561.675962038054, 183.94517744717086   ],
    [1561.6999677731228, 240.41595498015522  ],
    [1561.7479792432603, 327.0044805307325   ],
    [1561.795990713398, 353.35751004612575   ],
    [1561.8039926250874, 387.23997656591655  ],
    [1561.8920136536728, 289.35729550874294  ],
    [1561.8920136536728, 259.2395474911509   ],
    [1561.8920136536728, 229.1217994735589   ],
    [1561.9160193887417, 199.00405145596687  ],
    [1562.14007291605, 178.9255527775722     ],
    [1562.2280939446355, 206.53348846036442  ],
    [1562.3241168849106, 191.4746144515684   ],
    [1562.396134090117, 199.00405145596687   ],
    [1562.4201398251857, 251.71011048675246  ],
    [1562.4761532070127, 221.59236246916043  ],
    [1562.564174235598, 191.4746144515684    ],
    [1562.6121857057358, 172.65102194057363  ],
    [1562.8042315862858, 191.4746144515684   ],
    [1562.8522430564233, 172.65102194057363  ],
    [1562.9242602616296, 176.4157404427724   ],
    [1562.9482659966984, 206.53348846036442  ],
    [1563.0202832019047, 206.53348846036442  ],
    [1563.2363348175236, 191.4746144515684   ],
    [1563.2363348175236, 168.88630343837485  ],
    [1563.284346287661, 221.59236246916043   ],
    [1563.3083520227299, 199.00405145596687  ],
    [1563.3883711396256, 239.16104881275623  ],
    [1563.4523864331425, 244.1806734823549   ],
    [1563.5484093734174, 168.88630343837485  ],
    [1563.5724151084862, 191.4746144515684   ],
    [1563.6204265786237, 221.59236246916043  ],
    [1563.69244378383, 229.1217994735589     ],
    [1563.9084953994488, 225.3570809713592   ],
    [1563.9805126046551, 199.00405145596687  ],
    [1564.004518339724, 214.06292546476288   ],
    [1564.1085431916886, 209.0433007951642   ],
    [1564.1725584852052, 221.59236246916043  ],
    [1564.3005890722386, 239.16104881275623  ],
    [1564.3646043657554, 229.1217994735589   ],
    [1564.388610100824, 281.8278585043445    ],
    [1564.388610100824, 255.47482898895123   ],
    [1564.4606273060303, 266.76898449554847  ],
    [1564.5326445112366, 191.4746144515684   ],
    [1564.580655981374, 221.59236246916043   ],
    [1564.6286674515118, 199.00405145596687  ],
    [1564.6526731865804, 221.59236246916043  ],
    [1564.7486961268555, 259.2395474911509   ],
    [1564.7807037736138, 284.33767083914427  ],
    [1564.8687248021993, 311.9456065219365   ],
    [1564.9407420074056, 304.41616951753895  ],
    [1564.9647477424744, 330.7691990329322   ],
]

# test
#sp = SP2750()
#sp.strip_response()

# real
gui = GUI()  # starts GUI
gui.window.mainloop()
gui.sp.disconnect()   # closes connection with spectrometer

print("Closing program!")


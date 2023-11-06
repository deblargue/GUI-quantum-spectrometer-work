import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import time
from datetime import date
import numpy as np


# ---- Implement the default Matplotlib key bindings:
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# from matplotlib.backend_bases import key_press_handler

# TODO:
#  - check what variables need to be int vs floats!!! -->  tk.IntVar  or  tk.DoubleVar
#  - make a print tab to the right where "progress is being shown :)"
#  - when devices are set, button turns green
#  - plots
#  - ETA data saving and reading
#  - Display counts
#  - Add buttons for "setting" configurations (and indication/display of what is set)
#  - Add scrollbar for counts display (for when we have many)
#  - Add buttons to change spectrum plot x-label
#  - Add integration time
#  -

class GUI:

    def __init__(self):

        # --- MAIN ----
        self.current_file_name = None
        self.current_file_type = None
        self.current_file_path = None
        self.widgets = {}
        self.defaults = {}

        # INIT WINDOW
        self.window = tk.Tk()
        self.window.title("Ghostly matters - GUI")
        self.window.rowconfigure(0, minsize=30, weight=1)
        self.window.columnconfigure(0, minsize=50, weight=1)

        # create and place tabs frame on window grid
        self.fill_tabs()

        self.define_default_settings()  # TODO: later save to and from file

    def mark_done(self, button, col="#82CC6C"):
        button.config(highlightbackground=col)  # green

    def unmark_done(self, button, col='white'):
        button.config(highlightbackground=col)  # green

    def send_configs(self, tab):

        def get_str():
            temp1 = f"slit = {self.slit.get()} [um]"
            temp2 = f"grating = {self.grating.get()} "
            temp3 = f"center = {self.center_wavelength.get()} [nm]"
            temp4 = f"width = {self.width_wavelength.get()} [nm]"
            return [temp1, temp2, temp3, temp4]

        def check():
            temp = get_str()

            send_txt_1.config(text=temp[0], foreground='black')   # make green for passed tests!
            send_txt_2.config(text=temp[1], foreground='black')   # make green for passed tests!
            send_txt_3.config(text=temp[2], foreground='black')   # make green for passed tests!
            send_txt_4.config(text=temp[3], foreground='black')   # make green for passed tests!

            #self.ok_to_send = False

        def send():
            try:   # woking parts will be marked green
                if self.ok_to_send:
                    print(self.widgets['test_config'])
                    self.mark_done(btn_send_conf)
            except: #???
                pass

        temp = get_str()

        self.ok_to_send = False
        frm_send = tk.Frame(tab, relief=tk.RAISED, bd=2)

        send_txt_1 = tk.Label(frm_send, text=temp[0], foreground='white', justify="left")
        send_txt_2 = tk.Label(frm_send, text=temp[1], foreground='white', justify="left")
        send_txt_3 = tk.Label(frm_send, text=temp[2], foreground='white', justify="right")
        send_txt_4 = tk.Label(frm_send, text=temp[3], foreground='white', justify="right")

        btn_check_conf = tk.Button(frm_send, text="Check", command=check, activeforeground='blue')
        btn_send_conf = tk.Button(frm_send, text="Send Configs", command=send, activeforeground='green')

        send_txt_1.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        send_txt_2.grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        send_txt_3.grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        send_txt_4.grid(row=3, column=0, sticky="nw", padx=5, pady=5)

        btn_check_conf.grid(row=4, column=0, sticky="nw", padx=5, pady=5)
        btn_send_conf.grid(row=5, column=0, sticky="nw", padx=5, pady=5)

        return frm_send

    def test_combine_config_tab(self, tab):

        def default_0():  # clears everything
            print("Clear all")
            self.unmark_done(btn_def_1)
            self.unmark_done(btn_def_2)
            self.unmark_done(btn_def_3)

            for key in self.defaults.keys():
                #if key == 'nr_channels':
                #   self.defaults['nr_channels']['variable'].set(8)
                #   continue

                if self.defaults[key]['type'] == 'radio':
                    self.defaults[key]['variable'].set(0)
                elif self.defaults[key]['type'] == 'int entry':
                    self.defaults[key]['variable'].set(0)
                elif self.defaults[key]['type'] == 'str entry':
                    self.defaults[key]['variable'].set('')

            fill_ch()

        def default_1():
            default_button_press(0)
            self.unmark_done(btn_def_2)
            self.unmark_done(btn_def_3)
            self.mark_done(btn_def_1, col='blue')

        def default_2():
            default_button_press(1)
            self.unmark_done(btn_def_1)
            self.unmark_done(btn_def_3)
            self.mark_done(btn_def_2, col='blue')

        def default_3():
            default_button_press(2)
            self.unmark_done(btn_def_1)
            self.unmark_done(btn_def_2)
            self.mark_done(btn_def_3, col='blue')

        def default_button_press(n=0):
            for key in self.defaults.keys():
                # print("setting default:", key)
                self.defaults[key]['variable'].set(self.defaults[key]['value'][n])
                # note there can be several saved default sets

            fill_ch()

        def select_grating():  # TODO
            pass
            # selection = "\nChosen: " + str(self.grating.get())
            # label_choice.config(text=selection)
            # print("Updated grating to", str(self.grating.get()))

        def update_ch():
            self.channels = []

            # removes previously shown channels (in case we want to decrease in amount)
            for j, widget in enumerate(frm_ch.winfo_children()):   # FIXME NOTE TODO: USE THIS LATER TO ACCESS BUTTONS FOR MARKING DONE
                if j > 2:
                    widget.destroy()

            fill_ch()

        def fill_ch():
            for i in range(self.nr_channels.get()):
                #self.c1 = tk.IntVar()
                self.channels.append(tk.IntVar())  #

                tk.Label(frm_ch, text=f"Ch {i + 1}").grid(row=i + 2, column=0, sticky="ew", padx=5, pady=5)
                tk.Entry(frm_ch, bd=2, textvariable=self.channels[i], width=6).grid(row=i + 2, column=1, sticky="ew", padx=5, pady=5)

        # GLOBALS -----
        self.slit = tk.DoubleVar()  # IntVar()
        self.grating = tk.IntVar()  # for choice of grating
        self.grating_levels = [1, 2, 3]

        self.center_wavelength = tk.IntVar()
        self.width_wavelength = tk.IntVar()
        self.nr_channels = tk.IntVar(value=8)
        self.channels = []
        # ---------------

        # FRAMES
        frm_test = tk.Frame(tab, relief=tk.RAISED, bd=2)
        
        frm_default = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_slit = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_grating = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_detect = tk.Frame(frm_test, relief=tk.RAISED, bd=2)
        frm_ch = tk.Frame(frm_test, relief=tk.RAISED, bd=2)

        # WIDGETS
        #  -- Default:
        btn_clear = tk.Button(frm_default, text="Clear all", command=default_0, activeforeground='red')
        btn_def_1 = tk.Button(frm_default, text="Default 1", command=default_1, activeforeground='blue')
        btn_def_2 = tk.Button(frm_default, text="Default 2", command=default_2, activeforeground='blue')
        btn_def_3 = tk.Button(frm_default, text="Default 3", command=default_3, activeforeground='blue')

        #  -- Slit:
        slt_txt = tk.Label(frm_slit, text='Slit width')
        slt_entry = tk.Entry(frm_slit, bd=2, textvariable=self.slit, width=5)
        slt_unit = tk.Label(frm_slit, text='[um?]')

        #  -- Grating:
        grt_txt = tk.Label(frm_grating, text='Grating')
        grt_rad_1 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[0]), variable=self.grating, value=self.grating_levels[0], command=select_grating)
        grt_rad_2 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[1]), variable=self.grating, value=self.grating_levels[1], command=select_grating)
        grt_rad_3 = tk.Radiobutton(frm_grating, text=str(self.grating_levels[2]), variable=self.grating, value=self.grating_levels[2], command=select_grating)

        #  -- Detector:
        det_txt = tk.Label(frm_detect, text="Detector")

        det_wave_txt = tk.Label(frm_detect, text="Center wavelength")
        det_wave_val = tk.Entry(frm_detect, bd=2, textvariable=self.center_wavelength, width=6)
        det_wave_unit = tk.Label(frm_detect, text='[nm]')

        det_width_txt = tk.Label(frm_detect, text="Channel width")
        det_width_val = tk.Entry(frm_detect, bd=2, textvariable=self.width_wavelength, width=6)
        det_width_unit = tk.Label(frm_detect, text='[nm]')

        det_no_txt = tk.Label(frm_detect, text="Nr. of channels")
        det_no_val = tk.Entry(frm_detect, bd=2, textvariable=self.nr_channels, width=6)
        #det_no_unit = tk.Label(frm_detect, text='')
        ch_butt0 = tk.Button(frm_detect, text="Update", command=update_ch, activeforeground='green')  # NOTE: previously in channel frame below

        # -- Channels:
        ch_txt_ch = tk.Label(frm_ch, text='Channel')
        ch_txt_bias = tk.Label(frm_ch, text='Bias')
        ch_txt_cnts = tk.Label(frm_ch, text='Counts')

        # GRID
        # -- Default
        btn_clear.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        btn_def_1.grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        btn_def_2.grid(row=0, column=2, sticky="ew", padx=3, pady=3)
        btn_def_3.grid(row=0, column=3, sticky="ew", padx=3, pady=3)

        # -- Slit
        slt_txt.grid(row=0, column=0, sticky="", padx=3, pady=3)
        slt_entry.grid(row=0, column=1, sticky="", padx=3, pady=3)
        slt_unit.grid(row=0, column=2, sticky="", padx=3, pady=3)

        # -- Grating
        grt_txt.grid(row=2, column=0, sticky="", padx=3, pady=3)
        grt_rad_1.grid(row=2, column=1, sticky="s", padx=3, pady=3)
        grt_rad_2.grid(row=2, column=2, sticky="s", padx=3, pady=3)
        grt_rad_3.grid(row=2, column=3, sticky="s", padx=3, pady=3)

        # -- Detector
        det_txt.grid(row=0, column=0, columnspan=2, sticky="ew", padx=3, pady=3)

        det_wave_txt.grid(row=1, column=0, sticky="ew", padx=3, pady=3)
        det_wave_val.grid(row=1, column=1, sticky="ew", padx=3, pady=3)
        det_wave_unit.grid(row=1, column=2, sticky="ew", padx=3, pady=3)

        det_width_txt.grid(row=2, column=0, sticky="ew", padx=3, pady=3)
        det_width_val.grid(row=2, column=1, sticky="ew", padx=3, pady=3)
        det_width_unit.grid(row=2, column=2, sticky="ew", padx=3, pady=3)

        det_no_txt.grid(row=3, column=0, sticky="ew", padx=3, pady=3)
        det_no_val.grid(row=3, column=1, sticky="ew", padx=3, pady=3)
        #det_no_unit.grid(row=3, column=2, sticky="ew", padx=3, pady=3)   # there is no unit for number of channels
        ch_butt0.grid(row=3, column=2, sticky="ew", padx=5, pady=5)   # updates the channels displayed

        # -- Channels
        ch_txt_ch.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ch_txt_bias.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ch_txt_cnts.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        fill_ch()

        # ------------- COMBINING INTO TEST FRAME --------------
        frm_default.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        frm_slit.grid(row=1, column=0, sticky="ew", padx=3, pady=3)
        frm_grating.grid(row=2, column=0, sticky="ew", padx=3, pady=3)
        frm_detect.grid(row=3, column=0, sticky="ew", padx=3, pady=3)
        frm_ch.grid(row=4, column=0, rowspan=100, sticky="ew", padx=3, pady=3)

        return frm_test

    def fill_tabs(self):
        tabControl = ttk.Notebook(self.window)

        # ---- Settings and configurations  TAB ----
        settings_tab = ttk.Frame(tabControl)

        # ---- TEST Start new scan TAB ----  NOTE this should include settings and prep
        test_new_scan_tab = ttk.Frame(tabControl)

        self.widgets['test_config'] = self.test_combine_config_tab(test_new_scan_tab)
        self.widgets['misc'] = self.create_file_config(test_new_scan_tab)
        #self.widgets['channels'] = self.create_channel_config(test_new_scan_tab)

        self.widgets['test_config'].grid(row=0, column=1, sticky="n", padx=5, pady=5)
        #self.widgets['channels'].grid(row=1, column=1, rowspan=100, sticky="n", padx=5, pady=5)
        self.widgets['misc'].grid(row=0, column=3, columnspan=1, sticky="n", padx=5, pady=5)

        send_conf = self.send_configs(test_new_scan_tab)
        send_conf.grid(row=0, column=4, sticky="n", padx=5, pady=5)


        # ---- Start new scan TAB ----  NOTE this should include settings and prep
        """new_scan_tab = ttk.Frame(tabControl)

        self.widgets['default'] = self.create_default_buttons(new_scan_tab)
        self.widgets['default'].grid(row=0, column=0, sticky="", padx=5, pady=5)

        self.widgets['grating'] = self.create_grating_config(new_scan_tab)
        self.widgets['grating'].grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.widgets['entries'] = self.create_detector_config(new_scan_tab)
        self.widgets['entries'].grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self.widgets['misc'] = self.create_file_config(new_scan_tab)
        self.widgets['misc'].grid(row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        self.widgets['channels'] = self.create_channel_config(new_scan_tab)
        self.widgets['channels'].grid(row=0, column=4, rowspan=100,  sticky="new", padx=5, pady=5)"""

        # ---- 1 Plots  TAB ----
        plots_spectrum = ttk.Frame(tabControl)

        plt_frame, butt_frame = self.create_spectrum_plot(plots_spectrum)
        self.widgets['plot_spectrum_1'] = plt_frame
        self.widgets['plot_spectrum_1'].grid(row=0, rowspan=4, column=0, sticky="nsew", padx=5, pady=5)

        self.widgets['info_spectrum'] = self.create_plot_info(plots_spectrum, "Spectrum plot info")
        self.widgets['info_spectrum'].grid(row=0, rowspan=3, column=1, sticky="nsew" , padx=5, pady=5)

        self.widgets['butt_spectrum_1'] = butt_frame
        self.widgets['butt_spectrum_1'].grid(row=3, column=1, sticky="nsew", padx=5, pady=5)

        # ---- 2 Plots  TAB ----
        plots_correlation = ttk.Frame(tabControl)

        self.widgets['plot_correlation_1'] = self.create_correlation_plot(plots_correlation)
        self.widgets['plot_correlation_1'].grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.widgets['info_correlation'] = self.create_plot_info(plots_correlation, "Correlation plot info")
        self.widgets['info_correlation'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=5, pady=5)

        # ---- 3 Plots  TAB ----
        plots_lifetime = ttk.Frame(tabControl)

        self.widgets['plot_lifetime_1'] = self.create_choose_lifetime_plot(plots_lifetime)
        self.widgets['plot_lifetime_1'].grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.widgets['info_lifetime'] = self.create_plot_info(plots_lifetime, "Lifetime plot info")
        self.widgets['info_lifetime'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=5, pady=5)

        # ---- All Plots  TAB ----
        plots_3d_lifetime = ttk.Frame(tabControl)

        self.widgets['plot_3D_lifetime_1'] = self.create_3D_lifetime_plot(plots_3d_lifetime)
        self.widgets['plot_3D_lifetime_1'].grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.widgets['info_3D_lifetime'] = self.create_plot_info(plots_3d_lifetime, "3D Lifetime plot info")
        self.widgets['info_3D_lifetime'].grid(row=0, rowspan=2, column=2, sticky="nsew" , padx=5, pady=5)

        # ---- Text Editor TAB ----
        txt_tab = ttk.Frame(tabControl)

        self.widgets['save_buttons'] = self.create_text_save_buttons(txt_tab)
        self.widgets['save_buttons'].grid(rowspan=2, column=0, sticky="nsew")  # , padx=5, pady=5)

        self.widgets['disp_filepath'] = tk.Label(txt_tab, text=f'new file')
        self.widgets['disp_filepath'].grid(row=0, column=1, sticky="nsew")  # , padx=5, pady=5)

        self.widgets['txt_editor'] = self.create_text_editor(txt_tab)
        self.widgets['txt_editor'].grid(row=1, column=1, sticky="nsew")  # , padx=5, pady=5)

        # ---- Add all tabs to window: ----

        tabControl.add(test_new_scan_tab, text='Test Start New Scan')
        #tabControl.add(new_scan_tab, text='Start New Scan')
        tabControl.add(plots_spectrum, text='Spectrum Plot')
        tabControl.add(plots_correlation, text='Correlation Plot')
        tabControl.add(plots_lifetime, text='Lifetime Plot')
        tabControl.add(plots_3d_lifetime, text='3D Lifetime Plot')
        tabControl.add(settings_tab, text='Settings')
        tabControl.add(txt_tab, text='Text editor')
        tabControl.pack(expand=1, fill="both")

    """
    def create_default_buttons(self, tab):
        # EXAMPLE:
        # self.defaults = {'grating': {'variable': self.grating, 'type': 'radio', 'value': 1}}
        # self.defaults['grating']['variable'] = self.grating
        # self.defaults['grating']['type'] = 'radio'
        # self.defaults['grating']['value'] = 1
        def default_0():   # clears everything
            for key in self.defaults.keys():
                if self.defaults[key]['type'] == 'radio':
                    self.defaults[key]['variable'].set(0)
                elif self.defaults[key]['type'] == 'int entry':
                    self.defaults[key]['variable'].set(0)
                elif self.defaults[key]['type'] == 'str entry':
                    self.defaults[key]['variable'].set('')

        def default_1():
            default_button_press(0)

        def default_2():
            default_button_press(1)

        def default_3():
            default_button_press(2)

        def default_button_press(n=0):
            for key in self.defaults.keys():
                #print("setting default:", key)
                self.defaults[key]['variable'].set(self.defaults[key]['value'][n])
                # note there can be several saved default sets

        def_buttons = tk.Frame(tab, relief=tk.RAISED, bd=2)
        btn_new_0 = tk.Button(def_buttons, text="Clear all", command=default_0)
        btn_new_0.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        btn_new_1 = tk.Button(def_buttons, text="Default 1", command=default_1)
        btn_new_1.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        btn_new_2 = tk.Button(def_buttons, text="Default 2", command=default_2)
        btn_new_2.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        btn_new_3 = tk.Button(def_buttons, text="Default 3", command=default_3)
        btn_new_3.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        return def_buttons

    def create_grating_config(self, tab):

        def select():  # TODO
            pass
            #selection = "\nChosen: " + str(self.grating.get())
            #label_choice.config(text=selection)
            #print("Updated grating to", str(self.grating.get()))

        self.slit = tk.IntVar()
        self.grating = tk.IntVar()  # for choice of grating
        self.grating_levels = [1, 2, 3]
        frm_grating = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(frm_grating, text='Slit').grid(row=0, column=0, sticky="", padx=2, pady=3)
        tk.Entry(frm_grating, bd=2, textvariable=self.slit, width=5).grid(row=0, column=1, sticky="", padx=2, pady=3)
        tk.Label(frm_grating, text='[..m?]').grid(row=0, column=2, sticky="", padx=2, pady=3)

        '''tk.Label(frm_grating, text='Grating').grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        tk.Radiobutton(frm_grating, text="1", variable=self.grating, value=1, command=select).grid(row=1, column=1, sticky="ew", padx=2, pady=3)
        tk.Radiobutton(frm_grating, text="2", variable=self.grating, value=2, command=select).grid(row=2, column=1, sticky="ew", padx=2, pady=3)
        tk.Radiobutton(frm_grating, text="3", variable=self.grating, value=3, command=select).grid(row=3, column=1, sticky="ew", padx=2, pady=3)'''

        tk.Label(frm_grating, text='Grating').grid(row=2, column=0, sticky="", padx=5, pady=3)
        tk.Radiobutton(frm_grating, text="", variable=self.grating, value=self.grating_levels[0], command=select).grid(row=2, column=1, sticky="s", padx=0, pady=3)
        tk.Radiobutton(frm_grating, text="", variable=self.grating, value=self.grating_levels[1], command=select).grid(row=2, column=2, sticky="s", padx=0, pady=3)
        tk.Radiobutton(frm_grating, text="", variable=self.grating, value=self.grating_levels[2], command=select).grid(row=2, column=3, sticky="s", padx=0, pady=3)

        tk.Label(frm_grating, text=str(self.grating_levels[0])+"  ").grid(row=3, column=1, sticky="n", padx=0, pady=3)
        tk.Label(frm_grating, text=str(self.grating_levels[1])+"  ").grid(row=3, column=2, sticky="n", padx=0, pady=3)
        tk.Label(frm_grating, text=str(self.grating_levels[2])+"  ").grid(row=3, column=3, sticky="n", padx=0, pady=3)


        return frm_grating

    def create_detector_config(self, tab):

        self.center_wavelength = tk.IntVar()
        self.width_wavelength = tk.IntVar()
        self.nr_channels = tk.IntVar()

        frm_entry = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(frm_entry, text="Detector").grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        config_dict = {
            "Center wavelength"            : {'var' : self.center_wavelength, 'unit' : '[nm]'},
            "Wavelength width per pixel"   : {'var' : self.width_wavelength, 'unit' : '[nm]'},
            "Nr. of channels (pixles)"     : {'var' : self.nr_channels, 'unit' : ''},
            }

        for i, key in enumerate(config_dict.keys()):
            tk.Label(frm_entry, text=key).grid(row=i+1, column=0, sticky="ew", padx=5, pady=5)
            tk.Entry(frm_entry, bd=2, textvariable=config_dict[key]['var'], width=6).grid(row=i+1, column=1, sticky="ew", padx=5, pady=5)
            tk.Label(frm_entry, text=config_dict[key]['unit']).grid(row=i+1, column=2, sticky="ew", padx=5, pady=5)

        return frm_entry

    # NOTE: maybe remove
    def create_channel_config(self, tab):

        def update_ch():
            self.channels = []

            # removes previously shown channels (in case we want to decrease in amount)
            for j, widget in enumerate(frm_ch.winfo_children()):
                if j > 4:
                    widget.destroy()

            for i in range(self.nr_channels.get()):
                #self.c1 = tk.IntVar()
                self.channels.append(tk.IntVar())  #

                tk.Label(frm_ch, text=f"Ch {i + 1}").grid(row=i + 2, column=0, sticky="ew", padx=5, pady=5)
                tk.Entry(frm_ch, bd=2, textvariable=self.channels[i], width=6).grid(row=i + 2, column=1, sticky="ew", padx=5, pady=5)

        frm_ch = tk.Frame(tab, relief=tk.RAISED, bd=2)

        # Prompts to update number of channels displayed
        butt0 = tk.Button(frm_ch, text="Update", command=update_ch)
        butt0.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        tk.Label(frm_ch, text='Channel').grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        tk.Label(frm_ch, text='Bias').grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        tk.Label(frm_ch, text='Counts').grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        tk.Label(frm_ch, text='Counts??').grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        
        '''for i in range(self.nr_channels.get()):
            tk.Label(frm_ch, text=f"Ch {i+1}").grid(row=i+2, column=0, sticky="ew", padx=5, pady=5)
            tk.Entry(frm_ch, bd=2, textvariable=channels[i], width=6).grid(row=i+2, column=1, sticky="ew", padx=5, pady=5)
        return frm_ch'''

        return frm_ch
    """

    def create_file_config(self, tab):

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
            temp = f"grating({self.grating.get()})_" \
                   f"lamda({self.center_wavelength.get()})_" \
                   f"channels({self.nr_channels.get()})_" \
                   f"date({currDate})_time({currTime}).timeres"
            name_entry.delete(0, tk.END)
            name_entry.insert(0, temp)

        self.file_name = tk.StringVar()
        self.file_folder = tk.StringVar()
        self.eta_recipe = tk.StringVar()
        #self.misc4 = tk.IntVar()

        frm_misc = tk.Frame(tab, relief=tk.RAISED, bd=2)

        tk.Label(frm_misc, text="Analysis Configs").grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        tk.Label(frm_misc, text="(optional)").grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        tk.Label(frm_misc, text="New File Name").grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        name_entry = tk.Entry(frm_misc, bd=2, textvariable=self.file_name, width=20)
        name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        butt0 = tk.Button(frm_misc, text="Suggest...", command=suggest_filename)
        butt0.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        tk.Label(frm_misc, text="New File Location").grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        folder_entry = tk.Entry(frm_misc, bd=2, textvariable=self.file_folder, width=20)
        folder_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        butt1 = tk.Button(frm_misc, text="Open Folder", command=get_folder)
        butt1.grid(row=2, column=2, sticky="ew", padx=5, pady=5)

        tk.Label(frm_misc, text="ETA recipe").grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        recipe_entry = tk.Entry(frm_misc, bd=2, textvariable=self.eta_recipe, width=40)
        recipe_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        butt2 = tk.Button(frm_misc, text="Choose File", command=get_recipe)
        butt2.grid(row=3, column=2, sticky="ew", padx=5, pady=5)

        #tk.Label(frm_misc, text="...?").grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        #tk.Entry(frm_misc, bd=2, textvariable=self.misc4, width=40).grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        return frm_misc

     # ---- PLOTTING ----
    def create_spectrum_plot(self, tab):

        # TODO: create live graph???

        def pressed_xlabel():
            # TODO: add data conversion for respective unit
            # x = ...
            fig.clear()
            plot1 = fig.add_subplot(111)
            plot1.plot(y)  # plot1.(plot(x,y))
            plot1.set_xlabel(x_label.get())
            plot1.set_ylabel("counts")
            plot1.set_title("Spectrum")
            canvas.draw()

        x_label = tk.StringVar()
        x_label.set('lamda [nm]')

        # the figure that will contain the plot
        fig = plt.Figure(figsize=(10, 6), dpi=100)

        #x =
        # temp data
        y = [i ** 2 for i in range(101)]

        # adding the subplot
        plot1 = fig.add_subplot(111)
        plot1.plot(y)
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
        tk.Radiobutton(butt_frame, text="wavelength", value='wavelength    λ [nm]', variable=x_label, command=pressed_xlabel).grid(row=1, column=0, sticky="ew", padx=2, pady=3)
        tk.Radiobutton(butt_frame, text="frequency", value='frequency    f [Hz]', variable=x_label, command=pressed_xlabel).grid(row=2, column=0, sticky="ew", padx=2, pady=3)
        tk.Radiobutton(butt_frame, text="photon energy", value='photon energy    E [eV]', variable=x_label, command=pressed_xlabel).grid(row=3, column=0, sticky="ew", padx=2, pady=3)
        tk.Radiobutton(butt_frame, text="spectroscopic wave number", value='spectroscopic wave number    v [cm^-1]', variable=x_label, command=pressed_xlabel).grid(row=4, column=0, sticky="ew", padx=2, pady=3)

        return plt_frame, butt_frame

    def create_correlation_plot(self, tab):
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

    def create_3D_lifetime_plot(self, tab):
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

    def create_choose_lifetime_plot(self, tab):
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

    def create_plot_info(self, tab, tab_str):

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

    def create_text_editor(self, tab):
        # TODO: ADD SCROLLBAR
        t = tk.Text(tab)  # , xscrollcommand=h.set, yscrollcommand=v.set)
        return t

    def create_text_save_buttons(self, tab):

        def show_msg(msg, timeout=1000):
            lbl = tk.Label(text=msg, font=('', 14), bg='grey', relief=tk.RAISED, bd=2)
            lbl.place(relx=0.5, rely=0.2, anchor=tk.CENTER)
            self.window.after(timeout, lbl.destroy)  # timeout in ms

        def open_file():

            filepath = askopenfilename(
                filetypes=[("Text Files", "*.txt"), ("TimeRes", "*.timeres"), ("All Files", "*.*")])
            if not filepath:
                return

            self.widgets['txt_editor'].delete("1.0", tk.END)

            update_curr_file_var(filepath)  # updating global value of curr path

            if self.current_file_type == 'timeres':
                print("opening timeres file")
                with open(filepath, mode="rb") as input_file:
                    text = input_file.read()
                    text = str(text)
                    self.widgets['txt_editor'].insert(tk.END, text)

            elif self.current_file_type == 'txt':
                with open(filepath, mode="r", encoding="utf-8") as input_file:  # NOTE THIS ENCODING MIGHT NOT BE ENOUGH
                    text = input_file.read()
                    self.widgets['txt_editor'].insert(tk.END, text)
            else:
                print("NOT TXT OR TIMERES YET! RESETTING")
                self.current_file_type = None
                self.current_file_name = None
                self.current_file_path = None
                return

            self.widgets['disp_filepath'].config(text=f"{self.current_file_path}")

        def save_file():
            # If this is a new file (not opened or saved before) --> call save as function

            if self.current_file_path is None:  # --> need to get name!!
                # while current_file_path is None:
                print("Cannot save new file, instead saving as new file!")
                save_as_file()  # needs to ask for file name and type and path  # WARNING POTENTIAL RECURSION
                return

            # SAVE FILE!
            self.current_file_path = str(
                self.current_file_path)  # note: not actually needed but python complains about possibility of it being None type
            if self.current_file_type == 'txt':
                with open(self.current_file_path, mode="w", encoding="utf-8") as output_file:
                    text = self.widgets['txt_editor'].get("1.0", tk.END)
                    output_file.write(text)
            elif self.current_file_type == 'timeres':
                with open(self.current_file_path, mode="wb") as output_file:
                    text = self.widgets['txt_editor'].get("1.0", tk.END)  # FIXME bytes???
                    output_file.write(text)  # FIXME
            else:
                print("Could not save unknown filetype")
                show_msg(msg=" ~* ERROR: UNKNOWN FILETYPE *~ ", timeout=2000)
                # save_as_file()
                return

            show_msg(msg=" ~* FILE SAVED *~ ", timeout=1000)

            self.widgets['disp_filepath'].config(text=f"{self.current_file_path}")

        def save_as_file():

            """Save the current file as a new file."""
            filepath = asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("TimeRes", "*.timeres"), ("All Files", "*.*")],
            )
            if not filepath:  # if filepath is none? does this happen if we cancel?
                return

            update_curr_file_var(filepath)  # updating global value of curr path

            save_file()

        def new_file():
            self.widgets['txt_editor'].delete("1.0", tk.END)
            self.widgets['disp_filepath'].config(text=f"new file")
            self.current_file_path = None
            self.current_file_name = None
            self.current_file_type = None

        def update_curr_file_var(filepath):

            start_idx = filepath.rfind("/")
            stop_idx = filepath.rfind(".")
            self.current_file_path = filepath
            self.current_file_name = filepath[start_idx + 1: stop_idx]
            self.current_file_type = filepath[stop_idx + 1:]

        frm_buttons = tk.Frame(tab, relief=tk.RAISED, bd=2)

        btn_new = tk.Button(frm_buttons, text="New", command=new_file)
        btn_new.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        btn_open = tk.Button(frm_buttons, text="Open", command=open_file)
        btn_open.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        btn_save = tk.Button(frm_buttons, text="Save", command=save_file)
        btn_save.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        btn_save_as = tk.Button(frm_buttons, text="Save As...", command=save_as_file)
        btn_save_as.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        return frm_buttons

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
                'value': [1, 2, 3] },

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
                'value': [0.01, 0.1, 1]},

            'nr_channels': {
                'variable': self.nr_channels,
                'type': 'int entry',
                'value': [8, 8, 8]},

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


gui = GUI()  # starts GUI
gui.window.mainloop()


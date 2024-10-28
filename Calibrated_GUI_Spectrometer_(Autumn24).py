# - GUI IMPORTS
import serial
from serial.tools import list_ports
from datetime import date
import time                 # for eta?
import numpy as np

# - GUI IMPORTS
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename   # , askdirectory
from ttkthemes import ThemedTk
from tkinter import scrolledtext

# - PLOTTING IMPORTS
import matplotlib
matplotlib.use("TkAgg")   # NOTE: import order matters
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
# - RETINA SSPD driver IMPORTS
#from Code.RetinaFiles.src.WebSQController import WebSQController
# - Spectro GUI Library IMPORTS
from Code.SpectroGUILibrary.CIEColorMatching import ColorMatchingCIE
from Code.SpectroGUILibrary.SpectroGUILibrary import DebuggingFunctions, ETA, LiveCounts


# Plotting --> Approx 800 lines
class Plotting:
    def __init__(self, parent):
        self.parent = parent
        self.y_max_entry = tk.StringVar()
        self.y_max = tk.IntVar(value=1000)
        self.x_label = tk.StringVar(value='λ [nm]')
        self.scale_buttons = {}
        self.scale_buttons_3D = {}
        self.plots = {}  # TODO: save plot, axes, and frame handles for different plots
        # self.eta_class??? todo

    def plot_spectrum_widget(self, tab):

        def convert_values():
            # return a list of x values
            unit = self.x_label.get()
            if unit == "λ [nm]":
                return [value for value in x_bins]
            elif unit == "f [Hz]":
                return [2.99792458e9/(value*1e-9) for value in x_bins]  # c = 2.99792458e9
            elif unit == "E [eV]":
                return [1240/value for value in x_bins]
            elif unit == "v [1/cm]":
                return [1/(value_nm*1e-7) for value_nm in x_bins]
            else:
                self.parent.write_log(f"ERROR NOT FOUND")
                return []

        def pressed_xlabel():  # TODO: add data conversion for respective unit
            fig.clear()
            x_bins = convert_values()
            plot_spec(x_bins)

        def plot_spec(x_bins):
            plot1 = fig.add_subplot(111)

            N, bins, bars = plot1.hist(x=x_bins[:-1], bins=x_bins, weights=y_counts, rwidth=1, align='mid', edgecolor='white', linewidth=1 , label=ch_labels)  # TODO ASSIGN A CHANNEL A UNIVERSAL COLOR

            labels = []
            for b, bar in enumerate(bars):
                labels.append(f'ch.{b+1}')  # FIXME by mapping to channel

            plot1.set_title("Spectrum")
            plot1.set_xlabel(self.x_label.get())
            plot1.set_ylabel("counts")
            plot1.set_xlim([x_bins[0] - 2, x_bins[-1] + 2])  # plot1.set_xlim([725.9, 733.6])
            plot1.bar_label(bars, labels=labels)  # , fontsize=20, color='navy')
            canvas.draw()

        # TODO: Switch to utilizing calibrated values
        def get_bins():
            #nr_pix = self.parent.params['nr_pixels']['var'].get()
            nr_pix = 12  # len(self.parent.eta_class.folded_countrate_pulses.keys())   # TODO FIXME: what happens if we define more channels than we have data on?
            pixel_width = self.parent.params['width_nm']['var'].get()   # TODO: maybe make this different depending on which
            center_pix = self.parent.params['nm']['var'].get()

            left_pix_bound = center_pix - (nr_pix * pixel_width / 2)
            right_pix_bound = center_pix + (nr_pix * pixel_width / 2)

            bins = np.linspace(start=left_pix_bound, stop=right_pix_bound, num=nr_pix+1, endpoint=True)  # , dtype=)
            # TODO ADD LIST OF ACTUAL WAVELENGTHS
            bins = [726.1, 726.7, 727.3, 727.9, 728.5, 729.1,
                    729.7, 730.3, 730.9, 731.5, 732.1, 732.7, 733.3]
            return bins

        def get_counts():
            ch_labs = []  # bin centers   #TODO: use as extra label for x axis
            y_cnts = []  # total counts per bin
            # TODO FIX HARDCODE ABOVE TO BE NUMBER OF CHANNELS
            for i, channel in enumerate(self.parent.eta_class.folded_countrate_pulses.keys()):
                ch_labs.append(channel)  # TODO USE CHANNEL NUMBER TO GET WAVELENGTH
                y_cnts.append(sum(self.parent.eta_class.folded_countrate_pulses[channel]))  # TODO CHECK THAT THIS IS CORRECT
            return ch_labs, y_cnts

        self.x_label.set('λ [nm]')

        ch_labels, y_counts_temp = get_counts()
        y_counts = list(np.zeros(12))
        y_counts[4] = y_counts_temp[0]
        y_counts[5] = y_counts_temp[1]
        y_counts[6] = y_counts_temp[2]  # TODO FIXME THIS IS HARDCODED TEMP

        print("5-->", ch_labels[0])
        print("6-->", ch_labels[1])
        print("7-->", ch_labels[2])

        # style.use('ggplot')
        fig = plt.Figure(figsize=(8, 5), dpi=100)
        x_bins = get_bins()   # self.parent.eta_class.get

        # -----
        plt_frame, canvas = gui.pack_plot(tab, fig)
        plot_spec(x_bins)

        # BUTTONS:
        butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

        ttk.Label(butt_frame, text=f'Change X-axis to:').grid(row=0, column=0, sticky="nsew")
        ttk.Radiobutton(butt_frame, text="wavelength [nm]", value='λ [nm]', variable=self.x_label, command=pressed_xlabel).grid(row=1, column=0, sticky="ew")
        ttk.Radiobutton(butt_frame, text="frequency [Hz]", value='f [Hz]', variable=self.x_label, command=pressed_xlabel).grid(row=2, column=0, sticky="ew")
        ttk.Radiobutton(butt_frame, text="photon energy [eV]", value='E [eV]', variable=self.x_label, command=pressed_xlabel).grid(row=3, column=0, sticky="ew")
        ttk.Radiobutton(butt_frame, text="wave number [cm^{-1}]", value='v [1/cm]', variable=self.x_label, command=pressed_xlabel).grid(row=4, column=0, sticky="ew")

        plt_frame.grid(row=0, rowspan=4, column=0, sticky="nsew")
        butt_frame.grid(row=3, column=1, sticky="nsew")

    def plot_correlation_widget(self, tab):

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            butt_frame_t = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)

            ttk.Label(butt_frame_s, text="\nDisplay correlation:").grid(row=2, column=1, columnspan=2, sticky="ew")
            # TODO ADD CHECK BOXES

            #ttk.Checkbutton(butt_frame_t, text=lookup['h23'], command=update_plot, variable=self.ch_show_correlation['h23'], onvalue=True, offvalue=False).grid(row=0, column=0, columnspan=1, sticky="ew")
            #ttk.Checkbutton(butt_frame_t, text=lookup['h24'], command=update_plot, variable=self.ch_show_correlation['h24'], onvalue=True, offvalue=False).grid(row=1, column=0, columnspan=1, sticky="ew")
            #ttk.Checkbutton(butt_frame_t, text=lookup['h34'], command=update_plot, variable=self.ch_show_correlation['h34'], onvalue=True, offvalue=False).grid(row=2, column=0, columnspan=1, sticky="ew")
            ttk.Radiobutton(butt_frame_t, text=lookup['h23'], variable=active_plot, value='h23', command=update_plot).grid(row=0, column=0, columnspan=1, sticky="ew")
            ttk.Radiobutton(butt_frame_t, text=lookup['h24'], variable=active_plot, value='h24', command=update_plot).grid(row=1, column=0, columnspan=1, sticky="ew")
            ttk.Radiobutton(butt_frame_t, text=lookup['h34'], variable=active_plot, value='h34', command=update_plot).grid(row=2, column=0, columnspan=1, sticky="ew")

            butt_frame_s.grid(row=2, column=0, sticky="news")
            butt_frame_t.grid(row=3, column=0, sticky="news")

            return butt_frame

        def update_plot(scale=''):

            fig.clear()
            ax1 = fig.add_subplot(111)

            #b = self.parent.eta_class.lifetime_bins_ns
            ax1.set_title(f"G2 measurement")

            #for i, thing in enumerate(self.ch_show_correlation.keys()):
            #    if self.ch_show_correlation[thing].get() is False:
            #        print(f"{thing} is hidden")
            #        continue  # doesn't plot when hidden

            avg_val = np.mean(corr_dict[active_plot.get()])
            ax1.plot(delta_t, corr_dict[active_plot.get()]/avg_val, label=lookup[active_plot.get()])

            ax1.legend()
            ax1.set_xlabel('time [ns]', fontsize=10)
            ax1.set_ylabel('coincidence', fontsize=10)
            ax1.set_xlim([-30, 30])
            ax1.legend()
            fig.canvas.draw_idle()  # updates the canvas immediately?
        # h2 --> ch6
        # h3 --> ch7
        # h4 --> ch5
        lookup = {
            'h24': 'ch.5 - ch.6',
            'h23': 'ch.6 - ch.7',
            'h34': 'ch.5 - ch.7',
        }

        lookup_chs = {
            'h2': {
                'ch': '6',
                'nm': ch6_nm},
            'h3': {
                'ch': '7',
                'nm': ch7_nm},
            'h4': {
                'ch': '5',
                'nm': ch5_nm},
        }

        active_plot = tk.StringVar(value='h24')

        self.ch_show_correlation = {
            'h24': tk.BooleanVar(value=True),
            'h23': tk.BooleanVar(value=True),
            'h34': tk.BooleanVar(value=True),
        }

        # the figure that will contain the plot
        fig = plt.figure(figsize=(8, 5), dpi=100)  # 10 3
        ax1 = fig.add_subplot(111)
        delta_t, corr_dict = self.parent.eta_class.new_correlation_analysis()

        update_plot()

        plt_frame, canvas = gui.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()

        butt_frm.grid(row=0, column=2, columnspan=1, sticky="news")
        plt_frame.grid(row=0, rowspan=1, column=1, sticky="nsew")

    def plot_countrate_widget(self, tab):

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            butt_frame_t = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)

            ttk.Label(butt_frame_s, text="\nDisplay channels:").grid(row=2, column=1, columnspan=2, sticky="ew")
            # TODO ADD CHECK BOXES

            # NOTE: FIX THIS BELOW
            for ph_i in range(1, 13):
                if ph_i == 5:
                    ttk.Checkbutton(butt_frame_t, text=lookup['h4'], command=update_plot, variable=self.ch_show_countrate['h4'], onvalue=True, offvalue=False).grid(row=ph_i, column=0, columnspan=1, sticky="ew")
                elif ph_i == 6:
                    ttk.Checkbutton(butt_frame_t, text=lookup['h2'], command=update_plot, variable=self.ch_show_countrate['h2'], onvalue=True, offvalue=False).grid(row=ph_i, column=0, columnspan=1, sticky="ew")
                elif ph_i == 7:
                    ttk.Checkbutton(butt_frame_t, text=lookup['h3'], command=update_plot, variable=self.ch_show_countrate['h3'], onvalue=True, offvalue=False).grid(row=ph_i, column=0, columnspan=1, sticky="ew")
                else:
                    ttk.Checkbutton(butt_frame_t, text=lookup[f'ph{ph_i}'], state='disabled').grid(row=ph_i, column=0, columnspan=1,sticky="ew")
                    #but.configure(state='disabled')

            butt_frame_s.grid(row=2, column=0, sticky="news")
            butt_frame_t.grid(row=3, column=0, sticky="news")

            return butt_frame

        def update_plot(scale=''):

            fig.clear()
            ax1 = fig.add_subplot(111)

            #b = self.parent.eta_class.lifetime_bins_ns
            ax1.set_title(f"Countrate")

            for i, thing in enumerate(self.ch_show_countrate.keys()):
                if self.ch_show_countrate[thing].get() is False:
                    print(f"{thing} is hidden")
                    continue  # doesn't plot when hidden

                ax1.plot(time_axis, count_dict[thing], c=self.ch_colors[thing], label=lookup[thing]+' (0.1s)')
                #ax1.axhline(y=np.sum(count_dict[thing])/1.4, c=self.ch_colors[thing], linestyle='--', label=lookup[thing]+' (1s)')
                #ax1.axhline(y=np.sum(count_dict[thing]), c=self.ch_colors[thing], linestyle='-', label='TEMP: total accum')
                # TODO REMOVE^ only applicable for the 1s measurement

            ax1.legend()
            ax1.set_xlabel('time [s]', fontsize=10)
            ax1.set_ylabel('counts', fontsize=10)
            #ax1.set_xlim([-30, 30])
            ax1.legend()
            ax1.grid()
            fig.canvas.draw_idle()  # updates the canvas immediately?

        lookup = {'ph1':'ch.1',
                  'ph2': 'ch.2',
                  'ph3': 'ch.3',
                  'ph4': 'ch.4',
                  'h4' : 'ch.5',
                  'h2' : 'ch.6',
                  'h3' : 'ch.7',
                  'ph8':'ch.8',
                  'ph9':'ch.9',
                  'ph10':'ch.10',
                  'ph11':'ch.11',
                  'ph12':'ch.12',}

        self.ch_show_countrate = {
            'h4': tk.BooleanVar(value=True),
            'h2': tk.BooleanVar(value=True),
            'h3': tk.BooleanVar(value=True),
        }
        self.ch_colors = {
            'h4': 'tab:blue',
            'h2': 'tab:orange',
            'h3': 'tab:green'
        }

        # the figure that will contain the plot
        fig = plt.figure(figsize=(8, 5), dpi=100)  # 10 3
        ax1 = fig.add_subplot(111)
        time_axis, count_dict = self.parent.eta_class.new_countrate_analysis()

        update_plot()

        plt_frame, canvas = gui.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()

        butt_frm.grid(row=0, column=2, columnspan=1, sticky="news")
        plt_frame.grid(row=0, rowspan=1, column=1, sticky="nsew")

    def plot_lifetime_widget(self, tab):

        def reset_lims():
            x_min.set(0.0)
            x_max.set(self.parent.eta_class.lifetime_bins_ns[-1])
            y_min.set(0.0)
            max_count = [np.max(lst) for lst in self.parent.eta_class.folded_countrate_pulses.values()]
            print("max list", max_count)
            y_max.set(round(1.05 * np.max(max_count)))
            update_plot()

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_t = ttk.Frame(butt_frame, borderwidth=1, relief=tk.FLAT)

            # ttk.Label(butt_frame_t, text=f'\nAxis ranges:').grid(row=0, column=1, columnspan=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            ttk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'time').grid(row=2, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=x_min, width=6).grid(row=2, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=x_max, width=6).grid(row=2, column=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'counts').grid(row=3, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=y_min, width=5).grid(row=3, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=y_max, width=5).grid(row=3, column=2, sticky="ew")

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            ttk.Label(butt_frame_s, text="\nDisplay channels:").grid(row=2, column=1, columnspan=2, sticky="ew")
            ttk.Entry(butt_frame_s, textvariable=range_list, width=5).grid(row=3, column=1, columnspan=2, sticky="new")
            # ttk.Label(butt_frame_s, text="\nLine thickness:").grid(row=2, column=3, columnspan=2, sticky="new")
            # ttk.Entry(butt_frame_s, textvariable=line_thickness, width=5).grid(row=3, column=3, columnspan=2, sticky="new")

            butt_frame_p = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            # ttk.Label(butt_frame_p, text="\n  ").grid(row=0, column=0, sticky="ew")
            ttk.Label(butt_frame_p, text=f'\nScale:').grid(row=1, column=1, columnspan=1, sticky="ew")

            self.scale_buttons = {
                'linear': ttk.Radiobutton(butt_frame_p, text="Linear", value='linear', variable=plot_mode, command=press_scale_plot),
                'log': ttk.Radiobutton(butt_frame_p, text="Semi-Log", value='log', variable=plot_mode, command=press_scale_plot),
            }

            for i, thing in enumerate(self.scale_buttons.values()):
                # thing.grid(row=1+i, column=0, columnspan=2, sticky="ew")
                # thing.grid(row=2+i, column=1, columnspan=1, sticky="ew")
                thing.grid(row=2, column=1 + i, columnspan=1, sticky="ew")

            ttk.Label(butt_frame, text="\n").grid(row=4, column=0, sticky="ew")

            butt_frame_q = ttk.Frame(butt_frame, borderwidth=1, relief=tk.FLAT)

            ttk.Button(butt_frame_q, text=f"Apply", command=range_show).grid(row=0, column=0, columnspan=1, sticky="ew")
            ttk.Button(butt_frame_q, text="Reset", command=reset_lims).grid(row=0, column=1, columnspan=1, sticky="ew")

            butt_frame_q.grid(row=4, column=0, sticky="news")
            butt_frame_t.grid(row=3, column=0, sticky="news")
            butt_frame_s.grid(row=2, column=0, sticky="news")
            butt_frame_p.grid(row=1, column=0, sticky="news")

            return butt_frame

        def range_show():

            range_is_ok_bool = True

            range_str = range_list.get()
            range_str_list = range_str.split(sep=',')
            range_str_list_list = [x.split('-') for x in range_str_list]
            range_list_int = [[eval(x.strip(' ')) for x in pair] for pair in range_str_list_list]
            #self.parent.write_log(f"final range list {range_list_int}")

            for i in range(len(range_list_int) - 1):

                if len(range_list_int[i]) < 2:
                    #self.parent.write_log(f"note: single value")
                    continue
                # check if ranges overlap:    1-6, 4-8, 9-99
                elif range_list_int[i][1] >= range_list_int[i + 1][0]:
                    self.parent.write_log(f"Error: overlap, {range_list_int[i][1]} >= {range_list_int[i + 1][0]}")
                    range_is_ok_bool = False
                else:
                    self.parent.write_log(f"pass...")
                    pass
                    # self.parent.write_log(f"OK i={i}, {range_list_int[i][1]} < {range_list_int[i + 1][0]}")

            # check if any channels are invalid
            min_ch = 1
            max_ch = 4
            for i in range(len(range_list_int)):
                if len(range_list_int[i]) == 0:
                    range_is_ok_bool = False
                elif len(range_list_int[i]) < 2:
                    #self.parent.write_log(f"note single value")
                    if (range_list_int[i][0] < min_ch) or (range_list_int[i][0] > max_ch):
                        range_is_ok_bool = False
                elif range_list_int[i][0] >= range_list_int[i][1]:
                    self.parent.write_log(f"error: not increasing range")
                    range_is_ok_bool = False
                elif (range_list_int[i][0] < min_ch) or (range_list_int[i][1] > max_ch):
                    self.parent.write_log(f"error: channel in range is out of range")
                    range_is_ok_bool = False

            if range_is_ok_bool:  # if not errors!
                # self.parent.write_log(f"Range if good, ok to plot")

                # start by setting all to false
                for key in self.ch_show_lifetime.keys():
                    self.ch_show_lifetime[key] = False

                # set true for channels given in range
                for pair in range_list_int:
                    if len(pair) == 1:
                        self.ch_show_lifetime[f'h{pair[0]}'] = True
                    elif len(pair) == 2:
                        for idx in range(pair[0], pair[1] + 1):
                            self.ch_show_lifetime[f'h{idx}'] = True
                #self.parent.write_log(f"SHOW DICT: {self.ch_show_lifetime}")
                update_plot()

        def press_scale_plot():
            update_plot(plot_mode.get())

        def update_plot(scale=''):
            print("pressed update")
            if scale == '':
                scale = plot_mode.get()
            else:
                plot_mode.set(scale)

            fig.clear()
            ax1 = fig.add_subplot(111)
            plot_all = True  # FIXME note plotting too many value and trying to interact causes lag

            b = self.parent.eta_class.lifetime_bins_ns

            x = b  # [:-2]

            if x_min.get() >= x_max.get():
                x_min.set(x_max.get() - 1)  # note: to ensure the min < max

            if plot_all:
                idx_min = 0
                idx_max = -1
            else:
                # convert time to index??
                idx_min = int(1000 * x_min.get() / self.parent.eta_class.const['binsize'])
                idx_max = int(1000 * x_max.get() / self.parent.eta_class.const[
                    'binsize']) + 1  # note: round in case int would have rounded down

                if idx_min >= idx_max:
                    x_min.set(x_max.get() - 1)  # note: to ensure the min < max
                    idx_min = int(1000 * x_min.get() / self.parent.eta_class.const['binsize'])

            print(self.ch_show_lifetime.keys())
            for i, thing in enumerate(self.ch_show_lifetime.keys()):
                if self.ch_show_lifetime[thing] is False:
                    print(f"{thing} is hidden")
                    continue  # doesn't plot when hidden

                y = self.parent.eta_class.folded_countrate_pulses[thing]

                if scale == 'linear':
                    line_b, = ax1.plot(x[idx_min:idx_max], y[idx_min:idx_max],
                                       label=f'{lookup[thing]["nm"]} nm (ch.{lookup[thing]["ch"]})',
                                       #c=self.parent.eta_class.pix_dict[thing]["color"], alpha=0.8
                                        )
                elif scale == 'log':
                    line_b, = ax1.semilogy(x[idx_min:idx_max], y[idx_min:idx_max],
                                           label=f'{lookup[thing]["nm"]} nm (ch.{lookup[thing]["ch"]})',
                                           #label=f'{self.parent.eta_class.pix_dict[thing]["wavelength"]} (c{thing})',
                                           #c=self.parent.eta_class.pix_dict[thing]["color"], alpha=0.8
                                           )

                # elif scale == 'histo':
                #    N, bins, bars = ax1.hist(x[idx_min:idx_max], bins=b[idx_min:idx_max], weights=y[idx_min:idx_max], rwidth=1, align='left')

                ###plt.text(x[-1], y[-1], f'c{thing}')

            if scale == 'log':
                if y_min.get() == 0.0:
                    y_min.set(1.0)

            ax1.set_xlim([x_min.get(), x_max.get()])
            ax1.set_ylim([y_min.get(), y_max.get()])
            ax1.set_xlabel("time [ps]")
            ax1.set_ylabel("counts")
            ax1.set_title("Lifetime")

            ax1.legend()
            fig.canvas.draw_idle()  # updates the canvas immediately?

        self.ch_show_lifetime = {'h4': True, 'h2': True, 'h3': True}
        x_min = tk.DoubleVar(value=4000.0)   # time
        x_max = tk.DoubleVar(value=8500.0)
        y_min = tk.DoubleVar(value=0.0)      # counts
        y_max = tk.DoubleVar(value=20000.0)
        lookup = {
            'h2' : {
                'ch': '6',
                'nm' : ch6_nm},
            'h3' : {
                'ch': '7',
                'nm' : ch7_nm},
            'h4' : {
                'ch': '5',
                'nm' : ch5_nm},
        }
        range_list = tk.StringVar(value="2-4")
        plot_mode = tk.StringVar(value="linear")
        self.show_buttons = []

        fig = plt.figure(figsize=(8, 5), dpi=100)  # fig, ax1 = plt.subplots(1, 1, figsize=(8, 5))

        ax1 = fig.add_subplot(111)
        update_plot()  # TODO: check if we can use any of this
        reset_lims()
        plt_frame, canvas = gui.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()

        plt_frame.grid(row=2, column=1, columnspan=1, sticky="news")
        butt_frm.grid(row=2, column=2, columnspan=1, sticky="news")

    def plot_lifetime_colorbar_widget(self, tab):

        def reset_lims():
            x_min.set(0.0)
            x_max.set(self.parent.eta_class.lifetime_bins_ns[-1])

            y_min.set(0.0)
            max_count = [np.max(lst) for lst in self.parent.eta_class.folded_countrate_pulses.values()]

            if plot_mode.get() == 'linear':
                y_max.set(round(np.max(max_count)))
            else:
                y_max.set(round(np.log10(np.max(max_count)), 3))

            line_thickness.set(270.0)

            print("max list", max_count)

            update_plot()

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_t = ttk.Frame(butt_frame, borderwidth=1, relief=tk.FLAT)

            #ttk.Label(butt_frame_t, text=f'\nAxis ranges:').grid(row=0, column=1, columnspan=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            ttk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'time').grid(row=2, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=x_min, width=6).grid(row=2, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=x_max, width=6).grid(row=2, column=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'counts').grid(row=3, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=y_min, width=5).grid(row=3, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=y_max, width=5).grid(row=3, column=2, sticky="ew")

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            ttk.Label(butt_frame_s, text="\nDisplay \nchannels:").grid(row=2, column=1, columnspan=2, sticky="ew")
            ttk.Entry(butt_frame_s, textvariable=range_list, width=5).grid(row=3, column=1, columnspan=2, sticky="new")

            ttk.Label(butt_frame_s, text="\nLine \nthickness:").grid(row=2, column=3, columnspan=2, sticky="new")
            ttk.Entry(butt_frame_s, textvariable=line_thickness, width=5).grid(row=3, column=3, columnspan=2, sticky="new")

            butt_frame_p = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            #ttk.Label(butt_frame_p, text="\n  ").grid(row=0, column=0, sticky="ew")
            ttk.Label(butt_frame_p, text=f'\nScale:').grid(row=1, column=1, columnspan=1, sticky="ew")

            self.scale_buttons = {
                'linear':       ttk.Radiobutton(butt_frame_p, text="Linear", value='linear', variable=plot_mode, command=press_scale_plot),
                'log':          ttk.Radiobutton(butt_frame_p, text="Semi-Log", value='log', variable=plot_mode, command=press_scale_plot),
            }

            for i, thing in enumerate(self.scale_buttons.values()):
                #thing.grid(row=1+i, column=0, columnspan=2, sticky="ew")
                #thing.grid(row=2+i, column=1, columnspan=1, sticky="ew")
                thing.grid(row=2, column=1+i, columnspan=1, sticky="ew")

            ttk.Label(butt_frame, text="\n").grid(row=4, column=0, sticky="ew")

            butt_frame_q = ttk.Frame(butt_frame, borderwidth=1, relief=tk.FLAT)

            ttk.Button(butt_frame_q, text=f"Apply", command=range_show).grid(row=0, column=0, columnspan=1, sticky="ew")
            ttk.Button(butt_frame_q, text="Reset", command=reset_lims).grid(row=0, column=1, columnspan=1, sticky="ew")

            butt_frame_q.grid(row=4, column=0, sticky="news")
            butt_frame_t.grid(row=3, column=0, sticky="news")
            butt_frame_s.grid(row=2, column=0, sticky="news")
            butt_frame_p.grid(row=1, column=0, sticky="news")

            return butt_frame

        def range_show():
            range_is_ok_bool = True

            range_str = range_list.get()
            range_str_list = range_str.split(sep=',')
            range_str_list_list = [x.split('-') for x in range_str_list]
            range_list_int = [[eval(x.strip(' ')) for x in pair] for pair in range_str_list_list]
            #self.parent.write_log(f"final range list {range_list_int}")

            for i in range(len(range_list_int)-1):

                if len(range_list_int[i]) < 2:
                    self.parent.write_log(f"note single value")
                    continue
                # check if ranges overlap:    1-6, 4-8, 9-99
                elif range_list_int[i][1] >= range_list_int[i+1][0]:
                    self.parent.write_log(f"Error: overlap, {range_list_int[i][1]} >= {range_list_int[i + 1][0]}")
                    range_is_ok_bool = False
                else:
                    pass
                    #self.parent.write_log(f"OK i={i}, {range_list_int[i][1]} < {range_list_int[i + 1][0]}")

            # check if any channels are invalid
            min_ch = 2
            max_ch = 4
            for i in range(len(range_list_int)):
                if len(range_list_int[i]) == 0:
                    range_is_ok_bool = False
                elif len(range_list_int[i]) < 2:
                    self.parent.write_log(f"note single value")
                    if (range_list_int[i][0] < min_ch) or (range_list_int[i][0] > max_ch):
                        range_is_ok_bool = False
                elif range_list_int[i][0] >= range_list_int[i][1]:
                    self.parent.write_log(f"error: not increasing range")
                    range_is_ok_bool = False
                elif (range_list_int[i][0] < min_ch) or (range_list_int[i][1] > max_ch):
                    self.parent.write_log(f"error: channel in range is out of range")
                    range_is_ok_bool = False

            if range_is_ok_bool:  # if not errors!
                #self.parent.write_log(f"Range if good, ok to plot")

                # start by setting all to false
                for key in self.ch_show_lifetime.keys():
                    self.ch_show_lifetime[key] = False

                # set true for channels given in range
                for pair in range_list_int:
                    if len(pair) == 1:
                        self.ch_show_lifetime[f'h{pair[0]}'] = True
                    elif len(pair) == 2:
                        for idx in range(pair[0], pair[1]+1):
                            self.ch_show_lifetime[f'h{idx}'] = True
                #self.parent.write_log(f"SHOW DICT: {ch_show_lifetime.ch_show}")
                update_plot()

        def press_scale_plot():
            scale = plot_mode.get()
            if scale == 'linear' and prev_plot_mode.get() == 'log':
                mn = y_min.get()
                mx = y_max.get()
                y_min.set(round(10**mn, 3))
                y_max.set(round(10**mx, 3))
                #y_min.set(0)
                #y_max.set(1)

            elif scale == 'log' and prev_plot_mode.get() == 'linear':
                mn = max(1.0, y_min.get())
                mx = max(1.0, y_max.get())
                y_min.set(round(np.log10(mn), 3))
                y_max.set(round(np.log10(mx), 3))
                #y_min.set(0)
                #y_max.set(4)
                #pass

            prev_plot_mode.set(scale)

            for type in self.scale_buttons.keys():
                if type == scale:
                    c = 'green'
                else:
                    c = 'white'
                #self.scale_buttons[type].config(highlightbackground=c)

            update_plot(scale)

        def update_plot(scale=''):

            if scale == '':
                scale = plot_mode.get()
            else:
                plot_mode.set(scale)

            fig.clear()
            ax1 = fig.add_subplot(111)
            plot_all = False   # note plotting too many value and trying to interact causes lag

            b = self.parent.eta_class.lifetime_bins_ns
            x = b[:-2]

            if x_min.get() >= x_max.get():
                x_min.set(x_max.get() - 1)  # note: to ensure the min < max

            if plot_all:
                idx_min = 0
                idx_max = -1
            else:
                # convert time to index??
                idx_min = int(1000*x_min.get()/self.parent.eta_class.const['binsize'])
                idx_max = int(1000*x_max.get()/self.parent.eta_class.const['binsize'])+1   # note: round in case int would have rounded down

                if idx_min >= idx_max:
                    x_min.set(x_max.get() - 1)  # note: to ensure the min < max
                    idx_min = int(1000*x_min.get() / self.parent.eta_class.const['binsize'])
            # COLORS
            n_c = 256  # number of colors in gradient

            # --
            nr_shown_chs = 0
            all_lines = []
            #max_val = np.max([np.max(self.parent.eta_class.folded_countrate_pulses[c]) for c in self.ch_show_lifetime.keys()])

            for i, thing in enumerate(self.ch_show_lifetime.keys()):

                if self.ch_show_lifetime[thing] is False:
                    continue   # doesn't plot when hidden

                nr_shown_chs += 1
                time_vals = x[idx_min:idx_max]
                n = len(time_vals)  #idx_max - idx_min - 1  # nr of plotted points
                y_vals = list(np.ones(n)*nr_shown_chs)

                if scale == 'log':
                    mx = y_max.get()    # np.log10(y_max.get())
                    mn = y_min.get()    # np.log10(max(1.0, y_min.get()))
                    pre_counts = [max([1.0, c]) for c in self.parent.eta_class.folded_countrate_pulses[thing]+1]
                    counts = np.log10(pre_counts)
                    #if mx == mn:
                    #    mx = np.max(counts)
                    #y_max.set(mx)

                    # ABSOLUTE FILTER
                    """for l in range(len(counts)):
                        if counts[l] > y_max.get():
                            counts[l] = 0.0
                        elif counts[l] < y_min.get():
                            counts[l] = 0.0"""
                    # ----

                else:
                    #max_val = np.max([np.max(result[c]) for c in channels])
                    counts = self.parent.eta_class.folded_countrate_pulses[thing] # / max_val
                    mn = max(0.0, y_min.get())
                    mx = y_max.get()
                    #print("LIN POST", counts)


                # https://matplotlib.org/stable/gallery/lines_bars_and_markers/multicolored_line.html
                # Create a continuous norm to map from data points to colors
                norm = plt.Normalize(mn, mx) #counts.max())
                #norm_counts = [min((2*c)+1, 50) for c in counts]
                points = np.array([time_vals, y_vals]).T.reshape(-1, 1, 2)
                segments = np.concatenate([points[:-1], points[1:]], axis=1)
                lc = LineCollection(segments, cmap='plasma', norm=norm)  #, linewidths=norm_counts)
                # Set the values used for colormapping
                lc.set_array(counts[idx_min:idx_max])
                line = ax1.add_collection(lc)
                all_lines.append(lc)

            for lc in all_lines:
                lc.set_linewidth(line_thickness.get()/(len(all_lines)+1))

            fig.colorbar(line, ax=ax1)

            shown_ticks = []
            for key in self.ch_show_lifetime.keys():
                if self.ch_show_lifetime[key]:
                    shown_ticks.append(f'{lookup[key]["nm"]} nm\nch.{lookup[key]["ch"]}   ')

            ticks = [i + 1 for i in range(len(shown_ticks))]
            ax1.set_yticks(ticks)
            ax1.set_yticklabels(shown_ticks)  # note: this will be the amount of channels we are displaying
            #y_max.set(len(ticks)+1)

            ax1.set_xlim([x_min.get(), x_max.get()])
            ax1.set_ylim([0.0, len(shown_ticks)+1.0])  # not applicable here anymore, used to change range on colorbar
            ax1.set_xlabel("time [ps]")
            ax1.set_title("Lifetime Color")
            #ax1.legend()
            fig.canvas.draw_idle()   # updates the canvas immediately?

        self.ch_show_lifetime = {'h4': True, 'h2': True, 'h3': True}
        x_min = tk.DoubleVar(value=0.0)
        x_max = tk.DoubleVar(value=12500.0)
        y_min = tk.DoubleVar(value=0.0)
        y_max = tk.DoubleVar(value=100000.0)
        line_thickness = tk.DoubleVar(value=270.0)

        lookup = {
            'h2' : {
                'ch': '6',
                'nm' : ch6_nm},
            'h3' : {
                'ch': '7',
                'nm' : ch7_nm},
            'h4' : {
                'ch': '5',
                'nm' : ch5_nm},
        }

        range_list = tk.StringVar(value="2-4")
        plot_mode = tk.StringVar(value="linear")
        prev_plot_mode = tk.StringVar(value="linear")
        self.show_buttons = []

        fig = plt.figure(figsize=(8, 5), dpi=100)   # fig, ax1 = plt.subplots(1, 1, figsize=(8, 5))
        fig.subplots_adjust(left=0.1, right=1)

        update_plot()

        plt_frame, canvas = gui.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()

        plt_frame.grid(row=2, column=1, columnspan=1, sticky="news")
        butt_frm.grid(row=2, column=2, columnspan=1, sticky="news")

# GUI --> Approx 300 lines
class GUI:

    def __init__(self):
        # Create and configure the main GUI window
        #self.root = tk.Tk()

        self.sq = None

        self.CIE_colors = ColorMatchingCIE()   # self.CIE_colors.wavelengths[600]

        self.default_theme = 'breeze'  # 'radiance'
        self.root = ThemedTk(theme=self.default_theme)  # yaru is good I think

        self.root.title("OSQ - One Shot Quantum")   # *Ghosttly matters*
        self.root.geometry('1000x720')  # '1250x800')
        self.root.resizable(True, True)

        self.tabs = {
            'WebSQ' : {
                #'tab': None,
                #'notebook' : None,
                'children' : {},
                },

            'Calibration': {
                # 'tab': None,
                # 'notebook' : None,
                'children': {},
            },

            'Load'  : {
                #'tab': None,
                #'notebook' : None,
                'children' : {},
                },

            'New': {
                # 'tab': None,
                # 'notebook' : None,
                'children': {},
            },

            'Settings'  : {
                #'tab': None,
                #'notebook' : None,
                'children' : {},
                }
        }
        self.theme_list = [
            'adapta',
            'alt',
            'arc',  # not great, too pale
            'aqua',
            'aquativo',
            'black',
            'breeze',
            'blue',
            'clam',
            'classic',
            'clearlooks',
            'default',  # very box-y and old
            'elegance',
            'equilux', # nice grey/darkmode
            'itft1',
            'keramik',
            'kroc',
            'plastik',  # nice, light grey/blue but looks a bit old
            'radiance', # reminds me of linux, soft beige
            'scidgreen',
            'scidpink',
            'scidgrey',
            'scidblue',
            'scidmint',
            'scidpurple',  # white purple nice
            'scidsand',
            'smog',
            'ubuntu',
            'winxpblue',
            'yaru',  # nice and light, but buttons too big
        ]  # TODO: MOVE THESE TO A SEPARATE FILE THAT IS LOADED IN

    @staticmethod
    def pack_plot(tab, fig, use_toolbar=True):

        # FOR THE FIGURE
        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)
        canvas = FigureCanvasTkAgg(fig, master=plt_frame)  # self.root)
        canvas.draw()
        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        # FOR THE OPTIONAL TOOLBAR
        # creating the Matplotlib toolbar
        if use_toolbar:
            toolbar = NavigationToolbar2Tk(canvas, plt_frame)  # self.root)
            toolbar.update()
        # placing the toolbar on the Tkinter window
        canvas.get_tk_widget().pack()

        return plt_frame, canvas

    @staticmethod
    def add_tab(parent_nb, tab_name):
        child_tab = ttk.Frame(parent_nb, borderwidth=1, relief=tk.FLAT)   # TODO
        parent_nb.add(child_tab, text=tab_name)
        return child_tab

    @staticmethod
    def add_notebook(parent_tab, **kwargs):
        notebook = ttk.Notebook(parent_tab)
        notebook.pack(**kwargs)
        return notebook

    # CREATES AND BUILDS UP EMPTY TAB STRUCTURE
    def init_build_tabs(self):

        # Create root notebook
        self.root_nb = self.add_notebook(parent_tab=self.root, expand=1, fill="both", side='right')

        # Create parent tabs and pack into root notebook
        self.tabs['Calibration']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Calibration')
        self.tabs['Load']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Load Scan')
        self.tabs['New']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Create New Scan')
        self.tabs['Settings']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Settings')

        # -------
        # NOTE: don't know why we need to make load and new notebooks twice but it works :)
        load_nb = self.add_notebook(parent_tab=self.tabs['Load']['tab'], anchor='w', side='top')
        new_nb = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top')

        # --------
        # Create sub-notebooks for each tab and pack, then add children tabs
        for tabname in ['Calibration', 'Load', 'New', 'Settings']:
            self.tabs[tabname]['notebook'] = self.add_notebook(parent_tab=self.tabs[tabname]['tab'], anchor='w', side='top', fill='both', expand=1)
         #------
        # Create tabs within each tab notebook:

        # For Calibration tab
        for tabname in ['Wavelengths']:
            self.tabs['Calibration']['children'][tabname] = self.add_tab(parent_nb=self.tabs['Calibration']['notebook'], tab_name=tabname)

        # For Scan tabs
        for tabname in ['Countrate', 'Spectrum', 'Lifetime', 'Lifetime Color', 'Correlation']:
            self.tabs['Load']['children'][tabname] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name=tabname)
            self.tabs['New']['children'][tabname] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name=tabname)

        # For Settings tab
        for tabname in ['Appearance', 'Defaults', 'About']:
            self.tabs['Settings']['children'][tabname] = self.add_tab(parent_nb=self.tabs['Settings']['notebook'], tab_name=tabname)

        # Initializing tab contents:
        calibrationClass.init_wavelength_tab(self.tabs['Calibration']['children']['Wavelengths'])
        loadScanClass.acquisition_loadscan_tab(load_nb)   # adds in load params
        newScanClass.acquisition_newscan_tab(new_nb)
        self.build_appearance_settings(tab=self.tabs['Settings']['children']['Appearance'])

    # SETTINGS, e.g. theme
    def build_appearance_settings(self, tab):
        def change_theme(new_thm):
            print("changed to theme:", new_thm)
            self.root.set_theme(new_thm)
            thm_var.set(new_thm)

        conf_frm = ttk.Frame(tab)
        conf_frm.pack(expand=1, anchor='nw')  # 'ne' if in root_nb

        # THEME
        ttk.Label(conf_frm, text="Theme:").grid(row=0, column=0, sticky='news')
        thm_var = tk.StringVar(value=self.default_theme)
        option_thm = ttk.OptionMenu(conf_frm, variable=thm_var, default=self.default_theme)
        option_thm.grid(row=1, column=0)
        for theme in self.theme_list:
            option_thm['menu'].add_command(label=f"{theme}", command=lambda thm=theme: change_theme(thm))

    def add_new_plot_tab(self, parent_class, parent_name, tab_name, init=False):
        if init:
            print("init fill tabs, skipping creating new tab")
        elif tab_name in self.tabs[parent_name]['children'].keys():
            print("Plot already exists")
            return
        else:
            # not init and not already added: --> add new tab
            if tab_name == 'Spectrum':
                self.tabs[parent_name]['children']['Spectrum'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Spectrum')
            elif tab_name == 'Lifetime Color':
                self.tabs[parent_name]['children']['Lifetime Color'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Lifetime Color')
            elif tab_name == 'Lifetime':
                self.tabs[parent_name]['children']['Lifetime'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Lifetime')
            elif tab_name == 'Countrate':
                self.tabs[parent_name]['children']['Countrate'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Countrate')
            elif tab_name == 'Correlation':
                self.tabs[parent_name]['children']['Correlation'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Correlation')
            else:
                print(f"WARNING: ??? in function 'add_new_plot_tab()'")

        # ----

        if parent_name == 'Calibration':
            if tab_name == 'Wavelengths':
                print("PLOT NOT IMPLEMENTED")
                pass

            else:
                print(f'Calibration tab "{tab_name}" not found!')
            return

        elif tab_name == 'Spectrum':
            self.plot_spectrum_tab(self.tabs[parent_name]['children']['Spectrum'], parent_class)

        elif tab_name == 'Lifetime Color':
            self.plot_lifetime_color_tab(self.tabs[parent_name]['children']['Lifetime Color'], parent_class)

        elif tab_name == 'Lifetime':
            self.plot_lifetime_tab(self.tabs[parent_name]['children']['Lifetime'], parent_class)

        elif tab_name == 'Countrate':
            self.plot_countrate_tab(self.tabs[parent_name]['children']['Countrate'], parent_class)

        elif tab_name == 'Correlation':
            self.plot_correlation_tab(self.tabs[parent_name]['children']['Correlation'], parent_class)
        else:
            print(f"WARNING: Could not find plotting option for: {tab_name}")

    # **
    def plot_lifetime_tab(self, plots_lifetime, parent):
        parent.plotting_class.plot_lifetime_widget(plots_lifetime)

    def plot_lifetime_color_tab(self, plots_lifetime, parent):
        parent.plotting_class.plot_lifetime_colorbar_widget(plots_lifetime)

    # **
    def plot_spectrum_tab(self, plots_spectrum, parent):
        parent.plotting_class.plot_spectrum_widget(plots_spectrum)

    def plot_countrate_tab(self, plots_spectrum, parent):
        parent.plotting_class.plot_countrate_widget(plots_spectrum)

    # **
    def plot_correlation_tab(self, plots_correlation, parent):
        # TODO: add widgets
        #ttk.Label(plots_correlation, text='\nNOTHING TO SHOW YET. WORK IN PROGRESS...', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news")
        parent.plotting_class.plot_correlation_widget(plots_correlation)

    @staticmethod
    def add_to_grid(widg, rows, cols, sticky, columnspan=None):
        for i in range(len(widg)):
            if columnspan:
                # Note: not used atm
                print("NOTE: NOT ADDED TO GRID. FIXME")
                #widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], ipadx=5, columnspan=columnspan[i])
            else:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], ipadx=1, padx=1, pady=1)

    # -------

# Calibration --> Approx 100 lines
class Calibration:
    def __init__(self):
        self.livecounts_class = None

        self.nr_chs = tk.IntVar(value=24)
        self.web_url = tk.StringVar(value='ws://130.237.35.20')
        #self.channels = {i for i in range(1, self.nr_chs.get()+1)}
        self.wavelengths = {}

    def init_wavelength_tab(self, tab):
        frame = ttk.Frame(tab, borderwidth=3, relief=tk.FLAT)
        frame.grid(row=0, column=0, rowspan=15)

        # ------- CONNECT TO WEBSQ PARTS:
        sq_frame = ttk.Frame(frame, borderwidth=0.1, relief=tk.RAISED)
        sq_frame.grid(row=0, column=0, sticky="news", pady=5)

        url_label = ttk.Label(sq_frame, text='WebSQ URL', font="Helvetica 10 normal")
        url_entry = self.url_entry = ttk.Entry(sq_frame, textvariable=self.web_url, width=20)
        url_button = self.url_button = ttk.Button(sq_frame, text="Connect", command=self.press_connect_websq)

        url_label.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        url_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        # ------- CHANNEL PARTS: # note: entries are created after we connect to WebSQ
        self.wl_frame = ttk.Frame(frame, borderwidth=0.1, relief=tk.RAISED)
        self.wl_frame.grid(row=2, column=0, sticky='news', pady=5)

    def open_wavelength_calibration_file(self):
        file_name = askopenfilename(filetypes=[("Textfile", "*.txt")])

        if file_name:
            print("Config file found:", file_name)
            if file_name.endswith('.txt'):
                try:
                    with open(file_name, 'r') as f:
                        data = f.readlines()
                        f.close()

                    for entry in data:
                        ch, val = entry.strip("\n").split(" ")
                        self.wavelengths[eval(ch)].set(eval(val))
                    print(f"Loaded configs from file: {file_name}")

                except:
                    print("Error trying to read from config file")
                    for ch in self.wavelengths.keys():
                        self.wavelengths[eval(ch)].set(0)
                    raise

    def save_wavelength_calibration_file(self):
        file_name = asksaveasfilename(filetypes=[("Textfile", "*.txt")])
        if file_name:
            if file_name.endswith('.txt'):
                with open(file_name, 'w') as f:
                    f.writelines([f"{ch} {self.wavelengths[ch].get()}\n" for ch in self.wavelengths.keys()])
                    f.close()
                print(f"Saved configs to file: {file_name}")
        else:
            print("File NOT created")

    def press_connect_websq(self):
        # Try to connect and read off the counts from WebSQ:
        try:
            self.livecounts_class = LiveCounts(self.web_url.get())
            self.url_button.config(state='disabled')
            self.url_entry.config(state='readonly')
            self.nr_chs.set(self.livecounts_class.nr_chs)

            ttk.Label(self.wl_frame, text=f'Wavelength configs', font="Helvetica 10 normal italic").grid(row=0, column=0, columnspan=1, sticky='ew', padx=5, pady=5)
            ttk.Button(self.wl_frame, text="Load wavelengths", command=self.open_wavelength_calibration_file).grid(row=1, column=0, columnspan=1, sticky='ew', padx=5, pady=5)
            ttk.Button(self.wl_frame, text="Save wavelengths", command=self.save_wavelength_calibration_file).grid(row=2, column=0, columnspan=1, sticky='ew', padx=5, pady=5)

            ch_frame = ttk.Frame(self.wl_frame, borderwidth=0.1, relief=tk.RAISED)
            ch_frame.grid(row=0, column=3, rowspan=15, sticky='ew')

            offset = 0

            for ch in self.livecounts_class.ch_numbers:
                self.wavelengths[ch] = tk.DoubleVar(value=ch)
                if ch < 13:
                    row = offset
                    col = ch%(self.nr_chs.get()//2  +1)
                else:
                    row = offset + 2
                    col = ch%(self.nr_chs.get()//2 +1) +1
                ttk.Label(ch_frame, text=f'{ch}', font="Helvetica 10 normal").grid(row=row, column=col, columnspan=1, sticky='sw', padx=5, pady=1)
                ttk.Entry(ch_frame, textvariable=self.wavelengths[ch], width=5).grid(row=row+1, column=col, columnspan=1, sticky='nw', padx=5, pady=1)

        except:
            print("Error: Could not connect to WebSQ!")
            raise

# NewScanGroup --> Approx 400 lines
class NewScanGroup:
    def __init__(self):
        # class instances when connected
        self.eta_class = ETA(self, gui_class=gui)
        self.plotting_class = Plotting(self)

        # -----

        self.sq = None
        self.sp = None

        self.params = {
            'grating':     {'var': tk.IntVar(value=1),   'type': 'radio',     'default': 1,   'value': [1, 2, 3]},
            'nm':          {'var': tk.DoubleVar(value=ch6_nm), 'type': 'int entry', 'default': 532, 'value': [350, 650, 750]},
            'width_nm':    {'var': tk.DoubleVar(value=0.6),   'type': 'int entry', 'default': 5,  'value': [5, 15, 30]},
            'slit':        {'var': tk.IntVar(value=10),  'type': 'int entry', 'default': 10,  'value': [10, 20, 30]},
            'scantime':    {'var': tk.IntVar(value=5),   'type': 'int entry', 'default': 5,  'value': [1, 5, 10]},
            'nr_pixels':   {'var': tk.IntVar(value=12),   'type': 'int entry', 'default': 12,   'value': [8, 12, 24]},
            'file_name':   {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},
            'folder_name': {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['~/Desktop/GUI/Data1', '~/Desktop/GUI/Data2', '~/Desktop/GUI/Data3']},
            'eta_recipe':  {'var': tk.StringVar(value='3D_2_channels_tof_swabian_marker_ch4.eta'), 'type': 'str entry', 'default': '',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }
        self.data = []

        self.device_grating = 1
        self.device_wavelength = 600
        self.port = tk.StringVar(value="")     # note maybe change later when implemented

        self.demo_connect = False  # temp for demo to check if we've actually connected to device
        self.config_success = None   # None if not tried to configure yet
        self.checked_configs = False
        self.live_mode = True
        self.available_ports = {}
        self.port_list = []

        self.ok_to_send_list = []
        self.grating_lvl = {   # TODO: make this configurable?   # TODO fill in correct width (based on grating)
            1: {'grating': 600,  'blz': '750', 'width': 8},
            2: {'grating': 150,  'blz': '800', 'width': 4},
            3: {'grating': 1800, 'blz': 'H-VIS',  'width': 2},
        }
        self.ch_bias_list = {}
        self.ch_trig_list = {}
        self.pix_counts_list = {}

        #self.ch_nm_bin_edges = []  # TODO
        self.cumulative_ch_counts = []

    def acquisition_newscan_tab(self, new_scan_tab):

        # Full collection of settings for scan:
        self._params_frm = params_frm = ttk.Frame(new_scan_tab, borderwidth=1, relief=tk.FLAT)
        params_frm.grid(row=0, column=0, columnspan=2, sticky="nw")
        self.choose_param_configs_widget(params_frm).grid(row=0, column=0, sticky="ew")
        # ---
        # Frame to group together analysis configs (not including logger)
        scan_frm = ttk.Frame(new_scan_tab, borderwidth=1, relief=tk.FLAT)
        scan_frm.grid(row=1, column=0,  sticky='nw')  # nws

        # Analysis configs:
        self.analysis_config_widget(scan_frm).grid(row=1, column=0, sticky="news")

        # Row of start, stop buttons:
        self.start_scan_widget(scan_frm).grid(row=2, column=0, sticky="news")  # in sub frame

        # Analysis button:
        self.analysis_newscan_widget(scan_frm).grid(row=3, column=0, sticky="news")

        # ---
        # Logger box:
        log_box_frm = ttk.Frame(new_scan_tab, borderwidth=1, relief=tk.GROOVE)
        log_box_frm.grid(row=0, column=2, columnspan=10, rowspan=10, sticky="nws")  # in sub frame
        self.log_scan_widget(log_box_frm).grid(row=0, column=0, sticky="news")   # Inner thing

    # TODO: FIXME BELOW (make sure it connects and does right)
    def start_scan_widget(self, tab):

        def press_start():
            self.write_log(f"{self.sp.sp_handle}")
            self.write_log(f"{self.sq.websq_handle}")
            if (not self.sp.sp_handle) or (not self.sq.websq_handle):
                self.write_log(f"Can not start scan if we are not connected")
                return

            #self.save_data(mode="w")   # TODO: maybe only have this once per new measurement (so that we can pause and start again)
            # True:     if we have successfully configured the device
            # False:    failed to do all configs to device, should not start scan
            # None:     did not send new configs, will check but can start scan anyway (maybe??)
            outcome = {True : 'green', False : 'red', None : 'grey'}
            #self.mark_done(btn_start, highlight=outcome[self.config_success], type='button')
            #self.mark_done(btn_stop, highlight=self.button_color, type='button')

        frm_send = ttk.Frame(tab, relief=tk.FLAT, borderwidth=0)
        btn_start = ttk.Button(frm_send, text="Start Scan", command=press_start)

        btn_start.grid(row=0, column=0, sticky="nsew")

        return frm_send

    def choose_param_configs_widget(self, tab):

        def get_ports():  # TODO: find our device port and connect automatically
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
            self.available_ports = {}
            self.port_list = []
            for i, port in enumerate(serial.tools.list_ports.comports()):
                self.available_ports[i] = {
                    'device'          : port.device       ,   # !
                    'name'            : port.name         ,   # !
                    'description'     : port.description  ,   # !
                    'hwid'            : port.hwid         ,
                    'vid'             : port.vid          ,
                    'pid'             : port.pid          ,
                    'serial_number'   : port.serial_number,   # !
                    'location'        : port.location     ,
                    'manufacturer'    : port.manufacturer ,   # !
                    'product'         : port.product      ,
                    'interface'       : port.interface    ,
                }
                self.port_list.append(f'{port.name}') # (S/N:{port.serial_number})')

                #if (port.serial_number == self.acton_serial) and (port.manufacturer == 'FTDI'):
                #    # self.write_log(f"FOUND ACTON DEVICE ON PORT {port.device}")
                #    return port.device

                """self.write_log(f'---------\n'
                      f'device:          {port.device       }'
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

        def refresh_ports():
            self.port.set("Select...")
            port_parts['connect'].config(state='disabled')
            get_ports()

        def select_port(port):
            if port_parts['refresh']['state'] == 'disabled':
                self.write_log(f"Warning: Please disconnect from device before refreshing")
                return
            # Update chosen port and allow connection (if not connected^)

            self.port.set(port)
            port_parts['connect'].config(state='normal')

        # TODO:
        def press_connect():  # TODO
            if self.port.get() == "Select...":
                self.write_log(f"MUST SELECT PORT FIRST")

            self.write_log(f"connecting to port {self.port.get()}")

            # TODO CONNECTION....
            # if connect successful:
            port_parts['label'].config(text=f'Connected to {self.port.get()}')
            port_parts['refresh'].config(state='disabled')
            port_parts['connect'].config(text='Disconnect', command=press_disconnect)

            """if self.sp is None:
                self.init_sp()

            self.sp.acton_disconnect()
            self.sp.acton_connect()

            self.sp.sp_handle.write(b'NO-ECHO\r')
            self.sp.wait_for_read()  # b'  ok\r\n'
            port_parts['label'].config(text=f'{self.sp.port}')

            if self.sp.sp_handle.isOpen():
                gui.mark_done(port_parts['connect'], highlight="green", text_color='black', type='button')
            else:
                gui.mark_done(port_parts['connect'], highlight="red", text_color='black', type='button')"""

        # TODO:
        def press_disconnect():  # TODO
            self.write_log(f"pressed disconnect. fixme")
            self.write_log(f"disconnecting from port {self.port.get()}")

            # TODO DO DISCONNECT....

            # if successful:
            port_parts['label'].config(text='')
            #port_parts['connect'].config(state='normal')
            #port_parts['disconnect'].config(state='disabled')
            port_parts['refresh'].config(state='normal')
            port_parts['connect'].config(text='Connect', command=press_connect)


            """if self.sp is None:
                self.init_sp()
            self.sp.acton_disconnect()   # ????
            """

        # TODO
        def select_grating():
            # FIXME OR REMOVE
            # self.calculate_nm_bins()
            # TODO: auto update plot axis
            pass

        # FRAMES
        frm_configs = ttk.Frame(tab, relief=tk.FLAT)#, borderwidth=1)

        frm = {framename : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) for framename in ['port', 'slit', 'grating', 'detect']}

        # WIDGETS
        #  -- Slit:
        slt_parts = [ttk.Label(frm['slit'], text='Slit width (um)'), ttk.Entry(frm['slit'], textvariable=self.params['slit']['var'], width=4)]

        scanime_parts = [ttk.Label(frm['slit'], text='\nScantime (s)'), ttk.Entry(frm['slit'], textvariable=self.params['scantime']['var'], width=4)]

        #  -- Grating:
        grating_widget_dict = {
            'radio_b': [],
            'grt_txt': [ttk.Label(frm['grating'], text='Grating\n(gr/mm)')],
            'blz_txt': [ttk.Label(frm['grating'], text='Blaze\n(nm)')],
            'wid_txt': [ttk.Label(frm['grating'], text='Width')],
        }
        for c in range(3):
            grating_widget_dict['radio_b'].append(ttk.Radiobutton(frm['grating'], text="", variable=self.params['grating']['var'], value=c + 1, command=select_grating))
            grating_widget_dict['grt_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['grating']}"))
            grating_widget_dict['blz_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['blz']}"))
            grating_widget_dict['wid_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['width']}"))

        #  -- Detector:
        center_parts = [ttk.Label(frm['detect'], text="Center λ (nm)"), ttk.Entry(frm['detect'], textvariable=self.params['nm']['var'], width=4)]

        wid_parts = [ttk.Label(frm['detect'], text="Pixel width (nm)"), ttk.Entry(frm['detect'], textvariable=self.params['width_nm']['var'], width=4)]

        self.params['nr_pixels']['var'].set(24)
        det_no_parts = [ttk.Label(frm['detect'], text="Nr. of pixels"),
                        ttk.Radiobutton(frm['detect'], text="12", value=12, variable=self.params['nr_pixels']['var']),
                        ttk.Radiobutton(frm['detect'], text="24", value=24, variable=self.params['nr_pixels']['var']),
                        ]

        #  -- Port:
        get_ports()
        port_parts = { 'refresh'        : ttk.Button(frm['port'], text="Refresh", command=refresh_ports),
                       'option'         : ttk.OptionMenu(frm['port'], variable=self.port, default="Select..."),
                       'connect'        : ttk.Button(frm['port'], text="Connect", command=press_connect, state='disabled'),
                       'label'          : ttk.Label(frm['port'], text=f'', font="Helvetica 10 normal italic", anchor='center'),
                       }

        # Populate the dropdown menu with the list of options
        for port_name in self.port_list:
            port_parts['option']['menu'].add_command(label=f"{port_name}", command=lambda opt=port_name: select_port(opt))

        # GRID
        # -- Port
        port_parts['refresh'].grid(row=0, column=0, sticky='ew')
        port_parts['option'].grid(row=1, column=0, columnspan=2, sticky='ew')
        port_parts['connect'].grid(row=2, column=0, sticky='ew')
        #port_parts['disconnect'].grid(row=2, column=1, sticky='ew')
        port_parts['label'].grid(row=3, column=0, columnspan=2,  sticky='ew')
        #gui.add_to_grid(widg=list(port_parts.values()), rows=[0, 1, 2], cols=[0, 0, 0], sticky=["", "", ""])

        # -- Slit
        gui.add_to_grid(widg=slt_parts, rows=[0, 1], cols=[0, 0], sticky=["sew", "new"])
        gui.add_to_grid(widg=scanime_parts, rows=[2, 3], cols=[0, 0], sticky=["sew", "new"])

        # -- Grating
        gui.add_to_grid(widg=grating_widget_dict['radio_b'], rows=[3, 4, 5],    cols=[0, 0, 0],    sticky=["s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['grt_txt'], rows=[2, 3, 4, 5], cols=[1, 1, 1, 1], sticky=["", "s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['blz_txt'], rows=[2, 3, 4, 5], cols=[2, 2, 2, 2], sticky=["", "s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['wid_txt'], rows=[2, 3, 4, 5], cols=[3, 3, 3, 3], sticky=["", "s", "s", "s"])

        # -- Detector
        gui.add_to_grid(widg=[ttk.Label(frm['detect'], text="Detector")], rows=[0], cols=[0], sticky=["ew"])  # , columnspan=[2])

        gui.add_to_grid(widg=det_no_parts,  rows=[1, 2, 2, 2], cols=[0, 0, 1, 2], sticky=["ew", "ew", "ew", "ew"])  # nr of pixels
        gui.add_to_grid(widg=center_parts,  rows=[3, 4], cols=[0, 0], sticky=["ew", "ew"])  # center wavelength
        gui.add_to_grid(widg=wid_parts,     rows=[3, 4], cols=[1, 1], sticky=["ew", "ew"])


        # ------------- GRID FRAMES --------------
        # labels for each part:
        gui.add_to_grid(widg=[frm['port'], frm['grating'], frm['slit'], frm['detect']], cols=[1, 2, 3, 4], rows=[1]*4, sticky=["news"]*4)
        ttk.Label(frm_configs, text="Monochromator", relief=tk.GROOVE, anchor='center').grid(row=0, column=0, columnspan=4, sticky='ew')

        return frm_configs

    def analysis_config_widget(self, tab):

        def suggest_filename():
            currDate = date.today().strftime("%y%m%d")
            currTime = time.strftime("%Hh%Mm%Ss", time.localtime())
            temp = f"slit({self.params['slit']['var'].get()})_" \
                   f"grating({self.params['grating']['var'].get()})_" \
                   f"lamda({self.params['nm']['var'].get()})_" \
                   f"pixels({self.params['nr_pixels']['var'].get()})_" \
                   f"date({currDate})_time({currTime}).timeres"
            self.params['file_name']['var'].set(temp)

        frm_anal_configs = ttk.Frame(tab, borderwidth=0, relief=tk.FLAT)

        # choosing datafile and recipe entries:
        file_btn = ttk.Button(frm_anal_configs, text="Datafile  ", command=suggest_filename)
        file_entry = ttk.Entry(frm_anal_configs, textvariable=self.params['file_name']['var'], width=60)
        file_btn.grid(row=1, column=0, sticky="ew")
        file_entry.grid(row=1, column=1, columnspan=10, sticky="ew")

        return frm_anal_configs

    def analysis_newscan_widget(self, tab):

        def press_analyze():
            try:
                analyze_btn.config(state='disabled')
                self.write_log(f"Starting analysis")  # NOTE
                #self.eta_class.eta_lifetime_analysis()
                #self.eta_class.new_tof_analysis()
                # TODO FIXME ABOVE

                analyze_btn.config(state='normal')

                for tab_nm in gui.tabs['New']['children'].keys():
                    try:
                        gui.add_new_plot_tab(parent_class=self, parent_name='New', tab_name=tab_nm, init=True)
                    except:
                        print(f"ERROR: FAILED TO LOAD TAB '{tab_nm}'")
                        raise

                analyzed_file_label.config(text=f"Analyzed file: {self.params['file_name']['var'].get()}")

            except:
                self.write_log(f"Failed to analyze")
                raise

        frm_anal_buttons = ttk.Frame(tab, borderwidth=0, relief=tk.FLAT)
        # strt stop analysis buttons:
        analyze_btn = ttk.Button(frm_anal_buttons, text="Analyze", command=press_analyze)
        # shows which file we have analysed:
        analyzed_file_label = ttk.Label(frm_anal_buttons, text='', font="Helvetica 10 normal italic")
        analyze_btn.grid(row=3, column=0, sticky="ew")
        analyzed_file_label.grid(row=4, column=1, columnspan=10, sticky='ew')

        return frm_anal_buttons

    def log_scan_widget(self, tab):
        frm_log = ttk.Frame(tab, relief=tk.FLAT)
        self.log_box = log_box = scrolledtext.ScrolledText(frm_log, wrap=tk.WORD, width=50, height=12, font=('Helvetica', 12, "italic"), state='disabled')
        log_box.grid(row=0, column=0, pady=0, padx=0)

        return frm_log

    def write_log(self, msg):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', f'{msg}\n')
        self.log_box.configure(state='disabled')

# LoadScanGroup --> Approx 100 lines
class LoadScanGroup:
    def __init__(self):
        self.params = {
            'grating':     {'var': tk.IntVar(value=1),   'type': 'radio',     'default': 1,   'value': [1, 2, 3]},
            #'nm':          {'var': tk.IntVar(value=600), 'type': 'int entry', 'default': 350, 'value': [350, 650, 750]},
            #'width_nm':    {'var': tk.IntVar(value=10),   'type': 'int entry', 'default': 10,  'value': [5, 15, 30]},
            'nm': {'var': tk.DoubleVar(value=ch6_nm), 'type': 'int entry', 'default': 532, 'value': [350, 650, 750]},
            'width_nm': {'var': tk.DoubleVar(value=0.6), 'type': 'int entry', 'default': 5, 'value': [5, 15, 30]},
            'slit':        {'var': tk.IntVar(value=10),  'type': 'int entry', 'default': 10,  'value': [10, 20, 30]},
            'scantime': {'var': tk.DoubleVar(value=1), 'type': 'int entry', 'default': 1, 'value': [1, 5, 10]},
            'nr_pixels':   {'var': tk.IntVar(value=8),   'type': 'int entry', 'default': 8,   'value': [3, 8, 12]},
            'file_name':   {'var': tk.StringVar(value="Data/240614/Spectrometer_test_4s_(3ch_5_6_7)_240614.timeres"), 'type': 'str entry', 'default': '...',  'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},
            'eta_recipe':  {'var': tk.StringVar(value="3D_2_channels_tof_swabian_marker_ch4.eta"), 'type': 'str entry', 'default': '...',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
            'eta_recipe_correlation':  {'var': tk.StringVar(value="/Code/ETARecipes/Correlation-swabian_spectrometer.eta"), 'type': 'str entry', 'default': '...',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
            'eta_recipe_lifetime':  {'var': tk.StringVar(value="Code/ETARecipes/Countrate-swabian_spectrometer.eta"), 'type': 'str entry', 'default': '...',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
            'eta_recipe_spectrum':  {'var': tk.StringVar(value="Code/ETARecipes/Lifetime-swabian_spectrometer.eta"), 'type': 'str entry', 'default': '...',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }
        self.eta_class = ETA(self, gui_class=gui)
        self.plotting_class = Plotting(self)

    def acquisition_loadscan_tab(self, tab):

        def press_start():
            try:
                start_btn.config(state='disabled')
                self.write_log(f"Starting analysis")

                #self.eta_class.eta_lifetime_analysis()
                #self.eta_class.new_tof_analysis()
                #self.eta_class.new_correlation_analysis()

                start_btn.config(state='normal')

                scantime = self.params['scantime']['var'].get()
                self.eta_class.load_all_engines(scantime=scantime)
                self.eta_class.new_tof_analysis()

                # gui.add_plot_tabs(parent_class=self, parent_name='Load')
                for tab_nm in gui.tabs['Load']['children'].keys():
                    try:
                        gui.add_new_plot_tab(parent_class=self, parent_name='Load', tab_name=tab_nm, init=True)
                    except:
                        print(f"ERROR: FAILED TO LOAD TAB '{tab_nm}'")
                        raise

                analyzed_file_label.config(text=f"Analyzed file: {self.params['file_name']['var'].get()}")
                # ------
            except:
                self.write_log(f"Failed to analyze")
                raise

        def get_file():
            new_file = askopenfilename(filetypes=[("Timeres datafile", "*.timeres")])
            if new_file:
                self.params['file_name']['var'].set(new_file)

            frm_misc.children[list(frm_misc.children.keys())[-1]].destroy()

        frm_misc = ttk.Frame(tab, borderwidth=3, relief=tk.FLAT) #
        frm_misc.grid(row=1, column=0, rowspan=15)

        # shows which file we have analysed:
        analyzed_file_label = ttk.Label(frm_misc, text='', font="Helvetica 10 normal italic")
        analyzed_file_label.grid(row=4, column=1, columnspan=10, sticky='ew')
        # ----
        ttk.Button(frm_misc, text="Datafile", command=get_file).grid(row=1, column=0, sticky="ew")
        file_entry = ttk.Entry(frm_misc, textvariable=self.params['file_name']['var'], width=65)
        file_entry.grid(row=1, column=1, sticky="ew")

        start_btn = ttk.Button(frm_misc, text="Analyze", command=press_start)
        start_btn.grid(row=1, column=2, sticky="ew")

        # -----
        self.choose_params_widget(tab).grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    def choose_params_widget(self, tab):

        # FRAMES
        frm_configs = ttk.Frame(tab, relief=tk.FLAT)#, borderwidth=1)

        #  -- Detector:
        center_parts = [ttk.Label(frm_configs, text="Center λ (nm)"),
                        ttk.Entry(frm_configs, textvariable=self.params['nm']['var'], width=4)]

        wid_parts = [ttk.Label(frm_configs, text="Pixel width (nm)"),
                     ttk.Entry(frm_configs, textvariable=self.params['width_nm']['var'], width=4)]

        time_parts = [ttk.Label(frm_configs, text="Scan time (s)"),  # TODO USE!!! (only used in analysis now)
                     ttk.Entry(frm_configs, textvariable=self.params['scantime']['var'], width=4)]

        self.params['nr_pixels']['var'].set(4)

        # -- Detector
        gui.add_to_grid(widg=center_parts, rows=[1, 2], cols=[1, 1], sticky=["ew", "ew"])  # center wavelength
        gui.add_to_grid(widg=wid_parts, rows=[1, 2], cols=[2, 2], sticky=["ew", "ew"])
        gui.add_to_grid(widg=time_parts, rows=[1, 2], cols=[3, 3], sticky=["ew", "ew"])
        #gui.add_to_grid(widg=det_no_parts, rows=[1, 2, 3, 4], cols=[0, 0, 0, 0], sticky=["ew", "ew", "ew", "ew"])  # nr of pixels

        return frm_configs

    def write_log(self, msg, **kwargs):  # Note: we removed log from load scan tab, so we print instead
        print(msg)

# -------------

# TODO:
ch5_nm = 728.5
ch6_nm = 729.1
ch7_nm = 730.0

try:

    #sq = WebSQController(domain='http://130.237.35.62/')
    gui = GUI()
    newScanClass = NewScanGroup()
    loadScanClass = LoadScanGroup()
    calibrationClass = Calibration()
    gui.init_build_tabs()
    gui.root.mainloop()

except:
    print("some exception")
    raise

finally:
    print('------\nExiting...')

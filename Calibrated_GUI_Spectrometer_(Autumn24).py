# - PLATFORM IMPORTS
import os
import glob
import platform
from sys import platform as plat
import serial
from serial.tools import list_ports
from datetime import date
import json  # for eta?
import time  # for eta?
from pathlib import Path # for eta?

# - GUI IMPORTS
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory, asksaveasfilename
from ttkthemes import ThemedTk

# - SCIENTIFIC IMPORTS
import numpy as np
#import logging  ?

# - PLOTTING IMPORTS
import matplotlib   # JULIA NEW 2 sept
matplotlib.use("TkAgg")   # JULIA NEW 2 sept  # NOTE: import order matters
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import pyplot as plt
#import matplotlib.colors as mat_col
#import matplotlib.ticker as ticker
# from matplotlib import style
# from matplotlib.backend_bases import key_press_handler
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
import colour
from colour import Color

# - RETINA IMPORTS
# TODO: FIX
import websockets
#from Code.RetinaFiles.src.WebSQController import WebSQController
#from Code.RetinaFiles.src.WebSQSocketController import websocket_client

# - ETA backend IMPORTS
import etabackend.eta  # Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/

# - MISC IMPORTS???
import asyncio
import signal
import struct
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

# Grab and extend frames
# make whole notebook a scrollable frame (both horizontally and vertically)

# TODO:
#  With each measurement we should save a configuration file that can be used to load information about scan

# TODO:  (written: 16 june 2024)
#  break up GUI into several files which are called or used
#  look into SQL and especially API
#  consider making help functions more reusable and general
#  use more kwargs**
#  create configs file to save initialization procedure


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

# ----------

class ScrollFrame(ttk.Frame):
    # SOURCE: https://gist.github.com/mp035/9f2027c3ef9172264532fcd6262f3b01
    # ************************
    # Scrollable Frame Class
    # ************************
    # This Source Code Form is subject to the terms of the Mozilla Public
    # License, v. 2.0. If a copy of the MPL was not distributed with this
    # file, You can obtain one at https://mozilla.org/MPL/2.0/.

    def __init__(self, parent):
        super().__init__(parent)  # create a frame (self)

        #self.canvas = tk.Canvas(self, background="#ffffff", height=0, highlightthickness=0)  # place canvas on self
        self.canvas = tk.Canvas(self, height=10, highlightthickness=0, confine=True)  # place canvas on self
        self.viewPort = ttk.Frame(self.canvas, relief=tk.FLAT) #, borderwidth=1) #, background="#ffffff")  # place a frame on the canvas, this frame will hold the child widgets
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)  # place a scrollbar on self
        self.canvas.configure(yscrollcommand=self.vsb.set)  # attach scrollbar action to scroll of canvas

        self.vsb.pack(side="right", fill="y")  # pack scrollbar to right of self
        self.canvas.pack(side="left", fill="both", expand=True)  # pack canvas to left of self and expand to fil
        self.canvas_window = self.canvas.create_window((1, 1), window=self.viewPort, anchor="nw", tags="self.viewPort")  # add view port frame to canvas

        self.viewPort.bind("<Configure>", self.onFrameConfigure)  # bind an event whenever the size of the viewPort frame changes.
        self.canvas.bind("<Configure>", self.onCanvasConfigure)  # bind an event whenever the size of the canvas frame changes.
        self.viewPort.bind('<Enter>', self.onEnter)  # bind wheel events when the cursor enters the control
        self.viewPort.bind('<Leave>', self.onLeave)  # unbind wheel events when the cursorl leaves the control

        self.onFrameConfigure(None)  # perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))  # whenever the size of the frame changes, alter the scroll region respectively.

    def onCanvasConfigure(self, event):
        '''Reset the canvas window to encompass inner frame when required'''
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)  # whenever the size of the canvas changes alter the window region respectively.

    def onMouseWheel(self, event):  # cross platform scroll wheel event
        if platform.system() == 'Windows':
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == 'Darwin':
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def onEnter(self, event):  # bind wheel events when the cursor enters the control
        if platform.system() == 'Linux':  # TODO FIXME
            self.canvas.bind_all("<Button-4>", self.onMouseWheel)
            self.canvas.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':  # TODO FIXME
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")

class CreateScrollFrame(ttk.Frame):
    def __init__(self, root):
        ttk.Frame.__init__(self, root, borderwidth=1)
        self.scrollFrame = ScrollFrame(self)  # add a new scrollable frame.
        self.scrollFrame.grid(row=0, column=0, columnspan=1)

# --------------

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

    def create_color_gradient(self, start_hex='#000000', finish_hex='#ffffff', n=10):
        # SOURCE: https://bsouthga.dev/posts/color-gradients-with-python

        def hex_to_RGB(hex):
            ''' "#FFFFFF" -> [255,255,255] '''
            # Pass 16 to the integer function for change of base
            return [int(hex[i:i + 2], 16) for i in range(1, 6, 2)]

        def RGB_to_hex(RGB):
            ''' [255,255,255] -> "#FFFFFF" '''
            # Components need to be integers for hex to make sense
            RGB = [int(x) for x in RGB]
            return "#" + "".join(["0{0:x}".format(v) if v < 16 else
                                  "{0:x}".format(v) for v in RGB])

        def color_dict(gradient):
            ''' Takes in a list of RGB sub-lists and returns dictionary of
              colors in RGB and hex form for use in a graphing function
              defined later on '''
            return {"hex": [RGB_to_hex(RGB) for RGB in gradient],
                    "r": [RGB[0] for RGB in gradient],
                    "g": [RGB[1] for RGB in gradient],
                    "b": [RGB[2] for RGB in gradient]}

        ''' returns a gradient list of (n) colors between
          two hex colors. start_hex and finish_hex
          should be the full six-digit color string,
          inlcuding the number sign ("#FFFFFF") '''
        # Starting and ending colors in RGB form
        s = hex_to_RGB(start_hex)
        f = hex_to_RGB(finish_hex)
        # Initilize a list of the output colors with the starting color
        RGB_list = [s]
        # Calcuate a color at each evenly spaced value of t from 1 to n
        for t in range(1, n):
            # Interpolate RGB vector for color at the current value of t
            curr_vector = [ int(s[j] + (float(t) / (n - 1)) * (f[j] - s[j])) for j in range(3) ]
            # Add it to our list of output colors
            RGB_list.append(curr_vector)

        return color_dict(RGB_list)

    def colored_lines(self):
        pass
        """points = np.array([x_vals, counts]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        # Create a continuous norm to map from data points to colors
        norm = plt.Normalize(counts.min(), counts.max())
        lc = LineCollection(segments, cmap='viridis', norm=norm)
        # Set the values used for colormapping
        lc.set_array(counts)
        lc.set_linewidth(2)
        line = axs[0].add_collection(lc)
        fig.colorbar(line, ax=axs[0])"""

    def plot_spectrum_widget(self, tab):
        # TODO: make it live? live graph???

        def convert_values():
            unit = self.x_label.get()

            if unit == "λ [nm]":
                x = [value for value in x_bins]

            elif unit == "f [Hz]":
                c = 2.99792458e9
                x = [c/(value*1e-9) for value in x_bins]

            elif unit == "E [eV]":
                x = [1240/value for value in x_bins]

            elif unit == "v [1/cm]":
                x = [1/(value_nm*1e-7) for value_nm in x_bins]

            else:
                self.parent.write_log(f"ERROR NOT FOUND")
                x = []

            return x

        def pressed_xlabel():  # TODO: add data conversion for respective unit
            fig.clear()
            x_bins = convert_values()
            plot_spec(x_bins)

        def plot_spec(x_bins):
            plot1 = fig.add_subplot(111)

            x_centers = [(x_bins[i - 1] + x_bins[i]) / 2 for i in range(1, len(x_bins))]
            #plt.hist()
            #print("x bins:", x_bins)
            #print("centers:", x_centers)

            # N, bins, bars = plot1.hist(x=x_bins[:-2], bins=x_bins[:-1], weights=y_counts[:-1], rwidth=0.7, align='left')
            N, bins, bars = plot1.hist(x=x_bins[:-1], bins=x_bins, weights=y_counts,
                                       rwidth=1, align='mid',
                                       edgecolor='white', linewidth=1
                                       , label=ch_labels)  # TODO ASSIGN A CHANNEL A UNIVERSAL COLOR

            labels = []
            for b, bar in enumerate(bars):
                #bar.set_facecolor(self.parent.eta_class.pix_dict[f'h{b+1}']['color'])  # FIXME: does not work if we hide and only show some channels, must map
                labels.append(f'ch.{b+1}')  # FIXME by mapping to channel

            #print(bins, bars, N)
            ticks_list = sorted(list(x_centers)+list(bins))
            plot1.set_title("Spectrum")
            plot1.set_xlabel(self.x_label.get())
            plot1.set_ylabel("counts")
            #plot1.set_xlim([x_bins[0] - 2, x_bins[-1] + 2])
            plot1.set_xlim([725.9, 733.6])
            #plot1.set_xticks(ticks=ticks_list)
            #fig.axes[0].set_xticklabels(x_centers)
            plot1.bar_label(bars, labels=labels)  # , fontsize=20, color='navy')

            canvas.draw()

        def get_bins():
            #nr_pix = self.parent.params['nr_pixels']['var'].get()
            nr_pix = 12  # len(self.parent.eta_class.folded_countrate_pulses.keys())   # TODO FIXME: what happens if we define more channels than we have data on?
            pixel_width = self.parent.params['width_nm']['var'].get()   # TODO: maybe make this different depending on which
            center_pix = self.parent.params['nm']['var'].get()

            left_pix_bound = center_pix - (nr_pix * pixel_width / 2)
            right_pix_bound = center_pix + (nr_pix * pixel_width / 2)

            bins = np.linspace(start=left_pix_bound, stop=right_pix_bound, num=nr_pix+1, endpoint=True)  # , dtype=)

            #ch5_nm = 728.5
            #ch6_nm = 729.1
            #ch7_nm = 730.0

            #bins = [726.1, 726.7, 727.3, 727.9, 728.5, 729.1,
            #        729.7, 730.3, 730.9, 731.5, 732.1, 732.7, 733.8]
            # TODO ADD LIST OF ACTUAL WAVELENGTHS

            bins = [726.1, 726.7, 727.3, 727.9, 728.5, 729.1,
                    729.7, 730.3, 730.9, 731.5, 732.1, 732.7, 733.3]
            #print("bins len:", len(bins), bins)
            return bins

        def get_counts():
            ch_labs = []  # bin centers   #TODO: use as extra label for x axis
            y_cnts = []  # total counts per bin

            # TODO FIX HARDCODE ABOVE TO BE NUMBER OF CHANNELS
            #print(self.parent.eta_class.folded_countrate_pulses.keys())
            for i, channel in enumerate(self.parent.eta_class.folded_countrate_pulses.keys()):
                print("CHANNNEEEL", channel)
                ch_labs.append(channel)  # TODO USE CHANNEL NUMBER TO GET WAVELENGTH
                #print(self.parent.eta_class.folded_countrate_pulses[channel])
                y_cnts.append(sum(self.parent.eta_class.folded_countrate_pulses[channel]))  # TODO CHECK THAAT THIS IS CORRECT

            #y_cnts[0] += y_cnts[1] / 2  # note temp change to test  # REMOVE LATER!
            #y_cnts[3] += y_cnts[1] / 2  # note temp change to test  # REMOVE LATER!

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
        #return plt_frame, butt_frame

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
        #return plt_frame

    def plot_countrate_widget(self, tab):

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            butt_frame_t = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)

            ttk.Label(butt_frame_s, text="\nDisplay channels:").grid(row=2, column=1, columnspan=2, sticky="ew")
            # TODO ADD CHECK BOXES

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
        #return plt_frame

    def plot_visible_spectra_widget(self, tab, simple=False):
        #self.spectral_fig_dict = {}
        fig = plt.figure(figsize=(8, 1))  # 10 3

        #plot1 = fig.add_subplot(111)
        if not simple:
            wavelengths = gui.CIE_colors.wavelengths
        else:
            wavelengths = gui.CIE_colors.wavelengths_simple

        for key in wavelengths.keys():
            col = wavelengths[key]
            plt.plot([key, key], [0, 1], c=col)

        #plt.axes.yaxis().set_visible(False)
        plt.xlabel("Wavelength")
        plt.axis("off")

        # Fetching values and applying
        lam_wid = self.parent.params['width_nm']['var'].get()
        lam_mid = self.parent.params['nm']['var'].get()

        lam_lo = lam_mid-lam_wid
        lam_hi = lam_mid+lam_wid

        plt.plot([lam_lo, lam_lo], [0, 1], 'k--')
        plt.plot([lam_hi, lam_hi], [0, 1], 'k--')
        plt.plot([lam_mid, lam_mid], [0, 1], 'k-')
        plt.annotate(f"{lam_lo}", [lam_lo-10, 1.03])
        plt.annotate(f"{lam_hi}", [lam_hi-10, 1.03])
        plt.annotate(f"{lam_mid}", [lam_mid-10, -0.06])

        # NOTE TODO: FIXXXXXX
        #lo_txt.set_text("hi")
        #lo_txt.set_position((450, 450))

        plt_frame, canvas = gui.pack_plot(tab, fig, use_toolbar=False)

        return plt_frame

    def plot_lifetime_widget(self, tab):

        def reset_xlims():
            time_min.set(0.0)
            time_max.set(self.parent.eta_class.lifetime_bins_ns[-1])
            update_plot()

        def reset_ylims():
            cnt_min.set(0.0)
            max_count = [np.max(lst) for lst in self.parent.eta_class.folded_countrate_pulses.values()]
            cnt_max.set(round(1.05 * np.max(max_count)))
            update_plot()

        def reset_lims():
            time_min.set(0.0)
            time_max.set(self.parent.eta_class.lifetime_bins_ns[-1])
            cnt_min.set(0.0)
            max_count = [np.max(lst) for lst in self.parent.eta_class.folded_countrate_pulses.values()]
            print("max list", max_count)
            cnt_max.set(round(1.05 * np.max(max_count)))
            update_plot()

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_t = ttk.Frame(butt_frame, borderwidth=1, relief=tk.FLAT)

            # ttk.Label(butt_frame_t, text=f'\nAxis ranges:').grid(row=0, column=1, columnspan=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            ttk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'time').grid(row=2, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew")
            ttk.Label(butt_frame_t, text=f'counts').grid(row=3, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_min, width=5).grid(row=3, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_max, width=5).grid(row=3, column=2, sticky="ew")

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            ttk.Label(butt_frame_s, text="\nDisplay channels:").grid(row=2, column=1, columnspan=2, sticky="ew")
            ttk.Entry(butt_frame_s, textvariable=range_list, width=5).grid(row=3, column=1, columnspan=2, sticky="new")

            # ttk.Label(butt_frame_s, text="\nLine thickness:").grid(row=2, column=3, columnspan=2, sticky="new")
            # ttk.Entry(butt_frame_s, textvariable=line_thickness, width=5).grid(row=3, column=3, columnspan=2, sticky="new")

            butt_frame_p = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            # ttk.Label(butt_frame_p, text="\n  ").grid(row=0, column=0, sticky="ew")
            ttk.Label(butt_frame_p, text=f'\nScale:').grid(row=1, column=1, columnspan=1, sticky="ew")

            self.scale_buttons = {
                # 'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                # 'linear':       ttk.Button(butt_frame_p, text="  Linear  ", command=lambda: press_scale_plot('linear')),
                # 'log':          ttk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
                'linear': ttk.Radiobutton(butt_frame_p, text="Linear", value='linear', variable=plot_mode,
                                          command=press_scale_plot),
                'log': ttk.Radiobutton(butt_frame_p, text="Semi-Log", value='log', variable=plot_mode,
                                       command=press_scale_plot),
                # ttk.Radiobutton(frm['grating'], text="", variable=self.params['grating']['var'], value=c + 1, command=select_grating)
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

        def old_make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_t = ttk.Frame(butt_frame, borderwidth=1)

            ttk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            ttk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")

            ttk.Label(butt_frame_t, text=f'X').grid(row=2, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew")
            # ttk.Button(butt_frame_t, text="reset", width=2, command=reset_xlims).grid(row=2, column=3, columnspan=1, sticky="ew")

            ttk.Label(butt_frame_t, text=f'Y').grid(row=3, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_min, width=6).grid(row=3, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_max, width=6).grid(row=3, column=2, sticky="ew")
            # ttk.Button(butt_frame_t, text="reset", width=2, command=reset_ylims).grid(row=3, column=3, columnspan=1, sticky="ew")

            ttk.Button(butt_frame_t, text="Apply", command=update_plot).grid(row=4, column=0, columnspan=2, sticky="ew")
            ttk.Button(butt_frame_t, text="Reset", command=reset_lims).grid(row=4, column=2, columnspan=1, sticky="ew")

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)

            ttk.Label(butt_frame_s, text="Show Channels:").grid(row=2, column=0, columnspan=2, sticky="ew")
            ttk.Entry(butt_frame_s, textvariable=range_list, width=6).grid(row=3, column=0, columnspan=1, sticky="ew")
            ttk.Button(butt_frame_s, text=f"Update range", command=range_show).grid(row=4, column=0, columnspan=1,
                                                                                    sticky="ew")

            butt_frame_p = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            ttk.Label(butt_frame_p, text=f'Plot scale').grid(row=0, column=0, columnspan=2, sticky="ew")
            self.scale_buttons = {
                # 'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                'linear': ttk.Button(butt_frame_p, text="  Linear  ", command=lambda: press_scale_plot('linear')),
                # 'histo':      ttk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                'log': ttk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
            }

            for i, thing in enumerate(self.scale_buttons.values()):
                # thing.grid(row=1+i, column=0, columnspan=2, sticky="ew")
                thing.grid(row=1 + i, column=0, columnspan=1, sticky="ew")

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

        def press_scale_plot(scale=None):
            scale = plot_mode.get()

            """for type in self.scale_buttons.keys():
                if type == scale:
                    c = 'green'
                else:
                    c = 'white'
                #self.scale_buttons[type].config(highlightbackground=c)"""

            update_plot(scale)

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

            if time_min.get() >= time_max.get():
                time_min.set(time_max.get() - 1)  # note: to ensure the min < max

            if plot_all:
                idx_min = 0
                idx_max = -1
            else:
                # convert time to index??
                idx_min = int(1000 * time_min.get() / self.parent.eta_class.const['binsize'])
                idx_max = int(1000 * time_max.get() / self.parent.eta_class.const[
                    'binsize']) + 1  # note: round in case int would have rounded down

                if idx_min >= idx_max:
                    time_min.set(time_max.get() - 1)  # note: to ensure the min < max
                    idx_min = int(1000 * time_min.get() / self.parent.eta_class.const['binsize'])

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
                if cnt_min.get() == 0.0:
                    cnt_min.set(1.0)

            ax1.set_xlim([time_min.get(), time_max.get()])
            ax1.set_ylim([cnt_min.get(), cnt_max.get()])
            ax1.set_xlabel("time [ps]")
            ax1.set_ylabel("counts")
            ax1.set_title("Lifetime")

            ax1.legend()
            fig.canvas.draw_idle()  # updates the canvas immediately?

            """ 
                channels = ['h2', 'h3', 'h4']

                ax.set_title("Lifetime")

                ax.plot(time_axis, result['h2'], label='ch5')
                ax.plot(time_axis, result['h3'], label='ch6')
                ax.plot(time_axis, result['h4'], label='ch7')
                ax.legend()
                ax.set_xlabel("time [ps]")
            """

        # self.ch_show_corr = {'h2': True, 'h3': True, 'h4': True}
        self.ch_show_lifetime = {'h4': True, 'h2': True, 'h3': True}
        # self.ch_show = {'h2': True, 'h3': True, 'h4': True}
        time_min = tk.DoubleVar(value=4000.0)
        time_max = tk.DoubleVar(value=8500.0)
        cnt_min = tk.DoubleVar(value=0.0)
        cnt_max = tk.DoubleVar(value=20000.0)
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
        # return plt_frame, butt_frm

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
                #'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                #'linear':       ttk.Button(butt_frame_p, text="  Linear  ", command=lambda: press_scale_plot('linear')),
                #'log':          ttk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
                'linear':       ttk.Radiobutton(butt_frame_p, text="Linear", value='linear', variable=plot_mode, command=press_scale_plot),
                'log':          ttk.Radiobutton(butt_frame_p, text="Semi-Log", value='log', variable=plot_mode, command=press_scale_plot),
                #ttk.Radiobutton(frm['grating'], text="", variable=self.params['grating']['var'], value=c + 1, command=select_grating)
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
            #color_list = list(Color("green").range_to(Color("yellow"), n_c))
            color_list = self.create_color_gradient(start_hex='#000000', finish_hex='#ffffff', n=n_c)
            #print(color_list)

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

                # COLORS
                #counts = n_c*self.parent.eta_class.folded_countrate_pulses[thing]/(max(self.parent.eta_class.folded_countrate_pulses[thing])+1)
                #print(counts)
                #color_vals = [color_list['hex'][int(c)] for c in counts]
                # --

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
        #return plt_frame, butt_frm

    def plot_3D_lifetime_widget(self, tab):

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_t = ttk.Frame(butt_frame, borderwidth=1)

            ttk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            ttk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")

            ttk.Label(butt_frame_t, text=f'X').grid(row=2, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew")

            ttk.Label(butt_frame_t, text=f'Y').grid(row=3, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_min, width=6).grid(row=3, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_max, width=6).grid(row=3, column=2, sticky="ew")

            ttk.Button(butt_frame_t, text="Update", command=update_plot).grid(row=4, column=0, columnspan=3, sticky="ew")

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)

            ttk.Label(butt_frame_s, text="Show Channels:").grid(row=2, column=0, columnspan=2, sticky="ew")
            ttk.Entry(butt_frame_s, textvariable=range_list, width=6).grid(row=3, column=0, columnspan=1, sticky="ew")
            ttk.Button(butt_frame_s, text=f"Update range", command=range_show).grid(row=4, column=0, columnspan=1, sticky="ew")

            butt_frame_p = ttk.Frame(butt_frame, relief=tk.FLAT, borderwidth=1)
            ttk.Label(butt_frame_p, text=f'Plot scale').grid(row=0, column=0, columnspan=2, sticky="ew")
            self.scale_buttons_3D = {
                #'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                'linear':       ttk.Button(butt_frame_p, text="  Linear  ", command=lambda: press_scale_plot('linear')),
                #'histo':        ttk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                #'log':          ttk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
            }

            for i, thing in enumerate(self.scale_buttons_3D.values()):
                #thing.grid(row=1+i, column=0, columnspan=2, sticky="ew")
                thing.grid(row=1, column=i, columnspan=1, sticky="ew")

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
            #self.parent.write_log(f"final range list: {range_list_int}")

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
            min_ch = 1
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
                #self.parent.write_log(f"Range is good, ok to plot")

                # start by setting all to false
                for key in self.ch_show_3D.keys():
                    self.ch_show_3D[key] = False

                # set true for channels given in range
                for pair in range_list_int:
                    if len(pair) == 1:
                        self.ch_show_3D[f'h{pair[0]}'] = True
                    elif len(pair) == 2:
                        for idx in range(pair[0], pair[1]+1):
                            self.ch_show_3D[f'h{idx}'] = True
                self.parent.write_log(f"SHOW DICT: {self.ch_show_3D}")
                update_plot()

        def press_scale_plot(scale):
            for type in self.scale_buttons_3D.keys():
                if type == scale:
                    c = 'green'
                else:
                    c = 'white'
                self.scale_buttons_3D[type].config(highlightbackground=c)
            update_plot(scale)

        def update_plot(scale=''):

            if scale == '':
                scale = plot_mode.get()
            else:
                plot_mode.set(scale)

            if time_min.get() >= time_max.get():
                time_min.set(time_max.get() - 1)  # note: to ensure the min < max

            plot_all = False   # note plotting too many value and trying to interact causes lag

            if plot_all:
                idx_min = 0
                idx_max = -1
            else:
                # convert time to index??
                idx_min = int(1000*time_min.get()/self.parent.eta_class.const['binsize'])
                idx_max = int(1000*time_max.get()/self.parent.eta_class.const['binsize'])+1   # note: round in case int would have rounded down

                if idx_min >= idx_max:
                    time_min.set(time_max.get() - 1)  # note: to ensure the min < max
                    idx_min = int(1000*time_min.get() / self.parent.eta_class.const['binsize'])

            fig.clear()
            ax1 = fig.add_subplot(111, projection='3d')

            ax1.set_xlabel("time [ps]")
            ax1.set_zlabel("counts")
            ax1.set_title("Spectrum")

            b = self.parent.eta_class.lifetime_bins_ns
            x = b[:-2]

            X = x[idx_min:idx_max]  # note: dividing to get in nanoseconds
            N = len(X)  # number of data points per lifetime line   # FIXME to equal how many bins we have
            nr_ch = len(self.ch_show_3D.keys())
            Y = np.ones(N) * int(N / nr_ch)

            for i, ch in enumerate(self.ch_show_3D.keys()):
                if self.ch_show_3D[ch] is False:
                    continue   # doesn't plot when hidden

                Z = self.parent.eta_class.folded_countrate_pulses[ch][idx_min:idx_max]
                #y = self.parent.eta_class.folded_countrate_pulses[ch]

                if scale == 'log':

                    """for z_idx, z in enumerate(Z):
                        if z >= 1:
                            Z[z_idx] = np.log(z)
                        else:
                            Z[z_idx] = 0.0"""
                    pass

                    #Z = np.where(Z > 1.0, np.log(Z), 0.0)
                    #print(Z)
                    #ax1.zaxis.set_scale('log')

                ax1.plot(X, Y * i, Z, label='c' + ch)  # ax1.plot3D(X, Y, Z)

            if scale == 'log':
                if cnt_min.get() == 0.0:
                    cnt_min.set(1.0)

            ax1.set_yticks([int(N / nr_ch) * i for i in range(nr_ch)])
            ax1.set_yticklabels([f'ch.{j[1:]}' for j in self.ch_show_3D.keys()])  # note: this will be the amount of channels we are displaying

            ax1.set_xlim([time_min.get(), time_max.get()])
            ax1.set_zlim([cnt_min.get(), cnt_max.get()])
            ax1.set_xlabel("lifetime [ps]")
            ax1.set_title("3D Lifetime")
            #ax1.legend()
            fig.canvas.draw_idle()   # updates the canvas immediately?

        self.ch_show_3D = {'h2': True, 'h3': True, 'h4': True}
        time_min = tk.DoubleVar(value=54.0)
        time_max = tk.DoubleVar(value=59.0)
        cnt_min = tk.DoubleVar(value=0.0)
        cnt_max = tk.DoubleVar(value=6000.0)

        range_list = tk.StringVar(value="2, 3")
        plot_mode = tk.StringVar(value="linear")
        self.show_buttons = []

        # ---

        #fig, ax1 = plt.subplots(1, 1, figsize=(8, 5), subplot_kw={'projection': '3d'})
        fig = plt.figure(figsize=(8, 5), dpi=100)   # fig, ax1 = plt.subplots(1, 1, figsize=(8, 5))
        #ax1 = fig.add_subplot(111, projection='3d')

        update_plot()

        plt_frame, canvas = gui.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()
        plt_frame.grid(row=2, column=1, columnspan=1, sticky="news")
        butt_frm.grid(row=2, column=2, columnspan=1, sticky="news")

        return plt_frame

    def plot_display_info_widget(self, tab, tab_str):

        frm_info = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

        # TODO: add text or variables depending on which graph tab we have
        if tab_str == "tab 1 plots":
            pass

        elif tab_str == "tab 2 plots":
            pass
        elif tab_str == "tab 3 plots":
            pass

        elif tab_str == "tab all plots":
            pass

        ttk.Label(frm_info, text=f'{tab_str}').grid(row=0, column=0, sticky="nsew")
        ttk.Label(frm_info, text=f'info').grid(row=1, column=0, sticky="nsew")
        ttk.Label(frm_info, text=f'info').grid(row=2, column=0, sticky="nsew")
        ttk.Label(frm_info, text=f'info').grid(row=3, column=0, sticky="nsew")
        ttk.Label(frm_info, text=f'info').grid(row=4, column=0, sticky="nsew")

        ttk.Label(frm_info, text=f'  ').grid(row=0, column=1, sticky="nsew")
        ttk.Label(frm_info, text=f'...').grid(row=1, column=1, sticky="nsew")
        ttk.Label(frm_info, text=f'...').grid(row=2, column=1, sticky="nsew")
        ttk.Label(frm_info, text=f'...').grid(row=3, column=1, sticky="nsew")
        ttk.Label(frm_info, text=f'...').grid(row=4, column=1, sticky="nsew")

        return frm_info


class LivePlotting:   # A LOT TAKEN FROM SEPARATE SCRIPT
    def __init__(self):

        self.nr_chs = 24  # variable we should change later i think
        self.active_channels = {i : True for i in range(1, self.nr_chs+1)}  # [True for _ in range(self.nr_chs)]
        self.active_chs = [True for _ in range(self.nr_chs)]
        self.reset_vars()

    def reset_vars(self):
        self.case = 'calibrate'
        self.cnter = 0
        self.max_val = 0
        self.norm_counter = 0
        self.n = 10
        self.ch_list = range(1, self.nr_chs+1)
        self.curr_t = {k: 0 for k in self.ch_list}
        self.counts = {k: 0 for k in self.ch_list}                # {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0}
        self.max_counts = {k: 1 for k in self.ch_list}            # {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1}
        self.max_counts_list = {k: [] for k in self.ch_list}      # {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}

    def gen_fake_data(self):
        fake_counts = {
            1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0,
            13:0, 14:0, 15:0, 16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0, 24:0}

        fake_counts[5] += 100
        fake_counts[10] += 150
        fake_counts[15] += 70
        fake_counts[20] += 105

        fake_counts_series = []
        for _ in range(20):  # 10 diff
            for key in fake_counts.keys():
                fake_counts[key] += np.random.randint(-25, 25, 1)
                fake_counts[key] = np.max([0, fake_counts[key]])

            fake_counts_series.append(list(fake_counts.values()))

        return fake_counts_series

    def plot_normalized_widget(self, tab):
        # NOTE: THIS WILL BE REMOVED SINCE TKINTER IS TOO SLOW FOR LIVE PLOTS
        #  --> maybe instead have a button that runs the other script
        def update_plot(n):

            fig.clear()
            ax1 = fig.add_subplot(111)

            # b = self.parent.eta_class.lifetime_bins_ns
            ax1.set_title(f"Countrate")
            ax1.plot(self.ch_list, np.array(self.fake_counts_series[n])*np.array(self.active_chs))

            """for i, thing in enumerate(self.ch_show_countrate.keys()):
                if self.ch_show_countrate[thing].get() is False:
                    print(f"{thing} is hidden")
                    continue  # doesn't plot when hidden

                ax1.plot(time_axis, count_dict[thing], c=self.ch_colors[thing], label=lookup[thing] + ' (0.1s)')
                # ax1.axhline(y=np.sum(count_dict[thing])/1.4, c=self.ch_colors[thing], linestyle='--', label=lookup[thing]+' (1s)')
                # ax1.axhline(y=np.sum(count_dict[thing]), c=self.ch_colors[thing], linestyle='-', label='TEMP: total accum')
                # TODO REMOVE^ only applicable for the 1s measurement"""

            #ax1.legend()
            ax1.set_xlabel('Channel', fontsize=10)
            ax1.set_ylabel('Counts', fontsize=10)
            # ax1.set_xlim([-30, 30])

            ax1.grid()
            fig.canvas.draw_idle()  # updates the canvas immediately?

        if len(DebuggingFunctions.get_children(tab)) > 0:
            # Figure already exists!
            DebuggingFunctions.remove_child(tab, 0)
            print("live plt child found and removed")
        else:
            print("No live plt child found")

        # the figure that will contain the plot
        fig = plt.figure(figsize=(8, 5), dpi=100)  # 10 3
        ax1 = fig.add_subplot(111)

        self.fake_counts_series = self.gen_fake_data()  # series of 20 fake countrate measurements

        for nn in range(3):
            update_plot(nn)

            plt_frame, canvas = gui.pack_plot(tab, fig)
            plt_frame.grid(row=0, rowspan=1, column=1, sticky="nsew")

            gui.root.update()
            time.sleep(2)

        #butt_frm = make_time_scale_button()
        #butt_frm.grid(row=0, column=2, columnspan=1, sticky="news")


class GUI:

    def __init__(self):
        # Create and configure the main GUI window

        #self.root = tk.Tk()

        self.sq = None

        self.CIE_colors = ColorMatchingCIE()   # self.CIE_colors.wavelengths[600]

        self.default_theme = 'breeze' # 'radiance'
        self.root = ThemedTk(theme=self.default_theme)  # yaru is good i think

        #path = '@duck.cur'  # Path to the image followed by @
        self.root['cursor'] = ''  # = path  # Set the cursor

        self.root.title("OSQ - One Shot Quantum")   # *Ghosttly matters*
        self.root.geometry('1000x720')
        #self.root.geometry('1250x800')
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
        # self.tabs['WebSQ']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Config WebSQ')
        self.tabs['Calibration']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Calibration')
        self.tabs['Load']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Load Scan')
        self.tabs['New']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Create New Scan')
        self.tabs['Settings']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Settings')

        # --------
        #websq_nb = self.add_notebook(parent_tab=self.tabs['WebSQ']['tab'], anchor='w', side='top')  # TODO: maybe do something with??

        # TODO: ADD A CHANNEL SELECT THAT IS GRIDDED ABOVE ALL THE TABS
        #websqScanClass.init_channel_select_websqscan_tab(websq_nb)   # adds in load params
        # Create sub-notebooks for each tab and pack, then add children tabs
        #self.tabs['WebSQ']['notebook'] = self.add_notebook(parent_tab=self.tabs['WebSQ']['tab'], anchor='w', side='top')
        #self.tabs['WebSQ']['children']['Counts'] = self.add_tab(parent_nb=self.tabs['WebSQ']['notebook'], tab_name='Live counts')
        #self.tabs['WebSQ']['children']['Bias Trigger'] = self.add_tab(parent_nb=self.tabs['WebSQ']['notebook'], tab_name='Bias Trigger')
        #self.tabs['WebSQ']['children']['temp'] = self.add_tab(parent_nb=self.tabs['WebSQ']['notebook'], tab_name='(temp)')
        #self.tabs['WebSQ']['children']['temp'] = self.add_tab(parent_nb=self.tabs['WebSQ']['notebook'], tab_name='(temp)')
        #self.tabs['WebSQ']['children']['temp'] = self.add_tab(parent_nb=self.tabs['WebSQ']['notebook'], tab_name='(temp)')

        # --------
        # NOTE: don't know why we need to make load and new notebooks twice but it works :)
        load_nb = self.add_notebook(parent_tab=self.tabs['Load']['tab'], anchor='w', side='top')
        new_nb = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top')
        loadScanClass.acquisition_loadscan_tab(load_nb)   # adds in load params
        newScanClass.acquisition_newscan_tab(new_nb)

        # end note

        # Create sub-notebooks for each tab and pack, then add children tabs
        self.tabs['Calibration']['notebook'] = self.add_notebook(parent_tab=self.tabs['Calibration']['tab'], anchor='w', side='top', fill='both', expand=1)
        self.tabs['Load']['notebook'] = self.add_notebook(parent_tab=self.tabs['Load']['tab'], anchor='w', side='top', fill='both', expand=1)
        self.tabs['New']['notebook'] = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top', fill='both', expand=1)
        self.tabs['Settings']['notebook'] = self.add_notebook(parent_tab=self.tabs['Settings']['tab'], anchor='w', side='top', fill='both', expand=1)

        # NOTE NEW!
        #self.tabs['Calibration']['children']['Normalized'] = self.add_tab(parent_nb=self.tabs['Calibration']['notebook'], tab_name='Normalized Counts')
        self.tabs['Calibration']['children']['Wavelengths'] = self.add_tab(parent_nb=self.tabs['Calibration']['notebook'], tab_name='Channel Wavelengths')
        self.tabs['Calibration']['children']['...'] = self.add_tab(parent_nb=self.tabs['Calibration']['notebook'], tab_name='...')  # FIXME
        #calibrationClass.init_live_tab(self.tabs['Calibration']['children']['Normalized'])
        calibrationClass.init_wavelength_tab(self.tabs['Calibration']['children']['Wavelengths'])

        # ---

        #load_nb = self.tabs['Load']['notebook']
        self.tabs['Load']['children']['Countrate'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Countrate')
        self.tabs['Load']['children']['Spectrum'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Spectrum')
        self.tabs['Load']['children']['Lifetime'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime')
        self.tabs['Load']['children']['Lifetime Color'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime Color')
        self.tabs['Load']['children']['Correlation'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Correlation')
        #self.tabs['Load']['children']['Lifetime 3D'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime 3D')
        # NOTE  ('Visible Spectra' IS THE CIE COLOR plot)
        #self.tabs['Load']['children']['Visible Spectra'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Visible Spectra')
        # --------
        self.tabs['New']['children']['Countrate'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Countrate')
        self.tabs['New']['children']['Spectrum'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Spectrum')
        self.tabs['New']['children']['Lifetime'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Lifetime')
        self.tabs['New']['children']['Lifetime Color'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Lifetime Color')
        self.tabs['New']['children']['Correlation'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Correlation')
        #self.tabs['New']['children']['Lifetime 3D'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Lifetime 3D')
        #*self.tabs['New']['children']['Visible Spectra'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Visible Spectra')

        # --------
        self.tabs['Settings']['children']['Appearance'] = self.add_tab(parent_nb=self.tabs['Settings']['notebook'], tab_name='Appearance')
        self.tabs['Settings']['children']['Defaults'] = self.add_tab(parent_nb=self.tabs['Settings']['notebook'], tab_name='Defaults')
        self.tabs['Settings']['children']['About'] = self.add_tab(parent_nb=self.tabs['Settings']['notebook'], tab_name='About')

        # TODO MAYBE MOVE TO ANOTHER INITIALIZATION FUNCTION WHERE THINGS ARE CREATED
        self.build_appearance_settings(self.tabs['Settings']['children']['Appearance'])  # self.root_nb)
        # --------

        # Adding plot/image to the spectra tab ... TEMP? might move the image out of lower tab group
        #*self.plot_visible_spectra_tab(self.tabs['Load']['children']['Visible Spectra'], loadScanClass)  # NOTE TEMP FIXME!!!!

        #conf_frm = ttk.Frame(load_nb, relief=tk.FLAT)
        #option_thm = ttk.Label(conf_frm, text='TESTTT')
        #option_thm.grid(row=0, column=0)
        ##conf_frm.grid(row=4, column=100) #expand=1, anchor='ne')
        #load_nb.add(conf_frm, text='ssTESTTT')


    # SETTINGS THEME AND CURSOR (todo: make a sub class just for settings?)
    def build_appearance_settings(self, tab):
        def change_theme(new_thm):
            print("changed to theme:", new_thm)
            self.root.set_theme(new_thm)
            thm_var.set(new_thm)
            newScanClass.update_log_box_height()

        def change_cursor(new_crs):
            self.root['cursor'] = new_crs
            print("changed cursor to:", new_crs)
            if new_crs == '':
                cursor_var.set("default")
            else:
                cursor_var.set(new_crs[len(curs_folder):-4])
            self.root.update()

        conf_frm = ttk.Frame(tab)
        conf_frm.pack(expand=1, anchor='nw')  # 'ne' if in root_nb

        ttk.Label(conf_frm, text="Theme:").grid(row=0, column=0, sticky='news')
        ttk.Label(conf_frm, text="Cursor:").grid(row=0, column=1, sticky='news')

        # -----
        # THEME
        thm_var = tk.StringVar(value=self.default_theme)
        option_thm = ttk.OptionMenu(conf_frm, variable=thm_var, default=self.default_theme)
        option_thm.grid(row=1, column=0)
        for theme in self.theme_list:
            option_thm['menu'].add_command(label=f"{theme}", command=lambda thm=theme: change_theme(thm))

        # CURSOR
        cursor_list = []  #  ['']
        curs_folder = 'Configs/assets/cursors/'
        for file in glob.glob(f"{curs_folder}*.cur"):
            cursor_list.append(file)

        cursor_var = tk.StringVar(value='default')
        option_cursor = ttk.OptionMenu(conf_frm, variable=cursor_var, default='')
        option_cursor.grid(row=1, column=1)

        option_cursor['menu'].add_command(label=f"default", command=lambda cur='': change_cursor(cur))
        for cursor in cursor_list:
            #option_cursor['menu'].add_command(label=f"{cursor[8:-4]}", command=lambda cur=cursor: change_cursor(f'@{cur}'))
            option_cursor['menu'].add_command(label=f"{cursor[len(curs_folder):-4]}", command=lambda cur=cursor: change_cursor(f'@{cur}'))

    def add_plot_tabs(self, parent_class, parent_name):
        # NOTE: CREATE NEW TAB THAT DOESN'T EXIST WITH:
        #child_tab = self.tabs[parent_name]['children']['example_plot1'] = self.add_tab(parent_nb=self.tabs[parent_name]['notebook'], tab_name='example_plot1')
        #plot_3d_lifetime_tab(child_tab, parent_class)
        # ----

        for tab_nm in self.tabs[parent_name]['children'].keys():
            try:
                gui.add_new_plot_tab(parent_class=parent_class, parent_name=parent_name, tab_name=tab_nm, init=True)
            except:
                print(f"ERROR: FAILED TO LOAD TAB '{tab_nm}'")
                raise
        #self.plot_lifetime_color_tab(self.tabs[parent_name]['children']['Lifetime Color'], parent_class)  # note: temp moved to front for testing
        #self.plot_lifetime_tab(self.tabs[parent_name]['children']['Lifetime'], parent_class)  # note: temp moved to front for testing

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
            elif tab_name == 'Lifetime 3D':
                self.tabs[parent_name]['children']['Lifetime 3D'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Lifetime 3D')
            elif tab_name == 'Visible Spectra':
                self.tabs[parent_name]['children']['Visible Spectra'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Visible Spectra')
            elif tab_name == 'Correlation':
                self.tabs[parent_name]['children']['Correlation'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Correlation')
            else:
                print(f"WARNING: ??? in function 'add_new_plot_tab()'")

        # ----

        if parent_name == 'Calibration':
            if tab_name == 'Normalized':
                #self.plot_normalized_tab(self.tabs[parent_name]['children']['Normalized'], parent_class)
                print("NORMALIZED NOT IMPLEMENTED")
                pass

            elif tab_name == 'Wavelengths':
                print("PLOT NOT IMPLEMENTED")
                pass

            else:
                print(f'Calibration tab "{tab_name}" not found!')
            return

        if tab_name == 'Spectrum':
            self.plot_spectrum_tab(self.tabs[parent_name]['children']['Spectrum'], parent_class)

        elif tab_name == 'Lifetime Color':
            self.plot_lifetime_color_tab(self.tabs[parent_name]['children']['Lifetime Color'], parent_class)

        elif tab_name == 'Lifetime':
            self.plot_lifetime_tab(self.tabs[parent_name]['children']['Lifetime'], parent_class)

        elif tab_name == 'Lifetime 3D':
            self.plot_3d_lifetime_tab(self.tabs[parent_name]['children']['Lifetime 3D'], parent_class)

        elif tab_name == 'Countrate':
            self.plot_countrate_tab(self.tabs[parent_name]['children']['Countrate'], parent_class)

        elif tab_name == 'Correlation':
            self.plot_correlation_tab(self.tabs[parent_name]['children']['Correlation'], parent_class)

        elif tab_name == 'Visible Spectra':
            self.plot_visible_spectra_tab(self.tabs[parent_name]['children']['Visible Spectra'], parent_class)
        else:
            print(f"WARNING: Could not find plotting option for: {tab_name}")

    def plot_normalized_tab(self, plots_norm, parent):
        parent.plotting_class.plot_normalized_widget(plots_norm)

    # **
    def plot_lifetime_tab(self, plots_lifetime, parent):
        parent.plotting_class.plot_lifetime_widget(plots_lifetime)

    def plot_lifetime_color_tab(self, plots_lifetime, parent):
        parent.plotting_class.plot_lifetime_colorbar_widget(plots_lifetime)

    # **
    def plot_3d_lifetime_tab(self, plots_3d_lifetime, parent):
        t_plt = parent.plotting_class.plot_3D_lifetime_widget(plots_3d_lifetime)
        t_plt.grid(row=2, column=1, columnspan=1, sticky="news")

    # **
    def plot_spectrum_tab(self, plots_spectrum, parent):
        parent.plotting_class.plot_spectrum_widget(plots_spectrum)
        #info_frm = parent.plotting_class.plot_display_info_widget(plots_spectrum, "Spectrum plot info")
        #info_frm.grid(row=0, rowspan=1, column=1, sticky="nsew")

    def plot_countrate_tab(self, plots_spectrum, parent):
        parent.plotting_class.plot_countrate_widget(plots_spectrum)

    # **
    def plot_correlation_tab(self, plots_correlation, parent):
        # TODO: add widgets
        #ttk.Label(plots_correlation, text='\nNOTHING TO SHOW YET. WORK IN PROGRESS...', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news")
        parent.plotting_class.plot_correlation_widget(plots_correlation)

    # **?
    def plot_visible_spectra_tab(self, plots_spectrum, parent):
        # CALL WITH: self.plot_visible_spectra_tab(self.tabs['Load']['children']['Visible Spectra'], loadScanClass)  # NOTE TEMP FIXME!!!!

        # removes old fig if we have already have one
        if len(DebuggingFunctions.get_children(plots_spectrum)) > 0:
            # Figure already exists!
            DebuggingFunctions.remove_child(plots_spectrum, 0)
            # Note: for now we should only have one child here, but maybe later i'll add more children (?)

        # TODO: INSTEAD OF DESTROYING AND CREATING A NEW FIGURE, JUST CHANGE THE LINES AND ANNOTATION
        # CIE version:
        parent.plotting_class.plot_visible_spectra_widget(plots_spectrum).grid(row=0, column=0, sticky="nsew")
        #DebuggingFunctions.print_children(plots_spectrum, parentname="Spectra tab", info="...")

        # simple version:
        #parent.plotting_class.plot_visible_spectra_widget(plots_spectrum, simple=True).grid(row=1, column=0, sticky="nsew")

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


# TODO: FIX ME BELOW TO WORK WITH RETINA
'''class WebSQGroup:
    def __init__(self):
        # -------------- ARGUMENTS: --------------
        self.websq_handle = None
        self.url = '130.237.35.20'   # 12 channels
        self.base_url = f'ws://{self.url}'
        self.number_of_detectors = 24
        self.active_channels = {}
        self.reset_vars()

    def reset_vars(self):
        self.case = 'calibrate'
        self.cnter = 0
        self.max_val = 0
        self.norm_counter = 0
        self.n = 10
        self.counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0}
        self.max_counts = {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1}
        self.max_counts_list = {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [], 10: [], 11: [], 12: []}

        # print("done reset vars ")

    def get_live_counts(self, payload):
        self.payload = payload
        # print("case", self.case)

        if self.case == 'running':
            self.cnter += 1
            if self.cnter % 10 == 0:  # for when to update plot lims
                self.max_val = 0

            for message in payload:  # for every channel
                self.counts[message['rank']] = message['counts'] / (
                self.max_counts[message['rank']])  # divide by measured average

                if self.max_val < self.counts[message['rank']]:
                    self.max_val = self.counts[message['rank']]

                # thisapp._update()
                # self.print_counts(payload)

        elif self.case == 'calibrate':

            if self.norm_counter == self.n:
                self.case = 'running'
                # print("GO RUNNING")
                for key in self.max_counts.keys():
                    self.max_counts[key] = np.max([np.mean(self.max_counts_list[key]), 1.0])

            self.norm_counter += 1
            for message in payload:  # for every channel
                self.max_counts_list[message['rank']].append(message['counts'])

        else:
            print("WRONGG CASE")
            self.case = 'running'

        # print("done get live counts")

    def print_counts(self, payload):

        # print("---", end='\r---')
        # print(payload[0]['time'], end='')

        msg = f"{payload[0]['time']}"
        # init for loop every time step
        for message in payload:  # for every channel
            # time, mcuId, cuId, rank = message["time"], message['mcuId'], message['cuId'], message["rank"]
            # counts, monitorV, biasI, inttime = message['counts'], message['monitorV'], message['biasI'], message['inttime']
            msg += f"  ({message['rank']}):{message['counts']}  "
            # print(f"ch{message['rank']}: {message['counts']} counts")
    @staticmethod
    async def websocket_client(base_url, callback, n=0, normalized=False):
        """
        Listens to the Retina websocket and processes every package.
        For each package `callback` is called.
        Give the URL (base_url) for the socket stream
        and the callback that is called everytime a package is received.
        A package contains the information for all the channels in an array.
        If given n, the callback is called around n times.

        Notes
        -----
        The values for BiasI only update when an IV sweep is being done on the channel.
        """
        uri = base_url + "/counts"

        async with websockets.connect(uri) as websocket:
            # Close the connection when receiving SIGTERM.
            if plat == "linux" or plat == "linux2":
                loop = asyncio.get_event_loop()
                loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.ensure_future(websocket.close()))
            # Process messages received on the connection.
            i = 0
            async for message in websocket:
                channel_size = 32  # One channel gives 32 bytes of information.
                payload = []
                for offset in range(0, len(message), channel_size):
                    channel = message[offset:(offset + channel_size)]
                    inttime = struct.unpack("<I", channel[16:20])[0] * 10  # ms
                    payload.append(
                        {
                            "mcuId": struct.unpack("<B", channel[0:1])[0],
                            "cuId": struct.unpack("<B", channel[1:2])[0],
                            "cuStatus": struct.unpack("<B", channel[2:3])[0],
                            "monitorV": struct.unpack("<f", channel[4:8])[0],
                            "biasI": struct.unpack("<f", channel[8:12])[0],
                            "inttime": inttime,
                            "counts": (
                                int(1000 / inttime) * struct.unpack("<I", channel[12:16])[0]
                                if normalized
                                else struct.unpack("<I", channel[12:16])[0]
                            ),
                            "rank": struct.unpack("<I", channel[20:24])[0],
                            "time": struct.unpack("<d", channel[24:])[0],
                        }
                    )
                callback(payload)
                i += 1
                if n and i >= n:
                    return
    
    # --------
    def old_get_counts(self, num=1):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(websocket_client(self.base_url, self.old_fetch_counts, n=num))

    # TODO FIXME
    def old_fetch_counts(self, payload):
        # init for loop every time step
        for message in payload:  # for every channel
            time, mcuId, cuId, rank = message["time"], message['mcuId'], message['cuId'], message["rank"]
            counts, monitorV, biasI, inttime = message['counts'], message['monitorV'], message['biasI'], message['inttime']

    # TODO FIX print counts below
    def old_print_counts(self, payload):
        msg = f"{payload[0]['time']}"
        # init for loop every time step
        for message in payload:  # for every channel
            time, mcuId, cuId, rank = message["time"], message['mcuId'], message['cuId'], message["rank"]
            counts, monitorV, biasI, inttime = message['counts'], message['monitorV'], message['biasI'], message['inttime']

            print(f"""{time} | 
                        {mcuId}.{str(cuId).zfill(2)} ({str(rank).zfill(2)}) | 
                        Counts: {str(counts).rjust(10,' ')} Counts | 
                        monitorV: {str(round(monitorV,6)).rjust(6,' ')} V | 
                        BiasI: {str(biasI).rjust(6,' ')} μA | 
                        intTime: {inttime} ms""")'''
    
# TODO:FIX?
class CalibrateGroup:
    def __init__(self):
        self.WebSQ_link = None # WebSQGroup()
        self.histo = False

    def QT_graph(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(websocket_client(self.WebSQ_link.base_url, self.WebSQ_link.get_live_counts, n=10))

        app = QtWidgets.QApplication([])
        main = MainWindow(self.histo, self.WebSQ_link)
        main.show()
        # websocket_client(base_url, livecounts.get_live_counts, n=1)
        app.exec()

# NOTE: TESTING MAIN WINDOW HERE, MIGHT REMOVE
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, histo, SQ_link):
        super().__init__()
        self.histo = histo
        self.SQ_link = SQ_link
        if histo:

            window = pg.plot()
            window.setGeometry(100, 100, 600, 500)

            self.time = np.arange(0.5, 12.5, 1)
            self.counts = [1 for _ in range(12)]

            self.plot_graph = pg.BarGraphItem(x=self.time, height=self.counts, width=0.6, brush='g')

            #self.setCentralWidget(self.plot_graph)
            window.addItem(self.plot_graph)
            #window.setWindowTitle("QT Graph")
            #self.plot_graph.setBackground("w")

            # self.plot_graph.sigMouseReleased.connect(self.mouse_release)  # try to get some mouse event

            # -------------
            self.loop = loop = asyncio.get_event_loop()
            loop.run_until_complete(websocket_client(self.SQ_link.base_url, self.SQ_link.get_live_counts, n=10))

            # Add a timer to simulate new temperature measurements
            self.timer = QtCore.QTimer()
            self.timer.setInterval(50)
            self.timer.timeout.connect(self.update_plot)
            self.timer.start()


        else:
            # Temperature vs time dynamic plot
            self.plot_graph = pg.PlotWidget()
            self.setCentralWidget(self.plot_graph)

            self.plot_graph.setBackground("w")
            pen = pg.mkPen(color=(0, 0, 0))

            #self.plot_graph.setTitle("Placholder title", color="b", size="20pt")
            styles = {"color": "red", "font-size": "18px"}

            #self.plot_graph.setLabel("left", "Counts", **styles)
            #self.plot_graph.setLabel("bottom", "Channel", **styles)

            #self.plot_graph.addLegend()
            self.plot_graph.showGrid(x=True, y=True)

            self.plot_graph.setYRange(0, 2)

            self.time = np.arange(0.5, 12.5, 1)
            self.counts = [0 for _ in range(12)]

            # Get a line reference
            self.line = self.plot_graph.plot(
                self.time,
                self.counts,
                name="Counts",
                pen=pen,
                symbol="o",
                symbolSize=15,
                symbolBrush="b",
            )
            #self.plot_graph.sigMouseReleased.connect(self.mouse_release)  # try to get some mouse event

            # adding pushbutton
            self.pushButton = QtWidgets.QPushButton(self.plot_graph)
            self.pushButton.setGeometry(QtCore.QRect(20, 0, 50, 28))

            # adding signal and slot
            self.pushButton.clicked.connect(self.clicked)

            self.label = QtWidgets.QLabel(self.plot_graph)
            self.label.setGeometry(QtCore.QRect(80, 0, 50, 28))

            # keeping the text of label empty before button get clicked
            self.label.setText("<-- Reset")

            # -------------
            self.loop = loop = asyncio.get_event_loop()
            loop.run_until_complete(websocket_client(self.SQ_link.base_url, self.SQ_link.get_live_counts, n=10))

            # Add a timer to simulate new temperature measurements
            self.timer = QtCore.QTimer()
            self.timer.setInterval(50)
            self.timer.timeout.connect(self.update_plot)
            self.timer.start()

    def mouse_release(self):
        print('click')  # never execute

    def clicked(self):
        print('clicked reset')
        self.SQ_link.reset_vars()

    def update_plot(self):
        #for j in range(0, 24, 2):
        #    self.counts[j] = livecounts.counts[j//2 + 1]
        #    self.counts[j+1] = livecounts.counts[j//2 + 1]
        #print(self.counts)
        #self.line.setData(self.time, list(self.counts))
        if self.histo:
            rnd = np.random.random(12)
            time.sleep(0.5)
            self.plot_graph.setOpts(height=[self.SQ_link.counts[j+1]+rnd[j] for j in range(12)])
        else:
            self.line.setData(self.time, [self.SQ_link.counts[j+1] for j in range(12)])
        self.loop.run_until_complete(websocket_client(self.SQ_link.base_url, self.SQ_link.get_live_counts, n=1))

        if self.SQ_link.case == 'running':
            all_cnts = np.array([self.SQ_link.counts[i] for i in range(1, 13)])
            ch_nrs = np.arange(1, 13, 1)
            #print(all_cnts)
            #print(ch_nrs)
            if np.sum(all_cnts) != 0:
                self.weighted_avg = round(np.sum(ch_nrs * all_cnts) / np.sum(all_cnts), 2)
                #print(weighted_avg)
                self.plot_graph.setTitle(f"Avg ch={self.weighted_avg}", color="b", size="20pt")


        #livecounts.print_counts(livecounts.payload)


# -----

async def websocket_client(base_url, callback, n=0, normalized=False):
    """
    Listens to the Retina websocket and processes every package.
    For each package `callback` is called.
    Give the URL (base_url) for the socket stream
    and the callback that is called everytime a package is received.
    A package contains the information for all the channels in an array.
    If given n, the callback is called around n times.

    Notes
    -----
    The values for BiasI only update when an IV sweep is being done on the channel.
    """
    uri = base_url + "/counts"

    async with websockets.connect(uri) as websocket:
        # Close the connection when receiving SIGTERM.
        if platform == "linux" or platform == "linux2":
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.ensure_future(websocket.close()))
        # Process messages received on the connection.
        i = 0
        async for message in websocket:
            channel_size = 32  # One channel gives 32 bytes of information.
            payload = []
            for offset in range(0, len(message), channel_size):
                channel = message[offset:(offset + channel_size)]
                # ----
                # JULIA TESTING.. TODO: MUST REMOVE
                #if struct.unpack("<I", channel[20:24])[0] in [1, 2, 3, 8, 9, 12, 13, 22]:  # TESTING FAULTY CHANNELS
                #    continue
                # ----

                inttime = struct.unpack("<I", channel[16:20])[0] * 10  # ms
                payload.append(
                    {
                        "mcuId": struct.unpack("<B", channel[0:1])[0],
                        "cuId": struct.unpack("<B", channel[1:2])[0],
                        "cuStatus": struct.unpack("<B", channel[2:3])[0],
                        "monitorV": struct.unpack("<f", channel[4:8])[0],
                        "biasI": struct.unpack("<f", channel[8:12])[0],
                        "inttime": inttime,
                        "counts": (
                            int(1000 / inttime) * struct.unpack("<I", channel[12:16])[0]
                            if normalized
                            else struct.unpack("<I", channel[12:16])[0]
                        ),
                        "rank": struct.unpack("<I", channel[20:24])[0],
                        "time": struct.unpack("<d", channel[24:])[0],
                    }
                )
            callback(payload)
            i += 1
            if n and i >= n:
                return

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
            # --> how to use this function: "loop.run_until_complete(websocket_client(base_url, live_counts.get_active_channels, n=1))"

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

# -----


class Calibration:
    def __init__(self):
        self.plotting_class = LivePlotting()
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


class NewScanGroup:
    def __init__(self):
        #self.demo_class = Demo()
        #self.eta_class = ETA()
        #self.plotting_class = Plotting(self)

        # class instances when connected
        self.eta_class = ETA(self)
        self.plotting_class = Plotting(self)
        self.loading = False
        self.cancel = False

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

        self.running = False  # this tracks if we are running a scan (collecting counts from detector)
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
        self._scan_frm = scan_frm = ttk.Frame(new_scan_tab, borderwidth=1, relief=tk.FLAT)
        scan_frm.grid(row=1, column=0,  sticky='nw')  # nws

        # Analysis configs:
        self.analysis_config_widget(scan_frm).grid(row=1, column=0, sticky="news")

        # Row of start, stop buttons and progress bar:
        self.start_scan_widget(scan_frm).grid(row=2, column=0, sticky="news")  # in sub frame

        # Analysis buttons and progressbar to start:
        self.analysis_newscan_widget(scan_frm).grid(row=3, column=0, sticky="news")

        # ---
        # Logger box:
        log_box_frm = ttk.Frame(new_scan_tab, borderwidth=1, relief=tk.GROOVE)
        log_box_frm.grid(row=1, column=1, sticky="nws")  # in sub frame
        self.log_scan_widget(log_box_frm).grid(row=0, column=0, sticky="news")   # Inner thing

        # -----
        #self.show_geometry(params_frm, "Configs analysis top")
        #self.show_geometry(scan_frm, "Scan analysis left")
        #self.show_geometry(log_box_frm, "Log box right")
        self.update_log_box_height()

    # TODO: FIXME BELOW (make sure it connects and does right)
    def start_scan_widget(self, tab):

        def press_start():
            self.write_log(f"{self.sp.sp_handle}")
            self.write_log(f"{self.sq.websq_handle}")
            if (not self.sp.sp_handle) or (not self.sq.websq_handle):
                self.write_log(f"Can not start scan if we are not connected")
                self.running = False
                return

            #self.save_data(mode="w")   # TODO: maybe only have this once per new measurement (so that we can pause and start again)
            # True:     if we have successfully configured the device
            # False:    failed to do all configs to device, should not start scan
            # None:     did not send new configs, will check but can start scan anyway (maybe??)
            outcome = {True : 'green', False : 'red', None : 'grey'}
            #self.mark_done(btn_start, highlight=outcome[self.config_success], type='button')
            #self.mark_done(btn_stop, highlight=self.button_color, type='button')
            self.running = True

        def press_stop():
            self.running = False
            #self.mark_done(btn_start, highlight=self.button_color, type='button')
            #self.mark_done(btn_stop, highlight='red', type='button')

        frm_send = ttk.Frame(tab, relief=tk.FLAT, borderwidth=0)
        btn_start = ttk.Button(frm_send, text="Start Scan", command=press_start)
        btn_stop = ttk.Button(frm_send, text="Stop", command=press_stop)
        self.prog_bar = ttk.Progressbar(frm_send, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=430)  # progressbar

        btn_start.grid(row=0, column=0, sticky="nsew")
        btn_stop.grid(row=0, column=1, sticky="nsew")
        self.prog_bar.grid(row=0, column=2, sticky="ew")

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
            # self.running = False  # TODO CHECK: need to stop scanning i think???
            if self.port.get() == "Select...":
                self.write_log(f"MUST SELECT PORT FIRST")

            #s#elf.write_log(f"pressed connect. fixme for real")
            self.write_log(f"connecting to port {self.port.get()}")

            #if demo:
            #    Demo.d_connect(port_parts['connect'])  # changes color of button to green
            #    self.sp.sp_handle = True
            #    return

            # TODO CONNECTION....
            # if connect successful:
            port_parts['label'].config(text=f'Connected to {self.port.get()}')
            port_parts['refresh'].config(state='disabled')
            #port_parts['disconnect'].config(state='normal')
            #port_parts['connect'].config(state='disabled')
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
            # self.running = False  # TODO CHECK: need to stop scanning i think???
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

        def select_grating():
            # FIXME OR REMOVE
            # self.calculate_nm_bins()
            # TODO: auto update plot axis
            pass


        # FRAMES
        frm_configs = ttk.Frame(tab, relief=tk.FLAT)#, borderwidth=1)

        frm = {
            'port'    : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            'slit'    : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            'grating' : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            'detect'  : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            #'ch'      : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
        }

        # WIDGETS

        #  -- Slit:
        slt_parts = [ttk.Label(frm['slit'], text='Slit width (um)'),
                     ttk.Entry(frm['slit'], textvariable=self.params['slit']['var'], width=4)]

        scanime_parts = [ttk.Label(frm['slit'], text='\nScantime (s)'),
                     ttk.Entry(frm['slit'], textvariable=self.params['scantime']['var'], width=4)]

        #  -- Grating:
        grating_widget_dict = {
            'radio_b': [],
            'grt_txt': [ttk.Label(frm['grating'], text='Grating\n(gr/mm)')],
            'blz_txt': [ttk.Label(frm['grating'], text='Blaze\n(nm)')],
            'wid_txt': [ttk.Label(frm['grating'], text='Width')],
        }
        for c in range(3):
            grating_widget_dict['radio_b'].append(ttk.Radiobutton(frm['grating'], text="", variable=self.params['grating']['var'], value=c + 1,
                                                                  command=select_grating))
            grating_widget_dict['grt_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['grating']}"))
            grating_widget_dict['blz_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['blz']}"))
            grating_widget_dict['wid_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['width']}"))

        #  -- Detector:
        center_parts = [ttk.Label(frm['detect'], text="Center λ (nm)"),
                     ttk.Entry(frm['detect'], textvariable=self.params['nm']['var'], width=4),
                     ]

        wid_parts = [ttk.Label(frm['detect'], text="Pixel width (nm)"),
                     ttk.Entry(frm['detect'], textvariable=self.params['width_nm']['var'], width=4),]

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
                       #'disconnect'     : ttk.Button(frm['port'], text="Disconnect", command=press_disconnect, state='disabled'),
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
        gui.add_to_grid(widg=wid_parts,     rows=[3 ,4], cols=[1, 1], sticky=["ew", "ew"])


        # ------------- GRID FRAMES --------------
        # labels for each part:
        #gui.add_to_grid(widg=[frm['port'], frm['grating'], frm['slit'], frm['detect'], frm['ch']], cols=[1, 2, 3, 4, 5], rows=[1]*5, sticky=["news"]*5)
        gui.add_to_grid(widg=[frm['port'], frm['grating'], frm['slit'], frm['detect']], cols=[1, 2, 3, 4], rows=[1]*4, sticky=["news"]*4)

        ttk.Label(frm_configs, text="Monochromator", relief=tk.GROOVE, anchor='center').grid(row=0, column=0, columnspan=4, sticky='ew')

        return frm_configs

    def analysis_config_widget(self, tab):

        def get_recipe():
            new_reci = askopenfilename(filetypes=[("ETA recipe", "*.eta")])
            if new_reci:
                self.params['eta_recipe']['var'].set(new_reci)

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
        #*reci_btn = ttk.Button(frm_anal_configs, text="ETA recipe", command=get_recipe)
        file_entry = ttk.Entry(frm_anal_configs, textvariable=self.params['file_name']['var'], width=60)
        #reci_entry = ttk.Entry(frm_anal_configs, textvariable=self.params['eta_recipe']['var'], width=60)

        file_btn.grid(row=1, column=0, sticky="ew")
        #*sreci_btn.grid(row=2, column=0, sticky="ew")
        file_entry.grid(row=1, column=1, columnspan=10, sticky="ew")
        #reci_entry.grid(row=2, column=1, columnspan=10, sticky="ew")

        return frm_anal_configs

    def analysis_newscan_widget(self, tab):

        def press_analyze():
            try:
                self.cancel = False
                self.loading = True
                analyze_btn.config(state='disabled')
                self.write_log(f"Starting analysis")  # NOTE
                #self.eta_class.eta_lifetime_analysis()
                #self.eta_class.new_tof_analysis()
                # TODO FIXME ABOVE

                analyze_btn.config(state='normal')
                self.loading = False

                if not self.cancel:

                    gui.add_plot_tabs(parent_class=self, parent_name='Load')
                    analyzed_file_label.config(text=f"Analyzed file: {self.params['file_name']['var'].get()}")
                else:
                    self.cancel = False

            except:
                self.write_log(f"Failed to analyze")
                raise

        def press_cancel():
            if self.loading:
                self.write_log(f"Canceled Analysis")  # NOTE
                self.cancel = True
                self.eta_class.pb['value'] = 0

        def press_add():
            print('FIXME')

        frm_anal_buttons = ttk.Frame(tab, borderwidth=0, relief=tk.FLAT)

        # strt stop analysis buttons:
        analyze_btn = ttk.Button(frm_anal_buttons, text="Analyze", command=press_analyze)
        cancel_btn = ttk.Button(frm_anal_buttons, text="Cancel", command=press_cancel)
        #add_btn = ttk.Button(frm_anal_buttons, text="Add test", command=press_add)
        #add_btn.grid(row=4, column=0, sticky='ew')

        # shows which file we have analysed:
        analyzed_file_label = ttk.Label(frm_anal_buttons, text='', font="Helvetica 10 normal italic")

        analyze_btn.grid(row=3, column=0, sticky="ew")
        cancel_btn.grid(row=3, column=1, sticky="ew")
        analyzed_file_label.grid(row=4, column=1, columnspan=10, sticky='ew')

        # progress bar of analysis:
        self.eta_class.pb = ttk.Progressbar(frm_anal_buttons, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=430) # 400)  # progressbar

        self.eta_class.pb.grid(row=3, column=2, sticky="ew")

        return frm_anal_buttons

    def log_scan_widget(self, tab):
        from tkinter import scrolledtext

        frm_log = ttk.Frame(tab, relief=tk.FLAT)

        """
                __Configs analysis top__
                geometry    : [1206x122+0+0]
                width       : [1206]
                height      : [122]
                reqwidth    : [1206]
                reqheight   : [122]

                __Scan analysis left__
                geometry    : [673x167+0+122]
                width       : [673]
                height      : [167]
                reqwidth    : [673]
                reqheight   : [167]

                __Log box right__
                geometry    : [352x167+854+122]
                width       : [352]
                height      : [167]
                reqwidth    : [171]
                reqheight   : [156]

                """

        self.log_box = log_box = scrolledtext.ScrolledText(frm_log, wrap=tk.WORD, width=24, height=12, font=('Helvetica', 12, "italic"), state='disabled')
        log_box.grid(row=1, column=0, pady=0, padx=0)

        return frm_log

    def write_log(self, msg):
        self.log_box.configure(state='normal')
        self.log_box.insert('end', f'{msg}\n')
        self.log_box.configure(state='disabled')
        #label = ttk.Label(self.log_frm, text=f"{msg}")
        #label.pack(fill='both')
        #label.bind('<Configure>', lambda e: label.config(wraplength=label.winfo_width()-10))

    def show_geometry(self, wid, name):
        # 15 22
        wid.update()
        self.write_log(f"__{name}__")
        self.write_log(f" geometry    : [{wid.winfo_geometry()}]\n"
              f" width       : [{wid.winfo_width()}]\n"
              f" height      : [{wid.winfo_height()}]\n"
              f" reqwidth    : [{wid.winfo_reqwidth()}]\n"
              f" reqheight   : [{wid.winfo_reqheight()}]\n"
              )
        # self.write_log(full_w, full_h)

    def update_log_box_height(self):
        #s#elf.log_box.config(height=2, width=2)

        self._params_frm.update()
        self._scan_frm.update()
        box_w = self._params_frm.winfo_width() - self._scan_frm.winfo_width() - 42  # 9 is for scrollbar width
        box_h = self._scan_frm.winfo_height() - 7
        self.log_box.config(height=int(box_h/14), width=int(box_w/7))

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
        self.eta_class = ETA(self)
        self.plotting_class = Plotting(self)
        self.loading = False  # this tracks if we are running a scan (collecting counts from detector)
        self.cancel = False  # this tracks if we are running a scan (collecting counts from detector)

    def acquisition_loadscan_tab(self, tab):

        def press_start():
            try:
                self.cancel = False
                self.loading = True
                start_btn.config(state='disabled')
                self.write_log(f"Starting analysis")
                #self.eta_class.eta_lifetime_analysis()

                #self.eta_class.new_tof_analysis()

                #self.eta_class.new_correlation_analysis()

                start_btn.config(state='normal')
                option_plt['state'] = 'normal'

                self.loading = False

                if not self.cancel:
                    scantime = self.params['scantime']['var'].get()
                    self.eta_class.load_all_engines(scantime=scantime)
                    self.eta_class.new_tof_analysis()
                    gui.add_plot_tabs(parent_class=self, parent_name='Load')
                    analyzed_file_label.config(text=f"Analyzed file: {self.params['file_name']['var'].get()}")
                else:
                    self.cancel = False

                # ------

            except:
                self.write_log(f"Failed to analyze")
                raise

        def press_stop():
            if self.loading:
                self.cancel = True
                self.eta_class.pb['value'] = 0

        def get_file():
            new_file = askopenfilename(filetypes=[("Timeres datafile", "*.timeres")])
            if new_file:
                self.params['file_name']['var'].set(new_file)

        def get_recipe():
            new_reci = askopenfilename(filetypes=[("ETA recipe", "*.eta")])
            if new_reci:
                #reci_entry.delete(0, tk.END)
                self.params['eta_recipe']['var'].set(new_reci)

        def press_add(tab_name):  # new

            gui.add_new_plot_tab(parent_class=self, parent_name='Load', tab_name=tab_name)
            new_plt_var.set('+')
            new_options = get_plt_options()

            frm_misc.children[list(frm_misc.children.keys())[-1]].destroy()

            if new_options:
                option_plt = ttk.OptionMenu(frm_misc, new_plt_var, '+', *get_plt_options(), command=press_add)
                option_plt.grid(row=4, column=0, sticky='w')

        def get_plt_options():  # new
            remaining = []
            for op in ['Lifetime Color', 'Lifetime', 'Lifetime 3D', 'Spectrum', 'Correlation']:
                if op not in gui.tabs['Load']['children'].keys():
                    remaining.append(op)
            return remaining

        frm_misc = ttk.Frame(tab, borderwidth=3, relief=tk.FLAT) #
        frm_misc.grid(row=1, column=0, rowspan=15)

        # shows which file we have analysed:
        analyzed_file_label = ttk.Label(frm_misc, text='', font="Helvetica 10 normal italic")
        analyzed_file_label.grid(row=4, column=1, columnspan=10, sticky='ew')
        # ----
        ttk.Button(frm_misc, text="Datafile", command=get_file).grid(row=1, column=0, sticky="ew")
        #ttk.Button(frm_misc, text="ETA recipe", command=get_recipe).grid(row=2, column=0, sticky="ew")

        file_entry = ttk.Entry(frm_misc, textvariable=self.params['file_name']['var'], width=65)
        #reci_entry = ttk.Entry(frm_misc, textvariable=self.params['eta_recipe']['var'], width=65)
        file_entry.grid(row=1, column=1, sticky="ew")
        #reci_entry.grid(row=2, column=1, columnspan=10, sticky="ew")

        start_btn = ttk.Button(frm_misc, text="Analyze", command=press_start)
        start_btn.grid(row=1, column=2, sticky="ew")


        #self.eta_class.pb = ttk.Progressbar(frm_misc, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=475)  # progressbar
        #self.eta_class.pb.grid(row=3, column=3, sticky="ew")

        # -----
        new_plt_var = tk.StringVar(value='??')
        option_plt = ttk.OptionMenu(frm_misc, new_plt_var, '+', *get_plt_options(), command=press_add)
        option_plt.grid(row=4, column=0, sticky='w')
        option_plt['state'] = 'disabled'
        # ----

        # -------------
        # ---
        # Logger box:

        self.choose_params_widget(tab).grid(row=0, column=0, sticky="nw", padx=5, pady=5)

        # -----
        #self.show_geometry(params_frm, "Configs analysis top")
        #self.show_geometry(scan_frm, "Scan analysis left")
        #self.show_geometry(log_box_frm, "Log box right")
        #self.update_log_box_height()

    def choose_params_widget(self, tab):

        def update_spectrum(name=None, index=None, mode=None):

            gui.plot_visible_spectra_tab(gui.tabs['Load']['children']['Visible Spectra'], self)
            # FROM GUI CLASS:
            #   -->self.plot_visible_spectra_tab(self.tabs['Load']['children']['Visible Spectra'], loadScanClass)


        # FRAMES
        frm_configs = ttk.Frame(tab, relief=tk.FLAT)#, borderwidth=1)

        #  -- Detector:
        center_parts = [ttk.Label(frm_configs, text="Center λ (nm)"),
                        ttk.Entry(frm_configs, textvariable=self.params['nm']['var'], width=4)]

        wid_parts = [ttk.Label(frm_configs, text="Pixel width (nm)"),
                     ttk.Entry(frm_configs, textvariable=self.params['width_nm']['var'], width=4)]

        time_parts = [ttk.Label(frm_configs, text="Scan time (s)"),  # TODO USE!!! (only used in analysis now)
                     ttk.Entry(frm_configs, textvariable=self.params['scantime']['var'], width=4)]

        center_parts[1].bind('<Return>', update_spectrum)
        wid_parts[1].bind('<Return>', update_spectrum)

        self.params['nr_pixels']['var'].set(4)

        # -- Detector
        gui.add_to_grid(widg=center_parts, rows=[1, 2], cols=[1, 1], sticky=["ew", "ew"])  # center wavelength
        gui.add_to_grid(widg=wid_parts, rows=[1, 2], cols=[2, 2], sticky=["ew", "ew"])
        gui.add_to_grid(widg=time_parts, rows=[1, 2], cols=[3, 3], sticky=["ew", "ew"])
        #gui.add_to_grid(widg=det_no_parts, rows=[1, 2, 3, 4], cols=[0, 0, 0, 0], sticky=["ew", "ew", "ew", "ew"])  # nr of pixels

        return frm_configs

    def write_log(self, msg, **kwargs):
        print(msg)


class ETA:

    def __init__(self, parent):
        # TODO:  maybe make bins and binsize variable in code? or have txt file that we read/write from in settings (along with other defaults)
        self.parent = parent
        self.const = {
            'eta_format':    1,      # swabian = 1
            'eta_recipe':   '',
            'eta_recipe_corr':   'Code/ETARecipes/Correlation-swabian_spectrometer.eta',
            'eta_recipe_lifetime':   'Code/ETARecipes/Lifetime-swabian_spectrometer.eta',
            'eta_recipe_spectrum':   'Code/ETARecipes/Countrate-swabian_spectrometer.eta',
            'timetag_file': '', #'Data/ToF_Duck_10MHz_det1_det2_5.0ms_[2.1, 3.9, -3.2, -4.8]_100x100_231220.timeres',
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
        self.pb = None

        self.load_all_engines()

    def update_progressbar(self, n):
        if self.pb:
            if n == 0:
                self.pb['value'] = 0
                gui.root.update()  # testing

            elif self.pb['value'] <= 100:
                self.pb['value'] = n
                gui.root.update()  # testing
            else:
                self.parent.write_log(f"overshot progressbar: {n}")

    def load_eta(self, recipe, **kwargs):
        self.update_progressbar(n=0)
        gui.root.update()  # testing

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

        self.binsize_dict['counts'] = 10 * (10 ** 10)
        self.bins_dict['counts'] = (scantime * 0.1) * (10 ** 2)

        self.eta_engine_corr = self.load_eta(self.const["eta_recipe_corr"], bins=10000, binsize=20)
        self.eta_engine_lifetime = self.load_eta(self.const["eta_recipe_lifetime"], bins=125*5, binsize=20, det_delay = 12500)
        self.eta_engine_spectrum = self.load_eta(self.const["eta_recipe_spectrum"], bins=self.bins_dict['counts'], binsize=self.binsize_dict['counts'])

    def eta_lifetime_analysis(self):  # , const):

        self.folded_countrate_pulses = {}

        """# NOTE: MAYBE FIXME, MIGHT HAVE TO RELOAD RECIPE EVERY TIME!
        if self.const["eta_recipe"] != self.parent.params['eta_recipe']['var'].get():
            self.const["eta_recipe"] = self.parent.params['eta_recipe']['var'].get()
            self.eta_engine = self.load_eta(self.const["eta_recipe"], bins=self.const["bins"], binsize=self.const["binsize"])  # NOTE: removed for test
        """
        self.const["timetag_file"] = self.parent.params['file_name']['var'].get()

        # note: bins will be the same for all data channels
        bins_i = np.linspace(0, self.const['bins']+1, self.const['bins']+2)  # starting with 8 channels for now
        times_i = bins_i * self.const['binsize']   # time list in ps  (for one histogram)

        channels = ['h2', 'h3', 'h4']
        # fixme: we need to make sure that the channels matches what we have in the result dict
        self.folded_countrate_pulses = dict([(c, np.zeros(self.const['bins'])) for c in channels])

        # ------ETA PROCESSING OF ONE TIMERES FILE-----

        pulse_nr = 0
        pos = 0  # 0  # internal ETA tracker (-> maybe tracks position in data list?)
        context = None  # tracks info about ETA logic, so we can extract and process data with breaks (i.e. in parts)
        eta_format = self.const["eta_format"]   # eta_engine.FORMAT_SI_16bytes   # swabian = 1
        file = Path(self.const['timetag_file'])

        while True:
            # Extract histograms from eta
            file_clips = self.eta_engine.clips(filename=file, seek_event=pos, format=eta_format)
            result, context = self.eta_engine.run({"timetagger1": file_clips}, resume_task=context, return_task=True, group='quTAG', max_autofeed=1)

            if pulse_nr % 100 == 0:
                if self.parent.cancel:
                    self.parent.write_log(f"Cancelled Analysis")
                    return
                self.update_progressbar(n=pulse_nr/100)

            # Check if we've run out of data, otherwise update position
            if result['timetagger1'].get_pos() == pos:  # or (pos is None):
                self.parent.write_log(f"final pulse nr: {pulse_nr}")
                break
            else:
                pulse_nr += 1
                pos = result['timetagger1'].get_pos()

            # Folding histogram counts for each channel:
            for c in channels:
                self.folded_countrate_pulses[c] += np.array(result[c])

        self.parent.write_log(f"Eta processing complete")
        self.lifetime_bins_ns = list(np.array(times_i) / 1000)  # changing values from picoseconds to nanoseconds

        # -----

        wavelens = self.get_wavelengths()

        for c, channel in enumerate(self.folded_countrate_pulses.keys()):
            peak_idx = self.find_peak_idx(self.folded_countrate_pulses[channel])

            self.pix_dict[channel] = {
                'name': 'c' + channel,
                'wavelength': wavelens[c],  # computed
                #'color': self.ch_colors[c % len(self.ch_colors)],
                'color': gui.CIE_colors.get_rgb(wavelens[c]),
                'counts': sum(self.folded_countrate_pulses[channel]),  # sum of channel
                'peak idx': peak_idx,
                'lifetime': self.lifetime_bins_ns[peak_idx],  # calculated max value
            }

        return

    # ---------------------------------

    def new_correlation_analysis(self, ax=None, file=None):  # correlation

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

    def new_tof_analysis(self, ax=None, file=None):
        # note: hardcoded values set by theo # TODO FIXME
        bins = 125*5
        binsize = 20

        #bins_i = np.linspace(0, bins + 1, bins + 2)  # starting with 8 channels for now
        #self.lifetime_bins_ns = list(np.array(bins_i * binsize) / 1000)  # changing values from picoseconds to nanoseconds

        if not file:
            file = self.parent.params['file_name']['var'].get()

        cutfile = self.eta_engine_lifetime.clips(filename=file, format=1)
        result = self.eta_engine_lifetime.run({"timetagger1": cutfile}, group='swabian')  # Runs the time tagging analysis and generates histograms

        self.lifetime_bins_ns = time_axis = np.arange(bins) * binsize

        channels = ['h4', 'h2', 'h3']

        #max_val = np.max([np.max(result[c]) for c in channels])
        #self.folded_countrate_pulses = dict([(c, result[c]/max_val) for c in channels])
        self.folded_countrate_pulses = dict([(c, result[c]) for c in channels])

        # --TODO CHECK BELOW--
        wavelens = self.get_wavelengths()

        for c, channel in enumerate(self.folded_countrate_pulses.keys()):
            peak_idx = self.find_peak_idx(self.folded_countrate_pulses[channel])

            self.pix_dict[channel] = {
                'name': 'c' + channel,
                'wavelength': wavelens[c],  # computed
                # 'color': self.ch_colors[c % len(self.ch_colors)],
                'color': gui.CIE_colors.get_rgb(wavelens[c]),
                'counts': sum(self.folded_countrate_pulses[channel]),  # sum of channel
                'peak idx': peak_idx,
                'lifetime': self.lifetime_bins_ns[peak_idx],  # calculated max value
            }

        #return ax

    def new_countrate_analysis(self, file=None):
        # ETA Settings
        #binsize = 200   # 20
        #bins = 1000

        time_axis = np.arange(0, self.bins_dict['counts']) * self.binsize_dict['counts']

        if not file:
            file = self.parent.params['file_name']['var'].get()

        print(f'Starting ETA correlation analysis on file: {file}')
        cut = self.eta_engine_spectrum.clips(Path(file), format=1)
        result = self.eta_engine_spectrum.run({"timetagger1": cut}, group='swabian')
        print('Finished ETA analysis')

        print(result.keys())

        return time_axis / (10**12), result

     #TODO FIX TODO
    def new_spectrum_analysis(self, file=None):
            # ETA Settings
            binsize = 20
            bins = 10000

            time_axis = np.arange(0, bins) * binsize

            delta_t = np.arange(-bins, bins) * binsize * 1e-3
            if not file:
                file = self.parent.params['file_name']['var'].get()

            print(f'Starting ETA correlation analysis on file: {file}')
            cut = self.eta_engine_corr.clips(Path(file), format=1)
            result = self.eta_engine_corr.run({"timetagger1": cut}, group='swabian')
            print('Finished ETA analysis')

    def new_signal_counter_analysis(self):
        pass

    # ---------------------------------

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

        return x_centers

    def find_peak_idx(self, data):
        return np.where(data == np.max(data))[0][0]

class ColorMatchingCIE:
    # source/inspo: https://www.baeldung.com/cs/rgb-color-light-frequency
    def __init__(self):
        self.wavelengths = {}
        self.wavelengths_simple = {}

        for wl in np.arange(350, 750):
            self.wavelengths[wl] = self.get_rgb(wl)   # CIE
            self.wavelengths_simple[wl] = self.get_simple_rgb(wl)   # simplified (not CIE)

    def get_rgb(self, wavelength):
        def get_X(wavelen):
            # X is considered to represent the hue and saturation on the red-green axis.
            if wavelen < 442.0:
                factor1 = 0.0624
            else:
                factor1 = 0.0374

            if wavelen < 599.8:
                factor2 = 0.0264
            else:
                factor2 = 0.0323

            if wavelen < 501.1:
                factor3 = 0.0490
            else:
                factor3 = 0.0382

            Xt1 = (wavelen - 442.0) * factor1
            Xt2 = (wavelen - 599.8) * factor2
            Xt3 = (wavelen - 501.1) * factor3

            return (0.362 * np.exp(-0.5 * (Xt1 ** 2))) + (1.056 * np.exp(-0.5 * (Xt2 ** 2))) - (0.065 * np.exp(-0.5 * (Xt3 ** 2)))

        def get_Y(wavelen):
            # Y is considered to represent the luminosity.
            if wavelen < 568.8:
                factor1 = 0.0213
            else:
                factor1 = 0.0247
            if wavelen < 530.9:
                factor2 = 0.0613
            else:
                factor2 = 0.0322
            Yt1 = (wavelen - 568.8) * factor1
            Yt2 = (wavelen - 530.9) * factor2

            return (0.821 * np.exp(-0.5 * (Yt1 ** 2))) + (0.286 * np.exp(-0.5 * (Yt2 ** 2)))

        def get_Z(wavelen):
            # Z is considered to represent the hue and saturation on the blue-yellow axis.
            if wavelen < 437.0:
                factor1 = 0.0845
            else:
                factor1 = 0.0278
            if wavelen < 459.0:
                factor2 = 0.0385
            else:
                factor2 = 0.0725

            Zt1 = (wavelen - 437.0) * factor1
            Zt2 = (wavelen - 459.0) * factor2

            return (1.217 * np.exp(-0.5 * (Zt1 ** 2))) + (0.681 * np.exp(-0.5 * (Zt2 ** 2)))

        def calc_rgb(X, Y, Z):
            # calculate raw RBG values
            r_factors = [3.2406255, -1.537208, -0.4986286]
            g_factors = [-0.9689307, 1.8757561, 0.0415175]
            b_factors = [0.0557101, -0.2040211, 1.0569959]

            R_raw = r_factors[0]*X + r_factors[1]*Y + r_factors[2]*Z
            G_raw = g_factors[0]*X + g_factors[1]*Y + g_factors[2]*Z
            B_raw = b_factors[0]*X + b_factors[1]*Y + b_factors[2]*Z

            return R_raw, G_raw, B_raw

        def gamma_correction(value):
            # apply gamma correction and convert them to 0-255 range
            if value <= 0:
                return 0
            elif value <= 0.0031308:
                return round(255*value*12.92)
            elif value <= 1:
                return round(255 * (1.055 * (value**(1/2.4)) - 0.055 ))
            else:
                return 255

        X = get_X(wavelength)
        Y = get_Y(wavelength)
        Z = get_Z(wavelength)
        #print(X, Y, Z)
        R_raw, G_raw, B_raw = calc_rgb(X, Y, Z)
        #print(R_raw, G_raw, B_raw)

        R = gamma_correction(R_raw)
        G = gamma_correction(G_raw)
        B = gamma_correction(B_raw)
        #print(R, G, B)
        return '#{:02x}{:02x}{:02x}'.format(R, G, B)
        #return [R, B, G]

    def get_simple_rgb(self, wl):
        if 645 < wl <= 780:
            red = 1
            green = 0
            blue = 0
        elif 580 < wl <= 645:
            red = 1
            green = -(wl-645)/(645-580)  # FIXME -(wl-645)/(645/580)
            blue = 0
        elif 510 < wl <= 580:
            red = (wl-510)/(580-510)
            green = 1
            blue = 0
        elif 490 < wl <= 510:
            red = 0
            green = 1
            blue = -(wl-510)/(510-490)
        elif 440 < wl <= 490:
            red = 0
            green = (wl-440)/(490-440)
            blue = 1
        elif 380 < wl <= 440:
            red = -(wl-440)/(440-380)
            green = 0
            blue = 1
        else:
            red = 0
            green = 0
            blue = 0

        if 700 < wl <= 780:
            factor = 0.3 + (0.7*(780-wl)/(780-700))
        elif 420 < wl <= 700:
            factor = 1
        elif 380 < wl <= 420:
            factor = 0.3 + (0.7*(wl-380)/(420-380))
        else:
            factor = 0

        R = round(255*(red*factor)**0.8)
        G = round(255*(green*factor)**0.8)
        B = round(255*(blue*factor)**0.8)

        return '#{:02x}{:02x}{:02x}'.format(R, G, B)

# -------------

# TODO:
ch5_nm = 728.5
ch6_nm = 729.1
ch7_nm = 730.0

try:

    #sq = WebSQController(domain='http://130.237.35.62/')

    gui = GUI()
    #websqScanClass = WebSQGroup()
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
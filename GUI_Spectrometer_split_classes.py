import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, askdirectory
import serial
from serial.tools import list_ports
from datetime import date
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mat_col
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging

# from matplotlib import style
# from matplotlib.backend_bases import key_press_handler
from WebSQControl import WebSQControl
from test_data import example_data_blue, example_data_red
# Packages for ETA backend
import json
import etabackend.eta  # Available at: https://github.com/timetag/ETA, https://eta.readthedocs.io/en/latest/
import time
#import os
from pathlib import Path
from ttkthemes import ThemedTk

import platform  # for scrollable class
import colour
from colour import Color
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
import glob


# Grab and extend frames
# make whole notebook a scrollable frame (both horizontally and vertically)


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
        if platform.system() == 'Linux':
            self.canvas.bind_all("<Button-4>", self.onMouseWheel)
            self.canvas.bind_all("<Button-5>", self.onMouseWheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self.onMouseWheel)

    def onLeave(self, event):  # unbind wheel events when the cursorl leaves the control
        if platform.system() == 'Linux':
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
                x = [value for value in xar_b]

            elif unit == "f [Hz]":
                c = 2.99792458e9
                x = [c/(value*1e-9) for value in xar_b]

            elif unit == "E [eV]":
                x = [1240/value for value in xar_b]

            elif unit == "v [1/cm]":
                x = [1/(value_nm*1e-7) for value_nm in xar_b]

            else:
                self.parent.write_log(f"ERROR NOT FOUND")
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
        fig = plt.Figure(figsize=(8, 5), dpi=100)
        plot1 = fig.add_subplot(111)
        plot1.set_xlim(1545, 1565)
        plot1.set_ylim(0, 5000)
        line_b, = plot1.plot(xar_b, yar_b, 'b')  # , marker='o')
        #plot1.hist(yar_b, bins='auto')
        #N, bins, bars = plot1.hist(xar_b, weights=yar_b, rwidth=1, align='left')
        # TODO: make into histogram

        plot1.set_xlabel(self.x_label.get())
        plot1.set_ylabel("counts")
        plot1.set_title("Spectrum")

        plt_frame, canvas = gui.pack_plot(tab, fig)

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
        # TODO:
        # the figure that will contain the plot
        fig = plt.Figure(figsize=(8, 5), dpi=100)  # 10 3
        # data list
        y = []
        # adding the subplot
        plot1 = fig.add_subplot(111)
        # plotting the graph
        plot1.plot(y)

        plt_frame, canvas = gui.pack_plot(tab, fig)
        return plt_frame

    def plot_lifetime_widget(self, tab):

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
            self.scale_buttons = {
                #'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                'linear':       ttk.Button(butt_frame_p, text="  Linear  ", command=lambda: press_scale_plot('linear')),
                #'histo':      ttk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                'log':          ttk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
            }

            for i, thing in enumerate(self.scale_buttons.values()):
                #thing.grid(row=1+i, column=0, columnspan=2, sticky="ew")
                thing.grid(row=1+i, column=0, columnspan=1, sticky="ew")

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
            self.parent.write_log(f"final range list {range_list_int}")

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
                self.parent.write_log(f"Range if good, ok to plot")

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
                self.parent.write_log(f"SHOW DICT: {self.ch_show}")
                update_plot()

        def press_scale_plot(scale):
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

            b = self.parent.eta_class.bins_ns

            x = b[:-2]

            if time_min.get() >= time_max.get():
                time_min.set(time_max.get() - 1)  # note: to ensure the min < max

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

            for i, thing in enumerate(self.ch_show.keys()):
                if self.ch_show[thing] is False:
                    continue   # doesn't plot when hidden

                y = self.parent.eta_class.folded_countrate_pulses[thing]

                if scale == 'linear':
                    line_b, = ax1.plot(x[idx_min:idx_max], y[idx_min:idx_max], label='c' + thing, c=['red', 'orange', 'green', 'blue'][i%4])
                elif scale == 'log':
                    line_b, = ax1.semilogy(x[idx_min:idx_max], y[idx_min:idx_max], label='c' + thing, c=['red', 'orange', 'green', 'blue'][i%4])
                #elif scale == 'histo':
                #    N, bins, bars = ax1.hist(x[idx_min:idx_max], bins=b[idx_min:idx_max], weights=y[idx_min:idx_max], rwidth=1, align='left')

            if scale == 'log':
                if cnt_min.get() == 0.0:
                    cnt_min.set(1.0)

            ax1.set_xlim([time_min.get(), time_max.get()])
            ax1.set_ylim([cnt_min.get(), cnt_max.get()])
            ax1.set_xlabel("lifetime [ns]")
            ax1.set_title("Lifetime")

            ax1.legend()
            fig.canvas.draw_idle()   # updates the canvas immediately?

        self.ch_show = {'h1': True, 'h2': True, 'h3': True, 'h4': True}
        time_min = tk.DoubleVar(value=54.0)
        time_max = tk.DoubleVar(value=59.0)
        cnt_min = tk.DoubleVar(value=0.0)
        cnt_max = tk.DoubleVar(value=6000.0)

        range_list = tk.StringVar(value="2, 3")
        plot_mode = tk.StringVar(value="linear")
        self.show_buttons = []

        fig = plt.figure(figsize=(8, 5), dpi=100)   # fig, ax1 = plt.subplots(1, 1, figsize=(8, 5))

        update_plot()
        plt_frame, canvas = gui.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()

        plt_frame.grid(row=2, column=1, columnspan=1, sticky="news")
        butt_frm.grid(row=2, column=2, columnspan=1, sticky="news")
        #return plt_frame, butt_frm

    def plot_lifetime_colorbar_widget(self, tab):

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)

            butt_frame_t = ttk.Frame(butt_frame, borderwidth=1, relief=tk.FLAT)

            ttk.Label(butt_frame_t, text=f'\nAxis ranges:').grid(row=0, column=1, columnspan=2, sticky="ew")
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
            ttk.Entry(butt_frame_s, textvariable=range_list, width=5).grid(row=3, column=1, columnspan=1, sticky="new")

            ttk.Label(butt_frame_s, text="\nLine thickness:").grid(row=4, column=1, columnspan=2, sticky="new")
            ttk.Entry(butt_frame_s, textvariable=line_thickness, width=5).grid(row=5, column=1, columnspan=1, sticky="new")

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
                thing.grid(row=2+i, column=1, columnspan=1, sticky="ew")

            ttk.Label(butt_frame, text="\n").grid(row=4, column=0, sticky="ew")
            ttk.Button(butt_frame, text=f"Update", command=range_show).grid(row=5, column=0, columnspan=2, sticky="ew")
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
            self.parent.write_log(f"final range list {range_list_int}")

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
                self.parent.write_log(f"Range if good, ok to plot")

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
                self.parent.write_log(f"SHOW DICT: {self.ch_show}")
                update_plot()

        def press_scale_plot():
            scale = plot_mode.get()
            if scale == 'linear' and prev_plot_mode.get() == 'log':
                mn = y_min.get()
                mx = y_max.get()
                y_min.set(round(10**mn, 3))
                y_max.set(round(10**mx, 3))

            elif scale == 'log' and prev_plot_mode.get() == 'linear':
                mn = max(1.0, y_min.get())
                mx = max(1.0, y_max.get())
                y_min.set(round(np.log10(mn), 3))
                y_max.set(round(np.log10(mx), 3))

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

            b = self.parent.eta_class.bins_ns
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

            for i, thing in enumerate(self.ch_show.keys()):
                if self.ch_show[thing] is False:
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
                    mx = y_max.get()  # np.log10(y_max.get())
                    mn = y_min.get()  #np.log10(max(1.0, y_min.get()))
                    pre_counts = [max([1.0, c]) for c in self.parent.eta_class.folded_countrate_pulses[thing]]
                    counts = np.log10(pre_counts)

                    # ABSOLUTE FILTER
                    """for l in range(len(counts)):
                        if counts[l] > y_max.get():
                            counts[l] = 0.0
                        elif counts[l] < y_min.get():
                            counts[l] = 0.0"""
                    # ----

                else:
                    counts = self.parent.eta_class.folded_countrate_pulses[thing]
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
            for key in self.ch_show.keys():
                if self.ch_show[key]:
                    shown_ticks.append(f'ch.{key[1:]}')

            ticks = [i + 1 for i in range(len(shown_ticks))]
            ax1.set_yticks(ticks)
            ax1.set_yticklabels(shown_ticks)  # note: this will be the amount of channels we are displaying
            #y_max.set(len(ticks)+1)

            ax1.set_xlim([x_min.get(), x_max.get()])
            ax1.set_ylim([0.0, len(shown_ticks)+1.0])  # not applicable here anymore, used to change range on colorbar
            ax1.set_xlabel("time [ns]")
            ax1.set_title("Lifetime Color")
            #ax1.legend()
            fig.canvas.draw_idle()   # updates the canvas immediately?

        self.ch_show = {'h1': True, 'h2': True, 'h3': True, 'h4': True}
        x_min = tk.DoubleVar(value=0.0)
        x_max = tk.DoubleVar(value=100.0)
        y_min = tk.DoubleVar(value=0.0)
        y_max = tk.DoubleVar(value=2000.0)

        line_thickness = tk.DoubleVar(value=274.0)

        range_list = tk.StringVar(value="1-4")
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
            self.parent.write_log(f"final range list: {range_list_int}")

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
                self.parent.write_log(f"Range if good, ok to plot")

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

            ax1.set_xlabel("time [ns]")
            ax1.set_zlabel("counts")
            ax1.set_title("Spectrum")

            b = self.parent.eta_class.bins_ns
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
            ax1.set_xlabel("lifetime [ns]")
            ax1.set_title("3D Lifetime")
            #ax1.legend()
            fig.canvas.draw_idle()   # updates the canvas immediately?

        self.ch_show_3D = {'h1': True, 'h2': True, 'h3': True, 'h4': True}
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


    """def old_plot_3D_lifetime_widget(self, tab):
        # TODO:
        # the figure that will contain the plot
        #fig = plt.Figure(figsize=(10, 3), dpi=100)
        #y = []  # data list
        #plot1 = fig.add_subplot(111)  # adding the subplot
        #plot1.plot(y)  # plotting the graph
        fig, ax1 = plt.subplots(1, 1, figsize=(14, 7), subplot_kw={'projection': '3d'})

        #fig = plt.Figure(figsize=(8, 5), dpi=100)
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

        self.parent.write_log(f"x", X, type(X))
        self.parent.write_log(f"y", Y, type(Y))
        self.parent.write_log(f"z", Z, type(Z))

        # Give the second plot only wireframes of the type x = c
        #ax1.plot_wireframe(X, Y, Z, rstride=10, cstride=10)
        #ax1.plot_wireframe(X, Y, Z, rstride=0, cstride=10)  # only wireframes of the type x = c
        ax1.plot_wireframe(X, Y, Z, rstride=10, cstride=0)  # only wireframes of the type y = c

        ax1.set_title("3d lifetime")

        plt_frame, canvas = gui.pack_plot(tab, fig)
        return plt_frame"""

    """def old_plot_3D_lifetime_widget(self, tab):

        min_idx = 1000
        max_idx = 3000

        fig, ax1 = plt.subplots(1, 1, figsize=(8, 5), subplot_kw={'projection': '3d'})

        ax1.set_xlabel("time [ns]")
        #ax1.set_ylabel("channel")
        ax1.set_zlabel("counts")
        ax1.set_title("Spectrum")

        # x, bins shared data for all channels
        b = self.parent.eta_class.bins_ns
        x = b[:-2]

        X = x[min_idx:max_idx]   # note: dividing to get in nanoseconds
        N = len(X)  # number of data points per lifetime line   # FIXME to equal how many bins we have

        chs = ['h1', 'h2', 'h3', 'h4']
        nr_ch = len(chs)

        Y = np.ones(N) * int(N / nr_ch)

        for i, ch in enumerate(chs):   # NOTE: TEMP SOLUTION
            Z = self.parent.eta_class.folded_countrate_pulses[ch][min_idx:max_idx]
            ax1.plot(X, Y*i, Z, label='c'+ch)  # ax1.plot3D(X, Y, Z)

        ax1.set_yticks([int(N/nr_ch)*i for i in range(nr_ch)])
        ax1.set_yticklabels([f'ch.{j[1:]}' for j in chs])  # note: this will be the amount of channels we are displaying

        ax1.legend()

        ax1.set_title("3d lifetime")

        plt_frame, canvas = gui.pack_plot(tab, fig)
        return plt_frame
"""
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

'''class Logger:   # example from: https://stackoverflow.com/questions/30266431/create-a-log-box-with-tkinter-text-widget

    # this item "module_logger" is visible only in this module,
    # (but you can create references to the same logger object from other modules
    # by calling getLogger with an argument equal to the name of this module)
    # this way, you can share or isolate loggers as desired across modules and across threads
    # ...so it is module-level logging and it takes the name of this module (by using __name__)
    # recommended per https://docs.python.org/2/library/logging.html
    def __init__(self, tk_window):

        self.module_logger = logging.getLogger(__name__)

        # create Tk object instance
        app = self.simpleapp_tk(tk_window)

        # setup logging handlers using the Tk instance created above the pattern below can be used in other threads...
        #   to allow other thread to send msgs to the gui
        # in this example, we set up two handlers just for demonstration (you could add a fileHandler, etc)
        stderrHandler = logging.StreamHandler()  # no arguments => stderr
        self.module_logger.addHandler(stderrHandler)
        guiHandler = self.MyHandlerText(app.mytext)
        self.module_logger.addHandler(guiHandler)
        self.module_logger.setLevel(logging.INFO)

        # NOTE THIS IS HOW YOU LOG INTO THE BOX:  --> #self.module_logger.info("...some log text...")

    def simpleapp_tk(self, parent):
        #tk.Tk.__init__(self, parent)
        self.parent = parent

        #self.grid()

        self.mybutton = ttk.Button(parent, text="Test")
        self.mybutton.grid(row=0, column=1, sticky='ne')
        self.mybutton.bind("<ButtonRelease-1>", self.button_callback)

        """self.mybutton = tk.Button(parent, text="Clear")
        self.mybutton.grid(row=0, column=2, sticky='e')
        self.mybutton.bind("<ButtonRelease-1>", self.clear_button_callback)"""

        self.mytext = tk.Text(parent, state="disabled", height=15, width=30, wrap='word', background='#ffffff')
        self.mytext.grid(row=1, column=0, columnspan=3)

        return self

    def button_callback(self, event):
        now = time.strftime("%H:%M:%S", time.localtime())
        msg = "..."
        self.module_logger.info(f"({now})  ->  {msg}")

    class MyHandlerText(logging.StreamHandler):
        def __init__(self, textctrl):
            logging.StreamHandler.__init__(self)  # initialize parent
            self.textctrl = textctrl

        def emit(self, record):
            msg = self.format(record)
            self.textctrl.config(state="normal")
            self.textctrl.insert("end", msg + "\n")
            self.flush()
            self.textctrl.config(state="disabled")
            self.textctrl.see("end")
# TODO: ^ add clear button for logger'''

class GUI:

    def __init__(self):
        # Create and configure the main GUI window

        #self.root = tk.Tk()

        self.default_theme = 'radiance'
        self.root = ThemedTk(theme=self.default_theme)  # yaru is good i think

        print(self.root['cursor'])

        #path = '@duck.cur'  # Path to the image followed by @
        #path = '@troive_small.cur'  # Path to the image followed by @
        #path = '@try22.cur'  # Path to the image followed by @
        self.root['cursor'] = ''  # path  # Set the cursor

        self.root.title("OSQ - One Shot Quantum")   # *Ghosttly matters*
        self.root.geometry('1000x720')
        #self.root.geometry('1250x800')
        self.root.resizable(True, True)

        self.tabs = {
            'Load' : {
                #'tab': None,
                #'notebook' : None,
                'children' : {},
                },

            'New'  : {
                #'tab': None,
                #'notebook' : None,
                'children' : {},
                },

            'Settings'  : {
                #'tab': None,
                #'notebook' : None,
                'children' : {},
                }
        }
        self.theme_list = theme_list = [
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
        ]

        #self.cursor_list = cursor_list = ['']

        # Create root notebook
        #self.root_nb = self.add_notebook(parent_tab=self.root,  expand=1, fill="both")
        self.root_nb = self.add_notebook(parent_tab=self.root,  expand=1, fill="both", side='right')

        # Create parent tabs and pack into root notebook
        self.tabs['Load']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Load Scan')
        self.tabs['New']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='New Scan')
        self.tabs['Settings']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Settings')
        self.create_theme_sel(self.tabs['Settings']['tab'])  # self.root_nb)

    @staticmethod
    def pack_plot(tab, fig):

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = ttk.Frame(tab, relief=tk.FLAT, borderwidth=1)
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

    def init_fill_tabs(self):
        # Add acquisition Tabs for Load and New tabs

        # --------
        load_nb = self.add_notebook(parent_tab=self.tabs['Load']['tab'], anchor='w', side='top')

        # Create sub-notebooks for each tab and pack, then add children tabs
        self.tabs['Load']['notebook'] = self.add_notebook(parent_tab=self.tabs['Load']['tab'], anchor='w', side='top')
        #load_nb = self.tabs['Load']['notebook']
        self.tabs['Load']['children']['Lifetime Color'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime Color')
        self.tabs['Load']['children']['Lifetime'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime')
        #self.tabs['Load']['children']['Lifetime 3D'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime 3D')
        #self.tabs['Load']['children']['Spectrum'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Spectrum')
        #self.tabs['Load']['children']['Correlation'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Correlation')
        # --------
        new_nb = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top')
        # Create sub-notebooks for each tab and pack, then add children
        self.tabs['New']['notebook'] = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top')
        self.tabs['New']['children']['Lifetime Color'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Lifetime Color')
        self.tabs['New']['children']['Lifetime'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Lifetime')
        #self.tabs['New']['children']['Lifetime 3D'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Lifetime 3D')
        #self.tabs['New']['children']['Spectrum'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Spectrum')
        #self.tabs['New']['children']['Correlation'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Correlation')
        # --------
        self.tabs['Settings']['notebook'] = self.add_notebook(parent_tab=self.tabs['Settings']['tab'], anchor='w')
        # --------

        loadScanClass.acquisition_loadscan_tab(load_nb)   # adds in load params
        newScanClass.acquisition_newscan_tab(new_nb)

        #conf_frm = ttk.Frame(load_nb, relief=tk.FLAT)
        #option_thm = ttk.Label(conf_frm, text='TESTTT')
        #option_thm.grid(row=0, column=0)
        ##conf_frm.grid(row=4, column=100) #expand=1, anchor='ne')
        #load_nb.add(conf_frm, text='ssTESTTT')

    def create_theme_sel(self, tab):
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
                cursor_var.set(new_crs[9:-4])
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
        for file in glob.glob("cursors/*.cur"):
            cursor_list.append(f'{file}')

        cursor_var = tk.StringVar(value='default')
        option_cursor = ttk.OptionMenu(conf_frm, variable=cursor_var, default='')
        option_cursor.grid(row=1, column=1)

        option_cursor['menu'].add_command(label=f"default", command=lambda cur='': change_cursor(cur))
        for cursor in cursor_list:
            option_cursor['menu'].add_command(label=f"{cursor[8:-4]}", command=lambda cur=cursor: change_cursor(f'@{cur}'))

    def add_plot_tabs(self, parent_class, parent_name):
        # NOTE: CREATE NEW TAB THAT DOESN'T EXIST WITH:
        #child_tab = self.tabs[parent_name]['children']['example_plot1'] = self.add_tab(parent_nb=self.tabs[parent_name]['notebook'], tab_name='example_plot1')
        #plot_3d_lifetime_tab(child_tab, parent_class)
        # ----

        for tab_nm in self.tabs[parent_name]['children'].keys():
            gui.add_new_plot_tab(parent_class=parent_class, parent_name=parent_name, tab_name=tab_nm, init=True)
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
            if tab_name == 'Lifetime Color':
                self.tabs[parent_name]['children']['Lifetime Color'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Lifetime Color')

            elif tab_name == 'Lifetime':
                self.tabs[parent_name]['children']['Lifetime'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Lifetime')

            elif tab_name == 'Lifetime 3D':
                self.tabs[parent_name]['children']['Lifetime 3D'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Lifetime 3D')

            elif tab_name == 'Spectrum':
                self.tabs[parent_name]['children']['Spectrum'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Spectrum')

            elif tab_name == 'Correlation':
                self.tabs[parent_name]['children']['Correlation'] = self.add_tab(
                    parent_nb=self.tabs[parent_name]['notebook'], tab_name='Correlation')
            else:
                print(f"WARNING: ??? in function 'add_new_plot_tab()'")

        # ----
        if tab_name == 'Lifetime Color':
            self.plot_lifetime_color_tab(self.tabs[parent_name]['children']['Lifetime Color'], parent_class)

        elif tab_name == 'Lifetime':
            self.plot_lifetime_tab(self.tabs[parent_name]['children']['Lifetime'], parent_class)

        elif tab_name == 'Lifetime 3D':
            self.plot_3d_lifetime_tab(self.tabs[parent_name]['children']['Lifetime 3D'], parent_class)

        elif tab_name == 'Spectrum':
            self.plot_spectrum_tab(self.tabs[parent_name]['children']['Spectrum'], parent_class)

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
    def plot_3d_lifetime_tab(self, plots_3d_lifetime, parent):
        t_plt = parent.plotting_class.plot_3D_lifetime_widget(plots_3d_lifetime)
        t_plt.grid(row=2, column=1, columnspan=1, sticky="news")

    # **
    def plot_spectrum_tab(self, plots_spectrum, parent):
        parent.plotting_class.plot_spectrum_widget(plots_spectrum)
        info_frm = parent.plotting_class.plot_display_info_widget(plots_spectrum, "Spectrum plot info")
        info_frm.grid(row=0, rowspan=1, column=1, sticky="nsew")


    # **
    def plot_correlation_tab(self, plots_correlation, parent):
        # TODO: add widgets
        ttk.Label(plots_correlation, text='\nNOTHING TO SHOW YET. WORK IN PROGRESS...', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news")


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
            'nm':          {'var': tk.IntVar(value=1550), 'type': 'int entry', 'default': 350, 'value': [350, 650, 750]},
            'width_nm':    {'var': tk.IntVar(value=1),   'type': 'int entry', 'default': 10,  'value': [5, 15, 30]},
            'slit':        {'var': tk.IntVar(value=10),  'type': 'int entry', 'default': 10,  'value': [10, 20, 30]},
            'nr_pixels':   {'var': tk.IntVar(value=8),   'type': 'int entry', 'default': 8,   'value': [3, 8, 12]},
            'file_name':   {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},
            'folder_name': {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['~/Desktop/GUI/Data1', '~/Desktop/GUI/Data2', '~/Desktop/GUI/Data3']},
            'eta_recipe':  {'var': tk.StringVar(value='3D_2_channels_tof_swabian_marker_ch4.eta'), 'type': 'str entry', 'default': '',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }

        #self.data = []
        self.ch_bias_list = []
        self.pix_counts_list = []

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
        self.ch_bias_list = []
        self.ch_trig_list = []
        self.ch_nm_bin_edges = []  # TODO
        self.cumulative_ch_counts = []

    def acquisition_newscan_tab(self, new_scan_tab):

        # Full collection of settings for scan:
        self._params_frm = params_frm = ttk.Frame(new_scan_tab, borderwidth=1, relief=tk.FLAT)
        params_frm.grid(row=0, column=0, columnspan=2, sticky="nw")
        self.choose_param_configs_widget(params_frm).grid(row=0, column=0, sticky="ew")

        # ^
        #self.log_scan_widget(new_scan_tab).grid(row=1, column=1, rowspan=100, sticky="w")  # in sub frame
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

            self.write_log(f"pressed connect. fixme for real")
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

        def update_ch():
            nr_pixels = self.params['nr_pixels']['var'].get()
            if nr_pixels not in [4, 8, 16]:
                self.write_log(f"ERROR: other pixel amounts not available yet")
                return

            #self.write_log(f"Setting {nr_pixels} pixels")
            #self.params['nr_pixels']['var'].set(nr_pixels)

            scroll_frm = None  # placeholder
            # removes previously shown channels (in case we want to decrease in amount)
            for j, widget in enumerate(frm['ch'].winfo_children()):  # FIXME NOTE TODO: USE THIS LATER TO ACCESS BUTTONS FOR MARKING DONE
                #print(widget)
                if j == 4:
                    widget.destroy()
                    scroll_frm = CreateScrollFrame(frm['ch'])
                    scroll_frm.grid(row=1, column=0, columnspan=10)

            # Connecting to other/new WebSQ server   # TODO FIXME
            #self.sq.websq_disconnect()
            #self.sq.websq_connect(nr_pixels)
            fill_ch(scroll_frm)

        def fill_ch(scroll_frm):
            chosen_frm = scroll_frm.scrollFrame.viewPort
            self.ch_bias_list = []
            self.pix_counts_list = []

            demo = True
            if demo:
                device_bias = []
                device_trigger = []
                #self.params['nr_pixels']['var'].set(16)
                for ci in range(self.params['nr_pixels']['var'].get()):
                    device_bias.append(0)
                    device_trigger.append(100)
            else:
                device_bias = self.sq.get_curr_bias()
                device_trigger = self.sq.get_curr_trigger()

            for pix in range(self.params['nr_pixels']['var'].get()):
                self.ch_bias_list.append(tk.IntVar(value=device_bias[pix]))  # FIXME we are only displaying, not setting anything
                self.ch_trig_list.append(tk.IntVar(value=device_trigger[pix]))  # FIXME we are only displaying, not setting anything

                ttk.Label(chosen_frm, text=f"    {pix + 1}   ").grid(row=pix + 2, column=0, sticky="ew", padx=6)
                ttk.Entry(chosen_frm, textvariable=self.ch_bias_list[pix], width=6).grid(row=pix + 2, column=1, sticky="ew", padx=8)
                ttk.Entry(chosen_frm, textvariable=self.ch_trig_list[pix], width=8).grid(row=pix + 2, column=2, sticky="ew", padx=7)

                # ttk.Label(frm['ch'], text=f"0").grid(row=pix + 2, column=3, sticky="ew")  # counts
                c_temp = ttk.Label(chosen_frm, text=f"0")
                c_temp.grid(row=pix + 2, column=3, sticky="ew", padx=9)  # counts
                self.pix_counts_list.append(c_temp)

        #self.port.set(self.sp.port)  # note maybe change later when implemented

        # FRAMES
        frm_configs = ttk.Frame(tab, relief=tk.FLAT)#, borderwidth=1)

        frm = {
            'port'    : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            'slit'    : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            'grating' : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            'detect'  : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
            'ch'      : ttk.Frame(frm_configs, relief=tk.GROOVE, borderwidth=3) ,
        }

        # WIDGETS

        #  -- Slit:
        slt_parts = [ttk.Label(frm['slit'], text='Slit width'),
                     ttk.Entry(frm['slit'], textvariable=self.params['slit']['var'], width=4),
                     ttk.Label(frm['slit'], text='[um]')]

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
        det_parts = [ttk.Label(frm['detect'], text="Center λ (nm)"),
                     ttk.Entry(frm['detect'], textvariable=self.params['nm']['var'], width=4),
                     ]

        wid_parts = [ttk.Label(frm['detect'], text="Pixel width"),
                     ttk.Entry(frm['detect'], textvariable=self.params['width_nm']['var'], width=4),
                     ttk.Label(frm['detect'], text='[nm]')]

        self.params['nr_pixels']['var'].set(4)
        det_no_parts = [ttk.Label(frm['detect'], text="Nr. of channels"),
                        ttk.Radiobutton(frm['detect'], text="4", value=4, variable=self.params['nr_pixels']['var'], command=update_ch),
                        ttk.Radiobutton(frm['detect'], text="8", value=8, variable=self.params['nr_pixels']['var'], command=update_ch),
                        ttk.Radiobutton(frm['detect'], text="16", value=16, variable=self.params['nr_pixels']['var'], command=update_ch),
                        ]

        # -- Channels:
        ch_parts = [
            ttk.Label(frm['ch'], text='Channel'),
            ttk.Label(frm['ch'], text='Bias (uA)'),
            ttk.Label(frm['ch'], text='    Trigger (mV)'),
            ttk.Label(frm['ch'], text='  Counts')]

        scroll_frm = CreateScrollFrame(frm['ch'])
        scroll_frm.grid(row=1, column=0, columnspan=10)
        fill_ch(scroll_frm)

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
        gui.add_to_grid(widg=slt_parts, rows=[0, 1, 1], cols=[0, 0, 1], sticky=["", "", ""])
        # -- Grating
        gui.add_to_grid(widg=grating_widget_dict['radio_b'], rows=[3, 4, 5],    cols=[0, 0, 0],    sticky=["s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['grt_txt'], rows=[2, 3, 4, 5], cols=[1, 1, 1, 1], sticky=["", "s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['blz_txt'], rows=[2, 3, 4, 5], cols=[2, 2, 2, 2], sticky=["", "s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['wid_txt'], rows=[2, 3, 4, 5], cols=[3, 3, 3, 3], sticky=["", "s", "s", "s"])

        # -- Detector
        gui.add_to_grid(widg=[ttk.Label(frm['detect'], text="Detector")], rows=[0], cols=[0], sticky=["ew"])  # , columnspan=[2])
        gui.add_to_grid(widg=det_parts, rows=[1, 2], cols=[1, 1], sticky=["ew", "ew"])  # center wavelength
        # gui.add_to_grid(widg=wid_parts, rows=[2,2,2], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        gui.add_to_grid(widg=det_no_parts, rows=[1, 2, 3, 4], cols=[0, 0, 0, 0], sticky=["ew", "ew", "ew", "ew"])  # nr of pixels

        # -- Channels
        gui.add_to_grid(widg=ch_parts, rows=[0, 0, 0, 0, 0], cols=[0, 1, 2, 3, 4], sticky=["ew", "ew", "ew", "ew"])

        #fill_ch()  # Updates channels displayed

        # ------------- GRID FRAMES --------------
        # labels for each part:
        gui.add_to_grid(widg=[frm['port'], frm['grating'], frm['slit'], frm['detect'], frm['ch']],
                        cols=[1, 2, 3, 4, 5], rows=[1, 1, 1, 1, 1],
                        sticky=["news", "news", "news", "news", "news"])

        ttk.Label(frm_configs, text="Monochromator", relief=tk.GROOVE, anchor='center').grid(row=0, column=0, columnspan=4, sticky='ew')
        ttk.Label(frm_configs, text="SNSPD", relief=tk.GROOVE, anchor='center').grid(row=0, column=4, columnspan=2, sticky='ew')

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
        reci_btn = ttk.Button(frm_anal_configs, text="ETA recipe", command=get_recipe)
        file_entry = ttk.Entry(frm_anal_configs, textvariable=self.params['file_name']['var'], width=60)
        reci_entry = ttk.Entry(frm_anal_configs, textvariable=self.params['eta_recipe']['var'], width=60)

        file_btn.grid(row=1, column=0, sticky="ew")
        reci_btn.grid(row=2, column=0, sticky="ew")
        file_entry.grid(row=1, column=1, columnspan=10, sticky="ew")
        reci_entry.grid(row=2, column=1, columnspan=10, sticky="ew")

        return frm_anal_configs

    def analysis_newscan_widget(self, tab):

        def press_analyze():
            try:
                self.cancel = False
                self.loading = True
                analyze_btn.config(state='disabled')
                self.write_log(f"Starting analysis")  # NOTE
                self.eta_class.eta_lifetime_analysis()
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
        self.eta_class.pb = ttk.Progressbar(frm_anal_buttons, style='bar.Horizontal.TProgressbar',
                                            orient='horizontal', mode='determinate', length=430) # 400)  # progressbar

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
            'nm':          {'var': tk.IntVar(value=600), 'type': 'int entry', 'default': 350, 'value': [350, 650, 750]},
            'width_nm':    {'var': tk.IntVar(value=1),   'type': 'int entry', 'default': 10,  'value': [5, 15, 30]},
            'slit':        {'var': tk.IntVar(value=10),  'type': 'int entry', 'default': 10,  'value': [10, 20, 30]},
            'nr_pixels':   {'var': tk.IntVar(value=8),   'type': 'int entry', 'default': 8,   'value': [3, 8, 12]},
            'file_name':   {'var': tk.StringVar(value="Data/ToF_Duck_10MHz_det1_det2_5.0ms_[2.1, 3.9, -3.2, -4.8]_100x100_231220.timeres"), 'type': 'str entry', 'default': '...',  'value': ['butterfly.timeres', 'frog.timeres', 'sheep.timeres']},
            'eta_recipe':  {'var': tk.StringVar(value="3D_2_channels_tof_swabian_marker_ch4.eta"), 'type': 'str entry', 'default': '...',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
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
                self.eta_class.eta_lifetime_analysis()
                start_btn.config(state='normal')
                option_plt['state'] = 'normal'

                self.loading = False

                if not self.cancel:
                    gui.add_plot_tabs(parent_class=self, parent_name='Load')
                    analyzed_file_label.config(text=f"Analyzed file: {self.params['file_name']['var'].get()}")
                else:
                    self.cancel = False

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
        frm_misc.grid(row=0, column=0)

        # shows which file we have analysed:
        analyzed_file_label = ttk.Label(frm_misc, text='', font="Helvetica 10 normal italic")
        analyzed_file_label.grid(row=4, column=1, columnspan=10, sticky='ew')
        # ----
        ttk.Button(frm_misc, text="Datafile", command=get_file).grid(row=1, column=0, sticky="ew")
        ttk.Button(frm_misc, text="ETA recipe", command=get_recipe).grid(row=2, column=0, sticky="ew")

        file_entry = ttk.Entry(frm_misc, textvariable=self.params['file_name']['var'], width=65)
        reci_entry = ttk.Entry(frm_misc, textvariable=self.params['eta_recipe']['var'], width=65)
        file_entry.grid(row=1, column=1, columnspan=10, sticky="ew")
        reci_entry.grid(row=2, column=1, columnspan=10, sticky="ew")

        start_btn = ttk.Button(frm_misc, text="Analyze", command=press_start)
        start_btn.grid(row=3, column=0, sticky="ew")

        stop_btn = ttk.Button(frm_misc, text="Cancel", command=press_stop)
        stop_btn.grid(row=3, column=2, sticky="ew")

        self.eta_class.pb = ttk.Progressbar(frm_misc, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=475)  # progressbar
        self.eta_class.pb.grid(row=3, column=3, sticky="ew")

        # -----
        new_plt_var = tk.StringVar(value='??')
        option_plt = ttk.OptionMenu(frm_misc, new_plt_var, '+', *get_plt_options(), command=press_add)
        option_plt.grid(row=4, column=0, sticky='w')
        option_plt['state'] = 'disabled'
        # ----

        # -------------
        # ---
        # Logger box:
        log_box_frm = ttk.Frame(tab, borderwidth=1, relief=tk.FLAT)
        log_box_frm.grid(row=0, column=1, rowspan=10, sticky="nws")  # in sub frame
        self.log_scan_widget(log_box_frm).grid(row=0, column=0, sticky="news")   # Inner thing

        # -----
        #self.show_geometry(params_frm, "Configs analysis top")
        #self.show_geometry(scan_frm, "Scan analysis left")
        #self.show_geometry(log_box_frm, "Log box right")
        #self.update_log_box_height()

    def log_scan_widget(self, tab):
        from tkinter import scrolledtext

        frm_log = ttk.Frame(tab, relief=tk.GROOVE)

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

        #self.log_box = log_box = scrolledtext.ScrolledText(frm_log, wrap=tk.WORD, width=48, height=6, font=("Helvetica", 12, 'italic'), state='disabled')
        self.log_box = log_box = scrolledtext.ScrolledText(frm_log, wrap=tk.WORD, width=30, height=6, font=("Helvetica", 12, 'italic'), state='disabled')
        log_box.grid(row=1, column=0, pady=0, padx=0)
        log_box.tag_config('error', foreground='red')  # <--  Change colors of texts tagged `error`
        log_box.tag_config('log', foreground='grey')  # <--  Change colors of texts tagged `log`

        return frm_log

    def write_log(self, msg, **kwargs):
        if kwargs:
            print("ERROR: COULD NOT WRITE EVERYTHING TO LOG, MSG MUST BE SENT AS ONE STRING")
            msg += ' ...\n...ERROR: COULD NOT WRITE EVERYTHING TO LOG, MSG MUST BE SENT AS ONE STRING'
            print("kwargs:", kwargs)
        self.log_box.configure(state='normal')
        self.log_box.insert('end', f'{time.strftime("%H:%M:%S", time.localtime())} - {msg}\n', 'log')
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


class ETA:

    def __init__(self, parent):
        # TODO:  maybe make bins and binsize variable in code? or have txt file that we read/write from in settings (along with other defaults)
        self.parent = parent
        self.const = {
            'eta_format':    1,      # swabian = 1
            'eta_recipe':   '', #'3D_2_channels_tof_swabian_marker_ch4.eta',   # 'lifetime_new_spectrometer_4_ch_lifetime.eta',
            'timetag_file': '', #'Data/ToF_Duck_10MHz_det1_det2_5.0ms_[2.1, 3.9, -3.2, -4.8]_100x100_231220.timeres',
            'bins':          5000,
            'binsize':       20,     # bin width in ps
            }
        self.folded_countrate_pulses = []
        self.bins_ns = []
        self.eta_engine = None
        self.pb = None

    def update_progressbar(self, n):
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

        self.parent.write_log(f"Recipe loaded!")

        return eta_engine

    def eta_lifetime_analysis(self):  # , const):

        self.folded_countrate_pulses = []

        # NOTE: MAYBE FIXME, MIGHT HAVE TO RELOAD RECIPE EVERY TIME!
        if self.const["eta_recipe"] != self.parent.params['eta_recipe']['var'].get():
            self.const["eta_recipe"] = self.parent.params['eta_recipe']['var'].get()
            self.eta_engine = self.load_eta(self.const["eta_recipe"], bins=self.const["bins"], binsize=self.const["binsize"])  # NOTE: removed for test

        self.const["timetag_file"] = self.parent.params['file_name']['var'].get()

        # note: bins will be the same for all data channels
        bins_i = np.linspace(0, self.const['bins']+1, self.const['bins']+2)  # starting with 8 channels for now
        times_i = bins_i * self.const['binsize']   # time list in ps  (for one histogram)

        channels = ['h1', 'h2', 'h3', 'h4']
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
        self.bins_ns = list(np.array(times_i) / 1000)  # changing values from picoseconds to nanoseconds
        return

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


# -------------

try:
    gui = GUI()
    newScanClass = NewScanGroup()
    loadScanClass = LoadScanGroup()
    gui.init_fill_tabs()
    gui.root.mainloop()

except:
    print("some exception")
    raise

finally:
    print('------\nExiting...')
    #if newScanClass:
    #    if newScanClass.sp:
    #        newScanClass.sp.acton_disconnect()  # closes connection with spectrometer
    #    if newScanClass.sq:
    #        newScanClass.sq.websq_disconnect()  # close SQWeb connection

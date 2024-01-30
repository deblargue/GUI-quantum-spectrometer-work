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
#import os
from pathlib import Path
from ttkthemes import ThemedTk

import platform  # for scrollable class


class ScrollFrame(tk.Frame):
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
        self.canvas = tk.Canvas(self, height=0, highlightthickness=0)  # place canvas on self
        self.viewPort = ttk.Frame(self.canvas)  # background="#ffffff"  # place a frame on the canvas, this frame will hold the child widgets
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

class CreateScrollFrame(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.scrollFrame = ScrollFrame(self)  # add a new scrollable frame.
        self.scrollFrame.grid(row=1, column=0, columnspan=10)

#    Example(root).pack(side="top", fill="both", expand=True)

# --------------

class Plotting:
    def __init__(self, parent):

        self.parent = parent
        self.y_max_entry = tk.StringVar()
        self.y_max = tk.IntVar(value=1000)
        self.x_label = tk.StringVar(value='λ [nm]')

        self.plots = {}  # TODO: save plot, axes, and frame handles for different plots
        # self.eta_class??? todo

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
        #plot1.hist(yar_b, bins='auto')
        #N, bins, bars = plot1.hist(xar_b, weights=yar_b, rwidth=1, align='left')
        # TODO: make into histogram

        plot1.set_xlabel(self.x_label.get())
        plot1.set_ylabel("counts")
        plot1.set_title("Spectrum")

        plt_frame, canvas = gui.pack_plot(tab, fig)

        # BUTTONS:
        butt_frame = ttk.Frame(tab, relief=tk.FLAT)

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
        fig = plt.Figure(figsize=(9, 5), dpi=100)  # 10 3
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
            butt_frame = ttk.Frame(tab, relief=tk.FLAT)

            butt_frame_t = ttk.Frame(butt_frame)

            ttk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            ttk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")

            ttk.Label(butt_frame_t, text=f'X').grid(row=2, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew")

            ttk.Label(butt_frame_t, text=f'Y').grid(row=3, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_min, width=6).grid(row=3, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_max, width=6).grid(row=3, column=2, sticky="ew")

            ttk.Button(butt_frame_t, text="Update", command=update_plot).grid(row=4, column=0, columnspan=3, sticky="ew", padx=0,  pady=0)

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT)

            ttk.Label(butt_frame_s, text="Show Channels:").grid(row=2, column=0, columnspan=2, sticky="ew")
            ttk.Entry(butt_frame_s, textvariable=range_list, width=6).grid(row=3, column=0, columnspan=1, sticky="ew")
            ttk.Button(butt_frame_s, text=f"Update range", command=range_show).grid(row=3, column=1, columnspan=1, sticky="ew")

            butt_frame_p = ttk.Frame(butt_frame, relief=tk.FLAT)
            ttk.Label(butt_frame_p, text=f'Plot scale').grid(row=0, column=0, columnspan=2, sticky="ew")
            self.scale_buttons = {
                #'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                'linear':       ttk.Button(butt_frame_p, text="  Linear  ", command=lambda: press_scale_plot('linear')),
                #'histo':      ttk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                'log':          ttk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
            }

            for i, thing in enumerate(self.scale_buttons.values()):
                #thing.grid(row=1+i, column=0, columnspan=2, sticky="ew", padx=0,  pady=0)
                thing.grid(row=1, column=i, columnspan=1, sticky="ew", padx=0,  pady=0)

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

            print(cnt_min.get(), cnt_max.get())
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

        fig = plt.figure(figsize=(9, 5), dpi=100)   # fig, ax1 = plt.subplots(1, 1, figsize=(9, 5))

        update_plot()
        plt_frame, canvas = gui.pack_plot(tab, fig)
        butt_frm = make_time_scale_button()

        plt_frame.grid(row=2, column=1, columnspan=1, sticky="news")
        butt_frm.grid(row=2, column=2, columnspan=1, sticky="news")
        #return plt_frame, butt_frm

    def plot_3D_lifetime_widget(self, tab):

        def make_time_scale_button():
            butt_frame = ttk.Frame(tab, relief=tk.FLAT)

            butt_frame_t = ttk.Frame(butt_frame)

            ttk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            ttk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")

            ttk.Label(butt_frame_t, text=f'X').grid(row=2, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew")

            ttk.Label(butt_frame_t, text=f'Y').grid(row=3, column=0, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_min, width=6).grid(row=3, column=1, sticky="ew")
            ttk.Entry(butt_frame_t, textvariable=cnt_max, width=6).grid(row=3, column=2, sticky="ew")

            ttk.Button(butt_frame_t, text="Update", command=update_plot).grid(row=4, column=0, columnspan=3, sticky="ew", padx=0,  pady=0)

            butt_frame_s = ttk.Frame(butt_frame, relief=tk.FLAT)

            ttk.Label(butt_frame_s, text="Show Channels:").grid(row=2, column=0, columnspan=2, sticky="ew")
            ttk.Entry(butt_frame_s, textvariable=range_list, width=6).grid(row=3, column=0, columnspan=1, sticky="ew")
            ttk.Button(butt_frame_s, text=f"Update range", command=range_show).grid(row=3, column=1, columnspan=1, sticky="ew")

            butt_frame_p = ttk.Frame(butt_frame, relief=tk.FLAT)
            ttk.Label(butt_frame_p, text=f'Plot scale').grid(row=0, column=0, columnspan=2, sticky="ew")
            self.scale_buttons_3D = {
                #'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                'linear':       ttk.Button(butt_frame_p, text="  Linear  ", command=lambda: press_scale_plot('linear')),
                #'histo':        ttk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                #'log':          ttk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
            }

            for i, thing in enumerate(self.scale_buttons_3D.values()):
                #thing.grid(row=1+i, column=0, columnspan=2, sticky="ew", padx=0,  pady=0)
                thing.grid(row=1, column=i, columnspan=1, sticky="ew", padx=0,  pady=0)

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
                for key in self.ch_show_3D.keys():
                    self.ch_show_3D[key] = False

                # set true for channels given in range
                for pair in range_list_int:
                    if len(pair) == 1:
                        self.ch_show_3D[f'h{pair[0]}'] = True
                    elif len(pair) == 2:
                        for idx in range(pair[0], pair[1]+1):
                            self.ch_show_3D[f'h{idx}'] = True
                print("SHOW DICT: ", self.ch_show_3D)
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
                #print(Z)
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

            """z_t = ax1.get_zticks()
            z_t = np.where(z_t > 1.0, 2**(z_t), 1.0)
            print(z_t)
            ax1.set_zticks(z_t)"""

            print(cnt_min.get(), cnt_max.get())
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

        #fig, ax1 = plt.subplots(1, 1, figsize=(9, 5), subplot_kw={'projection': '3d'})
        fig = plt.figure(figsize=(9, 5), dpi=100)   # fig, ax1 = plt.subplots(1, 1, figsize=(9, 5))
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

        plt_frame, canvas = gui.pack_plot(tab, fig)
        return plt_frame"""

    """def old_plot_3D_lifetime_widget(self, tab):

        min_idx = 1000
        max_idx = 3000

        fig, ax1 = plt.subplots(1, 1, figsize=(9, 5), subplot_kw={'projection': '3d'})

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

        frm_info = ttk.Frame(tab, relief=tk.FLAT)

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


class GUI:

    def __init__(self):
        # Create and configure the main GUI window
        #self.root = tk.Tk()
        # 0
        self.theme_list = theme_list = ['scidpurple',  # white purple nice
                      'arc',  # not great, too pale
                      'equilux', # nice grey/darkmode
                      'yaru', # nice and light, but buttons too big
                      'radiance', # reminds me of linux, soft beige
                      'plastik',  # nice, light grey/blue but looks a bit old
                      'default',  # very box-y and old
                      'scidpink',
                      'black',
                      'adapta',
                      'scidgreen',
                      'keramik',
                      'scidgrey',
                      'itft1',
                      'aqua', 'elegance', 'breeze', 'kroc', 'smog', 'blue', 'clam', 'scidmint',
                      'scidblue', 'alt', 'aquativo', 'classic', 'clearlooks', 'ubuntu', 'winxpblue', 'scidsand']


        self.root = ThemedTk(theme='radiance')  # yaru is good i think

        self.root.title("Quantum Spectrometer GUI - Ghostly matters")   # *Ghostly matters*
        self.root.geometry('1070x730')
        #self.root.geometry('1080x800')
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

        # Create root notebook
        #self.root_nb = self.add_notebook(parent_tab=self.root,  expand=1, fill="both")
        self.root_nb = self.add_notebook(parent_tab=self.root,  expand=1, fill="both", side='right')

        # Create parent tabs and pack into root notebook
        self.tabs['Load']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Load Scan')
        self.tabs['New']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='New Scan')
        self.tabs['Settings']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Settings')
        self.create_theme_sel()

    @staticmethod
    def pack_plot(tab, fig):

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = ttk.Frame(tab, relief=tk.FLAT)
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
        child_tab = ttk.Frame(parent_nb)
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
        loadScanClass.acquisition_loadscan_tab(load_nb)   # adds in load params
        # Create sub-notebooks for each tab and pack, then add children tabs
        self.tabs['Load']['notebook'] = self.add_notebook(parent_tab=self.tabs['Load']['tab'], anchor='w', side='top')
        self.tabs['Load']['children']['Spectrum'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Spectrum')
        self.tabs['Load']['children']['Lifetime'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime')
        self.tabs['Load']['children']['Lifetime 3D'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Lifetime 3D')
        self.tabs['Load']['children']['Correlation'] = self.add_tab(parent_nb=self.tabs['Load']['notebook'], tab_name='Correlation')

        # --------
        new_nb = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top')
        newScanClass.acquisition_newscan_tab(new_nb)
        newScanClass.analysis_newscan_tab(new_nb)
        # Create sub-notebooks for each tab and pack, then add children
        self.tabs['New']['notebook'] = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top')
        self.tabs['New']['children']['Plot1'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot1')
        self.tabs['New']['children']['Plot2'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot2')
        self.tabs['New']['children']['Plot3'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot3')
        self.tabs['New']['children']['Plot4'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot4')

        # --------
        self.tabs['Settings']['notebook'] = self.add_notebook(parent_tab=self.tabs['Settings']['tab'], anchor='w')

        # ---- CHOOSING THEME ----
        #self.theme_var = tk.StringVar(value='yaru')
        #option_thm = ttk.OptionMenu(self.tabs['Settings']['notebook'], variable=self.theme_var, default="yaru")
        #option_thm.grid(row=0, column=0)
        #for theme in self.theme_list:
        #    option_thm['menu'].add_command(label=f"{theme}", command=lambda thm=theme: self.change_theme(thm))

    def create_theme_sel(self):
        def change_theme(new_thm):
            print("changed to theme:", new_thm)
            self.root.set_theme(new_thm)
            thm_var.set(new_thm)

        thm_var = tk.StringVar(value="yaru")
        option_thm = ttk.OptionMenu(self.root_nb, variable=thm_var, default="radiance")
        option_thm.pack(expand=1, anchor='ne')
        for theme in self.theme_list:
            option_thm['menu'].add_command(label=f"{theme}", command=lambda thm=theme: change_theme(thm))

    def add_plot_tabs(self, parent_class, parent_name):
        # NOTE: CREATE NEW TAB THAT DOESN'T EXIST WITH:
        #child_tab = self.tabs[parent_name]['children']['example_plot1'] = self.add_tab(parent_nb=self.tabs[parent_name]['notebook'], tab_name='example_plot1')
        #plot_3d_lifetime_tab(child_tab, parent_class)
        # ----

        self.plot_spectrum_tab(self.tabs[parent_name]['children']['Spectrum'], parent_class)  # note: temp moved to front for testing
        self.plot_lifetime_tab(self.tabs[parent_name]['children']['Lifetime'], parent_class)  # note: temp moved to front for testing
        self.plot_3d_lifetime_tab(self.tabs[parent_name]['children']['Lifetime 3D'], parent_class)  # note: temp moved to front for testing
        self.plot_correlation_tab(self.tabs[parent_name]['children']['Correlation'], parent_class)  # note: temp moved to front for testing

    # **
    def plot_lifetime_tab(self, plots_lifetime, parent):
        parent.plotting_class.plot_lifetime_widget(plots_lifetime)

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
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], ipadx=5, ipady=0, columnspan=columnspan[i])
            else:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], ipadx=2, ipady=0, padx=1, pady=1)

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
            'nm':          {'var': tk.IntVar(value=600), 'type': 'int entry', 'default': 350, 'value': [350, 650, 750]},
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
            1: {'grating': 600,  'blz': '750 nm', 'width': 8},
            2: {'grating': 150,  'blz': '800 nm', 'width': 4},
            3: {'grating': 1800, 'blz': 'H-VIS',  'width': 2},
        }
        self.ch_bias_list = []
        self.ch_trig_list = []
        self.ch_nm_bin_edges = []  # TODO
        self.cumulative_ch_counts = []

    def acquisition_newscan_tab(self, new_scan_tab):

        # Param config
        self.choose_param_configs_widget(new_scan_tab)

        # TODO: Move live histo to new tab FIXME
        #live_plt, button_frame = parent.plotting_class.plot_live_histo(new_scan_tab)
        #live_plt.grid(row=2, column=1, columnspan=1, sticky="news")
        #button_frame.grid(row=2, column=2, columnspan=1, sticky="news")

        start_tab = ttk.Frame(new_scan_tab, relief=tk.FLAT)   # frame to gather things to communicate with devices
        start_tab.grid(row=0, column=1, columnspan=1, sticky="news")
        #tk.Label(start_tab, text='Device Communication', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news")
        #newScanClass.choose_file_configs_widget(start_tab).grid(row=1, column=0, sticky="news")  # in sub frame
        #newScanClass.send_param_configs_widget(start_tab).grid(row=1, column=1, sticky="news")  # in sub frame
        self.start_scan_widget(new_scan_tab).grid(row=9, column=0, sticky="news")  # in sub frame

    # TODO: FIXME BELOW (make sure it connects and does right)
    def start_scan_widget(self, tab):

        def press_start():
            print(self.sp.sp_handle)
            print(self.sq.websq_handle)
            if (not self.sp.sp_handle) or (not self.sq.websq_handle):
                print("Can not start scan if we are not connected")
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

        frm_send = ttk.Frame(tab, relief=tk.FLAT)
        btn_start = ttk.Button(frm_send, text="Start Scan", command=press_start)
        btn_stop = ttk.Button(frm_send, text="Stop", command=press_stop)
        self.prog_bar = ttk.Progressbar(frm_send, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=500)  # progressbar

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
                #    # print(f"FOUND ACTON DEVICE ON PORT {port.device}")
                #    return port.device

                """print(f'---------\n'
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
            if port_parts['disconnect']['state'] == 'normal':
                print("Please disconnect first")
                return
            # Update chosen port and allow connection (if not connected^)
            self.port.set(port)
            port_parts['connect'].config(state='normal')

        # TODO:
        def press_connect():  # TODO
            # self.running = False  # TODO CHECK: need to stop scanning i think???
            if self.port.get() == "Select...":
                print("MUST SELECT PORT FIRST")

            print("pressed connect. fixme for real")
            print("connecting to port", self.port.get())

            #if demo:
            #    Demo.d_connect(port_parts['connect'])  # changes color of button to green
            #    self.sp.sp_handle = True
            #    return

            # TODO CONNECTION....
            # if connect successful:
            port_parts['label'].config(text=f'Connected to {self.port.get()}')
            port_parts['disconnect'].config(state='normal')
            port_parts['connect'].config(state='disabled')
            port_parts['refresh'].config(state='disabled')

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
            print("pressed disconnect. fixme for real")
            print("disconnecting from port", self.port.get())

            # TODO DO DISCONNECT....

            # if successful:
            port_parts['label'].config(text='')
            port_parts['connect'].config(state='normal')
            port_parts['disconnect'].config(state='disabled')
            port_parts['refresh'].config(state='normal')

            """if self.sp is None:
                self.init_sp()
            self.sp.acton_disconnect()   # ????
            """

        def select_grating():
            # FIXME OR REMOVE
            # self.calculate_nm_bins()
            # TODO: auto update plot axis
            pass

        def update_ch(nr_pixels):
            if nr_pixels not in [4, 8]:
                print("ERROR: other pixel amounts not available yet")
                return

            self.params['nr_pixels']['var'].set(nr_pixels)

            # TODO: FIXME
            # removes previously shown channels (in case we want to decrease in amount)
            for j, widget in enumerate(frm['ch'].winfo_children()):  # FIXME NOTE TODO: USE THIS LATER TO ACCESS BUTTONS FOR MARKING DONE
                if j == 0:
                    pass #print(widget)
                print(j, widget)
                print(widget.winfo_children())

            # Connecting to other/new WebSQ server
            #
            #self.sq.websq_disconnect()
            #self.sq.websq_connect(nr_pixels)
            #self.plotting_class.reset_histo_bins()
            fill_ch()

        def fill_ch():
            chosen_frm = scroll_frm.scrollFrame.viewPort
            self.ch_bias_list = []
            self.pix_counts_list = []

            demo = True
            if demo:
                device_bias = []
                device_trigger = []
                self.params['nr_pixels']['var'].set(16)
                for ci in range(self.params['nr_pixels']['var'].get()):
                    device_bias.append(0)
                    device_trigger.append(100)
            else:
                device_bias = self.sq.get_curr_bias()
                device_trigger = self.sq.get_curr_trigger()

            for pix in range(self.params['nr_pixels']['var'].get()):
                self.ch_bias_list.append(tk.IntVar(value=device_bias[pix]))  # FIXME we are only displaying, not setting anything
                self.ch_trig_list.append(tk.IntVar(value=device_trigger[pix]))  # FIXME we are only displaying, not setting anything

                ttk.Label(chosen_frm, text=f"{pix + 1}").grid(row=pix + 2, column=0, sticky="ew", padx=6)
                ttk.Entry(chosen_frm, textvariable=self.ch_bias_list[pix], width=6).grid(row=pix + 2, column=1, sticky="ew", padx=8)
                ttk.Entry(chosen_frm, textvariable=self.ch_trig_list[pix], width=8).grid(row=pix + 2, column=2, sticky="ew", padx=7)

                # ttk.Label(frm['ch'], text=f"0").grid(row=pix + 2, column=3, sticky="ew", padx=0, pady=0)  # counts
                c_temp = ttk.Label(chosen_frm, text=f"0")
                c_temp.grid(row=pix + 2, column=3, sticky="ew", padx=9)  # counts
                self.pix_counts_list.append(c_temp)

        # ---------------
        #self.port.set(self.sp.port)  # note maybe change later when implemented

        # FRAMES
        frm_test = ttk.Frame(tab, relief=tk.FLAT)
        frm_test.grid(row=0, column=0, sticky="news")

        frm = {
            'port'    : ttk.Frame(frm_test, relief=tk.GROOVE) ,
            'slit'    : ttk.Frame(frm_test, relief=tk.GROOVE) ,
            'grating' : ttk.Frame(frm_test, relief=tk.GROOVE) ,
            'detect'  : ttk.Frame(frm_test, relief=tk.GROOVE) ,
            'ch'      : ttk.Frame(frm_test, relief=tk.GROOVE)  ,
        }

        scroll_frm = CreateScrollFrame(frm['ch'])
        scroll_frm.grid(row=1, column=0, columnspan=10)
        fill_ch()

        # WIDGETS

        #  -- Slit:
        slt_parts = [ttk.Label(frm['slit'], text='Slit width'),
                     ttk.Entry(frm['slit'], textvariable=self.params['slit']['var'], width=5),
                     ttk.Label(frm['slit'], text='[um]')]

        #  -- Grating:
        grating_widget_dict = {
            'radio_b': [],
            'grt_txt': [ttk.Label(frm['grating'], text='Grating')],
            'blz_txt': [ttk.Label(frm['grating'], text='Blaze')],
            'wid_txt': [ttk.Label(frm['grating'], text='Width')],
        }
        for c in range(3):
            grating_widget_dict['radio_b'].append(ttk.Radiobutton(frm['grating'], text="", variable=self.params['grating']['var'], value=c + 1, command=select_grating))
            grating_widget_dict['grt_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['grating']}  [gr/mm]"))
            grating_widget_dict['blz_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['blz']}"))
            grating_widget_dict['wid_txt'].append(ttk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['width']}"))

        #  -- Detector:
        det_parts = [ttk.Label(frm['detect'], text="Center λ"),
                     ttk.Entry(frm['detect'], textvariable=self.params['nm']['var'], width=4),
                     ttk.Label(frm['detect'], text='[nm]', width=4)]

        wid_parts = [ttk.Label(frm['detect'], text="Pixel width"),
                     ttk.Entry(frm['detect'], textvariable=self.params['width_nm']['var'], width=6),
                     ttk.Label(frm['detect'], text='[nm]')]

        det_no_parts = [ttk.Label(frm['detect'], text="Nr. of pixels"),
                        ttk.Button(frm['detect'], text="4", command=lambda: update_ch(4)),
                        ttk.Button(frm['detect'], text="8", command=lambda: update_ch(8))]

        # -- Channels:
        ch_parts = [
            ttk.Label(frm['ch'], text='Pixel'),
            ttk.Label(frm['ch'], text='Bias (uA)'),
            ttk.Label(frm['ch'], text='    Trigger (mV)'),
            ttk.Label(frm['ch'], text='  Counts')]

        #  -- Port:
        get_ports()
        port_parts = { 'refresh'        : ttk.Button(frm['port'], text="Refresh Devices", command=refresh_ports),
                       'option'         : ttk.OptionMenu(frm['port'], variable=self.port, default="Select..."),
                       'connect'        : ttk.Button(frm['port'], text="Connect", command=press_connect, state='disabled'),
                       'disconnect'     : ttk.Button(frm['port'], text="Disconnect", command=press_disconnect, state='disabled'),
                       'label': ttk.Label(frm['port'], text=f''),
                       }

        # Populate the dropdown menu with the list of options
        for port_name in self.port_list:
            port_parts['option']['menu'].add_command(label=f"{port_name}", command=lambda opt=port_name: select_port(opt))

        # GRID
        # -- Port
        port_parts['refresh'].grid(row=0, column=0, sticky='ew')
        port_parts['option'].grid(row=1, column=0, columnspan=2, sticky='ew')
        port_parts['connect'].grid(row=2, column=0, sticky='ew')
        port_parts['disconnect'].grid(row=2, column=1, sticky='ew')
        port_parts['label'].grid(row=3, column=0, columnspan=4,  sticky='ew')
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
        gui.add_to_grid(widg=det_parts, rows=[1, 1, 1], cols=[0, 1, 2], sticky=["ew", "ew", "ew"])
        # gui.add_to_grid(widg=wid_parts, rows=[2,2,2], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        gui.add_to_grid(widg=det_no_parts, rows=[3, 3, 3], cols=[0, 1, 2], sticky=["ew", "ew", "ew"])

        # -- Channels
        gui.add_to_grid(widg=ch_parts, rows=[0, 0, 0, 0, 0], cols=[0, 1, 2, 3, 4], sticky=["ew", "ew", "ew", "ew"])

        #fill_ch()  # Updates channels displayed

        # ------------- GRID FRAMES --------------
        gui.add_to_grid(widg=[frm['port'], frm['grating'], frm['slit'], frm['detect'], frm['ch']],
                        cols=[1, 2, 3, 4, 5], rows=[0, 0, 0, 0, 0],
                        sticky=["news", "news", "news", "news", "news"])
        return frm_test

    def analysis_newscan_tab(self, tab):

        def press_analyze():
            try:
                self.cancel = False
                self.loading = True
                analyze_btn.config(state='disabled')

                self.eta_class.eta_lifetime_analysis()
                analyze_btn.config(state='normal')
                self.loading = False

                if not self.cancel:
                    gui.add_plot_tabs(parent_class=self, parent_name='Load')
                    analyzed_file_label.config(text=f"Analyzed file: {self.params['file_name']['var'].get()}")
                else:
                    self.cancel = False

            except:
                print("Failed to analyze")
                raise

        def press_cancel():
            if self.loading:
                self.cancel = True
                self.eta_class.pb['value'] = 0

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

        frm_misc = ttk.Frame(tab)
        frm_misc.grid(row=10, column=0, sticky="ew", columnspan=10)

        # shows which file we have analysed:
        analyzed_file_label = ttk.Label(frm_misc, text='', font="Helvetica 10 normal italic")
        analyzed_file_label.grid(row=10, column=0, columnspan=10, sticky='ew')
        # ----
        ttk.Button(frm_misc, text="Datafile  ", command=suggest_filename).grid(row=1, column=0, sticky="ew")
        ttk.Button(frm_misc, text="ETA recipe", command=get_recipe).grid(row=2, column=0, sticky="ew")

        file_entry = ttk.Entry(frm_misc, textvariable=self.params['file_name']['var'], width=100)
        reci_entry = ttk.Entry(frm_misc, textvariable=self.params['eta_recipe']['var'], width=100)
        file_entry.grid(row=1, column=1, columnspan=10, sticky="ew")
        reci_entry.grid(row=2, column=1, columnspan=10, sticky="ew")

        analyze_btn = ttk.Button(frm_misc, text="Analyze", command=press_analyze)
        cancel_btn = ttk.Button(frm_misc, text="Cancel", command=press_cancel)
        analyze_btn.grid(row=3, column=0, sticky="ew")
        cancel_btn.grid(row=3, column=1, sticky="ew")

        self.eta_class.pb = ttk.Progressbar(frm_misc, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=500)  # progressbar
        self.eta_class.pb.grid(row=3, column=2, sticky="ew")

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
                self.eta_class.eta_lifetime_analysis()
                start_btn.config(state='normal')
                self.loading = False

                if not self.cancel:
                    gui.add_plot_tabs(parent_class=self, parent_name='Load')
                    analyzed_file_label.config(text=f"Analyzed file: {self.params['file_name']['var'].get()}")
                else:
                    self.cancel = False

            except:
                print("Failed to analyze")
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

        frm_misc = ttk.Frame(tab)
        frm_misc.grid(row=0, column=0)

        # shows which file we have analysed:
        analyzed_file_label = ttk.Label(frm_misc, text='', font="Helvetica 10 normal italic")
        analyzed_file_label.grid(row=10, column=0, columnspan=10, sticky='ew')
        # ----
        ttk.Button(frm_misc, text="Datafile", command=get_file).grid(row=1, column=0, sticky="ew")
        ttk.Button(frm_misc, text="ETA recipe", command=get_recipe).grid(row=2, column=0, sticky="ew")

        file_entry = ttk.Entry(frm_misc, textvariable=self.params['file_name']['var'], width=100)
        reci_entry = ttk.Entry(frm_misc, textvariable=self.params['eta_recipe']['var'], width=100)
        file_entry.grid(row=1, column=1, columnspan=10, sticky="ew")
        reci_entry.grid(row=2, column=1, columnspan=10, sticky="ew")

        start_btn = ttk.Button(frm_misc, text="Analyze", command=press_start)
        start_btn.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.eta_class.pb = ttk.Progressbar(frm_misc, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=500)  # progressbar
        self.eta_class.pb.grid(row=3, column=2, sticky="ew")

        stop_btn = ttk.Button(frm_misc, text="Cancel", command=press_stop)
        stop_btn.grid(row=3, column=3, columnspan=2, sticky="ew")


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
            print("overshot progressbar: ", n)

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

        print("\nRecipe loaded!")
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
                    print("Cancelled Analysis")
                    return
                self.update_progressbar(n=pulse_nr/100)

            # Check if we've run out of data, otherwise update position
            if result['timetagger1'].get_pos() == pos:  # or (pos is None):
                print("final pulsenr", pulse_nr)
                break
            else:
                pulse_nr += 1
                pos = result['timetagger1'].get_pos()

            # Folding histogram counts for each channel:
            for c in channels:
                self.folded_countrate_pulses[c] += np.array(result[c])

        print("DONE")
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

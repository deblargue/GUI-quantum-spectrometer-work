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
        #plot1.hist(yar_b, bins='auto')
        #N, bins, bars = plot1.hist(xar_b, weights=yar_b, rwidth=1, align='left')
        # TODO: make into histogram

        plot1.set_xlabel(self.x_label.get())
        plot1.set_ylabel("counts")
        plot1.set_title("Spectrum")

        plt_frame, canvas = gui.pack_plot(tab, fig)

        # BUTTONS:
        butt_frame = tk.Frame(tab, relief=tk.FLAT, bd=2)

        tk.Label(butt_frame, text=f'Change X-axis to:').grid(row=0, column=0, sticky="nsew")
        tk.Radiobutton(butt_frame, text="wavelength [nm]", value='λ [nm]', variable=self.x_label, command=pressed_xlabel).grid(row=1, column=0, sticky="ew")
        tk.Radiobutton(butt_frame, text="frequency [Hz]", value='f [Hz]', variable=self.x_label, command=pressed_xlabel).grid(row=2, column=0, sticky="ew")
        tk.Radiobutton(butt_frame, text="photon energy [eV]", value='E [eV]', variable=self.x_label, command=pressed_xlabel).grid(row=3, column=0, sticky="ew")
        tk.Radiobutton(butt_frame, text="wave number [cm^{-1}]", value='v [1/cm]', variable=self.x_label, command=pressed_xlabel).grid(row=4, column=0, sticky="ew")

        plt_frame.grid(row=0, rowspan=4, column=0, sticky="nsew")
        butt_frame.grid(row=3, column=1, sticky="nsew")
        #return plt_frame, butt_frame

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

        plt_frame, canvas = gui.pack_plot(tab, fig)
        return plt_frame

    def plot_lifetime_widget(self, tab):

        def make_time_scale_button():
            butt_frame = tk.Frame(tab, relief=tk.FLAT, bd=2)

            butt_frame_t = tk.Frame(butt_frame, bd=2)

            tk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            tk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")

            tk.Label(butt_frame_t, text=f'X').grid(row=2, column=0, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew")

            tk.Label(butt_frame_t, text=f'Y').grid(row=3, column=0, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=cnt_min, width=6).grid(row=3, column=1, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=cnt_max, width=6).grid(row=3, column=2, sticky="ew")

            tk.Button(butt_frame_t, text="Update", command=update_plot).grid(row=4, column=0, columnspan=3, sticky="ew", padx=0,  pady=0)

            butt_frame_s = tk.Frame(butt_frame, relief=tk.FLAT, bd=2)

            tk.Label(butt_frame_s, text="Show Channels:").grid(row=2, column=0, columnspan=2, sticky="ew")
            tk.Entry(butt_frame_s, bd=2, textvariable=range_list, width=6).grid(row=3, column=0, columnspan=1, sticky="ew")
            tk.Button(butt_frame_s, text=f"Update range", highlightbackground='white', command=range_show).grid(row=3, column=1, columnspan=1, sticky="ew")

            butt_frame_p = tk.Frame(butt_frame, relief=tk.FLAT, bd=2)
            tk.Label(butt_frame_p, text=f'Plot scale').grid(row=0, column=0, columnspan=2, sticky="ew")
            self.scale_buttons = {
                'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                #'histo':        tk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                'log':          tk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
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
                self.scale_buttons[type].config(highlightbackground=c)

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
            butt_frame = tk.Frame(tab, relief=tk.FLAT, bd=2)

            butt_frame_t = tk.Frame(butt_frame, bd=2)

            tk.Label(butt_frame_t, text=f'min').grid(row=1, column=1, sticky="ew")
            tk.Label(butt_frame_t, text=f'max').grid(row=1, column=2, sticky="ew")

            tk.Label(butt_frame_t, text=f'X').grid(row=2, column=0, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=time_min, width=6).grid(row=2, column=1, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=time_max, width=6).grid(row=2, column=2, sticky="ew")

            tk.Label(butt_frame_t, text=f'Y').grid(row=3, column=0, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=cnt_min, width=6).grid(row=3, column=1, sticky="ew")
            tk.Entry(butt_frame_t, bd=2, textvariable=cnt_max, width=6).grid(row=3, column=2, sticky="ew")

            tk.Button(butt_frame_t, text="Update", command=update_plot).grid(row=4, column=0, columnspan=3, sticky="ew", padx=0,  pady=0)

            butt_frame_s = tk.Frame(butt_frame, relief=tk.FLAT, bd=2)

            tk.Label(butt_frame_s, text="Show Channels:").grid(row=2, column=0, columnspan=2, sticky="ew")
            tk.Entry(butt_frame_s, bd=2, textvariable=range_list, width=6).grid(row=3, column=0, columnspan=1, sticky="ew")
            tk.Button(butt_frame_s, text=f"Update range", highlightbackground='white', command=range_show).grid(row=3, column=1, columnspan=1, sticky="ew")

            butt_frame_p = tk.Frame(butt_frame, relief=tk.FLAT, bd=2)
            tk.Label(butt_frame_p, text=f'Plot scale').grid(row=0, column=0, columnspan=2, sticky="ew")
            self.scale_buttons_3D = {
                'linear':       tk.Button(butt_frame_p, text="  Linear  ", highlightbackground='green', command=lambda: press_scale_plot('linear')),
                #'histo':        tk.Button(butt_frame_p, text="Linear (histo)", command=lambda: press_scale_plot('histo')),
                #'log':          tk.Button(butt_frame_p, text=" Semi-Log ", command=lambda: press_scale_plot('log')),
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

        frm_info = tk.Frame(tab, relief=tk.FLAT, bd=2)

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


class GUI:

    def __init__(self):
        # Create and configure the main GUI window
        #self.root = tk.Tk()
        self.root = ThemedTk(theme="yaru")  # arc
        self.root.title("Quantum Spectrometer GUI - Ghostly matters")   # *Ghostly matters*
        self.root.geometry('1200x800')

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
        self.root_nb = self.add_notebook(parent_tab=self.root, expand=1, fill="both")

        # Create parent tabs and pack into root notebook
        self.tabs['Load']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Load Scan')
        self.tabs['New']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='New Scan')
        self.tabs['Settings']['tab'] = self.add_tab(parent_nb=self.root_nb, tab_name='Settings')


    @staticmethod
    def pack_plot(tab, fig):

        # creating the Tkinter canvas containing the Matplotlib figure
        plt_frame = tk.Frame(tab, relief=tk.FLAT, bd=2)
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
    def add_scrollbar_v(parent_frame, widget):
        # create a scrollbar widget and set its command to the text widget
        scrollbar = ttk.Scrollbar(parent_frame, orient='vertical', command=widget.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        #  communicate back to the scrollbar
        widget['yscrollcommand'] = scrollbar.set

    @staticmethod
    def add_scrollbar_h(parent_frame, widget):
        # create a scrollbar widget and set its command to the text widget
        scrollbar = ttk.Scrollbar(parent_frame, orient='horizontal', command=widget.xview)
        scrollbar.grid(row=1, column=0, sticky=tk.EW)
        #  communicate back to the scrollbar
        widget['xscrollcommand'] = scrollbar.set

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
        # Create sub-notebooks for each tab and pack, then add children
        self.tabs['New']['notebook'] = self.add_notebook(parent_tab=self.tabs['New']['tab'], anchor='w', side='top')
        self.tabs['New']['children']['Plot1'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot1')
        self.tabs['New']['children']['Plot2'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot2')
        self.tabs['New']['children']['Plot3'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot3')
        self.tabs['New']['children']['Plot4'] = self.add_tab(parent_nb=self.tabs['New']['notebook'], tab_name='Plot4')

        # --------
        self.tabs['Settings']['notebook'] = self.add_notebook(parent_tab=self.tabs['Settings']['tab'], anchor='w')

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
        info_frm.grid(row=0, rowspan=3, column=1, sticky="nsew" )


    # **
    def plot_correlation_tab(self, plots_correlation, parent):
        # TODO: add widgets
        tk.Label(plots_correlation, text='\nNOTHING TO SHOW YET. WORK IN PROGRESS...', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news")


    @staticmethod
    def add_to_grid(widg, rows, cols, sticky, columnspan=None):
        for i in range(len(widg)):
            if columnspan:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], padx=0, pady=0, columnspan=columnspan[i])
            else:
                widg[i].grid(row=rows[i], column=cols[i], sticky=sticky[i], padx=0, pady=0)

    # -------

class NewScanGroup:
    def __init__(self):
        #self.demo_class = Demo()
        #self.eta_class = ETA()
        #self.plotting_class = Plotting(self)

        # class instances when connected
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
            'eta_recipe':  {'var': tk.StringVar(),       'type': 'str entry', 'default': '',  'value': ['~/Desktop/GUI/Recipe/gui_recipe_1.eta', '~/Desktop/GUI/Recipe/gui_recipe_2.eta', '~/Desktop/GUI/Recipe/gui_recipe_3.eta']},
        }

        #self.data = []
        self.ch_bias_list = []
        self.pix_counts_list = []

        self.device_grating = 1
        self.device_wavelength = 600
        self.port = tk.StringVar()     # note maybe change later when implemented

        self.running = False  # this tracks if we are running a scan (collecting counts from detector)
        self.demo_connect = False  # temp for demo to check if we've actually connected to device
        self.config_success = None   # None if not tried to configure yet
        self.checked_configs = False
        self.live_mode = True

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
        newScanClass.choose_param_configs_widget(new_scan_tab).grid(row=0, column=0, sticky="news")

        separator = ttk.Separator(new_scan_tab, orient='horizontal')
        separator.grid(row=1, column=0, sticky="news")


        # TODO: Move live histo to new tab FIXME
        #live_plt, button_frame = parent.plotting_class.plot_live_histo(new_scan_tab)
        #live_plt.grid(row=2, column=1, columnspan=1, sticky="news")
        #button_frame.grid(row=2, column=2, columnspan=1, sticky="news")

        #start_tab = tk.Frame(new_scan_tab, relief=tk.FLAT, bd=2)   # frame to gather things to communicate with devices
        #start_tab.grid(row=0, column=1, columnspan=1, sticky="news")
        #tk.Label(start_tab, text='Device Communication', font=('', 15)).grid(row=0, column=0, columnspan=4, sticky="news")
        #newScanClass.choose_file_configs_widget(start_tab).grid(row=1, column=0, sticky="news")  # in sub frame
        #newScanClass.send_param_configs_widget(start_tab).grid(row=1, column=1, sticky="news")  # in sub frame
        #newScanClass.start_scan_widget(start_tab).grid(row=1, column=2, sticky="news")  # in sub frame

    def choose_param_configs_widget(self, tab):

        def press_connect():  # TODO
            # self.running = False  # TODO CHECK: need to stop scanning i think???
            print("pressed connect. fixme for real")

            """
            if demo:
                Demo.d_connect(port_parts[2])
                self.sp.sp_handle = True
                return

            if self.sp is None:
                self.init_sp()

            self.sp.acton_disconnect()
            self.sp.acton_connect()

            self.sp.sp_handle.write(b'NO-ECHO\r')
            self.sp.wait_for_read()  # b'  ok\r\n'
            port_parts[1].config(text=f'{self.sp.port}')

            if self.sp.sp_handle.isOpen():
                gui.mark_done(port_parts[2], highlight="green", text_color='black', type='button')
            else:
                gui.mark_done(port_parts[2], highlight="red", text_color='black', type='button')"""

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

            # removes previously shown channels (in case we want to decrease in amount)
            for j, widget in enumerate(
                    frm['ch'].winfo_children()):  # FIXME NOTE TODO: USE THIS LATER TO ACCESS BUTTONS FOR MARKING DONE
                if j > 2:
                    widget.destroy()

            # Connecting to other/new WebSQ server
            self.sq.websq_disconnect()
            self.sq.websq_connect(nr_pixels)
            self.plotting_class.reset_histo_bins()
            fill_ch()

        def fill_ch():
            self.ch_bias_list = []
            self.pix_counts_list = []

            demo = True
            if demo:
                return

            device_bias = self.sq.get_curr_bias()
            device_trigger = self.sq.get_curr_trigger()

            for pix in range(self.params['nr_pixels']['var'].get()):
                self.ch_bias_list.append(
                    tk.IntVar(value=device_bias[pix]))  # FIXME we are only displaying, not setting anything
                self.ch_trig_list.append(
                    tk.IntVar(value=device_trigger[pix]))  # FIXME we are only displaying, not setting anything

                tk.Label(frm['ch'], text=f"{pix + 1}").grid(row=pix + 2, column=0, sticky="ew", padx=0, pady=0)
                tk.Entry(frm['ch'], bd=2, textvariable=self.ch_bias_list[pix], width=6).grid(row=pix + 2, column=1,
                                                                                             sticky="ew", padx=0,
                                                                                             pady=0)
                tk.Entry(frm['ch'], bd=2, textvariable=self.ch_trig_list[pix], width=6).grid(row=pix + 2, column=2,
                                                                                             sticky="ew", padx=0,
                                                                                             pady=0)

                # tk.Label(frm['ch'], text=f"0").grid(row=pix + 2, column=3, sticky="ew", padx=0, pady=0)  # counts
                c_temp = tk.Label(frm['ch'], text=f"0")
                c_temp.grid(row=pix + 2, column=3, sticky="ew", padx=0, pady=0)  # counts
                self.pix_counts_list.append(c_temp)

        # ---------------
        #self.port.set(self.sp.port)  # note maybe change later when implemented

        # FRAMES
        frm_test = tk.Frame(tab, relief=tk.FLAT, bd=2)
        frm = {}
        for name in ['default', 'port', 'slit', 'grating', 'detect', 'ch']:
            frm[name] = tk.Frame(frm_test, relief=tk.FLAT, bd=2)

        # WIDGETS

        #  -- Port:
        port_parts = [tk.Label(frm['port'], text='USB Port'),
                      # port_entry = tk.Entry(frm_port, bd=2, textvariable=self.port, width=5)   # FIXME later
                      tk.Label(frm['port'], text=f'{self.port.get()}'),
                      tk.Button(frm['port'], text="Connect Device", command=press_connect)]

        #  -- Slit:
        slt_parts = [tk.Label(frm['slit'], text='Slit width'),
                     tk.Entry(frm['slit'], bd=2, textvariable=self.params['slit']['var'], width=5),
                     tk.Label(frm['slit'], text='[um]')]

        #  -- Grating:
        grating_widget_dict = {
            'radio_b': [],
            'grt_txt': [tk.Label(frm['grating'], text='Grating')],
            'blz_txt': [tk.Label(frm['grating'], text='Blaze')],
            'wid_txt': [tk.Label(frm['grating'], text='Width')],
        }
        for c in range(3):
            grating_widget_dict['radio_b'].append(tk.Radiobutton(frm['grating'], text="", variable=self.params['grating']['var'], value=c + 1, command=select_grating))
            grating_widget_dict['grt_txt'].append(tk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['grating']}  [gr/mm]"))
            grating_widget_dict['blz_txt'].append(tk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['blz']}"))
            grating_widget_dict['wid_txt'].append(tk.Label(frm['grating'], text=f"  {self.grating_lvl[c + 1]['width']}"))

        #  -- Detector:
        det_parts = [tk.Label(frm['detect'], text="Center λ"),
                     tk.Entry(frm['detect'], bd=2, textvariable=self.params['nm']['var'], width=4),
                     tk.Label(frm['detect'], text='[nm]', width=4)]

        wid_parts = [tk.Label(frm['detect'], text="Pixel width"),
                     tk.Entry(frm['detect'], bd=2, textvariable=self.params['width_nm']['var'], width=6),
                     tk.Label(frm['detect'], text='[nm]')]

        det_no_parts = [tk.Label(frm['detect'], text="Nr. of pixels"),
                        tk.Button(frm['detect'], text="4", command=lambda: update_ch(4)),
                        tk.Button(frm['detect'], text="8", command=lambda: update_ch(8))]

        # -- Channels:
        ch_parts = [
            tk.Label(frm['ch'], text='Pixel'),
            tk.Label(frm['ch'], text='Bias (uA)'),
            tk.Label(frm['ch'], text='Trigger (mV)'),
            tk.Label(frm['ch'], text='Counts')]

        # GRID
        # -- Port
        gui.add_to_grid(widg=port_parts, rows=[0, 0, 0], cols=[0, 1, 2], sticky=["", "", ""])
        # -- Slit
        gui.add_to_grid(widg=slt_parts, rows=[0, 0, 0], cols=[0, 1, 2], sticky=["", "", ""])
        # -- Grating
        gui.add_to_grid(widg=grating_widget_dict['radio_b'], rows=[3, 4, 5], cols=[0, 0, 0],
                         sticky=["", "s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['grt_txt'], rows=[2, 3, 4, 5], cols=[1, 1, 1, 1],
                         sticky=["", "s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['blz_txt'], rows=[2, 3, 4, 5], cols=[2, 2, 2, 2],
                         sticky=["", "s", "s", "s"])
        gui.add_to_grid(widg=grating_widget_dict['wid_txt'], rows=[2, 3, 4, 5], cols=[3, 3, 3, 3],
                         sticky=["", "s", "s", "s"])

        # -- Detector
        gui.add_to_grid(widg=[tk.Label(frm['detect'], text="Detector")], rows=[0], cols=[0],
                         sticky=["ew"])  # , columnspan=[2])
        gui.add_to_grid(widg=det_parts, rows=[1, 1, 1], cols=[0, 1, 2], sticky=["ew", "ew", "ew"])
        # gui.add_to_grid(widg=wid_parts, rows=[2,2,2], cols=[0,1,2], sticky=["ew", "ew", "ew"])
        gui.add_to_grid(widg=det_no_parts, rows=[3, 3, 3], cols=[0, 1, 2], sticky=["ew", "ew", "ew"])

        # -- Channels
        gui.add_to_grid(widg=ch_parts, rows=[0, 0, 0, 0, 0], cols=[0, 1, 2, 3, 4], sticky=["ew", "ew", "ew", "ew"])
        fill_ch()  # Updates channels displayed

        # ------------- COMBINING INTO TEST FRAME --------------

        tk.Label(frm_test, text='Settings', font=('', 15)).grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        gui.add_to_grid(widg=[frm['default'], frm['port'], frm['slit'], frm['grating'], frm['detect']],
                         rows=[1, 2, 3, 4, 5], cols=[0, 0, 0, 0, 0], sticky=["ew", "ew", "ew", "ew", "ew"])
        frm['ch'].grid(row=6, column=0, rowspan=100, sticky="ew", padx=0, pady=0)

        return frm_test

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
                #file_entry.delete(0, tk.END)
                self.params['file_name']['var'].set(new_file)

        def get_recipe():
            new_reci = askopenfilename(filetypes=[("ETA recipe", "*.eta")])
            if new_reci:
                #reci_entry.delete(0, tk.END)
                self.params['eta_recipe']['var'].set(new_reci)

        frm_misc = tk.Frame(tab)
        frm_misc.grid(row=0, column=0)

        tk.Button(frm_misc, text="Datafile  ", command=get_file).grid(row=1, column=0, sticky="ew")
        tk.Button(frm_misc, text="ETA recipe", command=get_recipe).grid(row=2, column=0, sticky="ew")

        file_entry = tk.Entry(frm_misc, bd=2, textvariable=self.params['file_name']['var'], width=100)
        reci_entry = tk.Entry(frm_misc, bd=2, textvariable=self.params['eta_recipe']['var'], width=100)
        file_entry.grid(row=1, column=1, columnspan=10, sticky="ew")
        reci_entry.grid(row=2, column=1, columnspan=10, sticky="ew")

        start_btn = tk.Button(frm_misc, text="Analyze", command=press_start)
        start_btn.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.eta_class.pb = ttk.Progressbar(frm_misc, style='bar.Horizontal.TProgressbar', orient='horizontal', mode='determinate', length=300)  # progressbar
        self.eta_class.pb.grid(row=3, column=2, sticky="ew")

        stop_btn = tk.Button(frm_misc, text="Cancel", command=press_stop)
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

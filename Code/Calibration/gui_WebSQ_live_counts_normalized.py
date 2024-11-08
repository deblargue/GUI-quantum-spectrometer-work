import time
from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import sys
import asyncio
import signal
import struct
from sys import platform
import websockets
import numpy as np
from sklearn import cluster
import os


from Code.RetinaFiles.src.WebSQController import WebSQController

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
            #loop = asyncio.get_event_loop()
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

def create_retina_webserver():
    websq_domain = os.environ.get("WEBSQ_DOMAIN", 'http://localhost:8080/')
    sq = WebSQController(websq_domain)
    return sq

class LiveCounts:
    def __init__(self, base_url=None):
        if base_url:
            #loop = asyncio.get_event_loop()

            if base_url == 'http://localhost:8080/':   # TODO FIX
                self.sq = create_retina_webserver()

            loop.run_until_complete(websocket_client(base_url, self.get_active_channels, n=1))  # finds which channels we collect from Retina setup
            self.nr_chs = self.found_channels.shape[0]   # self.nr_chs = 24
            self.ch_numbers = self.found_channels.copy()  # FIXME
            self.active_chs = {}
            for i in self.found_channels:
                self.active_chs[i] = True

            self.X = np.array([i for i in self.ch_numbers]).reshape(-1, 1)  # for clustering
            self.reset_vars(n=10)   # TODO: check if we should use self.n below?
            loop.run_until_complete(websocket_client(base_url, self.get_live_counts, n=10))
        else:
            self.nr_chs = 24
            self.ch_numbers = np.arange(1, self.nr_chs + 1, 1)
            self.active_chs = {c: True for c in self.ch_numbers}
            self.X = np.array([i for i in self.ch_numbers]).reshape(-1, 1)  # for clustering
            self.reset_vars(n=5)

    def reset_vars(self, n):
        self.n = n
        #self.n = 30  # number of calibration measurements  # FIXME --> increase but remove print
        self.case = 'calibrate'
        self.cnter = 0
        self.norm_counter = 0

        #self.raw_counts = {k: 0 for k in self.ch_numbers}
        #self.norm_counts_per_ch = {k: 0 for k in self.ch_numbers}  # div by calibrated max average for given channel

        self.counts = {k: 0 for k in self.ch_numbers}  # FIXME: phase out
        self.copy_counts = {k: 0 for k in self.ch_numbers}  # FIXME: phase out
        self.calibration_counts_dict_lists = {k: [] for k in self.ch_numbers}
        self.averaged_calibration_counts = {k: 1 for k in self.ch_numbers}  # AVG OF ABOVE

        #print("done reset vars ")

    def get_live_counts(self, payload):

        self.payload = payload

        if self.case == 'running':

            for message in payload:  # for every channel

                if self.active_chs[message['rank']] is False:
                    self.counts[message['rank']] = 0
                else:
                    self.counts[message['rank']] = message['counts']

                self.copy_counts[message['rank']] = message['counts']  # this is just to display text even when channel is deactivated

                #thisapp._update()

        elif self.case == 'calibrate':

            if self.norm_counter == self.n:
                self.case = 'running'
                print("")
                try:
                    main.entry_calibrate.setText("")
                except:
                    pass

                for k in self.ch_numbers:
                    self.averaged_calibration_counts[k] = np.max([np.mean(self.calibration_counts_dict_lists[k]), 1.0])
            else:
                self.norm_counter += 1
                for message in payload:  # for every channel
                    if self.active_chs[message['rank']] is False:  # If the channel is inactive we don't collect counts
                        self.calibration_counts_dict_lists[message['rank']].append(0)
                    else:
                        self.calibration_counts_dict_lists[message['rank']].append(message['counts'])

            print(f"\r---sampling: {self.norm_counter}/{self.n}", end='')

        else:
            print("ERROR: WRONG CASE IN 'get_live_counts'")
            exit()

    def get_active_channels(self, payload):
        """
            # --> how to use this function: "loop.run_until_complete(websocket_client(base_url, live_counts.get_active_channels, n=1))"

            message['mcuId']        # this is the retina driver number (e.g. mcuId = 1 or 2, if we have 2 retinas)
            message['cuId']         # for each driver, which channel number (cuId is between 1-12)
            message['cuStatus']     # ????
            message['rank']         # channel number in total (e.g. with 2 retinas and 12 channels each: rank is between 1-24)
            message = {'mcuId': 1, 'cuId': 10, 'cuStatus': 0, 'monitorV': -0.0006128550739958882, 'biasI': 0.0, 'inttime': 100, 'counts': 0, 'rank': 10, 'time': 1729066371.8}
        """

        found_channels = []
        self.nr_chs = 0
        print("payload=", payload)
        for message in payload:  # for every channel
            #if len(found_channels) > 15:
            #    continue
            found_channels.append(message['rank'])
            print(message)
        try:
            self.int_time = message['inttime']
            print("int time:", self.int_time)
        except:
            pass

        found_channels.sort()
        self.found_channels = np.array(found_channels)

class MainWindow:

    def __init__(self):
        #super().__init__()  # THIS WAS TO INIT THE SUPERCLASS

        self.livecounts = LiveCounts(base_url=None)  # temporary class until we connect

        self.autoscale = False
        self.wavelengths = {i : i for i in self.livecounts.ch_numbers}
        self.acquired_wavelengths = False

        self.col_choice = [
            (0, 255, 0),  # green
            (0, 128, 255),  # medium blue
            (255, 0, 0),  # red
            (255, 0, 255),  # magenta
            (255, 255, 0),  # yellow
            (255, 128, 0),  # orange
            (0, 255, 255),  # cyan
            (127, 0, 255),  # purple
            (255, 0, 127),  # cerise
            (128, 128, 128),  # grey
            (128, 255, 0),  # yellow-green
            (0, 0, 255),  # dark blue
            (0, 255, 128),  # green-blue
        ]

        self.nr_colors = len(self.col_choice)

        # note: moved from main:
        self.view = QtWidgets.QWidget()
        self.initialize()  # Create interface
        self.view.showMaximized()
        self.view.show()

    def start_prog(self):
        # NOTE: MUST TRY TO CONNECT FIRST TO SERVER

        try:
            print("Trying to connect to:", self.entry_url.text())
            self.livecounts = LiveCounts(base_url=self.entry_url.text())
            self.base_url = self.entry_url.text()
            self.button_url.setDisabled(True)  # disable connect button if we succeed to connect
            self.entry_url.setReadOnly(True)   # disable connect entry text if we succeed to connect
            self.timer = QtCore.QTimer()
            self.timer.setInterval(100)
            self.timer.timeout.connect(self.update_plot)
            self.timer.start()

        except:
            print("FAILED TO CONNECT TO URL")
            raise

    def initialize(self):
        self.plot_window = pg.PlotWidget()
        self.pltitem = self.plot_window.plotItem
        self.ax_vb = self.pltitem.getViewBox()

        # ---- CREATE GRIDLAYOUT ------
        lay = QtWidgets.QGridLayout(self.view)  # view
        lay.setColumnStretch(0, 1)   # first column has relative width 1
        lay.setColumnStretch(1, 1)   # second column has relative width 1
        lay.setColumnStretch(2, 20)  # third column has much larger relative width to fit graph

        # ----- PLOT/BAR GRAPH WIDGET-----
        self.adjust_window()  # configure plot window
        # create histo item
        self.histo = pg.BarGraphItem(x=self.livecounts.ch_numbers, height=np.zeros(self.livecounts.nr_chs), width=0.6, brush='grey')
        self.plot_window.addItem(self.histo)  # add histo item to window
        #self.histo_colors = {i : 'g' for i in self.livecounts.ch_numbers}
        self.histo_colors = {i: 'grey' for i in self.livecounts.ch_numbers}   # set all to grey before changing

        #self.histo.setOpts(brushes=[self.histo_colors[ch] for ch in self.livecounts.ch_numbers])
        # note: it is added to grid at the end of this function

        # ----- CONNECT TO URL TEXT BOX -----  NEW!!
        self.entry_url = QtWidgets.QLineEdit()
        self.entry_url.setText("ws://130.237.35.20")
        self.entry_url.setPlaceholderText("WebSQ URL")
        lay.addWidget(self.entry_url, 0, 0, 1, 2)
        # --> CONNECT URL BUTTON
        self.button_url = QtWidgets.QPushButton(f"Connect to server")
        self.button_url.clicked.connect(self.start_prog)  # TODO FIXME
        lay.addWidget(self.button_url, 1, 0, 1, 2)

        # ------- RESET RANGE BUTTONS -----
        self.checkbox_auto = QtWidgets.QCheckBox("Auto Scale")
        self.checkbox_auto.toggled.connect(self.clicked_autoscale)
        lay.addWidget(self.checkbox_auto, 2, 0)


        # ------ TEXT INPUT MIN/MAX Y RANGE ------
        self.entry_max = entry_max = QtWidgets.QLineEdit()
        entry_max.editingFinished.connect(self.clicked_setYmax)
        validator_max = QtGui.QDoubleValidator()
        validator_max.setLocale(QtCore.QLocale("en_US"))  # this is to use period as decimal instead of comma
        entry_max.setValidator(validator_max)  # can be a float
        entry_max.setMaxLength(9)
        entry_max.setPlaceholderText("Y max")   # for max y-axis value
        lay.addWidget(entry_max, 2, 1)

        # ------- NORMALIZED
        self.checkbox_norm = QtWidgets.QCheckBox("Norm")
        self.checkbox_norm.toggled.connect(self.clicked_normalized)
        lay.addWidget(self.checkbox_norm, 3, 0)

        # ---- REDO CALIBRATION SAMPLING FOR AVERAGE -----
        self.entry_calibrate = QtWidgets.QLineEdit()
        self.entry_calibrate.editingFinished.connect(self.clicked_recalibrate)
        validator_sample = QtGui.QDoubleValidator()
        validator_sample.setLocale(QtCore.QLocale("en_US"))  # this is to use period as decimal instead of comma
        self.entry_calibrate.setValidator(validator_sample)
        self.entry_calibrate.setPlaceholderText("Sample time (s)")
        lay.addWidget(self.entry_calibrate, 4, 0, 1, 2)

        # ---- BUNCHING AVERAGES ---
        self.entry_bunch = entry_bunch = QtWidgets.QLineEdit()
        entry_bunch.editingFinished.connect(self.clicked_bunch)
        entry_bunch.textChanged.connect(self.changed_bunch)
        entry_bunch.setValidator(QtGui.QIntValidator(0, self.livecounts.nr_chs))  # can be a float
        entry_bunch.setPlaceholderText("Number of bunches")   # for max y-axis value
        lay.addWidget(entry_bunch, 5, 0, 1, 2)

        # ----- CHANNEL BUTTONS -----
        b_off = 6  # which row the first buttons should be
        self.ch_buttons = {}
        self.entry_lams = {}  # to save lamda entries
        self.text_counts = {}
        self.text_peaks = {}
        for i in self.livecounts.ch_numbers:
            butt = QtWidgets.QPushButton(f"ch.{i}")

            butt.setStyleSheet("background-color: green")

            self.ch_buttons[i] = butt
            butt.clicked.connect(lambda checked, i=i: self.toggle_ch(i))  # FIXMEadding signal and slot
            lay.addWidget(butt, b_off+1+i, 0)

            # ----- WAVELENGTH ENTRIES AND BUTTON

            entry_lam = QtWidgets.QLineEdit()
            validator = QtGui.QDoubleValidator(0.0, 99999.0, 1)
            validator.setLocale(QtCore.QLocale("en_US"))
            entry_lam.setValidator(validator)
            entry_lam.setText("")
            entry_lam.editingFinished.connect(self.clicked_fill_wavelengths)
            self.entry_lams[i] = entry_lam
            lay.addWidget(entry_lam, b_off+1+i, 1)

            # COUNTRATE FIGURE TEXT ON BARS
            new_text = pg.TextItem(text=f'-', color=(0, 0, 0), anchor=(0, 0.5), angle=90, rotateAxis=(1, 0))
            new_text.setPos(i, 0)
            self.text_counts[i] = new_text
            self.ax_vb.addItem(new_text)

            if True:
                #new_peak_text = pg.TextItem(text=f'', color=(0, 0, 0), anchor=(0.5, 0.5), # where in the text box that the setPos with anchor to
                #                        angle=45, rotateAxis=(1, 0))
                new_peak_text = pg.TextItem(text=f'', color=(0, 0, 0), anchor=(0.0, 0.5), angle=20, rotateAxis=(1, 0))
                new_peak_text.setPos(i, 1)
                self.text_peaks[i] = new_peak_text
                self.ax_vb.addItem(new_peak_text)
                if False:
                    new_peak_text.setFlag(new_peak_text.GraphicsItemFlag.ItemIgnoresTransformations)  #NEW
                    # ^^^ This line is necessary
                    # Use this instead of `plot.addItem`
                    new_peak_text.setParentItem(self.plot_window.plotItem)  # NEW
                    new_peak_text.setPos(300, 300)

        open_lams = QtWidgets.QPushButton(f"Open λs")
        open_lams.clicked.connect(self.clicked_open_wavelengths)  # TODO FIXME
        lay.addWidget(open_lams, b_off, 0)

        save_lams = QtWidgets.QPushButton(f"Save λs")
        save_lams.clicked.connect(self.clicked_save_wavelengths)    # TODO FIXME
        lay.addWidget(save_lams, b_off, 1)

        clear_lams = QtWidgets.QPushButton(f"Clear λs")
        clear_lams.clicked.connect(self.clicked_clear_wavelengths)
        lay.addWidget(clear_lams, b_off+1, 0)

        update_lams = QtWidgets.QPushButton(f"Set λs")
        update_lams.clicked.connect(self.clicked_update_wavelength)
        lay.addWidget(update_lams, b_off+1, 1)

        # --- ADDING PLOT LAST TO ENSURE IT FILLS UP ALL ROWS
        self.checkbox_auto.setChecked(True)
        self.checkbox_norm.setChecked(True)
        self.autoscale = True
        lay.addWidget(self.plot_window, 0, 2, lay.rowCount(), 1)  # note that columnstrech on this column is much larger (prev def)

        # CHANNELS THAT AREN'T FOUND WON'T BE ADDED
        for i in self.livecounts.active_chs.keys():
            if not self.livecounts.active_chs[i]:  # if not active toggle off
                self.text_counts[i].setColor((200, 200, 200))
                self.ch_buttons[i].setStyleSheet("background-color: grey")

    def adjust_window(self):
        #self.plot_window.setGeometry(QtCore.QRect(0, 0, 600, 100))      # (0, 0, 600, 500))        #NOTE THIS DICTATES WHERE BUTTONS ARE PLACED I THINK
        self.plot_window.setMouseEnabled(x=False, y=True)

        # self.plot_window.geometry().left()
        # self.plot_window.geometry().top()
        self.win_h = self.plot_window.geometry().height()
        self.win_w = self.plot_window.geometry().width()
        #print(self.plot_window.geometry())

        self.plot_window.setBackground("w")

        axes_styles = {"color": "black", "font-size": "16px"}
        self.plot_window.setLabel("left", "Counts", **axes_styles)
        self.plot_window.setLabel("bottom", "Channel", **axes_styles)

        self.ax = self.plot_window.getAxis('bottom')
        self.ax.setTicks([[(i, f'{i}') for i in self.livecounts.ch_numbers]])   # adjust plot/histo axis

        # self.plot_window.addLegend()
        self.plot_window.showGrid(x=True, y=True)

        self.plot_window.setXRange(0, self.livecounts.nr_chs+1, padding=0.0)
        #self.plot_window.getAxis('bottom').setRange(0, self.livecounts.nr_chs+1)   # (0, 13) when we had 12 chs

    def clicked_bunch_old(self):
        if self.entry_bunch.text() == "":
            pass
        else:
            try:
                # ---- K MEANS CLUSTERING ----
                n_bunch = int(eval(self.entry_bunch.text()))    # how many grouping we want

                X_weight = np.array([self.livecounts.counts[i] for i in self.livecounts.ch_numbers])
                X = np.array([self.wavelengths[i] for i in self.livecounts.ch_numbers]).reshape(-1, 1)   # NOTE CHANGED TO WL
                result = cluster.k_means(X=X, n_clusters=n_bunch, sample_weight=X_weight, n_init=15)

                #cluster_centers = result[0]         # [[98.76185137], [ 9.68747405], [61.48770616]]
                #cluster_membership = result[1]      # [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0]

                if True:
                    bunched_dict = {}
                    for thing in range(n_bunch):
                        bunched_dict[thing] = {'members': [], 'avg': round(result[0][thing][0], 5)}

                # FOR EACH CHANNEL
                for ch, parent_idx in enumerate(result[1]):
                    if self.livecounts.counts[ch+1] > 0:   # ...counts[...]
                        bunched_dict[parent_idx]['members'].append(ch+1)    # bunched_dict[int(round(result[0][mem][0]))]['members'].append(ch+1)

                    self.text_peaks[ch+1].setText("")  # reset text

                # Display the final text and assign colors
                for i in bunched_dict.keys():
                    try:
                        #print(bunched_dict)
                        peak_ch = int(np.mean(bunched_dict[i]['members']))
                        self.text_peaks[peak_ch].setText(
                            f"(chs.{np.min(bunched_dict[i]['members'])}-{np.max(bunched_dict[i]['members'])}) = "
                            f"{bunched_dict[i]['avg']}")
                        for ch in bunched_dict[i]['members']:
                            self.histo_colors[ch] = self.col_choice[i % self.nr_colors]
                    except:
                        print(bunched_dict[i]['members'])
                        raise

                # TODO FIX ME HERE: CRASHES AT LIKE 12 BUNCHES

            except:
                print("ERROR BUNCHING!")

                if int(eval(self.entry_bunch.text())) > self.livecounts.nr_chs:
                    self.entry_bunch.setText(f"{self.livecounts.nr_chs}")
                elif int(eval(self.entry_bunch.text())) <= 0:
                    self.entry_bunch.setText("1")
                else:
                    raise

    def clicked_bunch(self):
        if self.entry_bunch.text() == "":
            pass
        else:
            try:
                # ---- K MEANS CLUSTERING ----
                n_bunch = int(eval(self.entry_bunch.text()))    # how many grouping we want

                X_weight = np.array([self.livecounts.counts[i] for i in self.livecounts.ch_numbers])
                #X_weight = np.array([1 for i in self.livecounts.ch_numbers])

                X = np.array([
                    [self.wavelengths[i] for i in self.livecounts.ch_numbers]
                    #,[self.livecounts.copy_counts[i] for i in self.livecounts.ch_numbers]
                    ]).T  #.reshape(-1, 1)   # NOTE CHANGED TO WL

                result = cluster.k_means(X=X, n_clusters=n_bunch, sample_weight=X_weight, n_init=15)

                #cluster_centers = result[0]         # [[98.76185137], [ 9.68747405], [61.48770616]]
                #cluster_membership = result[1]      # [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0]

                if True:
                    bunched_dict = {}
                    for thing in range(n_bunch):
                        bunched_dict[thing] = {'members': [], 'avg': round(result[0][thing][0], 5)}

                # FOR EACH CHANNEL
                for ch, parent_idx in enumerate(result[1]):
                    if self.livecounts.counts[ch+1] > 0:   # ...counts[...]
                        bunched_dict[parent_idx]['members'].append(ch+1)    # bunched_dict[int(round(result[0][mem][0]))]['members'].append(ch+1)

                    self.text_peaks[ch+1].setText("")  # reset text

                # Display the final text and assign colors
                for i in bunched_dict.keys():
                    try:
                        #print(bunched_dict)
                        peak_ch = int(np.mean(bunched_dict[i]['members']))
                        self.text_peaks[peak_ch].setText(
                            f"(chs.{np.min(bunched_dict[i]['members'])}-{np.max(bunched_dict[i]['members'])}) = "
                            f"{bunched_dict[i]['avg']}")
                        for ch in bunched_dict[i]['members']:
                            self.histo_colors[ch] = self.col_choice[i % self.nr_colors]
                    except:
                        print(bunched_dict[i]['members'])
                        raise

                # TODO FIX ME HERE: CRASHES AT LIKE 12 BUNCHES

            except:
                print("ERROR BUNCHING!")

                if int(eval(self.entry_bunch.text())) > self.livecounts.nr_chs:
                    self.entry_bunch.setText(f"{self.livecounts.nr_chs}")
                elif int(eval(self.entry_bunch.text())) <= 0:
                    self.entry_bunch.setText("1")
                else:
                    raise

    def changed_bunch(self):
        for i in self.livecounts.ch_numbers:
            self.text_peaks[i].setText("")

        self.histo_colors = {i: 'grey' for i in self.livecounts.ch_numbers}   # set all to grey before changing
        # self.histo_colors = ['g' for _ in self.livecounts.ch_numbers]

        if self.entry_bunch.text() != "":
            for i in self.livecounts.ch_numbers:
                self.text_peaks[i].setPos(self.wavelengths[i], 0.8*self.plot_window.getViewBox().viewRange()[1][1])

            self.clicked_bunch()  # this will calculate the bunches and potentially change self.histo_colors

        # Apply any color changes if needed
        self.histo.setOpts(brushes=[self.histo_colors[ch] for ch in self.livecounts.ch_numbers])

    def clicked_save_wavelengths(self):
        try:
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(None, "Save File", "", "Text Files(*.txt)")
            if file_name:
                if file_name.endswith('.txt'):
                    with open(file_name, 'w') as f:
                        f.writelines([f"channel laser_wavelength calibrated_wavelength\n"])
                        f.writelines([f"{ch} {-1} {self.entry_lams[ch].text()}\n" for ch in self.livecounts.ch_numbers])
                        # NOTE: ^ This program doesn't save laser wavelengths yet
                        f.close()
        except:
            print("Error trying to save config file")
            raise

    def clicked_open_wavelengths(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, 'Open File', r"", "Text Files (*.txt)")  # "All Files (*);;Text Files (*.txt)"

        if file_name:
            print("Config file found:", file_name)
            if file_name.endswith('.txt'):
                try:
                    with open(file_name, 'r') as f:
                        data = f.readlines()
                        f.close()

                    #for entry in data[1:]:  # note: first entry in data is just the labels for the columns
                    for entry in data:  # note: first entry in data is just the labels for the columns
                        #ch, las_val, cal_val = entry.strip("\n").split(" ")
                        ch, cal_val = entry.strip("\n").split(" ")
                        try:
                            self.entry_lams[eval(ch)].setText(cal_val)
                            #self.entry_laser_lams[eval(ch)].setText(cal_val)
                        except:
                            print(f"Failed to set ch {ch} with value {cal_val} from file")

                    print(f"Loaded configs from file: {file_name}")
                    self.clicked_update_wavelength()

                except:
                    print("Error trying to read from config file")
                    for ch in self.livecounts.ch_numbers:
                        self.entry_lams[ch].setText("")
                    raise

    def clicked_clear_wavelengths(self):  # NOTE: REMOVE BUNCHING AVERAGE
        self.acquired_wavelengths = False

        for i in self.livecounts.ch_numbers:
            if self.entry_lams[i].text() != "":  # If there is text to remove
                self.entry_lams[i].setPlaceholderText(self.entry_lams[i].text())
                self.entry_lams[i].setText("")

                #self.text_counts[i].setText("") #NOTE THIS ISN*T WORKING

            elif self.entry_lams[i].placeholderText() != "":
                self.entry_lams[i].setPlaceholderText("")

        self.clicked_update_wavelength(reset=True)

    def clicked_fill_wavelengths(self):
        # THIS VERSION (below) ACCOUNTS FOR CHANNELS THAT ARE MISSING
        try:
            provided_chs = []
            provided_wavelens = {}
            for i in self.livecounts.ch_numbers:
                if self.entry_lams[i].text() != "":
                    provided_wavelens[i] = eval(self.entry_lams[i].text())
                    provided_chs.append(i)

            n = len(provided_chs)
            self.acquired_wavelengths = True
            if n > 1:
                try:
                    wl_range = []
                    # FILLING CHANNELS BEFORE FIRST GIVEN CHANNEL
                    if provided_chs[0] != 1:  # if we have to interpolate backwards
                        delta_wl = (provided_wavelens[provided_chs[1]] - provided_wavelens[provided_chs[0]])/(provided_chs[1]-provided_chs[0])
                        wl_range += list(np.linspace(
                            start=provided_wavelens[provided_chs[0]] - delta_wl*(provided_chs[0]-1),
                            stop=provided_wavelens[provided_chs[0]],
                            num=provided_chs[0]-1, endpoint=False))
                    #print("wl_range FIRST", wl_range)

                    # FILLING IN BETWEEN ALL GIVEN WAVELENGTHS
                    for first in range(n - 1):
                        wl_range += list(np.linspace(start=provided_wavelens[provided_chs[first]],
                                                     stop=provided_wavelens[provided_chs[first+1]],
                                                     num=provided_chs[first+1] - provided_chs[first], endpoint=False))

                    #print("wl_range BETWEEN", wl_range)

                    # FILLING REMAINING CHANNELS AFTER
                    delta_wl = wl_range[-1] - wl_range[-2]
                    n_remain = self.livecounts.ch_numbers[-1] - provided_chs[-1]

                    #print("N REMAINING UNFILLED CHANNELS", n_remain)  # NOTE NEW
                    wl_range += list(np.linspace(
                        start=provided_wavelens[provided_chs[-1]],
                        stop=provided_wavelens[provided_chs[-1]] + n_remain * delta_wl,
                        num=n_remain+1, endpoint=True))  # +1 to include the last provided channel
                    #print("wl_range AFTER", wl_range)
                    #print("len wl range AFTER", len(wl_range))

                    # SETTING PLACEHOLDER TEXT
                    for i in self.livecounts.ch_numbers:
                        self.wavelengths[i] = round(wl_range[i-1], 1)
                        if i not in provided_chs:
                            self.entry_lams[i].setPlaceholderText(f"{self.wavelengths[i]}")
                        else:
                            self.entry_lams[i].setPlaceholderText(f"*{self.wavelengths[i]}")  # In case we delete a set text

                except:
                    self.acquired_wavelengths = False
                    print("INVALID RANGE OF WAVELENGTHS:")
                    print(provided_wavelens)
                    raise
        except:
            self.acquired_wavelengths = False
            raise

    def clicked_update_wavelength(self, reset=False):
        """If we want to toggle wavelength vs channel display on"""
        if self.acquired_wavelengths or True:
            self.acquired_wavelengths = False
            try:
                if not reset:
                    for i in self.livecounts.ch_numbers:
                        if self.entry_lams[i].text() == "":
                            if self.entry_lams[i].placeholderText() == "":
                                self.acquired_wavelengths = False
                                print("ERROR:MISSING WAVELENGTH ENTRIES")
                                return
                            else:
                                self.entry_lams[i].setText(self.entry_lams[i].placeholderText())
                        else:
                            self.entry_lams[i].setText(f"{float(eval(self.entry_lams[i].text()))}")

                        self.wavelengths[i] = eval(self.entry_lams[i].text())

                else:
                    self.wavelengths = {i: i for i in self.livecounts.ch_numbers}  # NEW TEST

                label_chs = [[(self.wavelengths[i], f'{i}') for i in self.livecounts.ch_numbers]]
                label_wls = [[(self.wavelengths[i], f'{self.wavelengths[i]}') for i in self.livecounts.ch_numbers]]

                wls = list(self.wavelengths.values())
                min_wl, max_wl = [wls[0] - (wls[1] - wls[0]), wls[-1] + (wls[1] - wls[0])]
                #print(min_wl, max_wl)

                self.plot_window.getAxis('bottom').setTicks(label_chs)
                self.plot_window.getAxis('bottom').setRange(min_wl, max_wl)
                # self.plot_window.getAxis('bottom').setLabel("Channel nr")
                self.plot_window.setXRange(min_wl, max_wl, padding=0.0)  # ensures we don't twitch at edges

                self.pltitem.showAxis('top')

                if reset:
                    self.pltitem.getAxis('top').setLabel('')
                else:
                    self.pltitem.getAxis('top').setLabel("Wavelength (nm)")

                self.pltitem.getAxis('top').setTicks(label_wls)
                self.pltitem.getAxis('top').linkToView(self.ax_vb)

                self.histo.setOpts(x=wls)
                delta_wls = np.min(np.array(wls[1:]) - np.array(wls[0:-1]))
                self.histo.setOpts(width=0.7 * delta_wls)

                for i in self.livecounts.ch_numbers:
                    self.text_counts[i].setPos(self.wavelengths[i], 0)
                    self.text_peaks[i].setPos(self.wavelengths[i], 0.8 * self.plot_window.getViewBox().viewRange()[1][1])

            except:
                print("ERROR: FAILED TO RESET X AXIS TICKS, REVERTING")
                self.ax.setTicks([[(i, f'({i})') for i in self.livecounts.ch_numbers]])  # adjust plot/histo axis
                self.plot_window.setXRange(0, self.livecounts.nr_chs+1)
                raise

    def toggle_ch(self, ch):
        if self.livecounts.active_chs[ch] is False:
            self.livecounts.active_chs[ch] = True
            self.text_counts[ch].setColor((0, 0, 0))
            self.ch_buttons[ch].setStyleSheet("background-color: green")
            print(f"Toggled ch {ch} --> ON")
        else:
            self.livecounts.active_chs[ch] = False
            self.text_counts[ch].setColor((200, 200, 200))
            self.ch_buttons[ch].setStyleSheet("background-color: red")
            print(f"Toggled ch {ch} --> OFF")

    def clicked_setYmax(self):
        try:
            new_ymax = eval(self.entry_max.text())
            self.plot_window.setYRange(0, new_ymax)
            self.autoscale = False  # if we succeed setting it then we don't want autoscale
            self.checkbox_auto.setChecked(False)
            for i in self.livecounts.ch_numbers:
                self.text_peaks[i].setPos(self.wavelengths[i], 0.8*new_ymax)  # self.plot_window.getViewBox().viewRange()[1][1])

        except:
            print("Error trying to set y range (likely invalid input)")
            raise

    def clicked_autoscale(self):
        if self.checkbox_auto.isChecked() == True:
            self.entry_max.setText("")  # remove manual y lim text
            existingViewRect = self.plot_window.getViewBox().viewRange()
            #print(f"Current bounds: x=[{existingViewRect[0][0]}, {existingViewRect[0][1]}], y=[{existingViewRect[1][0]}, {existingViewRect[1][1]}]")
            self.autoscale = True
        else:
            self.autoscale = False

    def clicked_normalized(self):
        if self.checkbox_norm.isChecked() == False:
            self.livecounts.averaged_calibration_counts = {k: 1 for k in self.livecounts.ch_numbers}
        else:
            self.entry_calibrate.setText(f"1")
            self.clicked_recalibrate()
    def clicked_recalibrate(self):
        print('Clicked recalibrate')
        self.checkbox_norm.setChecked(True)
        try:
            loop.run_until_complete(websocket_client(self.base_url, self.livecounts.get_active_channels, n=1))  # finds which channels we collect from Retina setup

            if self.livecounts.int_time:
                sampletime = eval(self.entry_calibrate.text())
                print("sample time (s) =", sampletime)
                n = int(sampletime*(1000/self.livecounts.int_time))     # calculate how many iteration we need to do to sample given nr of seconds for calibration
                print("Sampling", n, "times")
                if n < 1:
                    print("Warning: Sample time given is less than one integration time from retina!")
                    n = 1
            else:
                n = 1
                print("No integration time found")

            self.livecounts.reset_vars(n=n)
            self.histo.setOpts(height=np.zeros(self.livecounts.nr_chs))  # don't display counts while recalibrating
            for i in self.livecounts.ch_numbers:
                self.text_counts[i].setText("...")

        except:
            print("ERROR: Failed to get nr of samples, using default of 5")
            self.entry_calibrate.setText("Try Again")

    def update_plot(self):

        # Fetch new data
        loop.run_until_complete(websocket_client(self.base_url, self.livecounts.get_live_counts, n=1))

        if self.livecounts.case == 'running':
            # Extract raw counts into list (ordered by ch number)
            all_cnts_raw = np.array([self.livecounts.counts[i] for i in self.livecounts.ch_numbers])
            avg_cal_cnts = np.array([self.livecounts.averaged_calibration_counts[i] for i in self.livecounts.ch_numbers])

            # note: below is just local normalization
            #all_cnts_norm = all_cnts_raw / self.livecounts.averaged_calibration_counts
            all_cnts_norm = all_cnts_raw / avg_cal_cnts

            # Change histo heights
            self.histo.setOpts(height=all_cnts_norm)  # +1 for now

            for i in self.livecounts.ch_numbers:
                self.text_counts[i].setText(f"{int(self.livecounts.copy_counts[i])}")

            # CALCULATE WEIGHTED AVERAGE
            if np.sum(all_cnts_raw) != 0:

                main.clicked_bunch()

                #self.weighted_avg = round(np.sum(self.livecounts.ch_numbers * all_cnts_raw) / np.sum(all_cnts_raw), 2)  # FIXME

                if self.autoscale:
                    curr_y_max = np.max(all_cnts_norm)
                    yMaxInView = self.plot_window.getViewBox().viewRange()[1][1]
                    if (curr_y_max > yMaxInView) or (curr_y_max < yMaxInView * 0.5):
                        self.plot_window.setYRange(0, curr_y_max * 1.2)

            else:
                self.plot_window.setYRange(0, 1)


if __name__ == "__main__":
    #url = "130.237.35.20"
    #base_url = f"ws://{url}"

    # ----
    loop = asyncio.get_event_loop()
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()             # Initialize class for GUI/program
    sys.exit(app.exec_())

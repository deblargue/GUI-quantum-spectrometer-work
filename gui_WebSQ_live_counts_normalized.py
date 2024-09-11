from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import sys
import asyncio
import signal
import struct
from sys import platform
import websockets
import numpy as np


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
    def __init__(self):
        self.nr_chs = 24  # TODO: fix!
        self.ch_numbers = np.arange(1, self.nr_chs+1, 1)
        self.active_chs = {c : True for c in self.ch_numbers}
        print(self.active_chs)
        self.reset_vars(n=5)

    def reset_vars(self, n):
        self.n = n
        #self.n = 30  # number of calibration measurements  # FIXME --> increase but remove print
        self.case = 'calibrate'
        self.cnter = 0
        self.norm_counter = 0
        self.raw_counts = {k: 0 for k in self.ch_numbers}
        self.norm_counts_all_ch = {k: 0 for k in self.ch_numbers}  # div by global max avg
        self.norm_counts_per_ch = {k: 0 for k in self.ch_numbers}  # div by calibrated max average for given channel

        self.counts = {k: 0 for k in self.ch_numbers}  # FIXME: phase out
        self.copy_counts = {k: 0 for k in self.ch_numbers}  # FIXME: phase out
        self.calibration_counts_dict_lists = {k: [] for k in self.ch_numbers}
        self.averaged_calibration_counts = np.ones(self.nr_chs)  #AVG OF ABOVE

        #print("done reset vars ")

    def get_live_counts(self, payload):
        if demo:
            #p = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.5, 0.7, 0.9, 0.8, 0.8, 0.3, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])-0.05
            for i, message in enumerate(payload):
                payload[i]['counts'] = round(np.random.normal(loc=50, scale=2, size=1)[0], 0)#*p[message['rank']-1]

        self.payload = payload

        if self.case == 'running':

            for message in payload:  # for every channel

                if self.active_chs[message['rank']] is False:  # NOTE: NEW!!
                    self.counts[message['rank']] = 0
                else:
                    self.counts[message['rank']] = message['counts']

                self.copy_counts[message['rank']] = message['counts']

                #thisapp._update()

        elif self.case == 'calibrate':

            if self.norm_counter == self.n:
                self.case = 'running'
                try:
                    #main.button_recalibrate.setStyleSheet("background-color: white")
                    main.entry_calibrate.setText("")
                    print("DONE BUTTON GREY")
                except:
                    print("FAILED BUTTON GREY")

                for k in self.ch_numbers:
                    self.averaged_calibration_counts[k-1] = np.max([np.mean(self.calibration_counts_dict_lists[k]), 1.0])   # FIXME??
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

    def print_counts(self, payload):

        #print("---", end='\r---')
        #print(payload[0]['time'], end='')

        msg = f"{payload[0]['time']}"
        # init for loop every time step
        for message in payload:  # for every channel
            # time, mcuId, cuId, rank = message["time"], message['mcuId'], message['cuId'], message["rank"]
            # counts, monitorV, biasI, inttime = message['counts'], message['monitorV'], message['biasI'], message['inttime']
            msg += f"  ({message['rank']}) : {message['counts']}  "
            '''if False:
                print(f"""{time} | 
                        {mcuId}.{str(cuId).zfill(2)} ({str(rank).zfill(2)}) | 
                        Counts: {str(counts).rjust(10,' ')} Counts | 
                        monitorV: {str(round(monitorV,6)).rjust(6,' ')} V | 
                        BiasI: {str(biasI).rjust(6,' ')} μA | 
                        intTime: {inttime} ms""")'''

        print("---", end='\r---')
        print(msg, end='')

class MainWindow:  #()QtWidgets.QMainWindow):

    def __init__(self):
        #super().__init__()  # THIS WAS TO INIT THE SUPERCLASS
        self.autoscale = False
        self.wavelengths = {i : None for i in livecounts.ch_numbers}
        self.acquired_wavelengths = False

        # -------------
        loop = asyncio.get_event_loop()
        loop.run_until_complete(websocket_client(base_url, livecounts.get_live_counts, n=10))

        # Add a timer to simulate new temperature measurements
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def initialize(self):
        self.plot_window = pg.PlotWidget()
        self.pltitem = self.plot_window.plotItem
        self.ax_vb = self.pltitem.getViewBox()

        # ---- CREATE GRIDLAYOUT ------
        lay = QtWidgets.QGridLayout(view)  # view
        lay.setColumnStretch(0, 1)   # first column has relative width 1
        lay.setColumnStretch(1, 1)   # second column has relative width 1
        lay.setColumnStretch(2, 20)  # third column has much larger relative width to fit graph

        # ----- PLOT/BAR GRAPH WIDGET-----
        self.adjust_window()  # configure plot window
        # create histo item
        self.histo = pg.BarGraphItem(x=livecounts.ch_numbers, height=np.zeros(livecounts.nr_chs), width=0.6, brush='g')
        self.plot_window.addItem(self.histo)  # add histo item to window

        # ------- RESET RANGE BUTTONS -----
        self.checkbox_auto = QtWidgets.QCheckBox("Auto")
        self.checkbox_auto.toggled.connect(self.clicked_autoscale)
        lay.addWidget(self.checkbox_auto, 0, 0)

        # ------ TEXT INPUT MIN/MAX Y RANGE ------
        self.entry_max = entry_max = QtWidgets.QLineEdit()
        entry_max.editingFinished.connect(self.clicked_setYmax)
        validator_max = QtGui.QDoubleValidator()
        validator_max.setLocale(QtCore.QLocale("en_US"))  # this is to use period as decimal instead of comma
        entry_max.setValidator(validator_max)  # can be a float
        entry_max.setMaxLength(9)
        entry_max.setPlaceholderText("Y max")   # for max y-axis value
        lay.addWidget(entry_max, 0, 1)

        # ---- REDO CALIBRATION SAMPLING FOR AVERAGE -----
        self.entry_calibrate = QtWidgets.QLineEdit()
        self.entry_calibrate.editingFinished.connect(self.clicked_recalibrate)
        self.entry_calibrate.setValidator(QtGui.QIntValidator(0, 99))
        self.entry_calibrate.setPlaceholderText("Resample n times")
        lay.addWidget(self.entry_calibrate, 2, 0, 1, 2)

        # ----- CHANNEL BUTTONS -----
        if False:
            j = 0
            k = 0
            b_off = 6  # which row the first buttons should be
            self.ch_buttons = {}
            for i in livecounts.ch_numbers:
                butt = QtWidgets.QPushButton(f"ch.{i}")
                butt.setStyleSheet("background-color: green")
                if i % 13 == 0:
                    j = 0
                    k += 1
                self.ch_buttons[i] = butt
                butt.clicked.connect(lambda checked, i=i: self.toggle_ch(i))  # FIXMEadding signal and slot
                lay.addWidget(butt, j+b_off, k)
                j += 1
        else:  # If we want to use the wavelength entries
            b_off = 7  # which row the first buttons should be
            self.ch_buttons = {}
            self.entry_lams = {}  # to save lamda entries
            self.text_counts = {}
            for i in livecounts.ch_numbers:
                butt = QtWidgets.QPushButton(f"ch.{i}")
                butt.setStyleSheet("background-color: green")
                self.ch_buttons[i] = butt
                butt.clicked.connect(lambda checked, i=i: self.toggle_ch(i))  # FIXMEadding signal and slot
                lay.addWidget(butt, b_off+1+i, 0)

                # ----- WAVELENGTH ENTRIES AND BUTTON
                # self.clicked_update_wavelength

                entry_lam = QtWidgets.QLineEdit()
                validator = QtGui.QDoubleValidator(0.0, 99999.0, 1)
                validator.setLocale(QtCore.QLocale("en_US")) #
                entry_lam.setValidator(validator)
                entry_lam.setText("")
                self.entry_lams[i] = entry_lam
                lay.addWidget(entry_lam, b_off+1+i, 1)

                # COUNTRATE TEXT ON BARS
                new_text = pg.TextItem(
                    text=f'-',
                    color=(0, 0, 0),
                    anchor=(0, 0.5),  # where in the text box that the setPos with anchor to
                    angle=90,  # 90
                    rotateAxis=(1, 0))
                new_text.setPos(i, 0)
                self.text_counts[i] = new_text
                self.ax_vb.addItem(new_text)

            update_lams = QtWidgets.QPushButton(f"Set λs")  # Button to update lambdas
            #update_lams.setStyleSheet("background-color: green")
            update_lams.clicked.connect(self.clicked_update_wavelength)  # FIXME
            lay.addWidget(update_lams, b_off, 0)

            get_lams = QtWidgets.QPushButton(f"Get λs")  # Button to update lambdas
            get_lams.clicked.connect(self.clicked_fill_wavelengths)  # FIXME
            lay.addWidget(get_lams, b_off, 1)

            open_lams = QtWidgets.QPushButton(f"Open λs")  # Button to update lambdas
            open_lams.clicked.connect(self.clicked_open_wavelengths)  # FIXME
            lay.addWidget(open_lams, b_off-2, 1)

            clear_lams = QtWidgets.QPushButton(f"Clear λs")  # Button to update lambdas
            clear_lams.clicked.connect(self.clicked_clear_wavelengths)  # FIXMEadding signal and slot
            lay.addWidget(clear_lams, b_off-1, 1)

            save_lams = QtWidgets.QPushButton(f"Save λs")  # Button to update lambdas
            save_lams.clicked.connect(self.clicked_save_wavelengths)  # FIXMEadding signal and slot
            lay.addWidget(save_lams, b_off-1, 0)

            #("background-color: white")

        lay.addWidget(self.plot_window, 0, 2, lay.rowCount(), 1)  # note that columnstrech on this column is much larger (prev def)

    def adjust_window(self):
        #self.plot_window.setGeometry(QtCore.QRect(0, 0, 600, 100))      # (0, 0, 600, 500))        #NOTE THIS DICTATES WHERE BUTTONS ARE PLACED I THINK
        self.plot_window.setMouseEnabled(x=True, y=True)

        # self.plot_window.geometry().left()
        # self.plot_window.geometry().top()
        self.win_h = self.plot_window.geometry().height()
        self.win_w = self.plot_window.geometry().width()
        #print(self.plot_window.geometry())

        self.plot_window.setBackground("w")

        axes_styles = {"color": "black", "font-size": "18px"}
        self.plot_window.setLabel("left", "Counts", **axes_styles)
        self.plot_window.setLabel("bottom", "Channel", **axes_styles)

        self.ax = self.plot_window.getAxis('bottom')
        self.ax.setTicks([[(i, f'{i}') for i in livecounts.ch_numbers]])   # adjust plot/histo axis

        # self.plot_window.addLegend()
        self.plot_window.showGrid(x=True, y=True)

        #self.plot_window.setXRange(0, livecounts.nr_chs+1)   # (0, 13) when we had 12 chs
        self.plot_window.getAxis('bottom').setRange(0, livecounts.nr_chs+1)   # (0, 13) when we had 12 chs
        self.plot_window.setYRange(0, 2)  # FIXME? --> make auto scale? Add button to release auto

    def clicked_save_wavelengths(self):
        pass

    def clicked_open_wavelengths(self):
        pass

    def clicked_clear_wavelengths(self):
        for i in livecounts.ch_numbers:
            self.entry_lams[i].setText("")

    def clicked_fill_wavelengths(self):
        try:
            provided_chs = []
            provided_wavelens = {}
            for i in livecounts.ch_numbers:
                try:
                    provided_wavelens[i] = eval(self.entry_lams[i].text())
                    provided_chs.append(i)
                except:
                    continue

            n = len(provided_chs)
            self.acquired_wavelengths = True
            if n > 1:
                # this means we can extrapolate data
                """avg_delta = []
                for i in range(n):  # for each given channel
                    for j in range(i+1, n):  # for each of the remaining channels not compared with
                        # average wavelength distance (delta lambda/delta ch nr):
                        avg = (provided_wavelens[provided_chs[j]]-provided_wavelens[provided_chs[i]])/(provided_chs[j]-provided_chs[i])
                        avg_delta.append(avg)

                        if avg < 0:
                            self.acquired_wavelengths = False
                            print("INVALID RANGE OF WAVELENGTHS:")
                            print(provided_wavelens)
                            return"""

                try:
                    # Interpolating ranges between
                    wl_range = []
                    for start in range(n-1):
                        wl_range += list(np.linspace(start=provided_wavelens[provided_chs[start]], stop=provided_wavelens[provided_chs[start+1]], num=provided_chs[start+1]-provided_chs[start], endpoint=False))
                    livecounts.nr_chs - len(wl_range)
                    wl_range += list(np.linspace(start=provided_wavelens[provided_chs[-1]], stop=provided_wavelens[provided_chs[-1]] + (livecounts.nr_chs - len(wl_range))*(wl_range[-1]-wl_range[-2]),
                                                 num=livecounts.nr_chs - len(wl_range), endpoint=False))

                    for i in livecounts.ch_numbers:
                        self.wavelengths[i] = round(wl_range[i-1], 0)
                        self.entry_lams[i].setText(f"{round(wl_range[i-1], 1)}")

                        if i not in provided_chs:
                            self.entry_lams[i].setStyleSheet()

                except:
                    self.acquired_wavelengths = False
                    print("INVALID RANGE OF WAVELENGTHS:")
                    print(provided_wavelens)
                    raise
        except:
            self.acquired_wavelengths = False
            raise

    def clicked_update_wavelength(self):
        """If we want to toggle wavelength vs channel display on"""
        if self.acquired_wavelengths:
            try:
                for i in livecounts.ch_numbers:
                    self.wavelengths[i] = eval(self.entry_lams[i].text())

                #self.ax = self.plot_window.getAxis('bottom')
                #self.ax.setTicks([[(i, f'{i}') for i in livecounts.ch_numbers]])  # adjust plot/histo axis

                label_chs = [(self.wavelengths[i], f'{i}') for i in livecounts.ch_numbers]
                label_chs = [[(self.wavelengths[i], f'{i}') for i in livecounts.ch_numbers]]
                label_wls = [[(self.wavelengths[i], f'{self.wavelengths[i]}') for i in livecounts.ch_numbers]]

                wls = list(self.wavelengths.values())
                min_wl, max_wl = [wls[0]-(wls[1]-wls[0]) , wls[-1]+(wls[1]-wls[0])]
                print(min_wl, max_wl)
                self.plot_window.getAxis('bottom').setTicks(label_chs)
                self.plot_window.getAxis('bottom').setRange(min_wl, max_wl)
                self.plot_window.getAxis('bottom').setLabel("Channel nr")

                #pltitem.setLabels(bottom='Channel')
                #pltitem.setLabels(top='Wavelength (nm)')

                self.pltitem.showAxis('top')
                self.pltitem.getAxis('top').setLabel("Wavelength (nm)")
                self.pltitem.getAxis('top').setTicks(label_wls)
                self.pltitem.getAxis('top').linkToView(self.ax_vb)

                self.histo.setOpts(x=wls)
                self.histo.setOpts(width=0.6*(wls[1]-wls[0]))

                #self.plot_window.setXRange(list(self.wavelengths.values())[0], list(self.wavelengths.values())[-1])   # (0, 13) when we had 12 chs

                if True:
                    for i in livecounts.ch_numbers:
                        self.text_counts[i].setPos(self.wavelengths[i], 0)

            except:
                print("ERROR: FAILED TO RESET X AXIS TICKS, REVERTING")
                self.ax.setTicks([[(i, f'({i})') for i in livecounts.ch_numbers]])  # adjust plot/histo axis
                #self.plot_window.setXRange(0, livecounts.nr_chs+1)
                raise

    def toggle_ch(self, ch):
        if livecounts.active_chs[ch] is False:
            livecounts.active_chs[ch] = True
            self.text_counts[ch].setColor((0, 0, 0))
            self.ch_buttons[ch].setStyleSheet("background-color: green")
            print(f"Toggled ch {ch} --> ON")
        else:
            livecounts.active_chs[ch] = False
            self.text_counts[ch].setColor((200, 200, 200))
            self.ch_buttons[ch].setStyleSheet("background-color: red")
            print(f"Toggled ch {ch} --> OFF")

    def clicked_setYmax(self):
        new_y = self.entry_max.text()
        try:
            self.plot_window.setYRange(0, eval(new_y))
            self.autoscale = False  # if we succeed setting it then we don't want autoscale
            self.checkbox_auto.setChecked(False)
        except:
            print("Error trying to set y range (likely invalid input)")
            raise

    def clicked_autoscale(self):
        if self.checkbox_auto.isChecked() == True:
            self.entry_max.setText("")  # remove manual y lim text
            existingViewRect = self.plot_window.getViewBox().viewRange()
            print(f"Current bounds: x=[{existingViewRect[0][0]}, {existingViewRect[0][1]}], y=[{existingViewRect[1][0]}, {existingViewRect[1][1]}]")
            self.autoscale = True
        else:
            self.autoscale = False

    def clicked_recalibrate(self):
        print('Clicked recalibrate')
        try:
            livecounts.reset_vars(n=eval(self.entry_calibrate.text()))
            self.histo.setOpts(height=np.zeros(livecounts.nr_chs))  # don't display counts while recalibrating
            for i in livecounts.ch_numbers:
                self.text_counts[i].setText("...")

        except:
            print("ERROR: Failed to get nr of samples, using default of 5")
            self.entry_calibrate.setText("5")
            livecounts.reset_vars(n=5)

        #self.button_recalibrate.setStyleSheet("background-color: grey")

    def update_plot(self):

        # Fetch new data
        loop.run_until_complete(websocket_client(base_url, livecounts.get_live_counts, n=1))

        if livecounts.case == 'running':
            # Extract raw counts into list (ordered by ch number)
            all_cnts_raw = np.array([livecounts.counts[i] for i in livecounts.ch_numbers])

            # note: below is just nor local normalization
            all_cnts_norm = all_cnts_raw / livecounts.averaged_calibration_counts

            # Change histo heights
            self.histo.setOpts(height=all_cnts_norm)  # +1 for now

            for i in livecounts.ch_numbers:
                self.text_counts[i].setText(f"{int(livecounts.copy_counts[i])}")

            # self.line.setData(livecounts.ch_numbers, all_cnts)   # for line plot   #FIXME???

            # CALCULATE WEIGHTED AVERAGE
            if np.sum(all_cnts_raw) != 0:
                # TODO FIXME: CHECK IF WEIGHTED AVERAGE IF BEFORE OR AFTER NORM
                self.weighted_avg = round(np.sum(livecounts.ch_numbers * all_cnts_raw) / np.sum(all_cnts_raw), 2)  # FIXME
                self.plot_window.setTitle(f"Weighted Average Channel = {self.weighted_avg}", color="k", size="20pt")

                if self.autoscale:
                    curr_y_max = np.max(all_cnts_norm)
                    yMaxInView = self.plot_window.getViewBox().viewRange()[1][1]
                    if (curr_y_max > yMaxInView) or (curr_y_max < yMaxInView * 0.5):
                        self.plot_window.setYRange(0, curr_y_max * 1.2)

            else:
                self.plot_window.setTitle(f"", color="k", size="20pt")
                self.plot_window.setYRange(0, 1)


'''def STANDALONE_initialize():
    lay = QtWidgets.QGridLayout(view)

    # ------ TEXT INPUT BOX ------
    e1 = QtWidgets.QLineEdit()
    e1.setValidator(QtGui.QIntValidator())
    e1.setMaxLength(5)
    # e1.setAlignment(QtCore.Qt.AlignRight)
    # e1.setFont(QtCore.Qt.QFont("Arial", 20))
    lay.addWidget(e1, 0, 1, 1, 1)

    e2 = QtWidgets.QLineEdit()
    e2.setValidator(QtGui.QIntValidator())
    e2.setMaxLength(5)
    # e1.setAlignment(QtCore.Qt.AlignRight)
    # e1.setFont(QtCore.Qt.QFont("Arial", 20))
    lay.addWidget(e2, 0, 2, 1, 1)

    # ------ BUTTONS ------
    def handle_button_clicked(button):
        print(button, button.text())

    group = QtWidgets.QButtonGroup()
    j = 1
    k = 1
    for i in range(1, 25):
        button = QtWidgets.QPushButton(f"ch.{i}")
        lay.addWidget(button, j, k, 1, 1)
        j += 1
        if i % 12 == 0:
            j = 1
            k += 1
        group.addButton(button)

    group.buttonClicked.connect(handle_button_clicked)

    # ----- PLOT -----

    plot_window = pg.PlotWidget()  ##parent=self.new_w)
    lay.addWidget(plot_window, 0, 0, 30, 1)

    histo = pg.BarGraphItem(x=[0, 1, 2, 3, 4, 5], height=[1, 2, 3, 4, 5, 6], width=0.6, brush='g')

    # add histo item to window
    plot_window.addItem(histo)
'''

if __name__ == "__main__":
    url = "130.237.35.20"
    base_url = f"ws://{url}"
    demo = True

    livecounts = LiveCounts()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(websocket_client(base_url, livecounts.get_live_counts, n=10))

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()  # Initialize class

    view = QtWidgets.QWidget()
    main.initialize()  # Create interface

    # ------
    view.showMaximized()
    view.show()

    sys.exit(app.exec_())  # TODO: figure out why sys.exit


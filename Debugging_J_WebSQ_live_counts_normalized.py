import asyncio
import random
import signal
import struct
from sys import platform
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
import websockets
import time

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


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.nr_chs = 24  # TODO FIX

        self.create_window()
        self.create_histo()
        self.create_reset_button()
        self.create_ch_buttons()

        # -------------
        loop = asyncio.get_event_loop()
        loop.run_until_complete(websocket_client(base_url, livecounts.get_live_counts, n=10))

        # Add a timer to simulate new temperature measurements
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def create_window(self):
        # Temperature vs time dynamic plot
        self.window = pg.PlotWidget()
        self.setCentralWidget(self.window)
        self.window.setGeometry(QtCore.QRect(0, 0, 600, 100))      # (0, 0, 600, 500))        #NOTE THIS DICTATES WHERE BUTTONS ARE PLACED I THINK
        self.window.setMouseEnabled(x=False, y=False)

        # self.window.geometry().left()
        # self.window.geometry().top()
        self.win_h = self.window.geometry().height()
        self.win_w = self.window.geometry().width()
        # print(self.window.geometry())

        self.window.setBackground("w")

        axes_styles = {"color": "black", "font-size": "18px"}
        self.window.setLabel("left", "Counts", **axes_styles)
        self.window.setLabel("bottom", "Channel", **axes_styles)

        # self.window.addLegend()
        self.window.showGrid(x=True, y=True)

        self.window.setXRange(0, self.nr_chs+1)   # (0, 13) when we had 12 chs
        self.window.setYRange(0, 5)

    def create_histo(self):
        self.time = np.arange(1, self.nr_chs+1, 1)
        self.counts = [0 for _ in range(self.nr_chs)]
        self.histo = pg.BarGraphItem(x=self.time, height=self.counts, width=0.6, brush='g')
        self.window.addItem(self.histo)

        self.ax = self.window.getAxis('bottom')  # This is the trick
        self.ax.setTicks([[(i + 1, f'{i + 1}') for i in range(self.nr_chs)]])

    def create_reset_button(self):
        # self.window.sigMouseReleased.connect(self.mouse_release)  # try to get some mouse event
        self.resetButton = QtWidgets.QPushButton(self.window, text='  reset  ')
        self.resetButton.setGeometry(QtCore.QRect(100, 0, 80, 28))
        self.resetButton.clicked.connect(self.clicked_reset)  # adding signal and slot

    def create_ch_buttons(self):
        # TODO: FIX SUCH THAT buttons follow resizing!
        self.ch_buttons = []
        butt_w = 20    # 40
        butt_h = 14    # 28
        butt_space = 3  # 3   # spacing between each button
        for i in range(0, self.nr_chs):
            x_pos = 84 + (i * (butt_w + butt_space))
            self.ch_buttons.append(QtWidgets.QPushButton(self.window, text=f'{i + 1}'))
            self.ch_buttons[i].setGeometry(QtCore.QRect(x_pos, self.win_h - 70, butt_w, butt_h))   # (x_pos, self.win_h - 70, 40, 28)
            #self.ch_buttons[i].clicked.connect(lambda i: self.toggle_ch(int(i)))  # adding signal and slot  # TODO FIX??+
            self.ch_buttons[i].setStyleSheet("background-color: green")

        if True:   # TODO FIX: MUST DO THIS IN LOOP BUT BUG?
            self.ch_buttons[0].clicked.connect(lambda: self.toggle_ch(0))  # adding signal and slot
            self.ch_buttons[1].clicked.connect(lambda: self.toggle_ch(1))  # adding signal and slot
            self.ch_buttons[2].clicked.connect(lambda: self.toggle_ch(2))  # adding signal and slot
            self.ch_buttons[3].clicked.connect(lambda: self.toggle_ch(3))  # adding signal and slot
            self.ch_buttons[4].clicked.connect(lambda: self.toggle_ch(4))  # adding signal and slot
            self.ch_buttons[5].clicked.connect(lambda: self.toggle_ch(5))  # adding signal and slot
            self.ch_buttons[6].clicked.connect(lambda: self.toggle_ch(6))  # adding signal and slot
            self.ch_buttons[7].clicked.connect(lambda: self.toggle_ch(7))  # adding signal and slot
            self.ch_buttons[8].clicked.connect(lambda: self.toggle_ch(8))  # adding signal and slot
            self.ch_buttons[9].clicked.connect(lambda: self.toggle_ch(9))  # adding signal and slot
            self.ch_buttons[10].clicked.connect(lambda: self.toggle_ch(10))  # adding signal and slot
            self.ch_buttons[11].clicked.connect(lambda: self.toggle_ch(11))  # adding signal and slot
            self.ch_buttons[12].clicked.connect(lambda: self.toggle_ch(12))  # adding signal and slot
            self.ch_buttons[13].clicked.connect(lambda: self.toggle_ch(13))  # adding signal and slot
            self.ch_buttons[14].clicked.connect(lambda: self.toggle_ch(14))  # adding signal and slot
            self.ch_buttons[15].clicked.connect(lambda: self.toggle_ch(15))  # adding signal and slot
            self.ch_buttons[16].clicked.connect(lambda: self.toggle_ch(16))  # adding signal and slot
            self.ch_buttons[17].clicked.connect(lambda: self.toggle_ch(17))  # adding signal and slot
            self.ch_buttons[18].clicked.connect(lambda: self.toggle_ch(18))  # adding signal and slot
            self.ch_buttons[19].clicked.connect(lambda: self.toggle_ch(19))  # adding signal and slot
            self.ch_buttons[20].clicked.connect(lambda: self.toggle_ch(20))  # adding signal and slot
            self.ch_buttons[21].clicked.connect(lambda: self.toggle_ch(21))  # adding signal and slot
            self.ch_buttons[22].clicked.connect(lambda: self.toggle_ch(22))  # adding signal and slot
            self.ch_buttons[23].clicked.connect(lambda: self.toggle_ch(23))  # adding signal and slot

    def toggle_ch(self, ch):
        if livecounts.active_chs[ch] is False:
            livecounts.active_chs[ch] = True
            self.ch_buttons[ch].setStyleSheet("background-color: green")
            print(f"Toggled ch {ch+1} ON")
        else:
            livecounts.active_chs[ch] = False
            self.ch_buttons[ch].setStyleSheet("background-color: red")
            print(f"Toggled ch {ch+1} OFF")

    def clicked_reset(self):
        print('clicked reset')
        livecounts.reset_vars()

    def update_plot(self):
        #for j in range(0, 24, 2):
        #    self.counts[j] = livecounts.counts[j//2 + 1]
        #    self.counts[j+1] = livecounts.counts[j//2 + 1]
        #print(self.counts)
        #self.line.setData(self.time, list(self.counts))

        #self.histo.setOpts(height=[livecounts.counts[j+1] for j in range(self.nr_chs)])
        #time_list = [i for i in livecounts.curr_t.values()]
        #max_time = np.max(time_list) + 1
        #time_list /= max_time
        time_list = [livecounts.curr_t[j + 1] for j in range(self.nr_chs)] - np.max([livecounts.curr_t[j + 1] for j in range(self.nr_chs)])
        self.histo.setOpts(height=time_list )  # NEW
        #self.histo.setOpts(height=time_list)  # NEW
        #self.line.setData(self.time, [livecounts.counts[j+1] for j in range(self.nr_chs)])   # for line plot

        loop.run_until_complete(websocket_client(base_url, livecounts.get_live_counts, n=1))

        if livecounts.case == 'running':
            all_cnts = np.array([livecounts.counts[i] for i in range(1, self.nr_chs+1)])
            ch_nrs = np.arange(1, self.nr_chs+1, 1)
            #print(all_cnts)
            #print(ch_nrs)
            if np.sum(all_cnts) != 0:
                self.weighted_avg = round(np.sum(ch_nrs * all_cnts) / np.sum(all_cnts), 2)
                #print(weighted_avg)
                #self.window.setTitle(f"t={livecounts.curr_t}", color="b", size="20pt")
                #self.window.setTitle(f"Avg ch={self.weighted_avg}", color="b", size="20pt")
                #self.window.setYRange(0, np.max(all_cnts) + 1)   # NOTE: NEW AUTOMATICALLY SCALES
                ##self.window.setYRange(np.min(time_list) - 1, np.max(time_list) + 1)   # NOTE: NEW AUTOMATICALLY SCALES
            else:
                self.window.setTitle(f"Avg ch=...", color="b", size="20pt")

        #livecounts.print_counts(livecounts.payload)

class LiveCounts:
    def __init__(self):
        self.nr_chs = 24  # TODO: fix!
        self.start_time = None
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

        #print("done reset vars ")

    def get_live_counts(self, payload):

        self.payload = payload

        #print("case", self.case)
        if self.case == 'running':
            self.cnter += 1
            if self.cnter % 10 == 0:  # for when to update plot lims
                self.max_val = 0

            self.counts =  {k: 0 for k in self.ch_list} # TEMP
            temp_list = [0 for _ in range(self.nr_chs)]
            temp2_list = [0 for _ in range(self.nr_chs)]
            for message in payload:  # for every channel

                #temp_list[message['rank']-1] += 1
                #temp2_list[message['rank']-1] = message['time']
                self.curr_t[message['rank']] = message['time']

                if self.active_chs[message['rank']-1] is False:  # NOTE: NEW!!
                    self.counts[message['rank']] = 0
                    print("inactive!")
                else:
                    if fake_data:
                        #self.counts[message['rank']] = np.random.randint(0, 5)
                        #self.counts[message['rank']] += 1
                        self.counts[message['rank']] = 1
                    else:
                        self.counts[message['rank']] = message['counts'] / (self.max_counts[message['rank']])  # divide by measured average


                # FIXME check if this needs to be under else
                if self.max_val < self.counts[message['rank']]:
                    self.max_val = self.counts[message['rank']]

                #thisapp._update()
                #self.print_counts(payload)
            #tprint(temp_list)
            #tprint(temp2_list)
            #tprint(" ")

        elif self.case == 'calibrate':

            if self.norm_counter == self.n:
                self.case = 'running'
                #print("GO RUNNING")
                for key in self.max_counts.keys():
                    #if self.active_chs[key-1] is False:   # NOTE: NEW!!
                    #    self.max_counts[key] = 1
                    #    print(f"skipped ch {key} in reset!!")
                    #else:
                    self.max_counts[key] = np.max([np.mean(self.max_counts_list[key]), 1.0])

            self.norm_counter += 1

            for message in payload:  # for every channel
                print(message)
                if self.active_chs[message['rank']-1] is False:  # NOTE: NEW!!
                    self.max_counts_list[message['rank']].append(0)
                else:
                    self.max_counts_list[message['rank']].append(message['counts'])

        else:
            print("WRONGG CASE")
            self.case = 'running'

        #print("done get live counts")

    def print_counts(self, payload):

        #print("---", end='\r---')
        #print(payload[0]['time'], end='')

        msg = f"{payload[0]['time']}"
        # init for loop every time step
        for message in payload:  # for every channel
            # time, mcuId, cuId, rank = message["time"], message['mcuId'], message['cuId'], message["rank"]
            # counts, monitorV, biasI, inttime = message['counts'], message['monitorV'], message['biasI'], message['inttime']
            msg += f"  ({message['rank']}):{message['counts']}  "
            #print(f"ch{message['rank']}: {message['counts']} counts")
            '''if False:
                print(f"""{time} | 
                        {mcuId}.{str(cuId).zfill(2)} ({str(rank).zfill(2)}) | 
                        Counts: {str(counts).rjust(10,' ')} Counts | 
                        monitorV: {str(round(monitorV,6)).rjust(6,' ')} V | 
                        BiasI: {str(biasI).rjust(6,' ')} μA | 
                        intTime: {inttime} ms""")'''

        print("---", end='\r---')
        print(msg, end='')


if __name__ == '__main__':

    fake_data = True  # if we don't have counts we can randomly generate fake data

    url = "130.237.35.20"  # url = "192.168.1.1"
    base_url = f'ws://{url}'
    # livecounts = LiveCounts()

    livecounts = LiveCounts()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(websocket_client(base_url, livecounts.get_live_counts, n=10))

    app = QtWidgets.QApplication([])
    main = MainWindow()
    main.show()
    #websocket_client(base_url, livecounts.get_live_counts, n=1)
    app.exec()







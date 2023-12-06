
from WebSQControl import WebSQControl

"""
The following code explains how to
    - receive counts from the detectors
    - set/get a bias current
    - set/get trigger level
    - set/get the measurement time
    - enable the detectors
    - get the number of detectors
"""


class SQControl:
    def __init__(self):
        # -------------- ARGUMENTS: --------------
        # Number of measurements (default 10)
        self.N = 1
        # dest='N', type=int, default=10, help='The amount of measurements done.'

        # TODO: FIGURE OUT CORRECT IP ADDRESS
        # TCP IP Address of your system (default 192.168.1.1)
        self.tcp_ip_address = '192.168.35.236'
        # dest='tcp_ip_address', type=str, default='192.168.1.1', help='The TCP IP address of the detector'

        # The control port (default 12000)
        self.control_port = 12000

        # The port emitting the photon Counts (default 12345)
        self.counts_port = 12345

    def main(self):
        self.open_connection()
        try:
            self.get_bias_current()
            self.get_number_of_detectors()
            self.set_integration_time()
            self.enable_detector()
            self.set_curr_bias()
            self.set_trigger_lvl()
            self.get_counts()
            self.read_back()
            self.close_connection()
        except:
            self.close_connection()
            raise

    def open_connection(self):
        try:
            self.websq = WebSQControl(TCP_IP_ADR=self.tcp_ip_address, CONTROL_PORT=self.control_port, COUNTS_PORT=self.counts_port)
            self.websq.connect()
            print("Connected to WebSQ")
        except:
            print("Connection error")
            raise

    def get_bias_current(self):
        print("Automatically finding bias current, avoid Light exposure")
        self.found_bias_current = self.websq.auto_bias_calibration(DarkCounts=[100, 100, 100, 100])
        print("Bias current: " + str(self.found_bias_current))

    def get_number_of_detectors(self):
        # Acquire number of detectors in the system
        self.number_of_detectors = self.websq.get_number_of_detectors()
        print("Your system has " + str(self.number_of_detectors) + ' detectors\n')

    def set_integration_time(self, dt=100):
        print(f"Set integration time to {dt} ms\n")
        self.websq.set_measurement_periode(dt)  # Time in ms

    def enable_detector(self):
        print("Enable detectors\n")
        self.websq.enable_detectors(True)

    def set_curr_bias(self, bias=None):
        if not bias:
            bias = -15  # uA

        # Set the bias current
        curr = []
        for n in range(self.number_of_detectors):
            curr.append(bias)

        print(f"Set bias currents to: {curr}")
        self.websq.set_bias_current(current_in_uA=curr)
        print("\n")

    def set_trigger_lvl(self, trigger=None):
        if not trigger:
            trigger = -150  # mV

        # Set the trigger level
        trig = []
        for n in range(self.number_of_detectors):
            trig.append(trigger)

        print(f"Set trigger levels to: {trig}")
        self.websq.set_trigger_level(trigger_level_mV=trig)
        print("\n")

    def get_counts(self):
        # Acquire N counts measurements:
        #   Returns an array filled with N numpy arrays each containing as first element a
        #   time stamp and then the detector counts ascending order

        print(f"Acquire {self.N} counts measurements \n============================\n")
        # Get the counts
        counts = self.websq.acquire_cnts(self.N)

        # Print the counts nicely
        header = "Timestamp\t\t"
        for n in range(self.number_of_detectors):
            header += "Channel" + str(n + 1) + "\t"
        print("Header:", header)

        for row in counts:
            line = ""
            for element in row:
                line += str(element) + '\t'
            print(line)

    def read_back(self):
        print("\nRead back set values\n====================\n")
        print(f"Measurement Periode (ms): \t {self.websq.get_measurement_periode()}")
        print(f"Bias Currents in uA: \t\t {self.websq.get_bias_current()}")
        print(f"Trigger Levels in mV: \t\t {self.websq.get_trigger_level()}")

    def close_connection(self):
        # Close connection
        self.websq.close()



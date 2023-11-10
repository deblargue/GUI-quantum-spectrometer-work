
import serial
import time

"""
The SP-2150i monochromator or spectrograph can also be controlled from an RS-232 terminal or from a
computer using RS-232 or USB. The same command set, listed below, is used for RS-232 or USB control.

* Commands can be sent as single commands or grouped into strings of commands. 
* All commands are single words (contain no spaces) 
    and all commands in a string are separated by at least one space. 
* params, if needed, precede the command and are separated from the command by at least one space 
    (e.g., 546.7 GOTO).

* All commands or strings of commands must be terminated with a carriage return (0D hex). 
* The SP-2150i responds to a command when the command has been completed by 
    returning the characters “OK” followed by carriage return and line feed (hex ASCII sequence 20 6F 6B 0D 0A). 

* The default condition is to echo each character that is sent to the SP-2150i. 
* If no echo is desired, the command NO-ECHO will suppress the echo. 
* The command ECHO will return the SP-2150i to the default echo state.
"""

class SP2750:

    def __init__(self):
        # Serial connection settings:
        self.handle = None
        self.port = "COM4"        # usb port
        self.serial_timeout = 1   # in seconds  (can change to desired time)

    def connect(self):

        try:
            print("Establishing connection...")
            self.handle = serial.Serial(port=self.port, baudrate=9600, parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=self.serial_timeout)
            if self.handle:
                print(f"Successfully connected to PORT: {self.port}\nSerial handle:", self.handle)
            else:
                print("ERROR: handle still None")

        except serial.SerialException:
            print(f"ERROR: Timeout ({self.serial_timeout}s), could not connect to PORT: {self.port}")
            if self.handle:
                self.disconnect()
            raise

    def disconnect(self):
        time.sleep(1)
        self.handle.close()
        #print("handle after close:", self.handle, "?= None")
        self.handle = None  # TODO CHECK!
        print("Connection Closed!")

    def wait_for_read(self):
        count = 0
        res = ''
        for i in range(20):
            count += 1
            if len(res) < 2:   # maybe increase idk?
                if count > 3:
                    print("waiting", count)

                time.sleep(1)
                res_r = self.handle.readall()
                res = res_r.decode("ASCII")
                # TODO: strip line termination etc.
            else:
                return res

    def read_cmd(self, param):
        cmd = ''
        if param == 'grating':
            print("\nReading grating...")
            cmd = "?GRATING\r"

        elif param == 'gratings list':
            print("\nReading all grating...")
            cmd = "?GRATINGS\r"

        elif param == 'nm':
            print("\nReading nm...")
            cmd = "?NM\r"

        elif param == 'temp':
            return

        else:
            print("ERROR: UNKNOWN READ param")
            return

        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)
        res = self.wait_for_read()
        print("Read Response =", res)

    def write_cmd(self, param, value):
        # TODO: ADD SAFETY CHECK FOR VALUE RANGE!

        cmd = ''
        if param == 'grating':
            print("\nWriting grating...")
            cmd = f"{int(value)} GRATING\r"

        elif param == 'nm':
            print("\nWriting nm...")
            cmd = f"{float(value)} NM\r"

        elif param == 'temp':
            return
        else:
            print("ERROR: UNKNOWN WRITE param")
            return

        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)
        res = self.wait_for_read()
        print("Write Response =", res)

    def main(self):

        self.write_cmd(param='grating', value=1)
        self.write_cmd(param='nm'     , value=800)

        self.read_cmd('grating')
        self.read_cmd('nm')
        self.read_cmd('gratings list')   # all gratings



sp = SP2750()
sp.connect()
sp.main()
sp.disconnect()

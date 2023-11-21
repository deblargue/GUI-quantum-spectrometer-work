import serial
import time

"""
The SP-2150i monochromator or spectrograph can also be controlled from an RS-232 terminal or from a
computer using RS-232 or USB. The same command set, listed below, is used for RS-232 or USB control.

* Commands can be sent as single commands or grouped into strings of commands. 
* All commands are single words (contain no spaces) 
    and all commands in a string are separated by at least one space. 
* Parameters, if needed, precede the command and are separated from the command by at least one space 
    (e.g., 546.7 GOTO).

* For RS-232 operation, the port setup is:
    * 9600 baud
    * 8 data bits
    * 1 stop bit
    * no parity. 

* All commands or strings of commands must be terminated with a carriage return (0D hex). 
* The SP-2150i responds to a command when the command has been completed by 
    returning the characters “OK” followed by carriage return and line feed (hex ASCII sequence 20 6F 6B 0D 0A). 

* The default condition is to echo each character that is sent to the SP-2150i. 
* If no echo is desired, the command NO-ECHO will suppress the echo. 
* The command ECHO will return the SP-2150i to the default echo state.
"""


"""
Writing grating...
b'2 GRATING  ok\r\n'

Writing nm...
b'750.0NM 750.0NM ? \r\n'

Reading nm...
b'?NM 749.998 nm  ok\r\n'

Reading grating...
b'?GRATING 2  ok\r\n'
"""

class SP2750:

    def __init__(self):

        # Serial connection settings:
        self.handle = None
        self.baudrate = 9600
        self.databits = serial.EIGHTBITS
        self.stopbits = serial.STOPBITS_ONE
        self.parity = serial.PARITY_NONE
        self.timeout = 1   # in seconds  (can change to desired time)

    def main(self):

        #self.read_sp('scan rate')
        #self.write_sp('scan rate', 500.0)

        #self.write_sp('grating', 1)
        self.read_sp('grating')

        #self.write_sp('nm', 700.0)
        #self.read_sp('nm')
        #self.read_sp('info gratings')

    def strip_response(self, res):
        res = res[:-2]  # removing carriage return and line feed
        res_s = res.decode("ASCII")
        return res_s

    def connect(self, port):
        try:
            self.handle = serial.Serial(port=port, baudrate=self.baudrate, parity=self.parity, stopbits=self.stopbits, bytesize=self.databits, timeout=self.timeout)
            if self.handle:
                print("Successfully connected to PORT:", port, ", Serial handle:", self.handle)
            else:
                print("ERROR: handle is None")
        except serial.SerialException:
            print(f"ERROR: Timeout ({self.timeout}s), could not connect to PORT: "+port)
            if self.handle:
                self.disconnect()
            raise

    def disconnect(self):
        time.sleep(1)
        self.handle.close()
        self.handle = None  # TODO CHECK!

    def wait_for_read(self):
        res = ''
        for i in range(30):
            if 'ok' in res:
                print('done')
                return res
            else:
                time.sleep(1)
                res_r = self.handle.readall()
                res_s = self.strip_response(res_r)
                res += res_s
                print("waiting", i, "res:", res_r, "--", res)

    def write_sp(self, str, val):
        print(f"\nWriting {str}...")
        cmd = f"{val}{dict[str]['w']}\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)
        res = self.wait_for_read()
        print(f"Response {str} =", res)

    def read_sp(self, str):
        print(f"\nReading {str}...")
        cmd = f"?{dict[str]['r']}\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)
        res = self.wait_for_read()
        print(f"Response {str} =", res)

dict = {
    'goto nm': {'r': 'NM', 'w':' NM'},
    'scan nm': {'r': 'NM', 'w':'NM'},
    'scan rate': {'r': 'NM/MIN', 'w': ' NM/MIN'},
    'grating': {'r': 'GRATING', 'w': ' GRATING'},
    'info gratings': {'r': 'GRATINGS'},
    }

sp = SP2750()
sp.connect("COM4")
sp.main()
sp.disconnect()

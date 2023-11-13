
import serial
import time

# Driver files?
# ftser2k.sys
# serenum.sys
# ftcserco.dll
# ftserui2.dll

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


# TODO:
#  - set up connection
#  - read grating
#  - test read commands (such as grating)

"""
Writing grating...
waiting 0 res b'2 GRATING  ok\r\n'
Response grating = 2 GRATING  ok


Writing nm...
waiting 0 res b'750.0NM 750.0NM ? \r\n'
Response nm = 750.0NM 750.0NM ? 


Reading nm...
waiting 0 res b'?NM 749.998 nm  ok\r\n'
Response nm = ?NM 749.998 nm  ok


Reading grating...
waiting 0 res b'?GRATING 2  ok\r\n'
Response grating = ?GRATING 2  ok

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

        self.read_nm_scan_rate()
        self.write_nm_scan_rate(500.0)
        self.read_nm_scan_rate()

        #self.write_grating(grating=1)
        #self.write_nm(nm=700.0)
        #self.read_nm()  # Response nm = ?NM 749.977 nm  ok
        #self.read_grating()
        #self.read_all_gratings()

    def strip_response(self, res):
        res = res[:-2]  # removing carriage return and line feed
        res_s = res.decode("ASCII")
        #print(f"({res}) ({res_s}), ({len(res_s)})")
        return res_s

    def connect(self, port):
        try:
            print("Establishing connection...")
            self.handle = serial.Serial(
                port=port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.databits,
                timeout=self.timeout)

            """if self.handle.isOpen():
                print("Handle is open!")
            else:
                self.handle.open()
                print("handle after open:", self.handle)"""

            if self.handle:
                print("Successfully connected to PORT:", port)
                print("Serial handle:", self.handle)
            else:
                print("ERROR: handle still None")

        except serial.SerialException:
            print(f"ERROR: Timeout ({self.timeout}s), could not connect to PORT: "+port)
            if self.handle:
                self.disconnect()
            raise

    def disconnect(self):
        time.sleep(1)
        self.handle.close()
        #print("handle after close:", self.handle, "?= None")
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
                #res = res_r.decode("ASCII")

                res_s = self.strip_response(res_r)
                res += res_s  # res_r.decode("ASCII")
                print("waiting", i, "res:", res_r, "--", res)

    def read_grating(self):
        print("\nReading grating...")
        cmd = "?GRATING\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()
        print("Response grating =", res)

    def read_all_gratings(self):
        print("\nReading all grating...")
        cmd = "?GRATINGS\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()

        print("Response grating =", res)

    def write_grating(self, grating):
        print("\nWriting grating...")
        cmd = f"{grating} GRATING\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()

        print("Response grating =", res)

    def read_nm_scan_rate(self):
        print("\nReading NM/MIN ...")
        cmd = "?NM/MIN\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()

        print("Response nm =", res)

    def write_nm_scan_rate(self, val):
        print("\nReading NM/MIN ...")
        cmd = f"{val} NM/MIN\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()

        print("Response nm =", res)

    def read_nm(self):
        print("\nReading nm...")
        cmd = "?NM\r"
        cmd_b = cmd.encode("ASCII")
        print(cmd_b)
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()

        print("Response nm =", res)

    def write_nm(self, nm):
        print("\nWriting GOTO nm...")
        #cmd = f"GRATING {grating}\r"
        cmd = f"{nm} NM\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()

        print("Response nm =", res)
        #time.sleep(20)

    def write_scan_to_nm(self, nm):
        print("\nWriting GOTO nm...")
        #cmd = f"GRATING {grating}\r"
        cmd = f"{nm}NM\r"
        cmd_b = cmd.encode("ASCII")
        self.handle.write(cmd_b)    # return carriage
        res = self.wait_for_read()

        print("Response nm =", res)
        #time.sleep(20)


sp = SP2750()
sp.connect("COM4")
sp.main()
sp.disconnect()


"""

 1  600 g/mm BLZ=  750NM 
 2  150 g/mm BLZ=  800NM 
 3 1800 g/mm BLZ= H-VIS  
 
 4 1800 g/mm BLZ= H-VIS  
 5  600 g/mm BLZ=  750NM 
 6  150 g/mm BLZ=  800NM 
 7  Not Installed     
 8  Not Installed     
 9  Not Installed     




"""
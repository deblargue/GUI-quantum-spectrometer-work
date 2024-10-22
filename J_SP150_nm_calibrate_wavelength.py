#calibration for wavelengths

from tabulate import tabulate
import numpy as np
from scipy.optimize import curve_fit
import matplotlib
import matplotlib.pyplot as plt

import serial
import time


# ------------ ANALYSIS: ------------

def get_polyfit(x_list, y_list):

    if len(x_list) == 0 or len(y_list) == 0:
        print("TRYING TO EXTRAPOLATE FROM EMPTY LIST. USING OLD DEFAULT VALUES")
        x_list = [532.0, 650.0]
        y_list = [529.0, 656.0]

    # Polynomial coefficients, highest power first. If y was 2-D, the coefficients for k-th data set are in p[:,k].
    coeff = np.polyfit(np.array(x_list), np.array(y_list), 1)
    a = coeff[0]
    b = coeff[1]
    print(f"Regression line: y = {round(a, 4)} x + {round(b, 4)}")

    return a, b

def RMSE(a, b, des, cal):
    x_desired = np.array(des)   # the desired
    y_prediction = (a*x_desired) + b
    y_calibration = np.array(cal)

    error = np.sqrt(np.mean(np.square(y_prediction - y_calibration)))
    return error #np.sqrt(((np.array(y_calibration) - np.array(y_prediction)) ** 2).mean())

def plot_calibration(x_list, y_list):

    a, b = get_polyfit(x_list, y_list)
    print('RMS Error=', round(RMSE(a, b, x_list, y_list), 4))
    rms_error = RMSE(a, b, x_list, y_list)

    x = [0, 1000]   # arbitrary limits since we have the slope on the line. (i think)
    y = [(a*x_i)+b for x_i in x]

    plt.figure()

    #for i in range(len(x_list)):
    #plt.scatter(x_list[i], y_list[i])  # label=f'({x_list[i]}, {y_list[i]})')

    plt.scatter(x_list, y_list, label="Calibrated wavelengths")  # label=f'({x_list[i]}, {y_list[i]})')
    plt.plot(x, y, 'r-', label="Linear regression")
    plt.xlabel("Actual wavelength (nm)")
    plt.ylabel("Adjusted wavelength (nm)")
    plt.title(f"Calibration for the spectrometer\n(RMSE={round(rms_error, 4)})")
    plt.legend(loc="best", framealpha=1)
    plt.grid()
    #plt.savefig("Calibration curve.png", format='png', dpi=300)


    #plt.show()
    #plt.close()

# ------------ SERIAL: ------------

def connect_serial(port='COM4'):

    # ----
    handle = serial.Serial(port=port, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
    if handle:
        print("Successfully connected to PORT:", 'COM4')
        #for thing in handle:
        #    print('>', thing)
        #print("Serial handle:", handle)
        #time.sleep(1)
        return handle
    else:
        print("ERROR: Could not connect to handle")
        return None

def create_cmd(cmd_type, value=None):
    if value is None:
        cmd_in = f"{lookup_dict[cmd_type]['cmd']}"   # reading
    else:
        cmd_in = f"{value}{lookup_dict[cmd_type]['cmd']}"  # writing

    return cmd_in.encode('utf-8')

def send_cmd(type, handle, value=None, speed=None):

    strip_i = lookup_dict[type]['strip']
    time_iter = lookup_dict[type]['time']

    # If we are writing a value, get the approx marginal time we need to wait for a response
    if time_iter == -1:
        time_iter, curr_val = calcualte_time_iter(handle, value)
        if value:
            if abs(value - curr_val) > 100:
                cmd = create_cmd('write scan speed', 1000.0)
                ans = input(f'cmd={cmd}. Continue?')
                if ans == 'y':
                    handle.write(cmd)
                else:
                    print("cancelled")
                    return -1

                ans = input(f'You are asking for a large change in wavelength (delta={abs(value - curr_val)}).\n>>> Do you wish to proceed with the change? (y/n) ')
                if ans in ['y', 'Y', 'yes']:
                    pass
                else:
                    print(f'You answered {ans}. Canceling change by request.')
                    return -1

    if strip_i is None:  # default value
        strip_i = [0, -2]

    cmd = create_cmd(type, value)

    if cmd is None:
        print("COMMAND IS NONE")
        return -1  # TODO: MAYBE ADD SOMETHING HERE

    handle.write(cmd)
    # 3) WAIT FOR OK SIGN
    res = ''
    off_time = 1  # seconds between each request
    #print('write done, cmd=', cmd)
    for i in range(int(off_time*time_iter)):
            if 'ok' in res:
                res = res[strip_i[0]:strip_i[1]]
                #print('OK FOUND --> done! \nFinal response:', res)

                if speed:
                    cmd = create_cmd('write scan speed', 100)
                    ans = input(f'cmd={cmd}. Continue?')
                    if ans == 'y':
                        handle.write(cmd)

                return res

            else:
                time.sleep(off_time//4)  # time.sleep(round(off_time/4, 2))
                res_r = handle.readall()
                res += res_r.decode("ASCII")  # ASCII
                if value:
                    print(f'({i}/{time_iter})', "--> Response so far:", res)
                else:
                    if i > 10:
                        print(f'({i}/{time_iter})', "--> Response so far:", res)

    print("ERROR: NO Response Found, talk to Julia to check for bug")
    #if handle:
    #    handle.close()
    #    #exit()
    #exit()

    if speed:   # change write scan speed back to 100
        cmd = create_cmd('write scan speed', 100)
        ans = input(f'cmd={cmd}. AT END Continue?')
        if ans == 'y':
            handle.write(cmd)

    return -1


# ------------ CALIBRATION: ------------

def calcualte_time_iter(handle, new_val):
    max_wait = 20  # upper limit for how long we should wait
    scan_speed = send_cmd('read scan speed', handle)
    current_nm = send_cmd('read nm value', handle)

    return np.max([int(60 * (np.abs(float(current_nm) - float(new_val)) / float(scan_speed))), max_wait]), round(float(eval(current_nm)), 1)  # in seconds


# ------------ MAIN: ------------

def get_menu(step_size):
    menu_str = f" ------------------------------MENU--------------------------------" \
               f"\n  ->     ***.*                 (move to given wavelength)" \
               f"\n  ->     u / U / up            (toggle step +{step_size} nm)           "\
               f"\n  ->     d / D / down          (toggle step -{step_size} nm)           " \
               f"\n  ->     s / S / step          (change step size of toggle in nm)      " \
               f"\n  ->     g / G / goto          (goto corrected wavelength given nm)      " \
               f"\n  ->     a / A / accept        (accept and save calibration wavelength)" \
               f"\n  ->     c / C / change        (start a new calibration wavelength)    " \
               f"\n  ->     t / T / table         (display table of saved calibrations so far)" \
               f"\n  ->     i / I / insert        (insert value into calibration table)" \
               f"\n  ->     r / R / remove        (remove value from calibration table)" \
               f"\n  ->     l / L / line          (display equation for alignment regression line)" \
               f"\n  ->     p / P / plot          (plot the saved calibrations so far)    " \
               f"\n  ->     save                  (save calibrations to text file)    " \
               f"\n  ->     load                  (load calibrations from text file)    " \
               f"\n  ->     e / E / exit          (stop calibration program)              " \
               f"\n------------------------------------------------------------------"
    return menu_str

def main():

    step_size = 0.5    # +- step size for toggle nm
    handle = None      # NOTE: THIS IS INIT, i.e. OUTSIDE PROGRAM LOOP
    running = True

    print(f"\n------------------------------------------------------------------"
          f"\n               WELCOME TO THE WAVELENGTH CALIBRATION              "
          f"\n------------------------------------------------------------------")

    try:
        handle = connect_serial()
        current_nm = float(send_cmd('read nm value', handle))
        print(f"\nCURRENT DEVICE NM: {current_nm} nm")

        saved_calibrations = {
            532.0 : 529,
            650.0 : 656.0
        }
        table_head = ["Laser", "Calibrated"]

        current_desired_nm = None

        while running:   # This is the program loop that will keep asking for new wave lengths until we are done

            # 1) Check if we need reconnecting
            if handle is None:  # in case we need to disconnect
                handle = connect_serial()

            if current_desired_nm is None:
                try:
                    temp = float(input("\n>>> Wavelength you would like to calibrate for: "))
                    current_desired_nm = temp
                except:
                    print('Failed to set new desired wavelength. Try Again')
                    current_desired_nm = None

            # 2) Check and display current value
            #current_nm = float(send_cmd('read nm value', handle))
            new_nm = None
            print("\n__________________________________________________________________")
            print("__________________________________________________________________\n")
            #print("\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
            print(f"CALIBRATING FOR WAVELENGTH = {current_desired_nm} nm")
            print(f"CURRENT DEVICE WAVELENGTH = {current_nm} nm")

            # 3) Ask for input
            menu_str = get_menu(step_size)
            print(menu_str)
            res = input(f">>> Choose menu option: ")

            # 4) Check response
            if res in ['u', 'U', 'up']:  # toggle up
                new_nm = float(current_nm) + step_size

            elif res in ['d', 'D', 'down']:  # toggle down
                new_nm = float(current_nm) - step_size

            elif res in ['s', 'S', 'step']:  # change step for toggle
                step_size = int(input("\n>>> New step size = "))
                continue

            elif res in ['c', 'C', 'change']:  # change to new desired calibration wavelength
                current_desired_nm = None
                continue

            elif res in ['t', 'T', 'table']:  # plot the current calibration values

                x = [xi for xi in saved_calibrations.keys()]
                y = [yi for yi in saved_calibrations.values()]

                print("Calibration table")
                table_data = []
                for key in saved_calibrations.keys():
                    table_data.append([key, saved_calibrations[key]])

                # display table
                print(tabulate(table_data, headers=table_head, tablefmt="grid"))

                if len(saved_calibrations.keys()) < 2:
                    print("Not enough points to get RMS error")
                    continue

                a, b = get_polyfit(x, y)
                print('RMS Error=', round(RMSE(a, b, x, y), 4))

            elif res in ['g', 'G', 'goto']:  # plot the current calibration values
                try:
                    if len(saved_calibrations.keys()) < 2:
                        print("Not enough values in table. Can not get regression. Try again!")
                        continue

                    goto_nm_actual = float(input(f">>> Which laser wavelength would you like to go to? "))
                    """if goto_nm_actual in saved_calibrations.keys():
                        goto_nm_calibration = round(saved_calibrations[goto_nm_actual], 1)
                        ans = input(f">>> Do you want to go to the calibrated value: {new_nm} nm? ")
                        if ans in ['y', 'Y', 'yes']:
                            new_nm = goto_nm_calibration
                        else:
                            print("Cancelled goto.")
                    else:
                        print(f"{goto_nm_actual} nm does not have a saved calibration value. Try again")"""

                    a, b = get_polyfit([xi for xi in saved_calibrations.keys()], [yi for yi in saved_calibrations.values()])
                    goto_nm_calibration = round(float((a*goto_nm_actual) + b), 1)

                    ans = input(f">>> Do you want to go to the calibrated value: {goto_nm_calibration} nm? ")
                    if ans in ['y', 'Y', 'yes']:
                        new_nm = goto_nm_calibration
                    else:
                        print("Cancelled goto.")
                        new_nm = None
                except:
                    print("Error with input. Try again.")

            elif res in ['i', 'I', 'insert']:  # plot the current calibration values
                try:
                    temp_new_actual = round(float(input(">>> Entry for LASER wavelength: ")), 1)
                    temp_new_calibration = round(float(input(">>> Entry for CALIBRATION wavelength: ")), 1)

                    if temp_new_actual in saved_calibrations.keys():
                        ans = input(f"WARNING: There is already a saved entry for {temp_new_actual} nm!\n>>> Would you like to overwrite the saved calibration value "
                                    f"which is {saved_calibrations[temp_new_actual]} nm? (y/n) ")
                        if ans in ['y', 'Y', 'yes']:
                            saved_calibrations[temp_new_actual] = temp_new_calibration
                        else:
                            print("Did not save new value.")
                    else:
                        saved_calibrations[temp_new_actual] = temp_new_calibration

                except:
                    print("Incorrect input into table. Try again.")

            elif res in ['r', 'R', 'remove']:  # plot the current calibration values

                x = [xi for xi in saved_calibrations.keys()]
                y = [yi for yi in saved_calibrations.values()]

                print("Current calibration table")
                table_data = []
                for key in saved_calibrations.keys():
                    table_data.append([key, saved_calibrations[key]])
                # display table
                print(tabulate(table_data, headers=table_head, tablefmt="grid"))

                try:
                    temp_new_actual = float(input(">>> Remove entry for LASER wavelength: "))
                    if temp_new_actual in saved_calibrations.keys():
                        old_val = saved_calibrations[temp_new_actual]
                        del saved_calibrations[temp_new_actual]
                        print(f"Removed entry: {temp_new_actual} with calibration value {old_val}")
                    else:
                        print(f"Could not find {temp_new_actual} in table. Try again.")
                except:
                    print("Incorrect deletion from table. Try again.")

            elif res in ['p', 'P', 'plot']:  # plot the current calibration values

                x = [xi for xi in saved_calibrations.keys()]
                y = [yi for yi in saved_calibrations.values()]

                print("Calibration table")
                table_data = []
                for key in saved_calibrations.keys():
                    table_data.append([key, saved_calibrations[key]])

                if len(saved_calibrations.keys()) < 2:
                    print("Not enough points to plot")
                    continue

                # display table
                print(tabulate(table_data, headers=table_head, tablefmt="grid"))
                #a, b = get_polyfit(x, y)
                #print('RMS Error=', round(RMSE(a, b, x, y), 4))

                plot_calibration(x, y)  # a, b = get_polyfit(x_list, y_list)
                plt.show()

                continue

            elif res in ['l', 'L', 'line']:
                x = [xi for xi in saved_calibrations.keys()]
                y = [yi for yi in saved_calibrations.values()]
                _, _ = get_polyfit(x, y)  # a, b = get_polyfit(x_list, y_list)

            elif res in ['a', 'A', 'accept']:  # plot the current calibration values
                saved_calibrations[current_desired_nm] = current_nm
                current_desired_nm = None   # NOTE: MAYBE REMOVE
                continue

            elif res in ['save']:  # save configs to file
                try:
                    filename = input(">>> Enter save filename: ")
                    if not filename.endswith('.txt'):
                        filename += '.txt'

                    with open(filename, 'w') as f:
                        f.writelines([f"{key} {saved_calibrations[key]}\n" for key in saved_calibrations.keys()])
                        f.close()
                    print("Saved calibrations to:", filename)
                except:
                    print("Failed to save to file:", filename)
                    raise

            elif res in ['load']:  # exit the program
                try:
                    filename = input("Enter load filename: ")
                    if filename.endswith('.txt'):
                        saved_calibrations = {}
                        with open(filename, 'r') as f:
                            data = f.readlines()
                            f.close()
                        for entry in data:
                            key, val = entry.strip("\n").split(" ")
                            saved_calibrations[eval(key)] = eval(val)
                            print(key, "-->", val)
                        print(f"Loaded configs from file: {filename}")
                    else:
                        print("Invalid filename. Try again")
                        raise
                except:
                    print("Error trying to read from config file")
                    raise

            elif res in ['e', 'E', 'exit']:  # exit the program
                if handle:
                    handle.close()
                    handle = None
                running = False
                continue

            else:
                # - note: make sure that the separator is a decimal and not a comma
                try:
                    new_nm = round(float(eval(res)), 1)
                except:
                    print(f"ERROR IN INPUT ('{res}'), TRY AGAIN")
                    continue


            # 5) Check if input is ok
            if new_nm is not None:
                if 0.0 <= new_nm <= 1000.0:  # if in range, send value
                    # 7) Send new value
                    if isinstance(new_nm, float):
                        new_nm = round(new_nm, 1)
                        print(f"new wavelength to set = {new_nm} nm")
                        _ = send_cmd('write nm value', handle, new_nm)
                        current_nm = float(send_cmd('read nm value', handle))
                    else:
                        print('Not a float!')

                else:
                    print("WARNING: Desired wavelength is outside allowed range [0, 1000] nm")


        if handle:
            handle.close()
            handle = None

        print(f"\n------------------------------------------------------------------"
              f"\n                 CALIBRATION PROGRAM TERMINATED                   "
              f"\n------------------------------------------------------------------")

    except:
        if handle:
            handle.close()
            handle = None
            print("(Forced close handle due to error)")
        raise


# ------------------------------------

lookup_dict = {
    'read scan speed': {
        'info': f'\n----------\nChecking scan speed',
        'cmd': '?NM/MIN\r',
        'time': 20,
        'strip': [8, -6],
        'unit': 'nm/min',
        'default': 100,
    },

    'write scan speed': {
        'info': f'\n----------\nWriting scan speed',
        'cmd': ' NM/MIN\r',
        'time': 20,
        'strip': [8, -6],
        'unit': 'nm/min',
        'default': 100,
    },

    'read nm value': {
        'info': f'\n----------\nChecking current wavelength',
        'cmd': '?NM\r',
        'time': 20,
        'strip': [4, -6],
        'unit': 'nm',
    },

    'write nm value': {
        'info': f'\n----------\nSending new wavelength',
        'cmd': ' NM\r',  # note: to use this we do-->  cmd =  f"{value}{lookup_dict['write nm value']['cmd']}"
        'time': -1,
        # NOTE THIS MEANS WE NEED TO CALCULATE THE TIME ITER BASED ON HOW FAR AWAY WE ARE ---> # wait_iter = np.max([int(60*(np.abs(float(current_nm) - new_val)/float(scan_speed))), 20])  # in seconds
        'strip': [0, -9],
        'unit': 'nm',
    }
}

main()

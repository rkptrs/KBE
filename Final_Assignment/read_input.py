from airfoil import get_airfoil
from parapy.geom import Point
from tkinter import Tk, mainloop, X, messagebox
import warnings


def get_line(f, number=True):           # Function for reading a line of f and returning the number specified in the line
    line = f.readline()
    mode = 0                            # this indicates that the number part of the string was not reached
    out = ""
    for s in line:
        if mode == 1:                   # mode 1 indicates that we are within the number part
            if s == " " or s == "\n" or s == "\t":  # pass if the symbol is a space, tab or new line
                pass
            elif s == "#":               # "#" is used for comments after number and means that all of the number was read
                break
            else:
                out += s                 # append character to string
        elif s == "=":
            mode = 1                     # number part starts once "=" is reached
    if number:                           # convert to float if the parameter is a number
        return float(out)
    else:
        return out


class get_input:                # class for reading planform input file. returns an instance with all the parameters as attributes of the class
    def __init__(self, name):
        exception = False       # variable turned to True if a problem occurs
        try:
            f = open(name)      # open file if it exists, if not then give error message
        except:
            error("Planform file with specified name does not exist. Default planform was loaded instead.")
            f = open("program_files/default_planform.txt")
            exception = True

        self.wing_span = get_line(f)        # read all parameters in the order of the planform text file
        self.root_chord = get_line(f)
        self.taper_inner = get_line(f)
        self.taper_outer = get_line(f)
        self.kink_position = get_line(f)
        self.flap_gap = get_line(f)
        self.sweep_deg = get_line(f)
        self.dihedral_deg = get_line(f)
        self.front_spar = get_line(f)
        self.rear_spar = get_line(f)
        self.outer_flap_lim = get_line(f)
        self.fuselage_radius = get_line(f)
        self.clmax = get_line(f)
        self.twist = get_line(f)
        self.speed = get_line(f)
        self.airfoil_name = get_line(f, number=False)
        self.flap_type = get_line(f, number=False)


        if exception:
            self.colour = "red"                 # set color to red if an exception occurred. this will make the model appear red to notify user
            self.valid = False                  # also make this false for other functions to know input is not valid
        else:
            self.colour = "yellow"
            self.valid = True

        coords = get_airfoil(self.airfoil_name)     # read airfoil coordinates file and save that as an input variable as well
        self.airfoil_coordinates = []
        for i in range(len(coords[0])):             # convert tuple format of coordinates to Point format
            self.airfoil_coordinates.append(Point(coords[0][i], 0, coords[1][i]))


def check_input(out, name):     # this function is used to check whether the input variables are within the specified limits
    minimum = get_input("program_files/planform_min_values.txt")            # minimum values are saved in this file
    maximum = get_input("program_files/planform_max_values.txt")            # maximum values are here
    parameters = list(out.__dict__.keys())                                  # get the attributes of all parameters to be compared

    for parm in parameters[0:parameters.index("speed")+1]:                                                      # only variables up to "speed" are numbers so we dont want to compare any further
        if not minimum.__getattribute__(parm) <= out.__getattribute__(parm) <= maximum.__getattribute__(parm):  # make comparison
            out.valid = False                                                                                   # set valid to false is parameter is outside of limits and raise appropriate error
            warnings.warn("Input parameter " + parm + " as specified in '" + name +
                          "' is outside of the allowed limits of " + str(minimum.__getattribute__(parm)) + "-" +
                          str(maximum.__getattribute__(parm)) + ".")

    # also check for other consistencies
    if out.kink_position > out.wing_span + 1:                                                                   # make sure kink is within the wing span
        out.valid = False
        msg = "Position of kink is closer than 1 m to or behind the leading edge which is not allowed."
        warnings.warn(msg)
    if out.wing_span - out.flap_gap - out.fuselage_radius < 1:                                                  # make sure there is at least some room for flaps
        out.valid = False
        warnings.warn("The wing contains less than 1 m of span available for HLDs which is not allowed.")
    if len(out.airfoil_coordinates) < 50:                                                                       # check that there are at least 50 points in airfoil coordinates
        warnings.warn("Airfoil coordinates file does not contain at least 50 points which is the minimum required amount.")
        out.valid = False
    if out.wing_span*out.outer_flap_lim < out.kink_position + out.flap_gap + 0.5:                               # make sure there is enough room for outer flap
        warnings.warn("Specified outer flap limit is too close to the kink")
        out.valid = False

    if not out.valid:                                                                                           # in order for the program to not crash, default values will be loaded if there is a problem
        out = get_input("program_files/default_planform.txt")
        out.colour = "red"
        warnings.warn("Default planform file was loaded instead of '" + name + "'.")
        error("One or more planform inputs are invalid, check console for more details. Default planform parameters were loaded instead of ones specified in requested file")
    return out


def error(msg):     # function for displaying error popup
    window = Tk()
    window.withdraw()
    messagebox.showwarning("Invalid Input", msg)


def custom_warning(msg, *args, **kwargs):   # function for making warnings in console more concise and not display location of error and the message twice
    return str(msg) + '\n'


warnings.formatwarning = custom_warning     # format warning function using the one above

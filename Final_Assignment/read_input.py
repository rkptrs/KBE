from airfoil import get_airfoil
from parapy.geom import Point
from tkinter import Tk, mainloop, X, messagebox
import warnings


def get_line(f, number=True): # Function for reading a line of f and returning the number specified in the line
    line = f.readline()
    mode = 0    
    out = ""
    for s in line:
        if mode == 1:
            if s == " " or s == "\n" or s == "\t":
                pass
            elif s == "#":
                break
            else:
                out += s
        elif s == "=":
            mode = 1
    if number:
        return float(out)
    else:
        return out


class get_input:
    def __init__(self, name):
        exception = False
        try:
            f = open(name)
        except:
            error("Planform file with specified name does not exist. Default planform was loaded instead.")
            f = open("program_files/default_planform.txt")
            exception = True

        self.wing_span = get_line(f)
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
            self.colour = "red"
            self.valid = False
        else:
            self.colour = "yellow"
            self.valid = True

        coords = get_airfoil(self.airfoil_name)
        self.airfoil_coordinates = []
        for i in range(len(coords[0])):
            self.airfoil_coordinates.append(Point(coords[0][i], 0, coords[1][i]))


def check_input(out, name):
    minimum = get_input("program_files/planform_min_values.txt")
    maximum = get_input("program_files/planform_max_values.txt")
    parameters = list(out.__dict__.keys())
    for parm in parameters[0:parameters.index("speed")+1]:
        if not minimum.__getattribute__(parm) <= out.__getattribute__(parm) <= maximum.__getattribute__(parm):
            out.valid = False
            warnings.warn("Input parameter " + parm + " as specified in '" + name +
                          "' is outside of the allowed limits of " + str(minimum.__getattribute__(parm)) + "-" +
                          str(maximum.__getattribute__(parm)) + ".")

    if out.kink_position > out.wing_span + 1:
        out.valid = False
        msg = "Position of kink is closer than 1 m to or behind the leading edge which is not allowed."
        warnings.warn(msg)
    if out.wing_span - out.flap_gap - out.fuselage_radius < 1:
        out.valid = False
        warnings.warn("The wing contains less than 1 m of span available for HLDs which is not allowed.")
    if len(out.airfoil_coordinates) < 50:
        warnings.warn("Airfoil coordinates file does not contain at least 50 points which is the minimum required amount.")
        out.valid = False
    if out.wing_span*out.outer_flap_lim < out.kink_position + out.flap_gap + 0.5:
        warnings.warn("Specified outer flap limit is too close to the kink")
        out.valid = False

    if not out.valid:
        out = get_input("program_files/default_planform.txt")
        out.colour = "red"
        warnings.warn("Default planform file was loaded instead of '" + name + "'.")
        error("One or more planform inputs are invalid, check console for more details. Default planform parameters were loaded instead of ones specified in requested file")
    return out


def error(msg):
    window = Tk()
    window.withdraw()
    messagebox.showwarning("Invalid Input", msg)


def custom_warning(msg, *args, **kwargs):
    return str(msg) + '\n'


warnings.formatwarning = custom_warning

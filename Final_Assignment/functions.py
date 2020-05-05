from parapy.geom import *
from parapy.core import *
import numpy as np


def p2v(point):
    return Vector(point[0], point[1], point[2])


def v2p(vector):
    return Point(vector[0], vector[1], vector[2])


def hinge_position(hinge_point):
    position = translate(XOY, "x", hinge_point[0],
                         "y", hinge_point[1],
                         "z", hinge_point[2])
    return rotate(position, "x", np.pi / 2)


def split_coordinates(airfoil_coordinates):
    x, z = [], []
    for c in airfoil_coordinates:
        x.append(c[0])
        z.append(c[2])
    xb, zb = x[0:int(len(x)/2)], z[0:int(len(z)/2)]
    xt, zt = x[int(len(x)/2):], z[int(len(z)/2):]
    return xb, zb, xt, zt


def interp_coords(x_list, z_list, x_target):
    x = list(abs(np.array(x_list) - x_target))
    closest1 = x.index(min(x))
    x[closest1] = 100
    closest2 = x.index(min(x))
    dx = abs(x_list[closest1] - x_list[closest2])
    z_target = (z_list[closest1]*abs(x_list[closest2]-x_target) + z_list[closest2]*abs(x_list[closest1]-x_target))/dx
    return z_target


class v:
    md = 0.0001

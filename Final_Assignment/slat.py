from parapy.geom import *
from parapy.core import *
from functions import p2v, v2p, interp_coords, split_coordinates, hinge_position
from wing_section import Wing_base
import numpy as np


class Slat(Base):
    points = Input()
    chords = Input()
    wing_solid = Input()
    point = Input(Point(0.2, 0, -0.2))


    @Attribute
    def circle_center(self):
        out = [0, 0]
        for i in range(2):
            out[i] = self.point + p2v(self.points[i])
        return out

    @Attribute
    def flap_split_cylinder(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.hinge_points[i])
            circles[i] = Circle(self.hinge_dimension[1]*self.chords[i]/2*1.01, position)
        cylinder = RuledSurface(circles[0], circles[1])
        return SplitSurface(cylinder, self.wing_surf).faces[4]

    @Part
    def m(self):
        return Solid(self.wing_solid)

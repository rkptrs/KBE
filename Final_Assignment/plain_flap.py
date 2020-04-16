from parapy.geom import *
from parapy.core import *
from functions import p2v, hinge_position
from wing_section import Wing_base
import numpy as np


class Plain_flap_section(Wing_base):

    @Attribute
    def hinge_points(self):
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location*self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + self.hinge_dimension[0]*self.chords[i])
        return out

    @Attribute
    def flap_split_cylinder(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.hinge_points[i])
            circles[i] = Circle(self.hinge_dimension[1]*self.chords[i]/2*1.01, position)
        cylinder = RuledSurface(circles[0], circles[1])
        return SplitSurface(cylinder, self.wing_surf).faces[4]

    @Attribute
    def wing_surf(self):
        return RuledSurface(self.airfoils[0], self.airfoils[1])

    @Attribute
    def wing_parts(self):
        return SplitSolid(self.wing_solid, self.flap_split_cylinder)

    @Part
    def main_wing(self):
        return Solid(self.wing_parts.solids[1])

    @Part
    def flap(self):
        return RotatedShape(self.wing_parts.solids[0], self.hinge_points[0],
                            p2v(self.hinge_points[0])-p2v(self.hinge_points[1]),
                            angle=-self.flap_deflection*np.pi/180)

from parapy.geom import *
from parapy.core import *
from functions import p2v, v2p, interp_coords, split_coordinates, hinge_position
from wing_section import Wing_base
import numpy as np


class Slotted_flap_section(Wing_base):

    @Attribute
    def centers_1(self):
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location*self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + (self.hinge_dimension[0] - self.hinge_dimension[1]/4)*self.chords[i])
        return out

    @Attribute
    def lower_arc(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.centers_1[i])
            circles[i] = Arc(self.hinge_dimension[1]*self.chords[i]/4, angle=3*np.pi/2, position=position,
                             start=self.centers_1[i] + Vector(-1, 0, 0), color="Green")
        return circles

    @Attribute
    def upper_points(self):
        xb, zb, xt, zt = split_coordinates(self.airfoil_coordinates)
        points_1, points_2, points_3 = [], [], []
        x_1 = self.flap_hinge_location + 0.5 * self.hinge_dimension[1]
        x_2 = x_1 + 0.001
        z_1, z_2 = interp_coords(xt, zt, x_1), interp_coords(xt, zt, x_2)
        for i in range(2):
            points_1.append(self.points[i] + Vector(x_1, 0, z_1+0.001)*self.chords[i])
            points_2.append(self.points[i] + Vector(x_2, 0, z_2+0.001)*self.chords[i])
            points_3.append(self.centers_1[i] + Vector(-self.hinge_dimension[1]/4*self.chords[i], 0, 0))
        return points_1, points_2, points_3

    @Attribute
    def safety_line(self): ### better safety lines when tangent?
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.centers_1[i] + Vector(0, 0, -self.hinge_dimension[1])*self.chords[i]/4,
                self.centers_1[i] + Vector(-self.hinge_dimension[1], 0, -self.hinge_dimension[1])*self.chords[i]/4]))
        return lines

    @Attribute
    def split_arcs(self):
        arcs = []
        for i in range(2):
            upper_arc = Arc3P(self.upper_points[1][i], self.upper_points[0][i], self.upper_points[2][i])
            arcs.append(Wire([upper_arc, self.lower_arc[i]]).compose())
        return arcs

    @Attribute
    def wing_surf(self):
        return RuledSurface(self.airfoils[0], self.airfoils[1])

    @Attribute
    def split_surface(self):
        return RuledSurface(self.split_arcs[0], self.split_arcs[1])

    @Attribute
    def wing_parts(self):
        return SplitSolid(self.wing_solid, self.split_surface)

    @Part
    def main_wing(self):
        return Solid(self.wing_parts.solids[1])

    @Attribute
    def hinge_location(self):
        points = []
        for i in range(2):
            points.append(self.centers_1[i] + Vector(0, 0, -self.hinge_dimension[1]*self.chords[i]))
        return points

    @Part
    def flap(self):
        return RotatedShape(self.wing_parts.solids[0], self.hinge_location[0],
                            vector=p2v(self.hinge_location[1]) - p2v(self.hinge_location[0]),
                            angle=self.flap_deflection*np.pi/180)


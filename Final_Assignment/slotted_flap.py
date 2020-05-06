from parapy.geom import *
from parapy.core import *
from functions import p2v, v2p, interp_coords, split_coordinates, hinge_position, v
from wing_section import Wing_base
import numpy as np


class Slotted_flap_section(Wing_base):

    @Attribute
    def centers1(self):
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location*self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + (self.hinge_dimension[0] - self.hinge_dimension[1]/4)*self.chords[i])
        return out

    @Attribute
    def lowerArc(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.centers1[i])
            circles[i] = Arc(self.hinge_dimension[1] * self.chords[i] / 4, angle=3*np.pi/2, position=position+Vector(0, 0, 0),
                             start=self.centers1[i] + Vector(-1, 0, 0), color="Green", mesh_deflection=v.md)
        return circles


    @Attribute
    def upperPoints(self):
        xb, zb, xt, zt = split_coordinates(self.airfoil_coordinates)
        points_1, points_2, points_3 = [], [], []
        x_1 = self.flap_hinge_location + 0.5 * self.hinge_dimension[1]
        x_2 = x_1 + 0.001
        z_1, z_2 = interp_coords(xt, zt, x_1), interp_coords(xt, zt, x_2)
        for i in range(2):

            points_1.append(self.points[i] + Vector(x_1, 0, z_1+0.001)*self.chords[i])
            points_2.append(self.points[i] + Vector(x_2, 0, z_2+0.001)*self.chords[i])
            points_3.append(self.centers1[i] + Vector(-self.hinge_dimension[1] / 4 * self.chords[i], 0, 0))
        return points_1, points_2, points_3

    @Attribute
    def lowerLine(self):
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.centers1[i] + Vector(0, 0, -self.hinge_dimension[1]) * self.chords[i] / 4,
                                      self.centers1[i] + Vector(self.hinge_dimension[1], 0, -self.hinge_dimension[1] * 2) * self.chords[i] / 4],
                                     mesh_deflection=v.md, color="green"))
        return lines

    @Attribute
    def splitArcs(self):
        arcs = []
        for i in range(2):
            upper_arc = Arc3P(self.upperPoints[1][i], self.upperPoints[0][i], self.upperPoints[2][i], mesh_deflection=v.md, color="red")
            composed_arc = Wire([upper_arc, self.lowerArc[i], self.lowerLine[i]], mesh_deflection=v.md).compose()
            adjusted_arc = TranslatedCurve(composed_arc, Vector(0, (i*2-1)*0.01))
            arcs.append(adjusted_arc)
        return arcs

    @Attribute
    def wingSurface(self):
        return RuledSurface(self.airfoils[0], self.airfoils[1], mesh_deflection=v.md)

    @Attribute
    def splitSurface(self):
        return RuledSurface(self.splitArcs[0], self.splitArcs[1], mesh_deflection=v.md, color="green")

    @Attribute
    def wingParts(self):
        return SplitSolid(self.wingSolid, self.splitSurface, mesh_deflection=v.md)

    @Part
    def mainWing(self):
        return Solid(self.wingParts.solids[1], mesh_deflection=v.md)

    @Attribute
    def hingeLocation(self):
        points = []
        for i in range(2):
            points.append(self.centers1[i] + Vector(0, 0, -self.hinge_dimension[1] * self.chords[i]))
        return points

    @Part
    def flap(self):
        return RotatedShape(self.wingParts.solids[0], self.hingeLocation[0],
                            vector=p2v(self.hingeLocation[1]) - p2v(self.hingeLocation[0]),
                            angle=self.flap_deflection*np.pi/180, mesh_deflection=v.md)


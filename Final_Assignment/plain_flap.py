from parapy.geom import *
from parapy.core import *
from functions import p2v, hinge_position, v
from wing_section import Wing_base
import numpy as np


class Plain_flap_section(Wing_base):

    @Attribute
    def hingePoints(self):
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location*self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + self.hinge_dimension[0]*self.chords[i])
        return out


    @Attribute
    def arcs(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.hingePoints[i]) + Vector(0, 0, 0)
            circles[i] = Arc(self.hinge_dimension[1] * self.chords[i]/2, angle=3 * np.pi / 2, position=position,
                start=self.hingePoints[i] + Vector(0, 0, 1), mesh_deflection=v.md, color="red")
        return circles

    @Attribute
    def lowerLine(self):
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.hingePoints[i] + Vector(0, 0, -self.hinge_dimension[1]*self.chords[i]/2),
                         self.hingePoints[i] + Vector(self.hinge_dimension[1]*self.chords[i], 0, -self.hinge_dimension[1]*self.chords[i])],
                         mesh_deflection=v.md, color="green"))
        return lines

    @Attribute
    def upperLine(self):
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.hingePoints[i] + Vector(0, 0, +self.hinge_dimension[1]*self.chords[i]/2),
                         self.hingePoints[i] + Vector(self.hinge_dimension[1]*self.chords[i], 0, +self.hinge_dimension[1]*self.chords[i])],
                         mesh_deflection=v.md, color="green"))
        return lines

    @Part(parse=False)
    def flapSplitSurface(self):
        curves = []
        for i in range(2):
            c = (i * 2 - 1) * 0.00
            flap_curve = Wire([self.upperLine[i], self.arcs[i], self.lowerLine[i]], mesh_deflection=v.md).compose()
            curves.append(TranslatedCurve(flap_curve, Vector(0, c, 0)))
        return RuledSurface(curves[0], curves[1], mesh_deflection=v.md, color="red")

    @Attribute
    def wing_parts(self):
        return SplitSolid(self.wingSolid, self.flapSplitSurface, mesh_deflection=v.md)

    @Part
    def main_wing(self):
        return Solid(self.wing_parts.solids[1], mesh_deflection=v.md)

    @Part
    def flap(self):
        return RotatedShape(self.wing_parts.solids[0], self.hingePoints[0],
                            p2v(self.hingePoints[0]) - p2v(self.hingePoints[1]),
                            angle=-self.flap_deflection*np.pi/180, mesh_deflection=v.md)

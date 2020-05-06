from parapy.geom import *
from parapy.core import *
from functions import p2v, hinge_position, v
from wing_section import WingBase
import numpy as np


class Plain_flap_section(WingBase):    # class defining a section of the wing with a plain flap
    # this class inherits from the wing base class
    # Many Attributes return a list of two. if this is the case then the first element is for the root chord and the second for the tip chord of the section

    @Attribute
    def hingePoints(self):
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location * self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + self.hingeDimension[0] * self.chords[i])
        return out


    @Attribute                  # this arc defines the LE of the flap
    def arcs(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.hingePoints[i]) + Vector(0, 0, 0)
            circles[i] = Arc(self.hingeDimension[1] * self.chords[i] / 2, angle=3 * np.pi / 2, position=position,
                             start=self.hingePoints[i] + Vector(0, 0, 1), mesh_deflection=v.md, color="red")
        return circles

    @Attribute                  # extra line coming from top of LE is defined to guarantee complete intersection with wing solid
    def lowerLine(self):
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.hingePoints[i] + Vector(0, 0, -self.hingeDimension[1] * self.chords[i] / 2),
                                      self.hingePoints[i] + Vector(self.hingeDimension[1] * self.chords[i], 0, -self.hingeDimension[1] * self.chords[i])],
                                     mesh_deflection=v.md, color="green"))
        return lines

    @Attribute
    def upperLine(self):            # extra line coming from bottom of LE is defined to guarantee complete intersection with wing solid
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.hingePoints[i] + Vector(0, 0, +self.hingeDimension[1] * self.chords[i] / 2),
                                      self.hingePoints[i] + Vector(self.hingeDimension[1] * self.chords[i], 0, +self.hingeDimension[1] * self.chords[i])],
                                     mesh_deflection=v.md, color="green"))
        return lines

    @Part(parse=False)
    def flapSplitSurface(self):     # a surface used to split the wing solid into flap and wing is defined here
        curves = []
        for i in range(2):
            c = (i * 2 - 1) * 0.00
            flap_curve = Wire([self.upperLine[i], self.arcs[i], self.lowerLine[i]], mesh_deflection=v.md).compose()      # all the curves are first stitched together
            curves.append(TranslatedCurve(flap_curve, Vector(0, c, 0)))                                                  # and translated away from wing section by
        return RuledSurface(curves[0], curves[1], mesh_deflection=v.md, color="red")                                     # small amount to guarantee intersection

    @Attribute                      # wing solid is split into wing and flap using the flap split surface defined above
    def wing_parts(self):
        return SplitSolid(self.wingSolid, self.flapSplitSurface, mesh_deflection=v.md)

    @Part
    def main_wing(self):            # main wing is second in the list of the split solids
        return Solid(self.wing_parts.solids[1], mesh_deflection=v.md)

    @Part
    def flap(self):                 # flap solid is first in the list of split solids
        return RotatedShape(self.wing_parts.solids[0], self.hingePoints[0],                     # flap must also be rotated around hinge line
                            p2v(self.hingePoints[0]) - p2v(self.hingePoints[1]),
                            angle=-self.flap_deflection*np.pi/180, mesh_deflection=v.md)

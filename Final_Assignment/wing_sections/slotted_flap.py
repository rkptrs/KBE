from parapy.geom import *
from parapy.core import *
from utilities.functions import p2v, interp_coords, split_coordinates, hinge_position, v
from wing_sections.wing_section import WingBase
import numpy as np


class Slotted_flap_section(WingBase):      # class defining a wing section with a slotted flap
    # this class inherits from the wing base class
    # Many Attributes return a list of two. if this is the case then the first element is for the root chord and the second for the tip chord of the section

    # the LE of the flap is defined using a quarter circle for the lower part and a larger arc made from 3 points for the upper part to give it its characteristic shape
    @Attribute                  # this defined the center of the quarter circles for the lower part of the LE edge of flap
    def centers1(self):
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location * self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + (self.hingeDimension[0] - self.hingeDimension[1] / 4) * self.chords[i])
        return out

    @Attribute                  # this defined the quarter circles for the lower part of the LE edge of flap
    def lowerArc(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.centers1[i])
            circles[i] = Arc(self.hingeDimension[1] * self.chords[i] / 4, angle=3 * np.pi / 2, position=position + Vector(0, 0, 0),
                             start=self.centers1[i] + Vector(-1, 0, 0), color="Green", mesh_deflection=v.md)
        return circles

    # Two points close to each other are defined just above the surface of the wing behind the LE of the flap. third point is the upper point of the arc defined above
    # This way a 3 point arc will come close to tangent with the upper surface of the wing but still above it so that there is an intersection
    # the x location of the top two points is fixed and y coordinate is obtained by interpolating the airfoil coordinates and raising it by a small amount
    @Attribute
    def upperPoints(self):
        xb, zb, xt, zt = split_coordinates(self.airfoil_coordinates)        # this splits airfoil coordinates into lower and upper
        points_1, points_2, points_3 = [], [], []
        x_1 = self.flap_hinge_location + 0.5 * self.hingeDimension[1]      # x location of of one of top points
        x_2 = x_1 + 0.001                                                   # x location of the second point is slightly behind
        z_1, z_2 = interp_coords(xt, zt, x_1), interp_coords(xt, zt, x_2)   # z locations of the two points found by interpolation
        for i in range(2):

            points_1.append(self.points[i] + Vector(x_1, 0, z_1+0.001)*self.chords[i])
            points_2.append(self.points[i] + Vector(x_2, 0, z_2+0.001)*self.chords[i])
            points_3.append(self.centers1[i] + Vector(-self.hingeDimension[1] / 4 * self.chords[i], 0, 0))
        return points_1, points_2, points_3

    # extra bit of curve is added below the leading edge in order to ensure overlap due to interpolation inaccuracies
    @Attribute
    def lowerLine(self):
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.centers1[i] + Vector(0, 0, -self.hingeDimension[1]) * self.chords[i] / 4,
                                      self.centers1[i] + Vector(self.hingeDimension[1], 0, -self.hingeDimension[1] * 2) * self.chords[i] / 4],
                                     mesh_deflection=v.md, color="green"))
        return lines

    # all of the curves defining the flap are stitched together and translated outwards away from the solid in the y direction in order to ensure overlap
    @Attribute
    def splitArcs(self):
        arcs = []
        for i in range(2):
            upper_arc = Arc3P(self.upperPoints[1][i], self.upperPoints[0][i], self.upperPoints[2][i], mesh_deflection=v.md, color="red")
            composed_arc = Wire([upper_arc, self.lowerArc[i], self.lowerLine[i]], mesh_deflection=v.md).compose()
            adjusted_arc = TranslatedCurve(composed_arc, Vector(0, (i*2-1)*0.01))
            arcs.append(adjusted_arc)
        return arcs

    # the surface that will split the wing into the flap and the rest is defined as a ruled surface using the two curves
    @Attribute
    def splitSurface(self):
        return RuledSurface(self.splitArcs[0], self.splitArcs[1], mesh_deflection=v.md, color="green")

    # The wing solid is split into the flap and the rest of the wing using the previously defined surface
    @Attribute
    def wingParts(self):
        return SplitSolid(self.wingSolid, self.splitSurface, mesh_deflection=v.md)

    # wing is second in the split solids list
    @Part
    def mainWing(self):
        return Solid(self.wingParts.solids[1], mesh_deflection=v.md)

    # hinge location for the flap is defined to be under the leading edge so that a slot appears when the flap is deflected.
    @Attribute
    def hingeLocation(self):
        points = []
        for i in range(2):
            points.append(self.centers1[i] + Vector(0, 0, -self.hingeDimension[1] * self.chords[i]))
        return points

    # flap is rotated around the hinge
    @Part
    def flap(self):
        return RotatedShape(self.wingParts.solids[0], self.hingeLocation[0],
                            vector=p2v(self.hingeLocation[1]) - p2v(self.hingeLocation[0]),
                            angle=self.flap_deflection*np.pi/180, mesh_deflection=v.md)


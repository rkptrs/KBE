from parapy.geom import *
from parapy.core import *
from utilities.functions import p2v, v2p, hinge_position, v
from wing_sections.wing_section import WingBase
from utilities.read_input import error
import numpy as np


class FowlerFlapSection(WingBase):     # wing section with a flower flap
    # this class inherits from the wing base class
    # Many Attributes return a list of two. if this is the case then the first element is for the root chord and the second for the tip chord of the section

    @Attribute
    def hingePoints(self):          # define location of the center of the hinge
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location * self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + (self.hingeDimension[0] - self.hingeDimension[1] / 4) * self.chords[i])
        return out

    @Attribute
    def flapSplitArcs(self):        # this defines the circular leading edge of the flap
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.hingePoints[i])
            circles[i] = Arc(self.hingeDimension[1] * self.chords[i] / 4, angle=3 * np.pi / 2, position=position,
                             start=self.hingePoints[i] + Vector(0, 0, 1), mesh_deflection=v.md)
        return circles

    @Attribute                      # this defines the upper surface of the flap
    def upperLine(self):
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.hingePoints[i] + Vector(0, 0, self.hingeDimension[1] * self.chords[i] / 4),
                                      Point(self.chords[i] * 1.001 + self.points[i][0], self.points[i][1],
                                            self.points[i][2]+0.001)], mesh_deflection=v.md, color="green"))
        return lines

    @Attribute                      # an extra line extending diagonally downwards from the bottom of the LE is defines in case small errors in grid make stuff not align
    def lowerLine(self):
        lines = []
        for i in range(2):
            lines.append(
                FittedCurve([self.hingePoints[i] + Vector(0, 0, -self.hingeDimension[1]) * self.chords[i] / 4,
                             self.hingePoints[i] + Vector(self.hingeDimension[1], 0,
                                                          -self.hingeDimension[1] * 2) * self.chords[i] / 4],
                            mesh_deflection=v.md, color="green"))
        return lines

    # A ruled surface is created from the above defined parts of the flap
    # This is used to split the wing solid into the flap and the rest of the wing
    @Attribute
    def flapSplitSurface(self):
        composed_1, composed_2 = [0, 0], [0, 0]
        for i in range(2):
            c = (i * 2 - 1) * 0.005
            composed_2[i] = Wire([self.upperLine[i], self.flapSplitArcs[i], self.lowerLine[i]],    # all of the lines defining the flap shape are composed
                                 mesh_deflection=v.md).compose()
            composed_2[i] = TranslatedCurve(composed_2[i], Vector(0, c, 0))     # the two lines are moved in the y direction by a small amount inwards/outwards to guarantee an overlap
        return RuledSurface(composed_2[0], composed_2[1], mesh_deflection=v.md, color="green")

    @Attribute
    def splitWing(self):  # Split wing along flap split surface
        parts = SplitSolid(self.wingSolid, self.flapSplitSurface, mesh_deflection=v.md).solids

        # Check that the wing was actually split by the flap split surface
        if len(parts) < 2:
            error("Unable to construct flap from wing geometry. Try using a different airfoil with a trailing edge more suitable for a fowler flap.")
        return parts, "Yellow"

    @Attribute
    def wingParts(self):  # Sort parts according to volume
        parts = self.splitWing[0]
        volumes = []
        for p in parts:                                 # get volumes of all parts
            volumes.append(p.volume)
        wing_index = volumes.index(max(volumes))        # make wing the part with the largest volume
        volumes[wing_index] = 0
        flap_index = volumes.index(max(volumes))        # make flap the part with the second largest volume
        return parts[wing_index], parts[flap_index]     # occasionally there can be some residual parts at the trailing edge with ~ 0 volume, they are neglected

    @Part
    def mainWing(self):
        return Solid(self.wingParts[0], mesh_deflection=v.md)

    # define the distance that the flap needs to be displaced backwards and downwards
    @Attribute
    def flapDisplacement(self):  # Defined at average chord
        if self.flap_deflection > 0:
            z_displacement_factor = - 0.5
            x_displacement = (1 - self.flap_hinge_location) * np.mean(self.chords)
            z_displacement = (-self.hingeDimension[0] - self.hingeDimension[1] * (
                    1 + z_displacement_factor)) * np.mean(self.chords)
            return Vector(x_displacement, 0, z_displacement)
        else:
            return Vector(0, 0, 0)

    # because the wing has taper, it is not enough to displace it. slight correctional rotations have to be made around x and z axis
    # z correction to allign LE of flap with TE of wing at all locations
    @Attribute
    def zRotationCorrection(self):
        dx = (1 - self.flap_hinge_location - self.flapDisplacement[0] / np.mean(self.chords)) * (
                self.chords[1] - self.chords[0]) + self.points[1][0] - self.points[0][1]
        return np.arctan(dx / (self.points[1][1] - self.points[0][1])) - self.flapSweep

    # same correction but around the x axis, this corrects the height of the flap to be scaled with the chord at all locations
    @Attribute
    def xRotationCorrection(self):
        dz = self.flapDisplacement[2]*(0.5*(self.chords[0]/self.chords[1] - 1) + 1)*(1 - self.chords[1]/self.chords[0])
        return - np.arctan(dz / (self.points[1][1] - self.points[0][1]))

    # now the flap solid is rotated according to the previous attributes
    @Attribute
    def rotatedFlap(self):
        deflected_flap = RotatedShape(self.wingParts[1], self.hingePoints[0],  # Rotate around hinge
                                      p2v(self.hingePoints[0]) - p2v(self.hingePoints[1]),
                                      angle=-self.flap_deflection * np.pi / 180, mesh_deflection=v.md)
        center_point = v2p(p2v(self.hingePoints[0]) / 2 + p2v(self.hingePoints[1]) / 2)  # Rotation point for corrections
        deflected_flap = RotatedShape(deflected_flap, center_point, Vector(0, 0, 1), angle=self.zRotationCorrection,
                                      mesh_deflection=v.md)  # Adjust rotation around z axis
        return RotatedShape(deflected_flap, center_point, Vector(1, 0, 0), angle=self.xRotationCorrection,
                            mesh_deflection=v.md)  # Adjust rotation around x axis

    @Part
    def flap(self):
        return TranslatedShape(self.rotatedFlap, displacement=self.flapDisplacement,
                               mesh_deflection=v.md)  # Translate flap backwards

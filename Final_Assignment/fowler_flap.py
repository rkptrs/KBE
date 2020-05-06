from parapy.geom import *
from parapy.core import *
from functions import p2v, v2p, hinge_position, v
from wing_section import Wing_base
from read_input import error
import numpy as np


class FowlerFlapSection(Wing_base):     # wing section with a flower flap
    # Many Attributes return a list of two 


    @Attribute
    def hingePoints(self):              # define location of the center of the hinge
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location * self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + (self.hinge_dimension[0] - self.hinge_dimension[1] / 4) * self.chords[i])
        return out

    @Attribute
    def flapSplitArcs(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.hingePoints[i])
            circles[i] = Arc(self.hinge_dimension[1] * self.chords[i] / 4, angle=3 * np.pi / 2, position=position,
                             start=self.hingePoints[i] + Vector(0, 0, 1), mesh_deflection=v.md)
        return circles

    @Attribute
    def upperLine(self):
        lines = []
        for i in range(2):
            lines.append(FittedCurve([self.hingePoints[i] + Vector(0, 0, self.hinge_dimension[1] * self.chords[i] / 4),
                                      Point(self.chords[i] * 1.001 + self.points[i][0], self.points[i][1],
                                            self.points[i][2]+0.001)], mesh_deflection=v.md, color="green"))
        return lines

    @Attribute
    def lowerLine(self):
        lines = []
        for i in range(2):
            lines.append(
                FittedCurve([self.hingePoints[i] + Vector(0, 0, -self.hinge_dimension[1]) * self.chords[i] / 4,
                             self.hingePoints[i] + Vector(self.hinge_dimension[1], 0,
                                                          -self.hinge_dimension[1] * 2) * self.chords[i] / 4],
                            mesh_deflection=v.md, color="green"))
        return lines

    @Attribute
    def flapSplitSurface(self):
        composed_1, composed_2 = [0, 0], [0, 0]
        for i in range(2):
            c = (i * 2 - 1) * 0.005
            composed_2[i] = Wire([self.upperLine[i], self.flapSplitArcs[i], self.lowerLine[i]],
                                 mesh_deflection=v.md).compose()
            composed_2[i] = TranslatedCurve(composed_2[i], Vector(0, c, 0))
        return RuledSurface(composed_2[0], composed_2[1], mesh_deflection=v.md, color="green")

    @Attribute
    def splitWing(self):  # Split wing along flap split surface
        parts = SplitSolid(self.wingSolid, self.flapSplitSurface, mesh_deflection=v.md).solids
        if len(parts) < 2:
            error("Unable to construct flap from wing geometry. Try using a different airfoil with a trailing edge more suitable for a fowler flap.")
        return parts, "Yellow"

    @Attribute
    def wingParts(self):  # Sort parts according to volume
        parts = self.splitWing[0]
        volumes = []
        for p in parts:
            volumes.append(p.volume)
        wing_index = volumes.index(max(volumes))
        volumes[wing_index] = 0
        flap_index = volumes.index(max(volumes))
        return parts[wing_index], parts[flap_index]

    @Part
    def mainWing(self):
        return Solid(self.wingParts[0], mesh_deflection=v.md)

    @Attribute
    def flapDisplacement(self):  # Defined at average chord
        if self.flap_deflection > 0:
            z_displacement_factor = - 0.5
            x_displacement = (1 - self.flap_hinge_location) * np.mean(self.chords)
            z_displacement = (-self.hinge_dimension[0] - self.hinge_dimension[1] * (
                    1 + z_displacement_factor)) * np.mean(self.chords)
            return Vector(x_displacement, 0, z_displacement)
        else:
            return Vector(0, 0, 0)

    @Attribute
    def zRotationCorrection(self):
        dx = (1 - self.flap_hinge_location - self.flapDisplacement[0] / np.mean(self.chords)) * (
                self.chords[1] - self.chords[0]) + self.points[1][0] - self.points[0][1]
        return np.arctan(dx / (self.points[1][1] - self.points[0][1])) - self.flap_sweep

    @Attribute
    def xRotationCorrection(self):
        dz = self.flapDisplacement[2]*(0.5*(self.chords[0]/self.chords[1] - 1) + 1)*(1 - self.chords[1]/self.chords[0])
        return - np.arctan(dz / (self.points[1][1] - self.points[0][1]))

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

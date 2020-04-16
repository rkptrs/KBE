from parapy.geom import *
from parapy.core import *
from functions import p2v, interp_coords, split_coordinates
import numpy as np


class Wing_base(Base):
    chords = Input(settable=False)
    points = Input(settable=False)
    airfoil_coordinates = Input(settable=False)
    flap_hinge_location = Input(0.67, settable=False)
    flap_deflection = Input(0, settable=False)

    @Attribute
    def unit_airfoil(self):
        return FittedCurve(self.airfoil_coordinates)

    @Attribute
    def airfoils(self):
        out = [0, 0]
        for i in range(2):
            scaled_airfoil = ScaledCurve(self.unit_airfoil, factor=self.chords[i], reference_point=Point(0, 0, 0))
            out[i] = TranslatedCurve(scaled_airfoil, p2v(self.points[i]))
        return out

    @Attribute
    def wing_solid(self):
        #return RuledSolid(self.airfoils[0], self.airfoils[1])
        return LoftedSolid([self.airfoils[0], self.airfoils[1]])

    @Attribute
    def hinge_dimension(self):
        xb, zb, xt, zt = split_coordinates(self.airfoil_coordinates)
        z_bottom = interp_coords(xb, zb, self.flap_hinge_location)
        z_top = interp_coords(xt, zt, self.flap_hinge_location)
        return (z_top + z_bottom) / 2, (z_top - z_bottom)*1.01

    @Attribute
    def flap_sweep(self):
        dx = (1-self.flap_hinge_location)*(self.chords[1]-self.chords[0]) + self.points[1][0] - self.points[0][1]
        return np.arctan(dx/(self.points[1][1]-self.points[0][1]))


class Wing_section(Wing_base):
    @Part
    def main_wing(self):
        return Solid(self.wing_solid.solids[0])

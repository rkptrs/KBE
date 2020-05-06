from parapy.geom import *
from parapy.core import *
from functions import p2v, interp_coords, split_coordinates, v
import numpy as np

# this is the base class that defines any section of the wing and is further expanded by the different flap classes
# the attributes common to all these classes are defined here

class WingBase(Base):
    chords = Input(settable=False)
    points = Input(settable=False)
    airfoil_coordinates = Input(settable=False)
    flap_hinge_location = Input(0.67, settable=False)     # these two inputs are never used but defined because the hinge dimension attribute
    flap_deflection = Input(0, settable=False)            # is common to all flap types and is defined here, a section without a flap would therefore give an error

    @Attribute                  # the airfoils are constructed using the fitted curve class from the coordinates, this is an airfoil with a chord of 1
    def unitAirfoil(self):
        return FittedCurve(self.airfoil_coordinates, mesh_deflection=v.md)

    @Attribute                  # the root and tip airfoils of the section are scaled here
    def airfoils(self):
        out = [0, 0]
        for i in range(2):
            scaled_airfoil = ScaledCurve(self.unitAirfoil,
                                         factor=self.chords[i],
                                         reference_point=Point(0, 0, 0),
                                         mesh_deflection=v.md)
            out[i] = TranslatedCurve(scaled_airfoil, p2v(self.points[i]))
        return out

    @Attribute                  # Returns the wing solid constructed from the two airfoils
    def wingSolid(self):
        return LoftedSolid([self.airfoils[0], self.airfoils[1]], mesh_deflection=v.md)

    # The height of the airfoil at hinge location and z coordinate of center of hinge computed by
    # interpolating airfoil coordinates
    @Attribute
    def hingeDimension(self):
        xb, zb, xt, zt = split_coordinates(self.airfoil_coordinates)
        z_bottom = interp_coords(xb, zb, self.flap_hinge_location)
        z_top = interp_coords(xt, zt, self.flap_hinge_location)
        return (z_top + z_bottom) / 2, (z_top - z_bottom)*1.01

    @Attribute                  # Returns the sweep of the hinge line of flaps
    def flapSweep(self):
        dx = (1-self.flap_hinge_location)*(self.chords[1]-self.chords[0]) + self.points[1][0] - self.points[0][1]
        return np.arctan(dx/(self.points[1][1]-self.points[0][1]))


class Wing_section(WingBase):  # This is a wing section without flaps
    @Part
    def mainWing(self):
        return Solid(self.wingSolid.solids[0], mesh_deflection=v.md)

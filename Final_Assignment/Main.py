from parapy.geom import *
from parapy.core import *
from parapy.gui import display
from airfoil import get_airfoil
from wing_section import Wing_section
from plain_flap import Plain_flap_section
from flower_flap import Flower_flap_section
from slotted_flap import Slotted_flap_section
import numpy as np


class Fuselage(Base):
    length = Input(10)
    radius = Input(settable=False)

    @Part(parse=False)
    def cylinder(self):
        surf = CylindricalSurface(radius=self.radius,
                                  height=self.length,
                                  position=rotate(XOY, "y", np.pi/2))
        return TranslatedSurface(surf, Vector(-1, 0, self.radius))


class Wing(Base):
    wing_span = Input(12)
    root_chord = Input(5)
    kink_chord = Input(3.5)
    tip_chord = Input(2)
    kink_position = Input(4)
    sweep_deg = Input(25)
    dihedral_deg = Input(5)
    fuselage_radius = Input(1.5)
    airfoil_name = Input("ex3")
    flap_hinge_location = Input(0.67)
    flap_deflection = Input(30)
    flap_type = Input("Flower")
    outer_flap_lim = Input(0.7)

    @Attribute
    def sweep(self):
        return self.sweep_deg*np.pi/180

    @Attribute
    def dihedral(self):
        return self.dihedral_deg*np.pi/180

    @Attribute
    def airfoil_coordinates(self):
        coords = get_airfoil(self.airfoil_name)
        points = []
        for i in range(len(coords[0])):
            points.append(Point(coords[0][i], 0, coords[1][i]))
        return points

    def le_pos(self, y):
        x = y*np.tan(self.sweep)
        z = y*np.tan(self.dihedral)
        return Point(x, y, z)

    def chord(self, y):
        if y < self.kink_position:
            return (self.root_chord*(self.kink_position - y) + self.kink_chord*y)/self.kink_position
        else:
            y1 = y - self.kink_position
            span = self.wing_span - self.kink_position
            return (self.kink_chord*(span - y1) + self.tip_chord*y1)/span

    @Attribute
    def flap_function(self):
        if self.flap_type == "Plain":
            return Plain_flap_section
        elif self.flap_type == "Flower":
            return Flower_flap_section
        elif self.flap_type == "None":
            return Wing_section
        elif self.flap_type == "Slotted":
            return Slotted_flap_section

    @Part
    def section_0(self):
        return Wing_section(chords=[self.root_chord, self.chord(self.fuselage_radius)],
                            points=[self.le_pos(0), self.le_pos(self.fuselage_radius)],
                            airfoil_coordinates=self.airfoil_coordinates)

    @Part
    def section_1(self):
        return self.flap_function(chords=[self.chord(self.fuselage_radius), self.kink_chord],
                                  points=[self.le_pos(self.fuselage_radius), self.le_pos(self.kink_position)],
                                  airfoil_coordinates=self.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_2(self):
        return self.flap_function(chords=[self.kink_chord, self.chord(self.outer_flap_lim*self.wing_span)],
                                  points=[self.le_pos(self.kink_position), self.le_pos(self.outer_flap_lim*self.wing_span)],
                                  airfoil_coordinates=self.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_3(self):
        return Wing_section(chords=[self.chord(self.outer_flap_lim*self.wing_span), self.tip_chord],
                            points=[self.le_pos(self.outer_flap_lim*self.wing_span), self.le_pos(self.wing_span)],
                            airfoil_coordinates=self.airfoil_coordinates, hidden=True)

    @Part
    def fuselage(self):
        return Fuselage(radius=self.fuselage_radius, hidden=False)


if __name__ == "__main__":
    obj = Wing()
    display(obj)

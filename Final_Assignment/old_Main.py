from parapy.geom import *
from parapy.core import *
from parapy.gui import display
from airfoil import get_airfoil
from wing_section import Wing_section
from plain_flap import Plain_flap_section
from fowler_flap import FowlerFlapSection
from slotted_flap import Slotted_flap_section
from read_input import get_input
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


class Model(Base):
    @Part
    def wing(self):
        return Wing()

    @Attribute
    def wing_parts(self):
        part_list = []
        for section in self.wing.parts:
            for sub_section in section.parts:
                part_list.append(Solid(sub_section))
        return part_list

    @Part
    def mirror(self):
        return MirroredShape(self.wing_parts[child.index], XOY, vector1=Vector(0, 0, 1), vector2=Vector(1, 0, 0),
                             quantify=len(self.wing_parts))


class Wing(Base):
    planform_file_name = Input("test_planform")

    inp = Input(get_input("test_planform"), settable=False)

    wing_span = Input(inp.wing_span)
    root_chord = Input(inp.root_chord)
    taper_inner = Input(inp.taper_inner)
    taper_outer = Input(inp.taper_outer)
    kink_position = Input(inp.kink_position)
    flap_gap = Input(inp.flap_gap)
    sweep_deg = Input(inp.sweep)
    dihedral_deg = Input(inp.dihedral)
    fuselage_radius = Input(inp.fuselage_radius)
    airfoil_name = Input(inp.airfoil_name)
    flap_type = Input(inp.flap_type)

    flap_deflection = Input(30)

    flap_hinge_location = Input(0.67)
    outer_flap_lim = Input(0.7)

    @Attribute
    def sweep(self):
        print(self.sweep_deg)
        return self.sweep_deg*np.pi/180

    @Attribute
    def dihedral(self):
        return self.dihedral_deg*np.pi/180

    @Attribute
    def kink_chord(self):
        return self.root_chord*self.taper_inner

    @Attribute
    def tip_chord(self):
        return self.kink_chord*self.taper_outer

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
            return FowlerFlapSection
        elif self.flap_type == "None":
            return Wing_section
        elif self.flap_type == "Slotted":
            return Slotted_flap_section

    @Part
    def section_mid(self):
        return Wing_section(chords=[self.root_chord, self.chord(self.fuselage_radius)],
                            points=[self.le_pos(0), self.le_pos(self.fuselage_radius)],
                            airfoil_coordinates=self.airfoil_coordinates)

    @Part
    def section_flap1(self):
        return self.flap_function(chords=[self.chord(self.fuselage_radius), self.kink_chord],
                                  points=[self.le_pos(self.fuselage_radius), self.le_pos(self.kink_position)],
                                  airfoil_coordinates=self.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_gap(self):
        return Wing_section(chords=[self.kink_chord, self.chord(self.kink_position+self.flap_gap)],
                            points=[self.le_pos(self.kink_position), self.le_pos(self.kink_position+self.flap_gap)],
                            airfoil_coordinates=self.airfoil_coordinates)

    @Part
    def section_flap2(self):
        return self.flap_function(chords=[self.chord(self.kink_position+self.flap_gap), self.chord(self.outer_flap_lim*self.wing_span)],
                                  points=[self.le_pos(self.kink_position+self.flap_gap), self.le_pos(self.outer_flap_lim*self.wing_span)],
                                  airfoil_coordinates=self.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_outer(self):
        return Wing_section(chords=[self.chord(self.outer_flap_lim*self.wing_span), self.tip_chord],
                            points=[self.le_pos(self.outer_flap_lim*self.wing_span), self.le_pos(self.wing_span)],
                            airfoil_coordinates=self.airfoil_coordinates, hidden=False)

    @Part
    def fuselage(self):
        return Fuselage(radius=self.fuselage_radius, hidden=False)


if __name__ == "__main__":
    obj = Model()
    display(obj)

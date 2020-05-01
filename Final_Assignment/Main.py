from parapy.geom import *
from parapy.core import *
from parapy.gui import display
from wing_section import Wing_section
from plain_flap import Plain_flap_section
from fowler_flap import Fowler_flap_section
from slotted_flap import Slotted_flap_section
from read_input import get_input, check_input
import numpy as np


class Fuselage(Base):
    radius = Input(settable=False)
    root_chord = Input(settable=False)

    @Part(parse=False)
    def cylinder(self):
        surf = CylindricalSurface(radius=self.radius,
                                  height=self.root_chord*3,
                                  position=rotate(XOY, "y", np.pi/2))
        return TranslatedSurface(surf, Vector(-self.root_chord, 0, self.radius))


class Model(Base):

    planform_file_name = Input('test_planform1')

    @Attribute
    def input(self):
        out = get_input("planforms/" + self.planform_file_name + ".txt")
        if out.valid:
            out = check_input(out, self.planform_file_name)
        return out

    flap_deflection = Input(35)
    flap_hinge_location = Input(0.67)
    outer_flap_lim = Input(0.7)

    # This is a good place for your code come and define the three inputs above. All of the inputs you need
    # should be in the input attribute (self.input.wing_span, self.input.root_chord etc.), you can file all the
    # input attributes in read_input.py. The input also contains a list of airfoil coordinates in the from of parapy
    # Points. If you want to make the airfoils the same way as I did, you can copy paste the unit_airfoil and
    # airfoils attribute

    # Also there is no code that checks whether the three inputs are bullshit yet

    @Part
    def wing(self):
        return Wing(input=self.input, flap_hinge_location=self.flap_hinge_location, outer_flap_lim=self.outer_flap_lim,
                    color=self.input.colour, flap_deflection=self.flap_deflection)


    @Attribute
    def wing_parts(self):
        part_list = []
        for section in self.wing.children:
            for sub_section in section.children:
                part_list.append(Solid(sub_section))
        return part_list

    @Part
    def mirror(self):
        return MirroredShape(self.wing_parts[child.index], XOY, vector1=Vector(0, 0, 1), vector2=Vector(1, 0, 0),
                             quantify=len(self.wing_parts)-1, color=self.input.colour)


class Wing(Base):

    flap_deflection = Input(settable=False)
    flap_hinge_location = Input(settable=False)
    outer_flap_lim = Input(settable=False)
    input = Input(settable=False)

    @Attribute
    def sweep(self):
        return self.input.sweep_deg*np.pi/180

    @Attribute
    def dihedral(self):
        return self.input.dihedral_deg*np.pi/180

    @Attribute
    def kink_chord(self):
        return self.input.root_chord*self.input.taper_inner

    @Attribute
    def tip_chord(self):
        return self.kink_chord*self.input.taper_outer

    def le_pos(self, y):
        x = y*np.tan(self.sweep)
        z = y*np.tan(self.dihedral)
        return Point(x, y, z)

    def chord(self, y):
        if y < self.input.kink_position:
            return (self.input.root_chord*(self.input.kink_position - y) + self.kink_chord*y)/self.input.kink_position
        else:
            y1 = y - self.input.kink_position
            span = self.input.wing_span - self.input.kink_position
            return (self.kink_chord*(span - y1) + self.tip_chord*y1)/span

    @Attribute
    def flap_function(self):
        if self.input.flap_type == "Plain":
            return Plain_flap_section
        elif self.input.flap_type == "Fowler":
            return Fowler_flap_section
        elif self.input.flap_type == "None":
            return Wing_section
        elif self.input.flap_type == "Slotted":
            return Slotted_flap_section

    @Part
    def section_mid(self):
        return Wing_section(chords=[self.input.root_chord, self.chord(self.input.fuselage_radius)],
                            points=[self.le_pos(0), self.le_pos(self.input.fuselage_radius)],
                            airfoil_coordinates=self.input.airfoil_coordinates)
    @Part
    def section_flap1(self):
        return self.flap_function(chords=[self.chord(self.input.fuselage_radius), self.kink_chord],
                                  points=[self.le_pos(self.input.fuselage_radius), self.le_pos(self.input.kink_position)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_gap(self):
        return Wing_section(chords=[self.kink_chord, self.chord(self.input.kink_position+self.input.flap_gap)],
                            points=[self.le_pos(self.input.kink_position), self.le_pos(self.input.kink_position+self.input.flap_gap)],
                            airfoil_coordinates=self.input.airfoil_coordinates)

    @Part
    def section_flap2(self):
        return self.flap_function(chords=[self.chord(self.input.kink_position+self.input.flap_gap), self.chord(self.outer_flap_lim*self.input.wing_span)],
                                  points=[self.le_pos(self.input.kink_position+self.input.flap_gap), self.le_pos(self.outer_flap_lim*self.input.wing_span)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_outer(self):
        return Wing_section(chords=[self.chord(self.outer_flap_lim*self.input.wing_span), self.tip_chord],
                            points=[self.le_pos(self.outer_flap_lim*self.input.wing_span), self.le_pos(self.input.wing_span)],
                            airfoil_coordinates=self.input.airfoil_coordinates, hidden=False)

    @Part
    def fuselage(self):
        return Fuselage(radius=self.input.fuselage_radius, root_chord=self.input.root_chord, hidden=False)


if __name__ == "__main__":
    obj = Model()
    display(obj)

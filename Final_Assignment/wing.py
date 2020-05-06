from parapy.core import *
from parapy.geom import *
import numpy as np
from wing_section import Wing_section
from plain_flap import Plain_flap_section
from fowler_flap import FowlerFlapSection
from slotted_flap import Slotted_flap_section


class Wing(Base):
    flap_deflection = Input(settable=False)
    flap_hinge_location = Input(settable=False)
    input = Input(settable=False)
    flap_count = Input(settable=False)

    @Attribute
    def sweep(self):
        return self.input.sweep_deg * np.pi / 180

    @Attribute
    def dihedral(self):
        return self.input.dihedral_deg * np.pi / 180

    @Attribute
    def kinkChord(self):
        return self.input.root_chord * self.input.taper_inner

    @Attribute
    def tipChord(self):
        return self.kinkChord * self.input.taper_outer

    def le_pos(self, y):
        x = y * np.tan(self.sweep)
        z = y * np.tan(self.dihedral)
        return Point(x, y, z)

    def chord(self, y):
        if y < self.input.kink_position:
            return (self.input.root_chord * (
                    self.input.kink_position - y) + self.kinkChord * y) / self.input.kink_position
        else:
            y1 = y - self.input.kink_position
            span = self.input.wing_span - self.input.kink_position
            return (self.kinkChord * (span - y1) + self.tipChord * y1) / span

    @Attribute
    def flapFunction1(self):
        if self.flap_count == 0:
            return Wing_section
        else:
            if self.input.flap_type == "Plain":
                return Plain_flap_section
            elif self.input.flap_type == "Fowler":
                return FowlerFlapSection
            elif self.input.flap_type == "None":
                return Wing_section
            elif self.input.flap_type == "Slotted":
                return Slotted_flap_section

    @Attribute
    def flapFunction2(self):
        if self.flap_count == 2:
            return self.flapFunction1
        else:
            return Wing_section

    @Part
    def sectionMiddle(self):
        return Wing_section(chords=[self.input.root_chord, self.chord(self.input.fuselage_radius)],
                            points=[self.le_pos(0), self.le_pos(self.input.fuselage_radius)],
                            airfoil_coordinates=self.input.airfoil_coordinates)

    @Part
    def sectionFlap1(self):
        return self.flapFunction1(chords=[self.chord(self.input.fuselage_radius), self.kinkChord],
                                  points=[self.le_pos(self.input.fuselage_radius),
                                          self.le_pos(self.input.kink_position)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def sectionGap(self):
        return Wing_section(chords=[self.kinkChord, self.chord(self.input.kink_position + self.input.flap_gap)],
                            points=[self.le_pos(self.input.kink_position),
                                    self.le_pos(self.input.kink_position + self.input.flap_gap)],
                            airfoil_coordinates=self.input.airfoil_coordinates)

    @Part
    def sectionFlap2(self):
        return self.flapFunction2(chords=[self.chord(self.input.kink_position + self.input.flap_gap),
                                          self.chord(self.input.outer_flap_lim * self.input.wing_span)],
                                  points=[self.le_pos(self.input.kink_position + self.input.flap_gap),
                                           self.le_pos(self.input.outer_flap_lim * self.input.wing_span)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def sectionOuter(self):
        return Wing_section(chords=[self.chord(self.input.outer_flap_lim * self.input.wing_span), self.tipChord],
                            points=[self.le_pos(self.input.outer_flap_lim * self.input.wing_span),
                                    self.le_pos(self.input.wing_span)],
                            airfoil_coordinates=self.input.airfoil_coordinates, hidden=False)

    @Part
    def fuselage(self):
        return Fuselage(radius=self.input.fuselage_radius, root_chord=self.input.root_chord, hidden=False)


class Fuselage(Base):
    radius = Input(settable=False)
    root_chord = Input(settable=False)

    @Part(parse=False)
    def cylinder(self):
        surf = CylindricalSurface(radius=self.radius,
                                  height=self.root_chord * 3,
                                  position=rotate(XOY, "y", np.pi / 2))
        return TranslatedSurface(surf, Vector(-self.root_chord, 0, self.radius))

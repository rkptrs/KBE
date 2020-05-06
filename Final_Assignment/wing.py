from parapy.core import *
from parapy.geom import *
import numpy as np
from wing_section import Wing_section
from plain_flap import Plain_flap_section
from fowler_flap import FowlerFlapSection
from slotted_flap import Slotted_flap_section

# This class defines all of the sections o the wing, this consists of:
# - middle section under the fuselage with span = fuselage radius
# - inner flap section that ends at the kink
# - gap section with span equal to flap_gap specified in the inputs
# - outer flap section that ends at the specified flap limit
# - outer wing that goes until the wing span

# this structure is not followed if the flap needs to be very small, in that case the outer flap is replaced by a plain section
# in case there are no flaps, all sections are defined as plain wing

# The fuselage is also defined here because the necessary inputs were available here - makes no difference to anything as it is just a single cylinder

class Wing(Base):
    flap_deflection = Input(settable=False)
    flap_hinge_location = Input(settable=False)
    input = Input(settable=False)
    flap_count = Input(settable=False)

    # Additional parameters are computed here from the inputs
    @Attribute              # wing sweep is converted from deg to radians
    def sweep(self):
        return self.input.sweep_deg * np.pi / 180

    @Attribute              # dihedral is converted from deg to radians
    def dihedral(self):
        return self.input.dihedral_deg * np.pi / 180

    @Attribute              # kink chord is computed from taper ratio and root chord
    def kinkChord(self):
        return self.input.root_chord * self.input.taper_inner

    @Attribute              # tip chord computed from kink chord and taper
    def tipChord(self):
        return self.kinkChord * self.input.taper_outer

    def le_pos(self, y):    # function for computing leading edge position at any y coordinate
        x = y * np.tan(self.sweep)
        z = y * np.tan(self.dihedral)
        return Point(x, y, z)

    def chord(self, y):     # function for computing wing chord at any y location
        if y < self.input.kink_position:        # if before kink
            return (self.input.root_chord * (
                    self.input.kink_position - y) + self.kinkChord * y) / self.input.kink_position
        else:
            y1 = y - self.input.kink_position   # if after kink
            span = self.input.wing_span - self.input.kink_position
            return (self.kinkChord * (span - y1) + self.tipChord * y1) / span

    # based on flap type assign the correct function for constructing the inner flap section
    @Attribute
    def flapFunction1(self):                        # use plain for no flaps
        if self.flap_count == 0:
            return Wing_section
        else:                                       # convert the text input into function name
            if self.input.flap_type == "Plain":
                return Plain_flap_section
            elif self.input.flap_type == "Fowler":
                return FowlerFlapSection
            elif self.input.flap_type == "None":
                return Wing_section
            elif self.input.flap_type == "Slotted":
                return Slotted_flap_section

    # assign function for constructing outer flap section
    @Attribute
    def flapFunction2(self):
        if self.flap_count == 2:        # use same as inner flap if there are both flaps required
            return self.flapFunction1
        else:
            return Wing_section         # use a plain wing section of only inner flap required

    @Part                               # plain section under fuselage
    def sectionMiddle(self):
        return Wing_section(chords=[self.input.root_chord, self.chord(self.input.fuselage_radius)],
                            points=[self.le_pos(0), self.le_pos(self.input.fuselage_radius)],
                            airfoil_coordinates=self.input.airfoil_coordinates)

    @Part                               # inner flap section
    def sectionFlap1(self):
        return self.flapFunction1(chords=[self.chord(self.input.fuselage_radius), self.kinkChord],
                                  points=[self.le_pos(self.input.fuselage_radius),
                                          self.le_pos(self.input.kink_position)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part                               # gap between inner and outer flaps
    def sectionGap(self):
        return Wing_section(chords=[self.kinkChord, self.chord(self.input.kink_position + self.input.flap_gap)],
                            points=[self.le_pos(self.input.kink_position),
                                    self.le_pos(self.input.kink_position + self.input.flap_gap)],
                            airfoil_coordinates=self.input.airfoil_coordinates)

    @Part                               # outer flap section
    def sectionFlap2(self):
        return self.flapFunction2(chords=[self.chord(self.input.kink_position + self.input.flap_gap),
                                          self.chord(self.input.outer_flap_lim * self.input.wing_span)],
                                  points=[self.le_pos(self.input.kink_position + self.input.flap_gap),
                                           self.le_pos(self.input.outer_flap_lim * self.input.wing_span)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part                               # wing after the outer flap
    def sectionOuter(self):
        return Wing_section(chords=[self.chord(self.input.outer_flap_lim * self.input.wing_span), self.tipChord],
                            points=[self.le_pos(self.input.outer_flap_lim * self.input.wing_span),
                                    self.le_pos(self.input.wing_span)],
                            airfoil_coordinates=self.input.airfoil_coordinates, hidden=False)

    @Part                               # fuselage is defined here because the fuselage radius is passed to this class
    def fuselage(self):
        return Fuselage(radius=self.input.fuselage_radius, root_chord=self.input.root_chord, hidden=False)

# the only purpose of the fuselage is to visualize what the wing with it will look like, as the inner flap limit is set to be the fuselage radius
class Fuselage(Base):
    radius = Input(settable=False)
    root_chord = Input(settable=False)

    @Part(parse=False)
    def cylinder(self):
        surf = CylindricalSurface(radius=self.radius,
                                  height=self.root_chord * 3,
                                  position=rotate(XOY, "y", np.pi / 2))
        return TranslatedSurface(surf, Vector(-self.root_chord, 0, self.radius))


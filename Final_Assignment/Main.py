from parapy.geom import *
from parapy.core import *
from parapy.gui import display
from wing_section import Wing_section
from plain_flap import Plain_flap_section
from fowler_flap import Fowler_flap_section
from slotted_flap import Slotted_flap_section
from read_input import get_input, check_input
from hld_size import HLDsize
from avl_wing import Avl_Wing
from avl_wing import Avl_analysis
from xfoil_analysis import XfoilAnalysis
from bar import bar
from write_pdf import write_pdf
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

    @Attribute
    def flap_hinge_location(self):
        return self.newspar

    @Attribute
    def flap_deflection(self):
        return self.hld_size.angle_max

    # This is a good place for your code come and define the three inputs above. All of the inputs you need
    # should be in the input attribute (self.input.wing_span, self.input.root_chord etc.), you can file all the
    # input attributes in read_input.py. The input also contains a list of airfoil coordinates in the from of parapy
    # Points. If you want to make the airfoils the same way as I did, you can copy paste the unit_airfoil and
    # airfoils attribute

    # Also there is no code that checks whether the three inputs are bullshit yet
    #

    def reynolds(self, chord):
        return self.input.speed*chord/1.5111E-5

    @Attribute
    def mach(self):
        return self.input.speed/343

    @Attribute
    def xfoil(self):
        clmaxfoil = np.zeros(20)
        p_bar = bar()
        p_bar.update(0)
        for j in range(20):
            y = j/20 * self.input.wing_span
            if y < self.input.kink_position:
                chord = self.input.root_chord - (self.hld_size.chordroot-self.hld_size.chordkink)*(y/self.input.kink_position)
            else:
                y1 = y - self.input.kink_position
                span = self.input.wing_span - self.input.kink_position
                chord = self.hld_size.chordkink - (self.hld_size.chordkink-self.hld_size.chordtip)*(y1/span)
            xfoil_analysis = XfoilAnalysis(lifting_surface=self.avl_wing.surface1,
                                           cutting_plane_span_fraction=j/20,
                                           flydir=True,
                                           reynolds_number=self.reynolds(chord),
                                           root_section=self.avl_wing.root_section,
                                           tip_section=self.avl_wing.kink_section,
                                           mach=self.mach)

            clmaxfoil[j] = xfoil_analysis.clmax
            p_bar.update(j*5)
        p_bar.update(100)
        p_bar.kill()
        return clmaxfoil

    @Attribute
    def clmax(self):
        Avl_aircraft = Avl_Wing(span=self.input.wing_span,
                            taper_outer=self.input.taper_outer,
                            le_sweep=self.input.sweep_deg,
                            twist=self.input.twist,
                            airfoil=self.input.airfoil_name,
                            chord_root=self.input.root_chord,
                            chord_kink=self.hld_size.chordkink,
                            kink_positionm=self.input.kink_position,
                            dihedral_deg=self.input.dihedral_deg,
                            mach=self.mach)

        aoa = 0
        cltotlist = []
        stall = 0

        while stall < 1:
            cases = [('fixed_aoa', {'alpha': aoa})]
            analysis = Avl_analysis(aircraft=Avl_aircraft,
                                    case_settings=cases)
            cltot = list(analysis.cltot)[0]
            cltotlist.append(cltot)
            aoa = aoa + 0.5
            for k in range(20):
                clnorm = list(analysis.strip(k))[0]
                if clnorm > self.xfoil[k]:
                    stall = stall + 1

        return cltotlist[-1], cltotlist

    @Part
    def avl_wing(self):
        return Avl_Wing(span=self.input.wing_span,
                        taper_outer=self.input.taper_outer,
                        le_sweep=self.input.sweep_deg,
                        twist=self.input.twist,
                        airfoil=self.input.airfoil_name,
                        chord_root=self.input.root_chord,
                        chord_kink=self.hld_size.chordkink,
                        kink_positionm=self.input.kink_position,
                        dihedral_deg=self.input.dihedral_deg,
                        mach=self.mach)

    @Part
    def hld_size(self):
        return HLDsize(root_chord=self.input.root_chord,
                       kink_position=self.input.kink_position,
                       sweep=self.input.sweep_deg,
                       dihedral=self.input.dihedral_deg,
                       taper_inner=self.input.taper_inner,
                       taper_outer=self.input.taper_outer,
                       wing_span=self.input.wing_span,
                       frontpar=self.input.front_spar,
                       rearspar=self.input.rear_spar,
                       aileronloc=self.input.outer_flap_lim,
                       fuselage_radius=self.input.fuselage_radius,
                       flap_gap=self.input.flap_gap,
                       naca=self.input.airfoil_name,
                       clmaxclean=self.clmax[0],
                       clmaxflapped=self.input.clmax,
                       flaptype=self.input.flap_type)

    @Attribute
    def newspar(self):
        if self.hld_size.can_attain:
            dcl45 = self.hld_size.dcl_flap[0]
            dcl_target = self.hld_size.dcl_flap[1]
            newspar = self.input.rear_spar
            while dcl45 > dcl_target and newspar < 1.0:
                newspar = newspar + 0.01
                hldsize = HLDsize(root_chord=self.input.root_chord,
                        kink_position=self.input.kink_position,
                        sweep=self.input.sweep_deg,
                        dihedral=self.input.dihedral_deg,
                        taper_inner=self.input.taper_inner,
                        taper_outer=self.input.taper_outer,
                        wing_span=self.input.wing_span,
                        frontpar=self.input.front_spar,
                        rearspar=newspar,
                        aileronloc=self.input.outer_flap_lim,
                        fuselage_radius=self.input.fuselage_radius,
                        flap_gap=self.input.flap_gap,
                        naca=self.input.airfoil_name,
                        clmaxclean=self.clmax[0],
                        clmaxflapped=self.input.clmax,
                        flaptype=self.input.flap_type)
                dcl45 = hldsize.dcl_flap[0]
                dcl_target = hldsize.dcl_flap[1]
        else:
            newspar = self.input.rear_spar


        return newspar - 0.01

    @Part
    def wing(self):
        return Wing(input=self.input, flap_hinge_location=self.flap_hinge_location,
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

    @Attribute
    def export_pdf(self):
        write_pdf(self.input, self.clmax[0], self.input.clmax - self.clmax[0], self.flap_hinge_location,
                  self.planform_file_name)
        return "Done"



class Wing(Base):

    flap_deflection = Input(settable=False)
    flap_hinge_location = Input(settable=False)
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
        return self.flap_function(chords=[self.chord(self.input.kink_position+self.input.flap_gap), self.chord(self.input.outer_flap_lim*self.input.wing_span)],
                                  points=[self.le_pos(self.input.kink_position+self.input.flap_gap), self.le_pos(self.input.outer_flap_lim*self.input.wing_span)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_outer(self):
        return Wing_section(chords=[self.chord(self.input.outer_flap_lim*self.input.wing_span), self.tip_chord],
                            points=[self.le_pos(self.input.outer_flap_lim*self.input.wing_span), self.le_pos(self.input.wing_span)],
                            airfoil_coordinates=self.input.airfoil_coordinates, hidden=False)

    @Part
    def fuselage(self):
        return Fuselage(radius=self.input.fuselage_radius, root_chord=self.input.root_chord, hidden=False)


if __name__ == "__main__":
    obj = Model()
    display(obj)

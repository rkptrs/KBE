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
from functions import v
import numpy as np


class Fuselage(Base):
    radius = Input(settable=False)
    root_chord = Input(settable=False)

    @Part(parse=False)
    def cylinder(self):
        surf = CylindricalSurface(radius=self.radius,
                                  height=self.root_chord * 3,
                                  position=rotate(XOY, "y", np.pi / 2))
        return TranslatedSurface(surf, Vector(-self.root_chord, 0, self.radius))


class Model(Base):
    planform_file_name = Input('test_planform2')
    cl_max_wing = Input(1.9)  # Set this to None to compute using internal analysis

    @Attribute
    def input(self):
        out = get_input("planforms/" + self.planform_file_name + ".txt")
        if out.valid:
            out = check_input(out, self.planform_file_name)
        return out

    @Attribute
    def flap_hinge_location(self):
        return self.newspar[0]

    @Attribute
    def flap_count(self):
        return self.newspar[1]

    @Attribute
    def flap_deflection(self):
        return self.hld_size.angle_max

    def reynolds(self, chord):
        return self.input.speed * chord / 1.5111E-5

    @Attribute
    def mach(self):
        return self.input.speed / 343

    @Attribute
    def xfoil(self):
        clmaxfoil = np.zeros(20)
        p_bar = bar()
        p_bar.update(0)
        for j in range(20):
            y = j / 20 * self.input.wing_span
            if y < self.input.kink_position:
                chord = self.input.root_chord - (self.hld_size.chordroot - self.hld_size.chordkink) * (
                        y / self.input.kink_position)
            else:
                y1 = y - self.input.kink_position
                span = self.input.wing_span - self.input.kink_position
                chord = self.hld_size.chordkink - (self.hld_size.chordkink - self.hld_size.chordtip) * (y1 / span)
            xfoil_analysis = XfoilAnalysis(lifting_surface=self.avl_wing.surface1,
                                           cutting_plane_span_fraction=j / 20,
                                           flydir=True,
                                           reynolds_number=self.reynolds(chord),
                                           root_section=self.avl_wing.root_section,
                                           tip_section=self.avl_wing.kink_section,
                                           mach=self.mach)

            clmaxfoil[j] = xfoil_analysis.clmax

            p_bar.update(j * 5)
        for k in range(20):
            if k > 0:
                if clmaxfoil[k] > 1.2 * clmaxfoil[k - 1] or clmaxfoil[k] < 0.85 * clmaxfoil[k - 1]:
                    if clmaxfoil[k] > 1.2 * np.average(clmaxfoil) or clmaxfoil[k] < 0.85 * np.average(clmaxfoil):
                        clmaxfoil[k] = clmaxfoil[k - 1]
        p_bar.update(100)
        p_bar.kill()
        return clmaxfoil

    @Attribute
    def clmax(self):
        if self.cl_max_wing is None:
            Avl_aircraft = Avl_Wing(span=self.input.wing_span,
                                    taper_outer=self.input.taper_outer,
                                    le_sweep=self.input.sweep_deg,
                                    twist=self.input.twist,
                                    airfoil=self.input.airfoil_name,
                                    chord_root=self.input.root_chord,
                                    chord_kink=self.hld_size.chordkink,
                                    kink_positionm=self.input.kink_position,
                                    dihedral_deg=self.input.dihedral_deg,
                                    mach=self.mach,
                                    airfoil_coordinates=self.input.airfoil_coordinates)

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

            return cltotlist[-1]
        else:
            return self.cl_max_wing

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
                        mach=self.mach,
                        airfoil_coordinates=self.input.airfoil_coordinates, hidden=True)

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
                       clmaxclean=self.clmax,
                       clmaxflapped=self.input.clmax,
                       flaptype=self.input.flap_type,
                       singleflap=False, hidden=True)

    @Attribute
    def newspar(self):
        flap_count = 2
        if self.hld_size.can_attain:
            dcl45 = self.hld_size.dcl_flap[0]
            dcl_target = self.hld_size.dcl_flap[1]
            newspar = self.input.rear_spar

            sf1 = self.hld_size.sf1
            sf2 = self.hld_size.sf2

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
                                  clmaxclean=self.clmax,
                                  clmaxflapped=self.input.clmax,
                                  flaptype=self.input.flap_type,
                                  singleflap=False)
                dcl45 = hldsize.dcl_flap[0]
                dcl_target = hldsize.dcl_flap[1]
        else:
            newspar = self.input.rear_spar + 0.01
        newspar2 = newspar
        # If the spar location is more than 0.95, the following code calculates if the inner flap is enough to attain
        # the desired CLmax

        if newspar2 > 0.95:
            newspar = self.input.rear_spar
            hldsize1 = HLDsize(root_chord=self.input.root_chord,
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
                               clmaxclean=self.clmax,
                               clmaxflapped=self.input.clmax,
                               flaptype=self.input.flap_type,
                               singleflap=True)
            dcl45_1 = hldsize1.dcl_flap[0]
            dcl_target_1 = hldsize1.dcl_flap[1]
            if dcl45_1 >= dcl_target_1:  # Checking if the inner flap with the maximum possible chord is enough to reach the required CLmax

                dcl45 = self.hld_size.dcl_flap[0]
                dcl_target = self.hld_size.dcl_flap[1]
                while dcl45 > dcl_target and newspar < 1.0:  # Calculating the hinge location of the flap if only the inner flap is used.
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
                                      clmaxclean=self.clmax,
                                      clmaxflapped=self.input.clmax,
                                      flaptype=self.input.flap_type,
                                      singleflap=True)
                    dcl45 = hldsize.dcl_flap[0]
                    dcl_target = hldsize.dcl_flap[1]
                flap_count = 1
            else:
                newspar = newspar2
        return newspar - 0.01, flap_count

    @Part
    def wing(self):
        return Wing(input=self.input, flap_hinge_location=self.flap_hinge_location,
                    color=self.input.colour, flap_deflection=self.flap_deflection, flap_count=self.flap_count)

    @Attribute
    def wing_parts(self):
        part_list = []
        for section in self.wing.children:
            for sub_section in section.children:
                part_list.append(Solid(sub_section))
        return part_list
    """
    @Part
    def mirror(self):
        return MirroredShape(self.wing_parts[child.index], XOY, vector1=Vector(0, 0, 1), vector2=Vector(1, 0, 0),
                             quantify=len(self.wing_parts) - 1, color=self.input.colour, mesh_deflection=v.md)
    """
    @Attribute
    def export_pdf(self):
        write_pdf(self.input, self.clmax, self.input.clmax - self.clmax, self.flap_hinge_location,
                  self.planform_file_name, self.flap_deflection)
        return "Done"


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
    def kink_chord(self):
        return self.input.root_chord * self.input.taper_inner

    @Attribute
    def tip_chord(self):
        return self.kink_chord * self.input.taper_outer

    def le_pos(self, y):
        x = y * np.tan(self.sweep)
        z = y * np.tan(self.dihedral)
        return Point(x, y, z)

    def chord(self, y):
        if y < self.input.kink_position:
            return (self.input.root_chord * (
                    self.input.kink_position - y) + self.kink_chord * y) / self.input.kink_position
        else:
            y1 = y - self.input.kink_position
            span = self.input.wing_span - self.input.kink_position
            return (self.kink_chord * (span - y1) + self.tip_chord * y1) / span

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

    @Attribute
    def flap_function2(self):
        if self.flap_count == 2:
            return self.flap_function
        else:
            return Wing_section

    @Part
    def section_mid(self):
        return Wing_section(chords=[self.input.root_chord, self.chord(self.input.fuselage_radius)],
                            points=[self.le_pos(0), self.le_pos(self.input.fuselage_radius)],
                            airfoil_coordinates=self.input.airfoil_coordinates)

    @Part
    def section_flap1(self):
        return self.flap_function(chords=[self.chord(self.input.fuselage_radius), self.kink_chord],
                                  points=[self.le_pos(self.input.fuselage_radius),
                                          self.le_pos(self.input.kink_position)],
                                  airfoil_coordinates=self.input.airfoil_coordinates,
                                  flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_gap(self):
        return Wing_section(chords=[self.kink_chord, self.chord(self.input.kink_position + self.input.flap_gap)],
                            points=[self.le_pos(self.input.kink_position),
                                    self.le_pos(self.input.kink_position + self.input.flap_gap)],
                            airfoil_coordinates=self.input.airfoil_coordinates)

    @Part
    def section_flap2(self):
        return self.flap_function2(chords=[self.chord(self.input.kink_position + self.input.flap_gap),
                                           self.chord(self.input.outer_flap_lim * self.input.wing_span)],
                                   points=[self.le_pos(self.input.kink_position + self.input.flap_gap),
                                           self.le_pos(self.input.outer_flap_lim * self.input.wing_span)],
                                   airfoil_coordinates=self.input.airfoil_coordinates,
                                   flap_deflection=self.flap_deflection, flap_hinge_location=self.flap_hinge_location)

    @Part
    def section_outer(self):
        return Wing_section(chords=[self.chord(self.input.outer_flap_lim * self.input.wing_span), self.tip_chord],
                            points=[self.le_pos(self.input.outer_flap_lim * self.input.wing_span),
                                    self.le_pos(self.input.wing_span)],
                            airfoil_coordinates=self.input.airfoil_coordinates, hidden=False)

    @Part
    def fuselage(self):
        return Fuselage(radius=self.input.fuselage_radius, root_chord=self.input.root_chord, hidden=False)


if __name__ == "__main__":
    obj = Model()
    display(obj)

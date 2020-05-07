from parapy.exchange import STEPWriter
from parapy.geom import *
from parapy.core import *
from parapy.gui import display
from wing import Wing
from read_input import get_input, check_input, error
from hld_size import HLDsize
from avl_wing import Avl_Wing
from avl_wing import Avl_analysis
from xfoil_analysis import XfoilAnalysis
from bar import bar
from write_pdf import write_pdf
from functions import v
import numpy as np

# This is the base class of the entire model and uses the following structure:
# - Input is read from text file and stored in an instance of the get_input class
# - Sizing of the HLD, this includes
#   - defining a few extra parameters using the inputs
#   - creating a model of the wing without any flaps
#   - using xfoil to get a cl vs alpha curve for each section of the wing
#   - using AVL to get a cl distribution over the wing
#   - combining this information to get a CL_max for the wing without flaps
#   - sizing the HLD using design process proposed by Roskam
# - Constructing the model with the flaps using the Wing class


class Model(Base):
    planform_file_name = Input('test_planform1')        # name of input file located in planforms folder, without ".txt"
    cl_max_wing = Input(1.1)                            # Set this to None to compute using internal analysis or specify a maximum lift coefficient of the wing if known
    hideLeftWing = Input(False)                          # Set to true to only display the right wing

    @Attribute                                          # this attribute is an instance of the get_input class and contains all inputs read from file
    def input(self):
        out = get_input("planforms/" + self.planform_file_name + ".txt")
        if out.valid:                                   # if the input was successfully read, it will be checked using this function to make sure it is within limits
            out = check_input(out, self.planform_file_name)
        return out

    def reynoldsNumber(self, chord):
        return self.input.speed * chord / 1.5111E-5

    @Attribute
    def mach(self):
        return self.input.speed / 343

    # Sizing of HLD starts here
    # this attribute computes the cl alpha curves of 20 wing sections and returns the CL_max of each
    @Attribute
    def xfoil(self):
        clmaxfoil = np.zeros(20)
        p_bar = bar()
        p_bar.update(0)
        for j in range(20):
            y = j / 20 * self.input.wing_span
            if y < self.input.kink_position:
                chord = self.input.root_chord - (self.hldSize.chordroot - self.hldSize.chordkink) * (
                        y / self.input.kink_position)
            else:
                y1 = y - self.input.kink_position
                span = self.input.wing_span - self.input.kink_position
                chord = self.hldSize.chordkink - (self.hldSize.chordkink - self.hldSize.chordtip) * (y1 / span)
            xfoil_analysis = XfoilAnalysis(lifting_surface=self.avlWing.surface1,
                                           cutting_plane_span_fraction=j / 20,
                                           flydir=True,
                                           reynolds_number=self.reynoldsNumber(chord),
                                           root_section=self.avlWing.root_section,
                                           tip_section=self.avlWing.kink_section,
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

    # The cl distribution along the wing is compared to the CL_max of each airfoil a CL_max of the whole wing is determined.
    @Attribute
    def clMax(self):
        if self.cl_max_wing is None:
            Avl_aircraft = Avl_Wing(span=self.input.wing_span,
                                    taper_outer=self.input.taper_outer,
                                    le_sweep=self.input.sweep_deg,
                                    twist=self.input.twist,
                                    airfoil=self.input.airfoil_name,
                                    chord_root=self.input.root_chord,
                                    chord_kink=self.hldSize.chordkink,
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

    # cl distribution over the whole wing is computed here
    @Part
    def avlWing(self):
        return Avl_Wing(span=self.input.wing_span,
                        taper_outer=self.input.taper_outer,
                        le_sweep=self.input.sweep_deg,
                        twist=self.input.twist,
                        airfoil=self.input.airfoil_name,
                        chord_root=self.input.root_chord,
                        chord_kink=self.hldSize.chordkink,
                        kink_positionm=self.input.kink_position,
                        dihedral_deg=self.input.dihedral_deg,
                        mach=self.mach,
                        airfoil_coordinates=self.input.airfoil_coordinates, hidden=True)

    # here the dimension of the HLD is determined as proposed by Roskam
    @Part
    def hldSize(self):
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
                       airfoilCoordinates=self.input.airfoil_coordinates,
                       clmaxclean=self.clMax,
                       clmaxflapped=self.input.clmax,
                       flaptype=self.input.flap_type,
                       singleflap=False, hidden=True)

    @Attribute
    def newSpar(self):
        flap_count = 2
        if self.hldSize.can_attain:
            dcl45 = self.hldSize.dcl_flap[0]
            dcl_target = self.hldSize.dcl_flap[1]
            newspar = self.input.rear_spar

            sf1 = self.hldSize.sf1
            sf2 = self.hldSize.sf2

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
                                  airfoilCoordinates=self.input.airfoil_coordinates,
                                  clmaxclean=self.clMax,
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
                               airfoilCoordinates=self.input.airfoil_coordinates,
                               clmaxclean=self.clMax,
                               clmaxflapped=self.input.clmax,
                               flaptype=self.input.flap_type,
                               singleflap=True)
            dcl45_1 = hldsize1.dcl_flap[0]
            dcl_target_1 = hldsize1.dcl_flap[1]
            if dcl45_1 >= dcl_target_1:  # Checking if the inner flap with the maximum possible chord is enough to reach the required CLmax

                dcl45 = self.hldSize.dcl_flap[0]
                dcl_target = self.hldSize.dcl_flap[1]
                while dcl45 > dcl_target and newspar < 1.0:  # Calculating the hinge location of the flap if only the inner flap is used.
                    newspar = newspar + 0.01
                    hldsize2 = HLDsize(root_chord=self.input.root_chord,
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
                                      airfoilCoordinates=self.input.airfoil_coordinates,
                                      clmaxclean=self.clMax,
                                      clmaxflapped=self.input.clmax,
                                      flaptype=self.input.flap_type,
                                      singleflap=True)
                    dcl45 = hldsize2.dcl_flap[0]
                    dcl_target = hldsize2.dcl_flap[1]
                flap_count = 1
            else:
                newspar = newspar2

            if newspar > 0.99:
                #flap_count = 0
                error("The size of the flap might be too small to justify its use. "
                      "Consider a small increase in wing area instead.")

        return newspar - 0.01, flap_count

    # Results of the HLD sizing are given by the three attributes bellow:
    @Attribute
    def flapHingeLocation(self):
        return self.newSpar[0]

    @Attribute
    def flapCount(self):
        return self.newSpar[1]

    @Attribute
    def flapDeflection(self):
        return self.hldSize.angle_max

    # The model of the wing with flaps is constructed here
    @Part
    def wing(self):
        return Wing(input=self.input, flap_hinge_location=self.flapHingeLocation,
                    color=self.input.colour, flap_deflection=self.flapDeflection, flap_count=self.flapCount)

    # all the parts of the wing are gathered in a list so that they can be mirrored one by one
    @Attribute
    def wingParts(self):
        part_list = []
        for section in self.wing.children:
            for sub_section in section.children:
                part_list.append(Solid(sub_section))
        return part_list

    # left wing constructed by mirroring all parts
    @Part
    def mirror(self):
        return MirroredShape(self.wingParts[child.index], XOY, vector1=Vector(0, 0, 1), vector2=Vector(1, 0, 0),
                             quantify=len(self.wingParts) - 1, color=self.input.colour, mesh_deflection=v.md,           # -1 is to not include the fuselage
                             hidden=self.hideLeftWing)

    # This is an attibute that when evaluated exports a pdf. this means that the user can export pdf when desired and
    # not after each time something is changed. sort of a "save" function
    @Attribute
    def exportPdf(self):
        write_pdf(self.input, self.clMax, self.input.clmax - self.clMax, self.flapHingeLocation,
                  self.planform_file_name, self.flapDeflection, 10, self.flapCount)
        return "Done"

    @Part
    def exportSTEP(self):
        return STEPWriter(trees=[self.wing, self.mirror])
    STEPWriter()

if __name__ == "__main__":
    obj = Model()
    display(obj)

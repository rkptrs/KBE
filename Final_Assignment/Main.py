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

    def reynoldsNumber(self, chord):                    #Calculation of the Reynolds number, is used for Xfoil
        return self.input.speed * chord / 1.5111E-5

    @Attribute
    def mach(self):                                     #Calculation of the Mach number, used for both the AVL and Xfoil analyses
        return self.input.speed / 343

    # Sizing of HLD starts here
    # this attribute computes the cl alpha curves of 20 wing sections and returns the CL_max of each
    @Attribute
    def xfoil(self):
        clmaxfoil = np.zeros(20)
        p_bar = bar() #used for the progress bar
        p_bar.update(0) #used for the progress bar
        for j in range(20): # 20 cross sections are taken along the span
            y = j / 20 * self.input.wing_span
            if y < self.input.kink_position: #calculation of the chords inboard of the kink
                chord = self.input.root_chord - (self.hldSize.chordroot - self.hldSize.chordkink) * (
                        y / self.input.kink_position)
            else:       #calculation of the chords outboard of the kink
                y1 = y - self.input.kink_position
                span = self.input.wing_span - self.input.kink_position
                chord = self.hldSize.chordkink - (self.hldSize.chordkink - self.hldSize.chordtip) * (y1 / span)
            xfoil_analysis = XfoilAnalysis(lifting_surface=self.avlWing.surface1, #Surface of which xfoil takes its sections
                                           cutting_plane_span_fraction=j / 20, #fraction along the span at which the section is taken
                                           flydir=True, #if true, the section is taken parallel to the flight direction
                                           reynolds_number=self.reynoldsNumber(chord), #Reynolds number at the specific chord
                                           root_section=self.avlWing.root_section,  #root section
                                           tip_section=self.avlWing.kink_section, # tip section
                                           mach=self.mach) # mach number

            clmaxfoil[j] = xfoil_analysis.clmax

            p_bar.update(j * 5)
        for k in range(20):         # Sometimes one section has a significantly lower clmax than the rest of the wing.
                                    # This is because of how the section is taken by xfoil and not because the clmax is actually lower there.
            if k > 0:   #This function makes sure that these outliers are corrected
                if clmaxfoil[k] > 1.2 * clmaxfoil[k - 1] or clmaxfoil[k] < 0.85 * clmaxfoil[k - 1]:
                    if clmaxfoil[k] > 1.2 * np.average(clmaxfoil) or clmaxfoil[k] < 0.85 * np.average(clmaxfoil):
                        clmaxfoil[k] = clmaxfoil[k - 1]
            if k == 0:
                if clmaxfoil[k] > 1.2 * clmaxfoil[k + 1] or clmaxfoil[k] < 0.85 * clmaxfoil[k + 1]:
                    if clmaxfoil[k] > 1.2 * np.average(clmaxfoil) or clmaxfoil[k] < 0.85 * np.average(clmaxfoil):
                        clmaxfoil[k] = clmaxfoil[k + 1]
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
            #The angle of attack is increased until any part of the wing has a higher CL than the CLmax of that section in Xfoil
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

            return cltotlist[-1], aoa
        else:
            return self.cl_max_wing, "Unknown"

    # The avl surfaces and avl configuration are determined here
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
                       clmaxclean=self.clMax[0],
                       clmaxflapped=self.input.clmax,
                       flaptype=self.input.flap_type,
                       singleflap=False, hidden=True)


    #If the flap can attain the desired CLmax with the hinge located at the rear spar location, this attribute will
    #move the hinge line aft until the design can just attain the required CLmax
    @Attribute
    def newSpar(self):
        if self.hldSize.noflap:
            error('The wing can already attain the required CLmax by itself, no flaps are required')
            return self.input.rear_spar, 0, 0
        flap_count = 2
        if self.hldSize.can_attain:
            dcl45 = self.hldSize.dcl_flap[0]
            dcl_target = self.hldSize.dcl_flap[1]
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
                                  airfoilCoordinates=self.input.airfoil_coordinates,
                                  clmaxclean=self.clMax[0],
                                  clmaxflapped=self.input.clmax,
                                  flaptype=self.input.flap_type,
                                  singleflap=False)
                dcl45 = hldsize.dcl_flap[0]
                dcl_target = hldsize.dcl_flap[1]
            flaparea = hldsize.sf*(1-newspar+0.01)
        else:
            newspar = self.input.rear_spar + 0.01
            flaparea = self.hldSize.sf*(1-self.input.rear_spar)
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
                               clmaxclean=self.clMax[0],
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
                                      clmaxclean=self.clMax[0],
                                      clmaxflapped=self.input.clmax,
                                      flaptype=self.input.flap_type,
                                      singleflap=True)
                    dcl45 = hldsize2.dcl_flap[0]
                    dcl_target = hldsize2.dcl_flap[1]
                flap_count = 1
                flaparea = hldsize2.sf * (1 - newspar + 0.01)
            else:
                newspar = newspar2
                flaparea = hldsize.sf*(1-newspar2+0.01)

            if newspar > 0.99:
                #flap_count = 0
                error("The size of the flap might be too small to justify its use. "
                      "Consider a small increase in wing area instead.")

        return newspar - 0.01, flap_count, flaparea

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

    # This function intersects the wing and the flap solids of the inner flap section with a plane in order to get an
    # airfoil of both the wing and the flap. This is used for to draw the airfoil in the output PDF
    @Attribute
    def pdfWingSection(self):
        plane = Plane(reference=Point(0, self.input.fuselage_radius/2+self.input.kink_position/2, 0),
                      normal=Vector(0, 1, 0))
        airfoil = IntersectedShapes(self.wing.sectionFlap1.mainWing, plane, color="red")
        if self.flapCount > 0:
            flap = IntersectedShapes(self.wing.sectionFlap1.flap, plane, color="red")
            return airfoil, flap
        else:
            return airfoil

    # The curves obtained with the pdfWingSection are converted into lists of coordinates that can be used for the drawing
    @Attribute
    def pdfCoordinates(self):
        coordinates = []
        if self.flapCount >0:
            sections = self.pdfWingSection[0].edges + self.pdfWingSection[1].edges
        else:
            sections = self.pdfWingSection.edges
        for ed in sections:
            points = ed.equispaced_points(500)
            coords = []
            for p in points:
                coords.append((p[0], p[2]))
            coordinates.append(coords)
        return coordinates

    # This is an attibute that when evaluated exports a pdf. this means that the user can export pdf when desired and
    # not after each time something is changed. sort of a "save" function
    @Attribute
    def exportPdf(self):
        write_pdf(self.input, self.clMax[0], self.input.clmax - self.clMax[0], self.flapHingeLocation,
                  self.planform_file_name, self.flapDeflection, self.clMax[1], self.flapCount, self.cl_max_wing,
                  self.mach, self.wing.kinkChord, self.wing.tipChord, self.newSpar[2], self.pdfCoordinates)
        return "Done"

    @Part
    def exportSTEP(self):
        return STEPWriter(trees=[self.wing, self.mirror])
    STEPWriter()

if __name__ == "__main__":
    obj = Model(label='HLD sizing application')
    display(obj)

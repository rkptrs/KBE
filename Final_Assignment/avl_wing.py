from math import radians, tan

from parapy.core import *
from parapy.geom import *
from parapy.gui import display
from avl_section import Section
import kbeutils.avl as avl


class Avl_Wing(GeomBase):
    name = Input("wing")
    span = Input()
    taper_outer = Input()
    le_sweep = Input()
    twist = Input()
    airfoil = Input()
    chord_root = Input()
    chord_kink = Input()
    kink_positionm = Input()
    dihedral_deg = Input()
    mach = Input()
    airfoil_coordinates = Input()

    @Attribute
    def kink_position(self):
        return self.kink_positionm/self.span

    @Attribute
    def chord_tip(self):
        return self.chord_kink * self.taper_outer

    @Attribute
    def taper_ratio(self):
        return self.chord_tip/self.chord_root

    @Attribute
    def half_span(self):
        return self.span

    @Attribute
    def planform_area(self):
        return ((self.chord_root+self.chord_kink)/2 * self.kink_position*self.half_span + (self.chord_kink+self.chord_tip)/2 * (1-self.kink_position)*self.half_span)*2

    @Attribute
    def mac(self):
        return 2/3*self.chord_root *(1+self.taper_ratio+self.taper_ratio**2)/(1+self.taper_ratio)

    @Attribute
    def chords(self):
        root = self.chord_root
        kink = self.chord_kink
        tip = self.chord_tip
        return root, kink, tip

    @Attribute
    def section_positions(self):
        sweep = radians(self.le_sweep)
        root = self.position
        tip = rotate(self.position.translate('x', self.half_span * tan(sweep),'y', self.half_span,'z',tan(radians(self.dihedral_deg))*self.half_span),
                     'y', -self.twist, deg=True)
        kink = rotate(self.position.translate('x', self.kink_position*self.half_span * tan(sweep),'y', self.kink_position*self.half_span,'z',tan(radians(self.dihedral_deg))*self.half_span*self.kink_position),
                     'y', self.kink_position*self.twist, deg=True)
        return root, kink, tip

    """
    @Part
    def root_section(self):
        return Section(airfoil_name=self.airfoil,
                       chord=self.chords[0],
                       position=self.section_positions[0])

    @Part
    def kink_section(self):
        return Section(airfoil_name=self.airfoil,
                       chord=self.chords[1],
                       position=self.section_positions[1])

    @Part
    def tip_section(self):
        return Section(airfoil_name=self.airfoil,
                       chord=self.chords[2],
                       position=self.section_positions[2])
    """
    @Attribute
    def reversed_coordinates(self):
        coords = []
        for i in range(len(self.airfoil_coordinates)):
            coords.append(self.airfoil_coordinates[-i-1])
        return coords

    @Attribute
    def unit_airfoil(self):
        return FittedCurve(self.reversed_coordinates, mesh_deflection=0.00001)

    @Part(parse=False)
    def root_section(self):
        return Section(chord=self.chords[0], unit_airfoil=self.unit_airfoil, section_positions=self.section_positions[0], twist=0)

    @Part(parse=False)
    def kink_section(self):
        return Section(chord=self.chords[1], unit_airfoil=self.unit_airfoil, section_positions=self.section_positions[1], twist=self.kink_position*self.twist)

    @Part(parse=False)
    def tip_section(self):
        return Section(chord=self.chords[2], unit_airfoil=self.unit_airfoil, section_positions=self.section_positions[2], twist=self.twist)

    @Part
    def surface1(self):
        return LoftedShell(profiles=[self.root_section.curve, self.kink_section.curve],
                           mesh_deflection=0.0001)

    @Part
    def surface2(self):
        return LoftedShell(profiles=[self.kink_section.curve, self.tip_section.curve],
                           mesh_deflection=0.0001)
    @Part
    def mirrored1(self):
        return MirroredSurface(surface_in=self.surface1.faces[0],
                               reference_point=self.position.point,
                               vector1=self.position.Vx,
                               vector2=self.position.Vz,
                               mesh_deflection=0.0001)

    @Part
    def mirrored2(self):
        return MirroredSurface(surface_in=self.surface2.faces[0],
                               reference_point=self.position.point,
                               vector1=self.position.Vx,
                               vector2=self.position.Vz,
                               mesh_deflection=0.0001)
    @Part
    def avl_surface1(self):
        return avl.Surface(name=self.name,
                           n_chordwise=12,
                           chord_spacing=avl.Spacing.cosine,
                           n_spanwise=20,
                           span_spacing=avl.Spacing.equal,
                           y_duplicate=self.position.point[0],
                           sections=[self.root_section.avl_section, self.kink_section.avl_section, self.tip_section.avl_section])


    @Attribute
    def avl_surfaces(self):  # this scans the product tree and collect all instances of the avl.Surface class
        return self.find_children(lambda o: isinstance(o, avl.Surface))
    @Part
    def avl_configuration(self):
        return avl.Configuration(name='aircraft',
                                 reference_area=self.planform_area,
                                 reference_span=self.span,
                                 reference_chord=self.mac,
                                 reference_point=self.position.point,
                                 surfaces=self.avl_surfaces,
                                 mach=self.mach)

class Avl_analysis(avl.Interface):
    aircraft = Input(in_tree=True)
    case_settings = Input()
    # name = Input("wing")
    # span = Input()
    # taper_outer = Input()
    # le_sweep = Input()
    # twist = Input()
    # airfoil = Input()
    # chord_root = Input()
    # chord_kink = Input()
    # kink_position = Input()
    # dihedral_deg = Input()
    # mach = Input(0.01)

    @Attribute
    def configuration(self):
        return self.aircraft.avl_configuration

    @Part
    def cases(self):
        return avl.Case(quantify=len(self.case_settings),
                        name=self.case_settings[child.index][0],
                        settings=self.case_settings[child.index][1])

    @Attribute
    def l_over_d(self):
        return {result['Totals']['CLtot']/result['Totals']['CDtot']
                for case_name, result in self.results.items()}


    def strip(self, i):
        return {(result['StripForces']['wing']['cl_norm'][i])
                for case_name, result in self.results.items()}

    @Attribute
    def cltot(self):
        return {result['Totals']['CLtot']
                for case_name, result in self.results.items()}

    # @Attribute
    # def clmax(self):
    #     Avl_aircraft = Wing(name=self.name,
    #                span=self.span,
    #                taper_outer=self.taper_outer,
    #                le_sweep=self.le_sweep,
    #                twist=self.twist,
    #                airfoil=self.airfoil,
    #                chord_root=self.chord_root,
    #                chord_kink=self.chord_kink,
    #                kink_positionm=self.kink_position,
    #                dihedral_deg=self.dihedral_deg,
    #                mach=self.mach
    #                )
    #     clnorm = 0
    #     aoa = 0
    #     cltotlist = []
    #     while clnorm < self.clmaxfoil:
    #         cases = [('fixed_aoa', {'alpha': aoa})]
    #         analysis = Avl_analysis(aircraft=Avl_aircraft,
    #                                 case_settings=cases,
    #                                 clmaxfoil=0.5)
    #
    #         clnorm = list(analysis.strip)[0]
    #         cltot = list(analysis.cltot)[0]
    #         aoa = aoa + 0.5
    #         cltotlist.append(cltot)
    #     return cltotlist[-2]



# if __name__ == '__main__':
#     air = Wing(name = 'wing',
#                     span = 50,
#                     taper_ratio = 1,
#                     le_sweep = 0,
#                     twist = 0,
#                     airfoil = '2024',
#                     chord_root = 5,
#                     chord_kink = 5,
#                     kink_position = 0.9,
#                     dihedral_deg = 0,
#                     mach = 0.1
#                    )
#     #['wing']['cl_norm']
#     # cases = [('fixed_aoa', {'alpha':2})]
#     # analysis = Avl_analysis(aircraft=air,
#     #                         case_settings=cases)
#     clnorm = 0.1
#     aoa = 0
#     clnormlist = []
#     cltotlist = []
#     while clnorm < 0.2:
#         cases = [('fixed_aoa', {'alpha':aoa})]
#         analysis = Avl_analysis(aircraft=air,
#                                 case_settings=cases)
#
#         clnorm = list(analysis.strip)[0]
#         cltot = list(analysis.cltot)[0]
#         aoa = aoa+0.5
#         clnormlist.append(clnorm)
#         cltotlist.append(cltot)
#
#     display(analysis)





























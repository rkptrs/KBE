
from parapy.geom import *
from parapy.core import *
import kbeutils.avl as avl
from parapy.core.validate import AdaptedValidator
from utilities.functions import p2v
import numpy as np

_len_4_or_5 = AdaptedValidator(lambda a: 4 <= len(a) <= 5)


class Section(GeomBase):
    
    #Inputs
    chord = Input()
    unit_airfoil = Input()
    section_positions = Input()
    twist = Input()


    @Attribute
    def curve(self):    # the curve is first scaled to the size of the requested chord and then twisted by the amount
                        # dictated by the spanwise position and the twist angle
        scaled_airfoil = ScaledCurve(self.unit_airfoil, factor=self.chord, reference_point=Point(0, 0, 0), mesh_deflection=0.00001)
        twisted_airfoil = RotatedCurve(scaled_airfoil, Point(0, 0, 0), Vector(0, 1, 0), self.twist*np.pi/180)
        return TranslatedCurve(twisted_airfoil, p2v(self.section_positions), color="blue")




    @Part  # the camber of the airfoil is accounted. Any curve is allowed. It includes avl_section_by_points
    def avl_section(self):
        return avl.SectionFromCurve(curve_in=self.curve)




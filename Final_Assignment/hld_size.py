from math import *

from parapy.core import *
from parapy.geom import *
from hld_functions import K, cldf, Kprime, adf, cldelta
import warnings
from tkinter import Tk, mainloop, X, messagebox
import numpy as np
class HLDsize(GeomBase):


    ##Inputs##

    root_chord = Input()
    kink_position = Input()
    sweep = Input()
    dihedral = Input()
    taper_inner = Input()
    taper_outer = Input()
    wing_span = Input()
    frontpar = Input()
    rearspar = Input()
    aileronloc = Input()
    fuselage_radius = Input()
    flap_gap = Input()
    naca = Input()
    clalpha = Input(2*pi)
    clmaxclean = Input()
    clmaxflapped = Input()
    trimfactor = Input(1.1)
    flaptype = Input()
    singleflap = Input()
    angle_max = Input(45)

    @Attribute
    def t_c(self):
        return int(self.naca[-2:])/100

    @Attribute
    def fuselageloc(self):
        return self.fuselage_radius/self.span

    @Attribute
    def coor1(self):
        return [0, 0, 0]

    @Attribute
    def coor2(self):
        return [self.root_chord, 0, 0]

    @Attribute
    def coor3(self):
        return [self.kink_position*np.tan(radians(self.sweep)), self.kink_position, self.kink_position*np.tan(radians(self.dihedral))]

    @Attribute
    def coor4(self):
        return [self.kink_position * np.tan(radians(self.sweep)) + self.root_chord*self.taper_inner, self.kink_position,
                self.kink_position * np.tan(radians(self.dihedral))]

    @Attribute
    def chordkink(self):
        return self.coor4[0] - self.coor3[0]

    @Attribute
    def coor5(self):
        return [self.wing_span * np.tan(radians(self.sweep)),
                self.wing_span,
                self.wing_span * np.tan(radians(self.dihedral))]

    @Attribute
    def coor6(self):
        return [self.wing_span * np.tan(radians(self.sweep)) + self.chordkink*self.taper_outer,
                self.wing_span,
                self.wing_span * np.tan(radians(self.dihedral))]

    @Attribute
    def chordroot(self):
        return self.root_chord

    @Attribute
    def chordkink(self):
        return self.coor4[0]-self.coor3[0]
    @Attribute
    def chordtip(self):
        return self.coor6[0]-self.coor5[0]


    @Attribute
    def span(self):
        return (self.coor5[1]-self.coor1[1])

    @Attribute
    def kinkloc(self):
        return (self.coor3[1]-self.coor1[1])/self.span

    @Attribute
    def flap1stop(self):
        return self.kinkloc

    @Attribute
    def flap2start(self):
        return self.flap1stop + self.flap_gap/self.span

    @Attribute
    def chordfuselage(self):
        return self.chordroot - (self.chordroot - self.chordkink) * (self.fuselageloc/self.kinkloc)

    @Attribute
    def chordaileron(self):
        return self.chordkink - (self.chordkink- self.chordtip) * ((self.aileronloc-self.kinkloc) / (1-self.kinkloc))

    @Attribute
    def chordflapstop(self):
        if self.flap1stop <= self.kinkloc:
            chordflapstop = self.chordroot - (self.chordroot - self.chordkink) * (self.flap1stop / self.kinkloc)
        elif self.flap1stop > self.kinkloc:
            chordflapstop = self.chordkink - (self.chordkink - self.chordtip) * ((self.flap1stop-self.kinkloc) / (1-self.kinkloc))
        return chordflapstop

    @Attribute
    def chordflapstart(self):
        if self.flap2start <= self.kinkloc:
            chordflapstart = self.chordroot - (self.chordroot - self.chordkink) * (self.flap2start / self.kinkloc)
        elif self.flap2start > self.kinkloc:
            chordflapstart = self.chordkink - (self.chordkink - self.chordtip) * (
                        (self.flap2start - self.kinkloc) / (1 - self.kinkloc))
        return chordflapstart

    @Attribute
    def cfc(self):
        return 1 - self.rearspar

    @Attribute
    def area1(self):
        return (self.chordroot + self.chordkink) * sqrt(
            self.coor3[1] ** 2 + self.coor3[2] ** 2)

    @Attribute
    def area2(self):
        return (self.chordkink + self.chordtip) * sqrt(
            (self.coor5[1] - self.coor3[1]) ** 2 + (self.coor5[2] - self.coor3[2]) ** 2)

    @Attribute
    def s(self):
        return self.area1 + self.area2

    @Attribute
    def sweep1_4_1(self):
        return atan((self.coor3[0]+0.25*self.chordkink-self.coor1[0]-0.25*self.chordroot)/(self.coor3[1]-self.coor1[1]))

    @Attribute
    def sweep1_4_2(self):
        return atan((self.coor5[0]+0.25*self.chordtip-self.coor3[0]-0.25*self.chordkink)/(self.coor5[1]-self.coor3[1]))

    @Attribute
    def avgsweep1_4(self):
        return (self.sweep1_4_1*self.area1+self.sweep1_4_2*self.area2)/self.s



    @Attribute
    def sf1(self):
        if self.flap1stop <= self.kinkloc:
            sf1 = (self.chordfuselage+self.chordflapstop)*(self.flap1stop-self.fuselageloc)*self.span
        elif self.flap1stop > self.kinkloc:
            sf1 = (self.chordfuselage+self.chordkink)*(self.kinkloc-self.fuselageloc)*self.span + (self.chordkink+self.chordflapstop)*(self.flap1stop-self.kinkloc)*self.span
        return sf1

    @Attribute
    def sf2(self):
        if self.flap2start < self.kinkloc:
            sf2 = (self.chordflapstart + self.chordkink) * (self.kinkloc - self.flap2start) * self.span  + (
                        self.chordkink + self.chordaileron) * (self.aileronloc - self.kinkloc) * self.span
        elif self.flap2start >= self.kinkloc:
            sf2 = (self.chordflapstart + self.chordaileron) * (self.aileronloc - self.flap2start) * self.span
        return sf2

    @Attribute
    def sf(self):
        if self.singleflap:
            sf = self.sf1
        elif not self.singleflap:
            sf = self.sf1+self.sf2
        return sf

    @Attribute
    def clmaxtrim(self):
        return self.clmaxclean/self.trimfactor

    @Attribute
    def dclmaxtrimmed(self):
        if self.clmaxtrim >= self.clmaxflapped:
            error('The clean wing can already attain the required CLmax, no flaps are required.')
        return 1.05*(self.clmaxflapped-self.clmaxtrim)

    @Attribute
    def klambda(self):
        return (1-0.08*cos(self.avgsweep1_4)**2)*cos(self.avgsweep1_4)**(3/4)

    @Attribute
    def dclmax(self):
        return self.dclmaxtrimmed*self.klambda*self.s/self.sf

    @Attribute
    def dcl_flap(self):
        if self.flaptype == "Plain":
            k = K(self.cfc, 1)
            dcltarget = (1 / k) * self.dclmax
            dcl45 = cldf(self.cfc, self.t_c) * radians(self.angle_max) * Kprime(self.angle_max, self.cfc)
            return dcl45, dcltarget
        elif self.flaptype == "Fowler":
            k = K(self.cfc, 3)
            dcltarget = (1 / k) * self.dclmax
            clalphaf = self.clalpha * (1 + self.cfc)
            dcl45 = clalphaf * adf(self.angle_max, self.cfc) * radians(self.angle_max)
            return dcl45, dcltarget
        elif self.flaptype == "Slotted":
            k = K(self.cfc, 2)
            dcltarget = (1 / k) * self.dclmax
            dcl45 = self.clalpha * adf(self.angle_max, self.cfc) * radians(self.angle_max)
            return dcl45, dcltarget
        else:
            return error('Flap name not recognised')

    @Attribute
    def can_attain(self):
        if self.dcl_flap[0] >= self.dcl_flap[1]:
            attain_flap = True
        elif self.dcl_flap[0] < self.dcl_flap[1]:
            attain_flap = False
            error('With the chosen flap type and rear spar location, the wing cannot attain the specified CLmax.'
                  'Choose a different flap type, move the rear spar forward or increase the maximum deflection angle of the flap')
        return attain_flap





# class Plainflap(GeomBase):
#     angle = Input()
#     @Part
#     def hldsize(self):
#         return HLDsize()
#
#     @Attribute
#     def k(self):
#         return K(self.hldsize.cfc,1)
#
#     @Attribute
#     def dcltarget(self):
#         return (1/self.k)*self.hldsize.dclmax
#
#     @Attribute
#     def dcl45(self):
#         return cldf(self.hldsize.cfc,self.hldsize.t_c)*radians(self.angle)*Kprime(self.angle,self.hldsize.cfc)
#
# class Singleslot(GeomBase):
#     angle = Input()
#     @Part
#     def hldsize(self):
#         return HLDsize()
#
#     @Attribute
#     def K(self):
#         return K(self.hldsize.cfc,2)
#
#     @Attribute
#     def dcltarget(self):
#         return (1/self.K)*self.hldsize.dclmax
#
#     @Attribute
#     def dcl45(self):
#         return self.hldsize.clalpha * adf(self.angle,self.hldsize.cfc)*radians(self.angle)
#
#
# class Fowler(GeomBase):
#     angle = Input()
#     @Part
#     def hldsize(self):
#         return HLDsize()
#
#     @Attribute
#     def K(self):
#         return K(self.hldsize.cfc,2)
#
#     @Attribute
#     def dcltarget(self):
#         return (1/self.K)*self.hldsize.dclmax
#
#     @Attribute
#     def clalphaf(self):
#         return self.hldsize.clalpha*(1+self.hldsize.cfc)
#
#     @Attribute
#     def dcl45(self):
#         return self.clalphaf * adf(self.angle,self.hldsize.cfc)*radians(self.angle)
#
#
# class Krueger(GeomBase):
#
#     @Part
#     def hldsize(self):
#         return HLDsize()
#
#     @Attribute
#     def dclkr(self):
#         dclkrmax = 0
#         for i in range(0,30):
#             df = radians(i)
#             cprime = 1 + self.hldsize.frontspar * cos(df)
#             dclk = cldelta(self.hldsize.cfc)*i*cprime
#             if dclk > dclkrmax:
#                 dclkrmax = dclk
#         return dclkrmax










def error(msg):
    window = Tk()
    window.withdraw()
    messagebox.showwarning("Invalid Input", msg)









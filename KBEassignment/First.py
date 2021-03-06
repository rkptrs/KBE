from math import *

from parapy.core import *
from parapy.geom import *
from functions import K, cldf, Kprime, adf, cldelta

class HLDsize(GeomBase):


    ##Temporary inputs###

    kink = Input(True)
    coordinates = Input(True)
    leadingflap = Input(True)
    flapsplit = Input(True)
    coor1 = Input([0, 0, 0])
    coor2 = Input([3, 0, 0])
    coor3 = Input([1, 5, 0])
    coor4 = Input([3, 5, 0])
    coor5 = Input([6, 15, 0])
    coor6 = Input([7, 15, 0])
    #Spar location with respect to chord
    frontspar = Input(0.2)
    rearspar = Input(0.75)
    #locations with respect to span
    aileronloc = Input(0.9)
    fuselageloc = Input(0.15)
    flap1stop = Input(0.4)
    flap2start = Input(0.5)
    t_c = Input(0.10)
    clalpha = Input(2*pi)
    clmaxclean = Input(1.6)
    clmaxflapped = Input(2.5)
    trimfactor = Input(1.1)


    @Attribute
    def chordroot(self):
        return self.coor2[0]-self.coor1[0]

    @Attribute
    def chordkink(self):
        return self.coor4[0]-self.coor3[0]
    @Attribute
    def chordtip(self):
        return self.coor6[0]-self.coor5[0]


    @Attribute
    def span(self):
        return self.coor5[1]-self.coor1[1]

    @Attribute
    def kinkloc(self):
        return (self.coor3[1]-self.coor1[1])/self.span

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
            self.coor3[1] ** 2 + self.coor3[2] ** 2) / 2

    @Attribute
    def area2(self):
        return (self.chordkink + self.chordtip) * sqrt(
            (self.coor5[1] - self.coor3[1]) ** 2 + (self.coor5[2] - self.coor3[2]) ** 2) / 2

    @Attribute
    def S(self):
        return self.area1 + self.area2

    @Attribute
    def sweep1_4_1(self):
        return atan((self.coor3[0]+0.25*self.chordkink-self.coor1[0]-0.25*self.chordroot)/(self.coor3[1]-self.coor1[1]))

    @Attribute
    def sweep1_4_2(self):
        return atan((self.coor5[0]+0.25*self.chordtip-self.coor3[0]-0.25*self.chordkink)/(self.coor5[1]-self.coor3[1]))

    @Attribute
    def avgsweep1_4(self):
        return (self.sweep1_4_1*self.area1+self.sweep1_4_2*self.area2)/self.S



    @Attribute
    def Sf1(self):
        if self.flap1stop <= self.kinkloc:
            sf1 = (self.chordfuselage+self.chordflapstop)*(self.flap1stop-self.fuselageloc)*self.span/2
        elif self.flap1stop > self.kinkloc:
            sf1 = (self.chordfuselage+self.chordkink)*(self.kinkloc-self.fuselageloc)*self.span/2 + (self.chordkink+self.chordflapstop)*(self.flap1stop-self.kinkloc)*self.span/2
        return sf1

    @Attribute
    def Sf2(self):
        if self.flap2start < self.kinkloc:
            sf2 = (self.chordflapstart + self.chordkink) * (self.kinkloc - self.flap2start) * self.span / 2 + (
                        self.chordkink + self.chordaileron) * (self.aileronloc - self.kinkloc) * self.span / 2
        elif self.flap2start >= self.kinkloc:
            sf2 = (self.chordflapstart + self.chordaileron) * (self.aileronloc - self.flap2start) * self.span / 2
        return sf2

    @Attribute
    def Sf(self):
        return self.Sf1+self.Sf2

    @Attribute
    def clmaxtrim(self):
        return self.clmaxclean*self.trimfactor

    @Attribute
    def dclmaxtrimmed(self):
        return 1.05*(self.clmaxflapped-self.clmaxtrim)
    @Attribute
    def klambda(self):
        return (1-0.08*cos(self.avgsweep1_4)**2)*cos(self.avgsweep1_4)**(3/4)

    @Attribute
    def dclmax(self):
        return self.dclmaxtrimmed*self.klambda*self.S/self.Sf


class Plainflap(GeomBase):

    @Part
    def hldsize(self):
        return HLDsize()

    @Attribute
    def K(self):
        return K(self.hldsize.cfc,1)

    @Attribute
    def dcltarget(self):
        return (1/self.K)*self.hldsize.dclmax

    @Attribute
    def dcl45(self):
        return cldf(self.hldsize.cfc,self.hldsize.t_c)*radians(45)*Kprime(45,self.hldsize.cfc)

class Singleslot(GeomBase):

    @Part
    def hldsize(self):
        return HLDsize()

    @Attribute
    def K(self):
        return K(self.hldsize.cfc,2)

    @Attribute
    def dcltarget(self):
        return (1/self.K)*self.hldsize.dclmax

    @Attribute
    def dcl45(self):
        return self.hldsize.clalpha * adf(45,self.hldsize.cfc)*radians(45)


class Fowler(GeomBase):

    @Part
    def hldsize(self):
        return HLDsize()

    @Attribute
    def K(self):
        return K(self.hldsize.cfc,2)

    @Attribute
    def dcltarget(self):
        return (1/self.K)*self.hldsize.dclmax

    @Attribute
    def clalphaf(self):
        return self.hldsize.clalpha*(1+self.hldsize.cfc)

    @Attribute
    def dcl45(self):
        return self.clalphaf * adf(45,self.hldsize.cfc)*radians(45)


class Krueger(GeomBase):

    @Part
    def hldsize(self):
        return HLDsize()

    @Attribute
    def dclkr(self):
        dclkrmax = 0
        for i in range(0,30):
            df = radians(i)
            cprime = 1 + self.hldsize.frontspar * cos(df)
            dclk = cldelta(self.hldsize.cfc)*i*cprime
            if dclk > dclkrmax:
                dclkrmax = dclk
        return dclkrmax






obj = HLDsize()
obj1 = Krueger()






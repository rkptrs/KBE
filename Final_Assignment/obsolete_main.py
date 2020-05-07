"""
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
                                  singleflap=False,
                                  angle_max=self.input.max_deflection)
                dcl45 = hldsize.dcl_flap[0]
                dcl_target = hldsize.dcl_flap[1]
            flaparea = self.hldSize.sf1*(1-newspar+0.01)
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
                               singleflap=True,
                               angle_max=self.input.max_deflection)
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
                                      singleflap=True,
                                      angle_max=self.input.max_deflection)
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
    """
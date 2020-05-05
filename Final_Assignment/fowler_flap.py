from parapy.geom import *
from parapy.core import *
from functions import p2v, v2p, interp_coords, split_coordinates, hinge_position, v
from wing_section import Wing_base
import numpy as np


class Fowler_flap_section(Wing_base):

    @Attribute
    def hinge_points(self):
        out = [0, 0]
        for i in range(2):
            out[i] = Point(self.flap_hinge_location*self.chords[i] + self.points[i][0],
                           self.points[i][1],
                           self.points[i][2] + (self.hinge_dimension[0] - self.hinge_dimension[1]/4)*self.chords[i])
        return out

    @Attribute
    def flap_split_circles(self):
        circles = [0, 0]
        for i in range(2):
            position = hinge_position(self.hinge_points[i])
            circles[i] = Arc(self.hinge_dimension[1]*self.chords[i]/4, angle=3*np.pi/2, position=position,
                             start=self.hinge_points[i] + Vector(0, 0, 1), mesh_deflection=v.md)
        return circles

    @Attribute
    def camber_line(self):
        xb, zb, xt, zt = split_coordinates(self.airfoil_coordinates)
        x_locations = np.linspace(self.flap_hinge_location, 1, 25)
        points_list_1, points_list_2 = [], []
        for i in range(len(x_locations)):
            z_bottom = interp_coords(xb, zb, x_locations[i])
            z_top = interp_coords(xt, zt, x_locations[i])
            margin = (x_locations[i]-self.flap_hinge_location)*0.01
            points_list_1.append(Point(x_locations[i], 0, (z_top + z_bottom)/2))
            points_list_2.append(Point(x_locations[i], 0, (z_top+z_bottom)/2+margin))
        lines_1, lines_2 = [], []
        for i in range(2):
            lines_1.append(FittedCurve(np.array(points_list_1)*self.chords[i]+p2v(self.points[i]), mesh_deflection=v.md))
            lines_2.append(FittedCurve(np.array(points_list_2) * self.chords[i] + p2v(self.points[i]), mesh_deflection=v.md))
        return lines_1, lines_2

    @Attribute
    def flap_split_surface(self):
        composed_1, composed_2 = [0, 0], [0, 0]
        for i in range(2):
            composed_1[i] = Wire([self.camber_line[0][i], self.flap_split_circles[i]], mesh_deflection=v.md).compose()
            composed_2[i] = Wire([self.camber_line[1][i], self.flap_split_circles[i]], mesh_deflection=v.md).compose()
        return RuledSurface(composed_1[0], composed_1[1], mesh_deflection=v.md), RuledSurface(composed_2[0], composed_2[1], mesh_deflection=v.md)

    @Attribute
    def split_wing(self):       # Split wing along flap split surface
        parts = SplitSolid(self.wing_solid, self.flap_split_surface[0], mesh_deflection=v.md).solids
        if len(parts) > 1:
            return parts, "Yellow"
        else:
            parts = SplitSolid(self.wing_solid, self.flap_split_surface[1], mesh_deflection=v.md).solids
            from read_input import error
            error("Airfoil trailing edge is too sharp for an optimal fowler flap design. Flap geometry was modified in order to make it feasible.")
            return parts, "Red"

    @Attribute
    def wing_parts(self):       # Sort parts according to volume
        parts = self.split_wing[0]
        volumes = []
        for p in parts:
            volumes.append(p.volume)
        wing_index = volumes.index(max(volumes))
        volumes[wing_index] = 0
        flap_index = volumes.index(max(volumes))
        return parts[wing_index], parts[flap_index]

    @Part
    def main_wing(self):
        return Solid(self.wing_parts[0], mesh_deflection=v.md)

    @Attribute
    def flap_displacement(self):  # Defined at average chord
        if self.flap_deflection > 0:
            z_displacement_factor = 0.5
            x_displacement = (1 - self.flap_hinge_location)*np.mean(self.chords)
            z_displacement = -self.hinge_dimension[0] - self.hinge_dimension[1]*(1 + z_displacement_factor)
            return Vector(x_displacement, 0, z_displacement)
        else:
            return Vector(0, 0, 0)

    @Attribute
    def z_rot_correction(self):
        dx = (1 - self.flap_hinge_location - self.flap_displacement[0]/np.mean(self.chords))*(
                    self.chords[1] - self.chords[0]) + self.points[1][0] - self.points[0][1]
        return np.arctan(dx / (self.points[1][1] - self.points[0][1])) - self.flap_sweep

    @Attribute
    def x_rot_correction(self):
        dz = self.flap_displacement[2]*(0.5*(self.chords[0]/self.chords[1] - 1) + 1)*(1 - self.chords[1]/self.chords[0])
        return - np.arctan(dz/(self.points[1][1] - self.points[0][1]))

    @Attribute
    def rotated_flap(self):
        deflected_flap = RotatedShape(self.wing_parts[1], self.hinge_points[0],  # Rotate around hinge
                                      p2v(self.hinge_points[0])-p2v(self.hinge_points[1]),
                                      angle=-self.flap_deflection*np.pi/180, mesh_deflection=v.md)
        center_point = v2p(p2v(self.hinge_points[0]) / 2 + p2v(self.hinge_points[1]) / 2)  # Rotation point for corrections
        deflected_flap = RotatedShape(deflected_flap, center_point, Vector(0, 0, 1), angle=self.z_rot_correction, mesh_deflection=v.md)  # Adjust rotation around z axis
        return RotatedShape(deflected_flap, center_point, Vector(1, 0, 0), angle=self.x_rot_correction, mesh_deflection=v.md)  # Adjust rotation around x axis

    @Part
    def flap(self):
        return TranslatedShape(self.rotated_flap, displacement=self.flap_displacement, color=self.split_wing[1], mesh_deflection=v.md)  #Translate flap backwards

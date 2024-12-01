


class LabelObj(object):
    def __init__(self, path, name, hemi, color, opacity, border):
        self.path = path
        self.name = name
        self.hemi = hemi
        self.color = color
        self.opacity = opacity
        self.border = border


class AnnotObj(object):
    def __init__(self, path, name, hemi, opacity, border):
        self.path = path
        self.name = name
        self.hemi = hemi
        self.opacity = float(opacity)
        self.border = border


class SurfObj(object):
    def __init__(self, path, name, hemi, color, aesthetic, opacity):
        self.path = path
        self.name = name
        self.hemi = hemi
        self.color = color
        self.aesthetic = aesthetic
        self.opacity = opacity


class FociObj(object):
    def __init__(self, x, y, z, name, hemi, map_surface, scale_factor, color, opacity):
        self.x = x
        self.y = y
        self.z = z
        self.map_surface = map_surface
        self.scale_factor = scale_factor
        self.color = color
        self.opacity = opacity
        self.name = name
        self.hemi = hemi



# class ChannelObj(object):
#     def __init__(self, name, x, y, z, hemi, scale_factor, color, opacity):
#         self.


class ElecObj(object):
    def __init__(self, name, channels):
        self.name = name
        self.elec_type = elec_type
        self.channels = channels
        self.color = color
        self.scale_factor = scale_factor
        self.opacity = opacity

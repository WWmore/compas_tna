from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import compas_rhino

from compas_rhino import MeshArtist
from compas_tna.diagrams import FormDiagram


__author__    = ['Tom Van Mele', ]
__copyright__ = 'Copyright 2014 - Block Research Group, ETH Zurich'
__license__   = 'MIT License'
__email__     = 'vanmelet@ethz.ch'


__all__ = ['RhinoFormDiagram', ]


class RhinoFormDiagram(FormDiagram):

    def __init__(self):
        super(RhinoFormDiagram, self).__init__()
        self.attributes.update({
            'layer': 'FormDiagram'
        })

    def draw(self):
        vertexcolor = {}
        for name in ('is_fixed', 'is_anchor'):
            a = 'color.vertex:{}'.format(name)
            vertexcolor.update({key: self.attributes[a] for key in self.vertices_where({name: True})})

        artist = MeshArtist(self, layer=self.attributes['layer'])
        artist.clear_layer()
        artist.draw_vertices(color=vertexcolor)
        artist.draw_edges(keys=list(self.edges_where({'is_edge': True})))
        artist.draw_faces(fkeys=list(self.faces_where({'is_unloaded': False})))
        artist.redraw()

    # ==========================================================================
    # modify
    # ==========================================================================

    # anchor vertex
    # move vertex
    # pull down vertex
    # smooth pattern
    # subdivide
    # constrain vertex locations

    # ==========================================================================
    # visualisation
    # ==========================================================================

    def hide_(self, spec):
        name = self.attributes['name']
        guids = compas_rhino.get_objects(name="{}.{}.*".format(name, spec))
        compas_rhino.delete_objects(guids)

    def hide_reactions(self):
        self.hide_('reaction')

    def hide_selfweight(self):
        self.hide_('selfweight')

    def hide_loads(self):
        self.hide_('load')

    def hide_residuals(self):
        self.hide_('residual')

    def show_reactions(self):
        self.hide_reactions()

        name = self.attributes['name']
        layer = self.attributes['layer']
        color = self.attributes['color.reaction']
        scale = self.attributes['scale.reaction']

        lines = []
        for key, attr in self.vertices(True):
            if not attr['is_anchor']:
                continue

            rx, ry, rz = attr['rx'], attr['ry'], attr['rz']
            x, y, z = attr['x'], attr['y'], attr['z']
            ep = x + scale * rx, y + scale * ry, z + scale * rz

            lines.append({
                'start' : (x, y, z),
                'end'   : ep,
                'name'  : "{}.reaction.{}".format(name, key),
                'color' : color,
                'arrow' : 'start'
            })

        compas_rhino.xdraw_lines(lines, layer=layer, clear=False, redraw=True)

    def show_selfweight(self):
        self.hide_selfweigt()

        name = self.attributes['name']
        layer = self.attributes['layer']
        color = self.attributes['color.selfweight']
        scale = self.attributes['scale.selfweight']

        lines = []
        for key, attr in self.vertices(True):
            lines.append({})

        compas_rhino.xdraw_lines(lines, layer=layer, clear=False, redraw=True)

    def show_loads(self):
        self.hide_loads()

        name = self.attributes['name']
        layer = self.attributes['layer']
        color = self.attributes['color.load']
        scale = self.attributes['scale.load']

        lines = []
        for key, attr in self.vertices(True):
            lines.append({})

        compas_rhino.xdraw_lines(lines, layer=layer, clear=False, redraw=True)

    def show_residuals(self):
        self.hide_residuals()

        name = self.attributes['name']
        layer = self.attributes['layer']
        color = self.attributes['color.residual']
        scale = self.attributes['scale.residual']

        lines = []
        for key, attr in self.vertices(True):
            if attr['is_anchor']:
                continue

            lines.append({})

        compas_rhino.xdraw_lines(lines, layer=layer, clear=False, redraw=True)


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":
    pass

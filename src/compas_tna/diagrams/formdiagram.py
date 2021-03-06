from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys

from math import pi
from math import sin
from math import cos
from math import sqrt

import compas
import compas_tna

from compas.utilities import pairwise

from compas.datastructures.mesh.mesh import TPL

from compas.geometry import subtract_vectors_xy
from compas.geometry import add_vectors_xy
from compas.geometry import normalize_vector_xy
from compas.geometry import cross_vectors
from compas.geometry import mesh_smooth_area

from compas_tna.diagrams import Diagram


__author__  = 'Tom Van Mele'
__email__   = 'vanmelet@ethz.ch'


__all__ = ['FormDiagram']


class FormDiagram(Diagram):
    """"""

    def __init__(self):
        super(FormDiagram, self).__init__()
        self.default_vertex_attributes.update({
            'x'           : 0.0,
            'y'           : 0.0,
            'z'           : 0.0,
            'px'          : 0.0,
            'py'          : 0.0,
            'pz'          : 0.0,
            'sw'          : 0.0,
            't'           : 1.0,
            'is_anchor'   : False,
            'is_fixed'    : False,
            'is_external' : False,
            'rx'          : 0.0,
            'ry'          : 0.0,
            'rz'          : 0.0,
        })
        self.default_edge_attributes.update({
            'q'           : 1.0,
            'l'           : 0.0,
            'f'           : 0.0,
            'qmin'        : 1e-7,
            'qmax'        : 1e+7,
            'lmin'        : 1e-7,
            'lmax'        : 1e+7,
            'fmin'        : 1e-7,
            'fmax'        : 1e+7,
            'a'           : 0.0,
            'is_edge'     : True,
            'is_external' : False
        })
        self.default_face_attributes.update({
            'is_loaded': True
        })
        self.attributes.update({
            'name'             : 'FormDiagram',

            'color.vertex'     : (255, 255, 255),
            'color.edge'       : (0, 0, 0),
            'color.face'       : (210, 210, 210),
            'color.reaction'   : (0, 255, 0),
            'color.residual'   : (0, 255, 255),
            'color.load'       : (0, 255, 0),
            'color.selfweight' : (0, 0, 255),
            'color.force'      : (0, 0, 255),

            'scale.reaction'   : 1.0,
            'scale.residual'   : 1.0,
            'scale.load'       : 1.0,
            'scale.force'      : 1.0,
            'scale.selfweight' : 1.0,

            'tol.reaction'     : 1e-3,
            'tol.residual'     : 1e-3,
            'tol.load'         : 1e-3,
            'tol.force'        : 1e-3,
            'tol.selfweight'   : 1e-3,

            'feet.scale'       : 0.1,
            'feet.alpha'       : 45,
            'feet.tol'         : 0.1,
        })

    @classmethod
    def from_rhinomesh(cls, guid):
        """Construct a FormDiagram from a Rhino mesh represented by a guid.

        Parameters
        ----------
        guid : str
            A globally unique identifier.

        Returns
        -------
        FormDiagram
            A Formdiagram object.

        Examples
        --------
        .. code-block:: python

            import compas_rhino
            from compas_tna.diagrams import FormDiagram

            guid = compas_rhino.select_mesh()
            form = FormDiagram.from_rhinomesh(guid)

        """
        from compas_rhino.helpers import mesh_from_guid
        return mesh_from_guid(cls, guid)

    @classmethod
    def from_lines(cls, lines, delete_boundary_face=True, precision=None):
        """Construct a FormDiagram from a list of lines described by start and end point coordinates.

        Parameters
        ----------
        lines : list
            A list of pairs of point coordinates.
        precision: str, optional
            The precision of the geometric map that is used to connect the lines.

        Returns
        -------
        FormDiagram
            A Formdiagram object.

        Examples
        --------
        .. code-block:: python

            from compas_tna.diagrams import FormDiagram

            form = FormDiagram.from_lines(lines)

        """
        from compas.topology import network_find_faces
        from compas.datastructures import Network
        network = Network.from_lines(lines, precision=precision)
        mesh = cls()
        for key, attr in network.vertices(True):
            mesh.add_vertex(key, x=attr['x'], y=attr['y'], z=0.0)
        mesh.halfedge = network.halfedge
        network_find_faces(mesh)
        if delete_boundary_face:
            mesh.delete_face(0)
        return mesh

    def __str__(self):
        """Compile a summary of the mesh."""
        numv = self.number_of_vertices()
        nume = len(list(self.edges_where({'is_edge': True})))
        numf = self.number_of_faces()
        vmin = self.vertex_min_degree()
        vmax = self.vertex_max_degree()
        fmin = self.face_min_degree()
        fmax = self.face_max_degree()
        return TPL.format(self.name, numv, nume, numf, vmin, vmax, fmin, fmax)

    def uv_index(self):
        """Returns a dictionary that maps edge keys (i.e. pairs of vertex keys)
        to the corresponding edge index in a list or array of edges.

        Returns
        -------
        dict
            A dictionary of uv-index pairs.

        """
        return {(u, v): index for index, (u, v) in enumerate(self.edges_where({'is_edge': True}))}

    def index_uv(self):
        """Returns a dictionary that maps edges in a list to the corresponding
        vertex key pairs.

        Returns
        -------
        dict
            A dictionary of index-uv pairs.

        """
        return dict(enumerate(self.edges_where({'is_edge': True})))

    # --------------------------------------------------------------------------
    # dual and reciprocal
    # --------------------------------------------------------------------------

    def dual(self, cls):
        """Construct the dual of the FormDiagram.

        Parameters
        ----------
        cls : Mesh
            The type of the dual.

        Returns
        -------
        Mesh
            The dual as an instance of type ``cls``.

        """
        dual = cls()
        fkey_centroid = {fkey: self.face_centroid(fkey) for fkey in self.faces()}
        outer = self.vertices_on_boundary()
        inner = list(set(self.vertices()) - set(outer))
        vertices = {}
        faces = {}
        for key in inner:
            fkeys = self.vertex_faces(key, ordered=True)
            for fkey in fkeys:
                if fkey not in vertices:
                    vertices[fkey] = fkey_centroid[fkey]
            faces[key] = fkeys
        for key, (x, y, z) in vertices.items():
            dual.add_vertex(key, x=x, y=y, z=z)
        for fkey, vertices in faces.items():
            dual.add_face(vertices, fkey=fkey)
        return dual

    # --------------------------------------------------------------------------
    # vertices
    # --------------------------------------------------------------------------

    def leaves(self):
        """Yields vertices with degree 1.
        
        Returns
        -------
        iterator
            An iterator of vertex keys.

        """
        return self.vertices_where({'vertex_degree': 1})

    def corners(self):
        """Yields vertices with degree 2.
        
        Returns
        -------
        iterator
            An iterator of vertex keys.

        """
        return self.vertices_where({'vertex_degree': 2})

    def anchors(self):
        return self.vertices_where({'is_anchor': True})

    def fixed(self):
        return self.vertices_where({'is_fixed': True})

    def residual(self):
        # there is a discrepancy between the norm of residuals calculated by the equilibrium functions`
        # and the result found here
        R = 0
        for key, attr in self.vertices_where({'is_anchor': False, 'is_fixed': False}, True):
            rx, ry, rz = attr['rx'], attr['ry'], attr['rz']
            R += sqrt(rx ** 2 + ry ** 2 + rz ** 2)
        return R

    # --------------------------------------------------------------------------
    # helpers
    # --------------------------------------------------------------------------

    def bbox(self):
        x, y, z = zip(* self.get_vertices_attributes('xyz'))
        return (min(x), min(y), min(z)), (max(x), max(y), max(z))

    # --------------------------------------------------------------------------
    # postprocess
    # --------------------------------------------------------------------------

    def collapse_small_edges(self, tol=1e-2):
        boundaries = self.vertices_on_boundaries()
        for boundary in boundaries:
            for u, v in pairwise(boundary):
                l = self.edge_length(u, v)
                if l < tol:
                    self.collapse_edge(v, u, t=0.5, allow_boundary=True)

    def smooth(self, fixed, kmax=10):
        mesh_smooth_area(self, fixed=fixed, kmax=kmax)

    # --------------------------------------------------------------------------
    # boundary conditions
    # --------------------------------------------------------------------------

    def update_boundaries(self, feet=2):
        boundaries = self.vertices_on_boundaries()
        exterior = boundaries[0]
        interior = boundaries[1:]
        self.update_exterior(exterior, feet=feet)
        self.update_interior(interior)

    def update_exterior(self, boundary, feet=2):
        """"""
        segments = self.split_boundary(boundary)
        if not feet:
            for vertices in segments:
                if len(vertices) > 2:
                    self.add_face(vertices, is_loaded=False)
                    u = vertices[-1]
                    v = vertices[0]
                    self.set_edge_attribute((u, v), 'is_edge', False)
                else:
                    u, v = vertices
                    self.set_edge_attribute((u, v), 'is_edge', False)
        else:
            self.add_feet(segments, feet=feet)

    def update_interior(self, boundaries):
        """"""
        for vertices in boundaries:
            self.add_face(vertices, is_loaded=False)

    def split_boundary(self, boundary):
        """"""
        segment = []
        segments = [segment]
        for key in boundary:
            segment.append(key)
            if self.vertex[key]['is_anchor']:
                segment = [key]
                segments.append(segment)
        segments[-1] += segments[0]
        del segments[0]
        return segments

    def add_feet(self, segments, feet=2):
        """"""
        def rotate(point, angle):
            x = cos(angle) * point[0] - sin(angle) * point[1]
            y = sin(angle) * point[0] + cos(angle) * point[1]
            return x, y, 0

        def cross_z(ab, ac):
            return ab[0] * ac[1] - ab[1] * ac[0]

        scale = self.attributes['feet.scale']
        alpha = self.attributes['feet.alpha'] * pi / 180
        tol   = self.attributes['feet.tol']

        key_foot = {}
        key_xy = {key: self.vertex_coordinates(key, 'xy') for key in self.vertices()}

        for i, vertices in enumerate(segments):
            key = vertices[0]
            after = vertices[1]
            before = segments[i - 1][-2]

            b = key_xy[before]
            o = key_xy[key]
            a = key_xy[after]

            ob = normalize_vector_xy(subtract_vectors_xy(b, o))
            oa = normalize_vector_xy(subtract_vectors_xy(a, o))

            z = cross_z(ob, oa)

            if z > +tol:
                r = normalize_vector_xy(add_vectors_xy(oa, ob))
                r = [-scale * axis for axis in r]

            elif z < -tol:
                r = normalize_vector_xy(add_vectors_xy(oa, ob))
                r = [+scale * axis for axis in r]

            else:
                ba = normalize_vector_xy(subtract_vectors_xy(a, b))
                r = cross_vectors([0, 0, 1], ba)
                r = [+scale * axis for axis in r]

            if feet == 1:
                x, y, z = add_vectors_xy(o, r)
                m = self.add_vertex(x=x, y=y, z=0, is_fixed=True, is_external=True)
                key_foot[key] = m

            elif feet == 2:
                lx, ly, lz = add_vectors_xy(o, rotate(r, +alpha))
                rx, ry, rz = add_vectors_xy(o, rotate(r, -alpha))
                l = self.add_vertex(x=lx, y=ly, z=0, is_fixed=True, is_external=True)
                r = self.add_vertex(x=rx, y=ry, z=0, is_fixed=True, is_external=True)
                key_foot[key] = l, r

            else:
                pass

        for vertices in segments:
            l = vertices[0]
            r = vertices[-1]

            if feet == 1:
                lm = key_foot[l]
                rm = key_foot[r]
                self.add_face([lm] + vertices + [rm], is_loaded=False)
                self.set_edge_attribute((l, lm), 'is_external', True)
                self.set_edge_attribute((rm, lm), 'is_edge', False)

            elif feet == 2:
                lb = key_foot[l][0]
                la = key_foot[l][1]
                rb = key_foot[r][0]
                self.add_face([lb, l, la], is_loaded=False)
                self.add_face([la] + vertices + [rb], is_loaded=False)
                self.set_edge_attribute((l, lb), 'is_external', True)
                self.set_edge_attribute((l, la), 'is_external', True)
                self.set_edge_attribute((lb, la), 'is_edge', False)
                self.set_edge_attribute((la, rb), 'is_edge', False)
            
            else:
                pass

    # --------------------------------------------------------------------------
    # visualisation
    # --------------------------------------------------------------------------

    def plot(self):
        from compas.plotters import MeshPlotter
        plotter = MeshPlotter(self)
        plotter.draw_vertices()
        plotter.draw_edges()
        plotter.draw_faces()
        plotter.show()

    def draw(self, layer=None, clear_layer=True):
        from compas_tna.rhino import FormArtist
        artist = FormArtist(self, layer=layer)
        if clear_layer:
            artist.clear_layer()
        vertexcolor = {}
        vertexcolor.update({key: '#00ff00' for key in self.vertices_where({'is_fixed': True})})
        vertexcolor.update({key: '#0000ff' for key in self.vertices_where({'is_external': True})})
        vertexcolor.update({key: '#ff0000' for key in self.vertices_where({'is_anchor': True})})
        artist.draw_vertices(color=vertexcolor)
        artist.draw_edges(keys=list(self.edges_where({'is_edge': True})))
        artist.draw_faces(keys=list(self.faces_where({'is_loaded': True})))
        artist.redraw()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    import compas
    from compas.files import OBJ

    filepath = compas.get('lines.obj')

    obj      = OBJ(filepath)
    vertices = obj.parser.vertices
    edges    = obj.parser.lines
    lines    = [(vertices[u], vertices[v], 0) for u, v in edges]

    form = FormDiagram.from_lines(lines)

    form.plot()

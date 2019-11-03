from cozmo_fsm import geometry
from math import sqrt, pi, atan2
import numpy as np

class Shape():
    def __init__(self, center=geometry.point()):
        if center is None: raise ValueError()
        self.center = center
        self.rotmat = geometry.identity()
        self.obstacle_id = None
    
    def __repr__(self):
        return "<%s >" % (self.__class__.__name__)

    def collides(self, shape):
        if isinstance(shape, Rectangle):
            return self.collides_rect(shape)
        elif isinstance(shape, Polygon):
            return self.collides_poly(shape)
        elif isinstance(shape, Circle):
            return self.collides_circle(shape)
        elif isinstance(shape, Compound):
            return shape.collides(self)
        else:
            raise Exception("%s has no collides() method defined for %s." % (self, shape))

    def get_bounding_box(self):
        """Should return ((xmin,ymin), (xmax,ymax))"""
        raise NotImplementedError("get_bounding_box")

#================ Basic Shapes ================

class Circle(Shape):
    def __init__(self, center=geometry.point(), radius=25/2):
        super().__init__(center)
        self.radius = radius
        self.orient = 0.

    def __repr__(self):
        id = self.obstacle_id if self.obstacle_id else '[no obstacle]'
        return '<Circle (%.1f,%.1f) r=%.1f %s>' % \
               (self.center[0,0], self.center[1,0], self.radius, id)

    def instantiate(self, tmat):
        return Circle(center=tmat.dot(self.center), radius=self.radius)        

    def collides_rect(self,rect):
        return rect.collides_circle(self)
        
    def collides_poly(self,poly):
        return poly.collides(self)

    def collides_circle(self,circle):
        dx = self.center[0,0] - circle.center[0,0]
        dy = self.center[1,0] - circle.center[1,0]
        dist = sqrt(dx*dx + dy*dy)
        return dist < (self.radius + circle.radius)
        
    def get_bounding_box(self):
        xmin = self.center[0,0] - self.radius
        xmax = self.center[0,0] + self.radius
        ymin = self.center[1,0] - self.radius
        ymax = self.center[1,0] + self.radius
        return ((xmin,ymin), (xmax,ymax))

class Polygon(Shape):
    def __init__(self, vertices=None, orient=0):
        center = vertices.mean(1)
        center.resize(4,1)
        super().__init__(center)
        self.vertices = vertices
        self.orient = orient # should move vertex rotation code from Rectangle to here
        N = vertices.shape[1]
        self.edges = tuple( (vertices[:,i:i+1], vertices[:,(i+1)%N:((i+1)%N)+1])
                            for i in range(N) )

    def get_bounding_box(self):
        mins = self.vertices.min(1)
        maxs = self.vertices.max(1)
        xmin = mins[0]
        ymin = mins[1]
        xmax = maxs[0]
        ymax = maxs[1]
        return ((xmin,ymin), (xmax,ymax))

    def collides_poly(self,poly):
        raise NotImplementedError()

    def collides_circle(self,circle):
        raise NotImplementedError()


class Rectangle(Polygon):
    def __init__(self, center=None, dimensions=None, orient=0):
        self.dimensions = dimensions
        self.orient = orient
        if not isinstance(dimensions[0],(float,int)):
            raise ValueError(dimensions)
        dx2 = dimensions[0]/2
        dy2 = dimensions[1]/2
        relative_vertices = np.array([[-dx2,  dx2, dx2, -dx2 ],
                                      [-dy2, -dy2, dy2,  dy2 ],
                                      [  0,    0,   0,    0  ],
                                      [  1,    1,   1,    1  ]])
        self.unrot = geometry.aboutZ(-orient)
        center_ex = self.unrot.dot(center)
        extents = geometry.translate(center_ex[0,0],center_ex[1,0]).dot(relative_vertices)
        # Extents measured along the rectangle's axes, not world axes
        self.min_Ex = min(extents[0,:])
        self.max_Ex = max(extents[0,:])
        self.min_Ey = min(extents[1,:])
        self.max_Ey = max(extents[1,:])
        vertices = geometry.translate(center[0,0],center[1,0]).dot(
            geometry.aboutZ(orient).dot(relative_vertices))
        super().__init__(vertices=vertices, orient=orient)

    def __repr__(self):
        id = self.obstacle_id if self.obstacle_id else '[no obstacle]'
        return '<Rectangle (%.1f,%.1f) %.1fx%.1f %.1f deg %s>' % \
               (self.center[0,0],self.center[1,0],*self.dimensions,
                self.orient*(180/pi), id)

    def instantiate(self, tmat):
        dimensions = (self.max_Ex-self.min_Ex, self.max_Ey-self.min_Ey)
        rot = atan2(tmat[1,0], tmat[0,0])
        return Rectangle(center = tmat.dot(self.center),
                         orient = rot + self.orient,
                         dimensions = dimensions)

    def collides_rect(self,other):
        # Test others edges in our reference frame
        o_verts = self.unrot.dot(other.vertices)
        o_min_x = min(o_verts[0,:])
        o_max_x = max(o_verts[0,:])
        o_min_y = min(o_verts[1,:])
        o_max_y = max(o_verts[1,:])
        if o_max_x <= self.min_Ex or self.max_Ex <= o_min_x or \
               o_max_y <= self.min_Ey or self.max_Ey <= o_min_y:
            return False

        if self.orient == other.orient: return True

        # Test our edges in other's reference frame
        s_verts = other.unrot.dot(self.vertices)
        s_min_x = min(s_verts[0,:])
        s_max_x = max(s_verts[0,:])
        s_min_y = min(s_verts[1,:])
        s_max_y = max(s_verts[1,:])
        if s_max_x <= other.min_Ex or other.max_Ex <= s_min_x or  \
               s_max_y <= other.min_Ey or other.max_Ey <= s_min_y:
            return False
        return True
            
    def collides_circle(self,circle):
        p = self.unrot.dot(circle.center)[0:2,0]
        pmin = p - circle.radius
        pmax = p + circle.radius
        if pmax[0] <= self.min_Ex or self.max_Ex <= pmin[0] or \
           pmax[1] <= self.min_Ey or self.max_Ey <= pmin[1]:
            return False
        # Need corner tests here
        return True

#================ Compound Shapes ================

class Compound(Shape):
    def __init__(self, shapes=[]):
        self.shapes = shapes

    def collides(self,shape):
        for s in self.shapes:
            if s.collides(shape):
                return True
        return False


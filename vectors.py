class Vector(tuple):

    def __add__(self, other): return Vector(v + w for v, w in zip(self, other))
    def __sub__(self, other): return Vector(v - w for v, w in zip(self, other))
    def __mul__(self, scalar): return Vector(scalar * v for v in self)
    def __rmul__(self, scalar):	return Vector(scalar * v for v in self)
    def __floordiv__(self, scalar): return Vector(v // scalar for v in self)
    def __neg__(self): return -1 * self

cdef class Class1:
    cdef int x
    cdef private_method(self)
    cpdef int add(self, int x)
    cpdef int add_two(self)
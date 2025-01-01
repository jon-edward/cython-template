from . cimport _module2


cdef class Class1:
    """
    This is a docstring for the entire class.
    """

    cdef private_method(self):
        """
        This is a docstring, but it won't appear in the stub.
        """
        self.x = 0

    def __init__(self):
        """
        This is the __init__ method.
        """
        self.private_method()
    
    cpdef int add(self, int x):
        """
        This adds an integer to the contained value, and returns the new integer.
        """
        self.x += x
        return self.x
    
    cpdef int add_two(self):
        """
        This adds two to the contained value, and returns the new integer.
        """
        self.x = _module2.custom_function2(self.x)
        return self.x

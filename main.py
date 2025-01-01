"""
This is a test script for using the test_cy Cython module
"""

from cython_template import module1, module2


# test access to private members

obj = module1.Class1()

try:
    print(obj.x)
except AttributeError:
    pass
else:
    assert False, "x should not be accessible"

try:
    print(obj.private_method())
except AttributeError:
    pass
else:
    assert False, "private_method should not be accessible"

print(obj.add(1))
print(obj.add_two())
print(module2.custom_function2(2))

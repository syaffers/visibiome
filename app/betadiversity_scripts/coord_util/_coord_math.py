"""Interface module to expose f2py functions like normal python module."""

import coord_math_f
for (func_name, func) in coord_math_f.coord_math_mod.__dict__.iteritems():
    if func_name != '__doc__':
        vars()[func_name] = func 
del func_name, func         # Don't expose these variables to importing modules

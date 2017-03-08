

def floatx(x):
    """Reads Fortran formatted floats."""
    x = x.strip()
    try:
        return float(x)
    except ValueError:
        if x[0] == '*':
            print 'WARNING: treating ******** as 9999.999 in mdcrd file.'
            return 9999.999
        elif x[1:].find('-') > 0 or x[1:].find('+') > 0:
            mantissa_start = x[1:].find('-') + x[1:].find('+') + 2
            return float(x[:mantissa_start] + 'E' + x[mantissa_start:])
        else:
            raise Exception("Can not convert '%s' to float." % x)

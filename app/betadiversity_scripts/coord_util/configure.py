#!/usr/bin/env python
"""Configure the makefile for the local computer."""

import os
import sys
import stat

def check_keys(dict):
    """Check that none of the keys in dict are substrings of another."""
    keys = dict.keys()
    for key in keys:
        for other_key in keys:
            if (key is not other_key) and (other_key.find(key) >= 0):
                raise Exception("Bad keys: %s is a substring of %s." % (key, other_key))


def configure(output_name, config_vars, input_name=None):
    """Create a new file by replacing strings according to the dict."""

    if input_name is None:
        input_name = output_name + '.in'

    if not os.path.exists(input_name):
        raise Exception("No such file: '%s'" % input_name)
    
    check_keys(config_vars)

    with open(input_name) as input_file:
        text = input_file.read()

    used_vars = []
    for (sig, fill) in config_vars.iteritems():
        if text.find(sig) >= 0:
            used_vars.append(sig)
        text = text.replace(sig, fill)


    # unused_vars = list(set(config_vars.keys()) - set(used_vars))
    # if unused_vars:
    #     print 'WARNING: unused configuration vars: ' + ', '.join(unused_vars) + '.'

    if os.path.exists(output_name):
        os.remove(output_name)
    with open(output_name, 'w') as output:
        output.write(text)
    
    # Remove write permissions to avoid accidental editing
    os.chmod(output_name, stat.S_IREAD)


def which(binary):
    """Return the path of the given executable."""
    if not binary:
        return None
    binary = str(binary)
    binaries = [ path+'/'+binary 
                 for path in os.environ['PATH'].split(':') 
                 if os.path.exists(path+'/'+binary) ]
    if len(binaries) > 0:
        return binaries[0]
    else:
        return None 

def link_makefile_inc(conf):
    if os.path.exists('Makefile.inc'):
        os.remove('Makefile.inc')
    os.symlink('Makefile_inc/Makefile.' + conf, 'Makefile.inc')


def main(argv=sys.argv[1:]):

    home = os.getcwd()

    config_vars = dict()
    config_vars['{{HOME}}'] = home

    if which('ifort'):
        print 'Configuring for ', 'ifort'
        link_makefile_inc('ifort')
        funderscore = '_'
        config_vars['{{AMBER_ENERGY_MOD}}'] = 'amber_energy_mod_mp_'
        config_vars['{{FUNDERSCORE}}'] = funderscore
    elif which('gfortran'):
        print 'Configuring for ', 'gfortran'
        link_makefile_inc('gfortran')
        funderscore = ''
        config_vars['{{AMBER_ENERGY_MOD}}'] = '__amber_energy_mod_MOD_'
        config_vars['{{FUNDERSCORE}}'] = funderscore
    else:
        raise Exception("Could not find a fortran compiler.")

    for filename in ['Makefile.conf']:
        configure(filename, config_vars)


    print 'Successfully configured coord_util.'
    

if __name__ == "__main__":
    main()

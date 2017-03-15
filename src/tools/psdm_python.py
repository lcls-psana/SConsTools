"""
Tool which selects correct python version for PSDM releases.
"""
import os
import sys
from os.path import join as pjoin

def generate(env):

    #**************************************************
    # This module will also be used outside scons so 
    # be careful what you use in the code below 
    # see __main__ below, env may just be a dictonary, not scons env
    #**************************************************
    
    if env.get('CONDA',False):
        prefix = env['CONDA_ENV_PATH']
        version = '%d.%d' % (sys.version_info.major, 
                             sys.version_info.minor)
    else:
        prefix = pjoin(env['SIT_EXTERNAL_SW'], "python/2.7.10", env['SIT_ARCH_BASE_OPT'])
        version = "2.7"

    libdir = "lib"
    
    env['PYTHON_PREFIX'] = prefix
    env['PYTHON_VERSION'] = version
    env['PYTHON'] = "python"+version
    env['PYTHON_LIBDIRNAME'] = libdir
    env['PYTHON_INCDIR'] = pjoin(prefix, "include", env['PYTHON'])
    env['PYTHON_LIBDIR'] = pjoin(prefix, libdir)
    env['PYTHON_BINDIR'] = pjoin(prefix, "bin")
    env['PYTHON_BIN'] = pjoin(env['PYTHON_BINDIR'], env['PYTHON'])
    env['SCRIPT_SUBS']['PYTHON'] = "/usr/bin/env python"
    
    #trace ( "Initialized psdm_python tool", "psdm_python", 2 )

def exists(env):
    return True

#
# This is very special use case for this module outside scons
#
if __name__ == '__main__':
    conda = False
    conda_env_path = ''
    if 'SIT_USE_CONDA' in os.environ and str(os.environ['SIT_USE_CONDA']) != '0':
        conda = True
        conda_env_path = os.environ.get('CONDA_ENV_PATH','')
        assert len(conda_env_path) and os.path.exists(conda_env_path), \
            "SIT_USE_CONDA is true, but conda_env_path isn't set or doesn't exist"
    sit_external_sw = pjoin(os.environ['SIT_ROOT'], "sw", "external")
    sit_arch = os.environ['SIT_ARCH']
    sit_arch_split = sit_arch.split('-')
    sit_arch_os = sit_arch_split[1]
    sit_arch_base = '-'.join(sit_arch_split[:3])
    sit_arch_base_opt = sit_arch_base + '-opt'
    env = dict(SIT_ARCH=sit_arch, SIT_ARCH_OS=sit_arch_os, SIT_ARCH_BASE=sit_arch_base, 
               SIT_ARCH_BASE_OPT=sit_arch_base_opt, SIT_EXTERNAL_SW=sit_external_sw,
               CONDA=conda, CONDA_ENV_PATH=conda_env_path)
    
    generate(env)
    
    if len(sys.argv) > 1:
        for k in sys.argv[1:]:
            print env.get(k, '')
    else:
        for k, v in env.items():
            if k.startswith('PYTHON') and type(v) == str: print '%s=%s' % (k, v)

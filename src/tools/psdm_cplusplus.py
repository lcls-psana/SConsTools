"""
Tool which selects correct C++ compiler version and options for PSDM releases.
"""
import os

from SConsTools.trace import *
from SConsTools.scons_functions import *

_gcc_opt = { 'opt' : '-O3',
            'dbg' : '-g' }

_ld_opt = { 'opt' : '',
            'dbg' : '-g' }

def generate(env):
    
    os = env['SIT_ARCH_OS']
    comp = env['SIT_ARCH_COMPILER']
    opt = env['SIT_ARCH_OPT']
    
    if comp == 'gcc41' :
        env['CC'] = 'gcc'
        env['CXX'] = 'g++'
        env.Append(CCFLAGS = ' ' + _gcc_opt.get(opt,'') + ' -Wall -Wno-unknown-pragmas')
        env.Append(CXXFLAGS = ' -Wno-invalid-offsetof')
        env.Append(LINKFLAGS = ' ' + _ld_opt.get(opt,''))

    elif comp in ['gcc44', 'gcc45'] :
        env['CC'] = 'gcc'
        env['CXX'] = 'g++'
        env.Append(CCFLAGS = ' ' + _gcc_opt.get(opt,'') + ' -Wall')
        env.Append(CXXFLAGS = ' -Wno-invalid-offsetof')
        env.Append(LINKFLAGS = ' ' + _ld_opt.get(opt,''))

    elif comp == 'gcc46' :
        env['CC'] = 'gcc-4.6'
        env['CXX'] = 'g++-4.6'
        env.Append(CCFLAGS = ' ' + _gcc_opt.get(opt,'') + ' -Wall')
        env.Append(CXXFLAGS = ' -Wno-invalid-offsetof')
        env.Append(LINKFLAGS = ' ' + _ld_opt.get(opt,''))

    elif comp == 'gcc48' :
        env['CC'] = 'gcc'
        env['CXX'] = 'g++'
        env.Append(CCFLAGS = ' ' + _gcc_opt.get(opt,'') + ' -Wall')
        env.Append(CXXFLAGS = ' -Wno-invalid-offsetof -Wno-unused-local-typedefs')
        env.Append(LINKFLAGS = ' ' + _ld_opt.get(opt,'') + ' -Wl,--copy-dt-needed-entries')

    elif comp in [ 'gcc53', 'gcc52', 'gcc51']:
        env['CC'] = 'gcc'
        env['CXX'] = 'g++'
        env.Append(CCFLAGS = ' ' + _gcc_opt.get(opt,'') + ' -Wall')
        if env['CONDA']:
            # currently in conda, the boost package 1.57 is built with an older version of g++. 
            # g++ 5.3 defaults to a newer ABI. This newer ABI works its way into the templatized functions 
            # of boost_regex that psana will call. So when compiling under g++ 5.3 but linking against 
            # the conda packaged boost libraries, you get undefined errors unless you define the macro below
            env.Append(CXXFLAGS = ' -Wno-invalid-offsetof -Wno-unused-local-typedefs -D_GLIBCXX_USE_CXX11_ABI=0')
        else:
            env.Append(CXXFLAGS = ' -Wno-invalid-offsetof -Wno-unused-local-typedefs')
        env.Append(LINKFLAGS = ' ' + _ld_opt.get(opt,'') + ' -Wl,--copy-dt-needed-entries')

    
    trace ( "Initialized psdm_cplusplus tool", "psdm_cplusplus", 2 )

def exists(env):
    return True

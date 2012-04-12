#===============================================================================
#
# SConscript fuction for standard SIT package
#
# $Id$
#
#===============================================================================

import os
import sys
from pprint import *
from os.path import join as pjoin

from SCons.Defaults import *
from SCons.Script import *

from SConsTools.trace import *
from SConsTools.dependencies import *
from SConsTools.scons_functions import *


_cplusplus_ext = [ 'cc', 'cpp', 'cxx', 'C', 'c' ]
_cython_ext = [ 'pyx' ]

# normalize source file path
def _normbinsrc ( dir, f ):
    if not os.path.split(f)[0] :
        return os.path.join(dir,f)
    else :
        return f

# get list of strings from kw, single string is split
def _getkwlist ( kw, name ):
    if name in kw :
        res = kw[name]
        if isinstance(res,(str,unicode)) : res = res.split()
        return res
    return []

# get package name
def _getpkg ( kw ) :
    pkg = kw.get('package', None )
    if not pkg : pkg = os.path.basename(os.getcwd())
    return pkg
    

#
# This is the content of the standard SConscript
#
def standardSConscript( **kw ) :

    """ Understands following keywords, all optional:
        LIBS - list of additional libraries needed by this package
        LIBPATH - list of directories for additional libraries
        BINS - dictionary of executables and their corresponding source files
        TESTS - dictionary of test applications and their corresponding source files
        SCRIPTS - list of scripts in app/ directory
        UTESTS - names of the unit tests to run, if not given then all tests are unit tests
        PYEXTMOD - name of the Python extension module, package name used by default
        CCFLAGS - additional flags passed to C/C++ compilers
    """

    pkg = _getpkg ( kw )
    trace ( "Standard SConscript in `"+pkg+"'", "SConscript", 1 )

    ukw = kw.copy()
    ukw['package'] = pkg
    
    standardLib( **ukw )
    standardPyLib( **ukw )
    standardPyExt( **ukw )
    standardScripts( **ukw )
    standardBins ( **ukw )
    standardTests ( **ukw )

#
# Process src/ directory, make library from all compilable files
#
def standardLib( **kw ) :
    
    libsrcs = Flatten ( [ Glob("src/*."+ext, source=True, strings=True ) for ext in _cplusplus_ext ] )
    libsrcs.sort()
    if libsrcs :
        
        trace ( "libsrcs = "+str(map(str,libsrcs)), "SConscript", 2 )

        pkg = _getpkg( kw )
        
        env = DefaultEnvironment()
        libdir = env['LIBDIR']

        binkw = {}
        binkw['LIBS'] = _getkwlist ( kw, 'LIBS' )
        binkw['LIBPATH'] = _getkwlist ( kw, 'LIBPATH' )  + env['LIBPATH']
        if 'CCFLAGS' in kw:
            binkw['CCFLAGS'] = env['CCFLAGS'] + ' ' + kw['CCFLAGS']
        lib = env.SharedLibrary ( pkg, source=libsrcs, **binkw )
        ilib = env.Install ( libdir, source=lib )
        env['ALL_TARGETS']['LIBS'].extend ( ilib )
        
        # get the list of libraries need for this package
        libs = [pkg] + _getkwlist ( kw, 'LIBS' )
        addPkgLib ( env, pkg, lib[0] )
        addPkgLibs ( env, pkg, libs )
        
#
# Process src/ directory, link python sources
#
def standardPyLib( **kw ) :

    pysrcs = Glob("src/*.py", source=True, strings=True )
    if pysrcs :
        
        pkg = _getpkg( kw )
        
        env = DefaultEnvironment()
        pydir = env['PYDIR']

        trace ( "pysrcs = "+str(map(str,pysrcs)), "SConscript", 2 )

        # python files area installed into python/Package
        doinit = True
        for src in pysrcs :
            
            # make symlink for every .py file and compile it into .pyc
            basename = os.path.basename(src)
            if basename == "__init__.py" : doinit = False
            pydst = pjoin(pydir,pkg,basename)
            env.Symlink ( pydst, source=src )
            pyc = env.PyCompile ( pydst+"c", source=pydst )
            env['ALL_TARGETS']['LIBS'].extend ( pyc )

        if doinit :
            # make __init__.py and compile it
            ini = pjoin(pydir,pkg,"__init__.py")
            env.Command ( ini, "", [ Touch("$TARGET") ] )
            pyc = env.PyCompile ( ini+"c", source=ini )
            env['ALL_TARGETS']['LIBS'].extend ( pyc )

#
# Process pyext/ directory, build python extension module
#
def standardPyExt( **kw ) :

    env = DefaultEnvironment()
    pkg = _getpkg( kw )

    # check for Cython files first    
    cysrcs = Flatten([MyGlob("pyext/*."+ext, source=True, strings=True, recursive=True) for ext in _cython_ext])
    trace ( "cysrcs = "+str(map(str, cysrcs)), "SConscript", 2 )
    extsrcs = [env.Cython(src) for src in cysrcs]
    trace ( "pyextsrc = "+str(map(str, extsrcs)), "SConscript", 2 )

    # this glob will find *.c files produced by Cython so I don't add above files
    extsrcs = Flatten([MyGlob("pyext/*."+ext, source=True, strings=True, recursive=True) for ext in _cplusplus_ext])
    if extsrcs :
        
        trace ( "pyextsrc = "+str(map(str, extsrcs)), "SConscript", 2 )
        
        pydir = env['PYDIR']

        extmodname = kw.get('PYEXTMOD', pkg)

        objects = [env.PythonObject(src) for src in extsrcs]
        # if package builds standard library then add it to the link
        libs = env['PKG_TREE_LIB'].get(pkg, [])
        if libs: libs = [pkg]
        extmod = env.PythonExtension ( extmodname, source=objects, LIBS=libs)
        iextmod = env.Install ( pydir, source=extmod )
        env['ALL_TARGETS']['LIBS'].extend ( iextmod )
        
        # get the list of libraries need for this package
        addPkgLib ( env, pkg, extmod[0] )
        addPkgLibs ( env, pkg, [extmodname] )

#
# Process app/ directory, install all scripts
#
def standardScripts( **kw ) :
    
    env = DefaultEnvironment()
    
    targets = _standardScripts ( 'app', 'SCRIPTS', env['BINDIR'], **kw )
    env['ALL_TARGETS']['BINS'].extend( targets )

#
# Process app/ directory, build all executables from C++ sources
#
def standardBins( **kw ) :
    
    env = DefaultEnvironment()
    
    targets = _standardBins ( 'app', 'BINS', True, **kw )
    env['ALL_TARGETS']['BINS'].extend( targets )

#
# Process test/ directory, build all executables from C++ sources
#
def standardTests( **kw ) :
    
    env = DefaultEnvironment()
    #trace ( "Build env = "+pformat(env.Dictionary()), "<top>", 7 )

    # binaries in the test/ directory
    targets0 = _standardBins ( 'test', 'TESTS', False, **kw )
    env['ALL_TARGETS']['TESTS'].extend( targets0 )

    # also scripts in the tst/ directory
    targets1 = _standardScripts ( 'test', 'TEST_SCRIPTS', "", **kw )
    env['ALL_TARGETS']['TESTS'].extend( targets1 )
    
    targets = targets0 + targets1

    # make a list of unit tests
    utests = kw.get('UTESTS', None)
    if utests is None :
        utests = targets
    else :
        # filter matching targets
        utests = [ t for t in targets if os.path.basename(str(t)) in utests ]

    # make new unit test target
    trace ( "utests = "+str(map(str,utests)), "SConscript", 2 )
    for u in utests :
        t = env.UnitTest ( str(u)+'.utest', u )
        env['ALL_TARGETS']['TESTS'].extend( t )
        # dependencies for unit tests are difficult to figure out,
        # especially for Python scripts, so make them run every time
        env.AlwaysBuild(t)

#
# Build binaries, possibly install them
#
def _standardBins( appdir, binenv, install, **kw ) :

    # make list of binaries and their dependencies if it has not been passed to us
    bins = kw.get(binenv,{})
    if bins :
        for k in bins.iterkeys() :
            src = bins[k]
            if isinstance(src,(str,unicode)) : src = src.split()
            src = [ _normbinsrc(appdir,s) for s in src ]
            bins[k] = src
    else :
        cpps = Flatten ( [ Glob(appdir+"/*."+ext, source=True, strings=True ) for ext in _cplusplus_ext ] )
        for f in cpps :
            bin = os.path.splitext(os.path.basename(f))[0]
            bins[bin] = [ f ]
            
    # make rules for the binaries
    targets = []
    if bins :

        trace ( "bins = "+str(map(str,bins)), "SConscript", 2 )

        env = DefaultEnvironment()
        bindir = env['BINDIR']
        
        # Program options
        binkw = {}
        binkw['LIBS'] = _getkwlist ( kw, 'LIBS' )
        #binkw['LIBS'].insert ( 0, _getpkg( kw ) )
        binkw['LIBPATH'] = _getkwlist ( kw, 'LIBPATH' )  + env['LIBPATH']
        if 'CCFLAGS' in kw:
            binkw['CCFLAGS'] = env['CCFLAGS'] + ' ' + kw['CCFLAGS']
    
        for bin, srcs in bins.iteritems() :
            
            b = env.Program( bin, source=srcs, **binkw )
            setPkgBins ( env, kw['package'], b[0] )
            if install : 
                b = env.Install ( bindir, source=b )
                
            targets.extend( b )
            
    return targets

#
# Process app/ directory, install all scripts
#
def _standardScripts( appdir, binenv, installdir, **kw ) :

    scripts = kw.get(binenv,None)
    if scripts is None :
        # grab any file without extension in app/ directory
        scripts = Glob(appdir+"/*", source=True, strings=True )
        scripts = [ ( f, str(Entry(f)) ) for f in scripts ]
        scripts = [ s[0] for s in scripts if not os.path.splitext(s[1])[1] and os.path.isfile(s[1]) ]
    else :
        scripts = [ _normbinsrc(appdir,s) for s in scripts ]

    env = DefaultEnvironment()

    trace ( "scripts = "+str(map(str,scripts)), "SConscript", 2 )

    # Scripts are installed in 'installdir' directory
    targets = []
    for s in scripts : 
        dst = pjoin(installdir,os.path.basename(s))
        trace ( "install script = "+dst, "SConscript", 2 )
        script = env.ScriptInstall(dst, s)
        targets.extend ( script )

    return targets

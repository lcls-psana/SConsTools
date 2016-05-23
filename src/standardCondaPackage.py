#===============================================================================
#
# SConscript function for standard conda package 
#
# $Id$
#
#===============================================================================

import os
import sys
import types
from os.path import join as pjoin
from fnmatch import fnmatch

from SCons.Defaults import *
from SCons.Script import *

from SConsTools.trace import *
from SConsTools.dependencies import *

from scons_functions import fail, warning
from CondaMeta import CondaMeta
from standardExternalPackage import standardExternalPackage

#
# This is an interface package to conda packages. We find the include
# and libs in the conda package that we should make the release aware of
# for compiling and linking.
#

def condaPackageExists(pkg):
    env = DefaultEnvironment()
    cm = condaMeta(pkg, mustExist=False)
    return cm.exists

def _as_list_strings(arg):
    if isinstance(arg,list): return arg
    if arg is None: return []
    return arg.split()

def standardCondaPackage(pkg, **kw) :
    """ Creates a external package from a conda package.
        INCDIR  - include come from entire subdir, link whole subdir
        INCLUDES - specific list of includes to copy (space-separated list of patterns)
                   defaults to all in conda-meta, set to [] for no includes
        COPYLIBS - library names to copy, deafults to none
        LINKLIBS - library names to link, 
                    defaults to all dynlibs in conda meta
        REQUIRED_PKGLIBS - libraries that must be linked to when using this package
                           defaults to all package names in dynlibs of conda meta
        EXPECTED_PKGLIBS - warn if these packages not in conda meta, if exist, then
                           add pkglib list (add to link line for clients of this package)
        DEPS     - names of other packages that we depend upon
        DOCGEN   - if this is is a string or list of strings then it should be name(s) of document 
                   generators, otherwise it is a dict with generator name as key and a list of 
                   file/directory names as values (may also be a string).

        returns PREFIX for conda package (the conda env)
    """
    condaMeta = CondaMeta(pkg)
    PREFIX = condaMeta.prefix()
    trace("standardCondaPackage pkg=%s prefix=%s" % (pkg, PREFIX), "SConscript", 1)
    INCDIR = kw.get('INCDIR', None)
    INCLUDES = kw.get('INCLUDES', None)
    if (not INCDIR) and (not INCLUDES):
        includes = condaMeta.includes()
        commonprefix = os.path.commonprefix(includes).split(os.path.sep)[0]
        if commonprefix:
            INCDIR = os.path.join('include',commonprefix)
            trace("  pkg=%s auto setting INCDIR=%s" % 
                  (pkg, INCDIR), "SConscript", 2)
        else:
            INCLUDES = includes
            trace("  pkg=%s auto setting INCLUDES to list of %d files" % 
                  (pkg, len(INCLUDES)), "SConscript", 2)
    else:
        trace("  one of INCDIR or INCLUDES specified", "SConscript", 2)

    COPYLIBS = kw.get('COPYLIBS',None)
    LINKLIBS = kw.get('LINKLIBS',None)
    
    if (not COPYLIBS) and (not LINKLIBS):
        LINKLIBS = condaMeta.dynlibs()
        trace("  pkg=%s auto setting LINKLIBS to list of %d files" % 
              (pkg,len(LINKLIBS)), "SConscript", 2)

    PKGLIBS = _as_list_strings(kw.get('REQUIRED_PKGLIBS', None))
    if not PKGLIBS:
        PKGLIBS = condaMeta.pkglibs()

    EXPECTED_PKGLIBS = _as_list_strings(kw.get('EXPECTED_PKGLIBS', None))
    if EXPECTED_PKGLIBS:
        metaPkgs = set(condaMeta.pkglibs())
        for exppkg in EXPECTED_PKGLIBS:
            if exppkg in metaPkgs and exppkg not in PKGLIBS:
                PKGLIBS.append(exppkg)
            else:
                warn("expected pkglib=%s not found in conda meta for pkg=%s" % \
                     (exppkg, pkg))

    DEPS = kw.get('DEPS',None)
    DOCGEN = kw.get('DOCGEN',None)

    standardExternalPackage(pkg, **locals())
    return PREFIX

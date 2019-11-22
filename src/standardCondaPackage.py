#===============================================================================
#
# SConscript function for standard conda package 
#
# $Id$
#
#===============================================================================

import os
import sys
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

class _NoArg(object):
    def __init__(self):
        pass
_noArg = _NoArg()

def _as_list_strings_or_none(arg):
    if arg is None: return None
    if isinstance(arg,list): return arg
    return arg.split()

def _filter_includes(includes, pkg):
    filtered = []
    for incfile in includes:
        if incfile.startswith('include' + os.path.sep):
            filtered.append(incfile[8:])
        else:
            trace('filtereing out file %s for pkg %s' % (incfile, pkg), 
                  'SConscript', 3)
    return filtered

def _commonDirectory(filenames):
    commonprefix = os.path.commonprefix(filenames)
    if commonprefix.endswith(os.path.sep):
        return commonprefix[0:-1]
        
    # all the file basenames start with the same thing (like 'H5_') 
    # strip that off to find the common directory
    flds = commonprefix.split(os.path.sep)
    flds=flds[0:-1]
    return os.path.sep.join(flds)

def _file_depth(fname):
    return len(fname.split(os.path.sep))

def standardCondaPackage(pkg, **kw) :
    """ Creates a external package for the SConsTools build system from a conda package. 
    The external package can have includes and libraries, but no binaries or
    Python - those come from the conda environment.

    By default, reads the conda meta for the package to identify the includes (.h
    files), dynamic libries, and dependencies. The include files will be added to 
    the release through the geninc mechanism, while the libraries and dependencies will
    be maintained in the sconstools build information.

        INCDIR  - directly specify include dir relative to conda env prefix - 
                  for example 'include/boost' 
        INCLUDES - directly specify list of includes to copy (space-separated list of patterns)
                   relative to INCDIR (if given) or relative to conda env prefix)
                   These includes must be shallow, i.e, only file in INCDIR are links, not
                   files in subdirs
        INCLUDE_EXTS - if neither INCDIR or INCLUDES is specified, all conda meta files
                       with these extensions are used (defaults to .h)
        COPYLIBS - library names to copy, deafults to none
        LINKLIBS - library names to link, defaults to all dynlibs in conda meta, set to 
                   None for no lib linking
        REQUIRED_PKGLIBS - libraries that must be linked to when using this package.
                           defaults to all package names in dynlibs of conda meta
        EXPECTED_PKGLIBS - libraries that we expect to be present and should be linked
                           to when using this package. However if they are not present,
                           emit a warning.
        DEPS     - names of other packages that we depend upon, if not specified, will look
                   at condaMeta to identify dependencies. Set to None to explicity do no
                   dependencies.
        DOCGEN   - if this is is a string or list of strings then it should be name(s) of document 
                   generators, otherwise it is a dict with generator name as key and a list of 
                   file/directory names as values (may also be a string).
    """
    condaMeta = CondaMeta(pkg)
    PREFIX = condaMeta.prefix()
    trace("standardCondaPackage pkg=%s prefix=%s" % (pkg, PREFIX), "SConscript", 1)
    incdir = kw.get('INCDIR', _noArg)
    includes = kw.get('INCLUDES', _noArg)
    
    if (incdir is _noArg) and (includes is _noArg):
        include_exts = _as_list_strings_or_none(kw.get('INCLUDE_EXTS', ['.h']))
        include_subdir = 'include'
        includes = condaMeta.includes(extensions=include_exts, subdirs=[include_subdir])
        
        trace("standardCondaPackage pkg=%s auto includes - %d files" % 
              (pkg, len(includes)), "SConscript", 1)
        if includes:
            commondir = _commonDirectory(includes)
            dirlist = commondir.split(os.path.sep)

            # now we decide if we want to link a directory in the sconstools release, or
            # link a set of files. If we see that all includes are in a directory, we 
            # will link it. However they may all be in a top level conda directory like
            # include. We don't want that. We want a depth of at least two to all the
            # includes, and we want the package name in the path.
            if len(dirlist)>1 and pkg in dirlist:
                INCDIR = commondir
                trace("  pkg=%s auto setting INCDIR=%s" % (pkg, INCDIR), "SConscript", 2)                
            else:
                trace("  pkg=%s header files under 'include' subdir not in common dir" % 
                      (pkg,), "SConscript", 2)
                INCDIR = include_subdir
                INCLUDES = [os.path.split(fname)[1] for fname in includes if _file_depth(fname)==1]
                trace("  pkg=%s auto setting INCLUDES to list of %d files and INCDIR=%s" % 
                      (pkg, len(INCLUDES), INCDIR), "SConscript", 2)
    else:
        trace("  pkg=%s one of INCDIR or INCLUDES specified" % pkg, "SConscript", 2)
        if includes is not _noArg:
            INCLUDES = kw['INCLUDES']
        if incdir is not _noArg:
            INCDIR = kw['INCDIR']
            assert len(INCDIR)>0 and INCDIR[0] != os.path.sep, "use relative paths for conda"

    copylibs = kw.get('COPYLIBS',_noArg)
    linklibs = kw.get('LINKLIBS',_noArg)
    
    if (copylibs is _noArg) and (linklibs is _noArg):
        LINKLIBS = condaMeta.dynlibs()
        trace("  pkg=%s auto setting LINKLIBS to list of %d files" % 
              (pkg,len(LINKLIBS)), "SConscript", 2)

    metaPkgs = condaMeta.pkglibs()
    pkglibs = False
    if kw.get('REQUIRED_PKGLIBS', _noArg) is _noArg:
        PKGLIBS = metaPkgs
        pkglibs = True
    else:
        required_pkglibs = _as_list_strings_or_none(kw['REQUIRED_PKGLIBS'])
        if required_pkglibs:
            PKGLIBS = required_pkglibs
            pkglibs = True

    pkgs_to_add_if_present = _as_list_strings_or_none(kw.get('EXPECTED_PKGLIBS', None))
    if pkgs_to_add_if_present:
        for pkg_to_add in pkgs_to_add_if_present:
            if pkglibs and pkg_to_add in PKGLIBS:
                continue
            if pkg_to_add in metaPkgs:
                if not pkglibs:
                    PKGLIBS=[pkg_to_add]
                    pkglibs = True
                else:
                    PKGLIBS.append(pkg_to_add)
            else:
                warning("expected pkglib=%s not found in conda meta for pkg=%s" % \
                        (pkg_to_add, pkg))

    if kw.get('DEPS', _noArg) is not _noArg:
        DEPS = kw['DEPS']
    else:
        DEPS = condaMeta.package_dependencies()

    if kw.get('DOCGEN', _noArg) is not _noArg:
        DOCGEN = kw['DOCGEN']

    standardExternalPackage(pkg, **locals())

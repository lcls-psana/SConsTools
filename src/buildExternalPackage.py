#===============================================================================
#
# SConscript function to build external package
#
# $Id$
#
#===============================================================================

import os
import sys
import types
from os.path import join as pjoin

from SCons.Defaults import *

from SConsTools.trace import *

from scons_functions import fail, warning

def prefixForBuildExternal(pkg):
    ## should be a way to use scons env, to form this path instead of
    ## getting release dirbut how does ${ARCHDIR} get expanded? I think 
    ## have to switch to installing with scons 
    env = DefaultEnvironment()
    orig_dir = os.path.abspath(os.curdir)
    release_dir = os.path.split(orig_dir)[0]
    prefix = pjoin(release_dir, 'arch', env['SIT_ARCH'], 'extpkgs', pkg)
    return prefix

def buildExternalPackage(pkg, buildcmds, PREFIX, startdir='pkg'):
    assert startdir in ['pkg', 'parent']
    env = DefaultEnvironment()
    assert env.get('CONDA',False), "not conda build"
    orig_dir = os.path.abspath(os.curdir)
    release_dir = os.path.split(orig_dir)[0]
    extpkgs_dir = pjoin(release_dir, 'extpkgs')
    assert os.path.exists(extpkgs_dir), "No extpkgs dir in release."
    srcpkgdir = pjoin(extpkgs_dir, pkg)
    assert os.path.exists(srcpkgdir), \
        "The source package: %s for this proxy package is not in the release" % pkg
    if startdir == 'pkg':
        os.chdir(srcpkgdir)
    else:
        os.chdir(extpkgs_dir)

    for cmd in buildcmds:
        print cmd
        assert 0 == os.system(cmd)

    os.chdir(orig_dir)


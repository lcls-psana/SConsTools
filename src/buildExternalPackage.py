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
    # hack, should be way to do this within scons
    env = DefaultEnvironment()
    orig_dir = os.path.abspath(os.curdir)
    release_dir = os.path.split(orig_dir)[0]
    prefix = pjoin(release_dir, 'arch', env['SIT_ARCH'], 'extpkgs', pkg)
    return prefix

def buildExternalPackage(pkg, buildcmds, PREFIX, ONE_TARGET,
                         startdir='pkg'):
    assert startdir in ['pkg', 'parent']
    env = DefaultEnvironment()
    assert env.get('CONDA',False), "not conda build"
    if env['SKIP_BUILD_EXT']: 
        return
    orig_dir = os.path.abspath(os.curdir)
    release_dir = os.path.split(orig_dir)[0]
    extpkgs_dir = pjoin(release_dir, 'extpkgs')
    assert os.path.exists(extpkgs_dir), "No extpkgs dir in release."
    one_target = os.path.join(PREFIX, ONE_TARGET)
    if os.path.exists(one_target):
        warning("skipping build of %s. remove %s to rebuild" % (pkg, one_target))
        return
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


#===============================================================================
#
# $Id$
#
#===============================================================================

import os
import sys
import json
from glob import glob
from os.path import join as pjoin

from trace import *

from SCons.Defaults import *
from SCons.Script import *
from SConsTools.trace import *
from SConsTools.scons_functions import warning, fail

def condaPackageExists(pkg):
    env = DefaultEnvironment()
    cm = CondaMeta(pkg, mustExist=False)
    return cm.exists

def _expected_dir_for_includes(dirname):
    if dirname in ['include','lib']:
        return True
    return False

class CondaMeta(object):
    def __init__(self, pkg, mustExist=True):
        '''gather meta information about a package in conda.

        Looks for the package .json file in the conda-meta directory.
        Default is to fail the build if it is not present, otherwise
        (if mustExists=False) the attribute .exists can be checked

        provides access to includes, libs, and pkg libs.

        ARGS: 

           pkg:  the package name
           mustExist - call scons Fail is package not in conda
        '''
        self.env = DefaultEnvironment()
        if not self.env['CONDA']:
            fail("must have a conda based build environment - pkg=%s" % pkg)
        self.pkg = pkg
        metadir = pjoin(self.env['CONDA_ENV_PATH'], 'conda-meta')
        if not os.path.exists(metadir):
            fail("metadir=%s doesn't exist" % metadir)

        matches = []
        for cand in glob(pjoin(metadir, '%s-*.json'%pkg)):
            pkgMeta = json.load(file(cand,'r'))
            if pkgMeta['name'] == pkg:
                matches.append((pkgMeta['version'], pkgMeta))

        if len(matches)==0:
            if mustExist:
                fail("No json file found for pkg=%s in cond env=%s" % (pkg, self.env['CONDA_ENV_PATH']))
                return
            else:
                self.exists = False
                return

        self.exists = True
        if len(matches)==1:
            self.pkgMeta = matches[0][1]
            return

        warning("several versions for package=%s versions=%s will use last from lexical sort" %
                (pkg, ','.join([m[0] for m in matches])))
        matches.sort()
        self.pkgMeta = matches[-1][1]

    def includes(self, extensions=['.h']):
        assert self.exists
        files = []
        for fname in self.pkgMeta['files']:
            rootdir = fname.split(os.path.sep)[0]
            if _expected_dir_for_includes(rootdir):
                ext = os.path.splitext(fname)[1]
                if ext in extensions:
                        files.append(fname)
            else:
                trace(("includes - skipping %s, doesn't look "
                       "like it should be an include") % fname, 'CondaMeta', 3)

        return files

    def prefix(self):
        return self.env['CONDA_ENV_PATH']

    def dynlibs(self):
        assert self.exists
        libFiles = self._getFilesInSubDir('lib')

        # filter out files not in the top 'lib' dir
        libFiles = [lib for lib in libFiles if os.path.dirname(lib)=='']

        # filter out files that don't start with lib
        libFiles = [lib for lib in libFiles if lib.startswith('lib')]

        # select shared objects
        ## todo - change for mac/win?
        libFiles = [lib for lib in libFiles if \
                    (lib.endswith('.so') or lib.find('.so.') >0) ]

        return libFiles
    
    def staticlibs(self):
        assert self.exists
        libFiles = self._getFilesInSubDir('lib')

        # filter out files not in the top 'lib' dir
        libFiles = [lib for lib in libFiles if os.path.dirname(lib)=='']

        # filter out files that don't start with lib
        libFiles = [lib for lib in libFiles if lib.startswith('lib')]

        # select static libs
        ## todo - change for mac/win?
        libFiles = [lib for lib in libFiles if lib.endswith('.a')]
        return libFiles

    def pkglibs(self):
        libs = self.dynlibs()
        libs = [lib for lib in libs if lib.startswith('lib')]
        libs = [lib for lib in libs if lib.endswith('.so')]
        pkgs = [lib[3:-3] for lib in libs]
        return pkgs

    def _getFilesInSubDir(self, subdir):
        files = []
        nn = len(subdir)+1
        for fname in self.pkgMeta['files']:
            if fname.startswith(subdir + os.path.sep):
                files.append(fname[nn:])
        return files

        

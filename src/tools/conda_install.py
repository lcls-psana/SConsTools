"""SCons.Tool.conda_install

Tool-specific initialization for conda_install builder.

AUTHORS:
 - David Schneider

"""

import os
from os.path import join as pjoin
import shutil

import SCons
from SCons.Builder import Builder
from SCons.Action import Action

from SConsTools.trace import *
from SConsTools.scons_functions import *


def _fmtList(lst):
    return '[' + ','.join(map(str, lst)) + ']'

def copytree(src, dest):
    def ignore(src, names):
        # I think these files were only there because I was doing development with
        # emacs, probably don't need ignore function
        return [nm for nm in names if nm.startswith('#') or nm.startswith('.#')]

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dest, item)
        if os.path.islink(s):
            s_real = os.path.realpath(s)
            print "  src -> %s" % s_real
            if (s_real == os.path.realpath(d)):
                print "  skipping src=%s, it is a soft link to conda file=%s" % (src, s_real)
                continue
        if os.path.isdir(s):
#            if os.path.exists(d): 
#                print "d exists, skipping"
#                continue
            print "  about to do copytree on src directory=%s" % s
            shutil.copytree(s, d, False, ignore)
        else:
            print "  copying file src=%s to dest=%s" % (s,d)
            shutil.copy2(s,d)

class _makeCondaInstall:

    def __call__(self, target, source, env) :
        """Target should be a single file, no source is needed"""
        if len(target) != 1 : fail("unexpected number of targets for CondaInstall: " + str(target))
        if len(source) != 0 : fail("unexpected number of sources for Condanstall: " + str(source))

        condaPrefix = str(target[0])
        trace("Executing CondaInstall: dest=%s" % condaPrefix, "makeCondaInstall", 3)
        if not os.path.exists(condaPrefix): fail("condaInstall - destdir %s doesn't exist, it should be the _build conda environment" % condaPrefix)
        condaBin = os.path.join(condaPrefix, 'bin')
        if not os.path.exists(condaBin): fail("condaInstall - destdir %s does not have a 'bin' subdir" % destdir)
        if not os.path.exists(os.path.join(condaBin, 'python')): fail("condaInstall - there is no python executable in the 'bin' subdir to the condaPrefix=%s, it does not look like we are installing into a conda environment" % condaPrefix)

        sit_arch = env['SIT_ARCH']
        sp_dir = env.get('SP_DIR', None)  # defined by conda build
        if sp_dir is None:
            sp_dir = os.environ.get('SP_DIR', None)
        if sp_dir is None: fail('SP_DIR is defined in neither the scons env or os.environ')

        release2conda = {'include':pjoin(condaPrefix,'include'),
                         'data':pjoin(condaPrefix,'data'),
                         os.path.join('arch', sit_arch, 'lib'):pjoin(condaPrefix,'lib'),
                         os.path.join('arch', sit_arch, 'bin'):pjoin(condaPrefix,'bin'),
                         os.path.join('arch', sit_arch, 'geninc'):pjoin(condaPrefix,'include'),
                         os.path.join('arch', sit_arch, 'python'):sp_dir,
        }
        
        for releaseDir, condaDir in release2conda.iteritems():
            if not os.path.exists(releaseDir):
                fail("Release path %s does not exit" % releaseDir)
            mkdirOrFail(condaDir)
            print "conda install: copying dir %s to %s" % (releaseDir, condaDir)
            copytree(releaseDir, condaDir)

    def strfunction(self, target, source, env):
        try :
            return "conda install in " + str(target[0])
        except :
            return 'CondaInstall(' + _fmtlist(target) + ')'

def create_builder(env):
    try:
        builder = env['BUILDERS']['CondaInstall']
    except KeyError:
        builder = SCons.Builder.Builder(action=_makeCondaInstall())
        env['BUILDERS']['CondaInstall'] = builder

    return builder

def generate(env):
    """Add special Builder for installing release to a new location."""

    # Create the PythonExtension builder
    create_builder(env)

    trace("Initialized conda_install tool", "conda_install", 2)

def exists(env):
    return True

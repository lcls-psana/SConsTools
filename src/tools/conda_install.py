"""SCons.Tool.conda_install

Tool-specific initialization for conda_install builder.

AUTHORS:
 - David Schneider

"""

import os

import SCons
from SCons.Builder import Builder
from SCons.Action import Action

from SConsTools.trace import *
from SConsTools.scons_functions import *


def _fmtList(lst):
    return '[' + ','.join(map(str, lst)) + ']'

class _makeCondaInstall:

    def __call__(self, target, source, env) :
        """Target should be a single file, no source is needed"""
        if len(target) != 1 : fail("unexpected number of targets for CondaInstall: " + str(target))
        if len(source) != 0 : fail("unexpected number of sources for Condanstall: " + str(source))

        destdir = str(target[0])
        trace("Executing CondaInstall: destdir=%s" % (destdir,), "makeCondaInstall", 3)

        # destination directory must exist
        if not os.path.exists(destdir): fail("CondaInstall: destination directory does not exists: " + destdir)

        raise Exception("conda install not implemented yet")

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

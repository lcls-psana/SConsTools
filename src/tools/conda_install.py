"""SCons.Tool.conda_install

Tool-specific initialization for conda_install builder.

AUTHORS:
 - David Schneider

"""

import os
from os.path import join as pjoin
import shutil

#try:

import SCons
from SCons.Builder import Builder
from SCons.Action import Action

from SConsTools.trace import *
from SConsTools.scons_functions import *

#except ImportError:
#    print "testing mode"
#    def warning(msg):
#        print "WARNING: %s" % msg
#    def info(msg):
#        print msg

#    def trace(msg, prefix, lvl):
#        print "%s: %s" % (prefix, msg)
#    def fail(msg):
#        raise Exception(msg)
#    def mkdirOrFail ( d ) :
#        try :
#            if not os.path.isdir( d ) :
#                os.makedirs ( d )
#                trace ( "Creating directory (1) `%s'" % d, "mkdirOrFail", 1 )
#        except :
#            fail ( "Failed to create `%s' directory" % ( d, ) )


def _fmtList(lst):
    return '[' + ','.join(map(str, lst)) + ']'

                                    
def copytree(src, dest, link_prefix):
    '''For links, the target is copied as long as it has the link_prefix,
    this is to prevent trying to copy links into conda itself

    returns number of files copied
    '''
    def ignore(names):
        # I think these files were only there because I was doing development with
        # emacs, probably don't need ignore function
        return [nm for nm in names if nm.startswith('#') or nm.startswith('.#')]

    names = os.listdir(src)
    ignore_names = ignore(names)
    num_files_copied = 0

    for name in names:
        if name in ignore_names: 
            continue
        srcname = os.path.join(src, name)
        destname = os.path.join(dest, name)
        if os.path.islink(srcname):
            src_real = os.path.realpath(srcname)
            if not src_real.startswith(link_prefix):
                info("conda_install: skipping src=%s, realpath from symlink, it does not start with %s" % (src_real, link_prefix))
                continue
            srcname = src_real
        if os.path.isdir(srcname):
            mkdirOrFail(destname)
            num_files_copied += copytree(srcname, destname, link_prefix)
        else:
            shutil.copy2(srcname, destname)
            info("conda_install: copied %s -> %s" % (srcname, destname))
            num_files_copied += 1
    info("conda_install: copystat(%s,%s)" % (src, dest))
    shutil.copystat(src, dest)
    return num_files_copied

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

        # get SConstruct.main installed
        sconstruct_main = os.path.join('SConsTools','src','SConstruct.main')
        assert os.path.exists(sconstruct_main), "file doesn't exist: %s" % sconstruct_main
        shutil.copy2(sconstruct_main, os.path.join('arch', sit_arch, 'python', 'SConsTools', 'SConstruct.main'))
        
        release2conda = {'include':pjoin(condaPrefix,'include'),
                         'data':pjoin(condaPrefix,'data'),
                         'web':pjoin(condaPrefix, 'web'),
                         os.path.join('arch', sit_arch, 'lib'):pjoin(condaPrefix,'lib'),
                         os.path.join('arch', sit_arch, 'bin'):pjoin(condaPrefix,'bin'),
                         os.path.join('arch', sit_arch, 'geninc'):pjoin(condaPrefix,'include'),
                         os.path.join('arch', sit_arch, 'python'):sp_dir,
        }
        
        for releaseDir, condaDir in release2conda.iteritems():
            if not os.path.exists(releaseDir):
                warning("Release path %s does not exist, will not install from it" % releaseDir)
                continue
            mkdirOrFail(condaDir)
            info("conda install: copying dir %s to %s" % (releaseDir, condaDir))
            copytree(releaseDir, condaDir, link_prefix=os.path.realpath('.'))


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

#if __name__ == '__main__':
#    print "testing conda_install"
#    condaInstall = _makeCondaInstall()
#    os.environ['SP_DIR'] = os.path.join(os.environ['CONDA_PREFIX'], 'lib', 'python2.7', 'site-packages')
#    condaInstall([os.environ['CONDA_PREFIX']], [], os.environ)

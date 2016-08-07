"""SCons.Tool.conda_install

Tool-specific initialization for conda_install builder.

AUTHORS:
 - David Schneider

"""

import os
from os.path import join as pjoin
import shutil
import py_compile

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

def generateAnaRelInfoFromPackageList(pyOutDir):
    if not os.path.exists('.sit_release'):
        warning('no .sit_release found, aborting anarel version info')
        return
    relverstr = file('.sit_release').read().strip()
    pkginfo = {}
    if not os.path.exists('psana-conda-tags'):
        warning('psana-conda-tags file not find, not adding anarel version info')
        return

    for ln in file('psana-conda-tags','r').read().split('\n'):
        ln = ln.strip()
        if len(ln)==0: continue
        flds = ln.split()
        if len(flds) not in [4,5]:
            warning('psana-conda-tags file format has changed, this line does not have 4 or 5 fields: %s' % ln)
            warning('  aborting anarel version info')
            return
        if len(flds)==5:
            jnk, tag = flds[4].split('tag=')
            pkginfo[flds[0]]=tag
        else:
            if flds[1] != 'conda_branch=True':
                warning('psana-conda-tags file format is not understood, this ln has 4 fields but doesnt specify conda_branch=True for field 1: %s' % ln )
            pkginfo[flds[0]]='conda_branch'
    assert os.path.exists(pyOutDir)
    outDir = os.path.join(pyOutDir, 'anarelinfo')
    if not os.path.exists(outDir):
        os.mkdir(outDir)
        trace("anarelinfo - made dir %s" % outDir, "condaInstall", 1)
    anarelinit = os.path.join(outDir, '__init__.py')
    fout = file(anarelinit,'w')
    fout.write("version='%s'\n" % relverstr)
    fout.write("pkgtags={  \n")
    for pkg, tagstr in pkginfo.iteritems():
        fout.write("'%s':'%s',\n" % (pkg, tagstr))
    fout.write("}\n")
    fout.close()
    py_compile.compile(anarelinit)
        
                
                    
def copytree(src, dest, link_prefix):
    '''src files that exist in the destination are ignored.
    For links, the target is copied as long as it has the link_prefix,
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
        if name in ignore_names: continue
        srcname = os.path.join(src, name)
        destname = os.path.join(dest, name)
        trace("src->dest %s -> %s" % (srcname, destname), "condaInstall", 3)
        if os.path.islink(srcname):
            src_real = os.path.realpath(srcname)
            if not src_real.startswith(link_prefix):
                trace("Skipping symlink %s, realpath=%s, does not start with %s" % (srcname, src_real, link_prefix), "condaInstall", 0)
                continue
            trace("copying src=%s, it is a symlink to a file within the release" % srcname, "condaInstall", 0)
            srcname = src_real
        if os.path.isdir(srcname):
            mkdirOrFail(destname)
            num_files_copied += copytree(srcname, destname, link_prefix)
        else:
            if os.path.exists(destname):
                warning("condaInstall: dest file exists, skipping, %s" % destname)
            else:
                trace("copy2(%s,%s)" % (srcname, destname), "condaInstall", 3)
                shutil.copy2(srcname, destname)
                num_files_copied += 1
    trace("copystat(%s,%s)" % (src, dest), "condaInstall", 0)
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

        generateAnaRelInfoFromPackageList(os.path.join('arch', sit_arch, 'python'))

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

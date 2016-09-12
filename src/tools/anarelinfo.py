import os
import sys
import py_compile
import shutil

def warning(msg):
    sys.stderr.write("%s\n" % msg)

def info(msg):
    sys.stdout.write("%s\n" % msg)

def copyDependenciesFile():
    if not os.path.exists('data'):
        os.mkdir('data')
    os.chdir('data')
    if not os.path.exists('anarelinfo'):
        os.mkdir('anarelinfo')
    os.chdir('..')
    PKG_TREE_FILE = '.pkg_tree.pkl'
    if not os.path.exists(PKG_TREE_FILE):
        warning("%s file not found, no dependencies copied over" % PKG_TREE_FILE)
        return
    src = PKG_TREE_FILE
    dest = os.path.join('data', 'anarelinfo', PKG_TREE_FILE)
    shutil.copy2(src, dest)
    info("copied %s -> %s" % (src, dest))
        
def generateAnaRelInfoFromPackageList():
    pyOutDir = os.path.join('arch', '$SIT_ARCH', 'python')
    pyOutDir = os.path.expandvars(pyOutDir)
    if not os.path.exists('.sit_release'):
        warning("no .sit_release found, aborting anarel version info")
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
    assert os.path.exists(pyOutDir), "output dir for anarelinfo doesn't exist: %s" % pyOutDir
    outDir = os.path.join(pyOutDir, 'anarelinfo')
    if not os.path.exists(outDir):
        os.mkdir(outDir)
        info("anarelinfo - made dir %s" % outDir)
    anarelinit = os.path.join(outDir, '__init__.py')
    fout = file(anarelinit,'w')
    fout.write("version='%s'\n" % relverstr)
    fout.write("pkgtags={  \n")
    for pkg, tagstr in pkginfo.iteritems():
        fout.write("'%s':'%s',\n" % (pkg, tagstr))
    fout.write("}\n")
    fout.close()
    info("wrote %s" % anarelinit)
    py_compile.compile(anarelinit)
        
if __name__ == '__main__':    
    generateAnaRelInfoFromPackageList()
    copyDependenciesFile()
    

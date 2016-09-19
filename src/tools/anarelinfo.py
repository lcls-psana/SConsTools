import os
import sys
import py_compile
import shutil

def warning(msg):
    sys.stderr.write("%s\n" % msg)

def info(msg):
    sys.stdout.write("%s\n" % msg)

def copyDependenciesFile(dataDir):
    PKG_TREE_FILE = '.pkg_tree.pkl'
    if not os.path.exists(PKG_TREE_FILE):
        warning("%s file not found, no dependencies copied over" % PKG_TREE_FILE)
        return
    src = PKG_TREE_FILE
    dest = os.path.join(dataDir, PKG_TREE_FILE)
    shutil.copy2(src, dest)
    info("copied %s -> %s" % (src, dest))
        
# lines in psana-conda-tags should look like this:
# RegDB                                  conda_branch=False                      repo=psdm                     subdir=None                        tag=V00-03-07      
# SConsTools                             conda_branch=True                       repo=psdm                     subdir=None           
# note - 4 or 5 fields
def parsePackageInfo():
    pkginfo = {}
    if not os.path.exists('psana-conda-tags'):
        warning('psana-conda-tags file not find.')
        return None

    for ln in file('psana-conda-tags','r').read().split('\n'):
        ln = ln.strip()
        if len(ln)==0: continue
        flds = ln.split()
        if len(ln)<1: 
            warning("unexpected error, ln=%s has no fields?")
            return None
        pkg = flds[0]
        if len(flds) not in [4,5]:
            warning('psana-conda-tags file format has changed, this line does not have 4 or 5 fields: %s' % ln)
            return None
        conda_branch, repo, subdir = flds[1:4]
        if len(flds)==5:
            taginfo = flds[4]
            tag = taginfo.split('tag=')[1]
            pkginfo[pkg]=tag
        else:
            if conda_branch != 'conda_branch=True':
                warning('psana-conda-tags file format is not understood, this ln has 4 fields, meaning no tag and it should come from the conda branch, but the ln=%s' % ln)
                return None
            pkginfo[pkg]='conda_branch'
    return pkginfo

def mkPkgTree(pkgname):
    if os.path.exists(pkgname):
        warning("output directory: %s exists, removing" % pkgname)
        shutil.rmtree(pkgname)

    os.mkdir(pkgname)
    info("anarelinfo - made dir %s" % pkgname)
    srcDir = os.path.join(pkgname, 'src')
    dataDir = os.path.join(pkgname, 'data')
    os.mkdir(srcDir)
    os.mkdir(dataDir)
    info("anarelinfo - made src dir %s" % srcDir)
    info("anarelinfo - made data dir %s" % dataDir)
    return pkgname, srcDir, dataDir

def generateAnaRelInfoFromPackageList(pkgname='anarelinfo'):
    ####### helper
    def writeFile(fname, txt):
        fout = file(fname,'w')
        fout.write(txt)
        fout.close()
        info("wrote %s" % fname)

    #########
    if not os.path.exists('.sit_release'):
        warning(".sit_release file doesn't exist, aborting.")
        return False

    relverstr = file('.sit_release').read().strip()

    pkginfo = parsePackageInfo()
    if pkginfo is None:
        warning("parsePackageInfo returned None - anarelinfo aborting")
        return False

    pkgDir, srcDir, dataDir = mkPkgTree(pkgname)

    writeFile(os.path.join(pkgDir, 'SConscript'), "Import('*')\nstandardSConscript()\n")
    init_dot_py = "version='%s'\n" % relverstr
    init_dot_py += "pkgtags={  \n"
    for pkg, tagstr in pkginfo.iteritems():
        init_dot_py += "  '%s':'%s',\n" % (pkg, tagstr)
    init_dot_py += "}\n"
    init_dot_py_fname = os.path.join(srcDir, '__init__.py') 
    writeFile(init_dot_py_fname, init_dot_py)
    py_compile.compile(init_dot_py_fname)
    copyDependenciesFile(dataDir)

if __name__ == '__main__':    
    generateAnaRelInfoFromPackageList()
    

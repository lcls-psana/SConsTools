"""
Tool supporting Qt5.
"""
import os
from SCons.Builder import Builder
from SCons.Action import Action

from SConsTools.trace import *
from SConsTools.scons_functions import *

# Qt5 directory location relative to SIT_ROOT
qt_dir = "sw/external/qt"

def _qtdir(env):
    if env['CONDA']:
        return env['CONDA_ENV_PATH']
    raise Exception("conda only now!")

mocAction = Action("$QT5_MOCCOM")

def create_builder(env):
    try:
        moc = env['BUILDERS']['Moc']
    except KeyError:
        moc = Builder( action = mocAction,
                  emitter = {},
                  suffix = ".cpp",
                  single_source = 1)
        env['BUILDERS']['Moc'] = moc

    return moc

def generate(env):
    qtdir = _qtdir(env)
    if not qtdir: fail("Cannot determine QTDIR")

    # extend CPPPATH
    p = os.path.join(qtdir, 'include', 'qt')
    incdirs = [p, pjoin(p, 'QtCore'), pjoin(p, 'QtGui'), pjoin(p, 'QtWidgets')] # QtWidgets for qt5

    # set env
    env["QTDIR"] = qtdir
    assert env["CONDA"]
    env["QT5_PREFIX"] = env["CONDA_ENV_PATH"]
    env["QT5_MOC"] = "$QTDIR/bin/moc"
    env["QT5_MOCCOM"] = "$QT5_MOC $QT5_MOCFLAGS -o $TARGET $SOURCE"
    env["QT5_MOCFLAGS"] = ""
    env["QT5_LIBS"] = ["Qt5Gui", "Qt5Core", "Qt5Widgets"]
    env["QT5_LIBDIR"] = os.path.join(qtdir, "lib")
    env["QT5_INCDIRS"] = incdirs
    env.Append(CPPPATH = incdirs)

    create_builder(env)

    trace ( "Initialized qt5 tool", "qt5", 2 )

def exists(env):
    return _qtdir(env) is not None

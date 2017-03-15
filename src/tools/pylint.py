"""
Tool to run pylint on python files

"""

import os
from  os.path import join as pjoin
import SCons
from SCons.Builder import Builder
from SCons.Action import Action
from SConsTools.trace import *


def strfunction(target, source, env):
    return "pylint {}".format(source[0])

if trace_level == 0:
    pylintAction = Action("$PYLINTCOM", strfunction=strfunction)
else:
    pylintAction = Action("$PYLINTCOM")

def create_builder(env):
    try:
        pylint = env['BUILDERS']['Pylint']
    except KeyError:
        pylint = SCons.Builder.Builder(
                  action = pylintAction,
                  single_source = 1)
        env['BUILDERS']['Pylint'] = pylint

    return pylint

def generate(env):
    
    if env['CONDA']:
        pylintbin = pjoin(env['CONDA_ENV_PATH'], 'bin', 'pylint')
        pypath = pjoin(env['CONDA_ENV_PATH'], 'lib', '$PYTHON', 'site-packages')
    else:
        pyextra = "$SIT_EXTERNAL_SW/pyextra-$PYTHON/$SIT_ARCH_BASE_OPT"
        pypath = pjoin(pyextra , "/lib/$PYTHON/site-packages")
        pylintbin = pyextra + '/bin/pylint'

    env["PYLINT"] = pylintbin
    pypath = os.environ['PYTHONPATH'] + ':' + pypath
    env["PYLINTCOM"] = "PYTHONPATH=" + pypath + " $PYLINT --rcfile=/dev/null --persistent=n -e $SOURCE"

    create_builder(env)

def exists(env):
    try:
#        import Cython
        return True
    except ImportError:
        return False

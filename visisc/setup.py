# Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
#
# Main author: Tomas Olsson <tol@sics.se>
#
# License: BSD 3 clause

import os
import sys
from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib;

from numpy.distutils.misc_util import get_numpy_include_dirs


numpyincdir = get_numpy_include_dirs()

extra_flags = []

visisc_dir = '_visisc_modules'


py_modules = [os.path.join(visisc_dir, mod) for mod in ["__init__", "EventVisualization", "EventDataModel", "EventDataObject", "EventHierarchy", "EventSelectionDialog", "EventSelectionQuery"]]+["visisc"]

pylib = get_python_lib()


# Must be updated if file structure changed

if "uninstall" in sys.argv:

    from glob import glob
    files = [os.path.join(pylib, mod)+".py" for mod in py_modules] + \
            [os.path.join(pylib, mod)+".pyc" for mod in py_modules] + \
            [os.path.join(pylib,visisc_dir)] + \
            [os.path.join(pylib, "pyisc-1.0-py2.7.egg-info")] + \
            glob(os.path.os.path.join(pylib, "_visisc.*"))

    for file in files:
        if os.path.exists(file):
            if os.path.isdir(file):
                os.removedirs(file)
            else:
                os.remove(file)
            print "removing "+file
    sys.exit()

isc_src_dir = os.path.join('..',os.path.join('pyisc','isc2'))
dataformat_src_dir = os.path.join('..',os.path.join('pyisc','dataformat'))
pyisc_src_dir = os.path.join('..', os.path.join('pyisc','src'))

if sys.platform  == 'darwin':
    extra_flags = ["-DPLATFORM_MAC"]
elif sys.platform == "win32":
    extra_flags = ["-DPLATFORM_MSW"]
else: # Default, works for Linux
    extra_flags = ["-Wmissing-declarations","-DUSE_WCHAR -DPLATFORM_GTK"]



setup(name="visISC",
      author="Tomas Olsson",
      author_email="tol@sics.se",
      url="http://www.sics.se",
      version="1.0",
      ext_modules=[
          Extension("_visisc",
                    sources=[os.path.join('src',"EventDataModel.cc"), "visisc.i"],
                    include_dirs=[pyisc_src_dir, isc_src_dir, dataformat_src_dir, numpyincdir, 'src', '..'],
                    extra_compile_args=extra_flags,
                    swig_opts=['-c++']),
      ],
      )

# The following overlapping setup is only run in order to inlcude pyisc.py when all *.py files are copied to the same folder.

setup(name="visISC",
      author="Tomas Olsson",
      author_email="tol@sics.se",
      url="http://www.sics.se",
      version="1.0",
      ext_modules=[
          Extension("_visisc",
                    sources=[os.path.join('src',"EventDataModel.cc"),"visisc.i"],
                    include_dirs=[pyisc_src_dir, isc_src_dir,dataformat_src_dir, numpyincdir, 'src', '..'],
                    extra_compile_args=extra_flags,
                    swig_opts=['-c++'])
      ],
      py_modules=py_modules
      )



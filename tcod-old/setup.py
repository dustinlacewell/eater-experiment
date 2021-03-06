from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules=[
    Extension("galife", 
        ["galife.pyx"],
	extra_compile_args=["-w"]),
]

setup(
  name = "galife",
  cmdclass = {"build_ext": build_ext},
  ext_modules = ext_modules
)

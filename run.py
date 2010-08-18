#! /usr/bin/env python

from galife import SimWindow
from pytcod import RENDER_SDL

SimWindow(100, 100, 30, 6, 0.03, 0.1, 0.1, 3000, 3000, 3000, renderer=RENDER_SDL).run()


#!/usr/bin/env python

"""Setup script for the ID3 module distribution."""

__revision__ = "$Id$"

from distutils.core import setup

setup(  # Distribution meta-data
    name="ID3",
    version="1.2",
    description="Module for manipulating ID3 informational tags on MP3 audio files",
    author="Ben Gertzfield",
    author_email="che@debian.org",
    url="http://id3-py.sourceforge.net/",
    # Description of the modules and packages in the distribution
    py_modules=["ID3"],
)

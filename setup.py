#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='StatusBoard',
    version='2.1',
    packages=find_packages(),
    package_data={
        'StatusBoard': [
            'templates/*.html', 'static/weather-icons/*.png', 'static/*.js',
            'static/*.css', 'static/gfx/*.png', 'static/gfx/*.jpg', 'static/gfx/*.css'
        ]
    },
    install_requires=[
        'brukva==0.0.1', 'feedparser==5.1.2', 'tornado==2.1', 'sleekxmpp==1.0rc2',
        'pytz==2012c'
    ],
    entry_points={
        'console_scripts': [
            'status_board=StatusBoard.scripts.status_board:main'
        ]
    },
    zip_safe=False
)
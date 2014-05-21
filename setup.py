#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='gsmsapi',
	version='0.10',
	description='SMS API for (german) SMS providers',
	author='Torge Szczepanek',
	author_email='debian@cygnusnetworks.de',
	maintainer='Torge Szczepanek',
	maintainer_email='debian@cygnusnetworks.de',
	license='MIT',
	packages=['gsmsapi'],
	url = 'https://github.com/CygnusNetworks/python-gsmsapi',
	download_url = 'https://github.com/CygnusNetworks/python-gsmsapi/tarball/v0.10',
	keywords = ["sms", "german", "sipgate", "smstrade", "api"],
	platforms='any',
	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Topic :: Software Development :: Libraries :: Python Modules']  # see: https://pypi.python.org/pypi?%3Aaction=list_classifiers
)

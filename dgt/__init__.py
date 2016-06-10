#! /usr/bin/env python2

import os
import sys
import glob
import pkgutil
import importlib
import inspect
import re

import git
import argparse # we need this for argparse.Namespace
import dgt.logger as logger
from dgt.base import Base


# Default "Bare" class, supporting only the Base actions
class Bare(Base):
	def __init__(self, options):
		Base.__init__(self, options)



# Custom exception handler, provides a bit more user-friendly messages
# The full stack is written in debug mode
def exhandler(t, value, traceback):
	logger.dgt.error("%s: %s" % (str(t.__name__), str(value)))
	# exit only if not in an interactive mode
	# __file__ is only defined in interactive mode
	import __main__
	if hasattr(__main__, '__file__'):
		sys.exit(1)



# the function looks up all the commands classes available in this package
def get_modules():
	#module_names = map(lambda x: x[1], pkgutil.iter_modules(__path__))
	module_names = map(lambda x: 'dgt.' + x[1], pkgutil.iter_modules(__path__))

	modules = {}
	for m in module_names:
		i = importlib.import_module(m)
		dg = getattr(i, '_dist_git', None)
		if dg:
			cls = None
			for n, o in inspect.getmembers(i):
				if getattr(o, '_commands_class', False):
					cls = o
					break
			modules[cls] = dg
			#, cls
	return modules



# generic wrapper function for Commands classes
# the function detects the appropriate Commands class based on the remote git url
# @returns an instance of the detected Commands class
# @takes options namespace -- can be passed directly from argparser
# @takes **kwargs and populates options with them
def Commands(options = None, **kwargs):
	# Initialize the options attribute
	options = options or argparse.Namespace()

	# Convert all the keyword arguments to the options namespace
	for arg in kwargs:
		setattr(options, arg, kwargs[arg])

	# Parse the Namespace
	path = getattr(options, 'path', './')
	debug = getattr(options, 'debug', False)
	quiet = getattr(options, 'quiet', False)
	dist_git = getattr(options, 'dist_git', None)

	## Setup loggers
	logger.cli.setLevel(level = logger.INFO)

	# Override the exception handler function if we are not debugging
	if debug:
		logger.dgt.setLevel(level=logger.DEBUG)
		logger.rpkg.setLevel(level=logger.DEBUG)
	else:
		sys.excepthook = exhandler
		if quiet:
			logger.dgt.setLevel(level=logger.ERROR)
			logger.rpkg.setLevel(level=logger.ERROR)
		else:
			logger.dgt.setLevel(level=logger.WARNING)
			logger.rpkg.setLevel(level=logger.WARNING)

	# Get some basic info from git
	repo = git.Repo(path)

	## Process modules
	modules = get_modules()
	logger.dgt.debug('The following modules were found: %s' % str(modules))

	# Detect the proper dist-git from the remote url
	Class = None

	# If we are given a dist_git, use the given dist_git
	if dist_git:
		modules = filter(lambda x: x._commands_name == dist_git, modules)
		if modules:
			Class = modules.pop()

	# Otherwise, detect the dist-git from remote url
	elif repo.head.ref.tracking_branch():
		# Find remote name of the current branch
		remote_name = repo.head.ref.tracking_branch().remote_name
		# Get the url from the config file
		remote_url = repo.config_reader().get('remote "%s"' % remote_name, 'url')
		logger.dgt.debug('Remote git url: %s' % remote_url)

		for cls in modules:
			if any(map(lambda x: re.search(x, remote_url), modules[cls])):
				Class = cls

	# If no class was found, switch to bare class
	if not Class:
		Class = Bare
	return Class(options)

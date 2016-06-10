#! /usr/bin/env python2

from argparse import ArgumentParser

class GitrpkgArgParser(ArgumentParser):
	def __init__(self, *args, **kwargs):
		ArgumentParser.__init__(self, *args, **kwargs)
		group = self.add_argument_group('global-modifiers', 'Modifiers that are common for all the git dist-* commands')
		group.add_argument('--debug', action='store_true', default=False, help='Be very verbose')
		group.add_argument('--config', dest='config_name', default=None, action='store', help='Specify a config file to use')
		group.add_argument('--path', metavar='DIR', action='store', default='./', help='Define the directory to work in (defaults to cwd)')
		group.add_argument('--noask', action='store_true', help='Always choose the default option')
		group.add_argument('--dist', action='store', help='Override the discovered distribution')
		group.add_argument('--target', action='store', help='Define build target to build into')
		#group.add_argument('--module-name', action='store', help='Override the module name')
		group.add_argument('--user', action='store', help='Override the discovered user name')
		group.add_argument('--dist-git', action='store', help='Specify the dist-git to use, do not auto-detect')

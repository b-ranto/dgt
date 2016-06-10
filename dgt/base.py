# Copyright (C) 2014-2016 Red Hat Inc.
# Author(s):
#   Jesse Keating <jkeating@redhat.com>
#   Boris Ranto <branto@redhat.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import dgt.logger as logger

class Base(object):
	def __init__(self, options = None):
		# load few basic attributes
		noask = getattr(options, 'noask', False)

		self.noask = noask


	def __getattr__(self, attr):
		raise AttributeError("the '%s' dist-git does not support the '%s' operation" % (str(type(self).__name__).lower(), str(attr)))


	def choose(self, options = [], default = 0):
		# Interpret -1 as len len(x) - 1
		if isinstance(default, int) and default < 0:
			default += len(options)
		# If noask is set just return default value
		if self.noask:
			return default
		while True:
			logger.cli.info("List of options:")
			for o in range(len(options)):
				out = '%d) ' % o
				if o == default:
					out = ''.join([out, str(options[o]), ' (default)'])
				else:
					out += str(options[o])
				logger.cli.info(out)
			choice = raw_input("Your choice (item number): ")
			if choice == '' and default != None:
				return default
			try:
				options[int(choice)]
				return int(choice)
			except:
				logger.cli.error("Invalid input, try again.")
				continue

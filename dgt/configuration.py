#! /usr/bin/env python2

from ConfigParser import SafeConfigParser
import dgt.logger as logger
import os
import collections

class ConfigParser(object):
	def __init__(self, module = 'dgt', config_type=None):
		self.config_files = collections.OrderedDict([
			('system', '/etc/dgt/dgt.conf'),
			('system-module', ''.join(['/etc/dgt/', module, '.conf'])),
			('user', os.path.expanduser('~/.local/dgt/dgt.conf')),
			('user-module', os.path.expanduser(''.join(['~/.local/dgt/', module, '.conf']))),
		])
		if config_type:
			if config_type in self.config_files.keys():
				logger.dgt.debug("Processing only %s config type" % config_type)
				self.config_files = {config_type: self.config_files[config_type]}
			else:
				logger.dgt.warning("No such config type, reading all of them")
				logger.dgt.warning("Use one of %s to override" % str(self.config_files.keys()))
		# parse configs
		self.config_parser = SafeConfigParser()
		self.config_parser.read(self.config_files.values())


	def items(self, section):
		if not self.config_parser.has_section(section):
			return {}
		return dict(self.config_parser.items(section))

	def parse_section(self, section, items, cls = None):
		if not self.config_parser.has_section(section):
			raise RuntimeError("No '%s' section in config file '%s'" % (section, self.config_file))

		values = []

		for option in items:
			if not self.config_parser.has_option(section, option):
				raise RuntimeError("No '%s' option in section '%s' of config file (%s)" % (key, section, ''.join(['/etc/rpkg/', config_name, '.conf'])))
			values.append(self.config_parser.get(section, option, raw = True))
			if cls:
				setattr(cls, option, values[-1])
		return values

	def set(self, section, option, value):
		self.config_parser.set(section, option, value)

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

import os
import time

import koji
import kobo.shortcuts

import pyrpkg

from dgt.configuration import ConfigParser
import dgt.logger as logger

class Koji(pyrpkg.Commands):
	def __init__(self, options = None):
		# load few basic attributes
		path = getattr(options, 'path', './')

		# load the <config_section> from the config file
		self.config = ConfigParser(getattr(options, 'config_name', None))
		args = self.config.parse_section('base', [
			'lookaside',
			'lookasidehash',
			'lookaside_cgi',
			'gitbaseurl',
			'anongiturl',
			'branchre',
			'kojiconfig',
			'build_client',
		])

		# parse global options
		kwargs = {
			'user': getattr(options, 'user', None),
			'dist': getattr(options, 'dist', None),
			'target': getattr(options, 'target', None),
			'quiet': getattr(options, 'quiet', False),
		}

		pyrpkg.Commands.__init__(self, path, *args, **kwargs)

		# initialize new properties
		self._srpm_koji_url = None
		self._srpmfilename = None
		self._latest_build = None


	@property
	def srpm_koji_url(self):
		if self._srpm_koji_url == None:
			self.load_srpm_koji_url()
		return self._srpm_koji_url


	def load_srpm_koji_url(self):
		logger.dgt.debug("Uploading srpm: %s" % self.srpmfilename)
		serverdir = 'cli-build/%r.%s' % (time.time(), kobo.shortcuts.random_string(8))
		logger.dgt.debug("serverdir: %s" % serverdir)
		# Upload the srpm to koji sever
		self.kojisession.uploadWrapper(self.srpmfilename, serverdir)
		self._srpm_koji_url = "%s/%s" % (serverdir, os.path.basename(self.srpmfilename))


	@property
	def srpmfilename(self):
		if self._srpmfilename == None:
			self.sources()
			self.srpm()
			self._srpmfilename = self.srpmname
		return self._srpmfilename


	def build_wait(self, task_id):
		logger.cli.info("[build] Waiting for task %s to finish..." % str(task_id))
		info = self.kojisession.getTaskInfo(task_id, request=True)
		while koji.TASK_STATES[info['state']] not in ['CLOSED', 'CANCELED', 'FAILED']:
			time.sleep(5)
			info = self.kojisession.getTaskInfo(task_id, request=True)
		logger.cli.info("[build] Task %s result: %s" % (str(task_id), str(koji.TASK_STATES[info['state']])))
		logger.cli.info("[build] See '%s/taskinfo?taskID=%s' for details" % (self.kojiweburl, task_id))
		return koji.TASK_STATES[info['state']] == 'CLOSED'


	def build_cancel(self, task_id):
		# Just force cancel the build
		try:
			self.kojisession.cancelTask(int(task_id))
		except Exception, e:
			logger.dgt.error(str(e))
			return False
		return True


	@property
	def latest_build(self):
		if self._latest_build == None:
			self.load_latest_build()
		return self._latest_build

	def load_latest_build(self):
		tags = None
		# you're free to extend it for other EPELs
		if self.branch_merge == "el6":
			tags = ["dist-6E-epel-testing-candidate"]
		elif self.branch_merge == 'master':
			tags = ["rawhide"]
		else:
			postfixes = ('-candidate', '-build', '', '-fastrack-candidate', '-fastrack', '-updates-candidate', '-updates-testing-pending', '')
			tags = []
			for p in postfixes:
				tags.append(self.branch_merge + p)
				tags.append(self.branch_merge.upper() + p)

		_pkg = self.module_name
		for tag in tags:
			try:
				data = self.kojisession.getLatestBuilds(tag, package = _pkg)
				logger.dgt.debug("load_latest_build: tag '%s' used" % tag)
			except Exception, e:
				# If koji raised an exception then we just go ahead and try another tag until we find a valid one
				logger.dgt.debug(str(e))
				continue
			if len(data) == 1:
				logger.dgt.debug(str(data[0]))
				self._latest_build = data[0]
				return True
			else:
				logger.dgt.warning("kojisession.getLatestBuilds returned an array of %d elements, expected one." % len(data))
		logger.dgt.warn("Could not find the latest build, maybe there was not one?")
		return False

#! /usr/bin/env python2

import re
import getpass

import pprint

import dgt.logger as logger

# Import python-bugzilla library
try:
	import bugzilla.rhbugzilla
except:
	logger.dgt.error('You do not have python-bugzilla installed or your instance of python-bugzilla is broken')
	raise


class Bugzilla(object):
	"""Query the rh bugzilla"""


	def __init__(self, options):
		# parse and save some config options
		self.config.parse_section('bugzilla', ['bugzillaurl'], cls = self)

		# initialize new properties
		self._bz = None


	@property
	def bz(self):
		if self._bz == None:
			self.load_bz()
		return self._bz


	def load_bz(self):
		# Reads the config file and logs in if username and password is present
		self._bz = bugzilla.rhbugzilla.RHBugzilla(url=self.bugzillaurl)
		if not self._bz.logged_in:
			if len(self.bugzillaurl.split('/')) > 2:
				# We want the part after https://
				section = self.bugzillaurl.split('/')[2]
			else:
				section = "<bz_url>"
			logger.dgt.warn("You do not have ~/.bugzillarc config file or your config file does not contain a section for the bugzilla server")
			logger.dgt.warn("If you want to setup your bugzilla login, add the following lines to your ~/.bugzillarc:\n\n[%s]\nuser = <username>\npassword = <password>\n\n" % section)
			logger.cli.info(("Now, please enter your bugzilla username and password:"))
			user = raw_input("username: ")
			password = getpass.getpass("password: ")
			try:
				self._bz.login(user=user, password=password)
			except:
				logger.dgt.error('Failed to connect to bugzilla, maybe incorrect self.options? (username or password)')
				logger.dgt.error(''.join(['USERNAME: ', user, "\n"]))
				raise RuntimeException("Bugzilla login failed")
		# No need to store the password anymore
		password = None
		logger.dgt.debug("bz = (%s, %s)" % (str(self._bz), str(self._bz.logged_in)))


	def bugzilla_bugs(self, start=None, end=None, bugs=[]):
		# If we already got some bugs, there is no need to look at the git history
		_bugs = {}
		for i in bugs:
			_bugs[i] = 'No commit URL provided.'
		if _bugs:
			return _bugs
		commits = []
		if start == None and end == None:
			if self.latest_build:
				scm = self.kojisession.getTaskRequest(self.latest_build['task_id'])[0]
				logger.dgt.debug('scm: %s' % str(scm))
				url = self.anongiturl % {'module': self.module_name}
				if scm[:len(url)] == url:
					commits = list(self.repo.iter_commits(scm[len(url)+2:] + '..'))
				else:
					logger.dgt.warn('Latest build is not from git')
			else:
				logger.dgt.warn('Latest build is not in the remote DB')
			# Use the latest commit by default
			if not commits:
				logger.dgt.warn('Failed to detect commit range')
				logger.dgt.warn('Falling back to latest commit')
				commits = [self.repo.commit('HEAD')]
		elif start == None:
			# This mode does not make much sense but we should probably allow it
			commits = list(self.repo.iter_commits(end))
		elif end == None:
			commits = list(self.repo.iter_commits(start + '..')) + [self.repo.commit(start)]
		else:
			commits = list(self.repo.iter_commits(start + '..' + end)) + [self.repo.commit(start)]

		# We detect bug numbers by these regexps
		bug_pattern = re.compile('(?:(?:bug|bz|rhbz)? *# *|(?:bug|bz|rhbz) *)(\d+)', re.IGNORECASE)
		resolves_pattern = re.compile('^(?: |-)*(Resolves) *:', flags=re.I) # TODO: Contemplate on the meaning of Related, here...
		for commit in commits:
			full_msg = filter(lambda x: resolves_pattern.search(x), commit.message.split('\n'))
			for msg_line in full_msg:
				line_bugs = map(int, bug_pattern.findall(msg_line))
				for bug in line_bugs:
					if _bugs.has_key(bug):
						_bugs[bug].extend([self.commiturl % {'pkg': self.module_name, 'branch': self.branch_merge}, commit.hexsha, '\n'])
					else:
						_bugs[bug] = ['dist-git commits related to build %s:\n', self.commiturl % {'pkg': self.module_name, 'branch': self.branch_merge}, commit.hexsha, '\n']
		for bug in _bugs:
			_bugs[bug] = "".join(_bugs[bug])
		logger.dgt.debug("_bugs = %s" % str(_bugs))
		return _bugs


	def bugzilla(self, fixed_in=False, comment=False, state=None, start=None, end=None, bugs=[]):
		if not bugs:
			bugs = self.bugzilla_bugs(start, end)
		if bugs:
			# just preload the nvr so that the output that follows is not interrupted by warnings
			self.nvr
			logger.cli.info("I'm about to update the following bugs:")
			logger.cli.info(pprint.pformat(list(bugs)))
			logger.cli.info("Add comment: " + str(comment))
			logger.cli.info("Update fixed-in-field: %s (%s)" % (str(fixed_in), str(self.nvr)))
			logger.cli.info("Change to state: " + str(state))
			logger.cli.info("Do you want to proceed with the update?")
			choice = self.choose(["no", "yes"], 1)
			if choice != 1:
				logger.cli.info("You chose no, I will not update any bug.")
				return True
		else:
			logger.dgt.warn("No bugs to update were found in git history. Maybe you need to specify --from <git_hash>?")
		for bugno in bugs:
			logger.cli.info("Updating bug %d..." % bugno)
			# Connect to the bug
			bug = self.bz.getbug(bugno)

			# Create the query
			query = {}

			# Update the Fixed in field
			# TODO: could probably be a bit more sophisticated
			if fixed_in:
				if self.nvr in bug.cf_fixed_in:
					logger.dgt.warning("".join(["Bug #", str(bugno), " is already a part of Fixed in field, not duplicating'"]))
				else:
					if bug.cf_fixed_in:
						query['cf_fixed_in'] = bug.cf_fixed_in + ' ' + str(self.nvr)
					else:
						query['cf_fixed_in'] = str(self.nvr)

			if comment:
				if isinstance(bugs, dict):
					query['comment'] = {'body': (bugs[bugno] % str(self.nvr)), 'is_private': True}
				else:
					logger.dgt.warn("Can't add commit comment for user supplied bugzillas")

			if state:
				query['status'] = state

			# Batch update the bugzilla iff the length of query is non-zero
			if len(query):
				rmt = self.bz.update_bugs([bug.id], query)
		return True


	def bugzilla_flag_state(self, bug, query_flag):
		for bug_flag in bug.flags:
			if bug_flag['name'] == query_flag:
				return bug_flag['status']
		return '?'


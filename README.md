dgt (dist-git tool) is an alternative implementation of packaging tools built on top of pyrpkg with few nice things such as semi-automated rebase/patching, workflow support, improved auto-detection, dist-git transparency, git cli fallback, library-like python interface, ...

Instructions:

* ./configure # this will create src.rpm as well
* python setup.py install # as root, alternatively build and install the src.rpm
* read the help/man pages or use zsh smart completion for more info: `dgt --help`


Sample usage:

* `dgt clone <package> --with-upstream git://<url> && cd <package>` # Setup a git repo with fedora and upstream remote (the branches of that names point to master of each remote)
* `dgt checkout -t fedora/f23` # Switch to a fedora dist-git branch
* `dgt bump --init <version>` # init semi-automated rebase, you can use 'dgt local --init' if you just want to apply a patch
* `dgt bump --patch` # apply all the patches from the spec file with git am, resolve conflicts, to continue run the command again
* `dgt cherry-pick <hexsha>` # I also want to include this upstream `hex-sha` commit to the rebase
* `dgt bump --apply` # apply back the rebased patches to the dist-git
* `dgt commit --amend `# review and update the generated patch
* `dgt push` # push if you like or 'dgt bump --abort' to reset
* `dgt koji --scratch` # do a scratch build, this is non-blocking, add --watch if you want to watch it
* `dgt bugzilla -fcm` # update bugzillla, you should do this before the koji package is built so that latest build points to the previous latest build, otherwise just last commit will be used
* `dgt workflow --run rebase <version>` # Do all the 'bump' machinery
* `dgt workflow --run patch <hexsha>` # Apply the given (upstream) patch to the dist-git (using the 'dgt local' machinery)

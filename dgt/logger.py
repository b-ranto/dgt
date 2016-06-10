from logging import getLogger, NullHandler, StreamHandler, Formatter
from logging import DEBUG, INFO, WARNING, ERROR
import sys

rpkg = getLogger('rpkg')

dgt = getLogger('dgt')

cli = getLogger('cli')

handler = NullHandler()
dgt.addHandler(handler)
cli.addHandler(handler)

# Add a default handler if there are no real handlers set, yet (not counting NullHandler)
if len(rpkg.handlers) <= 1:
	handler = StreamHandler(sys.stderr)
	formatter = Formatter('[%(name)s] %(levelname)s: %(message)s')
	handler.setFormatter(formatter)
	rpkg.addHandler(handler)
if len(dgt.handlers) <= 1:
	handler = StreamHandler(sys.stderr)
	formatter = Formatter('[%(name)s] %(levelname)s: %(message)s')
	handler.setFormatter(formatter)
	dgt.addHandler(handler)
if len(cli.handlers) <= 1:
	handler = StreamHandler(sys.stdout)
	formatter = Formatter('%(message)s')
	handler.setFormatter(formatter)
	cli.addHandler(handler)

# Colores
NORMAL      = '\x1B[0m'
BOLD        = '\x1B[1m'
BLUE        = '\x1B[0;34m'
BLUE_BOLD   = '\x1B[1;34m'
RED         = '\x1B[0;31m'
RED_BOLD    = '\x1B[1;31m'
GREEN       = '\x1B[0;32m'
GREEN_BOLD  = '\x1B[1;32m'
GREY        = '\x1B[0;30m'
GREY_BOLD   = '\x1B[1;30m'
LILAC       = '\x1B[0;35m'
LILAC_BOLD  = '\x1B[1;35m'
YELLOW      = '\x1B[2;33m'
YELLOW_BOLD = '\x1B[1;33m'

class Log:
	"""
	Clase usada para imprimir por pantalla
	"""
	def __init__(self, log_ns="Logger"):
		self.ns = log_ns
		self.msg = ""
		self.output = True

	def d(self, message, sub_ns=None):
		self.set_ns(sub_ns)
		self.set_color(YELLOW)
		self.flush(message)

	def v(self, message, sub_ns=None):
		self.set_ns(sub_ns)
		self.set_color(NORMAL)
		self.flush(message)

	def e(self, message, sub_ns=None):
		self.set_ns(sub_ns)
		self.set_color(RED)
		self.flush(message)

	def c(self, message, color='NORMAL', sub_ns=None):
		if sub_ns: self.set_ns(sub_ns)
		self.set_color(eval(color))
		self.flush(message)

	def set_ns(self, sub_ns=None):
		self.msg += "{}[ {} ] ".format(BOLD, self.ns)
		self.msg += "{}[ {} ] ".format(GREEN_BOLD, sub_ns) if sub_ns != None else ""

	def set_color(self, color=NORMAL):
		self.msg += color

	def flush(self, message=""):
		self.msg += message
		self.msg += NORMAL
		if self.output: print self.msg
		self.msg = ""

	def disable(self):
		self.output = False

	def enable(self):
		self.output = True
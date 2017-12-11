# Tampio Interpreter
# Copyright (C) 2017 Iikka Hauhio

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys

def fatalError(msg):
	sys.stderr.write(msg + "\n")
	raise(StopEvaluation())

class StopEvaluation(Exception):
	pass

def syntaxError(msg, tokens):
	raise(TampioSyntaxError(msg, tokens, tokens.i))

class TampioSyntaxError(Exception):
	def __init__(self, msg, tokens, i):
		self.msg = msg
		self.tokens = tokens
		self.place = i
	def printMe(self, stream):
		stream.write("Syntax error: " + self.msg + "\n" + self.tokens.fancyContext(self.place) + "\n")
	def __str__(self):
		stream.write("Syntax error: " + self.msg + " (in \"" + self.tokens.context(self.place) + "\")")

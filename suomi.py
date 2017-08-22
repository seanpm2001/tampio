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

import os, sys, traceback, argparse, operator, re
from voikko.libvoikko import Voikko, Token
from voikko.inflect_word import inflect_word

LANGUAGE = "fi-x-morpho"
ENCODING = "UTF-8"

voikko = Voikko(LANGUAGE)

CASES_LATIN = {
	"nimento": "nominatiivi",
	"omanto": "genetiivi",
	"osanto": "partitiivi",
	"olento": "essiivi",
	"tulento": "translatiivi",
	"ulkotulento": "allatiivi",
	"ulkoolento": "adessiivi",
	"ulkoeronto": "ablatiivi",
	"sisatulento": "illatiivi",
	"sisaolento": "inessiivi",
	"sisaeronto": "elatiivi",
	"vajanto": "abessiivi",
	"keinonto": "instruktiivi",
	"seuranto": "komitatiivi",
}

CASES_ABRV = {
	"": "*",
	"nimento": "N",
	"omanto": "G",
	"osanto": "P",
	"olento": "E",
	"tulento": "T",
	"ulkotulento": "U<",
	"ulkoolento": "U_",
	"ulkoeronto": "U>",
	"sisatulento": "S<",
	"sisaolento": "S_",
	"sisaeronto": "S>",
	"vajanto": "A",
	"keinonto": "I",
	"seuranto": "K",
}

CASES_A = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ta",
	"olento": ":na",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":lla",
	"ulkoeronto": ":lta",
	"sisatulento": ":han",
	"sisaolento": ":ssa",
	"sisaeronto": ":sta",
	"vajanto": ":tta",
	"keinonto": ":in",
	"seuranto": ":ineen",
}

CASES_F = {
	"nimento": "",
	"omanto": ":n",
	"osanto": ":ää",
	"olento": ":nä",
	"tulento": ":ksi",
	"ulkotulento": ":lle",
	"ulkoolento": ":llä",
	"ulkoeronto": ":ltä",
	"sisatulento": ":ään",
	"sisaolento": ":ssä",
	"sisaeronto": ":stä",
	"vajanto": ":ttä",
	"keinonto": ":in",
	"seuranto": ":ineen",
}

def inflect(word, case):
	case_latin = CASES_LATIN[case]
	if word[0] == "@":
		case_latin += "_mon"
	word = word[1:]
	
	if re.match(r"[0-9]+", word):
		if case == "sisatulento":
			if word[-1] in "123560":
				return word + ":een"
			elif word[-1] in "479":
				return word + ":ään"
			else: # 8
				return word + ":aan"
		elif word[-1] in "14579":
			return word + CASES_A[case].replace("a", "ä")
		else:
			return word + CASES_A[case]
	elif len(word) == 1:
		if word in "flmnrsx":
			return word + CASES_F[case]
		elif case == "sisatulento":
			if word in "aeiouyäöå":
				return word + ":h" + word + "n"
			elif word in "bcdgptvw":
				return word + ":hen"
			elif word in "hk":
				return word + ":hon"
			elif word == "j":
				return "j:hin"
			elif word == "q":
				return "q:hun"
			elif word == "z":
				return "z:aan"
		elif word in "ahkoquzå":
			return word + CASES_A[case]
		else:
			return word + CASES_A[case].replace("a", "ä")
	else:
		inflections = inflect_word(word)
		if case_latin not in inflections:
			return word + ":" + case
		return inflections[case_latin]
		

def lexLine(line):
	output = []
	if "#" in line:
		line = line[:line.index("#")]
	paragraph = line.strip()
	if paragraph == "":
		return []
	for token in voikko.tokens(paragraph):
		if token.tokenType != Token.WORD:
			continue
		word = token.tokenText
		analysisList = voikko.analyze(word)
		alternatives = []
		for analysis in analysisList:
			bf = analysis["BASEFORM"]
			cl = analysis["CLASS"]
			if cl == "nimisana" or cl == "lyhenne" or cl == "lukusana" or cl == "laatusana" or cl == "nimisana_laatusana" or cl == "etunimi":
				alternatives += [Noun(bf, analysis["SIJAMUOTO"], analysis["NUMBER"])]
			elif cl == "seikkasana":
				alternatives += [Noun(bf, "nimento", "na")]
			elif cl == "teonsana" or cl == "kieltosana":
				alternatives += [Verb(bf)]
			elif cl == "sidesana":
				alternatives += [Conj(bf)]
			#else:
			#	print("Unknown word:", bf, analysis)
		if len(analysisList) == 0:
			alternatives += [Noun(word, "nimento", "singular")]
		output += [alternatives]
	return output

class Noun:
	def __init__(self, bf, case, num):
		self.cl = "noun"
		self.bf = bf
		self.case = case
		self.num = num
	def str(self, nocase=False):
		num = "$" if self.num == "singular" else "@" if self.num == "plural" else "."
		case = CASES_ABRV[self.case]
		if nocase:
			return num + self.bf
		else:
			return num + self.bf + ":" + case

class Verb:
	def __init__(self, bf):
		self.cl = "verb"
		self.bf = bf
	def str(self):
		return "#" + self.bf

class Conj:
	def __init__(self, bf):
		self.cl = "conj"
		self.bf = bf
	def str(self, nocase=False):
		return "&" + self.bf

def next(words):
	if len(words) == 0:
		sys.stderr.write("Syntax error: unexpected eof\n")
		raise(StopEvaluation())
	w = words[0]
	del words[0]
	return as2w(w)

PROMOTE = [
	"yksi"
]

def as2w(w):
	return sorted(w, key=lambda a: 1 if a.cl == "noun" or a.bf in PROMOTE else 0)[-1]

class EqTree:
	def __init__(self, op, left, right):
		self.op = op
		self.left = left
		self.right = right
	def str(self):
		if self.query():
			return self.left.str()
		elif self.op == "#olla":
			return self.left.str() + " = " + self.right.str()
		elif self.op == "#esittää":
			return self.left.str() + ' = "' + self.right.str() + '"'
	def query(self):
		return self.right == None

def parseEq(words, allowQueries):
	words = words[:]
	c, left = parsePattern(words)
	if c != "nimento":
		sys.stderr.write("Syntax error: illegal case (" + left.str() + ")\n")
		raise(StopEvaluation())
	if len(words) == 0 and allowQueries:
		return EqTree("", left, None)
	w = next(words)
	if w.str() not in ["#olla", "#esittää"]:
		sys.stderr.write("Syntax error: expected 'on' or 'esitetään' (at " + w.str() + ")\n")
		raise(StopEvaluation())
	c, right = parsePattern(words)
	if c != "nimento":
		sys.stderr.write("Syntax error: illegal case (" + right.str() + ")\n")
		raise(StopEvaluation())
	return EqTree(w.str(), left, right)

def parseVar(name):
#	if re.match(name, r"\$[1-9][0-9]*"):
#		return NumTree(int(name[1:]))
#	else:
		return VarTree(name)

class VarTree:
	def __init__(self, name):
		self.name = name
	def __eq__(self, tree):
		return type(tree) == VarTree and self.name == tree.name
	def __hash__(self):
		return hash(self.name)
	def str(self):
		return self.name
	def match(self, tree):
		if len(self.name) == 2 and re.match(r".[^0-9]", self.name):
			return True, {self.name: tree}
		if isinstance(tree, VarTree):
			return self.name == tree.name, {}
#		elif isinstance(tree, NumTree):
#			return self.name == str(tree.num), {}
		return False, {}
	def inflect(self, case):
		return inflect(self.name, case)
	def subs(self, subs):
		if self.name in subs:
			return subs[self.name]
		else:
			return self

#class NumTree:
#	def __init__(self, num):
#		self.num = num
#	def __eq__(self, tree):
#		return type(tree) == NumTree and self.num == tree.num
#	def __hash__(self):
#		return self.num
#	def str(self):
#		return "$" + str(self.num)
#	def match(self, tree):
#		if isinstance(tree, NumTree):
#			return self.num == tree.num, {}
#		elif isinstance(tree, VarTree):
#			return str(self.num) == tree.name, {}
#		return False, {}
#	def subs(self, subs):
#		return self
#	def inflect(self, case):
#		return inflect(str(self.num), case)

class CallTree:
	def __init__(self, head, args, headInfl, argInfls):
		self.head = head
		self.args = args
		self.headInfl = headInfl
		self.argInfls = argInfls
		self.repr = self.head.str() + ":" + CASES_ABRV[self.headInfl] + "(" + ", ".join([arg.str() + ":" + CASES_ABRV[argInfl] for arg, argInfl in zip(self.args, self.argInfls)]) + ")"
		self.hash = hash(self.head) + sum([hash(a) for a in self.args]) + hash(self.headInfl) + sum([hash(ai) for ai in self.argInfls])
	def __eq__(self, tree):
		if type(tree) == CallTree:
			return self.repr == tree.repr
			#return self.head == tree.head and self.args == tree.args and self.headInfl == tree.headInfl and self.argInfls == tree.argInfls
		else:
			return False
	def __hash__(self):
		return self.hash
	def str(self):
		return self.repr
	def match(self, tree):
		if isinstance(tree, CallTree):
			if self.headInfl != tree.headInfl:
				return False, {}
			
			ok, subs = self.head.match(tree.head)
			
			if not ok or len(tree.args) != len(self.args):
				return False, {}
			
			for arg, arg2, ai, ai2 in zip(self.args, tree.args, self.argInfls, tree.argInfls):
				if ai != ai2:
					return False, {}
				ok, subs2 = arg.match(arg2)
				subs.update(subs2)
				if not ok:
					return False, {}
			return True, subs
		return False, {}
	def subs(self, subs):
		return CallTree(self.head.subs(subs), [arg.subs(subs) for arg in self.args], self.headInfl, self.argInfls)
	def inflect(self, case):
		if self in REPRS:
			return '"' + REPRS[self].inflect(case) + '"'
		if self.head.str() in ["&ja", "&sekä", "&tai"]:
			return self.args[0].inflect(case) + " " + self.head.name[1:] + " " + self.args[1].inflect(case)
		if self.head.str() in [".ynnä", "$plus", "$miinus"]:
			return self.args[0].inflect("nimento") + " " + self.head.name[1:] + " " + self.args[1].inflect(case)
		if self.headInfl == "olento":
			a = self.args[0].inflect(case) + " " + self.head.inflect("olento")
			if len(self.args) == 2: # TODO: entä jos tulevaisuudessa olisikin enemmän argumentteja???
				a += " " + self.args[1].inflect(self.argInfls[1])
			return a
		return self.args[0].inflect("omanto") + " " + self.head.inflect(case)

def parsePattern(words):
	case, root = parseUnary(words)
	while len(words) != 0:
		w = as2w(words[0])
		if w.str() in ["&ja", "&sekä", "&tai", ".ynnä:N", "$plus:N", "$miinus:N"]:
			del words[0]
			
			case2, arg = parseUnary(words)
			if w.str() in ["&ja", "&tai", "&sekä"] and case != case2:
				sys.stderr.write("Syntax error: illegal case (after " + w.str() + ", expected " + case + ", got " + case2 + ")\n")
				raise(StopEvaluation())
			case = case2
			
			root = CallTree(VarTree(w.str(nocase=True)), [root, arg], "", ["", ""])
		else:
			break
	return case, root

def parseUnary(words):
	w = next(words)
	if w.cl != "noun":
		sys.stderr.write("Syntax error: expected noun (at " + w.str() + ")\n")
		raise(StopEvaluation())
	root = parseVar(w.str(nocase=True))
	root = parseEssive(root, words, True)
	while w.case == "omanto":
		w = next(words)
		root = CallTree(parseVar(w.str(nocase=True)), [root], "", ["omanto"])
	if w.case != "nimento" and w.case != "omanto" and len(words) != 0 and as2w(words[0]).str() in ["&ja", "&tai", "&sekä"]:
		words2 = words[:]
		conj = as2w(words[0]).str()
		del words[0]
		#if w.case == "omanto":
			# ... TODO
		#else:
		case, arg = parseUnary(words)
		if case == w.case:
			root = CallTree(parseVar(conj), [root, arg], "", [case, case])
		else:
			del words[:]
			words += words2
	else:
		root = parseEssive(root, words, True)
	return w.case, root

def parseEssive(root, words, allowFullPattern):
	if len(words) != 0:
		w = as2w(words[0])
		if w.cl == "noun":
			owners = []
			if allowFullPattern:
				words2 = words[:]
				del words[0]
				while w.case == "omanto":
					owners += [w]
					w = next(words)
			#print([o.str() for o in owners])
			if w.case == "olento":
				args = []
				argInfls = []
				if len(words) != 0:
					if as2w(words[0]).cl == "noun":
						case, arg = parseUnary(words)
						args += [arg]
						argInfls += [case]
				root2 = parseVar(w.str(nocase=True))
				for o in owners[::-1]:
					root2 = CallTree(root2, [parseVar(o.str(nocase=True))], "", ["omanto"])
				root = CallTree(root2, [root]+args, "olento", [""]+argInfls)
			elif allowFullPattern:
				del words[:]
				words += words2
				return root
	return root

stack = []

class StopEvaluation(Exception):
	pass

def printStack():
	sys.stderr.write("Stack:\n")
	for val in stack:
		sys.stderr.write("  " + val.str() + "\n")
	raise(StopEvaluation())

def evals(tree):
	a = evals_(tree)
	while True:
		b = evals_(a)
		if a == b:
			break
		a = b
	#print("End: " + a.str())
	return a

def evals_(tree):
	global stack
	stack += [tree]
	try:
		a = None
		for defi in DEFS:
			ok, subs2 = defi.left.match(tree)
			if ok:
				#print("Match: " + tree.str() + " == " + defi.left.str() + " -> " + defi.right.str())
				a = defi.right.subs(subs2)
				break
		if a is None:
			if isinstance(tree, CallTree):
				a = CallTree(evals_(tree.head), [evals_(arg) for arg in tree.args], tree.headInfl, tree.argInfls)
			else:
				a = tree
	except StopEvaluation as e:
		raise(e)
	except Exception as e:
		traceback.print_exc(file=sys.stderr)
		printStack()
	del stack[-1]
	return a

DEFS = []
REPRS = {}

def evalFile(filename):
	with open(filename) as f:
		for line in f:
			evalLine(line)

def evalLine(line, allowQueries=False):
	global DEFS
	output = lexLine(line)
	if not output:
		return
	#print(" ".join(["|".join(set([a.str() for a in alternatives])) for alternatives in output]))
	eq = parseEq(output, allowQueries)
	#print(eq.str())
	if eq.query():
		return evals(eq.left)
	elif eq.op == "#olla":
		DEFS += [eq]
	elif eq.op == "#esittää":
		REPRS[evals(eq.left)] = eq.right

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
evalFile(os.path.join(SCRIPT_DIR, 'std.suomi'))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Interpret code.')
	parser.add_argument('filename', type=str, nargs='?',
		help='source code file')
	args = parser.parse_args()
	if args.filename:
		evalFile(args.filename)
		print(evals(parseVar("$tulos")).inflect("nimento"))
	else:
		print("""Tampio Interpreter
Copyright (C) 2017 Iikka Hauhio
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
Read the LICENSE file for details.""")
		while True:
			try:
				line = input(">>> ")
			except EOFError:
				print()
				break
			try:
				out = evalLine(line, True)
				if out:
					print(out.inflect("nimento"))
			except StopEvaluation:
				continue

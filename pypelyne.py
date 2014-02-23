#!/usr/bin/env python
#coding:utf-8

import re
import sys
from log import Log

# Codificación operaciones (no usado)
NOOP = 0x00
ADD = 0x01
SUB = 0x02
MULT = 0x04
TRAP = 0x08

# Inicializar logger
l = Log("Pypelyne")

class Trap(Exception):
	def __init__(self, msg):
		Exception.__init__(self, msg)

class EndOfProgram(Exception):
	def __init__(self, msg):
		Exception.__init__(self, msg)

class Programmer:
	def __init__(self, memory):
		self.memory = memory

	def insert_instruction(self, instruction_line):
		try:
			op, rc, ra, rb = re.split(',? ', instruction_line.strip())
		except ValueError:
			op, rc, ra, rb = instruction_line.strip(), None, None, None
		l.d("Insert: {op} {rc} {ra} {rb}".format(**locals()), "Programmer")
		self.memory.insert_instruction(Instruction(op, ra, rb, rc))

class InstructionsMemory:
	def __init__(self):
		self.instructions = []

	def insert_instruction(self, instruction):
		self.instructions.append(instruction)

	def get_instruction_at(self, pc):
		try:
			return self.instructions[pc]
		except IndexError:
			raise EndOfProgram("No more instructions.")

class Registers:
	def __init__(self):
		self.registers = {
			None : None,
			"r0" : 1,
			"r1" : 0,
			"r2" : 0,
			"r3" : 0,
			"r4" : 0,
			"r5" : 0,
			"r6" : 0,
			"r7" : 0,
			"r8" : 0 }

	def read_register(self, name):
		l.d("Read: {}".format(name), "Registers")
		return self.registers[name]

	def write_register(self, name, value):
		l.d("Write: {}".format(name), "Registers")
		self.registers[name] = value

	def __str__(self):
		out = "Registers:\n"
		for i, r in enumerate(self.registers.keys()):
			out += "[{:>3} = {:>4} ]\t".format(r, self.registers[r])
			if i % 3 == 2: out += "\n"
		return out

class Memory:
	def __init__(self):
		self.memory = [0x00 for word in xrange(32)]

	def read_byte(self, index):
		return self.memory[index]

	def write_byte(self, index, data):
		self.memory[index] = data

	def __str__(self):
		out = "Memory:\n"
		for i, w in enumerate(self.memory):
			out += "[ {:#04x} ] ".format(w)
			if i % 8 == 7: out += "\n"
		return out

class Instruction:
	def __init__(self, op, ra, rb, rc):
		self.op = op
		self.ra = ra
		self.rb = rb
		self.rc = rc

class Stage:
	def __init__(self, name, prev_reg, next_reg):
		self.name = name
		l.v("Stage %s initialized!" % name, "Stage")
		self.prev_reg = prev_reg
		self.next_reg = next_reg

	def prepare(self):
		raise NotImplementedError("Stage {0} has not implemented 'prepare' method!".format(self.name))

	def execute(self):
		raise NotImplementedError("Stage {0} has not implemented 'execute' method!".format(self.name))

	def finalize(self):
		raise NotImplementedError("Stage {0} has not implemented 'finalize' method!".format(self.name))

class IF(Stage):
	'''
	Instruction Fetch
	'''
	def __init__(self, initial, if_id):
		name = "IF"
		Stage.__init__(self, name, initial, if_id)

	def prepare(self):
		self.pc = self.prev_reg["PC"]
		l.e("PC: %d" % self.pc, "IF/prepare")
		self.instruction = self.prev_reg["IM"].get_instruction_at(self.pc)

	def execute(self):
		self.prev_reg["PC"] += 1
		l.e("prev_reg.PC: %d" % self.prev_reg["PC"], "IF/execute")

	def finalize(self):
		self.next_reg["PC"] = self.pc
		self.next_reg["CODOP"] = self.instruction.op
		self.next_reg["RA"] = self.instruction.ra
		self.next_reg["RB"] = self.instruction.rb
		self.next_reg["RC"] = self.instruction.rc

class ID(Stage):
	'''
	Instruction Decode
	'''
	def __init__(self, if_id, id_ex):
		name = "ID"
		Stage.__init__(self, name, if_id, id_ex)

	def prepare(self):
		self.pc = self.prev_reg["PC"]
		self.codop = self.prev_reg["CODOP"]
		self.ra = self.prev_reg["RA"]
		self.rb = self.prev_reg["RB"]
		self.rc = self.prev_reg["RC"]

	def execute(self):
		self.A = self.prev_reg['REG'].read_register(self.ra)
		self.B = self.prev_reg['REG'].read_register(self.rb)
		self.C = self.prev_reg['REG'].read_register(self.rc)

	def finalize(self):
		self.next_reg["PC"] = self.pc
		self.next_reg["CODOP"] = self.codop
		self.next_reg["RA"] = self.ra
		self.next_reg["RB"] = self.rb
		self.next_reg["RC"] = self.rc
		self.next_reg["A"] = self.A
		self.next_reg["B"] = self.B
		self.next_reg["C"] = self.C

class EX(Stage):
	def __init__(self, id_ex, ex_mem):
		name = "EX"
		Stage.__init__(self, name, id_ex, ex_mem)

	def prepare(self):
		self.pc = self.prev_reg["PC"]
		self.codop = self.prev_reg["CODOP"]
		self.ra = self.prev_reg["RA"]
		self.rb = self.prev_reg["RB"]
		self.rc = self.prev_reg["RC"]
		self.A = self.prev_reg["A"]
		self.B = self.prev_reg["B"]
		self.C = self.prev_reg["C"]

	def execute(self):
		if self.codop == "add":
			self.C = self.A + self.B
		elif self.codop == "sub":
			self.C = self.A - self.B
		elif self.codop == "mult":
			self.C = self.A * self.B
		elif self.codop == "trap":
			raise Trap("TRAP")
		else:
			pass

	def finalize(self):
		self.next_reg["PC"] = self.pc
		self.next_reg["CODOP"] = self.codop
		self.next_reg["RA"] = self.ra
		self.next_reg["RB"] = self.rb
		self.next_reg["RC"] = self.rc
		self.next_reg["A"] = self.A
		self.next_reg["B"] = self.B
		self.next_reg["C"] = self.C

class MEM(Stage):
	def __init__(self, ex_mem, mem_wb):
		name = "MEM"
		Stage.__init__(self, name, ex_mem, mem_wb)

class WB(Stage):
	def __init__(self, mem_wb, final):
		name = "WB"
		Stage.__init__(self, name, mem_wb, final)

	def prepare(self):
		self.pc = self.prev_reg["PC"]
		self.codop = self.prev_reg["CODOP"]
		self.ra = self.prev_reg["RA"]
		self.rb = self.prev_reg["RB"]
		self.rc = self.prev_reg["RC"]
		self.A = self.prev_reg["A"]
		self.B = self.prev_reg["B"]
		self.C = self.prev_reg["C"]

	def execute(self):
		self.next_reg["REG"].write_register(self.rc, self.C)

	def finalize(self):
		self.next_reg["PC"] = self.pc
		self.next_reg["CODOP"] = self.codop
		self.next_reg["RA"] = self.ra
		self.next_reg["RB"] = self.rb
		self.next_reg["RC"] = self.rc
		self.next_reg["A"] = self.A
		self.next_reg["B"] = self.B
		self.next_reg["C"] = self.C

class CPU:
	def __init__(self, program_file=None):
		self.registers = Registers()
		self.instructions_memory = InstructionsMemory()
		self.memory = Memory()

		# Registros de desacoplamiento
		initial = { 
			'PC' : 0, 
			'IM' : self.instructions_memory }
		if_id = initial.copy()
		if_id.update({ 
			'CODOP' : 0, 
			'RA' : 0, 
			'RB' : 0, 
			'RC' : 0, 
			'REG' : self.registers })
		id_ex = if_id.copy()
		id_ex.update({
			'A' : 0, 
			'B' : 0, 
			'C' : 0 })
		ex_mem = id_ex.copy()
		ex_mem.update({
			'MEM' : self.memory })
		mem_wb = ex_mem.copy()
		final = mem_wb.copy()
		
		# Setear etapas
		self.stages = [
			IF(initial, if_id), 
			ID(if_id, id_ex), 
			EX(id_ex, ex_mem), 
			WB(ex_mem, final)]

		self.dec_reg = [initial, if_id, id_ex, ex_mem, mem_wb, final]
		
		# Programar
		l.v("Program!", "CPU")
		if program_file != None:
			self.programmer = Programmer(self.instructions_memory)
			for line in open(program_file):
				self.programmer.insert_instruction(line)

	def run(self):
		'''
		Ejecutar el programa en memoria de instrucciones
		'''
		l.v("Run!", "CPU");
		# Ejecución
		trap = False
		ciclo = 1
		while not trap:
			l.c("Ciclo %d" % ciclo, 'RED', "CPU")
			for stage in reversed(self.stages):
				try:
					stage.prepare()
					stage.execute()
					stage.finalize()
				except NotImplementedError as nie:
					l.e(nie, "CPU")
				except Trap:
					trap = True
				except EndOfProgram:
					l.d("No more instructions", "CPU")
					continue
			ciclo += 1
		l.e("TRAP instruction found", "CPU")

if __name__ == '__main__':

	#l.disable()

	program_file = 'program.asm'

	if len(sys.argv) > 1:
		program_file = sys.argv[1]

	cpu = CPU(program_file)
	cpu.run()

	# for dec_reg in cpu.dec_reg:
	# 	print dec_reg
	
	print cpu.registers
	print cpu.memory

	l.v("End!", "Main");
class Byte:
    def format(self, string):
        if len(string) > 8: return string[-8:]
        else: 
            return '0'*(8-len(string)) + string   
    def __init__(self, decimal_value):
        self.binary_string = self.format(bin(decimal_value)[2:])
        self.decimal_value = int(self.binary_string, 2)
    def __repr__(self):
        return self.binary_string
    def __getitem__(self, item):
        return self.binary_string[item]
    def __setitem__(self, item, value):
        self.binary_string = list(self.binary_string)
        self.binary_string[item] = value 
        self.binary_string = ''.join(self.binary_string)
    def __add__(self, other):
        if self.decimal_value + other.decimal_value <= 255:
            return Byte(self.decimal_value + other.decimal_value)
        return Byte(self.decimal_value + other.decimal_value - 256)
    def __sub__(self, other):
        if self.decimal_value >= other.decimal_value:
            return Byte(self.decimal_value - other.decimal_value)
        return Byte(self.decimal_value - other.decimal_value + 256)
    def __and__(self, other):
        return Double(int(self.binary_string+other.binary_string, 2))
    def dec(self):
        return self.decimal_value
    def dec2(self):
        if self.binary_string[0] == '1':
            return self.decimal_value - 256
        else: return self.decimal_value

class Double:
    def format(self, string):
        if len(string) > 16: return string[-16:]
        else: 
            return '0'*(16-len(string)) + string   
    def __init__(self, decimal_value):
        self.binary_string = self.format(bin(decimal_value)[2:])
        self.decimal_value = int(self.binary_string, 2)
    def __repr__(self):
        return self.binary_string
    def __getitem__(self, item):
        return self.binary_string[item]
    def __add__(self, other):
        return Double(self.decimal_value + other.decimal_value)
    def __sub__(self, other):
        if self.decimal_value > other.decimal_value:
            return Double(self.decimal_value - other.decimal_value)
        return Double(self.decimal_value - other.decimal_value + 256)
    def dec(self):
        return self.decimal_value
    def to_byte(self):
        return [Byte(int(self.binary_string[:8], 2)), Byte(int(self.binary_string[8:], 2))]
    def to_hex(self):
        return hex(self.decimal_value)[2:]
A = '000'; B = '001'; C = '010'; FP = '011'; SP = '100'; HPC = '101'; LPC = '110'; F = '111'
class CPU():
    def __init__(self, program):
        for i in range(len(program)):
            self.ram.append(Byte(program[i]))
    ram = []
    registers = {'000': Byte(0), '001': Byte(0), '010': Byte(0), '011': Byte(0), '100': Byte(0), '101': Byte(0), '110': Byte(0), '111': Byte(0)}   
    halt = False
    output = None
    signed_output = False
    def reset(self):
        self.registers = {'000': Byte(0), '001': Byte(0), '010': Byte(0), '011': Byte(0), '100': Byte(0), '101': self.ram[0], '110': self.ram[1], '111': Byte(0)}   
        self.AB = self.registers[A] & self.registers[B]
        self.halt = False
        self.output = None
    def advance(self):
        self.outputCall = False
        address = (self.registers[HPC] & self.registers[LPC]).dec()
        self.old_address = address # for display
        next_address = address
        instruction = self.ram[address]
        next_byte = self.ram[address + 1]
        next_next_byte = self.ram[address + 2]
        opcode = instruction[:4]
        mode = instruction[4]
        reg0 = instruction[5:]
        reg1 = next_byte[-3:]
        jump = False
        AB = self.registers[A] & self.registers[B]
        match opcode:
            case '0000': # ldw
                if mode == '0':
                    self.registers[reg0] = self.ram[(next_byte & next_next_byte).dec()]
                    next_address += 3
                else:
                    self.registers[reg0] = self.ram[next_byte.dec()]
                    next_address += 2
            case '0001': # stw
                if mode == '0':
                    self.ram[(next_byte & next_next_byte).dec()] = self.registers[reg0]
                    next_address += 3
                else:
                   self.ram[next_byte.dec()] = self.registers[reg0]
                   next_address += 2
            case '0010': # mvw
                if mode == '0':
                    self.registers[reg0] = self.registers[reg1]
                    next_address += 2
                else:
                    self.registers[reg0] = self.ram[AB.dec()]
                    next_address += 1
            case '0011': # add
                self.registers[F] = Byte(0)
                termA = self.registers[reg0]
                if mode == '0':
                    termB = self.registers[reg1]
                if mode == '1':
                    termB = next_byte
                result = termA + termB
                self.registers[reg0] = result
                if termA[0] == termB[0] != result[0]: # set overflow bit
                    self.registers[F][2] = '1'
                if termA.dec() + termB.dec() > 255: # set carry bit
                    self.registers[F][3] = '1'
                if result.dec() == 0: # set zero bit
                    self.registers[F][0] = '1'
                if result[0] == '0': # set positive bit
                    self.registers[F][6] = '1'
                if result[0] == '1' or result.dec() == 0: # set negative bit
                    self.registers[F][7] = '1'                 
                next_address += 2
            case '0100': # adc
                self.registers[F] = Byte(0)
                termA = self.registers[reg0]
                if mode == '0':
                    termB = self.registers[reg1]
                if mode == '1':
                    termB = next_byte
                result = termA + termB + Byte(int(self.registers[F][3]))
                self.registers[reg0] = result
                if termA[0] == termB[0] != result[0]: 
                    self.registers[F][2] = '1'
                if termA.dec() + termB.dec() + int(self.registers[F][3]) > 255:
                    self.registers[F][3] = '1'
                if result.dec() == 0:
                    self.registers[F][0] = '1'
                if result[0] == '0':
                    self.registers[F][6] = '1'
                if result[0] == '1' or result.dec() == 0:
                    self.registers[F][7] = '1'                 
                next_address += 2
            case '0101': # sub
                self.registers[F] = Byte(0)
                termA = self.registers[reg0]
                if mode == '0':
                    termB = self.registers[reg1]
                if mode == '1':
                    termB = next_byte
                result = termA - termB
                self.registers[reg0] = result
                if termA[0] == termB[0] != result[0]: 
                    self.registers[F][2] = '1'
                if termA.dec() - termB.dec() < 0:
                    self.registers[F][4] = '1'
                if result.dec() == 0: 
                    self.registers[F][0] = '1'
                if result[0] == '0':
                    self.registers[F][6] = '1'
                if result[0] == '1' or result.dec() == 0:
                    self.registers[F][7] = '1'                 
                next_address += 2
            case '0110': # sbb
                self.registers[F] = Byte(0)
                termA = self.registers[reg0]
                if mode == '0':
                    termB = self.registers[reg1]
                if mode == '1':
                    termB = next_byte
                result = termA - termB - Byte(int(self.registers[F][4]))
                self.registers[reg0] = result
                if termA[0] == termB[0] != result[0]: 
                    self.registers[F][2] = '1'
                if termA.dec() - termB.dec() - int(self.registers[F][4]) < 0: 
                    self.registers[F][4] = '1'
                if result.dec() == 0:
                    self.registers[F][0] = '1'
                if result[0] == '0':
                    self.registers[F][6] = '1'
                if result[0] == '1' or result.dec() == 0:
                    self.registers[F][7] = '1'                
                next_address += 2
            case '0111': # iec
                self.registers[F] = Byte(0)
                if mode == '0':
                    termA = self.registers[reg0]
                    result = termA + Byte(1)
                    self.registers[reg0] = result
                    if termA[0] != result[0]: 
                        self.registers[F][2] = '1'
                    if termA.dec() + 1 > 255: 
                        self.registers[F][3] = '1'
                if mode == '1':
                    termA = self.registers[reg0]
                    result = termA - Byte(1)
                    self.registers[reg0] = result
                    if termA[0] != result[0]: 
                        self.registers[F][2] = '1'
                    if termA.dec() - 1 < 0: 
                        self.registers[F][3] = '1'
                if result.dec() == 0:
                    self.registers[F][0] = '1'
                if result[0] == '0':
                    self.registers[F][6] = '1'
                if result[0] == '1' or result.dec() == 0:
                    self.registers[F][7] = '1'
                next_address += 1
            case '1000': # cmp
                self.registers[F] = Byte(0)
                termA = self.registers[reg0]
                if mode == '0':
                    termB = self.registers[reg1]
                if mode == '1':
                    termB = next_byte
                if termA.dec() == 0: # zero flag
                    self.registers[F][0] = '1'
                if termA == termB: # equal flag
                    self.registers[F][1] = '1'
                if termA.dec() < termB.dec(): # less flag
                    self.registers[F][5] = '1'
                if termA[0] == '0': # positive flag
                    self.registers[F][6] = '1'
                if termA[0] == '1' or termA.dec() == 0: # negative flag
                    self.registers[F][7] = '1'
                next_address += 2
            case '1001': # jnz
                if self.registers[F][0] == '0':
                    if mode == '0':
                        self.registers[HPC] = next_byte
                        self.registers[LPC] = next_next_byte
                    if mode == '1':
                        self.registers[HPC] = self.registers[A]
                        self.registers[LPC] = self.registers[B]
                    jump = True
                else:
                    next_address += 3
            case '1010': # push
                self.registers[SP] += Byte(1)
                if mode == '0':
                    self.ram[self.registers[SP].dec()+65280] = self.registers[reg0]
                    next_address += 1
                if mode == '1':
                    self.ram[self.registers[SP].dec()+65280] = next_byte
                    next_address += 2
            case '1011': # pop
                if mode == '0':
                    self.registers[reg0] = self.ram[self.registers[SP].dec()+65280]
                    next_address += 1
                if mode == '1':
                    self.ram[(next_byte & next_next_byte).dec()] = self.ram[self.registers[SP].dec()+65280]
                    next_address += 3
                self.registers[SP] -= Byte(1)
            case '1100': # bsl
                if mode == '0':
                    self.registers[reg0] = Byte(self.registers[reg0].dec()<<1)
                if mode == '1':
                    self.registers[A] = Double((self.registers[A] & self.registers[B]).dec()<<1).to_byte()[0]
                    self.registers[B] = Double((self.registers[A] & self.registers[B]).dec()<<1).to_byte()[1]
                next_address += 1
            case '1101': # bsr
                if mode == '0':
                    self.registers[reg0] = Byte(self.registers[reg0].dec()>>1)
                if mode == '1':
                    self.registers[A] = Double((self.registers[A] & self.registers[B]).dec()>>1).to_byte()[0]
                    self.registers[B] = Double((self.registers[A] & self.registers[B]).dec()>>1).to_byte()[1]
                next_address += 1
            case '1110': # out
                self.output = self.registers[reg0]
                if mode == '0':
                    self.signed_output = False
                if mode == '1':
                    self.signed_output = True
                next_address += 1
                self.outputCall = True # for display
            case '1111': # halt
                self.halt = True
        if not jump:
            self.registers[HPC] = Double(next_address).to_byte()[0]
            self.registers[LPC] = Double(next_address).to_byte()[1]          
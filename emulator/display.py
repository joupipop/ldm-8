import time
import emulator
from sys import argv
try:
    with open(argv[1], 'rb') as file:
        program = file.read()
except Exception as e:
    print(f"error: {e}")

if '--display' in argv:
    display = True
else: display = False
if '--speed' in argv:
    cps_mhz = float(argv[argv.index('--speed')+1])
else: cps_mhz = 1
if '--step' in argv:
    step_by_step = True
else: step_by_step = False

def sleep():
        if step_by_step:
             input()
        else:
            time.sleep(1/(cps_mhz*1_000_000))
print('\x1b[?25l')
while len(program) != 2**16:
     program += b'\x00'
LDM = emulator.CPU(program)
def pad(num, char, length):
     return char*(length-len(str(num))) + str(num)
old_address = None
def genframe(CPU):
    if CPU.output is not None:
        if CPU.signed_output is True:
            output = pad(CPU.output.dec2(), ' ', 4)
        else: output = pad(CPU.output.dec(), ' ', 4)
    else: output = '   0'
    A = pad(LDM.registers['000'].dec(), ' ', 3)
    A2 = ' ' + pad(LDM.registers['000'].dec2(), ' ', 4)
    B = pad(LDM.registers['001'].dec(), ' ', 3)
    B2 = ' ' + pad(LDM.registers['001'].dec2(), ' ', 4)
    C = pad(LDM.registers['010'].dec(), ' ', 3)
    C2 = ' ' + pad(LDM.registers['010'].dec2(), ' ', 4)
    address = CPU.old_address
    hex_address = '0x' + pad(hex(CPU.ram[address+1].dec())[2:], '0', 4)
    hex_address0 = '0x' + pad(hex(address)[2:], '0', 4)
    hex_address1 = '0x' + pad(hex(address+1)[2:], '0', 4)
    hex_address2 = '0x' + pad(hex(address+2)[2:], '0', 4)
    hex_address3 = '0x' + pad(hex(address+3)[2:], '0', 4)
    hex_address4 = '0x' + pad(hex(address+4)[2:], '0', 4)
    stack_address = CPU.registers['100'].dec()+65280
    stack = [CPU.ram[stack_address], CPU.ram[stack_address-1], CPU.ram[stack_address-2], CPU.ram[stack_address-3], CPU.ram[stack_address-4], CPU.ram[stack_address-5], CPU.ram[stack_address-6]]
    next_byte = CPU.ram[CPU.ram[address+1].dec()]
    registers = {'000': 'a', '001': 'b', '010': 'c', '011': 'fp', '100': 'sp', '101': 'hpc', '110': 'lpc', '111': 'f'}
    match CPU.ram[address][:4]:
        case '0000':
            instruction = 'ldw'
            if CPU.ram[address][4] == '1':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', 0x'+pad((emulator.Byte(0)&CPU.ram[address+1]).to_hex(), '0' ,4)
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', 0x'+pad((CPU.ram[address+1]&CPU.ram[address+2]).to_hex(), '0' ,4)
            instruction += ' '*(15-len(instruction))
        case '0001':
            instruction = 'stw'
            if CPU.ram[address][4] == '1':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', 0x'+pad((emulator.Byte(0)&CPU.ram[address+1]).to_hex(), '0' ,4)
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', 0x'+pad((CPU.ram[address+1]&CPU.ram[address+2]).to_hex(), '0' ,4)
            instruction += ' '*(15-len(instruction))
        case '0010':
            instruction = 'mvw'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', '+registers[CPU.ram[address+1][-3:]]
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', *ab'
            instruction += ' '*(15-len(instruction))
        case '0011':
            instruction = ' add'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', '+registers[CPU.ram[address+1][-3:]]
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', '+str(CPU.ram[address+1].dec())
            instruction += ' '*(15-len(instruction))
        case '0100':
            instruction = ' adc'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', '+registers[CPU.ram[address+1][-3:]]
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', '+str(CPU.ram[address+1].dec())        
            instruction += ' '*(15-len(instruction))
        case '0101':
            instruction = ' sub'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', '+registers[CPU.ram[address+1][-3:]]
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', '+str(CPU.ram[address+1].dec())
            instruction += ' '*(15-len(instruction))
        case '0110':
            instruction = ' sbb'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', '+registers[CPU.ram[address+1][-3:]]
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', '+str(CPU.ram[address+1].dec())    
            instruction += ' '*(15-len(instruction))
        case '0111':
            if CPU.ram[address][4] == '0':
                instruction = ' inc '+registers[CPU.ram[address][-3:]]
            else: instruction = ' dec '+registers[CPU.ram[address][-3:]]
            instruction += ' '*(15-len(instruction))
        case '1000':
            instruction = ' cmp'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]+', '+registers[CPU.ram[address+1][-3:]]
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', '+str(CPU.ram[address+1].dec())
            instruction += ' '*(15-len(instruction))
        case '1001':
            instruction = ' jnz'
            if CPU.ram[address][4] == '0':
                instruction += ' 0x'+pad((CPU.ram[address+1]&CPU.ram[address+2]).to_hex(), '0' ,4)
            else: instruction += ' ab'
            instruction += ' '*(15-len(instruction))
        case '1010':
            instruction = ' push'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]
            else: instruction += ' '+str(CPU.ram[address+1].dec())
            instruction += ' '*(15-len(instruction))
        case '1011':
            instruction = ' pop'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]
            else: instruction += ' 0x'+pad((CPU.ram[address+1]&CPU.ram[address+2]).to_hex(), '0' ,4)
            instruction += ' '*(15-len(instruction))       
        case '1100':
            instruction = ' bsl'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]
            else: instruction += ' ab'
            instruction += ' '*(15-len(instruction))
        case '1101':
            instruction = ' bsr'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]
            else: instruction += ' ab'
            instruction += ' '*(15-len(instruction))        
        case '1110':
            instruction = ' out'
            if CPU.ram[address][4] == '0':
                instruction += ' '+registers[CPU.ram[address][-3:]]
            else: instruction += ' '+registers[CPU.ram[address][-3:]]+', -'
            instruction += ' '*(15-len(instruction))
        case '1111':
            instruction = ' halt          '
    print(f'╭Registers────────╮   ╭Output╮   ╭Instruction────╮')
    print(f'│ A :  {A} |{A2} │   │ {output} │   │{instruction}│')
    print(f'│ B :  {B} |{B2} │   ╰──────╯   ╰───────────────╯ ')
    print(f'│ C :  {C} |{C2} │                               ')
    print(f'╰─────────────────╯                      •          ')
    print(f'╭Flags────────────╮                      •	    ')
    print(f'│ '+"\u001b[31m"*int(CPU.registers['111'][0])+'Z\u001b[97m',"\u001b[31m"*int(CPU.registers['111'][1])+'E\u001b[97m', "\u001b[31m"*int(CPU.registers['111'][2])+'O\u001b[97m', "\u001b[31m"*int(CPU.registers['111'][3])+'C\u001b[97m', "\u001b[31m"*int(CPU.registers['111'][4])+'B\u001b[97m', "\u001b[31m"*int(CPU.registers['111'][5])+'L\u001b[97m', "\u001b[31m"*int(CPU.registers['111'][6])+'P\u001b[97m', "\u001b[31m"*int(CPU.registers['111'][7])+'N\u001b[97m'+' │                      •         ') # print(f'│ Z E O C B L P N │                      •         ')
    print(f'╰─────────────────╯              ├RAM────────────┤ ')
    print(f' fp \u001b[31m■\u001b[97m                     {hex_address} │ {next_byte} | AF │ ')
    print(f' ╭Stack──────────╮               ├───────────────┤ ')
    print(f' '+"\u001b[31m"*int(CPU.registers['011'].dec()+65280==stack_address)+f'│ \u001b[97m{stack[0]} | {pad(hex(stack[0].dec())[2:].capitalize(), "0", 2)} │                       •           ')
    print(f' ├───────────────┤                       •           ')
    print(f' '+"\u001b[31m"*int(CPU.registers['011'].dec()+65280==stack_address-1)+f'│ \u001b[97m{stack[1]} | {pad(hex(stack[1].dec())[2:].capitalize(), "0", 2)} │                       •           ')
    print(f' ├───────────────┤               ├───────────────┤  ')
    print(f' '+"\u001b[31m"*int(CPU.registers['011'].dec()+65280==stack_address-2)+f'│ \u001b[97m{stack[2]} | {pad(hex(stack[2].dec())[2:].capitalize(), "0", 2)} │      ▶ {hex_address0} │ {CPU.ram[address]} | {pad(hex(CPU.ram[address].dec())[2:].capitalize(), "0", 2)} │ ◀')
    print(f' ├───────────────┤               ├───────────────┤  ')
    print(f' '+"\u001b[31m"*int(CPU.registers['011'].dec()+65280==stack_address-3)+f'│ \u001b[97m{stack[3]} | {pad(hex(stack[3].dec())[2:].capitalize(), "0", 2)} │        {hex_address1} │ {CPU.ram[address+1]} | {pad(hex(CPU.ram[address+1].dec())[2:].capitalize(), "0", 2)} │ ')
    print(f' ├───────────────┤               ├───────────────┤ ')
    print(f' '+"\u001b[31m"*int(CPU.registers['011'].dec()+65280==stack_address-4)+f'│ \u001b[97m{stack[4]} | {pad(hex(stack[4].dec())[2:].capitalize(), "0", 2)} │        {hex_address2} │ {CPU.ram[address+2]} | {pad(hex(CPU.ram[address+2].dec())[2:].capitalize(), "0", 2)} │ ')
    print(f' ├───────────────┤     	         ├───────────────┤')
    print(f' '+"\u001b[31m"*int(CPU.registers['011'].dec()+65280==stack_address-5)+f'│ \u001b[97m{stack[5]} | {pad(hex(stack[5].dec())[2:].capitalize(), "0", 2)} │        {hex_address3} │ {CPU.ram[address+3]} | {pad(hex(CPU.ram[address+3].dec())[2:].capitalize(), "0", 2)} │')
    print(f' ├───────────────┤               ├───────────────┤')
    print(f' '+"\u001b[31m"*int(CPU.registers['011'].dec()+65280==stack_address-6)+f'│ \u001b[97m{stack[6]} | {pad(hex(stack[6].dec())[2:].capitalize(), "0", 2)} │        {hex_address4} │ {CPU.ram[address+4]} | {pad(hex(CPU.ram[address+4].dec())[2:].capitalize(), "0", 2)} │')
    print(f' ├───────────────┤               ├───────────────┤')
    print(f'        •                                •')
    print(f'        •                                •')
    print(f'        •                                •')

def run(CPU):
    print("\033c\033[3J")
    CPU.reset()
    while CPU.halt is False:
        
        if display:
            print("\033c\033[3J")
            CPU.advance()
            genframe(CPU)
        else:
            CPU.advance()
            if CPU.outputCall:
                if CPU.signed_output is True:
                    output = str(CPU.output.dec2())+'\n'
                else: output = str(CPU.output.dec())+'\n'
            else: output = ''
            print(output, end = '')            
        if CPU.halt:
            print('Computer halted.')
            break
        sleep()

LDM.reset()
run(LDM)
print('\x1b[?25h')
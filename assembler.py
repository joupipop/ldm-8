# CASM (Custom Assembler)
# RUN: $ casm input.asm output

from sys import argv
try:
    with open(argv[1], 'r') as file:
        code = file.read()
except Exception as e:
    print(f"error: {e}")

registers = {'a': '000', 'b': '001', 'hfp': '010', 'lfp': '011', 'sp': '100', 'hpc': '101', 'lpc': '110', 'f': '111'}

def pad(string, length, character):
    while len(string) < length:
        string = character + string
    return string
def assemble(code):
    variables = {}
    labels = {}
    expected_labels = {}
    macros = {}
    binary_data = b''
    start_address = 0
    binary_code = b''
    code = code.split('\n')[:-1]
    include_len = -1
    i = 0
    while i < len(code):
        command = code[i].strip()
        
        if ';' in command:
            command = command.replace(command[command.index(';'):], '')
            command = command.strip()
        if command == '':
            i += 1
        elif command[0] == '@' and command != '@endmacro': # DIRECTIVE
            if ' ' in command:
                directive = command[1:command.index(' ')]
                arguments = command[command.index(' ')+1:].split(' ')
                arguments_temp = []
                for arg in arguments:
                    if arg != '':
                        arguments_temp.append(arg)
                arguments = arguments_temp 
            else: 
                directive = command[1:]
                arguments = [0]
            j = i
            match directive:
                case 'db':
                    if len(arguments) == 2:
                        if arguments[0].isidentifier() and arguments[0] not in registers:
                            if arguments[1].isdigit():
                                if int(arguments[1]) < 256:
                                    variables[arguments[0]] = len(binary_data) + 2
                                    binary_data += bytes.fromhex(pad(hex(int(arguments[1]))[2:], 2, '0'))
                                else: print(f'\'{command}\' error: {arguments[1]} is larger then 255. (line {i+1})')
                            else: print(f'\'{command}\' error: expected number, got {arguments[1]}. (line {i+1})'); break
                        else: print(f'\'{command}\' error: expected identifier, got {arguments[0]}')
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i+1})'); break
                case 'dw':
                    if len(arguments) == 2:
                        if arguments[0].isidentifier() and arguments[0] not in registers:
                            if arguments[1].isdigit():
                                if int(arguments[1]) < 256:
                                    variables[arguments[0]] = len(binary_data) + 2
                                    binary_data += bytes.fromhex(pad(hex(int(arguments[1]))[2:], 4, '0'))
                                else: print(f'\'{command}\' error: {arguments[1]} is larger then 255. (line {i+1})'); break
                            else: print(f'\'{command}\' error: expected number, got {arguments[1]}. (line {i+1})'); break
                        else: print(f'\'{command}\' error: expected identifier, got {arguments[0]}'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i+1})'); break
                case 'dd':
                    if len(arguments) == 2:
                        if arguments[0].isidentifier() and arguments[0] not in registers:
                            if arguments[1].isdigit():
                                if int(arguments[1]) < 256:
                                    variables[arguments[0]] = len(binary_data) + 2
                                    binary_data += bytes.fromhex(pad(hex(int(arguments[1]))[2:], 8, '0'))
                                else: print(f'\'{command}\' error: {arguments[1]} is larger then 255. (line {i+1})'); break
                            else: print(f'\'{command}\' error: expected number, got {arguments[1]}. (line {i+1})'); break
                        else: print(f'\'{command}\' error: expected identifier, got {arguments[0]}'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i+1})'); break
                case 'macro':
                    if len(arguments) == 2:
                        if arguments[0].isidentifier() and arguments[0] not in registers:
                            if arguments[1].isdigit():
                                while code[j] != '@endmacro':
                                    j += 1
                                macros[arguments[0]] = [arguments[1],'\n'.join(code[i+1:j])]
                            else: print(f'\'{command}\' error: expected number of arguments got {arguments[1]}')
                        else: print(f'\'{command}\' error: expected macro name got {arguments[0]}')
                    else: print(f'\'{command}\' error: expected 2 arguments got {len(arguments)}')
                case 'include':
                    file = arguments[0]
                    try:
                        with open(file, 'r') as file:
                            included_code = file.read()
                    except Exception as e:
                        print(f"\'{command}\' error: {e} (line {i+1})")
                    included_code = included_code.split('\n')
                    include_len += len(included_code)
                    code = code[:i] + included_code + code[i+1:]
                    j -= 1
                case 'start':
                    start_address = len(binary_code)

            i = j + 1
        elif command[-1] == ':': # LABEL
            label_name = command[:-1].split(' ')
            if len(label_name) == 1:
                if label_name[0] in expected_labels:
                    labels[label_name[0]] = 2 + len(binary_data) + len(binary_code)
                    binary_code = list(binary_code)
                    binary_code[expected_labels[label_name[0]][0]] = int(pad(bin(2 + len(binary_data) + len(binary_code))[2:], 16, '0')[:9], 2)
                    binary_code[expected_labels[label_name[0]][0]+1] = int(pad(bin(2 + len(binary_data) + len(binary_code))[2:], 16, '0')[9:], 2)
                    binary_code = bytes(binary_code)
                    del expected_labels[label_name[0]]
                labels[label_name[0]] = 2 + len(binary_data) + len(binary_code)
            else: print(f'\'{command}\' error: unexpected \'{" ".join(label_name[1:])}\'. (line {i-include_len+1})')
            i += 1
        else: # INSTRUCTION
            if ' ' in command:
                operation = command[0:command.index(' ')]
                arguments = command[command.index(' '):].replace(' ', '').split(',')
            else: 
                operation = command
                arguments = []
            match operation:
                case 'ldw':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if (arguments[1] in variables and arguments[1] not in registers) or arguments[1] == '*ab': # CHECK VARIABLE ARGUMENT 
                                command_bytes = '0000'
                                if arguments[1] == '*ab':
                                    command_bytes += '1' 
                                    command_bytes += registers[arguments[0]] 
                                    binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                                else: 
                                    command_bytes += '0'
                                    command_bytes += registers[arguments[0]]
                                    command_bytes += pad(str(bin(variables[arguments[1]])[2:]), 16, '0')
                                    binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 6, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected variable, got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break    
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'stw':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if (arguments[1] in variables and arguments[1] not in registers) or arguments[1] == '*ab': # CHECK VARIABLE ARGUMENT 
                                command_bytes = '0001'
                                if arguments[1] == '*ab': # ZERO PAGE ADDRESSING
                                    command_bytes += '1'
                                    command_bytes += registers[arguments[0]]
                                    binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                                else: 
                                    command_bytes += '0'
                                    command_bytes += registers[arguments[0]]
                                    command_bytes += pad(str(bin(variables[arguments[1]])[2:]), 8, '0')
                                    binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 6, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: variable, got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'mvw':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if arguments[1] in registers: # CHECK SECOND REGISTER ARGUMENT
                                command_bytes = '0010'
                                command_bytes += '0'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(registers[arguments[1]], 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            elif arguments[1].isdigit() and int(arguments[1]) < 256:
                                command_bytes = '0010'
                                command_bytes += '1'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(str(bin(int(arguments[1]))[2:]), 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected register or imm8, got {arguments[1]}. (line {i-include_len+1})'); break   
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'add':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if arguments[1] in registers: # CHECK SECOND ARGUMENT
                                command_bytes = '0011'
                                command_bytes += '0'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(registers[arguments[1]], 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            elif arguments[1].isdigit() and int(arguments[1]) < 256:
                                command_bytes = '0011'
                                command_bytes += '1'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(str(bin(int(arguments[1]))[2:]), 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected register or number(<256), got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'adc':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if arguments[1] in registers: # CHECK SECOND ARGUMENT
                                command_bytes = '0100'
                                command_bytes += '0'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(registers[arguments[1]], 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            elif arguments[1].isdigit() and int(arguments[1]) < 256:
                                command_bytes = '0100'
                                command_bytes += '1'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(str(bin(int(arguments[1]))[2:]), 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected register or number(<256), got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break                        
                case 'sub':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if arguments[1] in registers: # CHECK SECOND ARGUMENT
                                command_bytes = '0101'
                                command_bytes += '0'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(registers[arguments[1]], 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            elif arguments[1].isdigit() and int(arguments[1]) < 256:
                                command_bytes = '0101'
                                command_bytes += '1'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(str(bin(int(arguments[1]))[2:]), 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected register or number(<256), got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'sbb':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if arguments[1] in registers: # CHECK SECOND ARGUMENT
                                command_bytes = '0110'
                                command_bytes += '0'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(registers[arguments[1]], 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            elif arguments[1].isdigit() and int(arguments[1]) < 256:
                                command_bytes = '0110'
                                command_bytes += '1'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(str(bin(int(arguments[1]))[2:]), 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected register or number(<256), got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'inc':
                    if len(arguments) == 1: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            command_bytes = '0111'
                            command_bytes += '0'
                            command_bytes += registers[arguments[0]]
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'dec':
                    if len(arguments) == 1: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            command_bytes = '0111'
                            command_bytes += '1'
                            command_bytes += registers[arguments[0]]
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break                        
                case 'cmp':
                    if len(arguments) == 2: # CHECK ARGUMENT LENGTH
                        if arguments[0] in registers: # CHECK REGISTER ARGUMENT
                            if arguments[1] in registers: # CHECK SECOND ARGUMENT
                                command_bytes = '1000'
                                command_bytes += '0'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(registers[arguments[1]], 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            elif arguments[1].isdigit():
                                command_bytes = '1000'
                                command_bytes += '1'
                                command_bytes += registers[arguments[0]]
                                command_bytes += pad(str(bin(int(arguments[1]))[2:]), 8, '0')
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected register or number, got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 2 arguments, got {len(arguments)}. (line {i-include_len+1})'); break                        
                case 'jnz':
                    if len(arguments) == 1:
                        if arguments[0] in labels:
                            command_bytes = '1001'
                            command_bytes += '0'
                            command_bytes += '000'
                            command_bytes += pad(str(bin(labels[arguments[0]])[2:]), 16, '0')
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        elif arguments[0] == 'ab':
                            command_bytes = '1001'
                            command_bytes += '1'
                            command_bytes += '000'
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        else:
                            expected_labels[arguments[0]] = [1 + len(binary_data) + len(binary_code), i+1]
                            command_bytes = '1001'
                            command_bytes += '0'
                            command_bytes += '000'
                            command_bytes += '0000000000000000'
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0'))
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'push':
                    if len(arguments) == 1:
                        if arguments[0] in registers:
                            command_bytes = '1010'
                            command_bytes += '0'
                            command_bytes += registers[arguments[0]]
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        elif arguments[0] in variables:
                            command_bytes = '1010'
                            command_bytes += '1'
                            command_bytes += '000'
                            command_bytes += pad(str(bin(int(variables[arguments[0]]))[2:]), 16, '0')
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        else: print(f'\'{command}\' error: expected register or number(<256), got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'pop':
                    if len(arguments) == 1:
                        if arguments[0] in registers:
                            command_bytes = '1011'
                            command_bytes += '0'
                            command_bytes += registers[arguments[0]]
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        elif arguments[0] in variables:
                            command_bytes = '1011'
                            command_bytes += '1'
                            command_bytes += '000'
                            command_bytes += pad(str(bin(int(variables[arguments[0]]))[2:]), 16, '0')
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 4, '0')) # 0110 → \x06
                        else: print(f'\'{command}\' error: expected register or variable, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'bsl':
                    if len(arguments) == 1:
                        if arguments[0] in registers:
                            command_bytes = '1100'
                            command_bytes += '0'
                            command_bytes += registers[arguments[0]]
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        elif arguments[0] == 'ab':
                            command_bytes = '1100'
                            command_bytes += '1'
                            command_bytes += '000'
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        else: print(f'\'{command}\' error: expected register or \'ab\', got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'bsr':
                    if len(arguments) == 1:
                        if arguments[0] in registers:
                            command_bytes = '1101'
                            command_bytes += '0'
                            command_bytes += registers[arguments[0]]
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        elif arguments[0] == 'ab':
                            command_bytes = '1101'
                            command_bytes += '1'
                            command_bytes += '000'
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0'))
                        else: print(f'\'{command}\' error: expected register or \'ab\', got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'out':
                    if len(arguments) == 1:
                        if arguments[0] in registers:
                            command_bytes = '1110'
                            command_bytes += '0'
                            command_bytes += registers[arguments[0]]
                            binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    elif len(arguments) == 2:
                        if arguments[0] in registers:
                            if arguments[1] == '-':
                                command_bytes = '1110'
                                command_bytes += '1'
                                command_bytes += registers[arguments[0]]
                                binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                            else: print(f'\'{command}\' error: expected \'-\', got {arguments[1]}. (line {i-include_len+1})'); break
                        else: print(f'\'{command}\' error: expected register, got {arguments[0]}. (line {i-include_len+1})'); break
                    else: print(f'\'{command}\' error: expected 1 argument, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'halt':
                    if len(arguments) == 0:
                        command_bytes = '11110000'
                        binary_code += bytes.fromhex(pad(hex(int('0b'+command_bytes, 2))[2:], 2, '0')) # 0110 → \x06
                    else: print(f'\'{command}\' error: expected 0 arguments, got {len(arguments)}. (line {i-include_len+1})'); break
                case 'restoreLabels':
                    labels = save_labels
                case _:
                    if operation in macros:
                        if len(arguments) == int(macros[operation][0]):
                            macro_code = macros[operation][1]
                            while '%' in macro_code:
                                macro_code = macro_code.replace(macro_code[macro_code.index('%'):macro_code.index('%')+2], arguments[int(macro_code[macro_code.index('%')+1])])
                            macro_code = macro_code.split('\n')
                            del code[i]
                            include_len += len(macro_code)
                            code = code[:i] + macro_code + ['restoreLabels'] + code[i:]
                            save_labels = labels
                            i -= 1
                        else: print(f'\'{command}\' error: expected {macros[operation][0]} arguments, got {len(arguments)}. (line {i-include_len+1})')
                    else: print(f'\'{command}\' error: unknown instruction {operation} (line {i-include_len+1})')
            i += 1
    if len(expected_labels) != 0:
        print(f'\'{command}\' error: expected address label, got \'{list(expected_labels)[0]}\'. (line {expected_labels[list(expected_labels)[0]][1]})')
    binary = bytes.fromhex(pad(str(hex(len(binary_data)+2+start_address)[2:]), 4, '0')) + binary_data + binary_code
    return binary

machine_code = assemble(code)
try:
    with open(argv[2], "wb") as binary_file:    
        binary_file.write(machine_code)
except Exception as e:
    print(f'error: {e}')

print(f'Succesfully wrote to \'{argv[2]}\'. ({len(machine_code)} bytes)')

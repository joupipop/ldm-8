from sys import argv
import numpy as np # for floating point generation



try:
    with open(argv[1], 'r') as file:
        input_file = file.read()
        file.close()
except Exception as e:
    print(f"error: {e}")


macroTable = {}
symbolTable = []
addressTable = []
discoveredSymbolTable = []
constTable = {}
literalTable = {"HPC": [0, 0, 1], "LPC": [1, 0, 1]}
branchTable = []
startAddress = 2
instructions = {"ldw": 0, "stw": 0, "mvw": 2, "add": 2, 
                "adc": 2, "sub": 2, "sbb": 2, "inc": 1,
                "dec": 1, "cmp": 2, "jnz": 0, "push": 0,
                "pop": 0, "bsl": 1, "bsr": 1, "out": 1,
                "halt": 1}
# {"instruction": byte_length} 0: undetermined byte_length
registers = {'a': "000", 'b': "001", 'c': "010", 'd': "011", 
             'hfp': "100", 'lfp': "101", 'sp': "110", 'f': "111"}


def make_number8(string):
    if string in constTable:
        return constTable[string] % 256
    if string[-1] == ']':
        if string[string.index('[')+1:-1] == '0':
            return constTable[string[:string.index('[')]] >> 8
        if string[string.index('[')+1:-1] == '1':
            return ((constTable[string[:string.index('[')]] << 8) % 65536) >> 8

    if string[:2] == "0x":
        return int(string, 16) % 256
    elif string[:2] == "0b":
        return int(string, 2) % 256
    else:        
        return int(string, 10) % 256
def make_number16(string):
    if string[:2] == "0x":
        return int(string, 16) % 65536
    elif string[:2] == "0b":
        return int(string, 2) % 65536
    elif '.' not in string:
        return int(string, 10) % 65536
    num = float(string)
    if num < 0:
        return (np.asarray(abs(num), dtype=np.float16).view(np.int16).item() + 32768) % 65536
    else:
        return np.asarray(abs(num), dtype=np.float16).view(np.int16).item() % 65536


def includepass(input_file):
    included_code = []
    try:
        code = input_file.split("\n")
        for i in range(len(code)):
            line = code[i]
            if line[:8] == "@include":
                #del output_code[output_code.index(line)]
                with open(line.split(" ")[1], "r") as file:
                    included_file = file.read()
                    file.close()
                included_code += included_file.split("/n")
            elif line.isspace():
                pass
            else:
                break
    except Exception as e:
        print("error:", line, e)
        exit()
    output_code = included_code + ["@start"] + code[i:]
    return "\n".join(output_code)
def pass0(input_file):
    code = input_file.split("\n")
    output_code = []
    in_macro = False
    current_macro_name = ""
    for line in code:
        line = line.strip()
        if ';' in line:
            line = line.replace(line[line.index(';'):], '')
            line = line.strip()
        if line == '':
            continue
        if in_macro:
            if line[:6] == "@macro":
                print("error:", line)
                exit()
            elif line == "@endmacro":
                in_macro = False
            else:
                macroTable[current_macro_name][1].append(line)
        else:
            if line [:6] == "@const":
                try:
                    constTable[line.split(" ")[1]] = make_number16(line.split(" ")[2])
                except Exception:
                    print("error:", line)
            if line[:6] == "@macro":
                try:
                    macroTable[line.split(" ")[1]] = [int(line.split(" ")[2]), []]
                    current_macro_name = line.split(" ")[1]
                    in_macro = True
                except Exception:
                    print("error:", line)
                    exit()
            elif line[:6] == "@clear":
                try:
                    del macroTable[line.split(" ")[1]]
                except Exception:
                    output_code.append(line)
            elif line.split(" ")[0] in macroTable:
                for macro_line in macroTable[line.split(" ")[0]][1]:
                    for arg_number in range(macroTable[line.split(" ")[0]][0]):
                        try:
                            arg_specifier = "%"+str(arg_number)
                            macro_line = macro_line.replace(arg_specifier, "".join(line.split(" ")[1:]).split(",")[arg_number])
                        except Exception:
                            print("error:", line)
                            exit()
                    output_code.append(macro_line)
            else:
                output_code.append(line)
    return "\n".join(output_code)
def pass1(inter_code):
    global startAddress
    code = inter_code.split("\n")
    location_counter = 2 # leave space for 2 byte program counter
    for line in code:
        try:
            if line[-1] == ':':
                if ' ' not in line:
                    symbolTable.append(line[:-1])
                    addressTable.append(location_counter)
                    constTable[line[:-1]] = location_counter
                else:
                    print("error:", line)
                    exit()
                continue
            if line[:4] == "@db ":
                tokens = line.split(" ")
                if make_number8(tokens[2]) != -1:
                    literalTable[tokens[1]] = [0, make_number8(tokens[2]), 1, False]
                else:
                    print("error:", line)
                    exit()
                continue
            if line[:4] == "@dd ":
                tokens = line.split(" ")
                if make_number16(tokens[2]) != -1:
                    literalTable[tokens[1]] = [0, make_number16(tokens[2]), 2, False]
                else:
                    print("error:", line)    
                    exit()   
                continue
            if line[:4] == "@dba": # @dba array 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2
                tokens = line.split(" ")
                valid_array = True
                for i in range(2, len(tokens)):
                    if make_number8(tokens[i]) == -1:
                        valid_array = False
                if valid_array:
                    literalTable[tokens[1]] = [0, tokens[2:], 1, True]
            if line[:4] == "@dda": # @dda array 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2
                tokens = line.split(" ")
                valid_array = True
                for i in range(2, len(tokens)):
                    if make_number16(tokens[i]) == -1:
                        valid_array = False
                if valid_array:
                    literalTable[tokens[1]] = [0, tokens[2:], 2, True]
            if line == "@start":
                startAddress = location_counter
            if line.split(" ")[0] in instructions:
                if instructions[line.split(" ")[0]] != 0:
                    location_counter += instructions[line.split(" ")[0]]
                    continue
            # tokenize:
            operation = line.split(" ")[0]
            arguments = "".join(line.split(" ")[1:]).split(",")
            match operation:
                case "ldw":
                    if len(arguments) == 2 and arguments[0] in registers:
                        if arguments[1] == "*ab":
                            location_counter += 1
                        else:
                            location_counter += 3
                    else:
                        print("error:", line)
                        exit()
                case "stw":
                    if len(arguments) == 2 and arguments[0] in registers:
                        if arguments[1] == "*ab":
                            location_counter += 1
                        else:
                            location_counter += 3
                    else:
                        print("error:", line)
                        exit()
                case "jnz":
                    if len(arguments) == 1:
                        if arguments[0] == "ab" or arguments[0] == "cd":
                            location_counter += 1
                        else:
                            if arguments[0] in symbolTable:
                                branchTable.append(addressTable[len(addressTable) - 1 - symbolTable[::-1].index(arguments[0])])
                            location_counter += 3
                case "push":
                    if len(arguments) == 1:
                        if arguments[0] in registers:
                            location_counter += 1
                        else:
                            location_counter += 3
                    else:
                        print("error:", line)
                        exit()
                case "pop":
                    if len(arguments) == 1:
                        if arguments[0] in registers:
                            location_counter += 1
                        else:
                            location_counter += 3
                    else:
                        print("error:", line)
                        exit()
        except:
            print("error:", line)
            exit()
    for variable in literalTable:
        if variable != "HPC" and variable != "LPC":
            literalTable[variable][0] = location_counter
            constTable[variable] = location_counter
            if literalTable[variable][3] == False:
                location_counter += literalTable[variable][2]
            else:
                location_counter += len(literalTable[variable][1])*literalTable[variable][2]
    return location_counter
def pass2(inter_code):
    binary_code = b""
    code = inter_code.split("\n")
    for line in code:
        try:
            if line[:6] == "@clear":
                if line.split(" ")[1] in symbolTable:
                    del addressTable[len(discoveredSymbolTable)- 1 - discoveredSymbolTable[::-1].index(line.split(" ")[1])]
                    del symbolTable[len(discoveredSymbolTable)- 1 - discoveredSymbolTable[::-1].index(line.split(" ")[1])]
                    del discoveredSymbolTable[len(discoveredSymbolTable)- 1 - discoveredSymbolTable[::-1].index(line.split(" ")[1])]
                else:
                    del macroTable[line.split(" ")[1]]
            #tokenize
            operation = line.split(" ")[0]
            arguments = "".join(line.split(" ")[1:]).split(",")
            operation_bytes = ""
            match operation:
                case "ldw":
                    assert len(arguments) == 2
                    operation_bytes = "0000"
                    if arguments[1] == "*ab":
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[1] in literalTable:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:016b}".format(literalTable[arguments[1]][0])
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[1][-1] == "]":
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:016b}".format(literalTable[arguments[1][:arguments[1].index("[")]][0]+make_number16(arguments[1][arguments[1].index("[")+1:-1]))
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))   
                    else:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:016b}".format(literalTable[arguments[1]][0])
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                case "stw":
                    assert len(arguments) == 2
                    operation_bytes = "0001"
                    if arguments[1] == "*ab":
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[1] in literalTable:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:016b}".format(literalTable[arguments[1]][0])
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[1][-1] == "]":
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:016b}".format(literalTable[arguments[1][:arguments[1].index("[")]][0]+make_number16(arguments[1][arguments[1].index("[")+1:-1]))
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:016b}".format(literalTable[arguments[1]][0])
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                case "mvw":
                    assert len(arguments) == 2
                    operation_bytes = "0010"
                    if arguments[1] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(int(registers[arguments[1]], 2))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(make_number8(arguments[1]))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                case "add":
                    assert len(arguments) == 2
                    operation_bytes = "0011"
                    if arguments[1] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(int(registers[arguments[1]], 2))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(make_number8(arguments[1]))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                case "adc":
                    assert len(arguments) == 2
                    operation_bytes = "0100"
                    if arguments[1] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(int(registers[arguments[1]], 2))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(make_number8(arguments[1]))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))  
                case "sub":
                    assert len(arguments) == 2
                    operation_bytes = "0101"
                    if arguments[1] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(int(registers[arguments[1]], 2))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(make_number8(arguments[1]))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2))) 
                case "sbb":
                    assert len(arguments) == 2
                    operation_bytes = "0110"
                    if arguments[1] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(int(registers[arguments[1]], 2))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(make_number8(arguments[1]))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2))) 
                case "inc":
                    assert len(arguments) == 1
                    operation_bytes = "0111"
                    operation_bytes += "0"
                    operation_bytes += registers[arguments[0]]
                    binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2))) 
                case "dec":
                    assert len(arguments) == 1
                    operation_bytes = "0111"
                    operation_bytes += "1"
                    operation_bytes += registers[arguments[0]]
                    binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))                 
                case "cmp":
                    assert len(arguments) == 2
                    operation_bytes = "1000"
                    if arguments[1] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(int(registers[arguments[1]], 2))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        operation_bytes += "{0:08b}".format(make_number8(arguments[1]))
                        binary_code += bytes.fromhex("{0:04x}".format(int("0b"+operation_bytes, 2)))
                case "jnz":
                    assert len(arguments) == 1
                    operation_bytes = "1001"
                    if arguments[0] == "ab":
                        operation_bytes += "1"
                        operation_bytes += "000"
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0] == "cd":
                        operation_bytes += "1"
                        operation_bytes += "001"
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0] in discoveredSymbolTable:
                        operation_bytes += "0"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(addressTable[len(discoveredSymbolTable) - 1 - discoveredSymbolTable[::-1].index(arguments[0])])
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0] in symbolTable:
                        operation_bytes += "0"
                        operation_bytes += "000"
                        #operation_bytes += "{0:016b}".format(addressTable[len(addressTable) - 1 - symbolTable[::-1].index(arguments[0])])
                        operation_bytes += "{0:016b}".format(addressTable[symbolTable.index(arguments[0])])

                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "0"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(make_number16(arguments[0]))
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                case "push":
                    assert len(arguments) == 1
                    operation_bytes = "1010"
                    if arguments[0] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0] in literalTable:
                        operation_bytes += "1"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(literalTable[arguments[0]][0])
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0][-1] == "]":
                        operation_bytes += "1"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(literalTable[arguments[1][:arguments[1].index("[")]][0]+make_number16(arguments[1][arguments[1].index("[")+1:-1]))
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(make_number16(arguments[0]))
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                case "pop":
                    assert len(arguments) == 1
                    operation_bytes = "1011"
                    if arguments[0] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0] in literalTable:
                        operation_bytes += "1"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(literalTable[arguments[0]][0])
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0][-1] == "]":
                        operation_bytes += "1"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(literalTable[arguments[0][:arguments[0].index("[")]][0]+make_number16(arguments[0][arguments[0].index("[")+1:-1]))
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))

                    else:
                        operation_bytes += "1"
                        operation_bytes += "000"
                        operation_bytes += "{0:016b}".format(make_number16(arguments[0]))
                        binary_code += bytes.fromhex("{0:06x}".format(int("0b"+operation_bytes, 2)))
                case "bsl":
                    assert len(arguments) == 1
                    assert arguments[0] in registers or arguments[0] == "ab" or arguments[0] == "cd"
                    operation_bytes = "1100"
                    if arguments[0] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0] == "ab":
                        operation_bytes += "1"
                        operation_bytes += "000"
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += "001"
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                case "bsr":
                    assert len(arguments) == 1
                    assert arguments[0] in registers or arguments[0] == "ab" or arguments[0] == "cd"
                    operation_bytes = "1101"
                    if arguments[0] in registers:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    elif arguments[0] == "ab":
                        operation_bytes += "1"
                        operation_bytes += "000"
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "1"
                        operation_bytes += "001"
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                case "out":
                    assert len(arguments) == 1 or (len(arguments) == 2 and arguments[-1] == "s")
                    operation_bytes = "1110"
                    if arguments[-1] == "s":
                        operation_bytes += "1"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                    else:
                        operation_bytes += "0"
                        operation_bytes += registers[arguments[0]]
                        binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                case "halt":
                    assert len(arguments) == 1 and arguments[0] == ""
                    operation_bytes = "11110000"
                    binary_code += bytes.fromhex("{0:02x}".format(int("0b"+operation_bytes, 2)))
                case _:
                    if line.split(" ")[0] in ["@db", "@dd", "@clear", "@start", "@const", "@dba", "@dda"]:
                        continue
                    elif line[-1] == ':':
                        discoveredSymbolTable.append(line[:-1])
                    else:
                        print("error:", line)
                        exit()

        except Exception as e:
            print("error:", line)
            print(e)
            exit()
    binary_code = bytes.fromhex("{0:04x}".format(startAddress)) + binary_code
    for variable in literalTable:
        if variable != "HPC" and variable != "LPC":
            if literalTable[variable][3] == False:
                if literalTable[variable][2] == 1:
                    binary_code += bytes.fromhex("{0:02x}".format(literalTable[variable][1]))
                elif literalTable[variable][2] == 2:
                    binary_code += bytes.fromhex("{0:04x}".format(literalTable[variable][1]))
            else:
                if literalTable[variable][2] == 1:
                    for i in range(len(literalTable[variable][1])):
                        binary_code += bytes.fromhex("{0:02x}".format(make_number8(literalTable[variable][1][i])))
                if literalTable[variable][2] == 2:
                    for i in range(len(literalTable[variable][1])):
                        binary_code += bytes.fromhex("{0:04x}".format(make_number16(literalTable[variable][1][i])))
    return binary_code

inter_code = includepass(input_file)

inter_code = pass0(inter_code)
byte_length = pass1(inter_code)
output = pass2(inter_code)
with open(argv[2], "wb") as file:
    file.write(output)
    file.close()
print(f"Succesfully wrote to '{argv[2]}'. ({byte_length} bytes)")


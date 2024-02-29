#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
typedef struct {
    uint8_t memory[65536];
    enum reg {a, b, hfp, lfp, sp, hpc, lpc, f};
    uint8_t registers[8];
    uint16_t ab, fp, pc;
    uint8_t halt;
    long cycles_count;
    int16_t output;
    uint8_t output_trigger; // for display purposes
} CPU;

void reset(CPU* CPU) {
    CPU->registers[a] = 0;
    CPU->registers[b] = 0;
    CPU->registers[hfp] = 255;
    CPU->registers[lfp] = 255;
    CPU->registers[sp] = 0;
    CPU->registers[hpc] = CPU->memory[0];
    CPU->registers[lpc] = CPU->memory[1];
    CPU->registers[f] = 0;
    CPU->ab = ((uint16_t)CPU->registers[a] * 256) + CPU->registers[b];
    CPU->fp = ((uint16_t)CPU->registers[hfp] * 256) + CPU->registers[lfp];
    CPU->pc = ((uint16_t)CPU->registers[hpc] * 256) + CPU->registers[lpc];
    CPU->halt = 0;
    CPU->cycles_count = 0;
    CPU->output = 0;
    CPU->output_trigger = 0;
}

void advance(CPU* CPU) {
    CPU->ab = ((uint16_t)CPU->registers[a] * 256) + CPU->registers[b];
    CPU->fp = ((uint16_t)CPU->registers[hfp] * 256) + CPU->registers[lfp];
    CPU->pc = ((uint16_t)CPU->registers[hpc] * 256) + CPU->registers[lpc];
    CPU->output = 0;
    CPU->output_trigger = 0;

    uint8_t current_instruction = CPU->memory[CPU->pc];
    uint8_t opcode = current_instruction >> 4;
    uint8_t mode = (uint8_t)(current_instruction<<4)>>7;
    uint8_t reg0 = (uint8_t)(current_instruction<<5)>>5;
    uint16_t old_pc = CPU->pc;
    int16_t alu_result = 0;
    printf("%.4x: %.2x\n", CPU->pc, current_instruction);
    usleep(100000);
    switch(opcode) {
        case 0: // ldw
            if(mode == 0) {
                CPU->pc += 3;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]];
                CPU->cycles_count += 5;
            }
            else {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[(CPU->registers[a] * 256)+CPU->registers[b]];
                CPU->cycles_count += 5;
            }
            break;
        
        case 1: // stw
            if(mode == 0) {
                CPU->pc += 3;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]] = CPU->registers[reg0];
                CPU->cycles_count += 5;
            }
            else {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->registers[a] * 256)+CPU->registers[b]] = CPU->registers[reg0];
                CPU->cycles_count += 5;
            }
            break;
        
        case 2: // mvw
            if(mode == 0) {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->registers[CPU->memory[old_pc+1]];
                CPU->cycles_count += 4;
            }
            else {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[old_pc+1];
                CPU->cycles_count += 4;
            }
            break;
        
        case 3: // add
            if(mode == 0) {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;
                alu_result = CPU->registers[reg0] + CPU->registers[CPU->memory[old_pc+1]];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;
                alu_result = CPU->registers[reg0] + CPU->memory[old_pc+1];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }

            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 128;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 32;
            if(alu_result > 255)
                CPU->registers[f] += 16;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 2;
            if((uint8_t)alu_result>>7 == 1 || (uint8_t)alu_result == 0)
                CPU->registers[f] += 1;
            break;
        
        case 4: // adc
            if(mode == 0) {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] + CPU->registers[CPU->memory[old_pc+1]] + ((uint8_t)(CPU->registers[f]<<3)>>7);
                CPU->registers[f] = 0;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] + CPU->memory[old_pc+1] + ((uint8_t)(CPU->registers[f]<<3)>>7);
                CPU->registers[f] = 0;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }

            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 128;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 32;
            if(alu_result > 255)
                CPU->registers[f] += 16;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 2;
            if((uint8_t)alu_result>>7 == 1 || (uint8_t)alu_result == 0)
                CPU->registers[f] += 1;
            break;

        case 5: // sub
            if(mode == 0) {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;
                alu_result = CPU->registers[reg0] - CPU->registers[CPU->memory[old_pc+1]];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;
                alu_result = CPU->registers[reg0] - CPU->memory[old_pc+1];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }

            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 128;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 32;
            if(alu_result < 0)
                CPU->registers[f] += 8;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 2;
            if((uint8_t)alu_result>>7 == 1 || (uint8_t)alu_result == 0)
                CPU->registers[f] += 1;
            break;

        case 6: // sbb
            if(mode == 0) {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] - CPU->registers[CPU->memory[old_pc+1]] - ((uint8_t)(CPU->registers[f]<<4)>>7);
                CPU->registers[f] = 0;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] - CPU->memory[old_pc+1] - ((uint8_t)(CPU->registers[f]<<4)>>7);
                CPU->registers[f] = 0;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }

            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 128;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 32;
            if(alu_result < 0)
                CPU->registers[f] += 8;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 2;
            if((uint8_t)alu_result>>7 == 1 || (uint8_t)alu_result == 0)
                CPU->registers[f] += 1;
            break;

        case 7: // iec
            if(mode == 0) {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;
                alu_result = CPU->registers[reg0] + 1;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;
                alu_result = CPU->registers[reg0] - 1;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }

            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 128;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 32;
            if(alu_result > 255)
                CPU->registers[f] += 16;
            if(alu_result < 0)
                CPU->registers[f] += 8;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 2;
            if((uint8_t)alu_result>>7 == 1 || (uint8_t)alu_result == 0)
                CPU->registers[f] += 1;
            CPU->cycles_count += 9;
            break;

        case 8: // cmp
            if(mode == 0) {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;

                if(CPU->registers[reg0] == 0)
                    CPU->registers[f] += 128;
                if(CPU->registers[reg0] == CPU->registers[CPU->memory[old_pc + 1]])
                    CPU->registers[f] += 64;
                if(CPU->registers[reg0] < CPU->registers[CPU->memory[old_pc + 1]])
                    CPU->registers[f] += 8;
                if(CPU->registers[reg0]>>7 == 0)
                    CPU->registers[f] += 2;
                if(CPU->registers[reg0]>>7 == 1 || CPU->registers[reg0] == 0)
                    CPU->registers[f] += 1;
            }
            else {
                CPU->pc += 2;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;

                if(CPU->registers[reg0] == 0)
                    CPU->registers[f] += 128;
                if(CPU->registers[reg0] == CPU->memory[old_pc + 1])
                    CPU->registers[f] += 64;
                if(CPU->registers[reg0] < CPU->memory[old_pc + 1])
                    CPU->registers[f] += 8;
                if(CPU->registers[reg0]>>7 == 0)
                    CPU->registers[f] += 2;
                if(CPU->registers[reg0]>>7 == 1 || CPU->registers[reg0] == 0)
                    CPU->registers[f] += 1;
            }
            CPU->cycles_count += 8;
            break;

        case 9: // jnz
            if(mode == 0) {
                if(CPU->registers[f]>>7 == 0) {
                    CPU->registers[lpc] = CPU->memory[CPU->pc + 2];
                    CPU->registers[hpc] = CPU->memory[CPU->pc + 1];
                }
                else {
                    CPU->pc += 3;
                    CPU->registers[lpc] = (uint8_t)CPU->pc;
                    CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                }
            }
            else {
                if(CPU->registers[f]>>7 == 0) {
                    CPU->registers[lpc] = CPU->registers[b];
                    CPU->registers[hpc] = CPU->registers[a];
                }
                else {
                    CPU->pc += 1;
                    CPU->registers[lpc] = (uint8_t)CPU->pc;
                    CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                }
            }
            CPU->cycles_count += 4;
            break;            

        case 10: // push
            CPU->registers[sp] += 1;
            if(mode == 0) {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[CPU->fp - CPU->registers[sp]] = CPU->registers[reg0];
                CPU->cycles_count += 8;
            }
            else {
                CPU->pc += 3;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->registers[hfp] * 256) + CPU->registers[lfp] - CPU->registers[sp]] = CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]];
                CPU->cycles_count += 10;
            }
            break;
        case 11: // pop
            if(mode == 0) {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[CPU->fp - CPU->registers[sp]];
                CPU->cycles_count += 8;
            }
            else {
                CPU->pc += 3;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]] = CPU->memory[(CPU->registers[hfp] * 256) + CPU->registers[lfp] - CPU->registers[sp]];
                CPU->cycles_count += 10;
            }
            CPU->registers[sp] -= 1;
            break;
        case 12: // bsl
            CPU->pc += 1;
            CPU->registers[lpc] = (uint8_t)CPU->pc;
            CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
            if(mode == 0) {
                CPU->registers[reg0] = CPU->registers[reg0] << 1;
            }
            else {
                CPU->ab = CPU->ab << 1;
                CPU->registers[a] = (uint8_t)CPU->ab;
                CPU->registers[b] = (uint8_t)(CPU->ab >> 8);
            }
            CPU->cycles_count += 6;
            break;

        case 13: // bsr
            CPU->pc += 1;
            CPU->registers[lpc] = (uint8_t)CPU->pc;
            CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
            if(mode == 0) {
                CPU->registers[reg0] = CPU->registers[reg0] >> 1;
            }
            else {
                CPU->ab = CPU->ab >> 1;
                CPU->registers[a] = (uint8_t)CPU->ab;
                CPU->registers[b] = (uint8_t)(CPU->ab >> 8);
            }
            CPU->cycles_count += 6;
            break;

        case 14: // out
            if(mode == 0) {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->output = CPU->registers[reg0];
                CPU->output_trigger = 1;
                CPU->cycles_count += 4;
            }
            else {
                CPU->pc += 1;
                CPU->registers[lpc] = (uint8_t)CPU->pc;
                CPU->registers[hpc] = (uint8_t)(CPU->pc >> 8);
                CPU->output = CPU->registers[reg0]-256; 
                CPU->output_trigger = 1;
                CPU->cycles_count += 4;            
            }
            break;

        case 15: // halt
            CPU->halt = 1;
            CPU->cycles_count += 1;
            break;
    }
}


float floatgen(uint16_t float16) {
    uint8_t sign = float16 >> 15;
    uint8_t exponent = (float16 << 1) >> 11;
    uint16_t mantissa = (float16 & 0x3ff) + 1024;
    //printf("%d, %d, %d\n", sign, exponent-14, mantissa);
    if(sign == 0) {
        if(exponent - 15 >= 0) {
            return (2 << (exponent-16)) * (mantissa/1024.0);
        }
        return (mantissa/1024.0) / (2 << (-exponent+14));
    }
    if(exponent - 15 >= 0) {
        return -1 * (2 << (exponent-16)) * (mantissa/1024.0);
    }
    return -1 * (mantissa/1024.0) / (2 << (-exponent+14));
}

int main(int argc, char **argv) {
    // reads file to byte array
    FILE *fileptr;
    char *program;
    long filelen;
    if(argc < 2) {
        printf("error: no program file.\n");
        return -1;
    }
    fileptr = fopen(argv[1], "rb");
    if(!fileptr) {
        printf("error: can't read from \'%s\'.\n", argv[1]);
        fclose(fileptr);
        return -1;
    }
    fseek(fileptr, 0, SEEK_END);
    filelen = ftell(fileptr);
    rewind(fileptr);
    if(filelen > 65536) {
        printf("error: file exceeds max memory length (65536).");
        fclose(fileptr);
        return -1;
    } 

    program = (uint8_t *)malloc(65536);
    if(!program) {
        printf("error: memory for ram could not be allocated.");
        fclose(fileptr);
        return -1;
    }
    fread(program, filelen, 1, fileptr);
    fclose(fileptr);
    
    // initialize CPU and load program to ram;
    CPU LDM;
    memset(LDM.memory, 0x00, 65536);
    memcpy(LDM.memory, program, filelen);
    reset(&LDM);
    uint8_t output_buffer = 0;
    while(LDM.halt != 1) {
        advance(&LDM);
        if(LDM.output_trigger == 1) {
            printf("%d ", LDM.output);
            printf("%d ", output_buffer * 256 + LDM.output);
            printf("%.4f\n", floatgen(output_buffer * 256 + LDM.output));
            output_buffer = LDM.output;
        }
    }
    double execution_time_s = LDM.cycles_count / 4000000.0;
    printf("Halted.\nProgram would have excecuted in %f seconds.\n", execution_time_s);
}




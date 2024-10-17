#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
typedef struct {
    uint8_t memory[65536];
    enum reg {a, b, c, d, hfp, lfp, sp, f};
    uint8_t registers[8];
    uint16_t ab, cd, fp, pc;
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
    CPU->registers[sp] = 255;
    CPU->registers[f] = 0;
    CPU->ab = ((uint16_t)CPU->registers[a] * 256) + CPU->registers[b];
    CPU->cd = ((uint16_t)CPU->registers[c] * 256) + CPU->registers[d];
    CPU->fp = ((uint16_t)CPU->registers[hfp] * 256) + CPU->registers[lfp];
    CPU->pc = ((uint16_t)CPU->memory[0] * 256) + CPU->memory[1];
    CPU->halt = 0;
    CPU->cycles_count = 0;
    CPU->output = 0;
    CPU->output_trigger = 0;
}

void advance(CPU* CPU) {
    CPU->ab = ((uint16_t)CPU->registers[a] * 256) + CPU->registers[b];
    CPU->cd = ((uint16_t)CPU->registers[c] * 256) + CPU->registers[d];
    CPU->fp = ((uint16_t)CPU->registers[hfp] * 256) + CPU->registers[lfp];
    CPU->pc = ((uint16_t)CPU->memory[0] * 256) + CPU->memory[1];
    CPU->output = 0;
    CPU->output_trigger = 0;

    uint8_t current_instruction = CPU->memory[CPU->pc];
    uint8_t opcode = current_instruction >> 4;
    uint8_t mode = (uint8_t)(current_instruction<<4)>>7;
    uint8_t reg0 = (uint8_t)(current_instruction<<5)>>5;
    uint16_t old_pc = CPU->pc;
    int16_t alu_result = 0; 
    switch(opcode) {
        case 0: // ldw
            if (mode == 0) {
                CPU->pc += 3;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]];
                CPU->cycles_count += 5;
            }
            else {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[(CPU->registers[a] * 256)+CPU->registers[b]];
                CPU->cycles_count += 5;
            }
            break;
        
        case 1: // stw
            if(mode == 0) {
                CPU->pc += 3;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]] = CPU->registers[reg0];
                CPU->cycles_count += 5;
            }
            else {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->registers[a] * 256)+CPU->registers[b]] = CPU->registers[reg0];
                CPU->cycles_count += 5;
            }
            break;
        
        case 2: // mvw
            if(mode == 0) {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->registers[CPU->memory[old_pc+1]];
                CPU->cycles_count += 4;
            }
            else {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[old_pc+1];
                CPU->cycles_count += 4;
            }
            break;
        
        case 3: // add
            if(mode == 0) {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] + CPU->registers[CPU->memory[old_pc+1]];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] + CPU->memory[old_pc+1];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            CPU->registers[f] = 0;
            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 16;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 1;
            if(alu_result > 255)
                CPU->registers[f] += 64;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 128;
            if((uint8_t)alu_result>>7 == 1)
                CPU->registers[f] += 2;
            break;
        
        case 4: // adc
            if(mode == 0) {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] + CPU->registers[CPU->memory[old_pc+1]] + ((uint8_t)(CPU->registers[f]<<1)>>7);
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] + CPU->memory[old_pc+1] + ((uint8_t)(CPU->registers[f]<<1)>>7);
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            CPU->registers[f] = 0;
            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 16;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 1;
            if(alu_result > 255)
                CPU->registers[f] += 64;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 128;
            if((uint8_t)alu_result>>7 == 1)
                CPU->registers[f] += 2;
            break;

        case 5: // sub
            if(mode == 0) {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] - CPU->registers[CPU->memory[old_pc+1]];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] - CPU->memory[old_pc+1];
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            CPU->registers[f] = 0;
            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 16;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 1;
            if(alu_result < 0)
                CPU->registers[f] += 4;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 128;
            if((uint8_t)alu_result>>7 == 1)
                CPU->registers[f] += 2;
            break;

        case 6: // sbb
            if(mode == 0) {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] - CPU->registers[CPU->memory[old_pc+1]] - ((uint8_t)(CPU->registers[f]<<5)>>7);
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] - CPU->memory[old_pc+1] - ((uint8_t)(CPU->registers[f]<<5)>>7);
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            CPU->registers[f] = 0;
            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 16;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 1;
            if(alu_result < 0)
                CPU->registers[f] += 4;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 128;
            if((uint8_t)alu_result>>7 == 1)
                CPU->registers[f] += 2;
            break;

        case 7: // iec
            if(mode == 0) {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] + 1;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            
            else {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                alu_result = CPU->registers[reg0] - 1;
                CPU->registers[reg0] = alu_result;
                CPU->cycles_count += 9;
            }
            CPU->registers[f] = 0;
            if((uint8_t)alu_result == 0)
                CPU->registers[f] += 16;
            if(CPU->registers[reg0]>>7 == CPU->registers[CPU->memory[old_pc+1]]>>7 && CPU->registers[reg0]>>7 != (uint8_t)alu_result>>7)
               CPU->registers[f] += 1;
            if(alu_result > 255)
                CPU->registers[f] += 64;
            if(alu_result < 0)
                CPU->registers[f] += 4;
            if((uint8_t)alu_result>>7 == 0)
                CPU->registers[f] += 128;
            if((uint8_t)alu_result>>7 == 1)
                CPU->registers[f] += 2;
            CPU->cycles_count += 9;
            break;

        case 8: // cmp
            if(mode == 0) {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;

                if(CPU->registers[reg0] == 0)
                    CPU->registers[f] += 16;
                if(CPU->registers[reg0] == CPU->registers[CPU->memory[old_pc + 1]])
                    CPU->registers[f] += 32;
                if(CPU->registers[reg0] < CPU->registers[CPU->memory[old_pc + 1]])
                    CPU->registers[f] += 8;
                if(CPU->registers[reg0]>>7 == 0)
                    CPU->registers[f] += 128;
                if(CPU->registers[reg0]>>7 == 1 || CPU->registers[reg0] == 0)
                    CPU->registers[f] += 2;
            }
            else {
                CPU->pc += 2;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[f] = 0;

                if(CPU->registers[reg0] == 0)
                    CPU->registers[f] += 16;
                if(CPU->registers[reg0] == CPU->memory[old_pc + 1])
                    CPU->registers[f] += 32;
                if(CPU->registers[reg0] < CPU->memory[old_pc + 1])
                    CPU->registers[f] += 8;
                if(CPU->registers[reg0]>>7 == 0)
                    CPU->registers[f] += 128;
                if(CPU->registers[reg0]>>7 == 1 || CPU->registers[reg0] == 0)
                    CPU->registers[f] += 2;
            }
            CPU->cycles_count += 8;
            break;

        case 9: // jnz
            if(mode == 0) {
                if((CPU->registers[f] & 0x10) == 0) {
                    CPU->memory[1] = CPU->memory[CPU->pc + 2];
                    CPU->memory[0] = CPU->memory[CPU->pc + 1];
                }
                else {
                    CPU->pc += 3;
                    CPU->memory[1]  = (uint8_t)CPU->pc;
                    CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                }
            }
            else {
                if((CPU->registers[f] & 0x10) == 0) {
                    if(reg0 == 0) {
                        CPU->memory[1]  = CPU->registers[b];
                        CPU->memory[0] = CPU->registers[a];
                    }
                    else {
                        CPU->memory[1]  = CPU->registers[d];
                        CPU->memory[0] = CPU->registers[c];
                    }
                }
                else {
                    CPU->pc += 1;
                    CPU->memory[1]  = (uint8_t)CPU->pc;
                    CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                }
            }
            CPU->cycles_count += 4;
            break;            

        case 10: // push
            CPU->registers[sp] += 1;
            if(mode == 0) {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[CPU->fp - CPU->registers[sp]] = CPU->registers[reg0];
                CPU->cycles_count += 8;
            }
            else {
                CPU->pc += 3;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->registers[hfp] * 256) + CPU->registers[lfp] - CPU->registers[sp]] = CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]];
                CPU->cycles_count += 10;
            }
            break;
        case 11: // pop
            if(mode == 0) {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->registers[reg0] = CPU->memory[CPU->fp - CPU->registers[sp]];
                CPU->cycles_count += 8;
            }
            else {
                CPU->pc += 3;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->memory[(CPU->memory[old_pc+1] * 256)+CPU->memory[old_pc+2]] = CPU->memory[(CPU->registers[hfp] * 256) + CPU->registers[lfp] - CPU->registers[sp]];
                CPU->cycles_count += 10;
            }
            CPU->registers[sp] -= 1;
            break;
        case 12: // bsl
            CPU->pc += 1;
            CPU->memory[1] = (uint8_t)CPU->pc;
            CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
            CPU->registers[f] = 0;
            if(mode == 0) {
                if((CPU->registers[reg0] & 0x80) == 128) {
                    CPU->registers[f] += 64;
                }
                CPU->registers[reg0] = CPU->registers[reg0] << 1;
                if(CPU->registers[reg0] == 0) {
                    CPU->registers[f] += 16;
                }                
            }
            else {
                if(reg0 == 0) {
                    if((CPU->registers[a] & 0x80) == 128) {
                        CPU->registers[f] += 64;
                    }
                    CPU->ab = CPU->ab << 1;
                    CPU->registers[b] = (uint8_t)CPU->ab;
                    CPU->registers[a] = (uint8_t)(CPU->ab >> 8);
                    if(CPU->ab == 0) {
                        CPU->registers[f] += 16;
                    }
                }
                else {
                    if((CPU->registers[c] & 0x80) == 128) {
                        CPU->registers[f] += 64;
                    }
                    CPU->cd = CPU->cd << 1;
                    CPU->registers[d] = (uint8_t)CPU->cd;
                    CPU->registers[c] = (uint8_t)(CPU->cd >> 8);
                    if(CPU->cd == 0) {
                        CPU->registers[f] += 16;
                    }
                }
            }   
            CPU->cycles_count += 6;
            break;

        case 13: // bsr
            CPU->pc += 1;
            CPU->memory[1] = (uint8_t)CPU->pc;
            CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
            CPU->registers[f] = 0;
            if(mode == 0) {
                if((CPU->registers[reg0] & 0x1) == 1) {
                        CPU->registers[f] += 64;
                }
                CPU->registers[reg0] = CPU->registers[reg0] >> 1;
                if(CPU->registers[reg0] == 0) {
                    CPU->registers[f] += 16;
                }
            }
            else {
                if(reg0 == 0) {
                    if((CPU->registers[b] & 0x1) == 1) {
                        CPU->registers[f] += 64;
                    }
                    CPU->ab = CPU->ab >> 1;
                    CPU->registers[b] = (uint8_t)CPU->ab;
                    CPU->registers[a] = (uint8_t)(CPU->ab >> 8);
                    if(CPU->ab == 0) {
                        CPU->registers[f] += 16;
                    }
                }
                else {
                    if((CPU->registers[d] & 0x1) == 1) {
                        CPU->registers[f] += 64;
                    }
                    CPU->cd = CPU->cd >> 1;
                    CPU->registers[d] = (uint8_t)CPU->cd;
                    CPU->registers[c] = (uint8_t)(CPU->cd >> 8);     
                    if(CPU->cd == 0) {
                        CPU->registers[f] += 16;
                    }               
                }            
            }
            CPU->cycles_count += 6;
            break;

        case 14: // out
            if(mode == 0) {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
                CPU->output = CPU->registers[reg0];
                CPU->output_trigger = 1;
                CPU->cycles_count += 4;
            }
            else {
                CPU->pc += 1;
                CPU->memory[1] = (uint8_t)CPU->pc;
                CPU->memory[0] = (uint8_t)(CPU->pc >> 8);
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
    CPU->fp = ((uint16_t)CPU->registers[hfp] * 256) + CPU->registers[lfp];
    printf("%.4x: %.2x A: %d B: %d C: %d, D: %d HPC: %d LPC: %d Stack:  %d, %d, %d, %d, %d\n", old_pc, CPU->memory[old_pc], CPU->registers[a], CPU->registers[b], CPU->registers[c], CPU->registers[d], CPU->memory[0], CPU->memory[1], CPU->memory[CPU->fp-CPU->registers[sp]], CPU->memory[CPU->fp-CPU->registers[sp]+1], CPU->memory[CPU->fp-CPU->registers[sp]+2], CPU->memory[CPU->fp-CPU->registers[sp]+3], CPU->memory[CPU->fp-CPU->registers[sp]+4]);
}


double floatgen(uint16_t x)
{
    int s = (x     & 0x8000);
    int e = (x>>10 & 0x001f) - 15;
    int m = (x     & 0x03ff);

    switch (e) {
    case -15: if (!m) {
                  e = 0;
              } else {
                  // convert from denormal
                  e += 1023 + 1;
                  while (!(m&0x400)) {
                      e--;
                      m <<= 1;
                  }
                  m &= 0x3ff;
              }
              break;
    case +16: m = !!m << 9;  // canonicalize to quiet NaN
              e = 2047;
              break;
    default:  e += 1023;
    }

    uint64_t b = (uint64_t)s<<48 |
                 (uint64_t)e<<52 |
                 (uint64_t)m<<42;
    double f;
    memcpy(&f, &b, 8);
    return f;
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
            printf("%.3f\n", floatgen(output_buffer * 256 + LDM.output));
            output_buffer = LDM.output;
        }
        getchar();

    }
    double execution_time_s = LDM.cycles_count / 4000000.0;
    printf("Halted.\nProgram would have excecuted in %f seconds.\n", execution_time_s);
}




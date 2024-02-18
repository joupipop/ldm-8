@db bufferH 0
@db bufferL 0
; STANDARD MACROS
@macro jmp 1
    mvw f, 0
    jnz %0
@endmacro

@macro jeq 1
    bsl f
    jnz %0
@endmacro

@macro peek 1 ; peeks to a
    mvw a, hfp
    push b
    mvw b, lfp
    sub b, sp
    sbb a, 0
    add b, 1
    adc a, 0
    add b, %0
    adc a, 0
    ldw a, *ab
    pop b
@endmacro

@macro put 1 ; put a
    push b
    push a
    mvw a, hfp
    mvw b, lfp
    sub b, sp
    sbb a, 0
    add b, %0
    adc a, 0
    add b, 2
    adc a, 0
    pop f
    stw f, *ab
    pop b
    mvw a, f
@endmacro

@macro call 1 ; arguments should be pushed in order onto stack before calling
    mvw a, 0
    push a
    push a
    mvw a, hfp
    mvw b, lfp
    push sp
    sub lfp, sp
    sbb hfp, 0 
    mvw sp, 0
    push a
    push b
    push hpc
    push lpc
    jmp %0
@endmacro

@macro ret 0
    mvw sp, 4
    put 5
    mvw a, b
    put 6
    pop bufferL
    pop bufferH
    pop b
    pop a
    pop sp
    mvw lfp, b
    mvw hfp, a
    ldw a, bufferH
    ldw b, bufferL ; not right address
    add b, 6
    adc a, 0
    mvw f, 0
    jnz ab
@endmacro


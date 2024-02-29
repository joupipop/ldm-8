@dd buffer 0
; STANDARD MACROS
@macro jmp 1
    mvw f, 0
    jnz %0
@endmacro

@macro jnq 1
    bsl f
    jnz %0
@endmacro

@macro jge 1
    bsl f
    bsl f
    bsl f
    bsl f
    bsl f
    jnz %0
@endmacro

@macro jn 1
    bsl f
    bsl f
    bsl f
    bsl f
    bsl f
    bsl f
    jnz %0
@endmacro

@macro jp 1
    bsl f
    bsl f
    bsl f
    bsl f
    bsl f
    bsl f
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
    pop buffer[0]
    pop buffer[1]
    pop b
    pop a
    pop sp
    mvw lfp, b
    mvw hfp, a
    ldw a, buffer[0]
    ldw b, buffer[1]
    add b, 5
    adc a, 0
    mvw f, 0
    jnz ab
@endmacro

@macro ldw16 1
    ldw a, %0[0]
    ldw b, %0[1]
@endmacro

@macro stw16 1
    stw a, %0[0]
    stw b, %0[1]
@endmacro

@macro add16 1
    push a
    ldw a, %0[1]
    add a, b
    pop b
    push a
    mvw a, b
    ldw b, %0[0]
    adc a, b
    pop b
@endmacro

@macro sub16 1
    push a
    ldw a, %0[1]
    sub a, b
    pop b
    push a
    mvw a, b
    ldw b, %0[0]
    sbb a, b
    pop b
@endmacro

@macro out16 0
    out a
    out b
@endmacro


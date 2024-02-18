; ARCHITECTURE CONSTANTS
@db ZERO 0

; STANDARD MACROS

@macro not 1
    push c
    mvw c, %0
    sub %0, c
    sub %0, c
    dec %0
    pop c
@endmacro

@macro jmp 1
    ldw f, ZERO
    jnz %0
@endmacro

@macro jeq 1
    bsl f
    jnz %0
@endmacro

@macro jnq 1
    not f
    bsl f
    jnz %0
@endmacro

@macro ldi 2
    sub %0, %0
    add %0, %1
@endmacro



@macro peek 1
    push a
    ldi a, 255
    push b
    ldi b, sp
    sub b, %0
    sub b, 2
    mvw c, *ab
    pop b
    pop a
@endmacro

@macro call 1 ; arguments should be pushed in order onto stack before calling
    push c
    push hpc
    push lpc
    push fp
    mvw fp, sp
    jmp %0
@endmacro

@macro ret 0
    mvw sp, fp
    push b
    push a
    add fp, 2
    peek 2
    mvw fp, c
    peek 3
    add c, 9
    mvw b, c
    push f
    peek 5
    pop f
    adc c, 0
    mvw a, c
    peek 5
    jmp ab
@endmacro
 

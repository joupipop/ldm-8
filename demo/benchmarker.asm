@include repo/libs/stdlib.asm
@include repo/libs/mathlib.asm


@start
mvw c, 0
mvw d, 0
loop:
    mvw a, c
    mvw b, d
    push d
    push c
    call cos
    out a
    out b

    pop c
    pop d
    inc d
    mvw a, f
    adc c, 0
    jnz loop
    mvw f, a
    jnz loop
halt
    

@include ../libs/stdlib.asm
sum:
    cmp a, 1
    jnq recursive_case
    ret
recursive_case:
    push a
    dec a
    call sum
    pop b
    add a, b
ret
@start
mvw a, 10
call sum
out a
halt

@include repo/libs/stdlib.asm
sum:
    peek 7
    cmp a, 1
    jnq sum_recursion
        mvw b, 1
        mvw a, 0
    ret
    sum_recursion:
        dec a
        push a
        call sum
        pop a
        pop b
        dec sp
        peek 7
        add b, a
        mvw a, 0
    ret

@start
mvw a, 10
push a
call sum
pop b
pop a
out b
halt
        

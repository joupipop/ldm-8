mvw a, 0
mvw b, 1
mvw d, 10
loop:
    out a
    add a, b
    mvw c, a
    mvw a, b
    mvw b, c
    dec d
jnz loop
halt
    

    

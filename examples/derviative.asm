@include ../libs/stdlib.asm
@include ../libs/mathlib.asm

@dd A 6.0
@const h 0.07873
@const 2h 0.15745

; algorithm to find derivative of f(x) at a
; with f : f16 → f16 and a : f16

func: ; func : [a-b]:f16 → [a-b]:f16 (x → x²)
    mvw c, a
    mvw d, b
    call fmul
ret


derv: ; derv: [a-b]:f16, [c-d]:f16 → [a-b]:f16 (t , f(x) → f'(t))
    push b
    push a
    push d
    push c
    mvw c,  h[0]
    mvw d, h[1]
    call fsub ; t - h
    pop c
    pop d
    push d
    push c
    callr cd ; f(t-h)
    pop c
    pop d
    push b
    push a
    sub sp, 2
    pop a 
    pop b
    add sp, 4
    push d
    push c
    mvw c, h[0]
    mvw d, h[1]
    call fadd ; t + h
    pop c
    pop d
    callr cd ; f(t+h)
    pop c
    pop d
    call fsub
    mvw c, 2h[0]
    mvw d, 2h[1]
    call fdiv
ret

@start
ldw16 a, b, A
mvw c, func[0]
mvw d, func[1]
call derv
out a
out b
halt


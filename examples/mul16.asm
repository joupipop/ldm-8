@dd NUM1 1234
@dd NUM2 1234

ldw a, NUM1[0]
ldw b, NUM1[1]

ldw c, NUM2[0]
ldw d, NUM2[1]


push b
push a

mvw a, 0
push d
push c
push a
push a

push a
push a
push a
push a

loop:
    sub sp, 9
    pop c
    add sp, 10
    bsl c
    bsl c
    bsl c
    bsl c
    mvw f, c
    jnz lsb_is_zero
        sub sp, 2
        pop a
        pop b
        sub sp, 2
        pop c
        pop d
        add b, d
        adc a, c
        mvw c, f
        add sp, 4
        push b
        push a
        add sp, 2

        pop a
        pop b
        sub sp, 3
        pop d
        mvw f, c
        adc b, d
        mvw d, f
        add sp, 2
        pop c
        mvw f, d
        adc a, c
        add sp, 3
        push b
        push a
        
        ; seems to be working from here

    lsb_is_zero:
        sub sp, 4
        pop a
        pop b
        pop c
        pop d
        bsl ab
        bsl cd
        adc b, 0
        push d
        push c
        push b
        push a
        sub sp, 4
        pop c
        pop d
        bsr cd
        mvw a, f
        push d
        push c
        add sp, 8
        mvw f, a
        
    jnz loop
    pop a
    pop b
    pop c
    pop d

out a
out b
out c
out d
halt

; STACK:
; RES[0] 
; RES[1] 
; RES[2] 
; RES[3] 
; NUM2[0] 
; NUM2[1] 
; NUM2[2] 
; NUM2[3] 
; NUM1[0]
; NUM1[1]

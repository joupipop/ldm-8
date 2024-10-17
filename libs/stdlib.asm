@dd buffer 0
; STANDARD MACROS
@macro jmp 1
    mvw f, 0
    jnz %0
@endmacro

@macro call 1
    push sp
    push hfp
    push lfp
    push HPC
    push LPC
    sub lfp, sp
    sbb hfp, 0
    mvw sp, 0
    mvw f, 0
    jnz %0
@endmacro

@macro callr 1
    push sp
    push hfp
    push lfp
    push HPC
    push LPC
    sub lfp, sp
    sbb hfp, 0
    mvw sp, 0
    mvw f, 0
    mvw a, a ; 2 byte padding
    jnz %0
@endmacro

@macro ret 0
    add lfp, 4
    adc hfp, 0
    mvw sp, 4
    pop buffer[1]
    pop buffer[0]
    pop d
    pop c
    pop sp
    mvw lfp, d
    mvw hfp, c
    ldw c, buffer[0]
    ldw d, buffer[1]
    sub d, 3 ; do NOT simplify to add 11, the "sub d, 3" must not have effect on c reg
    add d, 14 ; 14
    adc c, 0
    mvw f, 0
    jnz cd
@endmacro

@macro peek 2
    sub sp, %1
    pop %0
    add sp, %1 ; pos + 1
    inc sp
@endmacro

@macro put 2
    sub sp, %1 ; pos + 1
    dec sp
    push %0
    add sp, %1
@endmacro

@macro ldw16 3
    ldw %0, %2[0]
    ldw %1, %2[1]
@endmacro

@macro stw16 3
    stw %0, %2[0]
    stw %1, %2[1]
@endmacro


; STANDARD FUNCTIONS
umul:
    mvw c, 0
    push b
    push c
    push c
    mvw b, a
    mvw a, 0
    loop:
        sub sp, 2
        pop c
        add sp, 3
        bsl c
        bsl c
        bsl c
        bsl c
        mvw f, c
        jnz lsb_is_zero
            pop d
            pop c
            add d, b
            adc c, a
            push c
            push d
        lsb_is_zero:
        bsl ab
        sub sp, 2
        pop c
        bsr c
        mvw d, f
        push c
        add sp, 2
        mvw f, d
    jnz loop
    pop b
    pop a
@clear lsb_is_zero
@clear loop
ret

udiv:
    mvw c, 8 ; counter (n of bits in dividend) n
    mvw d, b ; divisor (const)                 M
    mvw b, a ; dividend -> quotient            Q
    mvw a, 0 ; 0 -> remainder                  A
    loop:
        bsl ab
        push a ; store a
        sub a, d
        ; checks msb in a
        bsr b
        bsl b ; b[0] := 0
        push a
        bsr a
        bsr a
        bsr a
        mvw f, a
        pop a
        jnz msb_is_zero
            ; msb is one
            pop a ; restore a
        mvw f, 0
        jnz rest
        msb_is_zero:
            inc b ; b[0] := 1
        rest:
        dec c
        jnz loop
    push b
    mvw b, a
    pop a
@clear loop
@clear rest
@clear msb_is_zero
ret

smul:
    mvw c, 0 ; bool : sign of result
    push a
    bsr a
    bsr a
    bsr a
    mvw f, a
    pop a
    jnz check_b_sign
        ; a is neg
        inc c
        ; make a pos
        mvw d, 255 ; -1
        sub d, a
        mvw a, d
        inc a
    check_b_sign:
    push b
    bsr b
    bsr b
    bsr b
    mvw f, b
    pop b
    jnz rest
        ; b is neg
        inc c
        ; make b pos
        mvw d, 255
        sub d, b
        mvw b, d
        inc b
    rest:
    push c
    call umul
    pop c
    push c
    bsl c
    bsl c
    bsl c
    bsl c
    mvw f, c
    pop c
    jnz result_is_pos
        ; result is neg
        mvw c, 255
        mvw d, 255
        sub d, b
        sbb c, a
        mvw a, c
        mvw b, d
        inc b
        adc a, 0
    result_is_pos:
@clear check_b_sign
@clear rest
@clear result_is_pos
ret

sdiv:
    mvw c, 0 ; bool : sign of result
    push a
    bsr a
    bsr a
    bsr a
    mvw f, a
    pop a
    jnz check_b_sign
        ; a is neg
        inc c
        ; make a pos
        mvw d, 255 ; -1
        sub d, a
        mvw a, d
        inc a
    check_b_sign:
    push b
    bsr b
    bsr b
    bsr b
    mvw f, b
    pop b
    jnz rest
        ; b is neg
        inc c
        ; make b pos
        mvw d, 255
        sub d, b
        mvw b, d
        inc b
    rest:
    push c
    call udiv
    pop c
    push c
    bsl c
    bsl c
    bsl c
    bsl c
    mvw f, c
    pop c
    jnz result_is_pos
        ; result is neg
        mvw c, 255
        sub c, a
        inc c
        mvw a, c
    result_is_pos:
@clear check_b_sign
@clear rest
@clear result_is_pos
ret  

fmul:
    ; check for zero
    add a, 0
    jnz check_NUM2
    ; a is zero
        add b, 0
        jnz check_NUM2
        ; b is zero
            ret
    check_NUM2:
    add c, 0
    jnz continue
    ; c is zero
        add d, 0
        jnz continue
        ; d is zero
            mvw a, 0
            mvw b, 0
            ret
    continue:
    @clear check_NUM2
    @clear continue
    ; create local variables:
    ; STACK:
    ; MANTISSA2[0]
    ; MANTISSA2[1]
    ; EXP2
    ; SIGN2
    ; MANTISSA1[0]
    ; MANTISSA1[1]
    ; EXP1
    ; SIGN1
    ; NUM1[0]
    ; NUM1[1]
    ; NUM2[0]
    ; NUM2[1] 

    push d
    push c
    push b
    push a
    
    bsr a ; a >> 7
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a
    
    push a ; sign of NUM1

    dec sp
    pop a
    add sp, 2
    
    bsl a ; (a << 1) >> 3
    bsr a
    bsr a
    bsr a
    push a ; exponent of NUM1
    
    sub sp, 2
    pop a
    add sp, 3
    bsl a ; (a << 6) >> 6
    bsl a
    bsl a
    bsl a
    bsl a
    bsl a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a

    add a, 4
    push b
    push a ; mantissa of NUM1
    
    bsr c ; a >> 7
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    
    push c ; sign of NUM2

    sub sp, 7
    pop c
    add sp, 8
    bsl c ; (a << 1) >> 3
    bsr c
    bsr c
    bsr c
    push c ; exponent of NUM2
    sub sp, 8
    pop c
    add sp, 9
     
    bsl c ; (a << 6) >> 6
    bsl c
    bsl c
    bsl c
    bsl c
    bsl c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    
    add c, 4

    push d
    push c ; mantissa of NUM2
    
    ; multiply mantissas

    ; add 2 bytes to MANTISSA2
    mvw a, 0
    push a
    push a
    ; make room for 32 bit result
    push a
    push a
    push a
    push a
    
    ; shift and add unsigned 16bit multiplier
    loop: 
        sub sp, 11
        pop c
        add sp, 12
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
            sub sp, 6
            pop c
            pop d
            bsr cd 
            mvw a, f
            push d
            push c
            add sp, 10
            mvw f, a
        jnz loop
        @clear loop
        @clear lsb_is_zero
    pop a
    pop b
    pop c
    pop d
    sub sp, 4
    ; keep only first 11 bits
    pop a
    add a, 4 ; NO IDEA HOW THIS WORKS BUT IT DOES
    push a
    loop:
        pop a
        dec a
        push a

        bsl b
        mvw a, f
        bsl cd
        adc b, 0
        bsr a
        bsr a
    mvw f, a
    jnz loop
    @clear loop
    
    mvw d, c
    mvw c, b
    bsr cd
    bsr cd
    bsr cd
    bsr cd
    bsr cd
    bsr cd
    adc d, 0
    adc c, 0
    
    sub sp, 4
    push d
    push c
    add sp, 2

    ; add exponents
    pop a
    sub sp, 3
    pop b
    add sp, 4
    add a, b
    sub a, 15
    ; test for overflow and underflow
    ; overflow:
    mvw b, a
    sub b, 30
    mvw d, f
    bsl d
    bsl d
    bsl d
    mvw f, d
    jnz exp_gt_30 ; return +/- infinity
    ; exp (biased) is lower than 30 (good)
    ; underflow:
    mvw b, a
    add b, 0
    mvw d, f
    bsr d
    bsr d
    bsr d
    mvw f, d
    jnz exp_lt_0 ; return +/- 0
    ; exp (biased) is not negative (good)
    bsl a
    bsl a
    ; add signs (XOR)
    pop c
    sub sp, 3
    pop d
    add sp, 4
    add c, d
    bsr cd
    
    ; assemble final float
    add a, d
    pop c
    pop b
    add a, c
ret

exp_gt_30:
    pop c
    sub sp, 3
    pop d
    add c, d
    bsr cd
    add d, 124
    mvw a, d
    mvw b, 0 ; +/- infinity 
ret

exp_lt_0:
    pop c
    sub sp, 3
    pop d
    add c, d
    bsr cd
    mvw a, d
    mvw b, 0 ; +/- 0
@clear exp_gt_30
@clear exp_lt_0
ret

fdiv:
    push b
    push a
    mvw a, 0x77 ; magic const
    mvw b, 0xab ; magic const2
    sub b, d
    sbb a, c ; x_0
    push b 
    push a
    call fmul
    add a, 128
    mvw c, 0x40
    mvw d, 0x00 
    call fadd ; +2
    pop c
    pop d
    call fmul ; x_1
    pop c
    pop d
    call fmul
ret


fadd:
    ; check for zero
    push a
    bsl a
    bsr a
    add a, 0
    pop a
    jnz check_NUM2
    ; a is zero
        add b, 0
        jnz check_NUM2
        ; b is zero
            mvw a, c
            mvw b, d
            ret
    check_NUM2:
    push c
    bsl c
    bsr c
    add c, 0
    pop c
    jnz continue
    ; c is zero
        add d, 0
        jnz continue
            ; d is zero
            ret
    continue:
    @clear check_NUM2
    @clear continue
    


    ; assumes NUM1 and NUM2 are both positive

    ; create local variables:
    ; STACK:
    ; MANTISSA2[0]
    ; MANTISSA2[1]
    ; EXP2
    ; SIGN2
    ; MANTISSA1[0]
    ; MANTISSA1[1]
    ; EXP1
    ; SIGN 1
    ; NUM1[0]
    ; NUM1[1]
    ; NUM2[0]
    ; NUM2[1]

    push d
    push c
    push b
    push a

    bsr a ; a >> 7
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a

    push a ; sign of NUM1

    dec sp
    pop a
    add sp, 2

    bsl a
    bsr a
    bsr a
    bsr a
    push a ; exponent of NUM1

    sub sp, 2
    pop a
    add sp, 3
    bsl a ; (a << 6) >> 6
    bsl a
    bsl a
    bsl a
    bsl a
    bsl a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a

    add a, 4
    push b
    push a ; mantissa of NUM1
   
    bsr c ; a >> 7
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c

    push c ; sign of NUM2

    sub sp, 7
    pop c
    add sp, 8
    bsl c ; (a << 1) >> 3
    bsr c
    bsr c
    bsr c
    push c ; exponent of NUM2

    sub sp, 8
    pop c
    add sp, 9

    bsl c ; (a << 6) >> 6
    bsl c
    bsl c
    bsl c
    bsl c
    bsl c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c

    add c, 4
    push d
    push c ; mantissa of NUM2
    
    ; compare exponents
    sub sp, 2
    pop a
    sub sp, 3
    pop b
    add sp, 7

    cmp a, b
    mvw c, f
    bsl c
    mvw f, c
    jnz a_ge_b
        ; a is smaller than b ⇒ EXP2 < EXP1
        ; shift MANTISSA2 accordingly
        sub b, a
        pop c
        pop d
        loop:
            bsr cd
            dec b
        jnz loop
        @clear loop
        push d
        push c
        sub sp, 6
        pop b
        add sp, 4
        push b
        add sp, 2
        mvw f, 0
        jnz continue
    a_ge_b:
    sub a, b
    jnz a_gt_b 
    ; a == b ⇒ EXP2 == EXP1
    mvw f, 0
    jnz continue
    a_gt_b: 
    ; a > b ⇒ EXP2 > EXP1
    sub sp, 4
    pop c
    pop d
    loop:
       bsr cd
       dec a
    jnz loop
    @clear loop
    push d
    push c
    add sp, 2
    pop a
    sub sp, 4
    push a
    add sp, 6
    continue:
    @clear continue
    ; negate mantissas if needed
    pop c
    pop d
    dec sp
    pop a
    add sp, 4
    sub a, 1
    jnz NUM2_is_pos
        ; NUM2 < 0, take 2's complement
        mvw a, 0
        mvw b, 0
        sub b, d
        sbb a, c
        mvw c, a
        mvw d, b
        sub sp, 2 
        push d
        push c
    NUM2_is_pos:
    @clear NUM2_is_pos
    sub sp, 4
    pop a
    pop b
    dec sp
    pop c
    add sp, 8
    sub c, 1
    jnz NUM1_is_pos
        ; NUM1 < 0, take 2's complement
        mvw c, 0
        mvw d, 0
        sub d, b
        sbb c, a
        mvw a, c
        mvw b, d
        sub sp, 6
        push b
        push a
        add sp, 4
    NUM1_is_pos:
    @clear NUM1_is_pos
    ; add mantissas
    pop c
    pop d
    sub sp, 2
    pop a
    pop b
    add b, d
    adc a, c
    push f
    ; check if result is zero
    add a, 0
    jnz rest
    add b, 0
    jnz rest
        ; RES = 0
        ret
    rest:
    @clear rest
    ; if result is negative, do the right stuff
    sub sp, 3
    mvw c, 0
    push c
    add sp, 2
    pop c
    bsl c
    bsl c
    bsl c
    mvw f, c
    jnz RES_is_pos
        ; RES < 0
        mvw c, 0
        mvw d, 0
        sub d, b
        sbb c, a
        mvw a, c
        mvw b, d
        sub sp, 2
        mvw c, 1
        push c
        inc sp
    RES_is_pos:
    @clear RES_is_pos
    ; normalize result (ab)
    pop c
    add c, 6 ; NO IDEA HOW THIS WORKS BUT IT DOES
    push c
    
    loop:
        pop c
        dec c
        push c
        bsl ab
        mvw d, f
        bsr d
        bsr d
    mvw f, d 
    jnz loop
    @clear loop

    bsr ab
    bsr ab
    bsr ab
    bsr ab
    bsr ab
    bsr ab
    adc b, 0

    ; return result
    pop c
    bsl c
    bsl c
    add a, c
    pop c
    mvw d, 0
    bsr cd
    add a, d
ret
@clear a_ge_b
@clear a_gt_b

fsub:
    ; check for zero
    push a
    bsl a
    bsr a
    add a, 0
    pop a
    jnz check_NUM2
    ; a is zero
        add b, 0
        jnz check_NUM2
        ; b is zero
            mvw a, c
            mvw b, d
            ret
    check_NUM2:
    push c
    bsl c
    bsr c
    add c, 0
    pop c
    jnz continue
    ; c is zero
        add d, 0
        jnz continue
            ; d is zero
            ret
    continue:
    @clear check_NUM2
    @clear continue

    ; check if numbers are equal
    push d
    push c
    push b
    push a

    bsl ab
    bsr ab
    bsl cd 
    bsr cd

    cmp a, c
    push b
    mvw b, f
    bsr b
    mvw f, b
    pop b
    jnz continue
        ; a == c
        cmp b, d
        push a
        mvw a, f
        bsr a
        mvw f, a
        pop a
        jnz continue
            ; NUM1 == NUM2
            mvw a, 0
            mvw b, 0 ; return 0
            ret
    
    continue:
    pop a
    pop b
    pop c
    pop d
    @clear continue

    ; create local variables:
    ; STACK:
    ; MANTISSA2[0]
    ; MANTISSA2[1]
    ; EXP2
    ; SIGN2
    ; MANTISSA1[0]
    ; MANTISSA1[1]
    ; EXP1
    ; SIGN 1
    ; NUM1[0]
    ; NUM1[1]
    ; NUM2[0]
    ; NUM2[1]
    push d
    push c
    push b
    push a

    bsr a ; a >> 7
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a

    push a ; sign of NUM1

    dec sp
    pop a
    add sp, 2

    bsl a
    bsr a
    bsr a
    bsr a
    push a ; exponent of NUM1

    sub sp, 2
    pop a
    add sp, 3
    bsl a ; (a << 6) >> 6
    bsl a
    bsl a
    bsl a
    bsl a
    bsl a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a
    bsr a

    add a, 4
    push b
    push a ; mantissa of NUM1

    bsr c ; a >> 7
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c

    push c ; sign of NUM2

    sub sp, 7
    pop c
    add sp, 8
    bsl c ; (a << 1) >> 3
    bsr c
    bsr c
    bsr c
    push c ; exponent of NUM2

    sub sp, 8
    pop c
    add sp, 9

    bsl c ; (a << 6) >> 6
    bsl c
    bsl c
    bsl c
    bsl c
    bsl c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c
    bsr c

    add c, 4
    push d
    push c ; mantissa of NUM2
     
    ; compare exponents
    sub sp, 2
    pop a
    sub sp, 3
    pop b
    add sp, 7

    cmp a, b
    mvw c, f
    bsl c
    mvw f, c
    jnz a_ge_b
        ; a is smaller than b ⇒ EXP2 < EXP1
        ; shift MANTISSA2 accordingly
        sub b, a
        pop c
        pop d
        loop:
            bsr cd
            dec b
        jnz loop
        @clear loop
        push d
        push c
        sub sp, 6
        pop b
        add sp, 4
        push b
        add sp, 2
        mvw f, 0
        jnz continue
    a_ge_b:
    sub a, b
    jnz a_gt_b 
    ; a == b ⇒ EXP2 == EXP1
    mvw f, 0
    jnz continue
    a_gt_b: 
    ; a > b ⇒ EXP2 > EXP1
    sub sp, 4
    pop c
    pop d
    loop:
       bsr cd
       dec a
    jnz loop
    @clear loop
    push d
    push c
    add sp, 2
    pop a
    sub sp, 4
    push a
    add sp, 6
    continue:
    @clear continue
    ; negate mantissas if needed
    pop c
    pop d
    dec sp
    pop a
    add sp, 4
    sub a, 1
    jnz NUM2_is_pos
        ; NUM2 < 0, take 2's complement
        mvw a, 0
        mvw b, 0
        sub b, d
        sbb a, c
        mvw c, a
        mvw d, b
        sub sp, 2
        push d
        push c
    NUM2_is_pos:
    @clear NUM2_is_pos
    sub sp, 4
    pop a
    pop b
    dec sp
    pop c
    add sp, 8
    sub c, 1
    jnz NUM1_is_pos
        ; NUM1 < 0, take 2's complement
        mvw c, 0
        mvw d, 0
        sub d, b
        sbb c, a
        mvw a, c
        mvw b, d
        sub sp, 6
        push b
        push a
        add sp, 4
    NUM1_is_pos:
    @clear NUM1_is_pos
    ; sub mantissas
    pop c
    pop d
    sub sp, 2
    pop a
    pop b
    sub b, d
    sbb a, c
    push f
    ; check if result is zero
    add a, 0
    jnz rest
    add b, 0
    jnz rest
        ; RES = 0
        ret
    rest:
    @clear rest
    ; if result is negative, do the right stuff
    pop c
    bsl c
    bsl c
    bsl c
    mvw f, c
    jnz RES_is_pos
        ; RES < 0
        mvw c, 0
        mvw d, 0
        sub d, b
        sbb c, a
        mvw a, c
        mvw b, d
        sub sp, 2
        mvw c, 1
        push c
        inc sp
    RES_is_pos:
    @clear RES_is_pos
    ; normalize result (ab)
    pop c
    add c, 6 ; NO IDEA HOW THIS WORKS BUT IT DOES
    push c
    
    loop:
        pop c
        dec c
        push c
        bsl ab
        mvw d, f
        bsr d
        bsr d
    mvw f, d 
    jnz loop
    @clear loop
    bsr ab
    bsr ab
    bsr ab
    bsr ab
    bsr ab
    bsr ab
    adc b, 0

    ; return result
    pop c
    bsl c
    bsl c
    add a, c
    pop c
    mvw d, 0
    bsr cd
    add a, d
    ret
@clear a_ge_b
@clear a_gt_b

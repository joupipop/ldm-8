; math library (include standard library to use)

@const PI 3.140625
@const twoPI 6.28125
@const halfPI 1.5703125

; USE THIS NOT fdiv(1.0, x)
inv: ; inv: [a-b]:f16 → [a-b]:f16 (x → 1/x)
    mvw c, 0x77 ; magic const
    mvw d, 0xab ; magic const2
    sub d, b
    sbb c, a
    push a ; check if borrow
    mvw a, f
    bsl a
    bsl a
    mvw f, a
    jnz no_carry
        ;carry
        mvw c, 0
        mvw d, 0
    no_carry:
    pop a
    push d
    push c
    call fmul
    add a, 128
    mvw c, 0x40
    mvw d, 0x00
    call fadd ; +2
    pop c
    pop d
    call fmul ; x_1
    add b, 2 ; this helps ig
    adc a, 0
ret
@clear no_carry

ipow: ; ipow: [a-b]:f16, [c]:int → [a-b]:f16 (x, n → x^n)
    add c, 0
    jnz n_is_not_zero
        ; n = 0
        mvw a, 0x3c
        mvw b, 0x00
        ret ; ret 1.0
    n_is_not_zero:
    mvw d, f
    bsr d
    bsr d
    bsr d
    mvw f, d
    jnz n_is_neg
        ; n > 0
        mvw d, c
        bsl d
        bsl d
        bsl d
        bsl d
        mvw f, d
        jnz n_is_even
            ; n is odd
            push b
            push a
            push c
            mvw c, a
            mvw d, b
            call fmul
            pop c
            dec c
            bsr c
            call ipow
            pop c
            pop d
            call fmul
        ret
        n_is_even:
            push c
            mvw c, a
            mvw d, b
            call fmul
            pop c
            bsr c
            call ipow
        ret
    n_is_neg:
        mvw d, 0
        sub d, c
        mvw c, d
        call ipow
        call inv
    ret

trunc: ; floor: [a-b]:f16 → [a-b]:f16 (x → integer part of x)
    ; check if x is larger than 1024 in which case return x
    cmp a, 0x64
    mvw c, f
    bsl c
    mvw d, 255
    sub d, c ; invert c
    mvw f, d
    jnz smaller
        ; x > 1024
    ret
    smaller:
    mvw d, 0
    mvw c, a
    bsr cd
    bsr cd
    bsr cd
    bsr cd
    bsr cd
    bsr cd
    bsr cd ; c contains sign
    push c
    bsr d
    bsr d 
    bsr d ; d contains exponent
    sub d, 15
    mvw c, f
    bsl c
    bsl c
    bsl c
    mvw f, c
    jnz exp_is_pos
        ; exp < 0
        mvw b, 0
        pop a
        bsr ab
    ret
    exp_is_pos:
    pop c
    bsl a
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
    bsr b
    bsl b
    inc b
    add a, 4
    push c
    mvw c, 10
    sub c, d
    push c
    loop:
        bsr ab
        dec c
    jnz loop
    pop c
    loop:
        bsl ab
        dec c
    jnz loop
    sub a, 4
    add d, 15
    bsl d
    bsl d
    add a, d
    pop c
    mvw d, 0
    bsr cd
    add a, d
    bsl d
    bsl d
    bsl d
ret
@clear exp_is_pos
@clear loop

fmod: ; fmod : [a-b]:f16, [c-d]:f16 → [a-b]:f16 (x, y → x % y)
    push c
    cmp a, c
    mvw c, f
    bsr c
    mvw f, c
    jnz a_ne_c
        ; a = c
        cmp b, d
        mvw c, f
        bsr c
        mvw f, c
        jnz b_ne_d
            ; b = d => x = y
            mvw a, 0
            mvw b, 0
        ret
        b_ne_d:
            bsl c
            bsl c
            mvw f, c
            jnz x_gt_y
                ; b < d => x < y
                ret
    a_ne_c:
        bsl c
        bsl c
        mvw f, c
        jnz x_gt_y
            ; a < c => x < y
            ret
    x_gt_y:
        pop c
        bsl c
        bsr c
        push d
        push c
        push a
        bsl a
        bsr a
        push b
        push a
        push d
        push c
        call fdiv
        call trunc
        pop c
        pop d
        call fmul
        add a, 128
        pop c
        pop d
        call fadd
        pop c
        bsr c
        bsr c
        bsr c
        mvw f, c
        jnz x_is_pos
            ; x < 0
            pop c
            pop d
            add a, 128
            call fadd
        x_is_pos:
ret
@clear a_ne_c
@clear b_ne_d
@clear x_gt_y
@clear x_is_pos

sin: ; sin: [a-b]:f16 → [a-b]:f16 (x → sin(x))
    mvw c, twoPI[0]
    mvw d, twoPI[1]
    call fmod
    mvw c, PI[0]
    mvw d, PI[1]
    push a
    bsl a
    bsr a
    cmp a, c
    pop a
    mvw c, f
    bsr c
    mvw f, c
    jnz a_ne_c
        ; a = c
        cmp b, d
        mvw c, f
        bsr c
        mvw f, c
        jnz b_ne_d
            ; b = d => x = pi
            mvw a, 0
            mvw b, 0 ; sin(pi) = 0
        ret
        b_ne_d:
            bsl c
            bsl c
            mvw f, c
            jnz x_gt_pi
                ; b < d => x < pi
                mvw f, 0
                jnz x_lt_pi
    a_ne_c:
        bsl c
        bsl c
        mvw f, c
        jnz x_gt_pi
            ; a < c => x < pi
            mvw f, 0
            jnz x_lt_pi

    x_gt_pi:
        mvw c, PI[0]
        mvw d, PI[1]
        call fsub
        add a, 128
    x_lt_pi:
    @clear a_ne_c
    @clear b_ne_d
    @clear x_lt_pi
    @clear x_gt_pi
    mvw c, halfPI[0]
    mvw d, halfPI[1]
    push a
    bsl a
    bsr a
    cmp a, c
    pop a
    mvw c, f
    bsr c
    mvw f, c
    jnz a_ne_c
        ; a = c
        cmp b, d
        mvw c, f
        bsr c
        mvw f, c
        jnz b_ne_d
            ; b = d => x = ±pi/2
            bsr a
            bsr a
            bsr a
            mvw f, a
            jnz x_is_pos
    ; x = -pi/2
                mvw a, 0xbc
                mvw b, 0x00 ; sin(-pi/2) = -1
            ret
            x_is_pos:
            @clear x_is_pos
                ; x = pi/2
                mvw a, 0x3c
                mvw b, 0x00 ; sin(pi/2) = 1
            ret
        b_ne_d:
            bsl c
            bsl c
            mvw f, c
            jnz b_gt_d
                ; b < d => |x| < pi/2
                mvw f, 0
                jnz x_lt_halfpi
            b_gt_d:
                ; b > d => |x| > pi/2
                mvw f, 0
                jnz x_gt_halfpi
    a_ne_c:
        bsl c
        bsl c
        mvw f, c
        jnz a_gt_c
            ; a < c => |x| < pi/2
            mvw f, 0
            jnz x_lt_halfpi
        a_gt_c:
            ; a > c => |x| > pi/2
            mvw f, 0
            jnz x_gt_halfpi

    x_gt_halfpi:
        push a
        bsr a
        bsr a
        bsr a
        mvw c, PI[0]
        mvw d, PI[1]
        mvw f, a
        jnz x_is_pos
            ; x < 0
            pop a
            add a, 128
            add c, 128
            call fadd
            mvw f, 0
            jnz x_lt_halfpi
        x_is_pos:
            ; x >= 0
            pop a
            add a, 128
            call fadd
    x_lt_halfpi:
    @clear a_ne_c
    @clear b_ne_d
    @clear b_gt_d
    @clear a_gt_c
    @clear x_lt_halfpi
    @clear x_gt_halfpi
    @clear x_is_pos
    ; RES[0]
    ; RES[1]
    ; NUM[0]
    ; NUM[1]
    push b
    push a
    push b
    push a
    mvw c, 3
    call ipow
    mvw c, 0xb1
    mvw d, 0x55
    call fmul
    pop c
    pop d
    call fadd
    push b
    push a
    sub sp, 2
    pop a
    pop b
    add sp, 4
    mvw c, 5
    call ipow
    mvw c, 0x20
    mvw d, 0x44
    call fmul
    pop c
    pop d
    call fadd
    push b
    push a
    sub sp, 2
    pop a
    pop b
    add sp, 4
    mvw c, 7
    call ipow
    mvw c, 0x81
    mvw d, 0x4c
    call fmul
    pop c
    pop d
    call fadd
    push b
    push a
    sub sp, 2
    pop a
    pop b
    add sp, 4
    mvw c, 9
    call ipow
    mvw c, 0x00
    mvw d, 0x2e
    call fmul
    pop c
    pop d
    call fadd
ret

cos:
    mvw c, twoPI[0]
    mvw d, twoPI[1]
    call fmod
    mvw c, PI[0]
    mvw d, PI[1]
    bsl a
    bsr a
    cmp a, c
    mvw c, f
    bsr c
    mvw f, c
    jnz a_ne_c
        ; a = c
        cmp b, d
        mvw c, f
        bsr c
        mvw f, c
        jnz b_ne_d
            ; b = d => x = pi
            mvw a, 0xbc
            mvw b, 0x00
        ret
        b_ne_d:
            bsl c
            bsl c
            mvw f, c
            jnz b_gt_d
                ; b < d => x < pi
                mvw f, 0
                jnz x_lt_pi
            b_gt_d:
                ; b > d => x > pi
                mvw f, 0
                jnz x_gt_pi
    a_ne_c:
        bsl c
        bsl c
        mvw f, c
        jnz a_gt_c
            ; a < c => x < pi
            mvw f, 0
            jnz x_lt_pi
        a_gt_c:
            ; a > c => x > pi
            mvw f, 0
            jnz x_gt_pi
    x_gt_pi:
        add a, 128
        mvw c, twoPI[0]
        mvw d, twoPI[1]
        call fadd
    x_lt_pi:
    @clear a_ne_c
    @clear b_ne_d
    @clear b_gt_d
    @clear a_gt_c
    @clear x_lt_pi
    @clear x_gt_pi
    mvw c, 0
    push c ; bool negate_result
    mvw c, halfPI[0]
    mvw d, halfPI[1]
    push a
    bsl a
    bsr a
    cmp a, c
    pop a
    mvw c, f
    bsr c
    mvw f, c
    jnz a_ne_c
        ; a = c
        cmp b, d
        mvw c, f
        bsr c
        mvw f, c
        jnz b_ne_d
            ; b = d => x = ±pi/2
            mvw a, 0x00
            mvw b, 0x00
        ret
        b_ne_d:
            bsl c
            bsl c
            mvw f, c
            jnz b_gt_d
                ; b < d => x < pi/2
                mvw f, 0
                jnz x_lt_halfpi
            b_gt_d:
                ; b > d => x > pi/2
                mvw f, 0
                jnz x_gt_halfpi
    a_ne_c:
        bsl c
        bsl c
        mvw f, c
        jnz a_gt_c
            ; a < c => x < pi/2
            mvw f, 0
            jnz x_lt_halfpi
        a_gt_c:
            ; a > c => x > pi/2
            mvw f, 0
            jnz x_gt_halfpi

    x_gt_halfpi:
        pop c
        add c, 128
        push c
        mvw c, PI[0]
        mvw d, PI[1]
        call fsub
    x_lt_halfpi:
    @clear a_ne_c
    @clear b_ne_d
    @clear b_gt_d
    @clear a_gt_c
    @clear x_lt_halfpi
    @clear x_gt_halfpi
    mvw c, 0x3c
    mvw d, 0x00
    push b
    push a
    push d
    push c
    mvw c, 2
    call ipow
    mvw c, 0xb8
    mvw d, 0x00
    call fmul
    pop c
    pop d
    call fadd
    push b
    push a
    sub sp, 2
    pop a
    pop b
    add sp, 4
    mvw c, 4
    call ipow
    mvw c, 0x29
    mvw d, 0x55
    call fmul
    pop c
    pop d
    call fadd
    push b
    push a
    sub sp, 2
    pop a
    pop b
    add sp, 4
    mvw c, 6
    call ipow
    mvw c, 0x95
    mvw d, 0xb0
    call fmul
    pop c
    pop d
    call fadd
    push b
    push a
    sub sp, 2
    pop a
    pop b
    add sp, 4
    mvw c, 8
    call ipow
    mvw c, 0x01
    mvw d, 0xa0
    call fmul
    pop c
    pop d
    call fadd
    sub sp, 2
    pop c
    add a, c
    ret
ret




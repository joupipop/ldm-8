@include spigot/array.asm
@dba x 0 0 0
@db q 0
@db predigit 0
@db nines 0
@dd index 0
@dd address 0 ; *(array[index])
@dba value 0 0 0
@dba value2 0 0 0
@db temp_quotient 0
@dd temp_remainder 0

@const size 32486 ;32485 88
@const sizem1 32485
@const digit_num 10000

big_loop:
    push d
    push c
    ; big_loop
    stw a, q
    
    mvw c, sizem1[0]
    mvw d, sizem1[1]
    small_loop:
        push d
        push c
        ; small_loop
            ; sets x to array[i]*10 + q*(i+1)
            stw c, index[0]
            stw d, index[1]
            bsl cd
            stw c, address[0]
            stw d, address[1]

            mvw a, array[0]
            mvw b, array[1]
            add b, d
            adc a, c
            ldw c, *ab
            inc b
            adc a, 0
            ldw d, *ab
            mvw b, 0
            bsl cd
            adc b, 0
            stw d, value[2]
            stw c, value[1]
            stw b, value[0]

            bsl b
            bsl cd
            adc b, 0
            bsl b
            bsl cd
            adc b, 0
            ldw a, value[2]
            add a, d
            stw a, value[2]
            ldw a, value[1]
            adc a, c
            stw a, value[1]
            ldw a, value[0]
            adc a, b
            stw a, value[0]

            ldw a, q
            ldw c, index[0]
            ldw d, index[1]
            inc d
            adc c, 0
            mvw b, 0
            stw b, x[2]
            stw b, x[1]
            stw b, x[0]
            q_loop:
                ldw b, x[2]
                add b, d
                stw b, x[2]
                ldw b, x[1]
                adc b, c
                stw b, x[1]
                ldw b, x[0]
                adc b, 0
                stw b, x[0]

                dec a
                mvw b, f
                bsl b
                bsl b
                mvw f, b
                jnz q_loop

            ldw b, x[2]
            sub b, d
            stw b, x[2]
            ldw b, x[1]
            sbb b, c
            stw b, x[1]
            ldw b, x[0]
            sbb b, 0
            stw b, x[0]

            ldw a, value[2]
            ldw b, x[2]
            add b, a
            stw b, x[2]
            ldw a, value[1]
            ldw b, x[1]
            adc b, a
            stw b, x[1]
            ldw a, value[0]
            ldw b, x[0]
            adc b, a
            stw b, x[0]
            mvw a, 0
            mvw b, 0

            ; sets array[i] to x % (2*i+1) and sets q to x / (2*i+1)
            mvw b, 0
            ldw c, index[0]
            ldw d, index[1]
            bsl cd
            adc b, 0
            inc d
            adc c, 0
            adc b, 0
            stw b, value2[0]
            stw c, value2[1]
            stw d, value2[2]

            ldw a, x[2]
            stw a, value[2]
            ldw a, x[1]
            stw a, value[1]
            ldw a, x[0]
            stw a, value[0]
            mvw a, 0
            div_loop:
                inc a
                ldw c, value[2]
                ldw d, value2[2]
                sub c, d
                stw c, value[2]
                ldw c, value[1]
                ldw d, value2[1]
                sbb c, d
                stw c, value[1]
                ldw c, value[0]
                ldw d, value2[0]
                sbb c, d
                stw c, value[0]
                mvw b, f
                bsl b
                bsl b
                mvw f, b
                jnz div_loop
            dec a
            stw a, q
            ldw c, value[2]
            ldw d, value2[2]
            add c, d
            stw c, value[2]
            ldw c, value[1]
            ldw d, value2[1]
            adc c, d
            stw c, value[1]
            ldw c, value[0]
            ldw d, value2[0]
            adc c, d
            stw c, value[0]

            mvw a, array[0]
            mvw b, array[1]
            ldw c, address[0]
            ldw d, address[1]
            add b, d
            adc a, c
            ldw c, value[1]
            stw c, *ab
            inc b
            adc a, 0
            ldw c, value[2]
            stw c, *ab

        ; end small_loop
        pop c
        pop d
        dec d
        sbb c, 0
        cmp c, 0xff
        mvw a, f
        bsr a
        mvw f, a
        jnz small_loop
            cmp d, 0xff
            mvw a, f
            bsr a
            mvw f, a
            jnz small_loop
        
        ; sets array[0] to q % 10 and sets q to q / 10
        ldw c, q
        mvw d, 10
        mvw a, 0
        div10_loop:
            inc a
            sub c, d
            mvw b, f
            bsl b
            bsl b
            mvw f, b
            jnz div10_loop
        dec a
        stw a, q
        add c, d
        mvw a, array[0]
        mvw b, array[1]
        mvw d, 0
        stw d, *ab
        inc b
        adc a, 0
        stw c, *ab
        ldw a, q
        sub a, 9
        jnz q_is_not_9
            ; q == 9
            ldw a, nines
            inc a
            stw a, nines
            
            mvw f, 0
            jnz big_loop_prologue
        q_is_not_9:
        ldw a, q
        sub a, 10
        jnz q_is_not_10
            ; q == 10
            ldw a, predigit
            inc a
            out a
            ldw a, nines
            mvw b, 0
            add a, b
            jnz zero_loop
                mvw f, 0
                jnz end_zero_loop
            zero_loop:
                out b
                dec a
                jnz zero_loop
            end_zero_loop:
            stw b, predigit
            stw b, nines
            mvw f, 0
            jnz big_loop_prologue
        q_is_not_10:
            ldw a, predigit
            out a
            ldw b, q
            stw b, predigit
            ldw a, nines
            add a, 0
            mvw b, 0
            stw b, nines
            mvw b, f
            add b, 16
            mvw f, b
            jnz big_loop_prologue
                ; nines != 0
                mvw b, 9
                nine_loop:
                    dec a
                    out b
                    jnz nine_loop
        

    ; end big_loop
    big_loop_prologue:
    pop c
    pop d
    inc d
    adc c, 0
    cmp c, digit_num[0]
    mvw a, f
    bsr a
    mvw f, a
    jnz big_loop
        cmp d, digit_num[1]
        mvw a, f
        bsr a
        mvw f, a
        jnz big_loop
halt

    


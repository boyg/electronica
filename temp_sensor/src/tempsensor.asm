; Register definitions
$NOLIST
$MODLP51
$LIST

; Write main to starting address
ORG 0000H
   ljmp Main

; Include files
$NOLIST
$include(LCD_4bit.inc) ; A library of LCD related functions and utility macros
$include(math32.inc) ; A library of 32bit math functions and utility macros
$LIST

; Symbolic constants
CLK     EQU 22118400
BAUD    EQU 115200
BRG_VAL EQU (0x100-(CLK/(16*BAUD)))

; LCD hardware wiring
LCD_RS EQU P1.1
LCD_RW EQU P1.2
LCD_E  EQU P1.3
LCD_D4 EQU P3.2
LCD_D5 EQU P3.3
LCD_D6 EQU P3.4
LCD_D7 EQU P3.5

; ADC hardware wiring
CE_ADC  EQU P2.0
MY_MOSI EQU P2.1
MY_MISO EQU P2.2
MY_SCLK EQU P2.3

; Misc hardware wiring
MODE_BUTTON EQU P2.4

; Direct access variables (address 0x30 - 0x7F) used by math32 library
DSEG at 30H
x:      ds 4
y:      ds 4
bcd:    ds 5
Result: ds 2
buffer: ds 30

mode_flag: ds 1 ; Flag to switch between temperature units. 0 is Celsius, 1 is Fahrenheit

BSEG
mf: dbit 1 ; Math flag

CSEG

; MACRO: BCD number to PuTTY
Send_BCD mac
	push ar0
	mov r0, %0
	lcall ?Send_BCD
	pop ar0
endmac

?Send_BCD:
	push acc
	; Write most significant digit
	mov a, r0
	swap a
	anl a, #0fh
	orl a, #30h
	lcall PutChar
	; write least significant digit
	mov a, r0
	anl a, #0fh
	orl a, #30h
	lcall PutChar
	pop acc
	ret

; LCD Strings
newline:
    db  ' ', '\r', '\n', 0

Celsius_Format:
;       123456789A
	db 'Temp:    C', 0

Fahrenheit_Format:
;       123456789A
	db 'Temp:    F', 0

; SUBROUTINE: Configure the serial port and baud rate
InitSerialPort:
    ; Since the reset button bounces, we need to wait a bit before
    ; sending messages, otherwise we risk displaying gibberish!
    mov R1, #222
    mov R0, #166
    djnz R0, $   ; 3 cycles->3*45.21123ns*166=22.51519us
    djnz R1, $-4 ; 22.51519us*222=4.998ms
    
    ; Now we can proceed with the configuration
	orl	PCON,#0x80
	mov	SCON,#0x52
	mov	BDRCON,#0x00
	mov	BRL,#BRG_VAL
	mov	BDRCON,#0x1E ; BDRCON=BRR|TBCK|RBCK|SPD;
    ret

; SUBROUTINE: Initialize SPI
INIT_SPI:
	setb MY_MISO ; Make MISO an input pin
	clr MY_SCLK  ; Mode 0,0 default
	ret

; SUBROUTINE: Check what mode we are in
Check_Mode:
	; Check if button is pressed
	jb MODE_BUTTON, Check_Mode_End
	Wait_Milli_Seconds(#125)
	jb MODE_BUTTON, Check_Mode_End

	; Change the flag and clear it if it overflows
	clr a
	mov a, mode_flag
	add a, #01H
	cjne a, #02H, Update_Mode
	mov a, #00H

Update_Mode:
	mov mode_flag, a

Check_Mode_End:
	ret

; SUBROUTINE: Bit-bang 2 bits, wait, then convert and send
Fetch_Voltage:
	clr CE_ADC
	mov R0, #00000001B ; Start bit:1
	lcall DO_SPI_G
	mov R0, #10000000B ; Single ended, read channel 0
	lcall DO_SPI_G
	mov a, R1 ; R1 contains bits 8 and 9
	anl a, #00000011B ; We need only the two least significant bits
	mov Result+1, a ; Save result high.
	mov R0, #55H ; It doesn't matter what we transmit...
	lcall DO_SPI_G
	mov Result, R1 ; R1 contains bits 0 to 7. Save result low.
	setb CE_ADC
	Wait_Milli_Seconds(#100)
	lcall Convert_And_Send
	ret

; SUBROUTINE: Convert temperature, send to PuTTY, and display on LCD
Convert_And_Send:
	mov a, mode_flag
	cjne a, #00H, Skip_Celsius

	lcall Volts_To_Celsius
	Set_Cursor(1,1)
    Send_Constant_String(#Celsius_Format)
    sjmp Convert_Finished

Skip_Celsius:
	lcall Volts_To_Fahrenheit
	Set_Cursor(1,1)
    Send_Constant_String(#Fahrenheit_Format)

Convert_Finished:
    ; Can't print degree symbol!
    ;Set_Cursor(1,9)
    ;Display_char(#176)

	Send_BCD(bcd)
	Set_Cursor(1,7)
	Display_BCD(bcd)
	
	mov DPTR, #newline
	lcall sendstring

	ret

; SUBROUTINE: Use math32 library to perform volts-to-celsius conversion
Volts_To_Celsius:
	mov x+0, Result + 0
	mov x+1, Result + 1
	mov x+2, #0x00
	mov x+3, #0x00
	
	; Celsius = Volts * 410 / 1023 - 273
	Load_Y(410)
	lcall mul32 
	Load_Y(1023)
	lcall div32
	Load_Y(273)
	lcall sub32

	lcall hex2bcd

	ret

; SUBROUTINE: Use math32 library to perform volts-to-fahrenheit conversion
Volts_To_Fahrenheit:
	mov x+0, Result + 0
	mov x+1, Result + 1
	mov x+2, #0x00
	mov x+3, #0x00
	
	Load_Y(410)
	lcall mul32 
	Load_Y(1023)
	lcall div32
	Load_Y(273)
	lcall sub32

	; Fahrenheit = Celsius * 9 / 5 + 32
	Load_Y(9)
	lcall mul32
	Load_Y(5)
	lcall div32
	Load_Y(32)
	lcall add32

	lcall hex2bcd

	ret

; SUBROUTINE: Send a constant-zero-terminated string using the serial port
SendString:
    clr A
    movc A, @A+DPTR
    jz SendStringDone
    lcall PutChar
    inc DPTR
    sjmp SendString

; SUBROUTINE: Send a character using the serial port
PutChar:
    jnb TI, PutChar
    clr TI
    mov SBUF, a
    ret    

SendStringDone:
    ret ; returns to main, not SendString

; SUBROUTINE: Perform bit bang SPI 
DO_SPI_G:
	mov R1, #0 ; Received byte stored in R1
	mov R2, #8 ; Loop counter (8-bits)
DO_SPI_G_LOOP:
	mov a, R0 ; Byte to write is in R0
	rlc a ; Carry flag has bit to write
	mov R0, a
	mov MY_MOSI, c
	setb MY_SCLK ; Transmit
	mov c, MY_MISO ; Read received bit
	mov a, R1 ; Save received bit in R1
	rlc a
	mov R1, a
	clr MY_SCLK
	djnz R2, DO_SPI_G_LOOP
	ret

; MAIN: Initialize LCD, serial port, and SPI, then continually fetch voltage
Main:
    mov SP, #7FH ; Set the stack pointer to the begining of idata

    lcall LCD_4BIT    
    lcall InitSerialPort
    lcall INIT_SPI
    mov mode_flag, #00H

Loop:
	lcall Check_Mode
	lcall Fetch_Voltage
	sjmp Loop
    
END

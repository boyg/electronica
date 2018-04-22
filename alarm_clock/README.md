# LCD alarm clock

This 24-hour alarm clock comes with a settable weekday alarm and a weekend alarm that the user can toggle. The alarms trigger a speaker that produces a beeping sound. Switches are used to toggle/view alarms and pause time; pushbuttons are used to adjust time.

The alarm clock is programmed with an Atmel AT89LP51RC2 microcontroller in 8051 assembly, and uses the system clock, along with its timer/interrupt functionalities, to keep track of time. The timer is also used to generate a 2048 Hz square wave that is used to sound a CEM-1203(42) buzzer, which is amplified by a MOSFET.

The assembly code for the device is primarily contained in the alarm.asm file. Helpful macros are contained in the LCD_4bit.inc file and register definitions are in the MODLP51.txt file, with full credit to Dr. Jesus Calvino-Fraga. The .hex and .asm files were produced by an A51 compiler, with the .hex file being the machine code that is flashed to the microcontroller. Finally, the datasheet and instruction set for the microcontroller have been added for convenience.

<img src="https://user-images.githubusercontent.com/32561115/35129454-8f1f7986-fc70-11e7-9285-d6fe73f0b1eb.jpg" width="420"> <img src="https://user-images.githubusercontent.com/32561115/35129326-00acfe58-fc70-11e7-8fbd-d933edeb3e4f.jpg" width="440">

## Demonstration

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/vrtLpjqpfDs/0.jpg)](http://www.youtube.com/watch?v=vrtLpjqpfDs)

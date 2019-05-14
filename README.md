# Temperature sensor

This temperature sensor prints out the current temperature on an LCD screen and produces a live temperature plot using a Python script. The user can toggle between Celsius mode and Fahrenheit mode with a pushbutton.

An LM335 reads the temperature (using an LM4040DIZ-4.1 to set the reference voltage) and sends it to an MCP3008 ADC as an analog voltage. The ADC converts it to a digital signal and uses bit banging to transmit the voltage to an AT89LP51RC2 microcontroller programmed in 8051 assembly. The microcontroller converts the voltage to a temperature reading, displays it on an LCD screen, and transmits the temperature (through a USB serial port) to a computer, where a Python script reads from the serial port and uses matplotlib to produce a plot of temperature over time.

The assembly code for the device is primarily contained in the tempsensor.asm file, and the python script is tempplot.py. LCD macros are contained in LCD_4bit.inc, register definitions are in MODLP51.txt, and math32.inc is a library of macros to perform 32-bit math are included with full credit to Dr. Jesus Calvino-Fraga. The .hex and .asm files are produced by an A51 compiler, with the .hex file being the machine code that is flashed to the microcontroller. Finally, the datasheets and instruction set for the microcontroller have been added for convenience.

<img src="https://user-images.githubusercontent.com/32561115/35721227-e530bdcc-07a5-11e8-8179-c7ae603f4b98.jpg" width="420"> <img src="https://user-images.githubusercontent.com/32561115/35721232-e73806fc-07a5-11e8-9a52-de5aae6bc7bf.jpg" width="440">

## Demonstration

[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/1yvg7m5pO5Y/0.jpg)](https://www.youtube.com/watch?v=1yvg7m5pO5Y)

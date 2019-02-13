import os
import pygame
from pygame.locals import *
import time

import serial
import serial.tools.list_ports
import codecs

#PF_PORT = '/dev/tty.Transmitter-DevB'
#PF_PORT = '/dev/tty.AHH-DevB'
PF_PORT = '/dev/tty.usbserial-DN03PX0Q'
TM_PORT = '/dev/tty.usbserial-DN036GC4'

PF_BAUD_RATE = 115200
TM_BAUD_RATE = 57600


class Data_Control(object):
    """User input string"""
    mode = None
    
    """Serial port for transmitter""" 
    tm = None
    
    """Data associated with PS4 controller"""
    controller = None
    axis_data = None
    button_data = None
    hat_data = None
    ps4_dp1 = None
    ps4_dp2 = None

    """Data associated with powerfist"""
    pf = None
    pf_data = None
    pf_dp1 = None
    pf_dp2 = None
    
    def init_tm(self):
        print('Establishing transmitter connection...')
        while True:
            try:
                self.tm = serial.Serial(TM_PORT, TM_BAUD_RATE, timeout=1) # Different timeout than powerfist?
                break
            except:
                pass
    
    def init_ps4(self):
        print('Establishing PS4 controller connection...')
        while True:
            try:
                pygame.init()
                pygame.joystick.init()
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                break
            except:
                pygame.quit()
        
        if not self.axis_data:
            self.axis_data = {}
        
        if not self.button_data:
            self.button_data = {}
            for i in range(self.controller.get_numbuttons()):
                self.button_data[i] = False
    
        if not self.hat_data:
            self.hat_data = {}
            for i in range(self.controller.get_numhats()):
                self.hat_data[i] = (0, 0)
    
    def init_pf(self):
        print('Establishing powerfist connection...')
        while True:
            try:
                self.pf = serial.Serial(PF_PORT, PF_BAUD_RATE, timeout=100)
                self.pf.reset_input_buffer()
                break
            except:
                pass

    def init_auto(self):
        for i in range(0,100):
            self.tm.write(bytes([0b00000101]))
            self.tm.write(bytes([0b00000000]))
            time.sleep(0.005)
        for i in range(0,100):
            self.tm.write(bytes([0b00000011]))
            self.tm.write(bytes([0b00000000]))
            time.sleep(0.005)
        for i in range(0,100):
            self.tm.write(bytes([0b00000001]))
            self.tm.write(bytes([0b00000010]))
            time.sleep(0.005)
        for i in range(0,100):
            self.tm.write(bytes([0b00000001]))
            self.tm.write(bytes([0b00000100]))
            time.sleep(0.005)

    def fetch_ps4_data(self):
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                self.axis_data[event.axis] = round(event.value,2)
            elif event.type == pygame.JOYBUTTONDOWN:
                self.button_data[event.button] = True
            elif event.type == pygame.JOYBUTTONUP:
                self.button_data[event.button] = False
            elif event.type == pygame.JOYHATMOTION:
                self.hat_data[event.hat] = event.value

    def package_ps4_dp1(self):
        self.ps4_dp1 = 0b00000001

        try:
            """Acquire x-axis joystick data"""
            x = self.axis_data[0]
            """Filter noise"""
            if x < 0.1 and x > -0.1:
                x = 0
            """Normalize it between [-7, 7]"""
            x = int(7*x)
            """Insert sign bit in position 7"""
            if x < 0:
                x = -x
                self.ps4_dp1 |= (1 << 6)
            """Insert magnitude in position 6-4"""
            self.ps4_dp1 |= (x << 3)
            """Insert open bit in position 3"""
            if self.button_data[4]:
                self.ps4_dp1 |= (1 << 2)
            """Insert close bit in position 2"""
            if self.button_data[5]:
                self.ps4_dp1 |= (1 << 1)
            """Convert type int to type bytes for transmission"""
            self.ps4_dp1 = bytes([self.ps4_dp1])

        except:
            print('Error packaging data packet 1 from PS4 controller')

    def package_ps4_dp2(self):
        self.ps4_dp2 = 0b00000000

        try:
            """Acquire y-axis joystick data"""
            y = (self.axis_data[4] - self.axis_data[5]) / 2
            """Filter noise"""
            if y < 0.1 and y > -0.1:
                y = 0
            """Normalize it between [-7, 7]"""
            y = int(7*y)
            """Insert sign bit in position 7"""
            if y < 0:
                y = -y
                self.ps4_dp2 |= (1 << 6)
            """Insert magnitude in position 6-4"""
            self.ps4_dp2 |= (y << 3)
            """Insert auto bit in position 3"""
            if self.button_data[12]:
                self.ps4_dp2 |= (1 << 2)
            """Insert boost bit in position 2"""
            if self.button_data[1]:
                self.ps4_dp2 |= (1 << 1)
            """Convert type int to type bytes for transmission"""
            self.ps4_dp2 = bytes([self.ps4_dp2])

        except:
            print('Error packaging data packet 2 from PS4 controller')

    def send_ps4_data(self):
        try:
            self.tm.write(self.ps4_dp1)
            self.tm.write(self.ps4_dp2)
        except:
            print('Unable to send data to transmitter. Attempting to re-connect to serial port')
            try:
                self.tm = serial.Serial(TM_PORT, TM_BAUD_RATE, timeout=1)
            except:
                pass

    def fetch_pf_data(self):
        try:
            self.pf.write(0x30)
            self.pf_data = self.pf.readline().decode('utf-8')
            self.pf.reset_input_buffer()
            print(self.pf.in_waiting)

        except:
            print('Error fetching powerfist data, trying to open serial port again')

            try:
                self.pf = serial.Serial(PF_PORT, 115200, timeout=100)

            except:
                pass

    def package_pf_dp1(self):
        self.pf_dp1 = 0b00000001

        try:
            """Acquire x-axis data"""
            x = int(self.pf_data.split()[0])
            """Insert sign bit in position 7"""
            if x < 0:
                x = -x
                self.pf_dp1 |= (1 << 6)
            """Insert magnitude in position 6-4"""
            self.pf_dp1 |= (x << 3)
            """Acquire claw/boost data"""
            press = int(self.pf_data.split()[2])
            """Insert open bit in position 3"""
            if press == 0:
                self.pf_dp1 |= (1 << 2)
            """Insert close bit in position 2"""
            if press == 1:
                self.pf_dp1 |= (1 << 1)
            """Convert type int to type bytes for transmission"""
            self.pf_dp1 = bytes([self.pf_dp1])

        except:
            print('Error packaging first data packet from powerfist, check pf_data')

    def package_pf_dp2(self):
        self.pf_dp2 = 0b00000000

        try:
            """Acquire y-axis data"""
            y = int(self.pf_data.split()[1])
            """Insert sign bit in position 7"""
            if y < 0:
                y = -y
                self.pf_dp2 |= (1 << 6)
            """Insert magnitude in position 6-4"""
            self.pf_dp2 |= (y << 3)
            """Convert type int to type bytes for transmission"""
            self.pf_dp2 = bytes([self.pf_dp2])
                
        except:
            print('Error packaging second data packet from powerfist, check pf_data')

    def send_pf_data(self):
        try:
            self.tm.write(self.pf_dp1)
            self.tm.write(self.pf_dp2)
        except:
            print('Unable to send data to transmitter. Attempting to re-connect to serial port')
            try:
                self.tm = serial.Serial(TM_PORT, TM_BAUD_RATE, timeout=1)
            except:
                pass

    def setup(self):
        self.init_tm()
        
        print('Welcome to the MCAR interface!')
        print('This device has 3 modes: PS4, Powerfist, and Autonomous.')
        self.mode = input('Enter your desired mode of operation: ')
        
        if self.mode.lower() == 'ps4':
            self.init_ps4()
        
        elif self.mode.lower() == 'powerfist':
            self.init_pf()
        
        elif self.mode.lower() == 'autonomous' or self.mode.lower() == 'auto':
            self.init_auto()

    def loop(self):
        while True:
            if self.mode.lower() == 'ps4':
                self.fetch_ps4_data()
                self.package_ps4_dp1()
                self.package_ps4_dp2()
                self.send_ps4_data()

                try:
                    print('Running in PS4 mode.')
                    print('Press "L1", "R1", "X", "PS" to enter autonomous mode.')
                    print('ps4_dp1:', '{0:b}'.format(ord(self.ps4_dp1)))
                    print('ps4_dp2:', '{0:b}'.format(ord(self.ps4_dp2)))
                except:
                    print('PS4 data packets not ready to be printed')
        
            elif self.mode.lower() == 'powerfist':
                self.fetch_pf_data()
                self.package_pf_dp1()
                self.package_pf_dp2()
                self.send_pf_data()

                try:
                    print('Running in powerfist mode.')
                    print('pf_dp1:', '{0:b}'.format(ord(self.pf_dp1)))
                    print('pf_dp2:', '{0:b}'.format(ord(self.pf_dp2)))
                except:
                    print('Powerfist data packets not ready to be printed')

            elif self.mode.lower() == 'autonomous' or self.mode.lower() == 'auto':
                print('Running in autonomous mode.')
                time.sleep(0.01)

            try:
                os.system('clear')
            except:
                os.system('cls')

if __name__ == '__main__':
    dc = Data_Control()
    dc.setup()
    dc.loop()
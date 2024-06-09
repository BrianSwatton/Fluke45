#!/usr/bin/python3

#   fluke45.py  [Alpha]

#   Module for getting data from the Fluke 45 bench multimeter.
#   Use or modify freely.

#   Brian Swatton, June 2024

__version__ = '1.0 a8'
__date__ = '9th June 2024, 12:23'

import sys, os, time
import logging

try:
    import serial
    import serial.tools.list_ports
except ImportError as impErr:
    print(f"[Error]: Failed to import - {impErr.args[0]}")
    print('\n !  This program requires the python module "pyserial"')
    print(' !  to be installed in your python environment.\n')
    sys.exit(1)


class Fluke45(serial.Serial):
    modbits = {64:'comp', 32:'rel', 16:'dbw', 8:'db', 4:'hold', 2:'max', 1:'min' }
    funcs = {'VDC':['Voltage', 'V',['dc']]}
    funcs['VAC'] = ['Voltage', 'V',['ac']]
    funcs['ADC'] = ['Current', 'A',['dc']]
    funcs['AAC'] = ['Current', 'A',['ac']]
    funcs['OHMS'] = ['Resistance', 'R',[]]
    funcs['FREQ'] = ['Frequency', 'Hz',[]]
    mults = { -3:'m', 3:'k', 0:'', 6:'M', 9:'!OR'}

    @classmethod
    def find_ports(cls, baudrate: int=9600) -> list:
        """Discover ports for connected Fluke45 meters"""
        logging.debug("Looking for ports")
        ports = []
        for port in serial.tools.list_ports.comports():
            device = port.device
            logging.debug(f"Found port {device}")
            if Fluke45.try_port(device):
                logging.debug(f"Port {device} is a Fluke45")
                ports.append(device)
        return ports

    @classmethod
    def try_port(cls, dev: str, baudrate: int=9600) -> bool:
        try:
            logging.debug(f"Testing port {dev}")
            tty = serial.Serial(port=dev, baudrate=baudrate, timeout=2)
            tty.reset_input_buffer()
            tty.gotprompt = False
            tty.gotprompt = Fluke45._getprompt(tty)
            return tty.gotprompt
        except serial.SerialException as Error:
            logging.error(f"An error ocurred whilst testing port {dev}: {Error}")
            return False


    @classmethod
    def _getprompt(cls, tty):
        if tty.gotprompt:
            return True
        got = False
        tries = 2
        while (not got) and (tries>0):
            ok, l = Fluke45._getln(tty)
            if ok:
                if l[:2] == b'=>':
                    got = True
            else:
                if tty.in_waiting == 0:
                    tty.write(chr(3).encode())
                tries -= 1
        tty.gotprompt = got
        return got


    @classmethod
    def _getln(cls, tty):
        wait = 2
        tmout = time.time() + wait
        while tmout > time.time():
            if tty.in_waiting > 0:
                l = tty.readline()
                # logging.debug(f'Read: "{l}"')
                return True, l[:-2]
        return False, ''


    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = 2
        self.open()
        self.meterstate = {}
        self._query('*RST; RATE F; FORMAT 1; AUTO')


    def _query(self, query: str) -> str:
        packet = bytes(f'{query}\r\n'.encode())
        self.write(packet)
        ok, reply = Fluke45._getln(self)
        pok, prompt = Fluke45._getln(self)
        if len(prompt) > 0:
            self.gotprompt = prompt == b'=>'
        if query.upper() != 'MEAS1?':
            self.meterstate = {}
        return reply.decode()


    def refresh_state(self):
        """Refreshes the meter's state disctionary"""
        query = '*IDN?; FUNC1?; AUTO?; MOD?; VAL1?; RANGE1?'
        replies = self._query(query).split(';')

        idport = self.port.split('/dev/')[1] if sys.platform == 'linux' else self.port
        self.id = f'fluke45-{idport}'
        self.meterstate = { 'id':self.id, 'info':replies.pop(0)}

        func = replies.pop(0)
        if func not in Fluke45.funcs.keys():
            logging.error(f'Unrecognized function {func}')
            return

        self.meterstate['function'] = Fluke45.funcs[func][0]
        self.meterstate['units'] = Fluke45.funcs[func][1]
        modes = list(Fluke45.funcs[func][2])

        if int(replies.pop(0)):
            modes.append('auto')

        modifiers = int(replies.pop(0))
        for modbit in Fluke45.modbits:
            if modifiers & modbit == modbit:
                modes.append(Fluke45.modbits[modbit])

        valstr = replies.pop(0)
        self.meterstate['value'] = float(valstr)
        # if 'E' in valstr:
        #     num, pwr = valstr.split('E')
        #     self.meterstate['mult'] = Fluke45.mults[int(pwr)]
        # else:
        #     self.meterstate['mult'] = ''
        num, pwr = valstr.split('E')
        self.meterstate['mult'] = Fluke45.mults[int(pwr)]

        self.meterstate['display'] = f'{num} {self.meterstate["mult"]}{self.meterstate["units"]} {modes}'

        self.meterstate['range'] = int(replies.pop(0))
        self.meterstate['modes'] = modes


    def get_reading(self):
        if not self.meterstate:
            self.refresh_state()
        valstr = (self._query('MEAS1?'))
        self.meterstate['value'] = float(valstr)
        if 'E' in valstr:
            num, pwr = valstr.split('E')
            self.meterstate['mult'] = Fluke45.mults[int(pwr)]
        self.meterstate['display'] = f'{num} {self.meterstate["mult"]}{self.meterstate["units"]}'

        for mode in self.meterstate['modes']:
            self.meterstate['display'] += f' {mode}'
        return self.meterstate['display']


    def get_state(self):
        """Returns the state dictionary since last reading, or refreshing if empty"""
        if not self.meterstate:
            self.refresh_state()
        return self.meterstate


    def is_set(self, function: str, modes: list, flush: bool =True) -> bool:
        """Confirms or denies a setting of function with modes"""
        lc_modes = [ mode.lower() for mode in modes]
        state = self.get_state()
        if state['function'].lower() != function.lower():
            return False
        for mode in lc_modes:
            if mode not in state['modes']:
                return False
        for mode in state['modes']:
            if mode not in lc_modes:
                return False
        return True



# End of Fluke45 class


def _connect(port=''):
    if port == '':
        print('Scanning ports... ', end='')
        ports = Fluke45.find_ports()
        if ports:
            port = ports[0]
            print(f'Fluke 45 found on {port}')
        else:
            print('Fluke 45 not found')
    return Fluke45(port)


def _demo(port=''):
    print(f'\n  Module: fluke45 v{__version__}, {__date__}  ~ Brian Swatton\n')
    print('  For reading the Fluke 45 bench multimeter.')
    print('  Intended for import.\n')

    meter = _connect(port)
    if meter is None:
        return

    while True:
        print(f'  {meter.get_reading()}\r', end='')
        time.sleep(0.2)


##################################################################
# Main program

# logging.basicConfig(filename='debug.log', level=logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    _demo()

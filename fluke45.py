#!/usr/bin/python3

#   fluke45.py

#   Module for getting data from the Fluke 45 bench multimeter.
#   Use or modify freely.

#   Brian Swatton, June 2024

__version__ = '1.0 a6'
__date__ = '9th June 2024, 00:15'

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
        self.mstate = {}
        self._query('RATE F; FORMAT 1; AUTO')


    def _query(self, query: str) -> str:
        packet = bytes(f'{query}\r\n'.encode())
        self.write(packet)
        ok, reply = Fluke45._getln(self)
        logging.debug(f'reply: {reply}')
        pok, prompt = Fluke45._getln(self)
        logging.debug(f'prompt: {prompt}')
        if len(prompt) > 0:
            self.gotprompt = prompt == b'=>'
            logging.debug(f'self.gotprompt: {self.gotprompt}, {prompt}')
        return reply.decode()


    def get_reading(self):
        return float(self._query('MEAS1?'))


    def get_state(self):
        modbits = {64:'comp', 32:'rel', 16:'dbw', 8:'db', 4:'hold', 2:'max', 1:'min' }
        funcs = {'VDC':['Voltage', 'V',['dc']]}
        funcs['VAC'] = ['Voltage', 'V',['ac']]
        state = {'modes':[]}

        function = self._query('FUNC1?')
        state['function'] = funcs[function][0]
        state['units'] = funcs[function][1]
        state['modes'] = funcs[function][2]

        modifiers = int(self._query('MOD?'))
        for modbit in modbits:
            if modifiers & modbit == modbit:
                state['modes'].append(modbits[modbit])
        return state


# End of Fluke45 class

def _connect(port='/dev/ttyS0'):
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
    # logging.basicConfig(filename='debug.log', level=logging.DEBUG)
    # logging.basicConfig(level=logging.DEBUG)

    print(f'\n  Module: fluke45 v{__version__}, {__date__}  ~ Brian Swatton\n')
    print('  For reading the Fluke 45 bench multimeter.')
    print('  Intended for import.\n')

    meter = _connect(port)
    if meter is None:
        return

    while True:
        print(meter.get_reading())
        time.sleep(1)




##################################################################
# Main program

if __name__ == '__main__':
    _demo()


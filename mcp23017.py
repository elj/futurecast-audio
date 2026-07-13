"""
Minimal MCP23017 driver (I2C via smbus2) — just what the button board needs.

Pin numbering follows the Adafruit convention used in the Arduino test sketch
(Channel_board_demo.ino): 0-7 = port A (GPA0-GPA7), 8-15 = port B (GPB0-GPB7).
"""

from smbus2 import SMBus

# Register addresses with IOCON.BANK = 0 (the power-on default).
# Each register is paired: port A at the address below, port B at address + 1.
_IODIR = 0x00  # direction: 1 = input, 0 = output
_GPPU = 0x0C   # 1 = internal 100k pull-up enabled (inputs only)
_GPIO = 0x12   # read = current pin levels
_OLAT = 0x14   # output latch


class MCP23017:
    def __init__(self, bus=1, address=0x21):
        self._bus = SMBus(bus)
        self._addr = address
        # Cached register images, indexed [port A, port B], so pin changes
        # are single read-free register writes.
        self._iodir = [0xFF, 0xFF]  # power-on default: all inputs
        self._gppu = [0x00, 0x00]
        self._olat = [0x00, 0x00]
        for port in (0, 1):
            self._write(_IODIR, port, self._iodir[port])
            self._write(_GPPU, port, self._gppu[port])
            self._write(_OLAT, port, self._olat[port])

    def input_pullup(self, pin):
        """Make `pin` an input with the internal pull-up (idle button state)."""
        port, bit = divmod(pin, 8)
        self._gppu[port] |= 1 << bit
        self._write(_GPPU, port, self._gppu[port])
        self._iodir[port] |= 1 << bit
        self._write(_IODIR, port, self._iodir[port])

    def output_low(self, pin):
        """Drive `pin` low — sinks current, lighting the channel LED."""
        port, bit = divmod(pin, 8)
        # Latch the low level before switching direction so the pin never
        # drives high, even for an instant.
        self._olat[port] &= ~(1 << bit)
        self._write(_OLAT, port, self._olat[port])
        self._iodir[port] &= ~(1 << bit)
        self._write(_IODIR, port, self._iodir[port])

    def read_all(self):
        """All 16 pin levels as one int; bit N = pin N, 1 = high (released)."""
        a, b = self._bus.read_i2c_block_data(self._addr, _GPIO, 2)
        return a | (b << 8)

    def close(self):
        self._bus.close()

    def _write(self, reg, port, value):
        self._bus.write_byte_data(self._addr, reg + port, value)

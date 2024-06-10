# Fluke45

11th June 2024

Python module for reading the Fluke 45 multimeter

    fluke45   v1.0 a8 (alpha), 9th June 2024

    Python module for reading data from the
    Fluke 45 bench mulitmeter.

    Linux and Windows (hopefully but not yet tested)

    By Brian Swatton


I consider the module still as in alpha, because a method for
changing settings is still to come. Apart from that, it would be beta,
as it operates largely the same as my module for the N56FU meter.

It's been designed so that applications can use either.  I already have
a fair few python programs that use the Fluke 45s, but not in such a
modular way.

It doesn't utilize every feature of the Fluke 45, but should be useful
for most computer driven metering tasks.


### Module Usage

If you run the file as a main program, it will just spit out
readings if/when it can. Not really the intended use, but handy
for checking setups.

I would import with the line:

    from fluke45 import Fluke45

It contains just one class, 'Fluke45', which inherits from
pyserial's serial.Serial() class. It has four methods for the
module user:

	find_ports()
	get_reading()
	get_state()
    is_set(function, modes)


Pass Fluke45 the port name, perhaps 'ttyS0', and it will return an
open a connection to it if it can.

You can get a list of ports with a running Fluke 45 meter attached with:

	ports = Fluke45.find_ports()

You can then:

    meter = Fluke45(ports[0])

    reading = meter.get_reading()

to have a human readable string returned, or

    meterstate = meter.get_state()

will give a dictionary back with all the information in a more
programmer friendly form:

    id          string identifying meter type and port
    info        string giving brand, type, s/n & diplay version
    display     string reflecting the main digital display
    function    string, 'Voltage', 'Current' etc.
    modes       list of strings of modes, ie 'ac' 'hold' etc.
    mult        string of reading mulitplier, ie 'm', 'k' etc.
    value       float of the value without mulitplier, in units
    units       string, 'V', 'A', 'Hz' etc
    range       integer, range number
    bargraph    int for bargraph (oops, still to come!)

"id" is also available as an instance variable, ie, meter.id

The is_set() method can be used to confirm or deny a desired set up,
ie:
    meter.is_set('Voltage', ['auto','ac'])

will return True if set so.


#### flush=True?

Flushing of the input buffer is not reuired with this unit, as measurements
are sent at the application's request.


#### Multiple Meters

It should be possible to open multiple connections to meters
on different ports, but this as yet untested.  ie

    m1 = Fluke45('ttyS0')
    m2 = Fluke45('ttyS1')


#### Collaboration

If you have something you'd like to contribute to the project, I
am open to suggestion for improvement. I am a bit of a noob with
github software collaboration.


#!/usr/bin/env python

# (C) 2002-2009 Chris Liechti <cliechti@gmx.net>
# redirect data from a TCP/IP connection to a serial port and vice versa
# requires Python 2.2 'cause socket.sendall is used


import sys
import os
import time
import signal
import threading
import socket
import codecs
import serial
import re
from Queue import Queue
from os import system

ser = None

def catch_SIGHUP(*args):
    global ser
    if ser == None:
        print "reestablishing connection!"
        ser = connect_to_serial()
    if ser != None:
	print "gracefully shutting down"
	ser.write('\r\n')
	ser.write('testmode off\r\n')
	print "got the signal!"	

try:
    True
except NameError:
    True = 1
    False = 0

def connect_to_serial():
    global ser
    # connect to serial port
    possible_ports = ['/dev/ttyUSB0','/dev/ttyUSB1']
    ser = serial.Serial()
    ser.baudrate = 115200
    ser.parity   = 'N'
    ser.rtscts   = False
    ser.xonxoff  = options.xonxoff
    ser.timeout  = 1     # required so that the reader thread can exit

    while True:
	for p in possible_ports:
	    ser.port = p
	    try:
		ser.open()
		print "Connected on port: " + p
		return ser
	    except:
		time.sleep(1)

class Redirector:
    def __init__(self, serial_instance, tcp_socket, client_ip, ser_newline=None, net_newline=None):
        self.serial = serial_instance
	n = self.serial.inWaiting()
	if n:
		self.serial.read(n)
		print "flushed serial port"
        self.socket = tcp_socket
        self.sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ser_newline = ser_newline
        self.net_newline = net_newline
        self._write_lock = threading.Lock()
	self.serial_command_queue = Queue()
        self.serial_read_flushed = False
        self.sensor_packet = ""
        self.client_ip = client_ip

    def shortcut(self):
        """connect the serial port to the TCP port by copying everything
           from one side to the other"""
        self.alive = True
        self.thread_read = threading.Thread(target=self.reader)
        self.thread_read.setDaemon(True)
        self.thread_read.setName('serial->socket')
        self.thread_read.start()

        self.thread_main_loop = threading.Thread(target=self.main_loop)
        self.thread_main_loop.setDaemon(True)
        self.thread_main_loop.setName('commands->serial')
        self.thread_main_loop.start()

        self.writer()

    def main_loop(self):
        while self.alive:
            while not self.client_ip:
                time.sleep(0.1)
            # reset all buffers
            #self.serial.flushInput()
            #self.serial.flushOutput()
            # enqueue all relevant commands
            loop_start = time.time()
            # reset the sensor packet since it has just been blasted over UDP
            self.sensor_packet = ""
            valid_packet = True
            last_control_z = -1
            self.serial_command_queue.put(("getldsscan\n",'.*ROTATION_SPEED,[0-9\.]+'))
            self.serial_command_queue.put(("getmotors\n", '.*SideBrush_mA,[0-9\.]+'))
            self.serial_command_queue.put(("getdigitalsensors\n", '.*RFRONTBIT,[0-9\.]+'))
            self.serial_command_queue.put(("getaccel\n", '.*SumInG, [0-9\.]+'))
	    while not self.serial_command_queue.empty():
                next_cmd, terminal_re = self.serial_command_queue.get()
                self.write_command_to_serial(next_cmd)
		# need to sleep until the serial port is empty, could use a condition... for now just spin wait
                search_count = 0
                while True:
                    t_start = time.time()
                    
                    new_last_control_z = self.sensor_packet.rfind(chr(26))
                    if new_last_control_z > last_control_z:
                        last_control_z = new_last_control_z
                        break 
                    if 'Ambiguous Cmd' in self.sensor_packet:
                        print "unexpectedly got this"
                        #print self.sensor_packet
                        valid_packet = False
                        break
                    search_count  += 1
                    if search_count > 100:
                        valid_packet = False
                        print 'Warning:', len(self.sensor_packet)
                        break
                    time.sleep(.01)
                if not valid_packet:
                    with self.serial_command_queue.mutex:
                        self.serial_command_queue.queue.clear()
                    break

            if valid_packet:
                # self.write(self.sensor_packet)
                self.sensor_socket.sendto(self.sensor_packet, (self.client_ip, 7777))
                #print "sending sensor packet", "self.client_ip", self.client_ip, "length", len(self.sensor_packet)
	    sleep_time = loop_start - time.time() + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)

    def reader(self):
        """loop forever and copy serial->socket"""
        while self.alive:
            try:
                self.serial_read_flushed = self.serial.inWaiting() == 0
                data = self.serial.read(1)              # read one, blocking
                n = self.serial.inWaiting()             # look if there is more
                if n:
		    # TODO: it would be nice to only get full lines, but I'm not sure if this is possible to do fast
                    data = data + self.serial.read(n)   # and get as much as possible
                if data:
                    if self.ser_newline and self.net_newline:
                        # do the newline conversion
                        # XXX fails for CR+LF in input when it is cut in half at the begin or end of the string
                        data = net_newline.join(data.split(ser_newline))
                    # escape outgoing data when needed (Telnet IAC (0xff) character)
		    self.sensor_packet += data
            except socket.error, msg:
                sys.stderr.write('ERROR: %s\n' % msg)
                # probably got disconnected
                break
	    except Exception as inst:
                sys.stderr.write('Non-socket error: %s\n' % str(inst))
        self.alive = False

    def write(self, data):
        """thread safe socket write with no data escaping. used to send telnet stuff"""
        self.socket.sendall(data)

    def write_command_to_serial(self, cmd):
        """ cmd is a string that should be sent to the serial port """	
        # print "writing!" + cmd
        # these commands are special
        self.serial.write(cmd)

    def writer(self):
        """loop forever and copy socket->serial"""
	remainder = ""
        while self.alive:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
		data = remainder + data
		if remainder:
		    remainder = ""

		if not(data.endswith('\n')):
		    pos = data.rfind('\n')
		    if pos != -1:
			remainder = data[pos+1:]
			data = data[0:pos+1]
		    else:
			remainder = data
			data = ""
		else:
		    remainder = ""

		if data.endswith('\n'):
                    # for control commands we always echo the command sent
                    self.serial_command_queue.put((data , data))
            except socket.error, msg:
                sys.stderr.write('ERROR: %s\n' % msg)
                # probably got disconnected
                break
        self.alive = False
        self.thread_read.join()
        self.thread_main_loop.join()

    def stop(self):
        """Stop copying"""
        if self.alive:
            self.alive = False
            self.thread_read.join()


if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(
        usage = "%prog [options] [port [baudrate]]",
        description = "Simple Serial to Network (TCP/IP) redirector.",
        epilog = """\
NOTE: no security measures are implemented. Anyone can remotely connect
to this service over the network.

Only one connection at once is supported. When the connection is terminated
it waits for the next connect.
""")

    parser.add_option("-q", "--quiet",
        dest = "quiet",
        action = "store_true",
        help = "suppress non error messages",
        default = False
    )

    group = optparse.OptionGroup(parser,
        "Serial Port",
        "Serial port settings"
    )
    parser.add_option_group(group)

    group.add_option("-p", "--port",
        dest = "port",
        help = "port, a number (default 0) or a device name",
        default = None
    )

    group.add_option("-b", "--baud",
        dest = "baudrate",
        action = "store",
        type = 'int',
        help = "set baud rate, default: %default",
        default = 9600
    )

    group.add_option("", "--parity",
        dest = "parity",
        action = "store",
        help = "set parity, one of [N, E, O], default=%default",
        default = 'N'
    )

    group.add_option("--rtscts",
        dest = "rtscts",
        action = "store_true",
        help = "enable RTS/CTS flow control (default off)",
        default = False
    )

    group.add_option("--xonxoff",
        dest = "xonxoff",
        action = "store_true",
        help = "enable software flow control (default off)",
        default = False
    )

    group.add_option("--rts",
        dest = "rts_state",
        action = "store",
        type = 'int',
        help = "set initial RTS line state (possible values: 0, 1)",
        default = None
    )

    group.add_option("--dtr",
        dest = "dtr_state",
        action = "store",
        type = 'int',
        help = "set initial DTR line state (possible values: 0, 1)",
        default = None
    )

    group = optparse.OptionGroup(parser,
        "Network settings",
        "Network configuration."
    )
    parser.add_option_group(group)

    group.add_option("-P", "--localport",
        dest = "local_port",
        action = "store",
        type = 'int',
        help = "local TCP port",
        default = 7777
    )

    group = optparse.OptionGroup(parser,
        "Newline Settings",
        "Convert newlines between network and serial port. Conversion is normally disabled and can be enabled by --convert."
    )
    parser.add_option_group(group)

    group.add_option("-c", "--convert",
        dest = "convert",
        action = "store_true",
        help = "enable newline conversion (default off)",
        default = False
    )

    group.add_option("--net-nl",
        dest = "net_newline",
        action = "store",
        help = "type of newlines that are expected on the network (default: %default)",
        default = "LF"
    )

    group.add_option("--ser-nl",
        dest = "ser_newline",
        action = "store",
        help = "type of newlines that are expected on the serial port (default: %default)",
        default = "CR+LF"
    )

    (options, args) = parser.parse_args()

    # get port and baud rate from command line arguments or the option switches
    port = options.port
    baudrate = options.baudrate
    if args:
        if options.port is not None:
            parser.error("no arguments are allowed, options only when --port is given")
        port = args.pop(0)
        if args:
            try:
                baudrate = int(args[0])
            except ValueError:
                parser.error("baud rate must be a number, not %r" % args[0])
            args.pop(0)
        if args:
            parser.error("too many arguments")
    else:
        if port is None: port = 0

    # check newline modes for network connection
    mode = options.net_newline.upper()
    if mode == 'CR':
        net_newline = '\r'
    elif mode == 'LF':
        net_newline = '\n'
    elif mode == 'CR+LF' or mode == 'CRLF':
        net_newline = '\r\n'
    else:
        parser.error("Invalid value for --net-nl. Valid are 'CR', 'LF' and 'CR+LF'/'CRLF'.")

    # check newline modes for serial connection
    mode = options.ser_newline.upper()
    if mode == 'CR':
        ser_newline = '\r'
    elif mode == 'LF':
        ser_newline = '\n'
    elif mode == 'CR+LF' or mode == 'CRLF':
        ser_newline = '\r\n'
    else:
        parser.error("Invalid value for --ser-nl. Valid are 'CR', 'LF' and 'CR+LF'/'CRLF'.")

    ser = None

    signal.signal(signal.SIGHUP, catch_SIGHUP)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind( ('', options.local_port) )
    srv.listen(1)
    while True:
        try:
            sys.stderr.write("Waiting for connection on %s...\n" % options.local_port)
            connection, addr = srv.accept()
            client_ip = addr[0]

            connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
	    connection.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 30)
	    connection.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 15)
	    #connection.settimeout(60)
            sys.stderr.write('Connected by %s\n' % (addr,))
            if ser != None:
                try:
                    ser.close()
                except Exception as inst:
                    sys.stderr.write('ERROR: %s\n', str(inst))
            # connect to serial port
            ser = connect_to_serial()
            if not options.quiet:
                sys.stderr.write("--- TCP/IP to Serial redirector --- type Ctrl-C / BREAK to quit\n")

            if options.rts_state is not None:
                ser.setRTS(options.rts_state)

            if options.dtr_state is not None:
                ser.setDTR(options.dtr_state)

            # enter network <-> serial loop
            r = Redirector(
                ser,
                connection,
                client_ip,
                options.convert and ser_newline or None,
                options.convert and net_newline or None,
            )
            r.shortcut()
            sys.stderr.write('Disconnected\n')
            connection.close()
	    ser.write('\r\n')
	    ser.write('testmode off\r\n')
	    system("sudo killall raspivid")
	    system("sudo killall gst-launch-1.0")
	except Exception as inst:
            sys.stderr.write('ERROR: %s\n' % str(inst))
	    break
    sys.stderr.write('\n--- exit ---\n')


#!/usr/bin/perl

# shutdown wireless monitoring
system("ps axww | grep monitor_wireless | awk \'{ print \$1 }\' | xargs kill");

my $mac_address = "";
my $foundNetwork = 0;
while (!$foundNetwork) {
	$scan_output = `iwlist scan`;
	print $scan_output
	@lines = split("\n",$scan_output);
	foreach my $line (@lines) {
		if ($foundNetwork == 0 && $line =~ /Cell.*Address: (.*)$/) {
			$mac_address = $1;
		}
		if ($line =~ /ESSID.*RPi209/) {
			print $mac_address;
			$foundNetwork = 1;
		}
	}
}
# override
system('service ifplugd stop');
system('ifdown wlan0');


system("iwconfig wlan0 mode ad-hoc essid RPi209 key aaaaa11111 ap $mac_address");
system("ifup -i /etc/network/interfaces_adhoc wlan0");
system("killall raspivid");
system('service ifplugd start');

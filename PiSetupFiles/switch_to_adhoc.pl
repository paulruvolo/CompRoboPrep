#!/usr/bin/perl

# shutdown wireless monitoring
system("ps axww | grep monitor_wireless | awk \'{ print \$1 }\' | xargs kill");

# override
system('ifdown wlan0');

my $mac_address = "";
my $foundNetwork = 0;
while (!$foundNetwork) {
	$scan_output = `iwlist scan`;
	@lines = split("\n",$scan_output);
	foreach my $line (@lines) {
		if ($foundNetwork == 0 && $line =~ /Cell.*Address: (.*)$/) {
			$mac_address = $1;
		}
		if ($line =~ /ESSID.*RPi204/) {
			print $mac_address;
			$foundNetwork = 1;
		}
	}
}

system("iwconfig wlan0 mode ad-hoc essid RPi204 key aaaaa11111 ap $mac_address");
system("ifup -i /etc/network/interfaces_adhoc wlan0");
system("killall raspivid");

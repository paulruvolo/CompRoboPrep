#!/usr/bin/perl

open(IN, "./repo_list") || die;

chdir('..');

if (!-e 'student_code') {
	system('mkdir student_code');
}
chdir('student_code');

while (my $line = <IN>) {
	print $line;
	chomp($line);
	my $repo = "https://github.com/" . $line . "/comprobo2014.git";
	if (!-e "./$line") {
		system("mkdir $line");
	}
	chdir("./$line");
	if (!-e "./comprobo2014") {
		if ($line eq 'kmcconnaughay') {
			system('git clone https://github.com/kmcconnaughay/CompRobo.git comprobo2014');
		} else {
			system("git clone " . $repo);
		}
	} else {
		chdir('./comprobo2014');
		system('git pull');
		chdir('..');
	}
	chdir('..');
}

chdir('..');

close(IN);

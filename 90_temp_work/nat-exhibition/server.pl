#!/usr/bin/perl
use strict;
use warnings;
use IO::Socket::INET;

my $port = $ARGV[0] || 10080;
my $root = $ARGV[1] || '/root/nat-exhibition';

my $server = IO::Socket::INET->new(
  LocalAddr => '0.0.0.0',
  LocalPort => $port,
  Proto     => 'tcp',
  Listen    => 32,
  Reuse     => 1,
) or die "cannot listen on port $port: $!\n";

$SIG{CHLD} = 'IGNORE';

sub content_type {
  my ($path) = @_;
  return 'text/html; charset=utf-8' if $path =~ /\.html?$/i;
  return 'text/css; charset=utf-8' if $path =~ /\.css$/i;
  return 'application/javascript; charset=utf-8' if $path =~ /\.js$/i;
  return 'image/svg+xml' if $path =~ /\.svg$/i;
  return 'text/plain; charset=utf-8';
}

sub reply {
  my ($client, $status, $type, $body, $head_only) = @_;
  print $client "HTTP/1.1 $status\r\n";
  print $client "Content-Type: $type\r\n";
  print $client "Content-Length: " . length($body) . "\r\n";
  print $client "Cache-Control: no-store\r\n";
  print $client "Connection: close\r\n\r\n";
  print $client $body unless $head_only;
}

while (my $client = $server->accept()) {
  next unless <$client> =~ /^(GET|HEAD)\s+(\S+)/;
  my ($method, $path) = ($1, $2);
  while (<$client>) { last if /^\r?\n$/; }
  my $head_only = $method eq 'HEAD';
  $path =~ s/\?.*//;
  $path = '/index.html' if $path eq '/';
  $path =~ s/\.\.//g;
  my $file = "$root$path";

  if (-f $file) {
    open my $fh, '<', $file or do { reply($client, '500 Internal Server Error', 'text/plain', 'read failed\n', $head_only); close $client; next; };
    binmode $fh;
    local $/;
    my $body = <$fh>;
    close $fh;
    reply($client, '200 OK', content_type($file), $body, $head_only);
  } else {
    reply($client, '404 Not Found', 'text/plain; charset=utf-8', "not found\n", $head_only);
  }
  close $client;
}

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > dynapath=$TESTDIR/dynapath.py
  > fixsocket=$TESTDIR/mocksocket.py
  > [dynapath]
  > cph.ipprefix=192.168.1.1/32
  > cph.pathprefix=https://publicdns/
  > cph.pathsubst=http://cphdns239847239847928347:14144/
  > arn.ipprefix=10.10.1.1/25 10.10.4.4/30
  > arn.pathprefix=https://publicdns/
  > arn.pathsubst=http://arndns09380498234:14144/
  > sin.ipprefix=2.4.3.4
  > sin.pathprefix=https://user@publicdns/foo
  > sin.pathsubst=http://sindns92834792374:14144/baaar
  > ipprefix=192.168
  > pathprefix=https://publicdns/
  > pathsubst=http://olddns239879238479247:14144/
  > [socketfix]
  > * = 192.168.1.1
  > publicdns = 127.0.0.8
  > otherdns = 127.0.0.9
  > privatedns982379487239847293847234 = 127.0.0.14
  > cphdns239847239847928347 = 127.0.0.15
  > arndns09380498234 = 127.0.0.16
  > olddns239879238479247 = 127.0.0.17
  > sindns92834792374 = 127.0.0.18
  > EOF

  $ hg -y clone https://publicdns/foo foo --debug
  finding addresses for * (glob)
  ip 192.168.1.1 does not match any of the ip prefixes 10.10.1.1/25, 10.10.4.4/30
  finding outgoing address to arndns09380498234
  error connecting to arndns09380498234* (glob)
  finding addresses for * (glob)
  ip 192.168.1.1 matched, path changed from https://publicdns/foo to http://cphdns239847239847928347:14144/foo
  using http://cphdns239847239847928347:14144/foo
  sending capabilities command
  abort: error: Connection refused
  [255]

  $ hg -y clone https://otherdns/foo foo --debug
  path https://otherdns/foo didn't match prefix https://publicdns/
  path https://otherdns/foo didn't match prefix https://publicdns/
  path https://otherdns/foo didn't match prefix https://user@publicdns/foo
  path https://otherdns/foo didn't match prefix https://publicdns/
  path https://otherdns/foo was not matched by any prefix
  using https://otherdns/foo
  sending capabilities command
  abort: error: Connection refused
  [255]

  $ hg -y --config socketfix.*=10.10.8.8 clone https://publicdns/foo foo --debug
  finding addresses for * (glob)
  ip 10.10.8.8 does not match any of the ip prefixes 10.10.1.1/25, 10.10.4.4/30
  finding outgoing address to arndns09380498234
  error connecting to arndns09380498234* (glob)
  finding addresses for * (glob)
  ip 10.10.8.8 does not match any of the ip prefixes 192.168.1.1/32
  finding outgoing address to cphdns239847239847928347
  error connecting to cphdns239847239847928347* (glob)
  finding addresses for * (glob)
  ip 10.10.8.8 does not match any of the ip prefixes 2.4.3.4
  finding outgoing address to sindns92834792374
  error connecting to sindns92834792374* (glob)
  finding addresses for * (glob)
  ip 10.10.8.8 does not match any of the ip prefixes 192.168.0.0/255.255.0.0
  finding outgoing address to olddns239879238479247
  error connecting to olddns239879238479247* (glob)
  path https://publicdns/foo was not matched by any prefix
  using https://publicdns/foo
  sending capabilities command
  abort: error: Connection refused
  [255]

  $ hg -y --config socketfix.*=8.8.8.8 clone https://otherdns/foo foo --debug
  path https://otherdns/foo didn't match prefix https://publicdns/
  path https://otherdns/foo didn't match prefix https://publicdns/
  path https://otherdns/foo didn't match prefix https://user@publicdns/foo
  path https://otherdns/foo didn't match prefix https://publicdns/
  path https://otherdns/foo was not matched by any prefix
  using https://otherdns/foo
  sending capabilities command
  abort: error: Connection refused
  [255]

  $ hg -y --config socketfix.*=10.10.4.6 clone https://publicdns/foo foo --debug
  finding addresses for * (glob)
  ip 10.10.4.6 matched, path changed from https://publicdns/foo to http://arndns09380498234:14144/foo
  using http://arndns09380498234:14144/foo
  sending capabilities command
  abort: error: Connection refused
  [255]

  $ hg -y --config socketfix.*=10.10.4.6 clone https://user@publicdns/foo foo --debug
  finding addresses for * (glob)
  ip 10.10.4.6 matched, path changed from https://user@publicdns/foo to http://user@arndns09380498234:14144/foo
  using http://arndns09380498234:14144/foo
  http auth: user user, password not set
  sending capabilities command
  abort: error: Connection refused
  [255]

  $ hg -y --config socketfix.*=2.4.3.4 clone https://user@publicdns/foo foo --debug
  finding addresses for * (glob)
  ip 2.4.3.4 does not match any of the ip prefixes 10.10.1.1/25, 10.10.4.4/30
  finding outgoing address to arndns09380498234
  error connecting to arndns09380498234* (glob)
  finding addresses for * (glob)
  ip 2.4.3.4 does not match any of the ip prefixes 192.168.1.1/32
  finding outgoing address to cphdns239847239847928347
  error connecting to cphdns239847239847928347* (glob)
  finding addresses for * (glob)
  ip 2.4.3.4 matched, path changed from https://user@publicdns/foo to http://user@sindns92834792374:14144/baaar
  using http://sindns92834792374:14144/baaar
  http auth: user user, password not set
  sending capabilities command
  abort: error: Connection refused
  [255]

  $ hg init x
  $ cat >> x/.hg/hgrc <<EOF
  > [paths]
  > default = https://publicdns/foo/baz
  > EOF
  $ hg -y --config socketfix.*=2.4.3.4 -R x pull --debug
  pulling from https://publicdns/foo/baz
  finding addresses for * (glob)
  ip 2.4.3.4 does not match any of the ip prefixes 10.10.1.1/25, 10.10.4.4/30
  finding outgoing address to arndns09380498234
  error connecting to arndns09380498234* (glob)
  finding addresses for * (glob)
  ip 2.4.3.4 does not match any of the ip prefixes 192.168.1.1/32
  finding outgoing address to cphdns239847239847928347
  error connecting to cphdns239847239847928347* (glob)
  finding addresses for * (glob)
  ip 2.4.3.4 matched, path changed from https://publicdns/foo/baz to http://user@sindns92834792374:14144/baaar/baz
  using http://sindns92834792374:14144/baaar/baz
  http auth: user user, password not set
  sending capabilities command
  abort: error: Connection refused
  [255]

# dynapath.py - change default path depending on local network
#
# Copyright Unity Technologies, Mads Kiilerich <madski@unity3d.com>
# Copyright Matt Mackall <mpm@selenic.com> and others
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

'''dynamically change the default path, depending on local IP address

Use local or global configuration like::

  [extensions]
  dynapath = /path/to/dynapath.py
  [dynapath]
  ipprefix = 192.168
  pathprefix = https://public/
  pathsubst = http://private/

If one of the local IPv4 addresses matches ipprefix then ``[paths] default``
will have pathprefix replaced with pathsubst. An empty pathprefix matches
everything.

In the example above, when the local IP address is ``192.168.1.42`` and the
default path is ``https://public/repo``, it will use ``http://private/repo``
instead.

The local IP addresses are determined from different sources. The IP addresses
of the hostname are looked up (quick, but also error prone - especially if the
hostname resolves to ``127.0.0.1``). If that doesn't give a matching result, it
will pretend to connect to the host in pathsubst and look at the IP of the
outgoing interface.

Note: It is also possible to specify a full IP address as ipprefix. That can be
convenient if the same IP network is used in different locations but it is
possible to assign the IP address statically.
'''

import socket

from mercurial.i18n import _
from mercurial import httppeer
from mercurial import extensions, util

testedwith = '2.7'

def localips(ui, probeip):
    ui.debug("finding addresses for %s\n" % socket.gethostname())
    for _af, _socktype, _proto, _canonname, sa in socket.getaddrinfo(
            socket.gethostname(), 0, socket.AF_INET, socket.SOCK_STREAM):
        yield sa[0]
    try:
        ui.debug("finding outgoing address to %s\n" % probeip)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((probeip, 1))
        yield s.getsockname()[0]
    except socket.error, e:
        ui.debug("error connecting to %s: %s\n" % (probeip, e))

def fixuppath(ui, path, ipprefix, pathprefix, pathsubst):
    if not path.startswith(pathprefix):
        ui.debug(_("path %s didn't match prefix %s\n")
                 % (util.hidepassword(path), util.hidepassword(pathprefix)))
        return path
    try:
        u = util.url(pathsubst)
        probehost = u.host or '1.0.0.1'
    except Exception:
        probehost = '1.0.0.1'
    for ip in localips(ui, probehost):
        if (ip + '.').startswith(ipprefix + '.'):
            new = pathsubst + path[len(pathprefix):]
            ui.write(_("ip %s matched, path changed from %s to %s\n") %
                       (ip, util.hidepassword(path), util.hidepassword(new)))
            return new
        ui.debug("ip %s do not match ip prefix '%s'\n"
                 % (ip, ipprefix))
    return path

def httppeer__init__(orig, self, ui, path):
    ipprefix = ui.config('dynapath', 'ipprefix', '0.0.0.0').rstrip('.')
    pathprefix = ui.config('dynapath', 'pathprefix', path)
    pathsubst = ui.config('dynapath', 'pathsubst', '')
    return orig(self, ui, fixuppath(ui, path, ipprefix, pathprefix, pathsubst))

extensions.wrapfunction(httppeer.httppeer, '__init__', httppeer__init__)

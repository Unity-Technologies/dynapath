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
'''

import socket

from mercurial.i18n import _
from mercurial import ui as uimod
from mercurial import extensions, util

testedwith = '2.7'

def ips(ui, probeip):
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

def config(orig, self, section, key, default=None, untrusted=False):
    if section == "paths" and key == "default":
        path = orig(self, 'paths', 'default', '')
        ipprefix = orig(self, 'dynapath', 'ipprefix', '0.0.0.0')
        if ipprefix.count('.') < 3 and not ipprefix.endswith('.'):
            ipprefix += '.'
        pathprefix = orig(self, 'dynapath', 'pathprefix', path)
        pathsubst = orig(self, 'dynapath', 'pathsubst', '')
        try:
            u = util.url(pathsubst)
            probehost = u.host or '1.0.0.1'
        except Exception:
            probehost = '1.0.0.1'
        for ip in ips(self, probehost):
            if not ip.startswith(ipprefix):
                self.debug("address %s do not match ip prefix '%s'\n" %
                           (ip, ipprefix))
                continue
            if path.startswith(pathprefix):
                path = pathsubst + path[len(pathprefix):]
                self.write(_("ip %s dynamically changed path to %s\n") %
                           (ip, util.hidepassword(path)))
            else:
                self.debug(_("ip %s matched but path didn't match\n") % ip)
            return path
    return orig(self, section, key, default, untrusted)

extensions.wrapfunction(uimod.ui, 'config', config)

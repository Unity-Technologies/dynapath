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
  dynapath = /path/to/dynapath/
  [dynapath]
  prefix1.ipprefix = 192.168.0.0/16
  prefix1.pathprefix = https://public/
  prefix1.pathsubst = http://private-prefix1/
  prefix2.ipprefix = 10.10.4.0/24 10.10.5.8
  prefix2.pathprefix = https://public/
  prefix2.pathsubst = http://private-prefix2/

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

from mercurial import util, demandimport

try:
    demandimport.disable()
    import ipaddress
except ImportError:
    # for backwards compatibility for people referencing dynapath.py
    # directly rather than as a module such that we can still find
    # and import ipaddress relative to dynapath.py
    import os.path
    import imp
    ipaddressfile = util.localpath(os.path.join(os.path.dirname(__file__),
        'ipaddress.py'))
    ipaddress = imp.load_source('ipaddress', ipaddressfile)
finally:
    demandimport.enable()

from mercurial.i18n import _
from mercurial import httppeer
from mercurial import extensions, util

testedwith = '3.8'

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

def _url_without_authentication(url):
    """return an url instance without user or password entries"""
    u = util.url(url)
    u.user = None
    u.passwd = None
    return u

def _is_match_path(path, pathprefix):
    """returns whether path starts with pathprefix

    When computing whether path starts with pathprefix, authentication
    information is removed from both URLs.
    """
    pathurl = _url_without_authentication(path)
    prefixurl = _url_without_authentication(pathprefix)

    return str(pathurl).startswith(str(prefixurl))

def _rewrite_path(path, pathsubst, pathprefix):
    """Change path into the substituted path up to the path prefix match

    If the substitution does not specify authentication information and either
    the path or the prefix does, then that authentication is copied to the
    substituted path.
    """
    pathurl = util.url(path)
    substurl = util.url(pathsubst)
    prefixurl = util.url(pathprefix)

    if not substurl.user:
        if pathurl.user:
            substurl.user = pathurl.user
        else:
            substurl.user = prefixurl.user
    if not substurl.passwd:
        if pathurl.passwd:
            substurl.passwd = pathurl.passwd
        else:
            substurl.passwd = prefixurl.passwd

    substurl.path += pathurl.path[len(prefixurl.path):]
    return str(substurl)

def fixuppath(ui, path, substitutions):
    for ipprefixes, pathprefix, pathsubst in substitutions:
        if not _is_match_path(path, pathprefix):
            ui.debug(_("path %s didn't match prefix %s\n")
                     % (util.hidepassword(path), util.hidepassword(pathprefix)))
            continue
        try:
            u = util.url(pathsubst)
            probehost = u.host or '1.0.0.1'
        except Exception:
            probehost = '1.0.0.1'
        for ip in localips(ui, probehost):
            if any(ipaddress.ip_address(unicode(ip))
                   in ipaddress.ip_network(unicode(ipprefix), False)
                   for ipprefix in ipprefixes):
                new = _rewrite_path(path, pathsubst, pathprefix)
                ui.write(_("ip %s matched, path changed from %s to %s\n") %
                           (ip, util.hidepassword(path),
                            util.hidepassword(new)))
                return new
            ui.debug("ip %s does not match any of the ip prefixes %s\n"
                     % (ip, ', '.join(ipprefixes)))

    ui.debug(_("path %s was not matched by any prefix\n"
        % util.hidepassword(path)))
    return path

def _rewrite_old_prefix(ipprefix):
    """Change old prefix to new prefix

    Prefixes could previously be written just as 192.168, but with the
    introduction of ipaddress, it must now be on the form
    192.168.0.0/255.255.0.0 instead.
    """
    count = ipprefix.count('.')

    if count != 3:
        ipprefix = ipprefix + '.0' * (3 - count)
        ipprefix = ipprefix + '/' + ('.255' * (count + 1)).lstrip('.')
        ipprefix = ipprefix + '.0' * (3 - count)

    return ipprefix

def load_substitutions(ui, path):
    items = ui.configitems('dynapath')
    prefixes = set(key.split('.')[0] for key, value in items if '.' in key)
    for prefix in sorted(prefixes):
        ipprefixes = ui.configlist('dynapath', prefix + '.ipprefix', [])
        ipprefixes = [ipprefix.rstrip('.') for ipprefix in ipprefixes]
        pathprefix = ui.config('dynapath', prefix + '.pathprefix', path)
        pathsubst = ui.config('dynapath', prefix + '.pathsubst', '')
        if not ipprefixes or not pathsubst:
            ui.warn(_('dynapath.%s is not configured properly, missing '
                'ipprefix/pathsubst\n' % prefix))
        yield (ipprefixes, pathprefix, pathsubst)

    # backwards compat
    ipprefix = ui.config('dynapath', 'ipprefix', '0.0.0.0').rstrip('.')
    ipprefix = _rewrite_old_prefix(ipprefix)
    pathprefix = ui.config('dynapath', 'pathprefix', path)
    pathsubst = ui.config('dynapath', 'pathsubst', '')
    if ipprefix == '0.0.0.0' and not pathsubst and pathprefix == path and prefixes:
        return  # if nothing is set and we have new config, let's ignore this
    yield ([ipprefix], pathprefix, pathsubst)


def httppeer__init__(orig, self, ui, path):
    substitutions = load_substitutions(ui, path)
    return orig(self, ui, fixuppath(ui, path, substitutions))

extensions.wrapfunction(httppeer.httppeer, '__init__', httppeer__init__)

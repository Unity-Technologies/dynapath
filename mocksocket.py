"""mock socket functionality to fix DNS lookups using getaddrinfo"""

import socket

def extsetup(ui):
    mapping = ui.configitems('socketfix')
    
    def _getaddrinfo(hostname, x, y, z):
        real = [m for m in mapping if m[0] == hostname]
        if not real:
            real = [m for m in mapping if m[0] == '*']
        if not real:
            raise Exception('missing socketfix configuration')

        return [(2, 1, 0, '', (real[0][1], 0))]

    socket.getaddrinfo = _getaddrinfo

#!/usr/bin/env python
# Copyright (C) 2012 Martin Walsh <sysadm@mwalsh.org>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from SocketServer import ForkingUDPServer, ForkingTCPServer,
        ThreadingUDPServer, ThreadingTCPServer, BaseRequestHandler
from optparse import OptionParser, OptionValueError

class RequestHandler(object): pass

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
       '-s', '--source', default='localhost', 
       help='The source host (default: localhost)'
    )
    parser.add_option(
        '-d', '--destination',
        help='The destination host'
    )
    parser.add_option(
        '--dport', '--destination-port', type='int', default=80,
        help='The destination port (default: 80)'
    )
    parser.add_option(
        '--sport', '--source-port', type='int', default=8080, 
        help='The source port (default: 8080)'
    )
    parser.add_option(
            '-p', '--protocol', dest='protocol', type='choice',
            choices=('tcp', 'udp'), default="tcp",
            help='Protocol option: TCP and UDP supported.'
    )

    opts, args = parser.parse_args()
    # helps detect -sport 8080 (first dash missing)
    if args: raise parser.error('invalid argument: %r' % args[0])






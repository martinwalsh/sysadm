# Copyright (C) 2008-2012 Martin Walsh <sysadm@mwalsh.org>
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
import sys
import time
import select
import StringIO

class StdIn(StringIO.StringIO):
    """
    An input container that doesn't block if nothing is waiting on stdin.
    It behaves more or less like a StringIO object, not surprising given
    it subclasses StringIO.StringIO.  
    
    It's hard to doctest this particular class for obvious reasons. Here is
    a contrived example, or two. 

    >>> # no pipe to stdin
    >>> from subprocess import Popen, PIPE, STDOUT
    >>> p = Popen(
    ...     ('/usr/bin/python -c '
    ...         '"import io; stdin = io.StdIn(); print stdin.getvalue(),"'), 
    ...         shell=True, stdout=PIPE, stderr=STDOUT
    ... )
    >>> p.communicate()[0]
    '\\n'
    
    >>> # pipe to stdin
    >>> p = Popen(
    ...     ('echo "This is piped to StdIn" | /usr/bin/python '
    ...         '-c "import io; stdin = io.StdIn(); print stdin.getvalue(),"'), 
    ...         shell=True, stdout=PIPE, stderr=STDOUT
    ... )
    >>> p.communicate()[0]
    'This is piped to StdIn\\n'
    
    """
    def __init__(self):
        time.sleep(0.01)
        poller = select.poll()
        poller.register(sys.stdin)
        polled = poller.poll()
        if any(mask & select.POLLIN for fd, mask in polled):
            buffer = ''.join(line for line in sys.stdin)
        else:
            buffer = ''
        StringIO.StringIO.__init__(self, buffer)

    def __repr__(self):
        return self.getvalue()


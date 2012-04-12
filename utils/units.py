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

__all__ = [
    'seconds_to_human', 'bytes_per_second', 
    'bits_per_second', 'bytes_to_human', 'bits_to_human'
]

def bits_to_human(bytes):
    """ 
    Accepts an integer or float reprsenting bits
    and returns a string in human readable form. 
    
    >>> bits_to_human(1000)
    '1Kb'
    """
    prefixes = ['', 'K', 'M', 'G', 'T']
    x = bytes
    for prefix in prefixes:
        if x < 1000:
            return '%.4g%sb' % (x, prefix)
        x /= 1000.0
    return '%.3eb' % bytes

def bytes_to_human(bytes):
    """ 
    Accepts an integer or float representing bytes
    and returns a string in human readable form. 

    >>> bytes_to_human(1024)
    '1KB'
    """
    prefixes = ['', 'K', 'M', 'G', 'T']
    x = bytes
    for prefix in prefixes:
        if x < 1024:
            return '%.4g%sB' % (x, prefix)
        x /= 1024.0
    return '%.3eB' % bytes

def seconds_to_human(s, float_secs=True):
    """
    Accepts a number representing seconds and 
    returns a string in human readable form.


    >>> seconds_to_human(31536999)
    '365 days 16 minutes 39.00 seconds'
    >>> seconds_to_human(7200)
    '2 hours'
    """
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    def pluralize(s, n):
        if n > 1: s += 's'
        return s % n
    
    out = []
    if d: out.append(pluralize('%d day', d))
    if h: out.append(pluralize('%d hour', h))
    if m: out.append(pluralize('%d minute', m))
    if float_secs:
        secondsfmt = '%0.2f second'
    else:
        secondsfmt = '%d second'
    if s: out.append(pluralize(secondsfmt, s))
    
    return ' '.join(out)

def bytes_per_second(bytes, seconds, human=True):
    """
    Accepts a number (of bytes) and seconds and
    returns bytes/seconds. 

    If human=True (the default), the result is 
    returned in human readable form. 

    >>> bytes_per_second(1024, 1)
    '1KBps'
    """
    ratio = float(bytes/seconds)
    if human:
        return '%sps' % bytes_to_human(ratio)
    else:
        return ratio

def bits_per_second(bytes, seconds, human=True):
    """
    Accepts a number (of bytes) and seconds and
    returns bits/seconds. 

    If human=True (the default), the result is 
    returned in human readbale form. 

    >>> bits_per_second(1000, 1)
    '1Kbps'
    """
    ratio = float(bytes/seconds)
    if human:
        return '%sps' % bits_to_human(ratio)
    else:
        return ratio


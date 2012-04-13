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
import inspect
import os as _os
from contextlib import contextmanager

@contextmanager
def chdir(path, makedirs=False):
    cwd = _os.getcwd()
    try:
        if makedirs and not _os.path.isdir(path):
            _os.makedirs(path)
        _os.chdir(path)
        yield path
    finally:
        _os.chdir(cwd)

def this(start_path=None, traverse=False, __depth=1):
    """ 
    A helper for finding an absolute path from the calling
    script or program. 
    
    >>> this() #doctest: +ELLIPSIS
    '.../paths.py'

    If optional argument start_path is not provided, the caller's 
    path is determined by inspecting the stack. If no viable 
    path is automatically detected the path to this module 
    (via __file__) is used instead. As in, 

    >>> this(__file__) #doctest: +ELLIPSIS
    '.../paths.py'

    >>> this(traverse=True) #doctest: +ELLIPSIS
    '.../doctest.py'

    If optional argument traverse is set to True the stack is 
    searched (from bottom up) until a valid path is found, or 
    if no frame contains a valid path, the path to this module 
    is used instead (as above). 
    """
    if start_path is None:
        if traverse:
            # start with the caller
            stack = inspect.stack()[__depth:]
            for i in range(len(stack)):
                start_path = stack[i][1]
                if _os.path.exists(start_path): break
        else:
            start_path = inspect.stack()[__depth][1]

        if not _os.path.exists(start_path):
            start_path = __file__
    return _os.path.realpath(_os.path.abspath(start_path))

def thisdir(start_path=None, traversal=False, __depth=2):
    """ 
    A helper for finding an absolute path to a directory containing
    a relative path element, usually __file__ is passed as script.
    
    >>> thisdir() #doctest: +ELLIPSIS
    '.../utils'
    """
    return _os.path.dirname(this(start_path, traversal, __depth))

def jointhis(element, start_path=None, traversal=False):
    """
    A helper for joining the path to a directory containing
    a relative path element, resulting in an absolute path 
    to the resource, usually __file__ is passed as script.
    
    >>> jointhis('nothing.txt') #doctest: +ELLIPSIS
    '.../nothing.txt'
    """
    return _os.path.join(thisdir(start_path, traversal, 3), element)





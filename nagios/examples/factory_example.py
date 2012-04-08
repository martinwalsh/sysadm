#!/usr/bin/env python
import sys; sys.path.append('../')

from plugin import NagiosPluginFactory


if __name__ == '__main__':
    def some_function():
        return [(10, 'Value %(value)s is %(status)s')]
    
    NagiosPluginFactory('CustomCheck', some_function, network=False).check()



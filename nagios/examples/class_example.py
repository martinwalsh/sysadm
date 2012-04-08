#!/usr/bin/env python
import sys; sys.path.append('../')

import time
from plugin import NagiosArgParser, NagiosPlugin, UnhandledExceptionHandler

class ExamplePlugin(NagiosPlugin):        
    @UnhandledExceptionHandler()
    def check(self):
        
        if self.options.simulate:
            # simulate a timeout
            time.sleep(self.options.timeout+1)
        
        self.performance.add_label('testValue', self.options.testValue)
        
        code = self.check_thresholds(self.options.testValue)
        
        info = 'Value is %s' % self.options.testValue
        self.die(code, info)

if __name__ == '__main__':
    parser = NagiosArgParser()
    parser.add_option('-N', '--number', dest='testValue', type='float',  
                      help='a test value', default=10)
    parser.add_option('-S', '--simulate-timeout', dest='simulate', 
                      action='store_true', help='simulate a timeout condition')
    
    ExamplePlugin(parser).check()
    

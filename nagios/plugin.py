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
import os
import re
import sys
import signal
import socket
import logging
import optparse
import traceback

"""
nagios/plugin.py Martin Walsh <sysadm@mwalsh.org>
    A collection of functions, constants, and classes intended to 
    ease the development of nagios plugins.
"""

__version__ = '0.4'
__package__ = 'sysadm'

__all__ = [
    'OK', 'WARN', 'CRIT', 'UNKN', 'LOG0', 'LOG1', 'LOG2', 'LOG3', 
    'NagiosArgParser', 'NagiosPlugin', 'UnhandledExceptionHandler',
]

# default thresholds
DEFAULT_WARN = 75
DEFAULT_CRIT = 90

# default socket/sigalrm timeout
try:
    DEFAULT_TIMEOUT = os.environ['DEFAULT_SOCKET_TIMEOUT']
except KeyError:
    DEFAULT_TIMEOUT = 20 # seconds

# nagios return codes
OK   = 0 # A-OK
WARN = 1 # Warning
CRIT = 2 # Critical
UNKN = 3 # Unknown

# nagios log levels
LOG0 = 103 # Single line, minimal output. Summary
LOG1 = 102 # Single line, additional information (eg list processes that fail)
LOG2 = 101 # Multi line, configuration debug output (eg ps command used)
LOG3 = 100 # Lots of detail for plugin problem diagnosis

def camel_to_under(word):
    """
    Converts standard CamelCase (class) names into lower-words delimited 
    by underscores, using a regexp following these rules:
    
    1. Never match the first character
    2. Match an uppercase character, if it comes after a lowercase letter
    3. Match a number, if it is followed by a lowercase letter, unless it 
       comes after another number
       
    Each match is prefixed by an underscore, and all caps are lowered before 
    returning the result. 

    >>> camel_to_under('camelToUnder')
    'camel_to_under'
    >>> camel_to_under('CamelToUnder')
    'camel_to_under'
    >>> camel_to_under('CamelToUnder2')
    'camel_to_under2'
    >>> camel_to_under('CamelToUnder2nd')
    'camel_to_under_2nd'
    """
    
    pattern = re.compile(
            r"(?<!^)(((?<=[a-z])[A-Z])|((?<![0-9])[0-9](?=[a-z])))"
    )
    return pattern.subn(r"_\1", word, 0)[0].lower()

class NagiosPluginError(Exception): pass

class NagiosPerfLabel(object):
    """
    A collection of performance metrics used for rrd graphing.

    >>> label = NagiosPerfLabel('temp', 75)
    >>> label.value
    75

    >>> label = NagiosPerfLabel('temp', 75, 'S', strict=True)
    Traceback (most recent call last):
    ...
    NagiosPluginError: Invalid UOM provided for performance data.
    """
    # Units of measure allowed in performance data, as 
    # defined by the nagios plugin development guidelines
    allowed_uoms = ['',                         # null, as number (int, float) 
                    's', 'us', 'ms',            # measure of time
                    '%',                        # percentage
                    'B', 'KB', 'MB', 'GB', 'TB',# quantity in bytes
                    'c',                        # continuous counter
    ]
    def __init__(self, label, value, uom='', warn='', 
                 crit='', min='', max='', strict=False):
        """
        @param label:  the name of the metric 
        @param value:  the value/data produced
        @param uom:    the unit of measure for value 
        @param warn:   the warning threshold (to be graphed)
        @param crit:   the critical threshold (to be graphed) 
        @param min:    the min value since last check (if applicable) 
        @param max:    the max value since last check (if applicable) 
        @param strict: determines if uom is restricted to nagios dev spec
        """
        
        if strict and uom not in self.allowed_uoms:
            raise NagiosPluginError(
                    'Invalid UOM provided for performance data.'
            )
            
        self.label = label
        self.value = value
        self.uom = uom
        self.warn = warn
        self.crit = crit
        self.min = min
        self.max = max

class NagiosPerformance(object):
    """
    Represents all performance data collected during a NagiosPlugin
    check sequence. 

    >>> perf = NagiosPerformance()

    >>> 'Not empty' if perf else 'Empty'
    'Empty'

    >>> perf.add_label('temp', 75)

    >>> 'Not empty' if perf else 'Empty'
    'Not empty'

    >>> perf.format_performance()
    "|'temp'=75.00;;;;"
    >>> '%r' % perf
    "|'temp'=75.00;;;;"
    >>> '%s' % perf
    "|'temp'=75.00;;;;"


    >>> perf = NagiosPerformance()
    >>> perf.add_label('temp', 75, 'S', strict=True)
    Traceback (most recent call last):
    ...
    NagiosPluginError: Invalid UOM provided for performance data.

    >>> perf = NagiosPerformance()

    """  
    _fmt = "'%(label)s'=%(value)0.2f%(uom)s;%(warn)s;%(crit)s;%(min)s;%(max)s"

    def __init__(self):
        self.labels = []
        
    def __nonzero__(self):
        """ 
        Returns True if performance data has been added 
        (via add_label), False otherwise. 
        """
        return bool(self.labels)
    # renamed to __bool__ in python 3000
    __bool__ = __nonzero__
        
    def add_label(self, label, value, uom='', warn='', 
                    crit='', min='', max='', strict=False):
        """ 
        Adds a unique label to the performance record. Raises a 
        NagiosPluginError if the label provided is not unique.
        See NagiosPerfLabel for a description of the arguments.  
        """   
        if label in self.labels:
            raise NagiosPluginError('Performance labels must be unique.')
        else:         
            self.labels.append(
                NagiosPerfLabel(
                    label, value, uom, warn, crit, min, max, strict
                )
            )
        
    def format_performance(self):
        """
        Returns a formatted representation of performance data as
        described in the nagios-plugin development guidelines. 
        """ 
        if self.labels:
            o = [self._fmt % label.__dict__ for label in self.labels]
            return '|'+' '.join(o)
        else:
            return '' 
    # allow alternative access to formated performance
    __repr__ = __str__ = format_performance


class NagiosRange(object):
    """
    Object representing a range as defined by the nagios-plugin
    development guidelines. as follows:
    
    A range is defined as a start and end point (inclusive) on a numeric 
    scale (possibly negative or positive infinity). This is the generalized 
    format for ranges: [@]start:end
    
    1. start <= end
    2. start and ":" is not required if start=0
    3. if range is of format "start:" and end is not specified, 
       assume end is infinity
    4. to specify negative infinity, use "~"
    5. alert is raised if metric is outside start and end range 
       (inclusive of endpoints)
    6. if range starts with "@", then alert if inside this range 
       (inclusive of endpoints)

    >>> rnge = NagiosRange('10')
    >>> filter(None, [rnge.check_range(x) for x in range(11)])
    []
    >>> all([rnge.check_range(x) for x in range(-5, 0)])
    True
    >>> all([rnge.check_range(x) for x in range(11, 21)])
    True

    >>> rnge = NagiosRange('10:')
    >>> filter(None, [rnge.check_range(x) for x in range(10, 15)])
    []
    >>> all([rnge.check_range(x) for x in range(-10, 10)])
    True

    >>> rnge = NagiosRange('~:10')
    >>> filter(None, [rnge.check_range(x) for x in range(-9, 10)])
    []
    >>> all([rnge.check_range(x) for x in range(11, 21)])
    True

    >>> rnge = NagiosRange('10:20')
    >>> filter(None, [rnge.check_range(x) for x in range(10, 21)])
    []
    >>> all([rnge.check_range(x) for x in range(-10, 10)])
    True
    >>> all([rnge.check_range(x) for x in range(21, 30)])
    True

    >>> rnge = NagiosRange('@10:20')
    >>> filter(None, [rnge.check_range(x) for x in range(-10, 10)])
    []
    >>> filter(None, [rnge.check_range(x) for x in range(21, 30)])
    []
    >>> all([rnge.check_range(x) for x in range(10, 21)])
    True

    >>> rnge = NagiosRange('10:20@')
    Traceback (most recent call last):
    ...
    NagiosPluginError: Invalid end value '10:20@' in 'unknown' range.
    """
    def __init__(self, range, type='unknown'):
        """
        @param range:  the range definition, None effectively disables 
                       this range (always returns False when checked)
        @param type:   the threshold type (waring|critical) 
        """ 
        self.range = range
        self.type = type
        # defaults 
        self.start = 0
        self.start_infinity = False
        self.end = 0
        self.end_infinity = True
        # alert_on
        self.inside = False
        
        self.__parse_range()

    def __eq__(self, other):
        return (self.range, self.type) == (other.range, other.type)
        
    def __str__(self):
        """ String casting operations return the range definition. """
        if self.range is None:
            return ''
        else:
            return self.range
        
    def __parse_range(self):
        """
        Private method for parsing the range definition into 
        useful comparison value(s). 
        """ 
        if self.range is None: return
        
        range = self.range       
        if range.startswith('@'):
            self.inside = True
            range = range[1:]
        
        try:
            start, end = range.split(':')
        except ValueError: # we have only one end-point
            try:
                self.end = float(range)
            except ValueError: # but it's not a number
                message = "Invalid range definition '%s' in '%s' range."
                raise NagiosPluginError(message % (self.range, self.type))
            else:
                self.end_infinity = False
        else:
            if start == '~':
                self.start_infinity = True
            else:
                try:
                    self.start = float(start)
                except ValueError:
                    message = "Invalid start value '%s' in '%s' range."
                    raise NagiosPluginError(
                            message % (self.range, self.type)
                    )
            try:
                self.end = float(end)
            except ValueError: 
                if end is not '': 
                    message = "Invalid end value '%s' in '%s' range."
                    raise NagiosPluginError(
                            message % (self.range, self.type)
                    )
            else:
                self.end_infinity = False
                
    def check_range(self, value):
        """
        Check if the value is outside of the range definition (or inside 
        the range if this is an inclusive range). 
        
        @param value: the value to check
        @return: bool, True if outside the threshold, False otherwise
        """
        if type(value) not in (int, long, float):
            raise ValueError("Value '%s' is not a number." % value)
        
        if self.range is None:
            return False
                
        if not self.start_infinity and not self.end_infinity:
            if self.start <= value <= self.end:
                inrange = True
            else:
                inrange = False
        elif not self.start_infinity and self.end_infinity:
            if self.start <= value:
                inrange = True
            else:
                inrange = False
        elif self.start_infinity and not self.end_infinity:
            if value <= self.end:
                inrange = True
            else:
                inrange = False
                
        if self.inside:
            return inrange
        else:
            return not inrange
        
class NagiosThresholds(object):
    """
    A collection of ranges as defined by the nagios-plugin
    development guidelines which states: A threshold is a range 
    with an alert level (either warning or critical).

    >>> th = NagiosThresholds('10', '20')
    >>> assert th.warning == NagiosRange('10', 'warning')
    >>> assert th.critical == NagiosRange('20', 'critical')

    >>> th = NagiosThresholds('10#', '$30')
    >>> assert th.warning == NagiosRange(None, 'warning')
    >>> assert th.critical == NagiosRange(None, 'critical')
    """
    def __init__(self, warningRange, criticalRange):
        """
        @param NagiosRange warningRange: the warning range
        @param NagiosRange criticalRange: the critical range
        
        NOTE: invalid nagios range definitions are silently ignored
        """
        try:
            self.warning = NagiosRange(warningRange, 'warning')
        except NagiosPluginError, e:
            logging.log(LOG2, e.message)
            self.warning = NagiosRange(None, 'warning')
    
        try:
            self.critical = NagiosRange(criticalRange, 'critical')
        except NagiosPluginError, e:
            logging.log(LOG2, e.message)
            self.critical = NagiosRange(None, 'critical')
        
class NagiosArgParser(object):
    """
    A very thin wrapper around an optparse.OptionParser which 
    adds a few default options as required by the nagios plugin 
    development guidelines. 
    
       -w warning threshold (--warning)
       -c critical threshold (--critical)
       -v verbose (--verbose)
       -V version (--version)
       -H hostname (--hostname)
       -t timeout (--timeout)
       -h help (--help) * already defined by optparse.OptionParser
       
    NOTE: It is assumed that these options are available to all nagios plugins. 
    """
    def __init__(self, *args, **kwargs):
        self.optionparser = optparse.OptionParser(*args, **kwargs)
        # nagios thresholds
        self.add_option('-w', '--warning', dest='warning', default=None,  
                        help='warning range threshold def')
        self.add_option('-c', '--critical', dest='critical', default=None, 
                        help='critical range threshold def')
        # other nagios reserved
        self.add_option('-v', '--verbose', action='count', dest='verbosity', 
                        help='increase verbosity')
        self.add_option('-V', '--version', action='store_true', default=False,  
                        dest='version', help='the plugin version')
        self.add_option('-H', '--hostname', dest='hostname', 
                        help='hostname or ip address to check')
        self.add_option('-t', '--timeout', dest='timeout', type='float', 
                        default=DEFAULT_TIMEOUT, help='script timeout')
    __init__.__doc__ = optparse.OptionParser.__init__.__doc__
            
    def add_option(self, *args, **kwargs):
        self.optionparser.add_option(*args, **kwargs)
    add_option.__doc__ = optparse.OptionParser.add_option.__doc__
    
    def add_options(self, *args, **kwargs):
        self.optionparser.add_options(*args, **kwargs)
    add_options.__doc__ = optparse.OptionParser.add_options.__doc__
        
    def parse_args(self, args=None, values=None):
        options, args = self.optionparser.parse_args(args, values)
        # comply with nagios log levels
        if options.verbosity is None:
            options.verbosity = 0
        if options.verbosity > 103:
            options.verbosity = 103
        options.verbosity = LOG0 - options.verbosity 
        return options, args
    parse_args.__doc__ = optparse.OptionParser.parse_args.__doc__
    
class UnhandledExceptionHandler(object):
    """
    A class to decorate nagios plugin check methods so that all 
    exceptions are handled, even unhandled ones. 
    """
    _fmt = '\n#\n##\n%s##\n#\n'

    def __call__(self, func):
        def wrapper(instance, *args, **kwargs):
            try:
                func(instance, *args, **kwargs)
            except SystemExit, e:
                sys.exit(e.code)
            except:
                instance.die(UNKN, self._fmt % traceback.format_exc())
                
        return wrapper

class NagiosPlugin(object):
    """
    Base class for all nagios plugins, provides the basic mechanism for 
    running a check and returning appropriately formatted output (including 
    performance data) as described in the nagios plugin development guidelines. 
    Subclasses should, at a minimum override the 'check' method, which may or
    may not be decorated with @UnhandledExceptionHandler(), to trap unhandled 
    exceptions, at the subclass author's discretion. 
    """
    __plugin_version__ = '$Revision: 0.1 $'
    
    __package_version__ = __version__  
    __package_name__ = __package__
    
    codewords = {
        OK:   'OK', 
        WARN: 'WARNING', 
        CRIT: 'CRITICAL', 
        UNKN: 'UNKNOWN', 
    }
    
    _fmt = '%(service)s %(status)s: %(info)s%(perf)s'
    
    def __init__(self, parser=None, network=True):
        """
        @param parser: a customized command line parser (optional)
        @param network: determines if the default socket timeout should be
                        set in addition to an alarm signal (if True, the 
                        default socket timeout is set from the timeout command
                        line option, and the sigalrm is set to same + 
                        SIGALRM_OFFSET, otherwise the a sigalrm is set with
                        the value of the timeout command line option)
        """
        if not isinstance(parser, NagiosArgParser): 
            parser = NagiosArgParser()
            
        self.performance = NagiosPerformance()
        
        options, args = parser.parse_args()
        
        logging.addLevelName(LOG0, 'L0')
        logging.addLevelName(LOG1, 'L1')
        logging.addLevelName(LOG2, 'L2')
        logging.addLevelName(LOG3, 'L3')
        logging.basicConfig(
            level=options.verbosity, format='%(message)s', stream=sys.stdout
        )
        
        # if version option then die peacefully            
        if options.version: self.__print_revision()
            
        if network:
            socket.setdefaulttimeout(options.timeout)
            signal_timeout = options.timeout + 1
        else:
            signal_timeout = options.timeout
            
        signal.signal(signal.SIGALRM, self.__handle_sigalrm)
        signal.alarm(int(signal_timeout)) # requires int 
            
        self.thresholds = NagiosThresholds(options.warning, options.critical)
        
        # shortcuts/aliases
        self.warning = self.thresholds.warning
        self.critical = self.thresholds.critical
        self.options, self.args = options, args
        
    def __handle_sigalrm(self, signum, frame):
        """
        Private method for processing a SIGALRM.
        """
        if self.options.timeout > 1: 
            plural = 's'
        else:
            plural = ''
            
        self.die(CRIT, 'Plugin timed out after %0.2f second%s.' % \
                 (self.options.timeout, plural), cancel_alarm=False)
               
    def __print_revision(self):
        """  
        Private method which responds to the -V (--version) command line option.
        """
        revision = '%s (%s %s) %s' % (
            camel_to_under(self.__class__.__name__), self.__package_name__, 
            self.__package_version__, self.__plugin_version__
        )
        logging.log(LOG0, revision)
        sys.exit(OK)

    def __format_dict(self, status, info):
        """
        Private method used to format plugin output. Should match the 
        signature provided by _fmt.
        """ 
        return dict(
            service = camel_to_under(self.__class__.__name__), 
            status = status,  
            info = info, 
            perf = self.performance.format_performance()
        )
        
    def check_thresholds(self, value):
        """
        Check both thresholds (warning and range) against value, and return 
        the appropriate status code
        
        @param value:    the value to check
        @return: int (one of OK, WARN, CRIT, or UNKN)
        """      
        if self.critical is not None and self.critical.check_range(value):
            code = CRIT
        elif self.warning is not None and self.warning.check_range(value):
            code = WARN
        else:
            code = OK
            
        return code
                
    def die(self, code, info, cancel_alarm=True):
        """
        Die gracefully, with appropriate output, canceling 
        the SIGALRM if necessary.
        """
        if cancel_alarm: 
            signal.alarm(0)
            message_map = self.__format_dict(self.codewords[code], info)
        else:
            message_map = self.__format_dict('SIGALRM', info)
        logging.log(LOG0, self._fmt % message_map)
        
        sys.exit(code)
        
    @UnhandledExceptionHandler()
    def check(self):
        """
        It is recommended that you override this method in your subclass, 
        and use it to perform any and all checks -- add performance data
        when appropriate, call check_thresholds to retrieve service status, 
        and die. However, it would be possible to use another named method 
        for a similar purpose -- but you run the risk of breaking 
        compatibility with a future version.    
        """
        raise NotImplementedError(
            "Subclasses of 'NagiosPlugin must override the 'check' method."
        )
        
class NagiosPluginFactory(object):
    """
    Auto-magically creates a very basic NagiosPlugin subclass from provided 
    parameters.
    
    @param plugin_name:   the name of the plugin (used for nagios-style output)
    @param checkFuction: the user created check function -- should return a 
                         sequence of (value, message) pair(s). 
    @param parser:       mirrors the NagiosPlugin constructor, a custom 
                         NagiosArgParser
    @param network:      mirrors the NagiosPlugin constructor (set a socket 
                         timeout)
    """
    def __init__(self, plugin_name, check_function, parser=None, network=True):
        self.plugin = NagiosPlugin(parser, network)
        self.plugin.__class__.__name__ = plugin_name
        self.plugin.check = check_function

    def __format_message(self, message, value, code):
        return message % dict(
                status=self.plugin.codewords[code], value=value, code=code
        )
    
    @UnhandledExceptionHandler()
    def check(self, perf_labels=None, *args, **kwargs):
        responses = self.plugin.check(*args, **kwargs)
        
        if perf_labels:
            for i, label in enumerate(perf_labels):
                try:
                    value, message = responses[i]
                except IndexError:
                    raise NagiosPluginError(
                    'Too few values, trouble matching label "%s".' % label
                    )
                else:
                    self.plugin.performance.add_label(label, value)

        codes = []; messages = []
        for value, message in responses:
            code = self.plugin.check_thresholds(value)
            messages.append(self.__format_message(message, value, code))
            codes.append(code)
            
        codes.sort(); codes.reverse()
        self.plugin.die(codes[0], ', '.join(messages))
        
    def die(self, code, info, cancel_alarm=True):
        self.plugin.die(code, info, cancel_alarm)
        
                


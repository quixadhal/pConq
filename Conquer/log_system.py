# -*- coding: utf-8 -*- line endings: unix -*-
__author__ = 'quixadhal'

import sys
import logging
import datetime
import pytz


def today():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')

def now_stamp():
    right_now = datetime.datetime.now(datetime.timezone.utc)
    part = right_now.strftime('%Y-%m-%d %H:%M:%S')
    msecs = right_now.microsecond
    result = "%s.%03d %s" % (part, msecs, datetime.timezone.utc)
    return result

def now():
    return datetime.datetime.now(datetime.timezone.utc).timestamp()


class LogReformatter(logging.Formatter):
    """
    The LogReformatter class allows us to change the formatting to properly
    align the text strings of a multi-line log entry to line up under the
    initial one, padding over the timestamp and other information.

    We also change the timestamp to add milliseconds as a faction, rather
    than the bizzare comma version that's the default.

    :return: An object which does proper formatting of our log entries
    :rtype: object
    """

    #ut = datetime.datetime.fromtimestamp(time.time())
    #print(ut.astimezone().tzinfo)

    time_converter = datetime.datetime.fromtimestamp

    def format(self, record):
        message = super().format(record)
        barpos = message.find('| ')
        if barpos >= 0:
            message = message.replace('\n', '\n' + ' '.ljust(barpos + 2))
        return message

    def formatTime(self, record, datefmt=None):
        timestamp = self.time_converter(record.created).astimezone(pytz.timezone('UTC'))
        if datefmt:
            result = timestamp.strftime(datefmt)
        else:
            part = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            result = "%s.%03d %s" % (part, record.msecs, timestamp.tzinfo)
        return result


class StreamLogger(logging.StreamHandler):
    """
    The StreamLogger class is really just a stream wrapper that imposes our
    custom formatting on any logging object that calls addHandler() with
    us.  The LogReformatter class above does the actual work.

    :return: A handler object for a logging stream.
    :rtype: object
    """

    def __init__(self):
        logging.StreamHandler.__init__(self)

        format_string = '%(asctime)s %(name)-8s %(levelname)-8s %(module)12s:%(lineno)5d| %(message)s'
        formatter = LogReformatter(format_string)
        self.setFormatter(formatter)


class FileLogger(logging.FileHandler):
    """
    The FileLogger class is really just a file wrapper that imposes our
    custom formatting on any logging object that calls addHandler() with
    us.  The LogReformatter class above does the actual work.

    :return: A handler object for a logging file.
    :rtype: object
    """

    def __init__(self, filename):
        if not filename.endswith(".log"):
            filename += ".log"
        logging.FileHandler.__init__(self, filename)

        format_string = '%(asctime)s %(name)-8s %(levelname)-8s %(module)12s:%(lineno)5d| %(message)s'
        formatter = LogReformatter(format_string)
        self.setFormatter(formatter)


class Loggers(object):
    """
    This is a singleton container class to hold our logger info and let us
    do basic setup when it gets instantiated.
    """
    _loggers = {}

    @classmethod
    def addLogger(cls, name):
        if name not in cls._loggers.keys():
            this_log            = logging.getLogger(name)
            this_stream         = StreamLogger()
            this_log.setLevel(logging.DEBUG)
            this_log.addHandler(this_stream)
            this_log.getName            = cls.getName.__get__(this_log)         # evil
            this_log.startFileoutput    = cls.startFileoutput.__get__(this_log) # evil
            this_log.stopFileoutput     = cls.stopFileoutput.__get__(this_log)  # evil
            cls._loggers[name] = {
                    "name"      : name,
                    "logger"    : this_log,
                    "stream"    : this_stream,
                    "file"      : None
                    }
        return cls._loggers[name]["logger"]

    @classmethod
    def showLoggers(cls):
        return ', '.join(cls._loggers.keys())

    # These functions get monkey-patched into the logging objects that
    # will use them.  This is evil.  Don't do this.

    def getName(self):
        """
        A small inefficient function to find the name of the logging
        object from which it was called.  Do this differently if you want
        to use the name in something that's called frequently.

        :return: The name of the logging object.
        :rtype: string
        """
        for i in Loggers._loggers:
            if Loggers._loggers[i]["logger"] is self:
                return i
        return None

    def startFileoutput(self):
        """
        This adds a file output logging handler to the logging object
        that called it, effectively starting logging to a fixed filename,
        which will be based on the logger name.
        This gets installed via a monkey-patch.

        :return: Nothing.
        :rtype: None
        """
        name = self.getName()
        print("Starting file log for %s" % (name))
        this_file = FileLogger(name + '-' + today())
        self.addHandler(this_file)
        Loggers._loggers[name]["file"] = this_file

    def stopFileoutput(self):
        """
        This removes a file output logging handler from the logging
        object that called it, effectively stopping output to that
        file.
        This gets installed via a monkey-patch.

        :return: Nothing.
        :rtype: None
        """
        name = self.getName()
        print("Stopping file log for %s" % (name))
        this_file = Loggers._loggers[name]["file"]
        #this_file.close()
        self.removeHandler(this_file)
        Loggers._loggers[name]["file"] = None


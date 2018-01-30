#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import inspect
import unicodedata
import locale
from lib.core.settings import UNICODE_ENCODING, INVALID_UNICODE_CHAR_FORMAT
from lib.core.settings import (BANNER, GIT_PAGE, ISSUES_PAGE, PLATFORM, PYVERSION, VERSION_STRING)
from lib.core.data import paths
from lib.core.convert import stdoutencode
from lib.core.exception import ZEROScanSystemException
from thirdparty.termcolor.termcolor import colored
from thirdparty.odict.odict import OrderedDict

def getUnicode(value, encoding=None, noneToNull=False):
    """
    Return the unicode representation of the supplied value:

    >>> getUnicode(u'test')
    u'test'
    >>> getUnicode('test')
    u'test'
    >>> getUnicode(1)
    u'1'
    """

    if noneToNull and value is None:
        return u'NULL'

    if isListLike(value):
        value = list(getUnicode(_, encoding, noneToNull) for _ in value)
        return value

    if isinstance(value, unicode):
        return value
    elif isinstance(value, basestring):
        while True:
            try:
                return unicode(value, encoding or UNICODE_ENCODING)
            except UnicodeDecodeError, ex:
                try:
                    return unicode(value, UNICODE_ENCODING)
                except:
                    value = value[:ex.start] + "".join(INVALID_UNICODE_CHAR_FORMAT % ord(_) for _ in value[ex.start:ex.end]) + value[ex.end:]
    else:
        try:
            return unicode(value)
        except UnicodeDecodeError:
            return unicode(str(value), errors="ignore")  # encoding ignored for non-basestring instances

def isListLike(value):
    """
    Returns True if the given value is a list-like instance

    >>> isListLike([1, 2, 3])
    True
    >>> isListLike(u'2')
    False
    """

    return isinstance(value, (list, tuple, set))

def unhandledExceptionMessage():
    """
    Returns detailed message about occurred unhandled exception
    """

    errMsg = "unhandled exception occurred in %s. It is recommended to retry your " % VERSION_STRING
    errMsg += "run with the latest development version from official Gitlab "
    errMsg += "repository at '%s'. If the exception persists, please open a new issue " % GIT_PAGE
    errMsg += "at '%s' " % ISSUES_PAGE
    errMsg += "with the following text and any other information required to "
    errMsg += "reproduce the bug. The "
    errMsg += "developers will try to reproduce the bug, fix it accordingly "
    errMsg += "and get back to you\n"
    errMsg += "zeroscan version: %s\n" % VERSION_STRING[VERSION_STRING.find('/') + 1:]
    errMsg += "Python version: %s\n" % PYVERSION
    errMsg += "Operating system: %s\n" % PLATFORM

    return errMsg

def setPaths():
    """
    Sets absolute paths for project directories and files
    """

    paths.ZEROSCAN_PLUGINS_PATH = os.path.join(paths.ZEROSCAN_ROOT_PATH, "plugins")
    paths.ZEROSCAN_DATA_PATH = os.path.join(paths.ZEROSCAN_ROOT_PATH, "data")
    paths.ZEROSCAN_TARGET_PATH = os.path.join(paths.ZEROSCAN_ROOT_PATH, "targets")


    paths.ZEROSCAN_TMP_PATH = os.path.join(paths.ZEROSCAN_PLUGINS_PATH, "tmp")
    paths.USER_AGENTS = os.path.join(paths.ZEROSCAN_DATA_PATH, "user-agents.txt")
    paths.WEAK_PASS = os.path.join(paths.ZEROSCAN_DATA_PATH, "password-top100.txt")
    paths.LARGE_WEAK_PASS = os.path.join(paths.ZEROSCAN_DATA_PATH, "password-top1000.txt")
    paths.WEB_DB = os.path.join(paths.ZEROSCAN_DATA_PATH, "web.db")

    paths.ZEROSCAN_OUTPUT_PATH = getUnicode(paths.get("ZEROSCAN_OUTPUT_PATH", os.path.join(paths.ZEROSCAN_ROOT_PATH, "output")), encoding=sys.getfilesystemencoding())

def banner():
    """
    Function prints ZEROScan banner with its version
    """
    _ = BANNER
    dataToStdout(_)


def dataToStdout(data, bold=False):
    """
    Writes text to the stdout (console) stream
    """

    message = ""

    if isinstance(data, unicode):
        message = stdoutencode(data)
    else:
        message = data

    sys.stdout.write(setColor(message, bold))

    try:
        sys.stdout.flush()
    except IOError:
        pass

def setColor(message, bold=False):
    retVal = message

    if message:
        if bold:
            retVal = colored(message, color=None, on_color=None, attrs=("bold",))

    return retVal

def safeExpandUser(filepath):
    """
    @function Patch for a Python Issue18171 (http://bugs.python.org/issue18171)
    """

    retVal = filepath

    try:
        retVal = os.path.expanduser(filepath)
    except UnicodeDecodeError:
        _ = locale.getdefaultlocale()
        retVal = getUnicode(os.path.expanduser(filepath.encode(_[1] if _ and len(_) > 1 else UNICODE_ENCODING)))

    return retVal

#打开文件夹并批量读取内容，以行为单位，可以自定义全部小写lowercase、是都采用有序列表unique
def getFileItems(filename, commentPrefix='#', unicode_=True, lowercase=False, unique=False):
    """
    @function returns newline delimited items contained inside file
    """

    retVal = list() if not unique else OrderedDict()
    checkFile(filename)

    try:
        with open(filename, 'r') as f:
            for line in (f.readlines() if unicode_ else f.xreadlines()):
                # xreadlines doesn't return unicode strings when codecs.open() is used
                if commentPrefix and line.find(commentPrefix) != -1:
                    line = line[:line.find(commentPrefix)]

                line = line.strip()

                if not unicode_:
                    try:
                        line = str.encode(line)
                    except UnicodeDecodeError:
                        continue

                if line:
                    if lowercase:
                        line = line.lower()

                    if unique and line in retVal:
                        continue

                    if unique:
                        retVal[line] = True

                    else:
                        retVal.append(line)

    except (IOError, OSError, MemoryError), ex:
        errMsg = "something went wrong while trying "
        errMsg += "to read the content of file '%s' ('%s')" % (filename, ex)
        raise ZEROScanSystemException(errMsg)

    return retVal if not unique else retVal.keys()

def checkFile(filename):
    """
    @function Checks for file existence and readability
    """

    valid = True

    if filename is None or not os.path.isfile(filename):
        valid = False

    if valid:
        try:
            with open(filename, "rb"):
                pass
        except:
            valid = False

    if not valid:
        raise ZEROScanSystemException("unable to read file '%s'" % filename)

def reIndent(s, numSpace):
    leadingSpace = numSpace * ' '
    lines = [leadingSpace + line for line in s.splitlines()]
    return '\n'.join(lines)

def normalizeUnicode(value):
    """
    Does an ASCII normalization of unicode strings
    Reference: http://www.peterbe.com/plog/unicode-to-ascii

    >>> normalizeUnicode(u'\u0161u\u0107uraj')
    'sucuraj'
    """

    return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore') if isinstance(value, unicode) else value

def getPublicTypeMembers(type_, onlyValues=False):
    """
    Useful for getting members from types (e.g. in enums)

    >>> [_ for _ in getPublicTypeMembers(OS, True)]
    ['Linux', 'Windows']
    """

    for name, value in inspect.getmembers(type_):
        if not name.startswith('__'):
            if not onlyValues:
                yield (name, value)
            else:
                yield value


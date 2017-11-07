'''
Created on 11.05.2013

@author: kca
'''

try:
    from types import ClassType
except ImportError:
    ClassType = type

try:
    basestring = basestring
except NameError:
    basestring = str

try:
    BASE_STR = unicode
except NameError:
    BASE_STR = str

'''
Created on 13.11.2012

@author: kca
'''

try:
    from abc import ABCMeta, abstractmethod, abstractproperty
except ImportError:
    from futile import identity
    ABCMeta = type
    abstractmethod = abstractproperty = identity

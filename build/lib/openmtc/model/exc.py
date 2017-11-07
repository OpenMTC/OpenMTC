'''
Created on 26.05.2013

@author: kca
'''
from openmtc.exc import OpenMTCError


class ModelError(OpenMTCError):
    pass


class ModelTypeError(ModelError, TypeError):
    pass

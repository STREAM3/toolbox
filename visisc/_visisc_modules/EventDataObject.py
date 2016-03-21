# Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
#
# Main author: Tomas Olsson <tol@sics.se>
#
# License: BSD 3 clause

from pyisc import DataObject

class EventDataObject(DataObject):
    '''
    The model that created this event data object.
    '''
    model_ = None
    '''
    The date column used by the model is explicitly kept here, since the support for date is better in python then
    in the C++ data object.
    '''
    dates_ = None
    '''
    The source column used the model is explicitly kept here for making it easy to access it for the EventVisualization class.
    '''
    sources_ = None


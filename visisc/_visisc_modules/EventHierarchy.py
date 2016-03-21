# Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
#
# Main author: Tomas Olsson <tol@sics.se>
#
# License: BSD 3 clause

from visisc import _EventHierEle

__author__ = 'tol'
import visisc
import pyisc


class EventHierarchyElement(_EventHierEle):
    child_ = None
    sibling_ = None
    parent_ = None
    num_of_children = 0
    def __init__(self, name):
        '''
        Create a event description that models the relation between a event and other events
        so that a hierarchy of events can be visualised.
        :param name: the string "name" is the name of the event.
        :param parent: the EventHierarchyElement "parent" is the parent of the event in the sense
        of being a more generic event type or a grouping of events.
        :return:
        '''
        _EventHierEle.__init__(self, name, len(name))


    def set_index_value(self, severity_level, index0):
        '''
        Set the index into the data vector (minus any offset) for a severity level
        :param severity_level: an integer >= 0 and < visisc.get_global_severity_levels() (if only one level exists/is used then it should be set to 0
        :param index: the integer "index" is the index of the event in the data vector for this event and severity_level
        '''
        assert severity_level >= 0 and severity_level < visisc.get_global_num_of_severity_levels()
        pyisc._set_array_value(self.index, severity_level, index0)

    def get_index_value(self, severity_level):
        '''
        Returns the index into the data vector for a severity level. If not set, it is equal to -1
        :param severity_level:
        :return: index to severity level
        '''
        assert severity_level >= 0 and severity_level < visisc.get_global_num_of_severity_levels()
        return _EventHierEle.get_index_value(self, severity_level)

    def add_child(self,element):
        '''
        Extends a parent with a child node.
        :param element:
        :return:
        '''
        element.parent = self
        element.parent_ = self
        self.num_of_children += 1
        if self.child_ is None:
            self.child_ = element
            self.child = element
        else:
            self.child_._add_sibling(element)

    def remove_child(self,element):
        if self.child_ is None:
            return

        if self.child_ == element:
            element.parent = None
            element.parent_ = None
            self.child_ = self.child_.sibling_
            self.child = self.child.sibling
            self.num_of_children -= 1
        else:
            self.child._remove_sibling(element)


    def _add_sibling(self,element):
        if self.sibling_ is None:
            self.sibling_ = element
            self.sibling = element
        else:
            self.sibling_._add_sibling(element)

    def _remove_sibling(self,element):
        if self.sibling_ == element:
            element.parent = None
            element.parent_ = None
            self.sibling_ = self.sibling_.sibling_
            self.sibling = self.sibling.sibling
            self.parent.num_of_children -= 1
        else:
            self.sibling_._remove_sibling(element)

    def to_string(self, level=0):
        '''
        Turns hierarchy to a string.
        :param level:
        :return:
        '''
        str = (" "*level) + self.name
        if self.child_ is not None:
            str += ":\n"
            str += self.child_.to_string(level+1)


        if self.sibling_ is not None:
            str += "\n"
            str += self.sibling_.to_string(level)


        return str

    def next(self):
        '''
        Let the caller iterate through the whole hierarchy until None is returned.
        Beginning with the child and then the siblings.
        :return: next element in the hierarchy.
        '''
        ele = self
        if ele.child_ is not None:
            return ele.child_
        while ele.sibling_ is None and ele.parent_ is not None:
            ele = ele.parent_
        return ele.sibling_


    def __str__(self):
        return self.to_string()



# Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
#
# Main author: Tomas Olsson <tol@sics.se>
#
# License: BSD 3 clause

from abc import abstractmethod

from traits.has_traits import HasTraits
from traits.trait_types import Date, List


class EventSelectionQuery(HasTraits):
    period_start_date = Date
    period_end_date = Date

    list_of_source_classes = List
    selected_list_of_source_classes = List

    list_of_event_severity_levels = List
    selected_list_of_event_severity_levels = List

    list_of_event_names =  List
    selected_list_of_event_names = List

    list_of_source_ids = List
    selected_list_of_source_ids = List


    @abstractmethod
    def execute_query(self):
        '''
        Method should be implemented by any user of the QuerySelectionDialog class.
        It uses Traits for creating a selection. Read Traits manual for more information
        on what can be done in subclasses. See http://docs.enthought.com/traits/traits_user_manual/front.html
        :return:
        '''
        pass
# Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
#
# Main author: Tomas Olsson <tol@sics.se>
#
# License: BSD 3 clause

import sys
from traits.has_traits import HasTraits
from traits.trait_types import String, Button, DelegatesTo, Instance
from traitsui.api import View, Item
from traitsui.editors.check_list_editor import CheckListEditor
from traitsui.editors.history_editor import HistoryEditor
from traitsui.group import Group, HGroup, VGroup
import re

from traitsui.item import Spring

from visisc import EventSelectionQuery


class EventSelectionDialog(HasTraits):
    source_class_label = String("Select Event Source Classes")
    severity_level_label = String("Select Event Severity Levels")

    search = String(regex="^[_a-zA-Z0-9\*\.\$\^\?\s]*$")
    shown_event_names_list = String(regex="[_a-zA-Z0-9\*\.\$\^\?\n]*")
    quit_button = Button('Quit')
    query_button = Button('Run Query...')
    period_start_date = DelegatesTo("query_object")
    period_end_date = DelegatesTo("query_object")

    selected_list_of_event_severity_levels = DelegatesTo("query_object")
    list_of_event_severity_levels = DelegatesTo("query_object")

    selected_list_of_source_classes = DelegatesTo("query_object")
    list_of_source_classes = DelegatesTo("query_object")

    query_object = Instance(EventSelectionQuery)

    spring = Spring

    help_text = ("Search engine like queries using alphanumeric characters and '_'and '.' \n" +
                 "Space indicate OR-separated queries\n" +
                 "? = match any character\n" +
                 "* = any number of characters\n" +
                 "^ = match beginning\n"
                 "$ = match end")

    view = View(
        Group(
            VGroup(
                HGroup(Item("period_start_date", label="Period"),
                       Item("period_end_date", show_label=False),
                       Item("", resizable=True, width=1.0, show_label=False),
                       HGroup(Item('quit_button', show_label=False), Item('query_button', show_label=False)),
                       springy=True
                       ),
                HGroup(VGroup(HGroup(Item("severity_level_label",show_label=False, style="readonly")),
                              Item("selected_list_of_event_severity_levels", editor=CheckListEditor(name="list_of_event_severity_levels"),
                                   style="custom", show_label=False)),
                       VGroup(HGroup(Item("source_class_label", show_label=False, style="readonly")),
                              Item("selected_list_of_source_classes",
                                   editor=CheckListEditor(name="list_of_source_classes"), style="custom",
                                   show_label=False)),
                       # springy=True
                       ),
                show_border=True
            ),
            Item("_"),
            VGroup(
                Item("search", editor=HistoryEditor(auto_set=True), show_label=False, width=1.0, tooltip=help_text),
                Item(name='shown_event_names_list',
                     style='readonly',
                     resizable=True,
                     show_label=False,
                     ),
                scrollable=True,
                show_border=True
            ),
            orientation='vertical',
        ),
        title='Select Events to Visualize',
        dock='horizontal',
        resizable=True,
        width=.5,
        height=.7)

    def __init__(self, query_object, **kwargs):
        '''
        Creates a dialog window for selecting date period, source classes and event severity levels/types.
        :param query_object:
        :return:
        '''
        assert isinstance(query_object, EventSelectionQuery)

        self.shown_event_names_list = "\n".join(list(query_object.list_of_event_names))
        self.query_object = query_object
        self.query_start_date = query_object.period_start_date
        self.query_end_date = query_object.period_end_date

        HasTraits.__init__(self,**kwargs)

    def _search_changed(self):
        '''
        Matches search query to the event names.
        :return:
        '''
        query_st = str(self.search).strip()

        if re.match("^[_a-zA-Z0-9\*\.\$\^\?\s]*$", query_st) is None:
            return

        query_st = query_st.replace(".", "\.")
        query_st = query_st.replace("*", ".*")
        query_st = query_st.replace("?", ".?")
        queries = query_st.split()

        print self.search, query_st, queries,

        if len(queries) == 0:
            queries = [""]

        result = [s for s in list(self.query_object.list_of_event_names) for q in queries if
                  re.search((".*%s.*" % q), s) is not None]

        self.query_object.selected_list_of_event_names = result
        self.shown_event_names_list = "\n".join(result)

        print len(self.shown_event_names_list)

    def _save_search(self):
        # A bug fix, stops the clearing of the search expression
        tmp = self.search
        self.search = " "
        self.search = tmp

        print len(self.query_object.selected_list_of_event_names)

    def _query_button_changed(self):
        self._save_search()
        self.query_object.execute_query()

    def _quit_button_changed(self):
        self._save_search()
        sys.exit(0)

# Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
#
# Main author: Tomas Olsson <tol@sics.se>
#
# License: BSD 3 clause

from numpy import array,r_, ndarray

from pyisc import AnomalyDetector, DataObject
from pyisc import P_PoissonOnesided, P_Poisson
from visisc import _EventDataModel, \
    EventHierarchyElement, \
    EventDataObject, \
    get_global_num_of_severity_levels, \
    set_global_num_of_severity_levels
__author__ = 'tol'


class EventDataModel(_EventDataModel):
    class_column = None
    period_column = None
    root_column = None
    _event_data_object = None
    _anomaly_detector = None
    num_of_event_columns = None
    num_of_severity_levels_ = None


    @staticmethod
    def flat_model(event_columns, event_names=None):
        '''
        Creates a flat event data model event structures with one single top element that is the sum of all the
        provided event columns.

        :param event_columns: column indexes pointing to frequencies of all events
        :param event_names: optional argument for giving names to each column
        :return: an instance of EventDataModel
        '''
        set_global_num_of_severity_levels(1)

        root_column = 2
        new_event_columns = range(root_column + 1, root_column + len(event_columns) + 1)

        if event_columns is not None and len(event_columns) > 0:
            _event_sev2original_column_map = {}
            root = EventHierarchyElement("Root")
            for i in xrange(len(new_event_columns)):
                event = EventHierarchyElement(event_names[i]) \
                    if event_names is not None else \
                    EventHierarchyElement("%i" % event_columns[i])
                event.set_index_value(0, new_event_columns[i])
                event.set_index_component(0, i+1)# Refers to the same component model as provided to the anomaly detector created in an instance method.
                root.add_child(event)
                _event_sev2original_column_map[(event.name, 0)] = event_columns[i]
            root.set_index_value(0,root_column)
            root.set_index_component(0, 0) # First component model below

            num_of_event_columns = len(event_columns) + 1

            model =  EventDataModel(root, num_of_event_columns, 0)
            model.root = root
            model.root_column = root_column
            model.num_of_event_columns = num_of_event_columns
            model._event_sev2original_column_map = _event_sev2original_column_map
            model.num_of_severity_levels_ = 1

            return model

        raise ValueError("No columns provided")


    @staticmethod
    def hierarchical_model(event_columns, get_event_path=None, get_severity_level=None, num_of_severity_levels=1, sep='.'):
        '''
        Creates an hierarchical event data model with types as defined by method get_event_path and with a severity
        level as defined by method get_severity_level.

        :param event_columns: a list or an array with original event column index.
        :param get_event_path: a callable that returns a list with path elements of strings defining the path for the
        event in the hierarchy. The given argument is the event column index from event_columns
        :param get_severity_level: a callable that returns the severity level in terms of an integer from 0 for least
        severity up to num_of_severity_levels as maximum severity level.
        :param num_of_severity_levels: an integer > 0 that specifies the number of severity levels.
        :param sep: a string that is put in between the path elements to form event names.
        :return:
        '''
        if get_severity_level is None:
            set_global_num_of_severity_levels(1)
            num_of_severity_levels = 1
        else:
            set_global_num_of_severity_levels(num_of_severity_levels)

        if event_columns is not None and len(event_columns) > 0:
            # Create Event hierarchy
            root = EventHierarchyElement("Root")
            events = {root.name:root}
            num_of_event_columns = 0
            for i in range(len(event_columns)):
                path0 = get_event_path(event_columns[i]) if get_event_path is not None else ["%i" % event_columns[i]]
                severity_level = get_severity_level(event_columns[i]) if get_severity_level is not None else 0
                parent = root
                if root.get_index_value(severity_level) == -1:
                    root.set_index_value(severity_level, 0)
                    num_of_event_columns += 1
                for h in range(1,len(path0)+1):
                    path = str(sep.join([root.name]+path0[:h]))
                    if path in events.keys():
                        event = events[path]
                    else:
                        event = EventHierarchyElement(path)
                        events[path] = event
                        parent.add_child(event)
                    if event.get_index_value(severity_level) == -1:
                        event.set_index_value(severity_level, i) # index to be replaced with true column index later
                        num_of_event_columns += 1
                    parent = event


            # Replace root if original root has only one child
            if root.num_of_children == 1:
                for sev_lev_ind in xrange(num_of_severity_levels):
                    if root.get_index_value(sev_lev_ind) != -1:
                        num_of_event_columns -= 1
                new_root = root.child_
                del events[root.name]
                for name in events.keys():
                    event = events[name]
                    del events[name]
                    event.name = name[len(root.name) + 1:]
                    events[event.name] = event
                root = new_root
                root.parent_ = None
                root.parent = None

            # Create new data object with hierarchical structure

            root_column = 2 # In _data_object we create a new data object with data from this column

            # map events to column index
            new_column = root_column
            event = root
            _event_sev2original_column_map = {}
            while event is not None:
                for sev_lev_ind in xrange(num_of_severity_levels):
                    if event.get_index_value(sev_lev_ind) != -1:
                        if event.num_of_children == 0:
                            _event_sev2original_column_map[(event.name,sev_lev_ind)] = event_columns[event.get_index_value(sev_lev_ind)] # Store original event columns
                        event.set_index_value(sev_lev_ind, new_column)
                        event.set_index_component(sev_lev_ind, new_column-root_column) # index to the component model provided to the anomaly detector
                        new_column += 1
                event = event.next()

            model = EventDataModel(root, len(events), 0)
            model.root = root
            model.root_column = root_column
            model.num_of_event_columns = num_of_event_columns
            model._event_sev2original_column_map = _event_sev2original_column_map
            model.num_of_severity_levels_ = num_of_severity_levels

            return model

        raise ValueError("No columns provided")

    def data_object(self, X, period_column, date_column, source_column, class_column=None):
        '''
        Creates a EventDataObject using the event model. It only takes a single, common period for all events.

        :param X: an numpy array
        :param period_column: column index pointing to the column containing the period.
        :param date_column: column index pointing to the date of each row, instance of datetime.date
        :param source_column: column index pointing to the identifier of the source of each row: must be convertible to str.
        :param class_column: column index pointing to the class of the source of each row.
        :return: an instance of EventDataObject with new column structure reflecting the event data model.
        '''
        assert isinstance(X, ndarray)

        XT = X.T

        offset_columns = [col for col in [class_column, period_column] if col is not None]

        X_newT = r_[
            XT[offset_columns],
            array([[0.0 for _ in xrange(len(X))] for _ in xrange(self.num_of_event_columns)])
        ]
        self.class_column = 0 if class_column > -1 else None
        self.period_column = 1 if self.class_column == 0 else 0

        # Sum the frequency counts of sub types, starting from the leaves and up
        event = self.root
        while event is not None:
            if event.num_of_children == 0: # If leaf
                for sev_lev_ind in xrange(self.num_of_severity_levels_):
                    if event.get_index_value(sev_lev_ind) != -1:
                        current = event
                        while current is not None:
                            X_newT[current.get_index_value(sev_lev_ind)] += XT[self._event_sev2original_column_map[(event.name,sev_lev_ind)]]
                            current = current.parent
            event = event.next()

        # End creating data object
        self._event_data_object = EventDataObject(X_newT.T,class_column=self.class_column)
        self._event_data_object.model_ = self
        self._event_data_object.dates_ = XT[date_column]
        self._event_data_object.sources_ = array([str(t) for t in XT[source_column]])

        return self._event_data_object

    def fit_anomaly_detector(self, data_object, poisson_onesided=True):
        if poisson_onesided:
            anomaly_detector = AnomalyDetector([
                                                   P_PoissonOnesided(self.root_column+i, self.period_column)
                                                   for i in xrange(self.num_of_event_columns)
                                                   ])
        else:
            anomaly_detector = AnomalyDetector([
                                                   P_Poisson(self.root_column+i, self.period_column)
                                                   for i in xrange(self.num_of_event_columns)
                                                   ])

        self._anomaly_detector = anomaly_detector.fit(data_object, y=self.class_column)

        return anomaly_detector

    def get_event_column_names(self, only_basic_events=False):
        names = []
        event = self.root
        while event is not None:
            if not only_basic_events or event.num_of_children == 0:
                for sev_lev in xrange(self.num_of_severity_levels_):
                    if event.get_index_value(sev_lev) != -1:
                        names += [event.name+"/severity_"+ str(sev_lev)]
            event = event.next()
        return names



    def get_column_names(self):
        names = []
        event = self.root
        while event is not None:
            for sev_lev in xrange(self.num_of_severity_levels_):
                if event.get_index_value(sev_lev) != -1:
                    names += [event.name+"/severity_"+ str(sev_lev)]
            event = event.next()
        return ([] if self.class_column is None else ['Class']) + ['Period'] + names;

    def calc_one(self, data_index):
        assert isinstance(data_index, int) and \
               data_index < len(self._event_data_object) and \
               data_index >= 0

        result  = self._anomaly_detector.anomaly_score_details(self._event_data_object, index=data_index)

        devs_index = 1+self._anomaly_detector.is_clustering + (self._anomaly_detector.class_column > -1)

        devs = result[devs_index]

        expected2 = result[devs_index+1]
        min_out = result[devs_index+2]
        max_out = result[devs_index+3]

        severities = self.summarize_event_anomalies(devs);

        expect = expected2[self._offset:]


        return devs, severities, expect, min_out, max_out

    def summarize_event_anomalies(self, devs):
        sevs = array([0.0]*get_global_num_of_severity_levels())
        ele = self.get_event_hierarchy()
        while ele is not None:
            for i in range(get_global_num_of_severity_levels()):
                if ele.get_index_value(i) != -1:
                    if devs[ele.get_index_component(i)] > sevs[i]:
                        sevs[i] = devs[ele.get_index_component(i)]
            ele = ele.event_hierarchy_next();

        return sevs
# Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
#
# Main author: Tomas Olsson <tol@sics.se>
#
# License: BSD 3 clause

import logging

import datetime
from pandas.core import datetools
from pandas.tseries.index import date_range
from pyface.gui import GUI
from traits.api import HasTraits, Instance
from traits.has_traits import on_trait_change
from traits.trait_types import Int, String, Range, Enum, Bool, Button, List, Date
from traits.traits import Trait

from traitsui.api import View, Item
from traitsui.editors.check_list_editor import CheckListEditor
from traitsui.group import HGroup
from traitsui.editors.range_editor import RangeEditor
from tvtk.pyface.scene_editor import SceneEditor
from mayavi.tools.mlab_scene_model import \
    MlabSceneModel
from mayavi.core.ui.mayavi_scene import MayaviScene

from numpy import array, min, max, median, argmax, unique

import pyisc
from visisc import EventDataModel

# This is used to ignore annoying error messages.
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
h = NullHandler()
logging.getLogger("mayavi.core.common").addHandler(h)

__author__ = 'tol'

class EventVisualization(HasTraits):

    scene = Instance(MlabSceneModel, ())

    def default_traits_view(self):
        view = View(
            Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                 height=600, width=600, show_label=False),
            HGroup(
                Item("current_time", label="Date"),
                Item(" "),
                Item("num_of_shown_days", label="Show"),
                Item("_selected_source_name", label="Selection"),
                Item("_selected_event_name", editor=CheckListEditor(name='_selected_events_list'), show_label=False),

                Item("_back1", show_label=False),
                Item("Relative_Start_Day", show_label=False, editor=RangeEditor(mode="slider", low_name="_low_start_day_number", high_name="_high_start_day_number"), tooltip="Shows total number of days in data set and the currently selected day", springy=True, full_size=True),
                Item("_forward1", show_label=False),
                Item("move_step", show_label=False),
                Item("play_button", label='Play')
            ),
            title="Visualization of Events",
            resizable=True

        )
        view.resizable = True
        return view

    # Index to the currently selected source. None if no source is selected.
    selected_source = Trait(None,None,Int)
    _selected_source_name = Enum(None, [None])


    # index to a selected event. None if not selected.
    selected_event = None
    _selected_event_name = List
    _selected_events_list = List(['None', 'None'])


    # Current (most recent) time, can also be set usinh start day, but then relative to the total number of days.
    current_time = Date
    start_day = Trait(None, int, tuple, String, Date)
    _low_start_day_number = Int(0) # minimum start day = 0
    _high_start_day_number = Int(100) # maximum start day = total number of days

    # Configures the shown number of days in the visualization.
    num_of_shown_days = Trait("30 days", Enum([
        "7 days",
        "14 days",
        "30 days",
        "60 days",
        "90 days",
        "120 days",
        "180 days",
        "365 days"
    ]))





    ## Buttons for controlling the visualization
    _back1 = Button("<", width_padding=0, height_padding=0)
    _forward1 = Button(">", width_padding=0, height_padding=0)

    # Play button sets the visualization on stepping in the last selected direction, back or forth.
    play_button = Bool


    # Configure the number of days the visualization can step.
    move_step = Trait("1 day", Enum(["1 day","2 days","3 days", "7 days"]))

    _last_clicked_direction = None
    def move_backward(self):
        '''
        Moves the shown area backward 1 step.
        :return:
        '''
        if self.Relative_Start_Day >= (self._low_start_day_number+int(self.move_step[0])):
            self.Relative_Start_Day -= int(self.move_step[0])

    def move_forward(self):
        '''
        Moves the shown area forward 1 step.
        :return:
        '''
        if self.Relative_Start_Day <= (self._high_start_day_number-int(self.move_step[0])):
            self.Relative_Start_Day += int(self.move_step[0])

    def __back1_changed(self):
        '''
        Triggered when back button is pressed
        :return:
        '''
        self.move_backward()
        self._last_clicked_direction = self.move_backward


    def __forward1_changed(self):
        '''
        Triggered when forward button is pressed
        :return:
        '''
        self.move_forward()
        self._last_clicked_direction = self.move_forward


    _play_thread = False
    def _play_button_changed(self, play_pressed):
        '''
        Triggered when play button is selected
        :param play_pressed:
        :return:
        '''
        if play_pressed:
            if not self._play_thread:
                self._play_thread = True
                GUI.invoke_after(1, self._play_func)
        else:
            self._play_thread = False

    def _play_func(self):
        '''
        Called while play button is selected
        :return:
        '''
        if self._play_thread:
            if self._last_clicked_direction is not None:
                self._last_clicked_direction()
            else:
                self.move_forward()

            GUI.invoke_after(1000, self._play_func)


    @on_trait_change("Relative_Start_Day")
    def _relative_start_day_changed(self, new_value):
        self.start_day = new_value

    def _start_day_changed ( self, new_time ):
        if isinstance(new_time, int):
            self.current_time = datetools.to_datetime(self._data_times.min()+datetools.Day(new_time))
        elif isinstance(new_time, str):
            self.current_time = datetools.to_datetime(new_time)
        elif isinstance(new_time, datetime.date):
            self.current_time = datetools.to_datetime(new_time)
        else:
            print "Unsupported start day ", new_time
            return


    def _selected_source_changed(self, old_source, new_source):
        #print "Source changed", old_source, new_source

        if old_source is not new_source:

            if new_source is not None:
                self._selected_source_name = self._get_source_name(new_source)
                self._update_selected_event(None)
                self._update_selected_event(self._vis_model.get_num_of_selected_events()-1)
            else:
                self._selected_source_name = None
                self._update_selected_event(None)



    def __selected_source_name_changed(self, old_source, new_source):
        if new_source in self.source_names:
            source_index = self.source_names.index(new_source)
        else:
            source_index = -1
        if self.selected_source != source_index:
            if source_index == -1:
                self.selected_source = None
            else:
                self.selected_source = source_index

    def _current_time_changed(self, old_time, new_time):
        num_of_days = int((datetools.to_datetime(new_time) - self._data_times.min()).days)
        if self.Relative_Start_Day != num_of_days:
            self.Relative_Start_Day = num_of_days
        elif old_time != new_time:
            self.update()


    _old_event_name = -1
    def _update_selected_event(self, event_index):

        if event_index > -1:
            event = self._vis_model.get_selected_event(event_index)
        else:
            event = None

        # if self._old_event_name == event or event is not None and self._old_event_name == event.name:
        #     return # Do nothing

        self._old_event_name = None if event is None else event.name

        if event_index > -1:
            selected_event = self._vis_model.expand_events(event.parent if self.selected_event > -1 and event_index >= self.selected_event else self._vis_model.get_selected_event(event_index))
        else:
            selected_event = self._vis_model.expand_events(None)

        self.selected_event = selected_event

        if event is not None:
            sevents = self._vis_model.get_selected_events_name()

            names = list(sorted([pyisc._get_string_value(sevents,i) for i in range(self._vis_model.get_num_of_selected_events())]))

            if event.name in names:
                self._selected_events_list = names
                self._selected_event_name = [event.name]
        else:
            self._selected_events_list = ['None']
            self._selected_event_name = ['None']

        self.update()

    def __selected_event_name_changed(self, oldvalue, newvalue):
        if self._old_event_name is None or len(self._selected_event_name) == 1 and self._old_event_name != self._selected_event_name[0]:
            if len(oldvalue) != len(newvalue) or len(newvalue) == 1 and oldvalue[0] != newvalue[0]:
                if len(self._selected_event_name) == 1 and self._selected_event_name[0] != 'None':
                    event_index = self._vis_model.get_event_index(self._selected_event_name[0])
                    self._update_selected_event(event_index)
                else:
                    self._update_selected_event(None)

    def _num_of_shown_days_changed(self):
        self.used_cache_size = self._num_of_shown_days_to_int()*self._num_of_sources
        self.update()


    # Used for caching anomaly calculations
    _cache = dict()
    # Used for scaling visualizatuion in the z direction
    _scale_z = Trait(0.1, Range(0.0, 1.0))
    # Used for setting a good default view in 3D
    _last_view = None


    def __init__(self, visualisation_model, decision_threshold, start_day=3, num_of_shown_days="30 days", precompute_cache=False):
        '''

        :param visualisation_model: an instance of EventDataModel
        :param decision_threshold: a float larger or equal to 0.0 that is used for deciding when an anomaly score is significantly anomalous
        :param start_day: an integer >= or an instance of datetime.date or an string, like "2014-10-11" or a tuple, like (2014, 10, 11)
        :param num_of_shown_days: an integer > 1 that specifies the number of days back in time from start_day that will be shown.
        :param precompute_cache: boolean that indates whether all anomaly scores should be computed at once or when asked for.
        :return:
        '''
        assert isinstance(visualisation_model, EventDataModel)
        assert isinstance(start_day, int) or isinstance(start_day, str) or isinstance(start_day, datetime.date) or (isinstance(start_day, tuple) and len(start_day) == 3)
        HasTraits.__init__(self)

        self.used_cache_size = 0 # must be initialized
        self._data = visualisation_model._event_data_object

        self.num_of_shown_days = num_of_shown_days # Updates self.used_cache_size

        self._vis_model = visualisation_model
        self._anomaly_detector = visualisation_model._anomaly_detector
        self.anomaly_detection_threshold = decision_threshold

        dates = visualisation_model._event_data_object.dates_
        self._data_times = array([datetools.to_datetime(d) for d in dates])

        self.source_names = list(unique(visualisation_model._event_data_object.sources_))
        self._data_sources = array([self.source_names.index(source) for source in visualisation_model._event_data_object.sources_])
        self._num_of_sources = len(unique(self.source_names)) # number of sources

        self.barcharts = []
        self.barchart_actors = []
        self.time_text3ds = []
        self.source_text3ds = []
        self.xy_positions = []

        self._high_start_day_number = int((self._data_times.max() - self._data_times.min()).days)

        self.scene.anti_aliasing_frames = 8

        # add traits dynamically
        self.add_trait("Relative_Start_Day", Range(0, self._high_start_day_number))

        self.add_trait("_selected_source_name", Enum(None,[None]+self.source_names))

        self.configure_traits()

        # add the mouse pick handler
        self.picker = self.scene.mayavi_scene.on_mouse_pick(self.vis_picker, 'cell')

        self.picker.tolerance = 0.01

        self.severity_color = [(1,x/100.0, x/100.0) for x in range(70, 30, -40/self._vis_model.num_of_severity_levels_)]

        # This used for a fix to manage a bug in Mayavi library, an invisible default object
        self._obj = self.scene.mlab.points3d(0, 0, 0, opacity=0.0)

        # Cache all anomaly calculations for all data values
        if precompute_cache:
            self.used_cache_size = len(self._data)
            for data_index in xrange(len(self._data)):
                self._populate_cache(data_index)

        self.start_day = start_day

        self.update()


    def _create_barcharts(self, severities, x, y, z):
        '''
        Creates and shows the 3D bars
        :param severities:
        :param x:
        :param y:
        :param z:
        :return:
        '''
        #self.scene.disable_render = True

        x = array(x)
        y = array(y)
        z = array(z)
        severities = array(severities)

        for s in set(severities):
            s_index = (severities == s)
            color = (1.0, 1.0, 1.0) if s == -1 else (0,0,0) if s == -2 else self.severity_color[s]
            x0 = x[s_index]
            y0 = y[s_index]
            z0 = z[s_index]

            barchart = self.scene.mlab.barchart(x0, y0, z0, color=color,  auto_scale=False, reset_zoom=False)
            self.barcharts.append(barchart)
            self.barchart_actors.append(barchart.actor.actors[0])
            self.xy_positions.append((x0,y0,z0))

        for actor in self.barchart_actors:
            actor.scale = array([1.0, 1.0, self._scale_z])

            #self.scene.disable_render = False


    def clear_figure(self):
        '''
        Removes the objects from the scene.
        :return:
        '''
        self.scene.remove_actors(self.barchart_actors)

        # A bug fix, when there are no objects left in the scene it stops working unless you set a default current_object
        # It is an invisibale point outside the 3D bar plot region.
        self.scene.mlab.get_engine().current_object = self._obj

        self.barchart_actors = []
        self.xy_positions = []

    def _trim_cache(self, data_index, used_cache_size):
        '''
        Keeps the cache to the defined size.
        :param data_index:
        :param used_cache_size:
        :return:
        '''
        if len(self._cache) > used_cache_size:
            max_index = max(self._cache.keys())
            min_index = min(self._cache.keys())
            if data_index > max_index:
                del self._cache[min_index]
            elif data_index < min_index:
                del self._cache[max_index]
            else:  # Remove the one farest away
                median_index = median(self._cache.keys())
                triple_indexes = array([min_index, median_index, max_index])
                diffs = abs(data_index - triple_indexes)
                diff_max_index = diffs.argmax()

                del self._cache[triple_indexes[diff_max_index]]

    def update(self):
        '''
        Plots the 3D bars and axis.
        :return:
        '''
        is_first_update = False

        if self._last_view is None:
            self._last_view = (38, 8, 205, array([  8,  17.5,  49.25]))
            self.scene.mlab.view(*self._last_view)
            is_first_update = True
        else:
            self._last_view = self.scene.mlab.view()

        self.scene.disable_render = True
        self.clear_figure()
        #print "Day: %s" % time.ctime(self.current_time)


        max_z = 0

        time_index = ((self._data_times <= self.current_time) &
                      (self._data_times >= (datetools.to_datetime(self.current_time) - self._num_of_shown_days_to_timedelta())))

        if self.selected_source is None: # Plot all sources
            x = []
            y = []
            z = []
            severities = []


            for source in range(self._num_of_sources):
                for data_index in array(range(len(self._data)))[time_index][self._data_sources[time_index] == source]:
                    if self.used_cache_size > 0 and self._cache.has_key(data_index):
                        devsptr, sevs, expectptr, min2, max2, count = self._cache[data_index]
                    else:
                        devs, sevs, expect, min2, max2= self._vis_model.calc_one(data_index)

                        devsptr = pyisc._to_cpp_array(devs)
                        expectptr = pyisc._to_cpp_array(expect)

                        count = None

                    if count is None:
                        self._trim_cache(data_index, self.used_cache_size)
                        vec = self._data._get_intfloat(data_index)
                        count = sum([pyisc._get_intfloat_value(vec, self._vis_model.get_event_hierarchy().get_index_value(l)) for l in range(self._vis_model.num_of_severity_levels_) if self._vis_model.get_event_hierarchy().get_index_value(l) != -1 ])
                        self._cache[data_index] = (devsptr, sevs, expectptr, min2, max2, count)


                    ztime = self._num_of_shown_days_to_int()-(self.current_time-self._data_times[data_index]).days

                    x.append(source)
                    y.append(ztime)

                    z.append(count)


                    sev_max = argmax(sevs)
                    sev = (-1 if sevs[sev_max] < self.anomaly_detection_threshold else sev_max)

                    severities.append(sev)
            self._create_barcharts(severities, x, y, z)

            max_z = max([max_z]+z)
        else: # Plot for selected source
            source_index = self._data_sources[time_index] == self.selected_source

            data_indexes = array(range(len(self._data)))[time_index][source_index]
            x = []
            y = []
            z = []
            severities = []

            # Plot selected events
            for data_index in data_indexes:
                if self.used_cache_size > 0 and self._cache.has_key(data_index):
                    devsptr, sevs, expectptr, min2, max2, _ = self._cache[data_index]
                else:
                    devs, sevs,expect, min2, max2 = self._vis_model.calc_one(data_index)
                    devsptr = pyisc._to_cpp_array(devs)
                    expectptr = pyisc._to_cpp_array(expect)


                    self._trim_cache(data_index, self.used_cache_size)

                    self._cache[data_index] = (devsptr, sevs, expectptr, min2, max2, None)

                ztime = self._num_of_shown_days_to_int()-(self.current_time-self._data_times[data_index]).days


                if self._vis_model.get_num_of_selected_events() > 0:
                    for element in range(self._vis_model.get_num_of_selected_events()):
                        x.append(element)
                        y.append(ztime)

                        (dev, sev, count, mexp, maxind) = self._vis_model.summarize_event_children(self._vis_model.get_selected_event(element), devsptr, expectptr, self._data._get_intfloat(data_index), 1 if element >= self.selected_event else 0)
                        z.append(count)


                        if dev < self.anomaly_detection_threshold:
                            severities.append(-1)
                        else:
                            severities.append(sev)

            self._create_barcharts(severities, x, y, z)
            max_z = max([max_z]+z)

        self.scene.disable_render = True

        curr_t = self.current_time
        time_strs = [str(t)for t in date_range(curr_t-self._num_of_shown_days_to_timedelta(), curr_t)]
        time_max_len = min([len(t) for t in time_strs])

        max_x = (self._num_of_sources if self.selected_source is None else  self._vis_model.get_num_of_selected_events())
        max_y = self._num_of_shown_days_to_int()

        if len(self.time_text3ds) != len(time_strs):
            self.scene.remove_actors([t.actor.actors[0] for t in self.time_text3ds])
            self.time_text3ds = []

            for slot in range(len(time_strs)):
                name = time_strs[slot]
                pos = (max_x+time_max_len/2-1, slot, 0)
                self.time_text3ds.append(self.scene.mlab.text3d(*pos, text=name, scale=0.5, color=(0, 0, 0), orient_to_camera=False, orientation=(180, 180, 0)))
        else:
            for slot in range(len(time_strs)):
                name = time_strs[slot]
                pos = (max_x+time_max_len/2-1, slot, 0)

                self.time_text3ds[slot].position = pos
                self.time_text3ds[slot].text=name

        if self.selected_source is None:
            source_strs = [self._get_source_name(source) for source in range(self._num_of_sources)]
            num_of_sources = self._num_of_sources
        else:
            source_strs = [self._get_event_name(element) for element in range(self._vis_model.get_num_of_selected_events())]
            num_of_sources = self._vis_model.get_num_of_selected_events()

        if len(self.source_text3ds) != num_of_sources or self.selected_source is None:
            self.scene.remove_actors([t.actor.actors[0] for t in self.source_text3ds])
            self.source_text3ds = []
            for source in range(num_of_sources):
                name = source_strs[source]
                if self.selected_source is None:
                    self.source_text3ds.append(self.scene.mlab.text3d(source, max_y + 0.5, 0, name, scale=0.6, color=(0, 0, 0), orient_to_camera=False, orientation=(0, 0, 90)))
                else:
                    self.source_text3ds.append(self.scene.mlab.text3d(source, max_y + 0.5, 0, name, color=(0, 0, 0) if source < self.selected_event else (0, 0, 0.8) if source > self.selected_event else (0, 0, 1), scale=0.5, orient_to_camera=False, orientation=(0, 0, 90)))
        else:
            for source in range(num_of_sources):
                name = source_strs[source]
                self.source_text3ds[source].text = name
                self.source_text3ds[source].position = (source, max_y + 0.5, 0)

        if is_first_update:
            self.scene.reset_zoom()

        self.scene.disable_render = False

        return

    last_picker = None
    def vis_picker(self,picker):
        '''
        Called when the user clicks in the scene in order to find the object that was selected.
        :param picker:
        :return:
        '''
        self.last_picker = picker
        _source = None


        if picker.actor is not None:

            if picker.actor in self.barchart_actors:
                actor_index = self.barchart_actors.index(picker.actor)
                _sources, _time_slots, _ = self.xy_positions[actor_index]

                _source = _sources[picker.point_id/24]
                _time_slot = _time_slots[picker.point_id/24]
            else:
                actors = [t.actor.actors[0] for t in self.source_text3ds]

                if picker.actor in actors:
                    actor_index = actors.index(picker.actor)
                    _source = actor_index

            if _source is not None:
                if self.selected_source is None:
                    if _source >= 0 and _source < self._num_of_sources:
                        self.selected_source = _source
                elif _source >= 0 and _source < self._vis_model.get_num_of_selected_events():
                    self._update_selected_event(_source)


    def _num_of_shown_days_to_timedelta(self):
        return datetools.to_offset(str(self.num_of_shown_days).split(' ')[0]+"d")

    def _num_of_shown_days_to_int(self):
        return int(str(self.num_of_shown_days).split(' ')[0])


    def _get_source_name(self,source):
        return self.source_names[source]

    def _get_event_name(self,element):
        return self._vis_model.get_selected_event(element).name


    def _populate_cache(self, data_index):
        devs, sevs, expect, min2, max2= self._vis_model.calc_one(data_index)

        devsptr = pyisc._to_cpp_array(devs)
        expectptr = pyisc._to_cpp_array(expect)

        vec = self._data._get_intfloat(data_index)
        count = sum([pyisc._get_intfloat_value(vec, self._vis_model.get_event_hierarchy().get_index_value(l)) for l in xrange(self._vis_model.num_of_severity_levels_) if self._vis_model.get_event_hierarchy().get_index_value(l) != -1 ])

        self._cache[data_index] = (devsptr, sevs, expectptr, min2, max2, count)


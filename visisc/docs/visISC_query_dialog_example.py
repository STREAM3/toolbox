
# coding: utf-8

# In[15]:

import visisc;
import numpy as np
import datetime
from scipy.stats import poisson

get_ipython().magic(u'matplotlib wx')
get_ipython().magic(u'gui wx')


# In[16]:

n_sources = 10
n_source_classes = 10
n_events = 100
num_of_normal_days = 200
num_of_anomalous_days = 10
data = None
days_list = [num_of_normal_days, num_of_anomalous_days]
dates = []
for state in [0,1]: # normal, anomalous data
    num_of_days = days_list[state]
    for k in range(n_source_classes):
        for i in range(n_sources):
            data0 = None
            for j in range(n_events):
                if state == 0:# Normal
                    po_dist = poisson(int((10+2*(n_source_classes-k))*(float(j)/n_events/2+0.75))) # from 0.75 to 1.25
                else: # anomalous
                    po_dist = poisson(int((20+2*(n_source_classes-k))*(float(j)/n_events+0.5))) # from 0.5 to 1.5

                tmp = po_dist.rvs(num_of_days)
                if data0 is None:
                    data0 = tmp
                else:
                    data0 = np.c_[data0,tmp]

            tmp =  np.c_[
                        [k*n_sources+i] * (num_of_days), # Sources
                        [k] * (num_of_days), # Source classes
                        [ # Timestamp
                            datetime.date(2015,02,24) + datetime.timedelta(d) 
                            for d in np.array(range(num_of_days)) + (0 if state==0 else num_of_normal_days)
                        ], 
                        [1] * (num_of_days), # Measurement period
                        data0, # Event frequency counts

                        ]

            if data is None:
                data = tmp
            else:
                data = np.r_[
                    tmp,
                    data
                ]

# Column index into the data
source_column = 0
class_column = 1
date_column = 2
period_column = 3
first_event_column = 4
last_event_column = first_event_column + n_events


# In[17]:

event_names = ["event_%i"%i for i in range(n_events)]

def event_path(x): # Returns a list of strings with 3 elements
    return ["Type_%i"%(x/N) for N in [50, 10]]+[event_names[x-first_event_column]]

def severity_level(x): # returns 3 different severity levels: 0, 1, 2
    return x-(x/3)*3

class MySelectionQuery(visisc.EventSelectionQuery):
    def __init__(self):
        self.list_of_source_ids = [i for i in range(n_sources*n_source_classes)]
        self.list_of_source_classes = [(i, "class_%i"%i) for i in range(n_source_classes)]
        self.list_of_event_names = event_names
        self.list_of_event_severity_levels = [(i, "Level %i"%i) for i in range(3)]
        self.period_start_date = data.T[date_column].min()
        self.period_end_date = data.T[date_column].max()
    
    def execute_query(self):
        query = self
        query.selected_list_of_source_ids = query.list_of_source_ids

        data_query = np.array(
            [
            data[i] for i in range(len(data)) if 
                data[i][source_column] in query.selected_list_of_source_ids and
                data[i][class_column] in query.selected_list_of_source_classes and
                data[i][date_column] >= query.period_start_date and
                data[i][date_column] <= query.period_end_date
            ]
        )

        event_columns = [first_event_column+event_names.index(e) for e in query.selected_list_of_event_names
             if severity_level(first_event_column+event_names.index(e)) in query.selected_list_of_event_severity_levels]

        model = visisc.EventDataModel.hierarchical_model(
            event_columns=event_columns,
            get_event_path = event_path,
            get_severity_level = severity_level,
            num_of_severity_levels=3
        )

        data_object = model.data_object(
            data_query,
            source_column = source_column,
            class_column = class_column,
            period_column=period_column,
            date_column=date_column
        )

        anomaly_detector = model.fit_anomaly_detector(data_object,poisson_onesided=True)

        vis = visisc.EventVisualization(model, 13.8,
                                        start_day=data_object.dates_.max(),
                                        precompute_cache=True)

query = MySelectionQuery()

dialog = visisc.EventSelectionDialog(
    query,
    source_class_label="Select Machine Types",
    severity_level_label="Select Event Severity Types"
)                                     


# In[23]:

dialog.configure_traits()


# In[ ]:




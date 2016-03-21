
# coding: utf-8

# # visISC Example: Visualizing Anomalous Frequency Data with Classes 
# In this example, we will show what to do when you are analysing frequency counts of data and you want to identify which part of the data is the reason for a deviation.   

# In[2]:

import pyisc;
import visisc;
import numpy as np
import datetime
from scipy.stats import poisson, norm, multivariate_normal
get_ipython().magic(u'matplotlib wx')
from pylab import plot, figure


# <b>First, we create a data set with a set of classes and a set of Poisson distributed frequency counts and then train an anomaly detector:</b>

# In[3]:

n_classes = 10
n_frequencies = 20
num_of_normal_days = 200
num_of_anomalous_days = 10
data = None
days_list = [num_of_normal_days, num_of_anomalous_days]
dates = []
for state in [0,1]:
    num_of_days = days_list[state]
    for i in range(n_classes):
        data0 = None
        for j in range(n_frequencies):
            if state == 0:
                po_dist = poisson(int((10+2*(n_classes-i))*(float(j)/n_frequencies/2+0.75))) # from 0.75 to 1.25
            else:
                po_dist = poisson(int((20+2*(n_classes-i))*(float(j)/n_frequencies+0.5))) # from 0.5 to 1.5

            tmp = po_dist.rvs(num_of_days)
            if data0 is None:
                data0 = tmp
            else:
                data0 = np.c_[data0,tmp]

        tmp =  np.c_[
                    [1] * (num_of_days),
                    data0,
                    [
                        datetime.date(2015,02,24) + datetime.timedelta(d) 
                        for d in np.array(range(num_of_days)) + (0 if state==0 else num_of_normal_days)
                    ],
                    ["Source %i"%i] * (num_of_days)
                    
                    ]
        
        if data is None:
            data = tmp
        else:
            data = np.r_[
                tmp,
                data
            ]

# Column index into the data
first_frequency_column = 1
period_column = 0
date_column = data.shape[-1]-2
source_column = data.shape[-1]-1


# <b>Next, we create a event data model that describes how our events are connected. In this case, we assume only a flat structure with events</b>

# First we create a flat model with a root element where all columns in the data is subelements

# In[6]:

model = visisc.EventDataModel.flat_model(
    event_columns=range(first_frequency_column, date_column)
)


# Second we transform numpy array to a pyisc data object with a class column and a period column.
# The last created data object is also kept in the model.

# In[7]:

data_object = model.data_object(    
    data,
    source_column = source_column,
    class_column = source_column,
    period_column = period_column,
    date_column =  date_column
)

# Then, we create an anomaly detector and fit a onesided poisson distribution for each event column.
# The last created and fitted anomaly detector is also kept in the model

# In[8]:

anomaly_detector = model.fit_anomaly_detector(data_object, poisson_onesided=True)


# <b>Finally, we can viualize the event frequency data using the Visualization class. However, due to a bug in the underlying 3D egnine, we have to run the notebook as a script:</b>

vis = visisc.EventVisualization(model, 13.8,start_day=209)




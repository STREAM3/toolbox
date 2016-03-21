// Author: Tomas Olsson (tol@sics.se)
// License: BSD 3 clause

 %module visisc


 %{
 #define SWIG_FILE_WITH_INIT

 /* Includes the header in the wrapper code */

 #include "src/EventDataModel.hh"
 %}

 %include <typemaps.i>

 %apply int &OUTPUT {int& maxsev, int& maxcount, int& maxind}
 %apply double &OUTPUT {double& maxdev, double& maxexp}
 %apply int &OUTPUT {int& selind}
 %apply pyisc::_EventHierEle** &OUTPUT {pyisc::_EventHierEle**& eles}

 %include "src/EventDataModel.hh"


 %pythoncode %{
from _visisc_modules.EventHierarchy import *
from _visisc_modules.EventDataObject import EventDataObject
from _visisc_modules.EventDataModel import EventDataModel
from _visisc_modules.EventVisualization import EventVisualization
from _visisc_modules.EventSelectionQuery import EventSelectionQuery
from _visisc_modules.EventSelectionDialog import EventSelectionDialog

 %}





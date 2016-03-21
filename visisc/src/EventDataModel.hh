/*
 * CranesDemo.hh
 *
 * Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
 *
 * Main authors: Anders Holst <aho@sics.se>
 * 				 Tomas Olsson <tol@sics.se>
 *
 * License: BSD 3 clause
 *
 */

#ifndef EventDataModel_HH_
#define EventDataModel_HH_

#include <intfloat.hh>
#include <_Format.hh>
#include <_DataObject.hh>
#include <isc_micromodel.hh>
#include <_AnomalyDetector.hh>
#include <string.h>

namespace visisc {


extern int num_of_severity_levels;

extern void set_global_num_of_severity_levels(int num_sev_levels);
extern int get_global_num_of_severity_levels();


struct _EventHierEle {

	_EventHierEle(const char* event_name, int name_len) {
		char* tmpname = strncpy(new char[name_len+1], event_name, name_len);
		tmpname[name_len] = 0;
		name = tmpname;
		index = new int[get_global_num_of_severity_levels()];
		index_component = new int[get_global_num_of_severity_levels()];
		for (int i=0; i<get_global_num_of_severity_levels(); i++) index[i] = -1; parent = sibling = child = 0;
	};
	~_EventHierEle() { delete [] name; delete [] index; delete [] index_component;};
	int* index;
	char* name;
	_EventHierEle* parent;
	_EventHierEle* sibling;
	_EventHierEle* child;
	int* index_component;

	int get_index_value(int ind) {
		return index[ind];
	}

	int get_index_component(int ind) {
		return index_component[ind];
	}

	int set_index_component(int ind, int component) {
		index_component[ind] = component;
	}

	_EventHierEle* event_hierarchy_next();

};

// inline methods must be in header otherwise the compiler will not find it when runing python setup.py
inline visisc::_EventHierEle* visisc::_EventHierEle::event_hierarchy_next()
{
	_EventHierEle* ele = this;
	if (ele->child)
		return ele->child;
	while (!ele->sibling && ele->parent)
		ele = ele->parent;
	return ele->sibling;
}


class _EventDataModel {
public:


	_EventDataModel(_EventHierEle* event_hierarchy, int event_hierarchy_size, int first_event_column);
	virtual ~_EventDataModel();

	virtual _EventHierEle* get_event_hierarchy();
	virtual int get_event_hierarchy_size();

	virtual _EventHierEle* get_selected_event(int message_index);
	virtual int expand_events(_EventHierEle* ele0);
	virtual void summarize_event_children(_EventHierEle* ele, double* devs, double* exps, intfloat* vec, double& maxdev, int& maxsev, int& maxcount, double& maxexp, int& maxind, int nosum);

	virtual _EventHierEle** get_selected_events() {return _selected_events;};

	virtual char** get_selected_events_name() {
		char** names = new char*[_num_of_selected_events];
		for(int i=0; i < _num_of_selected_events; i++) {
			names[i] = _selected_events[i]->name;
		}
		return names;
	};

	virtual int get_event_index(char* name) {
		for(int i=0; i < get_event_hierarchy_size(); i++) {
			if(strcmp(get_selected_event(i)->name, name) == 0) {
				return i;
			}
		}

		return -1;
	}

	virtual int get_num_of_selected_events() {return _num_of_selected_events;};

	int _offset;


protected:
	_EventHierEle* _event_hierarchy = 0;
	int _event_hierarchy_size = 0;
	_EventHierEle** _selected_events;
	int _num_of_selected_events;
};

}  // namespace visisc




#endif /* EventDataModel_HH_ */

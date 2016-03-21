/*
 * Copyright (C) 2014, 2015, 2016 SICS Swedish ICT AB
 *
 * Main authors: Anders Holst <aho@sics.se>
 * 				 Tomas Olsson <tol@sics.se>
 *
 * License: BSD 3 clause
 */

#include "EventDataModel.hh"
#include <isc_micromodel_gaussian.hh>
#include <isc_micromodel_poissongamma.hh>
#include <IscPoissonMicroModelOneside.hh>

int visisc::num_of_severity_levels = 5;
void visisc::set_global_num_of_severity_levels(int num_sev_levels) {num_of_severity_levels = num_sev_levels;};
int visisc::get_global_num_of_severity_levels(){return num_of_severity_levels;};


#define FORMESSHIER(ele) for(pyisc::EventHierEle* ele = _event_hierarchy; ele; ele=event_hierarchy_next(ele))



/*void pyisc::_VisualizationEventDataModel::summarize_event_anomalies(double* devs, double* sevs)
{
	pyisc::_EventHierEle* ele = _event_hierarchy;
	while (ele) {
		for (int i=0; i< get_global_num_of_severity_levels(); i++)
			if (ele->index[i] != -1)
				if (devs[ele->index[i]] > sevs[i])
					sevs[i] = devs[ele->index[i]];
		ele = ele->event_hierarchy_next();
	}
}*/

// Vi har klickat en unit - sel_target
//   vi ska anropa calc_one för varje dag i fönstret
// Vi har kanske klickat ett meddelande - sel_event
//   vi ska hitta en lista av hierarki-noder att visa,
//   och summera var och en av dem, (utom sel_event som visas direkt)

void visisc::_EventDataModel::summarize_event_children(visisc::_EventHierEle* ele, double* devs, double* exps, intfloat* vec, double& maxdev, int& maxsev, int& maxcount, double& maxexp, int& maxind, int nosum)
{
	visisc::_EventHierEle* end;
	maxcount = 0;
	maxdev = 0.0;
	maxexp = 0.0;
	maxsev = -1;
	maxind = -1;
	if (nosum) {
		for (int i=0; i<get_global_num_of_severity_levels(); i++) {
			if (ele->index[i] == -1) continue;
			maxcount += (int) vec[ele->index[i]+_offset].f;
			maxexp += exps[ele->index_component[i]];
			if (devs[ele->index_component[i]] > maxdev)
				maxsev = i, maxind = ele->index_component[i], maxdev = devs[maxind];
		}
	} else {
		for (int i=0; i<get_global_num_of_severity_levels(); i++) {
			if (ele->index[i] == -1) continue;
			maxcount += (int) vec[ele->index[i]+_offset].f;
			maxexp += exps[ele->index_component[i]];
		}
		for (end=ele; !end->sibling && end->parent; end=end->parent);
		end = end->sibling;
		while (ele != end) {
			for (int i=0; i<get_global_num_of_severity_levels(); i++)
				if (ele->index[i] != -1)
					if (devs[ele->index_component[i]] > maxdev)
						maxsev = i, maxind = ele->index_component[i], maxdev = devs[maxind];
			ele = ele->event_hierarchy_next();
		}
	}
}


visisc::_EventHierEle* visisc::_EventDataModel::get_selected_event(int event_index) {
	_EventHierEle* ele0;
	if(event_index > -1) {
		ele0 = _selected_events[event_index];
	} else {
		ele0 = 0;
	}

	return ele0;
}

int visisc::_EventDataModel::expand_events(_EventHierEle* ele0)
{
	static visisc::_EventHierEle** elements = 0;
	int k, num = 0, selind;
	_EventHierEle* ele;

	if (!elements)
		elements = new visisc::_EventHierEle*[_event_hierarchy_size];
	if (!ele0) {
		// översta noden och nivån närmast efter
		for (ele=_event_hierarchy->child; ele; ele=ele->sibling)
			elements[num++] = ele;
		selind = num;
		elements[num++] = _event_hierarchy;
	} else {
		if (!ele0->child && ele0->parent) ele0 = ele0->parent;
		// Sen de direkta barnen
		for (ele=ele0->child; ele; ele=ele->sibling)
			elements[num++] = ele;
		// Sen den sjålv
		selind = num;
		elements[num++] = ele0;
		// Först tidigare föräldrar
		//    for (k=0, ele=ele0->parent; ele ; k++, ele=ele->parent);
		//    num += k;
		for (k=0, ele=ele0->parent; ele ; k++, ele=ele->parent)
			elements[num++] = ele;
		// Först tidigare syskon - NEJ
		//    for (ele=(ele0->parent ? ele0->parent->child : event_hierarchy); ele && ele != ele0; ele=ele->sibling)
		//      elements[num++] = ele;
		// Sist senare syskon - NEJ
		//    for (ele=ele0->sibling; ele; ele=ele->sibling)
		//      elements[num++] = ele;
	}
	_selected_events = elements;
	_num_of_selected_events = num;
	return selind;
}

/*  -------------------------------------------------- */



/*static void func_info(int n, int col)
{
  const char *name;

  name = global_edata->format()->nth(aunit)->represent(n);
  printf("Some info on %s ...\n", name);


}*/

/*  -------------------------------------------------- */


/*int pyisc::_VisualizationEventDataModel::calc_one(int time, int target, DataObject *d,
		double *devs, double *vec, AnomalyDetector *isc,
		int size_of_data, int time_index, int target_index, double *expect, double *min, double *max, int start_index)
{
	//printf("%i %i %i %i %i %i\n", time, target, time_index, target_index, (int) ((*d)[size_of_data-1][time_index].i) ,(int) (*d)[size_of_data-1][target_index].i);
	if(start_index == -1) {
		start_index = 0;
	}
	int curi = start_index;
	double *expect2;
	intfloat *min2, *max2;
	//  double ano_max;
	double dum3;
	int dum1, dum2;
	int i1;

	for (int j=0; j < get_global_num_of_severity_levels(); j++)
		vec[j] = 0.0;

	//  for (int i2 = 0; i2 < np; i2++)
	//    devs[i2] = 0.0;

	int ano = 0;
	for (i1 = curi; i1 < size_of_data; i1++) {
		if ((int) ((*d)[i1][time_index].i) != time || (*d)[i1][target_index].i != target) {
			if ((int) ((*d)[i1][time_index].i) > time) {
				break;
			}
			continue;
		}

		ano = 1;
		break;
	}

	if (ano) {
		expect2 = new double[d->length()];
		//    min2 = new intfloat[d->length()];
		//    max2 = new intfloat[d->length()];
		min2 = max2 = 0;
		// Testning
		isc->CalcAnomalyDetails((*d)[i1], dum3, dum1, dum2, devs,
				0, (min ? min2 : 0), (max ? max2 : 0), (expect ? expect2 : 0), 0);

		summarize_event_anomalies(devs, vec);
		if (expect)
			for (int i = _offset; i < d->length(); i++) {
				expect[i-_offset] = expect2[i];
			}
		delete [] expect2;
		//    delete [] min2;
		//    delete [] max2;

		return i1;
	} else
		return -1;
}*/


visisc::_EventDataModel::_EventDataModel(_EventHierEle* event_hierarchy, int event_hierarchy_size, int first_event_count_column) {
	visisc::_EventDataModel::_selected_events = 0;
	_num_of_selected_events = 0;
	_event_hierarchy = event_hierarchy;
	_event_hierarchy_size = event_hierarchy_size;
	_offset = first_event_count_column;
	if(DEBUG)
		printf("EventDataModel created\n");

}

visisc::_EventDataModel::~_EventDataModel() {
	if(DEBUG)
		printf("EventDataModel deconstructed\n");
}




visisc::_EventHierEle* visisc::_EventDataModel::get_event_hierarchy() {
	return _event_hierarchy;
}

int visisc::_EventDataModel::get_event_hierarchy_size() {
	return _event_hierarchy_size;
}


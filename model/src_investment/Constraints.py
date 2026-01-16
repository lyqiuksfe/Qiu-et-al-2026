# -*- coding: utf-8 -*-
import numpy as np
import pyoptinterface as poi
from pyoptinterface import gurobi
import os
import pandas as pd

def inv_const_num_operational_generators(Model, DV, data, Setting):      
    max_gen_per_node = Setting['max_generators_per_node']
    for g in range(data.num_generators_vRE):
        vRE_type=data.Generators_vRE[g].Type
        for n in range(data.num_nodes):
            for u in range(max_gen_per_node):  
                if Setting['VRE_expansion_allowed']:
                    Model.add_linear_constraint(DV.gen_operational_vRE[g,n,u]-data.Nodes[n].vRE_existing[vRE_type][u]-DV.gen_establish_vRE[g,n,u], poi.Eq, 0)
                else:
                    Model.add_linear_constraint(DV.gen_operational_vRE[g,n,u]-data.Nodes[n].vRE_existing[vRE_type][u], poi.Eq, 0)                

    for g in range(data.num_generators_thermal):
        thermal_type=data.Generators_thermal[g].Type
        for n in range(data.num_nodes):
            if Setting['thermal_expansion_allowed']:
                Model.add_linear_constraint(DV.gen_operational_thermal[g,n]-data.Nodes[n].thermal_existing[thermal_type]-DV.gen_establish_thermal[g,n], poi.Eq, 0)
            else:
                Model.add_linear_constraint(DV.gen_operational_thermal[g,n]-data.Nodes[n].thermal_existing[thermal_type], poi.Eq, 0)

    for l in range(data.num_lines):
        if Setting['line_expansion_allowed']:
            Model.add_linear_constraint(DV.line_operational[l]-data.Lines[l].existing_cap-DV.line_establish[l], poi.Eq, 0)
        else:
            Model.add_linear_constraint(DV.line_operational[l]-data.Lines[l].existing_cap, poi.Eq, 0)        

    for s in range(data.num_storages):
        storage_type=data.Storages[s].Type
        for n in range(data.num_nodes):
            if Setting['storage_expansion_allowed']:
                Model.add_linear_constraint(DV.storage_capacity_operational[s,n]-data.Nodes[n].storage_capacity_existing-DV.storage_capacity_establish[s,n], poi.Eq, 0)
            else:
                Model.add_linear_constraint(DV.storage_capacity_operational[s,n]-data.Nodes[n].storage_capacity_existing, poi.Eq, 0)


def inv_const_land_availability_for_renewables(Model, DV, data, Setting):
    if Setting['VRE_expansion_allowed']:
        max_gen_per_node = Setting['max_generators_per_node']
        for g in range(data.num_generators_vRE):
            vRE_type=data.Generators_vRE[g].Type
            for n in range(data.num_nodes):
                for u in range(max_gen_per_node):
                    Model.add_linear_constraint(DV.gen_operational_vRE[g,n,u], 
                        poi.Leq, data.Nodes[n].area[vRE_type][u]* data.Generators_vRE[g].power2area_density)            



def oper_const_production_limits(Model, DV, data, Setting):         
    # production limits for each generator unit at each node at each time period
    # Thermal generation limits (1 per node, no u indexing needed)
    for g in range(data.num_generators_thermal):
        for n in range(data.num_nodes):
            for t in range(data.num_rep_hours):
                Model.add_linear_constraint(DV.generation_thermal[g,n,t]-DV.gen_operational_thermal[g,n], poi.Leq, 0)
    # vRE generation limits
    max_gen_per_node = Setting['max_generators_per_node']
    for g in range(data.num_generators_vRE):
        for n in range(data.num_nodes):
            for t in range(data.num_rep_hours):
                for u in range(max_gen_per_node):
                    Model.add_linear_constraint(DV.generation_vRE[g,n,u,t]-data.Nodes[n].cf[data.Generators_vRE[g].Type][data.rep_hours[t],u]*DV.gen_operational_vRE[g,n,u], poi.Leq, 0)


def oper_const_ramping(Model, DV, data, Setting):    
    # Only thermal generators have ramping constraints (1 per node, no u indexing needed)
    for g in range(data.num_generators_thermal):
        for n in range(data.num_nodes):
            for t in range(1, data.num_rep_hours):
                Model.add_linear_constraint(DV.generation_thermal[g,n,t]-DV.generation_thermal[g,n,t-1]-data.Generators_thermal[g].ramp_rate*DV.gen_operational_thermal[g,n], poi.Leq, 0)
                Model.add_linear_constraint(-DV.generation_thermal[g,n,t]+DV.generation_thermal[g,n,t-1]-data.Generators_thermal[g].ramp_rate*DV.gen_operational_thermal[g,n], poi.Leq, 0)

def oper_const_balance_equation(Model, DV, Con, data, Setting):
    Con.load_balance = np.empty((data.num_nodes, data.num_rep_hours), dtype=object) 
    for n in range(data.num_nodes):
        for t in range(data.num_rep_hours):
            Con.load_balance[n,t] = Model.add_linear_constraint(
                poi.quicksum(DV.generation_vRE[g,n,u,t] for g in range(data.num_generators_vRE) for u in range(Setting['max_generators_per_node'])) +
                poi.quicksum(DV.generation_thermal[g,n,t] for g in range(data.num_generators_thermal)) -
                poi.quicksum(data.Nodes[n].arc_signs[l]*DV.flow[data.Nodes[n].arcs[l],t] for l in range(len(data.Nodes[n].arcs))) +       
                poi.quicksum(DV.storage_discharge[s,n,t] for s in range(data.num_storages)) - 
                poi.quicksum(DV.storage_charge[s,n,t] for s in range(data.num_storages)) +                                                                              
                DV.load_shedding[n,t],   
                poi.Eq, data.Nodes[n].demand[data.rep_hours[t]]
            )

def oper_const_flow_limits(Model, DV, Con, data, Setting):
    for l in range(data.num_lines):
        for t in range(data.num_rep_hours):
            Model.add_linear_constraint(DV.flow[l,t]-DV.line_operational[l], poi.Leq, 0)
            Model.add_linear_constraint(-DV.flow[l,t]-DV.line_operational[l], poi.Leq, 0)


def oper_const_RPS(Model, DV, data, Setting):
    # renewable portfolio standard
    if Setting['RPS'] > 0:
        Model.add_linear_constraint(
        poi.quicksum(data.rep_hours_weights[t]*DV.generation_thermal[g,n,t] for g in range(data.num_generators_thermal) for n in range(data.num_nodes) for t in range(data.num_rep_hours)) -
        (1-Setting['RPS']) * poi.quicksum(data.rep_hours_weights[t]*(data.Nodes[n].demand[data.rep_hours[t]] - DV.load_shedding[n,t]) for n in range(data.num_nodes) for t in range(data.num_rep_hours)),
        poi.Leq, 0
        )

def oper_const_storage(Model, DV, data, Setting):
    # storage constraints
    for s in range(data.num_storages):
        for n in range(data.num_nodes):
            for t in range(data.num_rep_hours):
                if t>0:
                    Model.add_linear_constraint(DV.SOC[s,n,t]-(1-data.Storages[s].self_discharge)*DV.SOC[s,n,t-1] -
                    data.Storages[s].charging_eff*DV.storage_charge[s,n,t] +
                    DV.storage_discharge[s,n,t]/data.Storages[s].discharging_eff,
                    poi.Eq, 0)
                else:
                    Model.add_linear_constraint(DV.SOC[s,n,t]- DV.storage_capacity_operational[s,n]*data.Storages[s].duration_range/2, poi.Eq, 0)
                Model.add_linear_constraint(DV.storage_capacity_operational[s,n]-DV.storage_charge[s,n,t], poi.Geq, 0)
                Model.add_linear_constraint(DV.storage_capacity_operational[s,n]-DV.storage_discharge[s,n,t], poi.Geq, 0)
                Model.add_linear_constraint(DV.storage_capacity_operational[s,n]*data.Storages[s].duration_range-DV.SOC[s,n,t], poi.Geq, 0)


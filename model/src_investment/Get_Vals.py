import numpy as np
import time 
import pyoptinterface as poi
from pyoptinterface import gurobi

def get_variable_values(Model, DV, DV_values, data, Setting):
    # retrieve the values of the decision variables after solving the model
    max_gen_per_node = Setting.get('max_generators_per_node', 1)

    DV_values.gen_operational_vRE = np.array([[[Model.get_value(DV.gen_operational_vRE[g, n, u]) for u in range(max_gen_per_node)] for n in range(data.num_nodes)] for g in range(data.num_generators_vRE)])
    if Setting['VRE_expansion_allowed']:
        DV_values.gen_establish_vRE = np.array([[[Model.get_value(DV.gen_establish_vRE[g, n, u]) for u in range(max_gen_per_node)] for n in range(data.num_nodes)] for g in range(data.num_generators_vRE)])

    DV_values.gen_operational_thermal = np.array([[Model.get_value(DV.gen_operational_thermal[g,n]) for n in range(data.num_nodes)] for g in range(data.num_generators_thermal)])
    if Setting['thermal_expansion_allowed']:
        DV_values.gen_establish_thermal = np.array([[Model.get_value(DV.gen_establish_thermal[g,n]) for n in range(data.num_nodes)] for g in range(data.num_generators_thermal)])
    
    DV_values.line_operational = np.array([Model.get_value(DV.line_operational[l]) for l in range(data.num_lines)])
    if Setting['line_expansion_allowed']:
        DV_values.line_establish = np.array([Model.get_value(DV.line_establish[l]) for l in range(data.num_lines)])
    
    DV_values.storage_capacity_operational = np.array([[Model.get_value(DV.storage_capacity_operational[s, n]) for n in range(data.num_nodes)] for s in range(data.num_storages)])
    if Setting['storage_expansion_allowed']:
        DV_values.storage_capacity_establish = np.array([[Model.get_value(DV.storage_capacity_establish[s, n]) for n in range(data.num_nodes)] for s in range(data.num_storages)])


    DV_values.generation_vRE = np.array([[[[Model.get_value(DV.generation_vRE[g, n, u, t]) for t in range(data.num_rep_hours)] for u in range(max_gen_per_node)] for n in range(data.num_nodes)] for g in range(data.num_generators_vRE)])
    DV_values.generation_thermal = np.array([[[Model.get_value(DV.generation_thermal[g, n, t]) for t in range(data.num_rep_hours)] for n in range(data.num_nodes)] for g in range(data.num_generators_thermal)])
    DV_values.load_shedding = np.array([[Model.get_value(DV.load_shedding[n, t]) for t in range(data.num_rep_hours)] for n in range(data.num_nodes)])
    DV_values.storage_charge = np.array([[[Model.get_value(DV.storage_charge[s, n, t]) for t in range(data.num_rep_hours)] for n in range(data.num_nodes)] for s in range(data.num_storages)])
    DV_values.storage_discharge = np.array([[[Model.get_value(DV.storage_discharge[s, n, t]) for t in range(data.num_rep_hours)] for n in range(data.num_nodes)] for s in range(data.num_storages)])
    DV_values.SOC = np.array([[[Model.get_value(DV.SOC[s, n, t]) for t in range(data.num_rep_hours)] for n in range(data.num_nodes)] for s in range(data.num_storages)])
    DV_values.flow = np.array([[Model.get_value(DV.flow[l, t]) for t in range(data.num_rep_hours)] for l in range(data.num_lines)])

    # get the values of the cost components
    DV_values.total_cost = Model.get_value(DV.total_cost)
    DV_values.gen_est_cost_vRE = Model.get_value(DV.gen_est_cost_vRE)
    DV_values.gen_est_cost_thermal = Model.get_value(DV.gen_est_cost_thermal)
    DV_values.line_est_cost = Model.get_value(DV.line_est_cost)
    DV_values.storage_est_cost = Model.get_value(DV.storage_est_cost)

    DV_values.VOM_cost_vRE = Model.get_value(DV.VOM_cost_vRE)
    DV_values.VOM_cost_thermal = Model.get_value(DV.VOM_cost_thermal)
    DV_values.load_shedding_cost = Model.get_value(DV.load_shedding_cost)
    DV_values.gas_fuel_cost = Model.get_value(DV.gas_fuel_cost)
    DV_values.gen_FOM_cost_vRE = Model.get_value(DV.gen_FOM_cost_vRE)
    DV_values.gen_FOM_cost_thermal = Model.get_value(DV.gen_FOM_cost_thermal)
    DV_values.line_FOM_cost = Model.get_value(DV.line_FOM_cost)
    DV_values.storage_FOM_cost = Model.get_value(DV.storage_FOM_cost)


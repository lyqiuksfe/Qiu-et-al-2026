# -*- coding: utf-8 -*-
import numpy as np
import time
import pyoptinterface as poi
from pyoptinterface import gurobi

def define_objective(Model, DV, data, Setting):
    #### if new generator/line/storage is established, there is a cost
    max_gen_per_node = Setting['max_generators_per_node']
    if Setting['evaluation_type'] == 'in-sample':
        if Setting['VRE_expansion_allowed']:
            Model.add_linear_constraint(DV.gen_est_cost_vRE-poi.quicksum(data.Generators_vRE[g].annualized_capex_per_unit*DV.gen_establish_vRE[g, n, u] for g in range(data.num_generators_vRE) for n in range(data.num_nodes) for u in range(max_gen_per_node)), poi.Eq, 0)
        else:
            Model.add_linear_constraint(DV.gen_est_cost_vRE, poi.Eq, 0)
            
        if Setting['thermal_expansion_allowed']:
            Model.add_linear_constraint(DV.gen_est_cost_thermal-poi.quicksum(data.Generators_thermal[g].annualized_capex_per_unit*DV.gen_establish_thermal[g, n] for g in range(data.num_generators_thermal) for n in range(data.num_nodes)), poi.Eq, 0)
        else:
            Model.add_linear_constraint(DV.gen_est_cost_thermal, poi.Eq, 0)

        if Setting['line_expansion_allowed']:
            Model.add_linear_constraint(DV.line_est_cost- poi.quicksum(data.Lines[l].annualized_capex * DV.line_establish[l] for l in range(data.num_lines)), poi.Eq, 0)
        else:
            Model.add_linear_constraint(DV.line_est_cost, poi.Eq, 0)

        if Setting['storage_expansion_allowed']:
            Model.add_linear_constraint(DV.storage_est_cost-poi.quicksum(DV.storage_capacity_establish[s,n]*(data.Storages[s].annualized_power_capex_per_MW + data.Storages[s].annualized_energy_capex_per_MW * data.Storages[s].duration_range) for s in range(data.num_storages) for n in range(data.num_nodes)), poi.Eq, 0)
        else:
            Model.add_linear_constraint(DV.storage_est_cost, poi.Eq, 0)
        
        #FOM fixed operation and maintenance cost
        Model.add_linear_constraint(DV.gen_FOM_cost_vRE-poi.quicksum(data.Generators_vRE[g].FOM_per_unit * DV.gen_operational_vRE[g, n, u] for g in range(data.num_generators_vRE) for n in range(data.num_nodes) for u in range(max_gen_per_node)), poi.Eq, 0)
        Model.add_linear_constraint(DV.gen_FOM_cost_thermal-poi.quicksum(data.Generators_thermal[g].FOM_per_unit * DV.gen_operational_thermal[g, n] for g in range(data.num_generators_thermal) for n in range(data.num_nodes)), poi.Eq, 0)
        Model.add_linear_constraint(DV.line_FOM_cost-poi.quicksum(data.Lines[l].FOM * DV.line_operational[l] for l in range(data.num_lines)), poi.Eq, 0)
        Model.add_linear_constraint(DV.storage_FOM_cost-poi.quicksum(DV.storage_capacity_operational[s,n]*(data.Storages[s].FOM_power + data.Storages[s].duration_range*data.Storages[s].FOM_energy) for s in range(data.num_storages) for n in range(data.num_nodes)), poi.Eq, 0)
    
    # VOM generation variable operation and maintenance cost
    if Setting['evaluation_type'] == 'in-sample':
        Model.add_linear_constraint(DV.VOM_cost_vRE-poi.quicksum(data.rep_hours_weights[t]* data.Generators_vRE[g].VOM_per_MWh * DV.generation_vRE[g, n, u, t] for g in range(data.num_generators_vRE) for n in range(data.num_nodes) for u in range(max_gen_per_node) for t in range(data.num_rep_hours)), poi.Eq, 0)
        Model.add_linear_constraint(DV.VOM_cost_thermal-poi.quicksum(data.rep_hours_weights[t]* data.Generators_thermal[g].VOM_per_MWh * DV.generation_thermal[g, n, t] for g in range(data.num_generators_thermal) for n in range(data.num_nodes) for t in range(data.num_rep_hours)), poi.Eq, 0)
    else:
        Model.add_linear_constraint(DV.VOM_cost_vRE-poi.quicksum(data.rep_hours_weights[t]* data.Generators_vRE[g].VOM_per_MWh * DV.generation_vRE[g, n, t] for g in range(data.num_generators_vRE) for n in range(data.num_nodes) for t in range(data.num_rep_hours)), poi.Eq, 0)
        Model.add_linear_constraint(DV.VOM_cost_thermal-poi.quicksum(data.rep_hours_weights[t]* data.Generators_thermal[g].VOM_per_MWh * DV.generation_thermal[g, n, t] for g in range(data.num_generators_thermal) for n in range(data.num_nodes) for t in range(data.num_rep_hours)), poi.Eq, 0)

    #gas fuel cost
    Model.add_linear_constraint(DV.gas_fuel_cost-poi.quicksum(data.rep_hours_weights[t]*data.Generators_thermal[g].heat_rate* DV.generation_thermal[g, n, t] * Setting['NG_price'] for g in range(data.num_generators_thermal) for n in range(data.num_nodes) for t in range(data.num_rep_hours)), poi.Eq, 0)  
    # load shedding cost
    Model.add_linear_constraint(DV.load_shedding_cost-poi.quicksum(data.rep_hours_weights[t]*DV.load_shedding[n, t] * Setting['load_shedding_penalty'] for n in range(data.num_nodes) for t in range(data.num_rep_hours)), poi.Eq, 0)

    # total cost
    if Setting['evaluation_type'] == 'in-sample':
        Model.add_linear_constraint(DV.total_cost-
                                    DV.gen_est_cost_vRE* Setting['ny']-
                                    DV.gen_est_cost_thermal* Setting['ny']-
                                    DV.line_est_cost* Setting['ny'] - 
                                    DV.storage_est_cost* Setting['ny']-
                                    DV.gen_FOM_cost_vRE* Setting['ny']-
                                    DV.gen_FOM_cost_thermal* Setting['ny']-
                                    DV.line_FOM_cost* Setting['ny'] - 
                                    DV.storage_FOM_cost* Setting['ny']-
                                    DV.VOM_cost_vRE-
                                    DV.VOM_cost_thermal-
                                    DV.load_shedding_cost - 
                                    DV.gas_fuel_cost, 
                                    poi.Eq, 0)
    else:
        Model.add_linear_constraint(DV.total_cost-
                                    DV.VOM_cost_vRE* Setting['ny'] -
                                    DV.VOM_cost_thermal* Setting['ny'] -
                                    DV.load_shedding_cost - 
                                    DV.gas_fuel_cost, 
                                    poi.Eq, 0)
    # set the objective function                                 
    Model.set_objective(DV.total_cost, poi.ObjectiveSense.Minimize)





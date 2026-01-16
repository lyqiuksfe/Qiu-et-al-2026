# -*- coding: utf-8 -*-
import pyoptinterface as poi

def define_decision_variables(Model, DV, data, Setting):
    # Get max number of generators per technology per node from Setting
    max_gen_per_node = Setting['max_generators_per_node']
    if Setting['evaluation_type'] == 'in-sample':
         # define decision variables for investment (now 3D: generator_type, node, unit_index)
        DV.gen_operational_vRE = Model.add_variables(range(data.num_generators_vRE), range(data.num_nodes), range(max_gen_per_node), lb=0, domain=poi.VariableDomain.Continuous)  
        if Setting['VRE_expansion_allowed']:
            DV.gen_establish_vRE = Model.add_variables(range(data.num_generators_vRE), range(data.num_nodes), range(max_gen_per_node), lb=0, domain=poi.VariableDomain.Continuous) 

        DV.gen_operational_thermal = Model.add_variables(range(data.num_generators_thermal), range(data.num_nodes), lb=0, domain=poi.VariableDomain.Continuous)   
        if Setting['thermal_expansion_allowed']:
            DV.gen_establish_thermal = Model.add_variables(range(data.num_generators_thermal), range(data.num_nodes), lb=0, domain=poi.VariableDomain.Continuous)     
    
        DV.line_operational = Model.add_variables(range(data.num_lines), lb=0, domain=poi.VariableDomain.Continuous)   
        if Setting['line_expansion_allowed']:
            DV.line_establish = Model.add_variables(range(data.num_lines), lb=0, domain=poi.VariableDomain.Continuous)   
        
        DV.storage_capacity_operational = Model.add_variables(range(data.num_storages), range(data.num_nodes), lb=0, domain=poi.VariableDomain.Continuous)    
        if Setting['storage_expansion_allowed']:
            DV.storage_capacity_establish = Model.add_variables(range(data.num_storages), range(data.num_nodes), lb=0, domain=poi.VariableDomain.Continuous)

    # define decision variables for operation (now 4D: generator_type, node, unit_index, time)
    DV.generation_vRE = Model.add_variables(range(data.num_generators_vRE), range(data.num_nodes), range(data.num_rep_hours), lb=0, domain=poi.VariableDomain.Continuous)
    DV.generation_thermal = Model.add_variables(range(data.num_generators_thermal), range(data.num_nodes), range(data.num_rep_hours), lb=0, domain=poi.VariableDomain.Continuous)
    DV.load_shedding = Model.add_variables(range(data.num_nodes), range(data.num_rep_hours), lb=0, domain=poi.VariableDomain.Continuous)
    DV.storage_charge = Model.add_variables(range(data.num_storages), range(data.num_nodes), range(data.num_rep_hours), lb=0, domain=poi.VariableDomain.Continuous)
    DV.storage_discharge = Model.add_variables(range(data.num_storages), range(data.num_nodes), range(data.num_rep_hours), lb=0, domain=poi.VariableDomain.Continuous)
    DV.SOC = Model.add_variables(range(data.num_storages), range(data.num_nodes), range(data.num_rep_hours), lb=0, domain=poi.VariableDomain.Continuous)
    DV.flow = Model.add_variables(range(data.num_lines), range(data.num_rep_hours),  domain=poi.VariableDomain.Continuous)

    # cost components
    DV.total_cost = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
    if Setting['evaluation_type'] == 'in-sample':
        DV.gen_est_cost_vRE = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
        DV.gen_est_cost_thermal = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
        DV.line_est_cost = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
        DV.storage_est_cost = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)

    DV.VOM_cost_vRE = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
    DV.VOM_cost_thermal = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)

    DV.gas_fuel_cost = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
    DV.gen_FOM_cost_vRE = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
    DV.gen_FOM_cost_thermal = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
    DV.line_FOM_cost = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
    DV.storage_FOM_cost = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)
    DV.load_shedding_cost = Model.add_variable(lb=0, domain=poi.VariableDomain.Continuous)

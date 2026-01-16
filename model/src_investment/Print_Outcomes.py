import numpy as np
import pandas as pd
import time, os, csv 
import pyoptinterface as poi
from pyoptinterface import gurobi

def publish_extensive_form(DV_values, Duals, data, Setting):
    df=pd.DataFrame(index=range(data.num_nodes))

    for g in range(data.num_generators_vRE):
        df[f'Total_{data.Generators_vRE[g].Type}'] = DV_values.gen_operational_vRE[g,:,:].sum(axis=1)
        if Setting['VRE_expansion_allowed']:
            df[f'New_{data.Generators_vRE[g].Type}'] = DV_values.gen_establish_vRE[g,:,:].sum(axis=1)
        else:
            df[f'New_{data.Generators_vRE[g].Type}'] = 0.0

    for g in range(data.num_generators_thermal):
        df[f'Total_{data.Generators_thermal[g].Type}'] = DV_values.gen_operational_thermal[g,:]
        if Setting['thermal_expansion_allowed']:
            df[f'New_{data.Generators_thermal[g].Type}'] = DV_values.gen_establish_thermal[g,:]
        else:
            df[f'New_{data.Generators_thermal[g].Type}'] = 0.0

    df['Total_storage_capacity'] = DV_values.storage_capacity_operational[0,:]
    if Setting['storage_expansion_allowed']:
        df['New_storage_capacity'] = DV_values.storage_capacity_establish[0,:]
    else:
        df['New_storage_capacity'] = 0.0
    name =f"{Setting['output_prefix']}_nodal_capacity.csv"
    df.to_csv(name, index=False)

    flow_output=pd.DataFrame(index=range(data.num_rep_hours))
    for g in range(data.num_generators_vRE):
        flow_output[f'{data.Generators_vRE[g].Type}'] = DV_values.generation_vRE[g,:,:,:].sum(axis=(0,1))
    for g in range(data.num_generators_thermal):
        flow_output[f'{data.Generators_thermal[g].Type}'] = DV_values.generation_thermal[g,:,:].sum(axis=(0))
    flow_output['Demand'] = 0.0
    for t in range(data.num_rep_hours):
        flow_output.loc[t,'Demand'] = sum(data.Nodes[n].demand[data.rep_hours[t]] for n in range(data.num_nodes))
    flow_output['Strg_charge'] = DV_values.storage_charge.sum(axis=(0,1))
    flow_output['Strg_discharge'] = DV_values.storage_discharge.sum(axis=(0,1))
    flow_output['Strg_level'] = DV_values.SOC.sum(axis=(0,1))
    flow_output['load_shedding'] = DV_values.load_shedding.sum(axis=0)
    flow_output.to_csv(f"{Setting['output_prefix']}_Load.csv",index=False)

def export_detailed_generation_results(DV_values, data, Setting):
    vRE_names={'wind-onshore':'wind','solar-UPV':'solar'}
    for g in range(data.num_generators_vRE):
        varname=vRE_names[data.Generators_vRE[g].Type]
        loc_file = f'{os.getcwd()}/preprocess/Resource/{Setting["balancing_authority"]}/cf_{varname}/Loc_table.csv'
        if os.path.exists(loc_file):
            df = pd.read_csv(loc_file, index_col=0)
        else:
            print(f"Warning: {loc_file} not found, creating basic template")
            df = create_basic_template(data.num_nodes, Setting['max_generators_per_node'], varname)
        df['Total_capacity'] = 0.0
        row_idx = 0
        for n in range(data.num_nodes):
            for u in range(Setting['max_generators_per_node']):
                df.iloc[row_idx, df.columns.get_loc('Total_capacity')] = DV_values.gen_operational_vRE[g, n, u]
                row_idx += 1
        output_file = f"{Setting['output_prefix']}_{data.Generators_vRE[g].Type}_capacity.csv"
        df.to_csv(output_file)
        print(f"{varname} generation results saved to: {output_file}")

    line_file_path = Setting['line_file']

    df=pd.read_csv(line_file_path)
    df['Total_capacity']=DV_values.line_operational
    if Setting['line_expansion_allowed']:
        df['New_capacity']=DV_values.line_establish
    else:
        df['New_capacity']=0.0
    name =f"{Setting['output_prefix']}_line_capacity.csv"
    df.to_csv(name, index=False)

def create_basic_template(num_nodes, max_gen_per_node, tech_type):
    """Create a basic template if Loc_table.csv is not found"""
    rows = []
    for n in range(num_nodes):
        for u in range(max_gen_per_node):
            row = {
                'name': f'Node_{n}_{tech_type}_{u}',
                'mask': 0.0,
                'lat': '',
                'lon': '',
                'capacity': '',
                'loc_index': '',
                'FIPS': '',
                'distance_miles': ''
            }
            rows.append(row)
    
    return pd.DataFrame(rows)

def publish_summary(DV_values, data, Setting, start_time, relative_gap):
    max_gen_per_node = Setting['max_generators_per_node']
    res={}
    res['ISO'] = Setting['balancing_authority']
    res['inv_sce'] = Setting['inv_sce']
    res['nNodes'] = data.num_nodes
    res['ny'] = Setting['ny']
    res['ensid'] = Setting['ensid']
    res['in_sample_year_list'] = Setting['in_sample_year_list']
    res['num_rep_days'] = Setting['num_rep_days']
    res['RPS'] = Setting['RPS']
    res['line limit rate']= 100
    res['CRM reserve'] = 0
    res['run time(s)'] = time.time()-start_time
    res['greenfield_vRE'] = Setting['greenfield_vRE']
    res['greenfield_thermal'] = Setting['greenfield_thermal']
    res['greenfield_line'] = Setting['greenfield_line']
    res['greenfield_storage'] = Setting['greenfield_storage']
    res['VRE_expansion_allowed'] = Setting['VRE_expansion_allowed']
    res['thermal_expansion_allowed'] = Setting['thermal_expansion_allowed']
    res['line_expansion_allowed'] = Setting['line_expansion_allowed']
    res['storage_expansion_allowed'] = Setting['storage_expansion_allowed']

    res['total system cost'] = DV_values.total_cost
    
    total_gen = 0
    res['vRE_est_cost'] = DV_values.gen_est_cost_vRE
    res['vRE_FOM_cost'] = DV_values.gen_FOM_cost_vRE
    for g in range(data.num_generators_vRE):
        vRE_type=data.Generators_vRE[g].Type
        res[f'{vRE_type}_total_cap'] = np.sum(DV_values.gen_operational_vRE[g,:,:])
        if Setting['VRE_expansion_allowed']:
            res[f'{vRE_type}_new_cap'] = np.sum(DV_values.gen_establish_vRE[g,:,:])
        else:
            res[f'{vRE_type}_new_cap'] = 0
        res[f'{vRE_type}_FOM_cost'] = data.Generators_vRE[g].FOM_per_unit * res[f'{vRE_type}_total_cap']
        res[f'{data.Generators_vRE[g].Type}_est_cost'] = data.Generators_vRE[g].annualized_capex_per_unit*res[f'{data.Generators_vRE[g].Type}_new_cap']
        res[f'{vRE_type}_gen'] = np.sum(DV_values.generation_vRE[g,:,:,:]*data.rep_hours_weights[:])
        total_gen += res[f'{data.Generators_vRE[g].Type}_gen']
    
    res['thermal_est_cost'] = DV_values.gen_est_cost_thermal
    res['thermal_FOM_cost'] = DV_values.gen_FOM_cost_thermal
    res['thermal_VOM_cost'] = DV_values.VOM_cost_thermal
    for g in range(data.num_generators_thermal):
        gtype=data.Generators_thermal[g].Type
        res[f'{gtype}_total_cap'] = np.sum(DV_values.gen_operational_thermal[g,:])
        if Setting['thermal_expansion_allowed']:
            res[f'{gtype}_new_cap'] = np.sum(DV_values.gen_establish_thermal[g,:])
        else:
            res[f'{gtype}_new_cap'] = 0
        res[f'{gtype}_FOM_cost'] = data.Generators_thermal[g].FOM_per_unit * res[f'{gtype}_total_cap']
        res[f'{gtype}_est_cost'] = data.Generators_thermal[g].annualized_capex_per_unit*res[f'{gtype}_new_cap']
        res[f'{gtype}_gen'] = np.sum(DV_values.generation_thermal[g,:,:]*data.rep_hours_weights[:])
        total_gen += res[f'{data.Generators_thermal[g].Type}_gen']
    res['gas fuel cost'] = DV_values.gas_fuel_cost


    res['Line_total_cap'] = np.sum(DV_values.line_operational)
    if Setting['line_expansion_allowed']:
        res['Line_new_cap'] = np.sum(DV_values.line_establish)
    else:
        res['Line_new_cap'] = 0
    res['Line_num'] = np.sum(DV_values.line_operational>0)
    res['Line_FOM_cost'] = DV_values.line_FOM_cost
    res['Line_est_cost'] = DV_values.line_est_cost
    res['Line_flow']= np.sum(np.abs(DV_values.flow)*data.rep_hours_weights[:])

    res['storage_total_cap'] = np.sum(DV_values.storage_capacity_operational)
    if Setting['storage_expansion_allowed']:
        res['storage_new_cap'] = np.sum(DV_values.storage_capacity_establish)
    else:
        res['storage_new_cap'] = 0
    res['storage_FOM_cost'] = DV_values.storage_FOM_cost
    res['storage_est_cost'] = DV_values.storage_est_cost
    
    res['shed load']= np.sum(DV_values.load_shedding)
    res['shedding cost'] = DV_values.load_shedding_cost
    res['total generation'] = total_gen
    res['storage_charge'] = np.sum(DV_values.storage_charge*data.rep_hours_weights[:])
    res['storage_discharge'] = np.sum(DV_values.storage_discharge*data.rep_hours_weights[:])
    res['total demand'] = sum(data.Nodes[n].demand[data.rep_hours[t]]*data.rep_hours_weights[t] for n in range(data.num_nodes) for t in range(data.num_rep_hours))

    header = res.keys()
    row = res.values()
    if Setting['csv_output_file'] is None:
        csvfile = os.getcwd()+f'/{Setting["balancing_authority"]}_investment_summary.csv'
    else:
        csvfile = Setting['csv_output_file']
    
    if not os.path.isfile(csvfile):
        with open(csvfile, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)
        f.close()
    else:
        with open(csvfile, 'a', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        f.close()
    
    


import numpy as np
import os
import pandas as pd
from . import utils as util

from pathlib import Path
class Node:
    def __init__(self):
        self.node_num = int() # node number
        self.demand = np.array([], dtype=np.float32) # demand 
        self.area=dict() # area in km^2 for vRE    
        self.cf=dict() # capacity factor for different types of vRE
        self.vRE_existing=dict() # existing capacity for different types of vRE
        self.thermal_existing=dict() # existing capacity for different types of vRE
        self.storage_capacity_existing = 0.0
        self.arcs = np.array([]) # arcs to other nodes, arcs and arc_signs are populated in the Transmission_Line class
        self.arc_signs = np.array([]) # signs of the arcs, used in the balance equations

    def populate_node_data(self, Setting, Nodes):
        vRE_names={'wind-onshore':'wind','solar-UPV':'solar'}
        ba = Setting["balancing_authority"]
        sce = Setting["inv_sce"]
        years = Setting["data_year_list"]
        k = Setting["max_generators_per_node"]
        input_prefix = Setting["input_prefix"]
        node_file_path = Setting['node_file']
        df_nodes = pd.read_csv(node_file_path)

        # --- demand --
        if Setting.get("demand_file"):
            df_eDem = pd.read_csv(Setting["demand_file"])
        else:
            frames = []
            for year in years:
                frames.append(pd.read_csv(f'{os.getcwd()}/preprocess/Resource/{ba}/demand/{sce}/{year}.csv'))
            df_eDem=pd.concat(frames, axis=0).reset_index(drop=True)

        # --- vRE CFs, area, and existing capacity ---
        vRE_cf_df_all={}
        vRE_capacity_list={}
        vRE_area_list={}
        for g in range(len(self.Generators_vRE)):
            vRE_type = self.Generators_vRE[g].Type
            short = vRE_names[vRE_type]

            cf_frames = []
            for year in years:
                p = f'{os.getcwd()}/preprocess/Resource/{ba}/cf_{short}/{sce}/{year}.csv'
                cf_frames.append(pd.read_csv(p))
            cf_df = pd.concat(cf_frames, axis=0, ignore_index=True).fillna(0.0).reset_index(drop=True)
            vRE_cf_df_all[vRE_type] = cf_df.astype(np.float32)

            # Existing capacity per node-slot (length = num_nodes*k)
            if not Setting['greenfield_vRE']:
                cap_path = f"{Setting['input_prefix']}_{vRE_type}_capacity.csv"
                cap_series = pd.read_csv(cap_path)["Total_capacity"].astype(np.float32)
                vRE_capacity_list[vRE_type]=cap_series
            else:
                vRE_capacity_list[vRE_type]=None

            # Area list (mask) per node-slot
            loc_tbl = pd.read_csv(f"{os.getcwd()}/preprocess/Resource/{ba}/cf_{short}/Loc_table.csv",index_col='name')['mask'].astype(np.float32)
            vRE_area_list[vRE_type] = loc_tbl

        # --- thermal nodal capacities (+ storage) ---
        nodal_capacity_list={}
        if not Setting['greenfield_thermal']:
            cap=pd.read_csv(f'{Setting["input_prefix"]}_nodal_capacity.csv')
        for g in range(len(self.Generators_thermal)):
            thermal_type=self.Generators_thermal[g].Type
            if not Setting['greenfield_thermal']:
                nodal_capacity_list[thermal_type]=cap[f'Total_{thermal_type}']
        if not Setting['greenfield_storage']:        
            nodal_capacity_list['Storage']=cap['Total_storage_capacity']

        # Vectorized node creation
        for n in range(len(df_nodes)):
            en = Node()
            node_info=df_nodes.iloc[n]
            en.node_num = int(node_info["node_num"])
            en.demand = np.round(df_eDem.iloc[:, n+1], 2)
            node_name = node_info['FIPS']

            for g in range(len(self.Generators_vRE)):
                vRE_type=self.Generators_vRE[g].Type
                start=n*k
                stop=(n+1)*k
                en.area[vRE_type] = vRE_area_list[vRE_type].loc['%d_%s_0'%(node_name,vRE_names[vRE_type]):'%d_%s_%d'%(node_name,vRE_names[vRE_type],k-1)].values
                en.cf[vRE_type] = np.round(vRE_cf_df_all[vRE_type].T.loc['%d_%s_0'%(node_name,vRE_names[vRE_type]):'%d_%s_%d'%(node_name,vRE_names[vRE_type],k-1)].values.T, 2)

                if not Setting['greenfield_vRE']:
                    en.vRE_existing[vRE_type] = vRE_capacity_list[vRE_type].iloc[start:stop].values
                else:
                    en.vRE_existing[vRE_type] = np.zeros(k, dtype=np.float32)

            for g in range(len(self.Generators_thermal)):
                thermal_type=self.Generators_thermal[g].Type
                if not Setting['greenfield_thermal']:
                    en.thermal_existing[thermal_type] = nodal_capacity_list[thermal_type].iloc[n]
                else:
                    en.thermal_existing[thermal_type] = 0

            if not Setting['greenfield_storage']:
                en.storage_capacity_existing = nodal_capacity_list['Storage'].iloc[n]
            else:
                en.storage_capacity_existing = 0
            Nodes.append(en)


class Generator_Type_vRE:
    def __init__(self): 
        self.Type = str() # name of the generator type, e.g., solar, wind-offshore, gas, nuclear, hydro
        self.annualized_capex_per_unit = float() # capital expenditure per unit generator 
        self.VOM_per_MWh = float() # variable operation and maintenance cost per MWh
        self.FOM_per_unit = float() # fixed operation and maintenance cost per MW
        self.lifetime = int() # lifetime in years
        self.power2area_density = float() # power to area density in MW/km^2

    def populate_generator_type_vRE_data(self, Setting, Generators_vRE):
        # Use custom file path if specified in Setting, otherwise use default
        if 'gen_params_file' in Setting and Setting['gen_params_file']:
            gen_file_path = Setting['gen_params_file']
        else:
            gen_file_path = f'{os.getcwd()}/Params/generator_parameters.csv'

        df_gen = pd.read_csv(gen_file_path)
        for i in range(len(df_gen)):
            plant_info=df_gen.iloc[i]
            if (plant_info['is_VRE']==1)&(plant_info['allowed_to_establish']==1):
                plt = Generator_Type_vRE()
                plt.Type = plant_info['Type']
                plt.power2area_density = plant_info['Density (MW/km2)']
                plt.VOM_per_MWh = plant_info['VOM ($/MWh)']
                plt.lifetime = plant_info['Lifetime (year)']
                plt.FOM_per_unit = plant_info['FOM ($/kW-yr)']*1000 # convert to $/MW-yr
                crf = util.CRF(Setting['WACC'], plt.lifetime)
                plt.annualized_capex_per_unit = crf*plant_info['CAPEX($/kw)'] *1000
                Generators_vRE.append(plt)
        self.num_generators_vRE = len(self.Generators_vRE) # number of generator types 

class Generator_Type_thermal:
    def __init__(self): 
        self.Type = str() # name of the generator type, e.g., solar, wind-offshore, gas, nuclear, hydro
        self.annualized_capex_per_unit = float() # capital expenditure per unit generator 
        self.VOM_per_MWh = float() # variable operation and maintenance cost per MWh
        self.FOM_per_unit = float() # fixed operation and maintenance cost per MW
        self.ramp_rate = float() # ramp rate in percentage
        self.heat_rate = float() # heat rate in MMBtu/MWh
        self.lifetime = int() # lifetime in years
        self.power2area_density = float() # power to area density in MW/km^2
        
    def populate_generator_type_thermal_data(self, Setting, Generators_thermal):
        # Use custom file path if specified in Setting, otherwise use default
        if 'gen_params_file' in Setting and Setting['gen_params_file']:
            gen_file_path = Setting['gen_params_file']
        else:
            gen_file_path = f'{os.getcwd()}/Params/generator_parameters.csv'

        df_gen = pd.read_csv(gen_file_path)
        for i in range(len(df_gen)):
            plant_info=df_gen.iloc[i]
            if (plant_info['is_thermal']==1)&(plant_info['allowed_to_establish']==1):
                plt = Generator_Type_thermal()
                plt.Type = plant_info['Type']
                plt.power2area_density = plant_info['Density (MW/km2)']
                plt.VOM_per_MWh = plant_info['VOM ($/MWh)']
                plt.heat_rate = plant_info['Heat Rate (MMBtu/MWh)']
                plt.lifetime = int(plant_info['Lifetime (year)'])
                plt.FOM_per_unit = plant_info['FOM ($/kW-yr)']*1000 # convert to $/MW-yr
                plt.ramp_rate = plant_info['Hourly Ramp rate (%)']
                crf = util.CRF(Setting['WACC'], plt.lifetime)
                plt.annualized_capex_per_unit = crf*plant_info['CAPEX($/kw)'] *1000
                Generators_thermal.append(plt)

class Transmission_Line:
    def __init__(self):
        self.num = int() # line number
        self.from_node = int() # from node number
        self.to_node = int() # to node number
        self.length = float() # length in km
        self.existing_cap = float() # capacity in MW
        self.max_flow= float() # maximum flow in MW
        self.annualized_capex = float() # annualized capital expenditure
        self.FOM = float() # fixed operation and maintenance cost per MW

    def populate_line_data(self, Setting, Nodes, Lines):
        if 'line_file' in Setting and Setting['line_file']:
            line_file_path = Setting['line_file']
        else:
            line_file_path = f'{os.getcwd()}/preprocess/Network/Transmission_Lines_{Setting["balancing_authority"]}.csv'
        
        if 'line_params_file' in Setting and Setting['line_params_file']:
            line_params_path = Setting['line_params_file']
        else:
            line_params_path = f'{os.getcwd()}/Params/transmission_line_parameters.csv'
            
        df_br = pd.read_csv(line_file_path)
        df_br_par = pd.read_csv(line_params_path).iloc[0]
    
        arcs = [[] for x in range(len(Nodes))]
        arc_signs = [[] for x in range(len(Nodes))]
        if not Setting['greenfield_line']:
            capacity_list=pd.read_csv(f'{Setting["input_prefix"]}_line_capacity.csv')

        for b in range(len(df_br)):
            br = Transmission_Line()
            br.num = b
            line_info=df_br.iloc[b]
            br.from_node = int(line_info['from_node'])
            br.to_node = int(line_info['to_node'])
            arcs[br.from_node].append(b)
            arcs[br.to_node].append(b)
            if br.from_node>br.to_node:
                arc_signs[br.from_node].append(-1)
                arc_signs[br.to_node].append(1)
            else:
                arc_signs[br.from_node].append(1)
                arc_signs[br.to_node].append(-1)
            br.length = line_info['distance_mile']
            br.max_capacity = line_info['maxFlow']
            crf = util.CRF(Setting['WACC'],df_br_par['trans_line_lifetime'])
            br.FOM = br.length*df_br_par['trans_line_FOM ($/MW/mile)']
            br.annualized_capex = br.length*df_br_par['trans_line_inv_cost ($/MWyr/mile)']
            if not Setting['greenfield_line']:
                br.existing_cap = capacity_list['Total_capacity'][b]
            else:
                br.existing_cap = line_info['capacity']
            br.existing_cap = 0
            Lines.append(br)
        # create arcs and arc_sign for each node to be used in the balance equations
        for n in range(len(arcs)):
            Nodes[n].arcs = np.array(arcs[n])
            Nodes[n].arc_signs = np.array(arc_signs[n])

class Storage:
    def __init__(self):
        self.Type = str() # name of the storage type, e.g., Li-ion, metal-air
        self.annualized_energy_capex_per_MW = float() # capital expenditure for energy storage in $/kWh
        self.annualized_power_capex_per_MW = float() # capital expenditure for power storage in $/kW
        self.charging_eff = float() # charging efficiency
        self.discharging_eff = float() # discharging efficiency
        self.self_discharge = float() # self-discharge rate in %/day
        self.FOM_energy = float() # energy fixed operation and maintenance cost in 
        self.FOM_power = float() # power fixed operation and maintenance cost in $/kW-yr
        self.lifetime = int() # lifetime in years
        self.duration_range = float(); # duration range in hours, e.g., 4, 24 ,168
    def populate_storage_data(self, Setting, Storages): 
        if 'storage_params_file' in Setting and Setting['storage_params_file']:
            storage_params_path = Setting['storage_params_file']
        else:
            storage_params_path = f'{os.getcwd()}/Params/storage_parameters.csv'
            
        df_str = pd.read_csv(storage_params_path)
        for i in range(len(df_str)):
            st = Storage()
            strg_info=df_str.iloc[i]
            st.Type = strg_info['Storage technology']
            st.charging_eff = strg_info['charging efficiency']
            st.discharging_eff = strg_info['discharging efficiency']
            st.FOM_energy = strg_info['Energy FOM ($/MWh-yr)']
            st.FOM_power = strg_info['Power FOM ($/MW-yr)']
            st.lifetime = int(strg_info['lifetime'])
            st.self_discharge = strg_info['self-discharge']
            st.duration_range = strg_info['duration_range(h)']
            crf=util.CRF(Setting['WACC'],st.lifetime)
            st.annualized_energy_capex_per_MW = crf*strg_info['Energy CAPEX ($/MWh)']
            st.annualized_power_capex_per_MW = crf*strg_info['Power CAPEX ($/MW)']
            Storages.append(st)


class Data(Node, Generator_Type_vRE, Generator_Type_thermal,Transmission_Line, Storage):
    def __init__(self, Setting):
        Node.__init__(self)
        Generator_Type_vRE.__init__(self)
        Generator_Type_thermal.__init__(self)
        Transmission_Line.__init__(self)
        Storage.__init__(self)

        self.Generators_vRE = []  # list of generator types
        self.Generators_thermal = []  # list of generator types
        self.Lines = []  # list of transmission lines
        self.Storages = []  # list of storage types
        self.Nodes = []  # list of nodes

        # populate for nodes, generator types, transmission lines, and storage
        self.populate_data(Setting)
        self.num_nodes = len(self.Nodes) # number of nodes
        self.num_generators_vRE = len(self.Generators_vRE) # number of generator types 
        self.num_generators_thermal = len(self.Generators_thermal) # number of generator types
        self.num_lines = len(self.Lines) # number of transmission lines
        self.num_storages = len(self.Storages) # number of storage types
        
        # Multi-generator support
        self.max_generators_per_node = Setting['max_generators_per_node'] # maximum generators per technology per node
        self.num_generator_units = self.num_generators_thermal+self.num_generators_vRE * self.num_nodes * self.max_generators_per_node # total generator units
        self.rep_days = np.array([]) # representative days
        self.rep_hours = np.array([]) # representative hours   
        self.rep_day_weights = np.array([]) # weights for representative days
        self.rep_hours_weights = np.array([]) # weights for representative hours
        
        self.num_rep_days=365*len(Setting['data_year_list'])
        self.rep_days = np.arange(self.num_rep_days)
        self.rep_hours = np.arange(self.num_rep_days*24)
        self.rep_day_weights = np.ones(Setting['num_rep_days'], dtype=int)
        self.rep_hours_weights = np.ones(Setting['num_rep_days']*24, dtype=int)
        self.num_rep_hours = self.num_rep_days * 24 # number of representative hours


    def populate_data(self, Setting):
        """
        this function populates the data for nodes, generator types, transmission lines, and storage.
        It reads the data from the csv files and populates the respective classes.
        """
        self.populate_generator_type_vRE_data(Setting, self.Generators_vRE)
        self.populate_generator_type_thermal_data(Setting, self.Generators_thermal)
        self.populate_node_data(Setting, self.Nodes)
        self.populate_line_data(Setting, self.Nodes, self.Lines)
        self.populate_storage_data(Setting, self.Storages)



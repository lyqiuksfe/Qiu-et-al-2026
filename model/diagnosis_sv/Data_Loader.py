import numpy as np
import os
import pandas as pd

class Node:
    def __init__(self):
        self.node_num = int() # node number
        self.demand = np.array([], dtype=np.float32) # demand 
        self.vRE_gen=dict()
        self.vRE_existing=dict()
        self.vRE_sv=dict()

    def populate_node_data(self, Setting, Nodes):
        vRE_names={'wind-onshore':'wind','solar-UPV':'solar'}
        Generators_vRE=['wind-onshore','solar-UPV']
        ba = Setting["balancing_authority"]
        sce = Setting["test_sce"]
        years = Setting["data_year_list"]
        k = Setting["max_generators_per_node"]
        input_prefix = Setting["input_prefix"]
        node_file_path = Setting['node_file']
        df_nodes = pd.read_csv(node_file_path)
        
        vRE_cf_df_all={}
        vRE_capacity_list={}
        for g in range(len(Generators_vRE)):
            vRE_type = Generators_vRE[g]
            short = vRE_names[vRE_type]

            cf_frames = []
            for year in years:
                p = f'{os.getcwd()}/preprocess/Resource/{ba}/cf_{short}/{sce}/{year}.csv'
                cf_frames.append(pd.read_csv(p,index_col=0))
            cf_df = pd.concat(cf_frames, axis=0, ignore_index=True).fillna(0.0).reset_index(drop=True)
            vRE_cf_df_all[vRE_type] = cf_df.astype(np.float32)
            cap_path = f"{Setting['input_prefix']}_{vRE_type}_capacity.csv"
            cap_series = pd.read_csv(cap_path)["Total_capacity"].astype(np.float32)
            vRE_capacity_list[vRE_type]=cap_series

        
        for n in range(len(df_nodes)):
            en = Node()
            node_info=df_nodes.iloc[n]
            en.node_num = int(node_info["node_num"])
            for g in range(len(Generators_vRE)):
                vRE_type=Generators_vRE[g]
                start=n*k
                stop=(n+1)*k
                en.vRE_existing[vRE_type] = vRE_capacity_list[vRE_type].iloc[start:stop]
                gen = vRE_cf_df_all[vRE_type].iloc[:, start:stop].mul(en.vRE_existing[vRE_type].values, axis=1)
                en.vRE_gen[vRE_type]=gen
                en.keep=(en.vRE_existing[vRE_type].values  > 0)
                en.vRE_gen[vRE_type].loc[:, ~en.keep] = float('nan')
                en.vRE_gen[vRE_type] = en.vRE_gen[vRE_type].dropna(axis=1, how='all')
                if en.vRE_gen[vRE_type].shape[1] > 0:
                    en.vRE_sv[vRE_type] = en.vRE_gen[vRE_type].std(axis=1).values
                    en.vRE_gen[vRE_type] = en.vRE_gen[vRE_type].sum(axis=1).values
                else:
                    en.vRE_sv[vRE_type] = np.array([np.nan]*len(en.vRE_gen[vRE_type]))
                    en.vRE_gen[vRE_type] = np.array([np.nan]*len(en.vRE_gen[vRE_type]))
            Nodes.append(en)



class Data(Node):
    def __init__(self, Setting):
        Node.__init__(self)
        self.Nodes = []  # list of nodes
        # populate for nodes, generator types, transmission lines, and storage
        self.populate_data(Setting)


    def populate_data(self, Setting):
        """
        this function populates the data for nodes, generator types, transmission lines, and storage.
        It reads the data from the csv files and populates the respective classes.
        """
        self.populate_node_data(Setting, self.Nodes)


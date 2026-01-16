import numpy as np
import pandas as pd
import time
import sys
import itertools
from Setting_dispatch import Setting
import sys
sys.path.append('./model/')
from diagnosis_sv.Data_Loader import Data
import os
import argparse

np.random.seed(42)
parser = argparse.ArgumentParser(description='')
parser.add_argument('--iso', type=str,default=None, help='ISO name')
parser.add_argument('--inv_sce', type=str, default='historic', help='Climate scenario (default: historic)')
parser.add_argument('--test_sce', type=str, default='historic', help='Test scenario (default: historic)')
parser.add_argument('--start_id', type=int, default=0, help='Start index for in-sample year combinations (default: 0)')
parser.add_argument('--end_id', type=int, default=0, help='End index for in-sample year combinations (default: 0)')
parser.add_argument('--batch', type=int, default=0, help='Stage number for multi-stage investment (default: 0)')
parser.add_argument('--single_year', type=int, default=0, help='Stage number for multi-stage investment (default: 0)')

args = parser.parse_args()
Setting['balancing_authority']=args.iso
Setting['inv_sce']=args.inv_sce
Setting['test_sce']=args.test_sce
sn_y=args.start_id
en_y=args.end_id
test_scenario_batch=args.batch
single_year=args.single_year

Setting['line_file']=f'{os.getcwd()}/preprocess/Network/Transmission_Lines_{Setting["balancing_authority"]}_existing.csv'
Setting['node_file']=f'{os.getcwd()}/preprocess/Network/Power_Nodes_{Setting["balancing_authority"]}.csv'
if single_year!=0:
    test_years = [single_year]
else:
    if Setting['test_sce']=='historic':
        test_years=[2003,2005,2007,2008,2010,2011,2013,2015,2019]
    else:
        test_years=list(range(2046, 2056))


for en in range(sn_y,en_y+1):
    print(f"Processing ensemble {en}")
    std_wind=[]
    std_solar=[]
    for year in test_years:
        Setting['ensid']=en
        Setting['out_of_sample_year_list'] = [year]
        Setting['data_year_list'] = Setting['out_of_sample_year_list']
        Setting['test_year']=year
        Setting['num_rep_days']=365*len(Setting['data_year_list'])
        Setting['input_prefix'] =f"{os.getcwd()}/result_{Setting['balancing_authority']}_inv/ny_{Setting['ny']}_{Setting['inv_sce']}_ens_{Setting['ensid']}"
        Setting['output_fix'] =f"{os.getcwd()}/result_{Setting['balancing_authority']}_dispatch_{Setting['test_sce']}/ny_{Setting['ny']}_ens_{Setting['ensid']}"

        data = Data(Setting)
        for gtype in ['wind-onshore','solar-UPV']:
            tmp=np.zeros((len(data.Nodes),Setting['num_rep_days']*24))
            for node in range(len(data.Nodes)):
                tmp[node,:]=data.Nodes[node].vRE_gen[gtype]
            std_tmp=np.nanstd(tmp,axis=0)
            std_tmp=pd.Series(std_tmp)
            if gtype == 'wind-onshore':
                std_wind.append(std_tmp)
            else:
                std_solar.append(std_tmp)
    std_wind=pd.concat(std_wind,axis=0).reset_index(drop=True)
    std_solar=pd.concat(std_solar,axis=0).reset_index(drop=True)
    df_out=pd.DataFrame()
    df_out['wind-onshore']=std_wind
    df_out['solar-UPV']=std_solar
    df_out.to_csv(f"{Setting['output_fix']}_dispatch_SV.csv",index=True)



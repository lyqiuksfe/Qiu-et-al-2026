import numpy as np
import time
import sys
import itertools
import os
sys.path.append('./model/')
from Setting_investment import Setting
from src_investment.Data_Loader import Data
from src_investment.Model_Class import Power_System_Model
import argparse

np.random.seed(42)
parser = argparse.ArgumentParser(description='')
parser.add_argument('--iso', type=str,default=None, help='ISO name')
parser.add_argument('--inv_sce', type=str, default='historic', help='Climate scenario (default: historic)')
parser.add_argument('--start_id', type=int, default=0, help='Start index for in-sample year combinations (default: 0)')
parser.add_argument('--end_id', type=int, default=0, help='End index for in-sample year combinations (default: 0)')
args = parser.parse_args()

Setting['balancing_authority']=str(args.iso)
Setting['inv_sce']=args.inv_sce  # investment scenario: 'historic', 'rcp85hotter', 'rcp85colder'
sn_y=args.start_id
en_y=args.end_id


# Setting['balancing_authority']='ISONE'
# Setting['investment_type']='single'
# sn_y=0
# en_y=0
# Setting['inv_sce']='historic'  # investment scenario: 'historic', 'rcp85hotter', 'rcp85colder'


hist_years=np.random.choice(list(range(2001, 2020)), size=10, replace=False)
if Setting['inv_sce']=='historic':
    full_year_list = hist_years
else:
    full_year_list = list(range(2046, 2056))
year_lists = list(itertools.combinations(full_year_list, Setting['ny']))


Setting['line_file']=f'{os.getcwd()}/preprocess/Network/Transmission_Lines_{Setting["balancing_authority"]}_existing.csv'
Setting['node_file']=f'{os.getcwd()}/preprocess/Network/Power_Nodes_{Setting["balancing_authority"]}.csv'


for en in range(sn_y,en_y+1):
    Setting['ensid']=en
    Setting['in_sample_year_list']=list(year_lists[en])
    Setting['data_year_list']=Setting['in_sample_year_list']
    Setting['num_rep_days']=365*len(Setting['data_year_list'])
    Setting['ny']=len(Setting['data_year_list'])
    Setting['output_prefix'] =f"{os.getcwd()}/result_{Setting['balancing_authority']}_inv/ny_{Setting['ny']}_{Setting['inv_sce']}_ens_{Setting['ensid']}"
    Setting['input_prefix'] =None
    if not os.path.exists(f"{Setting['output_prefix']}_Load.csv"):
        data = Data(Setting)
        start_time = time.time()
        power_model = Power_System_Model(data, Setting)
        power_model.build_model()
        power_model.solve_model()
        power_model.get_DV_values()
        power_model.print_results(start_time)
        power_model.export_detailed_results()
    else:
        print(f"Results already exist for {Setting['output_prefix']}, skipping...")




import numpy as np
import time
import sys
import itertools
import os
sys.path.append('./model/')
from Setting_dispatch import Setting
from src_dispatch.Data_Loader import Data
from src_dispatch.Model_Class import Power_System_Model
import argparse

np.random.seed(42)
parser = argparse.ArgumentParser(description='')
parser.add_argument('--iso', type=str,default=None, help='ISO name (default: ERCOT)')
parser.add_argument('--inv_sce', type=str, default='historic', help='Climate scenario (default: historic)')
parser.add_argument('--test_sce', type=str, default='historic', help='Test scenario (default: historic)')
parser.add_argument('--start_id', type=int, default=0, help='Start index for in-sample year combinations (default: 0)')
parser.add_argument('--end_id', type=int, default=0, help='End index for in-sample year combinations (default: 0)')
parser.add_argument('--batch', type=int, default=0, help='Stage number for multi-stage investment (default: 0)')
parser.add_argument('--single_year', type=int, default=0, help='Stage number for multi-stage investment (default: 0)')

args = parser.parse_args()
Setting['balancing_authority']=str(args.iso)
sn_y=args.start_id
en_y=args.end_id
Setting['inv_sce']=str(args.inv_sce)
Setting['test_sce']=str(args.test_sce)
test_scenario_batch=int(args.batch)
single_year=args.single_year

# Setting['balancing_authority']='ISONE'
# sn_y=0
# en_y=0
# Setting['inv_sce']='historic'
# Setting['test_sce']='historic'
# test_scenario_batch=0
# single_year=2002

if single_year!=0:
    test_years = [single_year]
else:
    if Setting['test_sce']=='historic':
        test_years=[2003,2005,2007,2008,2010,2011,2013,2015,2019]
    else:
        if test_scenario_batch==1:
            test_years=list(range(2020,2030))
        elif test_scenario_batch==2:
            test_years=list(range(2030,2040))
        elif test_scenario_batch==3:
            test_years=list(range(2040,2050))
        elif test_scenario_batch==4:
            test_years=list(range(2050,2060))



Setting['line_file']=f'{os.getcwd()}/preprocess/Network/Transmission_Lines_{Setting["balancing_authority"]}_existing.csv'
Setting['node_file']=f'{os.getcwd()}/preprocess/Network/Power_Nodes_{Setting["balancing_authority"]}.csv'

for en in range(sn_y,en_y+1):
    for year in test_years:
        Setting['ensid']=en
        Setting['out_of_sample_year_list'] = [year]
        Setting['data_year_list'] = Setting['out_of_sample_year_list']
        Setting['test_year']=year
        Setting['num_rep_days']=int(365*len(Setting['data_year_list']))
        Setting['input_prefix'] =f"{os.getcwd()}/result_{Setting['balancing_authority']}_inv/ny_{Setting['ny']}_{Setting['inv_sce']}_ens_{Setting['ensid']}"
        Setting['output_fix'] =f"{os.getcwd()}/result_{Setting['balancing_authority']}_dispatch_{Setting['test_sce']}/ny_{Setting['ny']}_ens_{Setting['ensid']}"
        testfile=f"{Setting['output_fix']}_test_{year}_dispatch_Load.csv"
        if os.path.exists(testfile):
            print(f"Skip existing {testfile} test year {year}")
        else:
            print('generating '+testfile+f" test year {year}")
            start_time = time.time()
            data = Data(Setting)
            power_model = Power_System_Model(data, Setting)
            power_model.build_model()
            power_model.solve_model()
            power_model.get_DV_values()
            power_model.print_results(start_time)  





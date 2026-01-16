# -*- coding: utf-8 -*-
"""
Settings for dispatch test example
"""

Setting = {    
    'evaluation_type': 'out-of-sample',          
    'RPS': 1,     
    'max_generators_per_node': 8,                                                 # 50% renewable portfolio standard                 # 15% capacity reserve margin    
    'line_limit_rate': 100,    
    'load_shedding_penalty': 100000, 
    'WACC': 0.062,                          
    'NG_price': 5.45, 
    'solver': 'gurobi',
    'solver_gap': 0.01,
    'wall_clock_time_lim': 360000,            # 1 hour time limit
    'Cross_over_status': -1,
    'show_log_info': 1,
    'print_extensive_outcome': True,
    'print_result_header': True,   
    'solution_method': 'extensive_form',
    'solver_thread_num': 10,  
    'ny':2,         
    'greenfield_vRE':False,
    'greenfield_thermal':False,
    'greenfield_line':False,
    'greenfield_storage':False,   
    'VRE_expansion_allowed':False,
    'thermal_expansion_allowed':False,
    'line_expansion_allowed':False,
    'storage_expansion_allowed':False,            
    'Method': -1,
    'csv_output_file': None,     
}
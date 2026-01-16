# -*- coding: utf-8 -*-
"""
Settings for investment example
"""

Setting = {    
    'evaluation_type': 'in-sample',          
    'RPS': 1,                             # 100% renewable portfolio standard 
    'max_generators_per_node': 8,           # KEY NEW PARAMETER: Allow 8 generators per technology per node                                                                                                  
    'load_shedding_penalty': 100000,         
    'WACC': 0.062,                          
    'NG_price': 5.45,     
    'solver': 'gurobi',
    'solver_gap': 0.01,
    'wall_clock_time_lim': 360000,            # 1 hour time limit
    'Cross_over_status': 0,
    'show_log_info': 1,
    'print_extensive_outcome': True,
    'print_result_header': True,  
    'solution_method': 'extensive_form',
    'solver_thread_num': 32,   
    'ny':2,
    'greenfield_vRE':True,
    'greenfield_thermal':True,
    'greenfield_line':True,
    'greenfield_storage':True,
    'VRE_expansion_allowed':True,
    'thermal_expansion_allowed':True,
    'line_expansion_allowed':True,
    'storage_expansion_allowed':True,
}

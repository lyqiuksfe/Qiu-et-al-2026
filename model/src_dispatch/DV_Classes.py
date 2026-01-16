
# -*- coding: utf-8 -*-

import pyoptinterface as poi
import numpy as np

class Power_System_Decision_Variables:
    def __init__(self):
        # set of investment decision variables
        self.gen_establish_vRE = []      # established unt/capacity per generator (at each node)
        self.gen_operational_vRE = []   # operational unt/capacity per generator (at each node)
        self.gen_decommissioned_vRE = []   # decommissioned unt/capacity per generator (at each node)
        
        self.gen_establish_thermal = []
        self.gen_operational_thermal = []
        self.gen_decommissioned_thermal = []

        self.storage_capacity_operational = []     # storage charging and discharging capacity per each storage type (at each node)
        self.storage_capacity_establish = []     # established storage charging and discharging capacity per each storage type (at each node)
        self.storage_capacity_decommissioned = []     # decommissioned storage charging and discharging capacity per each storage type (at each node)
        
        self.line_establish = []     # established line capacity between two nodes
        self.line_operational = []     # operational line capacity between two nodes
        self.line_decommissioned = []     # decommissioned line capacity between two nodes

        # set of operational decision variables
        self.generation_vRE = []           # generation per generator per time period (at each node)
        self.generation_thermal = []       # load shedding per time period (at each node)
        self.load_shedding=[]
        self.storage_charge = []      # storage charging amount per each storage type per each time period (at each node)
        self.storage_discharge = []   # storage discharging amount per each storage type per each time period (at each node)
        self.SOC = []                 # state of charge per each storage type per each time period (at each node)
        self.flow = []                # electric power flow per line per time period (between two nodes)

        # cost components
        self.total_cost = []           # total cost of the system
        self.gen_est_cost_vRE = []         #  generation establishment cost
        self.gen_est_cost_thermal = []     # thermal generation establishment cost
        self.line_est_cost = []        # transmission line establishment cost
        self.storage_est_cost = []     # storage establishment cost
        self.VOM_cost_vRE = []             # variable operation and maintenance cost
        self.VOM_cost_thermal = []         # variable operation and maintenance cost
        self.gen_FOM_cost_vRE = []         # fixed operation and maintenance cost per generator
        self.gen_FOM_cost_thermal = []     # fixed operation and maintenance cost per thermal generator
        self.gas_fuel_cost = []       # gas fuel cost
        self.line_FOM_cost = []        # fixed operation and maintenance cost per line
        self.storage_FOM_cost = []     # fixed operation and maintenance cost per storage
        self.load_shedding_cost = []   # load shedding cost


class Power_System_Decision_Values(Power_System_Decision_Variables):
    def __init__(self): super().__init__()     

class Oper_Constraints_Names:
    def __init__(self, data):
        self.prod_limit_thermal = []
        self.prod_limit_solar = []
        self.prod_limit_wind = []
        self.load_balance = []
        self.ramp_limit_up = []
        self.ramp_limit_down = []
        self.flow_limit1 = []
        self.flow_limit2 = []
        self.storage_SOC_balance = []
        self.storage_charge_limit = []
        self.storage_discharge_limit = []
        self.storage_SOC_limit = []
        self.RPS = []
        self.CRM = []
        self.line_expansion_limit = []

class Dual_vals(Oper_Constraints_Names):
    def __init__(self, data=None): super().__init__(data)





import numpy as np
import time
import pyoptinterface as poi
from pyoptinterface import gurobi
from pyoptinterface import highs
from . import DV_Classes
from . import Define_DVs
from . import Constraints
from . import Objective_Function
from . import Get_Vals
from . import Print_Outcomes

class Power_System_Model():

    def __init__(self, data, Setting):
        self.data = data
        self.Setting = Setting
        self.Model = []
        self.DV = DV_Classes.Power_System_Decision_Variables()
        self.DV_values = DV_Classes.Power_System_Decision_Values()
        self.Con = DV_Classes.Oper_Constraints_Names(data)
        self.Duals = DV_Classes.Dual_vals(data)

    def build_model(self):
        if self.Setting['solver']=='gurobi':
            self.Model = gurobi.Model()
        if self.Setting['solver'] == 'highs':
            self.Model = highs.Model()
        Define_DVs.define_decision_variables(self.Model, self.DV, self.data, self.Setting)
        Objective_Function.define_objective(self.Model, self.DV, self.data, self.Setting)
        if self.Setting['evaluation_type']=='in-sample':
            self.add_investment_constraints()
        self.add_operation_constraints()

    def solve_model(self):
        # solve the model using the specified solver
        self.Model.set_raw_parameter('Timelimit', self.Setting['wall_clock_time_lim'])
        if self.Setting['evaluation_type']=='in-sample':
                if self.Setting['Cross_over_status']==0:
                    self.Model.set_raw_parameter('Method', 2)
                    self.Model.set_raw_parameter('Crossover', 0) 
        self.Model.set_raw_parameter('Method', -1)
        self.Model.set_raw_parameter('Crossover', -1)
        self.Model.set_raw_parameter('MIPGap', self.Setting['solver_gap'])
        self.Model.set_raw_parameter('Threads', self.Setting['solver_thread_num'])
        self.Model.set_raw_parameter('LogFile', 'log.txt')
        self.Model.set_raw_parameter('LogToConsole', self.Setting['show_log_info'])
        self.Model.optimize()
        print(self.Model.get_model_attribute(poi.ModelAttribute.TerminationStatus))
        print(f'Objective value: {np.round(self.Model.get_value(self.DV.total_cost),2)}')

    def add_investment_constraints(self):
        Constraints.inv_const_num_operational_generators(self.Model, self.DV, self.data, self.Setting)
        Constraints.inv_const_land_availability_for_renewables(self.Model, self.DV, self.data, self.Setting)

    def add_operation_constraints(self):       
        Constraints.oper_const_production_limits(self.Model, self.DV, self.data, self.Setting)  
        Constraints.oper_const_ramping(self.Model, self.DV, self.data, self.Setting)  
        Constraints.oper_const_balance_equation(self.Model, self.DV, self.Con, self.data, self.Setting)
        Constraints.oper_const_flow_limits(self.Model, self.DV, self.Con, self.data, self.Setting) 
        Constraints.oper_const_storage(self.Model, self.DV, self.data, self.Setting)
        Constraints.oper_const_RPS(self.Model, self.DV, self.data, self.Setting)
    
    def get_DV_values(self):
        Get_Vals.get_variable_values(self.Model, self.DV, self.DV_values, self.data, self.Setting)

    def print_results(self, start_time):
        Print_Outcomes.publish_summary(self.DV_values, self.data, self.Setting, start_time, self.Model.get_model_attribute(poi.ModelAttribute.RelativeGap))
        Print_Outcomes.publish_extensive_form(self.DV_values, self.Duals, self.data, self.Setting)
            
    def export_detailed_results(self):
        Print_Outcomes.export_detailed_generation_results(self.DV_values, self.data, self.Setting)

    def get_constraint_duals(self):
        Get_Vals.get_dual_values(self.Model, self.Con, self.Duals, self.data, self.Setting)

    



























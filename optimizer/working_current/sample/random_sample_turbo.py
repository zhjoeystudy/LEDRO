import numpy as np
from collections import OrderedDict
import yaml
import yaml.constructor

from turbo.turbo import Turbo1
#from turbo.turbo import TurboM
import numpy as np
import torch
import math
import matplotlib
import matplotlib.pyplot as plt
#from spectre_simulator.spectre.meas_script.fully_differential_folded_cascode_meas_man import *
import globalsy

#import psutil

np.random.seed(1299)
region_mapping = {
        0: 'cut-off',
        1: 'triode',
        2: 'saturation',
        3: 'sub-threshold',
        4: 'breakdown'
        }

class OrderedDictYAMLLoader(yaml.Loader):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    """

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                                                    'expected a mapping node, but found %s' % node.id, node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

# Define the ranges
nA1_range = (10e-9, 400e-9)
nB1_range = (1, 7)
nA2_range = (10e-9, 400e-9)
nB2_range = (1, 7)
nA3_range = (10e-9, 400e-9)
nB3_range = (1, 7)
nA4_range = (10e-9, 400e-9)
nB4_range = (1, 7)
nA5_range = (10e-9, 400e-9)
nB5_range = (1, 7)
nA6_range = (10e-9, 400e-9)
nB6_range = (1, 7)
nA7_range = (10e-9, 400e-9)
nB7_range = (1, 7)
nA8_range = (10e-9, 400e-9)
nB8_range = (1, 7)
nA9_range = (10e-9, 400e-9)
nB9_range = (1, 7)
vbiasp0_range = (0, 0.8)
vbiasp1_range = (0, 0.8)
vbiasp2_range = (0, 0.8)
vbiasn0_range = (0, 0.8)
vbiasn1_range = (0, 0.8)
vbiasn2_range = (0, 0.8)
cc_range = (1e-15, 1e-11)
vcm = 0.40
vdd = 0.8
tempc = 27

lb = np.array([
nA1_range[0], 
nB1_range[0], 
nA2_range[0], 
nB2_range[0], 
nA3_range[0], 
nB3_range[0], 
nA4_range[0], 
nB4_range[0], 
nA5_range[0], 
nB5_range[0], 
nA6_range[0], 
nB6_range[0], 
#nA7_range[0], 
#nB7_range[0], 
#nA8_range[0], 
#nB8_range[0], 
#nA9_range[0], 
#nB9_range[0], 
#vbiasp0_range[0],
vbiasp1_range[0], 
vbiasp2_range[0], 
vbiasn0_range[0], 
vbiasn1_range[0], 
vbiasn2_range[0],
#cc_range[0]
])
ub = np.array([
nA1_range[1], 
nB1_range[1], 
nA2_range[1], 
nB2_range[1], 
nA3_range[1], 
nB3_range[1], 
nA4_range[1], 
nB4_range[1], 
nA5_range[1], 
nB5_range[1], 
nA6_range[1], 
nB6_range[1], 
#nA7_range[1], 
#nB7_range[1], 
#nA8_range[1], 
#nB8_range[1], 
#nA9_range[1], 
#nB9_range[1], 
#vbiasp0_range[1],
vbiasp1_range[1], 
vbiasp2_range[1], 
vbiasn0_range[1], 
vbiasn1_range[1], 
vbiasn2_range[1],
#cc_range[1]
])
# Get a random sample

CIR_YAML = "/path/to/optimizer/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"
with open(CIR_YAML, 'r') as f:
            yaml_data = yaml.load(f, OrderedDictYAMLLoader)
f.close()
params = yaml_data['params']
specs = yaml_data['target_spec']
specs_ideal = []
for spec in list(specs.values()):
             specs_ideal.append(spec)
specs_ideal = np.array(specs_ideal)
params_id = list(params.keys())
specs_id = list(specs.keys())  

#import ipdb; ipdb.set_trace()

class Levy:
    def __init__(self, dim, params_id, specs_id, specs_ideal, vcm, vdd, tempc, ub, lb):
        self.dim = dim
        self.params_id = params_id
        self.specs_id = specs_id
        self.specs_ideal = specs_ideal
        self.vcm = vcm
        self.vdd = vdd
        self.tempc = tempc
        self.ub = ub
        self.lb = lb

    def lookup(self,spec, goal_spec):
        goal_spec = [float(e) for e in goal_spec]
        spec = [float(e) for e in spec]
        spec = np.array(spec)
        goal_spec =np.array(goal_spec)

        norm_spec = (spec-goal_spec)/(np.abs(goal_spec)+np.abs(spec)) #(spec-goal_spec)/(goal_spec+spec)
        return norm_spec
    
    def reward(self,spec, goal_spec, specs_id):
        rel_specs = self.lookup(spec, goal_spec)
        pos_val = [] 
        reward = 0
        for i,rel_spec in enumerate(rel_specs):
            if(specs_id[i] == 'power' and rel_spec > 0):
                reward += np.abs(rel_spec) #/10
            elif(specs_id[i] == 'gain' and rel_spec < 0):
                reward += 3*np.abs(rel_spec) #/10
            elif (specs_id[i] != 'power' and rel_spec < 0):
                reward += np.abs(rel_spec)
        return reward ###updated


    def __call__(self, x):
        assert len(x) == self.dim
        assert x.ndim == 1
        assert np.all(x <= self.ub) and np.all(x >= self.lb)
        # w = 1 + (x - 1.0) / 4.0
        # val = np.sin(np.pi * w[0]) ** 2 + \
        #     np.sum((w[1:self.dim - 1] - 1) ** 2 * (1 + 10 * np.sin(np.pi * w[1:self.dim - 1] + 1) ** 2)) + \
        #     (w[self.dim - 1] - 1) ** 2 * (1 + np.sin(2 * np.pi * w[self.dim - 1])**2)
        CIR_YAML = "/path/to/optimizer/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"
        sim_env = OpampMeasMan(CIR_YAML) 
        sample = x
        sample[1] = round(sample[1])
        sample[3] = round(sample[3])
        sample[5] = round(sample[5])
        sample[7] = round(sample[7])
        sample[9] = round(sample[9])
        sample[11] = round(sample[11])
        # sample[13] = round(sample[13])
        # sample[15] = round(sample[15])
        # sample[17] = round(sample[17])
        sample = np.append(sample,self.vcm)
        sample = np.append(sample,self.vdd)
        sample = np.append(sample,self.tempc)
        param_val = [OrderedDict(list(zip(self.params_id,sample)))]


        cur_specs = OrderedDict(sorted(sim_env.evaluate(param_val)[0][1].items(), key=lambda k:k[0]))
        
        dict1 = OrderedDict(list(cur_specs.items())[:-5]) #all the original
        dict3 = OrderedDict(list(cur_specs.items())[-5:-4]) #region
        dict2 = OrderedDict(list(cur_specs.items())[-4:]) #remaining 

        dict2_values = list(dict2.values())
        flattened_dict2 = [item for sublist in dict2_values for item in sublist]
        dict2_nparray = np.array(flattened_dict2)

        dict3_values = list(dict3.values())
        flattened_dict3 = [item for sublist in dict3_values for item in sublist]
        dict3_nparray = np.array(flattened_dict3) #extra_ob
                
        cur_specs = np.array(list(dict1.values()))[:-1]
        dummy = cur_specs[0]
        cur_specs[0] = cur_specs[1]
        cur_specs[1] = dummy
    # f = open("/path/to/optimizer/out1.txt",'a')
    # print("cur_specs", cur_specs, file=f)
        reward1 = self.reward(cur_specs,self.specs_ideal,self.specs_id)

        if globalsy.counterrrr < 200:
                f = open("/path/to/optimizer/out1.txt",'a')
                for ordered_dict in param_val:
                    formatted_items = [f"{k}: {format(v, '.3g')}" for k, v in ordered_dict.items()]
                    print(", ".join(formatted_items), file=f)
                f.close()
        elif globalsy.counterrrr < 1200:
                f = open("/path/to/optimizer/out11.txt",'a')
                for ordered_dict in param_val:
                    formatted_items = [f"{k}: {format(v, '.3g')}" for k, v in ordered_dict.items()]
                    print(", ".join(formatted_items), file=f)
                f.close()
        elif globalsy.counterrrr < 2000:
                f = open("/path/to/optimizer/out12.txt",'a')
                for ordered_dict in param_val:
                    formatted_items = [f"{k}: {format(v, '.3g')}" for k, v in ordered_dict.items()]
                    print(", ".join(formatted_items), file=f)
                f.close()


        if globalsy.counterrrr < 200:
                f = open("/path/to/optimizer/out1.txt",'a')
                for i, j in zip(range(11),[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
                   region = region_mapping.get(int(dict3_nparray[i]), 'unknown')
                   print(f"MM{j} is in {region}", end=', ' if i < 10 else '\n', file=f)
                print("reward", format(-reward1, '.3g'), file=f)
                f.close()
                globalsy.counterrrr=globalsy.counterrrr+1
        elif globalsy.counterrrr < 1200:
                f = open("/path/to/optimizer/out11.txt",'a')
                for i, j in zip(range(11),[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
                   region = region_mapping.get(int(dict3_nparray[i]), 'unknown')
                   print(f"MM{j} is in {region}", end=', ' if i < 10 else '\n', file=f)
                print("reward", format(-reward1, '.3g'), file=f)
                f.close()
                globalsy.counterrrr=globalsy.counterrrr+1
        elif globalsy.counterrrr < 2000:
                f = open("/path/to/optimizer/out12.txt",'a')
                for i, j in zip(range(11),[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]):
                   region = region_mapping.get(int(dict3_nparray[i]), 'unknown')
                   print(f"MM{j} is in {region}", end=', ' if i < 10 else '\n', file=f)
                print("reward", format(-reward1, '.3g'), file=f)
                f.close()
                globalsy.counterrrr=globalsy.counterrrr+1
        val = reward1
       # proc=psutil.Process()
       # print(proc.open_files())
        return val

f = Levy(17, params_id, specs_id, specs_ideal, vcm, vdd, tempc, ub, lb)

turbo1 = Turbo1(
    f=f,  # Handle to objective function
    lb=lb,  # Numpy array specifying lower bounds
    ub=ub,  # Numpy array specifying upper bounds
    n_init=20,  # Number of initial bounds from an Latin hypercube design
    max_evals = 2000,  # Maximum number of evaluations
    batch_size=5,  # How large batch size TuRBO uses
    verbose=True,  # Print information from each batch
    use_ard=True,  # Set to true if you want to use ARD for the GP kernel
    max_cholesky_size=2000,  # When we switch from Cholesky to Lanczos
    n_training_steps=30,  # Number of steps of ADAM to learn the hypers
    min_cuda=10.40,  # Run on the CPU for small datasets
    device="cpu",  # "cpu" or "cuda"
    dtype="float32",  # float64 or float32
)

turbo1.optimize()

X = turbo1.X  # Evaluated points
fX = turbo1.fX  # Observed values
ind_best = np.argmin(fX)
f_best, x_best = fX[ind_best], X[ind_best, :]

print("Best value found:\n\tf(x) = %.3f\nObserved at:\n\tx = %s" % (f_best, np.around(x_best, 3)))

# turbo_m = TurboM(
#     f=f,  # Handle to objective function
#     lb=lb,  # Numpy array specifying lower bounds
#     ub=ub,  # Numpy array specifying upper bounds
#     n_init=10,  # Number of initial bounds from an Symmetric Latin hypercube design
#     max_evals=300,  # Maximum number of evaluations
#     n_trust_regions=5,  # Number of trust regions
#     batch_size=10,  # How large batch size TuRBO uses
#     verbose=True,  # Print information from each batch
#     use_ard=True,  # Set to true if you want to use ARD for the GP kernel
#     max_cholesky_size=200,  # When we switch from Cholesky to Lanczos
#     n_training_steps=50,  # Number of steps of ADAM to learn the hypers
#     min_cuda=10.40,  # Run on the CPU for small datasets
#     device="cpu",  # "cpu" or "cuda"
#     dtype="float32",  # float64 or float32
# )

# turbo_m.optimize()

# X = turbo_m.X  # Evaluated points
# fX = turbo_m.fX  # Observed values
# ind_best = np.argmin(fX)
# f_best, x_best = fX[ind_best], X[ind_best, :]

# print("Best value found:\n\tf(x) = %.3f\nObserved at:\n\tx = %s" % (f_best, np.around(x_best, 3)))




import numpy as np
from collections import OrderedDict
import yaml
import yaml.constructor
from turbo.turbo import Turbo1
import numpy as np
import torch
import math
import matplotlib.pyplot as plt
import globalsy

np.random.seed(1299)

# Mapping for transistor operating region logging
region_mapping = {
    0: 'cut-off',
    1: 'triode',
    2: 'saturation',
    3: 'sub-threshold',
    4: 'breakdown'
}

# Custom YAML Loader to preserve order
class OrderedDictYAMLLoader(yaml.Loader):
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
            raise yaml.constructor.ConstructorError(
                None, None,
                f'expected a mapping node, but found {node.id}', node.start_mark
            )
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


# Define parameter ranges
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
vbiasp1_range = (0, 0.8)
vbiasp2_range = (0, 0.8)
vbiasn0_range = (0, 0.8)
vbiasn1_range = (0, 0.8)
vbiasn2_range = (0, 0.8)

vcm = 0.40
vdd = 0.8
tempc = 27

# Bounds
lb = np.array([
    nA1_range[0], nB1_range[0],
    nA2_range[0], nB2_range[0],
    nA3_range[0], nB3_range[0],
    nA4_range[0], nB4_range[0],
    nA5_range[0], nB5_range[0],
    nA6_range[0], nB6_range[0],
    vbiasp1_range[0], vbiasp2_range[0],
    vbiasn0_range[0], vbiasn1_range[0], vbiasn2_range[0]
])

ub = np.array([
    nA1_range[1], nB1_range[1],
    nA2_range[1], nB2_range[1],
    nA3_range[1], nB3_range[1],
    nA4_range[1], nB4_range[1],
    nA5_range[1], nB5_range[1],
    nA6_range[1], nB6_range[1],
    vbiasp1_range[1], vbiasp2_range[1],
    vbiasn0_range[1], vbiasn1_range[1], vbiasn2_range[1]
])

# Load specs from YAML
CIR_YAML = "/path/to/optimizer/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"
with open(CIR_YAML, 'r') as f:
    yaml_data = yaml.load(f, OrderedDictYAMLLoader)
params = yaml_data['params']
specs = yaml_data['target_spec']
specs_ideal = np.array([float(v) for v in specs.values()])
params_id = list(params.keys())
specs_id = list(specs.keys())

# Objective function wrapper
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

    def lookup(self, spec, goal_spec):
        spec = np.array([float(s) for s in spec])
        goal_spec = np.array([float(g) for g in goal_spec])
        norm_spec = (spec - goal_spec) / (np.abs(goal_spec) + np.abs(spec))
        return norm_spec

    def reward(self, spec, goal_spec, specs_id):
        rel_specs = self.lookup(spec, goal_spec)
        reward = 0
        for i, rel_spec in enumerate(rel_specs):
            if specs_id[i] == 'power' and rel_spec > 0:
                reward += np.abs(rel_spec)
            elif specs_id[i] == 'gain' and rel_spec < 0:
                reward += 3 * np.abs(rel_spec)
            elif specs_id[i] != 'power' and rel_spec < 0:
                reward += np.abs(rel_spec)
        return reward

    def __call__(self, x):
        assert len(x) == self.dim
        assert x.ndim == 1
        assert np.all(x <= self.ub) and np.all(x >= self.lb)

        sample = x.copy()

        # Round discrete parameters (multipliers)
        sample[1] = round(sample[1])   # nB1
        sample[3] = round(sample[3])   # nB2
        sample[5] = round(sample[5])   # nB3
        sample[7] = round(sample[7])   # nB4
        sample[9] = round(sample[9])   # nB5
        sample[11] = round(sample[11]) # nB6

        # Append fixed values
        sample = np.append(sample, self.vcm)
        sample = np.append(sample, self.vdd)
        sample = np.append(sample, self.tempc)

        # Simulate
        CIR_YAML = "/path/to/optimizer/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"
        sim_env = OpampMeasMan(CIR_YAML)
        param_val = [OrderedDict(zip(self.params_id, sample))]

        cur_specs = OrderedDict(sorted(sim_env.evaluate(param_val)[0][1].items(), key=lambda k: k[0]))
        dict1 = OrderedDict(list(cur_specs.items())[:-5])  # main specs
        dict3 = OrderedDict(list(cur_specs.items())[-5:-4])  # regions
        dict2 = OrderedDict(list(cur_specs.items())[-4:])  # extra info

        # Flatten dicts
        dict2_values = [item for sublist in dict2.values() for item in sublist]
        dict2_nparray = np.array(dict2_values)
        dict3_values = [item for sublist in dict3.values() for item in sublist]
        dict3_nparray = np.array(dict3_values)

        cur_specs = np.array(list(dict1.values()))[:-1]
        cur_specs[0], cur_specs[1] = cur_specs[1], cur_specs[0]  # swap gain and power

        reward1 = self.reward(cur_specs, self.specs_ideal, self.specs_id)

        # Logging
        if globalsy.counterrrr < 200:
            filename = "/path/to/optimizer/out1.txt"
        elif globalsy.counterrrr < 1200:
            filename = "/path/to/optimizer/out11.txt"
        else:
            filename = "/path/to/optimizer/out12.txt"

        with open(filename, 'a') as f:
            for ordered_dict in param_val:
                formatted_items = [f"{k}: {format(v, '.3g')}" for k, v in ordered_dict.items()]
                print(", ".join(formatted_items), file=f)

            for i, j in zip(range(11), range(11)):
                region = region_mapping.get(int(dict3_nparray[i]), 'unknown')
                print(f"MM{j} is in {region}", end=', ' if i < 10 else '\n', file=f)

            print("reward", format(-reward1, '.3g'), file=f)

        globalsy.counterrrr += 1
        return reward1


# Instantiate objective function
f = Levy(17, params_id, specs_id, specs_ideal, vcm, vdd, tempc, ub, lb)

# Configure and run optimizer
turbo1 = Turbo1(
    f=f,
    lb=lb,
    ub=ub,
    n_init=20,
    max_evals=2000,
    batch_size=5,
    verbose=True,
    use_ard=True,
    max_cholesky_size=2000,
    n_training_steps=30,
    min_cuda=10.40,
    device="cpu",
    dtype="float32",
)

turbo1.optimize()

# Get best result
X = turbo1.X
fX = turbo1.fX
ind_best = np.argmin(fX)
f_best, x_best = fX[ind_best], X[ind_best, :]

print("Best value found:\n\tf(x) = %.3f\nObserved at:\n\tx = %s" % (f_best, np.around(x_best, 3)))
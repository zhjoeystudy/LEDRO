import numpy as np
from collections import OrderedDict
import yaml
import yaml.constructor
import argparse
import importlib

from turbo.turbo import Turbo1
import globalsy

np.random.seed(1299)

region_mapping = {
    0: 'cut-off', 1: 'triode', 2: 'saturation', 3: 'sub-threshold', 4: 'breakdown'
}


class OrderedDictYAMLLoader(yaml.Loader):
    """A YAML loader that loads mappings into ordered dictionaries."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(None, None,
                                                    f'expected a mapping node, but found {node.id}', node.start_mark)
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


def load_config(yaml_path):
    """Loads the circuit configuration from the specified YAML file."""
    with open(yaml_path, 'r') as f:
        yaml_data = yaml.load(f, OrderedDictYAMLLoader)

    params = yaml_data['params']
    target_specs = yaml_data['target_spec']

    # Extract lower and upper bounds from the params section
    # This automatically handles which parameters are included.
    lb = np.array([p[0] for p in params.values() if p[0] != p[1]])
    ub = np.array([p[1] for p in params.values() if p[0] != p[1]])

    specs_ideal = np.array([s[0] for s in target_specs.values()])

    # Identify which parameters are variable (to be optimized) vs. fixed
    variable_params_id = [k for k, v in params.items() if v[0] != v[1]]
    fixed_params = {k: v[0] for k, v in params.items() if v[0] == v[1]}

    return params, target_specs, lb, ub, specs_ideal, variable_params_id, fixed_params


class ObjectiveFunction:
    def __init__(self, dim, variable_params_id, specs_id, specs_ideal, fixed_params, meas_class_instance, ub, lb):
        self.dim = dim
        self.variable_params_id = variable_params_id
        self.specs_id = specs_id
        self.specs_ideal = specs_ideal
        self.fixed_params = fixed_params
        self.sim_env = meas_class_instance
        self.ub = ub
        self.lb = lb

    def lookup(self, spec, goal_spec):
        spec = np.array([float(e) for e in spec if e is not None])
        goal_spec = np.array([float(e) for e in goal_spec if e is not None])
        return (spec - goal_spec) / (np.abs(goal_spec) + np.abs(spec))

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

        # Combine sampled variables with fixed ones from the YAML
        param_dict = OrderedDict(zip(self.variable_params_id, x))
        param_dict.update(self.fixed_params)

        # Round any parameters that are meant to be integers (e.g., finger numbers)
        for key in param_dict:
            if 'nB' in key:  # Example: assumes finger numbers contain 'nB'
                param_dict[key] = round(param_dict[key])

        param_val = [param_dict]

        # Call the evaluate method from the measurement class instance
        raw_specs = self.sim_env.evaluate(param_val)[0][1]

        # Process results... (This logic is specific to the original script)
        # Note: This may need adjustment if your spec dictionary changes.
        spec_values = [raw_specs.get(key) for key in self.specs_id]
        reward_val = self.reward(spec_values, self.specs_ideal, self.specs_id)

        # File logging logic...
        # ...

        return reward_val


def main(args):
    """Main execution function."""

    # Load configuration from the specified YAML file
    params, specs, lb, ub, specs_ideal, var_ids, fixed_params = load_config(args.yaml_file)
    specs_id = list(specs.keys())

    # Dynamically import the measurement module and instantiate the class
    meas_module = importlib.import_module(args.meas_module)
    meas_class = getattr(meas_module, args.meas_class)
    sim_env_instance = meas_class(args.yaml_file)

    # Initialize the objective function
    f = ObjectiveFunction(
        dim=len(lb),
        variable_params_id=var_ids,
        specs_id=specs_id,
        specs_ideal=specs_ideal,
        fixed_params=fixed_params,
        meas_class_instance=sim_env_instance,
        ub=ub,
        lb=lb
    )

    # Setup and run TuRBO
    turbo1 = Turbo1(
        f=f,  # Handle to objective function
        lb=lb,  # Numpy array specifying lower bounds
        ub=ub,  # Numpy array specifying upper bounds
        n_init=20,  # Number of initial bounds from an Latin hypercube design
        max_evals=2000,  # Maximum number of evaluations
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

    X = turbo1.X
    fX = turbo1.fX
    ind_best = np.argmin(fX)
    f_best, x_best = fX[ind_best], X[ind_best, :]

    print(f"Best value found:\n\tf(x) = {f_best:.3f}\nObserved at:\n\tx = {np.around(x_best, 3)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TuRBO optimization for an op-amp.")
    parser.add_argument(
        '--yaml_file',
        type=str,
        required=True,
        help="Path to the YAML configuration file (e.g., 'design1.yaml')."
    )
    parser.add_argument(
        '--meas_module',
        type=str,
        required=True,
        help="Name of the measurement module (e.g., 'folded_cascode_meas')."
    )
    parser.add_argument(
        '--meas_class',
        type=str,
        required=True,
        help="Name of the measurement class within the module (e.g., 'FoldedCascodeMeas')."
    )

    args = parser.parse_args()
    main(args)
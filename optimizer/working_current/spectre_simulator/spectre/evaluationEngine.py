import yaml
import numpy as np
from .design import Design
from .wrapper import NgSpiceWrapper

class EvaluationEngine(object):

    def __init__(self, yaml_fname):
        with open(yaml_fname, 'r') as f:
            self.ver_specs = yaml.load(f, Loader=yaml.Loader)

        self.spec_range = self.ver_specs['spec_range']
        params = self.ver_specs['params']

        self.params_vec = {k: np.arange(v[0], v[1], v[2]).tolist() for k, v in params.items()}

        self.measurement_specs = self.ver_specs['measurement']
        tbs = self.measurement_specs['testbenches']
        self.netlist_module_dict = {}
        for tb_kw, tb_val in tbs.items():
            # This assumes NgSpiceWrapper is the desired simulation engine
            self.netlist_module_dict[tb_kw] = NgSpiceWrapper(tb_val)

    def evaluate(self, design_list, debug=True):
        results = []
        # Assumes a single testbench for simplicity
        netlist_name, netlist_module = list(self.netlist_module_dict.items())[0]

        for design in design_list:
            try:
                # Get the actual parameter values from the indices in the design
                state_dict = {key: self.params_vec[key][design[i]] for i, key in enumerate(self.params_vec.keys())}

                # Run the simulation for the single design
                state, specs, info = netlist_module._create_design_and_simulate(state_dict, dsn_name=design.id)

                # Here you would add your logic to check if the design is valid
                # and calculate its cost based on the returned 'specs'.
                # For this example, we'll just attach the results.
                result = {
                    'valid': True,
                    'cost': 0,  # Placeholder for cost calculation
                    **specs
                }

            except Exception as e:
                if debug:
                    raise e
                result = {'valid': False}
                print(f"Evaluation failed for design {design.id}: {getattr(e, 'message', str(e))}")

            results.append(result)

        # Clean up the simulation directory after all evaluations are done
        netlist_module.cleanup()

        return results

    # Other methods like generate_data_set, cost_fun, etc. would go here.
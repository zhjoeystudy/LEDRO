import os
import shutil
import subprocess
import random
from jinja2 import Environment, FileSystemLoader
from multiprocessing.dummy import Pool as ThreadPool
import importlib

# Import from local project files
from .analysis import AcFileParser, DcOpParser
from .design import Design
from .ngspice_adapter import NgSpiceAdapter


class NgSpiceWrapper:
    """
    A wrapper to automate ngspice simulations.

    This class handles the creation of simulation netlists from templates,
    running the ngspice simulation in batch mode, and parsing the resulting
    text-based output files.
    """

    def __init__(self, tb_dict):
        """
        Initializes the NgSpiceWrapper.

        :param tb_dict: A dictionary containing testbench configuration, including
                        'netlist_template', 'tb_module' for post-processing, etc.
        """
        # Set up paths and import the post-processing function
        netlist_loc = tb_dict['netlist_template']
        if not os.path.isabs(netlist_loc):
            netlist_loc = os.path.abspath(netlist_loc)

        pp_module = importlib.import_module(tb_dict['tb_module'])
        pp_class = getattr(pp_module, tb_dict['tb_class'])
        self.post_process = getattr(pp_class, tb_dict['post_process_function'])
        self.tb_params = tb_dict['tb_params']

        # Configure simulation directories
        self.root_dir = os.environ.get('BASE_TMP_DIR')
        if not self.root_dir:
            raise EnvironmentError('BASE_TMP_DIR environment variable is not set.')

        self.num_process = int(os.environ.get('NUM_PROCESS', 1))

        _, dsn_netlist_fname = os.path.split(netlist_loc)
        self.base_design_name = os.path.splitext(dsn_netlist_fname)[0] + str(random.randint(0, 10000))
        self.gen_dir = os.path.join(self.root_dir, "designs_" + self.base_design_name)
        os.makedirs(self.gen_dir, exist_ok=True)

        # Set up Jinja2 template environment
        file_loader = FileSystemLoader(os.path.dirname(netlist_loc))
        self.jinja_env = Environment(loader=file_loader)
        self.template = self.jinja_env.get_template(dsn_netlist_fname)

    def _get_design_name(self, state):
        """Creates a unique folder name for a given parameter set."""
        fname = self.base_design_name
        for value in state.values():
            fname += "_" + str(round(value, 2))
        return fname

    def _create_design(self, state, dsn_name):
        """Creates the simulation folder and the 'ac.cir' netlist file."""
        output = self.template.render(**state)
        design_folder = os.path.join(self.gen_dir, dsn_name)
        os.makedirs(design_folder, exist_ok=True)
        fpath = os.path.join(design_folder, 'ac.cir')
        with open(fpath, 'w') as f:
            f.write(output)
        return design_folder, fpath

    def _simulate(self, fpath):
        """Runs the ngspice simulation with control blocks in the specified design folder."""
        log_file = os.path.join(os.path.dirname(fpath), 'sim_log.txt')
        design_folder = os.path.dirname(fpath)
        
        # Use ngspice with echo quit to automatically exit after control blocks
        command = ['bash', '-c', 'echo "quit" | ngspice ac.cir']

        with open(log_file, 'w') as file1:
            exit_code = subprocess.call(command, cwd=design_folder, stdout=file1, stderr=subprocess.STDOUT)

        # Return 1 for error, 0 for success
        return 1 if exit_code != 0 else 0


    def _parse_result(self, design_folder):
        """
        Uses the NgSpiceAdapter to parse ngspice outputs and convert them to the format
        expected by measurement scripts.
        """
        return NgSpiceAdapter.parse_and_adapt(design_folder)

    def _create_design_and_simulate(self, state, dsn_name=None, verbose=False):
        """A complete pipeline for a single design point."""
        if dsn_name is None:
            dsn_name = self._get_design_name(state)
        else:
            dsn_name = str(dsn_name)

        design_folder, fpath = self._create_design(state, dsn_name)
        info = self._simulate(fpath)
        results = self._parse_result(design_folder)

        if self.post_process:
            specs = self.post_process(results, self.tb_params)
            return state, specs, info

        return state, results, info

    def run(self, states, design_names=None, verbose=False):
        """
        Runs simulations for a list of states in parallel.

        :param states: A list of parameter dictionaries.
        :param design_names: A list of unique names for each design.
        :return: A list of tuples, with each containing (state, specs, info).
        """
        if design_names is None:
            design_names = [None] * len(states)

        pool = ThreadPool(processes=self.num_process)
        arg_list = [(state, dsn_name, verbose) for (state, dsn_name) in zip(states, design_names)]
        specs = pool.starmap(self._create_design_and_simulate, arg_list)
        pool.close()

        # Clean up the generated simulation directory
        shutil.rmtree(self.gen_dir)

        return specs
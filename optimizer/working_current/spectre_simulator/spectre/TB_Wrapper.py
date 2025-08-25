# run_testbench.py

import os
import shutil
import sys

# Import the main wrapper class from your wrapper.py file
from wrapper import NgSpiceWrapper


def create_test_files(base_dir):
    """Creates the necessary dummy files for the test in a flat directory."""
    # 1. Create a dummy netlist template
    template_path = os.path.join(base_dir, "ac_template.cir")
    template_content = """
* AC Testbench Template
Vinput vp 0 DC 0V AC 1V
R1 vout 0 {{ R1 }}k
.AC DEC 10 1k 100G
.PRINT AC V(vout) > ac_out.txt
.PRINT AC V(vp) > ac_vp.txt
.PRINT AC V(vn) > ac_vn.txt
.END
"""
    with open(template_path, 'w') as f:
        f.write(template_content)

    # 2. Create a dummy post-processing module
    module_path = os.path.join(base_dir, "my_post_process.py")
    module_content = """
class MyTB:
    @staticmethod
    def process_specs(results, params):
        print(f"Post-processing data for test param: {params.get('gain_min')}")
        vout_points = len(results.get('out', []))
        vn_points = len(results.get('vn', []))
        return {'vout_data_points': vout_points, 'vn_data_points': vn_points}
"""
    with open(module_path, 'w') as f:
        f.write(module_content)

    return template_path


def main_test():
    """Main test function to orchestrate the testbench."""
    TEST_DIR = "_test_environment"

    # Clean up previous runs
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR, exist_ok=True)

    # Set the environment variable that NgSpiceWrapper expects
    os.environ['BASE_TMP_DIR'] = os.path.abspath(TEST_DIR)

    # Create the necessary template and module files inside the temp directory
    template_path = create_test_files(TEST_DIR)

    # Add the temporary test directory to sys.path so its modules can be imported
    sys.path.insert(0, os.path.abspath(TEST_DIR))

    # --- Test Configuration ---
    tb_config = {
        'netlist_template': template_path,
        'tb_module': 'my_post_process',  # No 'modules.' prefix needed now
        'tb_class': 'MyTB',
        'post_process_function': 'process_specs',
        'tb_params': {'gain_min': 50}
    }

    # --- Mocking the Simulation Step ---
    def mock_simulate(self, fpath):
        print("--- MOCK SIMULATION (Skipping actual ngspice call) ---")
        design_folder = os.path.dirname(fpath)
        with open(os.path.join(design_folder, 'ac_out.txt'), 'w') as f:
            f.write("0\t1.0e3\t1.50, -0.1\n1\t2.0e3\t1.45, -0.2\n")
        with open(os.path.join(design_folder, 'ac_vn.txt'), 'w') as f:
            f.write("0\t1.0e3\t0.0, 0.0\n")
        with open(os.path.join(design_folder, 'ac_vp.txt'), 'w') as f:
            f.write("0\t1.0e3\t1.0, 0.0\n")
        print("--- MOCK: Dummy ac_*.txt files created. ---")
        return 0  # Return 0 for success

    NgSpiceWrapper._simulate = mock_simulate

    # --- Running the Testbench ---
    try:
        print("--- Initializing NgSpiceWrapper ---")
        wrapper = NgSpiceWrapper(tb_config)

        design_params = [{'R1': 10}]

        print("\n--- Calling wrapper.run() for 1 design ---")
        results = wrapper.run(design_params)

        # --- Verifying the Results ---
        print("\n--- TESTBENCH RESULTS ---")
        if results:
            state, specs, info = results[0]
            print(f"Input State: {state}")
            print(f"Processed Specs: {specs}")
            print(f"Simulation Info: {info}")

            assert info == 0
            assert specs['vout_data_points'] == 2
            assert specs['vn_data_points'] == 1
            print("\n✅ Test Passed!")
        else:
            print("\n❌ Test FAILED: No results returned.")

    except Exception as e:
        print(f"\n❌ Test FAILED with an exception: {e}")
        raise  # Re-raise exception to see full traceback
    finally:
        # --- Cleanup ---
        sys.path.pop(0)  # Remove the temporary directory from the path
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
        print("\n--- Test environment cleaned up. ---")


if __name__ == "__main__":
    main_test()
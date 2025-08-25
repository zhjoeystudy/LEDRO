import numpy as np
import os
import re

class NgSpiceParser:
    @classmethod
    def parse(cls, raw_folder):
        """
        Parses all relevant files in raw_folder and returns structured results.
        Assumes:
            - ac_out.txt contains AC analysis data
            - dc_out.txt contains DC operating point (optional)
        """
        folder_path = os.path.abspath(raw_folder)
        data = dict()

        # Parse AC output
        ac_file = os.path.join(folder_path, "ac_out.txt")
        if os.path.exists(ac_file):
            try:
                ac_data = cls._parse_ac_file(ac_file)
                data["ac"] = ac_data
            except Exception as e:
                print(f"Failed to parse AC file: {e}")

        # Optional: Parse DC operating point
        dc_file = os.path.join(folder_path, "dc_out.txt")
        if os.path.exists(dc_file):
            try:
                dc_data = cls._parse_dc_file(dc_file)
                data["dcOp"] = dc_data
            except Exception as e:
                print(f"Failed to parse DC file: {e}")

        return data

    @classmethod
    def _parse_ac_file(cls, file_path):
        """
        Parses NgSpice AC simulation output file into a dictionary.
        Example line:
        frequency        v(vp)            v(vn)            v(vout)
        1.000000e+03     9.000000e-01     9.000000e-01     1.118697e+00
        """
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Find header line
        header_line = None
        data_lines = []
        for line in lines:
            if line.strip().lower().startswith("frequency"):
                header_line = line.strip()
            elif re.match(r'[\d\.\+\-eE]+', line):
                data_lines.append(line)

        if not header_line:
            raise ValueError("No valid header found in AC file")

        # Split header
        headers = header_line.split()
        num_columns = len(headers)

        # Initialize arrays
        parsed_data = {}
        for h in headers:
            parsed_data[h] = []

        # Parse each line
        for line in data_lines:
            values = list(map(float, line.strip().split()))
            for i, h in enumerate(headers):
                parsed_data[h].append(values[i])

        # Convert lists to NumPy arrays
        for key in parsed_data:
            parsed_data[key] = np.array(parsed_data[key])

        return parsed_data

    @classmethod
    def _parse_dc_file(cls, file_path):
        """
        Parses NgSpice DC operating point output into a flat dictionary.
        Example line:
        net1 = 1.326592e+00
        """
        dc_data = {}
        with open(file_path, "r") as f:
            for line in f:
                match = re.match(r'^([^=]+)=\s*([^\s]+)', line.strip())
                if match:
                    key = match.group(1).strip()
                    val = float(match.group(2))
                    dc_data[key] = val
        return dc_data
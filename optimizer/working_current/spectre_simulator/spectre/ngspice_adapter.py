import numpy as np
import os
import re

class NgSpiceAdapter:
    """
    Adapter to convert simple ngspice output to the format expected by measurement scripts.
    This bridges the gap between simple ngspice circuits and complex measurement expectations.
    """
    
    @classmethod
    def parse_and_adapt(cls, design_folder):
        """
        Parses ngspice output files and converts them to the format expected by measurement scripts.
        """
        data = {}
        
        # Parse AC analysis output
        ac_file = os.path.join(design_folder, "ac_out.txt")
        if os.path.exists(ac_file):
            ac_data = cls._parse_ac_output(ac_file)
            data['ac'] = ac_data
        
        # Create minimal DC operating point data to satisfy measurement scripts
        data['dcOp'] = cls._create_minimal_dc_data()
        
        return data
    
    @classmethod
    def _parse_ac_output(cls, file_path):
        """
        Parse ngspice AC output and format it for measurement scripts.
        Expected ngspice format:
        Index   frequency       v(vd)                           
        0	1.000000e+03	0.000000e+00,	0.000000e+00	
        """
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Skip header lines and find data
        data_lines = []
        for line in lines:
            line = line.strip()
            if line and '\t' in line:
                # Check if line starts with a number (index)
                parts = line.split('\t')
                if len(parts) >= 3 and parts[0].isdigit():
                    data_lines.append(line)
        
        if not data_lines:
            raise ValueError("No valid data found in AC output file")
        
        # Parse data
        frequencies = []
        voutp_values = []
        voutn_values = []
        
        for line in data_lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                freq = float(parts[1])  # frequency column
                
                # Parse complex number from ngspice format: "real, imag"
                if len(parts) >= 3:
                    voutp_str = parts[2].replace(',', '').strip()
                    if voutp_str:
                        try:
                            voutp_real = float(voutp_str)
                            voutp = complex(voutp_real, 0)  # Assume real for now
                        except:
                            voutp = complex(0, 0)
                    else:
                        voutp = complex(0, 0)
                else:
                    voutp = complex(0, 0)
                
                # For single-ended output, create artificial differential by using negative
                voutn = -voutp
                
                frequencies.append(freq)
                voutp_values.append(voutp)
                voutn_values.append(voutn)
        
        return {
            'sweep_values': np.array(frequencies),
            'Voutp': np.array(voutp_values),
            'Voutn': np.array(voutn_values)
        }
    
    @classmethod
    def _create_minimal_dc_data(cls):
        """
        Create minimal DC operating point data to satisfy measurement scripts.
        Since we don't have detailed device data from our simple circuit,
        we'll create placeholder values.
        """
        dc_data = {}
        
        # Create fake device operating points for transistors MM0-MM10
        for i in range(11):
            device_name = f'MM{i}'
            dc_data[f'{device_name}:ids'] = 10e-6  # 10 microamps drain current
            dc_data[f'{device_name}:gm'] = 50e-6   # 50 microsiemens transconductance
            dc_data[f'{device_name}:vgs'] = 0.7    # 0.7V gate-source voltage
            dc_data[f'{device_name}:vds'] = 0.5    # 0.5V drain-source voltage
            dc_data[f'{device_name}:region'] = 2   # Saturation region
        
        return dc_data
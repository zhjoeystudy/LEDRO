from matplotlib import pyplot as plt
from scipy.interpolate import interp1d
from scipy.optimize import root_scalar

import numpy as np
import os
import re
from scipy.interpolate import interp1d
from scipy.optimize import root_scalar


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

        # Find the header and split the lines into different sections
        section_data = {"v(vp)": [], "v(vn)": [], "v(vout)": []}
        section = None
        for line in lines:
            # Skip separator lines, comments, or any non-numeric lines
            if line.strip() == "" or "----" in line or line.startswith("*") or not re.match(r'[\d\.\+\-eE]+', line):
                continue

            # Process data line
            values = list(map(str.strip, line.strip().split()))

            if len(values) >= 7:  # Ensure valid data line (frequency + 3 voltage values with real and imaginary parts)
                freq = values[0]
                v_vp_real, v_vp_imag = float(values[1].rstrip(',')), float(values[2].rstrip(','))
                v_vn_real, v_vn_imag = float(values[3].rstrip(',')), float(values[4].rstrip(','))
                v_vout_real, v_vout_imag = float(values[5].rstrip(',')), float(values[6].rstrip(','))

                # Store the data in the correct section
                section_data["v(vp)"].append(v_vp_real + 1j * v_vp_imag)
                section_data["v(vn)"].append(v_vn_real + 1j * v_vn_imag)
                section_data["v(vout)"].append(v_vout_real + 1j * v_vout_imag)

        # Convert the section data to numpy arrays
        freq = np.array([line.split()[0] for line in lines if line.strip() and re.match(r'[\d\.\+\-eE]+', line)])
        for key in section_data:
            section_data[key] = np.array(section_data[key])

        return {
            "frequency": freq,
            "v(vp)": section_data["v(vp)"],
            "v(vn)": section_data["v(vn)"],
            "v(vout)": section_data["v(vout)"]
        }

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


# === Main Processing ===

if __name__ == "__main__":
    # Folder path where the output files are located
    raw_folder = ""  # Update this with your folder path

    # Parse the AC data
    data = NgSpiceParser.parse(raw_folder)

    if "ac" in data:
        ac_data = data["ac"]
        freq = ac_data["frequency"]
        Vp = ac_data["v(vp)"]
        Vn = ac_data["v(vn)"]
        Vout = ac_data["v(vout)"]

        # Check the lengths of the arrays
        print(f"Length of freq: {len(freq)}")
        print(f"Length of Vp: {len(Vp)}")
        print(f"Length of Vn: {len(Vn)}")
        print(f"Length of Vout: {len(Vout)}")

        # Ensure the arrays have the same length
        if len(freq) == len(Vp) == len(Vn) == len(Vout):
            # Compute differential input
            Vin_diff = Vp - Vn

            # Compute gain and phase
            gain = 20 * np.log10(np.abs(Vout / Vin_diff))
            phase = np.angle(Vout / Vin_diff, deg=True)

            # Find Unity Gain Bandwidth (UGBW)
            gain_interp = interp1d(freq, gain, kind='linear', fill_value="extrapolate")
            ugbw = root_scalar(lambda f: gain_interp(f) - 0, bracket=[freq[0], freq[-1]], method='brentq').root

            # Find Phase Margin
            phase_interp = interp1d(freq, phase, kind='linear')
            phase_margin = phase_interp(ugbw)

            print(f"DC Gain: {gain[0]:.2f} dB")
            print(f"Unity Gain Bandwidth: {ugbw:.2e} Hz")
            print(f"Phase Margin: {phase_margin:.2f}°")

            # Plotting the results
            plt.figure(figsize=(12, 6))

            # Plot Gain vs Frequency
            plt.subplot(211)
            plt.semilogx(freq, gain)
            plt.title("Gain vs Frequency")
            plt.ylabel("Gain (dB)")
            plt.grid(True)

            # Plot Phase vs Frequency
            plt.subplot(212)
            plt.semilogx(freq, phase)
            plt.title("Phase vs Frequency")
            plt.ylabel("Phase (deg)")
            plt.xlabel("Frequency (Hz)")
            plt.grid(True)

            plt.tight_layout()
            plt.show()

        else:
            print("Error: Mismatched lengths between freq and voltage data arrays.")
    else:
        print("Error: AC data not found. Please check the input files.")

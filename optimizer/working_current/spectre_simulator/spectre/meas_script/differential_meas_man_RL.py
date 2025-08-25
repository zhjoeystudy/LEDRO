from ..evaluationEngine import EvaluationEngine
import numpy as np
import pdb
import IPython
import scipy.interpolate as interp
import scipy.optimize as sciopt
import matplotlib.pyplot as plt
import globalsy
class OpampMeasMan(EvaluationEngine):

    def __init__(self, yaml_fname):
        EvaluationEngine.__init__(self, yaml_fname)

    def get_specs(self, results_dict, params):
        specs_dict = dict()
        ac_dc = results_dict['ac_dc']
        for _, res, _ in ac_dc:
            specs_dict = res
        return specs_dict

    def compute_penalty(self, spec_nums, spec_kwrd):
        if type(spec_nums) is not list:
            spec_nums = [spec_nums]
        penalties = []
        for spec_num in spec_nums:
            penalty = 0
            spec_min, spec_max, w = self.spec_range[spec_kwrd]
            if spec_max is not None:
                if spec_num > spec_max:
                    penalty += w * abs(spec_num - spec_max) / abs(spec_num)
            if spec_min is not None:
                if spec_num < spec_min:
                    penalty += w * abs(spec_num - spec_min) / abs(spec_min)
            penalties.append(penalty)
        return penalties

class ACTB(object):

    @classmethod
    def process_ac(cls, results, params):
        ac_result = results['ac']
        dc_results = results['dcOp']
        vout = ac_result['Voutp']-ac_result['Voutn']
        freq = ac_result['sweep_values']

        ids_MM = []
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM0:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM1:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM2:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM3:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM4:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM5:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM6:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM7:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM8:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM9:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM10:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM11:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM12:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM13:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM14:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM15:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM16:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM17:ids'])))
        #ids_MM.append(float('%.3g' % np.abs(dc_results['MM18:ids'])))
        gm_MM = []
        #gm_MM.append(float('%.3g' % dc_results['MM0:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM1:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM2:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM3:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM4:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM5:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM6:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM7:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM8:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM9:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM10:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM11:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM12:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM13:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM14:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM15:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM16:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM17:gm']))
        #gm_MM.append(float('%.3g' % dc_results['MM18:gm']))
        vgs_MM = []
        #vgs_MM.append(round(dc_results['MM0:vgs'],3))
        #vgs_MM.append(round(dc_results['MM1:vgs'],3))
        #vgs_MM.append(round(dc_results['MM2:vgs'],3))
        #vgs_MM.append(round(dc_results['MM3:vgs'],3))
        #vgs_MM.append(round(dc_results['MM4:vgs'],3))
        #vgs_MM.append(round(dc_results['MM5:vgs'],3))
        #vgs_MM.append(round(dc_results['MM6:vgs'],3))
        #vgs_MM.append(round(dc_results['MM7:vgs'],3))
        #vgs_MM.append(round(dc_results['MM8:vgs'],3))
        #vgs_MM.append(round(dc_results['MM9:vgs'],3))
        #vgs_MM.append(round(dc_results['MM10:vgs'],3))
        #vgs_MM.append(round(dc_results['MM11:vgs'],3))
        #vgs_MM.append(round(dc_results['MM12:vgs'],3))
        #vgs_MM.append(round(dc_results['MM13:vgs'],3))
        #vgs_MM.append(round(dc_results['MM14:vgs'],3))
        #vgs_MM.append(round(dc_results['MM15:vgs'],3))
        #vgs_MM.append(round(dc_results['MM16:vgs'],3))
        #vgs_MM.append(round(dc_results['MM17:vgs'],3))
        #vgs_MM.append(round(dc_results['MM18:vgs'],3))
        vds_MM = []
        #vds_MM.append(round(dc_results['MM0:vds'],3))
        #vds_MM.append(round(dc_results['MM1:vds'],3))
        #vds_MM.append(round(dc_results['MM2:vds'],3))
        #vds_MM.append(round(dc_results['MM3:vds'],3))
        #vds_MM.append(round(dc_results['MM4:vds'],3))
        #vds_MM.append(round(dc_results['MM5:vds'],3))
        #vds_MM.append(round(dc_results['MM6:vds'],3))
        #vds_MM.append(round(dc_results['MM7:vds'],3))
        #vds_MM.append(round(dc_results['MM8:vds'],3))
        #vds_MM.append(round(dc_results['MM9:vds'],3))
        #vds_MM.append(round(dc_results['MM10:vds'],3))
        #vds_MM.append(round(dc_results['MM11:vds'],3))
        #vds_MM.append(round(dc_results['MM12:vds'],3))
        #vds_MM.append(round(dc_results['MM13:vds'],3))
        #vds_MM.append(round(dc_results['MM14:vds'],3))
        #vds_MM.append(round(dc_results['MM15:vds'],3))
        #vds_MM.append(round(dc_results['MM16:vds'],3))
        #vds_MM.append(round(dc_results['MM17:vds'],3))
        #vds_MM.append(round(dc_results['MM18:vds'],3))
        region_of_operation_MM = []
        #region_of_operation_MM.append(int(dc_results['MM0:region']))
        #region_of_operation_MM.append(int(dc_results['MM1:region']))
        #region_of_operation_MM.append(int(dc_results['MM2:region']))
        #region_of_operation_MM.append(int(dc_results['MM3:region']))
        #region_of_operation_MM.append(int(dc_results['MM4:region']))
        #region_of_operation_MM.append(int(dc_results['MM5:region']))
        #region_of_operation_MM.append(int(dc_results['MM6:region']))
        #region_of_operation_MM.append(int(dc_results['MM7:region']))
        #region_of_operation_MM.append(int(dc_results['MM8:region']))
        #region_of_operation_MM.append(int(dc_results['MM9:region']))
        #region_of_operation_MM.append(int(dc_results['MM10:region']))
        #region_of_operation_MM.append(int(dc_results['MM11:region']))
        #region_of_operation_MM.append(int(dc_results['MM12:region']))
        #region_of_operation_MM.append(int(dc_results['MM13:region']))
        #region_of_operation_MM.append(int(dc_results['MM14:region']))
        #region_of_operation_MM.append(int(dc_results['MM15:region'])) 
        #region_of_operation_MM.append(int(dc_results['MM16:region']))
        #region_of_operation_MM.append(int(dc_results['MM17:region']))
        #region_of_operation_MM.append(int(dc_results['MM18:region'])) 

        gain = cls.find_dc_gain(vout)
        ugbw,valid = cls.find_ugbw(freq, vout)
        phm = cls.find_phm(freq, vout)
        power = -dc_results['V0:p']
      #  if globalsy.counterrrr < 200:
      #          f = open("/path/to/optimizer/out1.txt",'a')
      #          print("metrics-", "gain: ", f'{float(gain):.3}', ", UGBW: ",  f'{float(ugbw):.3}', ", PM: ",  f'{float(phm):.3}', ", power: ", f'{float(power):.3}', valid, file=f)
      #          f.close()
        if globalsy.counterrrr < 1200:
                f = open("/path/to/optimizer/out11.txt",'a')
                print("metrics-", "gain: ", f'{float(gain):.3}', ", UGBW: ",  f'{float(ugbw):.3}', ", PM: ",  f'{float(phm):.3}', ", power: ", f'{float(power):.3}', valid, file=f)
                f.close()
        elif globalsy.counterrrr < 2000:
                f = open("/path/to/optimizer/out12.txt",'a')
                print("metrics-", "gain: ", f'{float(gain):.3}', ", UGBW: ",  f'{float(ugbw):.3}', ", PM: ",  f'{float(phm):.3}', ", power: ", f'{float(power):.3}', valid, file=f)
                f.close()
        results = dict(
            gain = gain,
            funity = ugbw,
            pm = phm,
            power = power,
            valid = valid,
            zregion_of_operation_MM = region_of_operation_MM,
            zzgm_MM = gm_MM,
            zzids_MM = ids_MM,
            zzvds_MM = vds_MM,
            zzvgs_MM = vgs_MM
        )
        f.close()
        return results

    @classmethod
    def find_dc_gain (self, vout):
        return np.abs(vout)[0]

    @classmethod
    def find_ugbw(self, freq, vout):
        gain = np.abs(vout)
        ugbw, valid = self._get_best_crossing(freq, gain, val=1)
        if valid:
            return ugbw, valid
        else:
            return freq[0], valid

    @classmethod
    def find_phm(self, freq, vout):
        gain = np.abs(vout)
        phase = np.angle(vout, deg=False)
        phase = np.unwrap(phase) # unwrap the discontinuity
        phase = np.rad2deg(phase) # convert to degrees
        #
        #plt.subplot(211)
        #plt.plot(np.log10(freq[:200]), 20*np.log10(gain[:200]))
        #plt.subplot(212)
        #plt.plot(np.log10(freq[:200]), phase)
        #plt.show()

        phase_fun = interp.interp1d(freq, phase, kind='quadratic')
        ugbw, valid = self._get_best_crossing(freq, gain, val=1)
        if valid:
            if phase[0] > 150:
                return phase_fun(ugbw)
            else:
                return 180+phase_fun(ugbw)
            #if phase_fun(ugbw) > 0:
            #    return -180+phase_fun(ugbw)
            #else:
            #    return 180 + phase_fun(ugbw)
        else:
            return -180

    @classmethod
    def _get_best_crossing(cls, xvec, yvec, val):
        interp_fun = interp.InterpolatedUnivariateSpline(xvec, yvec)

        def fzero(x):
            return interp_fun(x) - val

        xstart, xstop = xvec[0], xvec[-1]
        try:
            return sciopt.brentq(fzero, xstart, xstop), True
        except ValueError:
            # avoid no solution
            # if abs(fzero(xstart)) < abs(fzero(xstop)):
            #     return xstart
            return xstop, False

if __name__ == '__main__':

    yname = '/path/to/optimizer/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml'
    eval_core = OpampMeasMan(yname)

    designs = eval_core.generate_data_set(n=1)

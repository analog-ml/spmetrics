# This file is part of https://github.com/ksettaluri6/AutoCkt
# for more information please see the README.md file in the original repository.

from collections import OrderedDict
import re
import importlib
import numpy as np
import copy
from multiprocessing.dummy import Pool as ThreadPool
import os
import abc
import scipy.interpolate as interp
import scipy.optimize as sciopt
import random
import time
import pprint
import yaml
import IPython

debug = False


class NgSpiceWrapper(object):

    BASE_TMP_DIR = os.path.abspath("/tmp/ckt_da")

    def __init__(self, num_process, yaml_path, path, root_dir=None):
        if root_dir == None:
            self.root_dir = NgSpiceWrapper.BASE_TMP_DIR
        else:
            self.root_dir = root_dir
        with open(yaml_path, "r") as f:
            yaml_data = yaml.load(f, yaml.FullLoader)
        design_netlist = yaml_data["dsn_netlist"]
        design_netlist = path + "/" + design_netlist

        _, dsg_netlist_fname = os.path.split(design_netlist)
        self.base_design_name = os.path.splitext(dsg_netlist_fname)[0]
        self.num_process = num_process
        self.gen_dir = os.path.join(self.root_dir, "designs_" + self.base_design_name)

        os.makedirs(self.root_dir, exist_ok=True)
        os.makedirs(self.gen_dir, exist_ok=True)

        raw_file = open(design_netlist, "r")
        self.tmp_lines = raw_file.readlines()
        raw_file.close()

    def get_design_name(self, state):
        fname = self.base_design_name
        for value in state.values():
            fname += "_" + str(value)
        return fname

    def create_design(self, state, new_fname):
        print("new_fname", new_fname)
        design_folder = os.path.join(self.gen_dir, new_fname) + str(
            random.randint(0, 10000)
        )
        os.makedirs(design_folder, exist_ok=True)

        fpath = os.path.join(design_folder, new_fname + ".cir")
        print("Creating design at: %s" % fpath)
        lines = copy.deepcopy(self.tmp_lines)
        for line_num, line in enumerate(lines):
            if ".include" in line:
                regex = re.compile('\.include\s*"(.*?)"')
                found = regex.search(line)
                if found:
                    # current_fpath = os.path.realpath(__file__)
                    # parent_path = os.path.abspath(os.path.join(current_fpath, os.pardir))
                    # parent_path = os.path.abspath(os.path.join(parent_path, os.pardir))
                    # path_to_model = os.path.join(parent_path, 'spice_models/45nm_bulk.txt')
                    # lines[line_num] = lines[line_num].replace(found.group(1), path_to_model)
                    pass  # do not change the model path
            if ".param" in line:
                for key, value in state.items():
                    regex = re.compile("%s=(\S+)" % (key))
                    found = regex.search(line)
                    if found:
                        new_replacement = "%s=%s" % (key, str(value))
                        lines[line_num] = lines[line_num].replace(
                            found.group(0), new_replacement
                        )
            if "wrdata" in line:
                regex = re.compile("wrdata\s*(\w+\.\w+)\s*")
                found = regex.search(line)
                if found:
                    replacement = os.path.join(design_folder, found.group(1))
                    lines[line_num] = lines[line_num].replace(
                        found.group(1), replacement
                    )

        with open(fpath, "w") as f:
            f.writelines(lines)
            f.close()
        return design_folder, fpath

    def simulate(self, fpath):
        info = 0  # this means no error occurred
        command = "ngspice -b %s >/dev/null 2>&1" % fpath
        exit_code = os.system(command)
        if debug:
            print(command)
            print(fpath)

        if exit_code % 256:
            # raise RuntimeError('program {} failed!'.format(command))
            info = 1  # this means an error has occurred
        return info

    def create_design_and_simulate(self, state, dsn_name=None, verbose=False):
        if debug:
            print("state", state)
            print("verbose", verbose)
        if dsn_name == None:
            dsn_name = self.get_design_name(state)
        else:
            dsn_name = str(dsn_name)
        if verbose:
            print(dsn_name)
        design_folder, fpath = self.create_design(state, dsn_name)
        info = self.simulate(fpath)
        specs = self.translate_result(design_folder)
        return state, specs, info

    def run(self, states, design_names=None, verbose=False):
        """

        :param states:
        :param design_names: if None default design name will be used, otherwise the given design name will be used
        :param verbose: If True it will print the design name that was created
        :return:
            results = [(state: dict(param_kwds, param_value), specs: dict(spec_kwds, spec_value), info: int)]
        """
        pool = ThreadPool(processes=self.num_process)
        arg_list = [
            (state, dsn_name, verbose)
            for (state, dsn_name) in zip(states, design_names)
        ]
        specs = pool.starmap(self.create_design_and_simulate, arg_list)
        pool.close()
        return specs

    def translate_result(self, output_path):
        """
        This method needs to be overwritten according to cicuit needs,
        parsing output, playing with the results to get a cost function, etc.
        The designer should look at his/her netlist and accordingly write this function.

        :param output_path:
        :return:
        """
        result = None
        return result


class TwoStageClass(NgSpiceWrapper):

    def translate_result(self, output_path):
        """

        :param output_path:
        :return
            result: dict(spec_kwds, spec_value)
        """

        # use parse output here
        freq, vout, ibias = self.parse_output(output_path)
        gain = self.find_dc_gain(vout)
        ugbw = self.find_ugbw(freq, vout)
        phm = self.find_phm(freq, vout)

        spec = dict(ugbw=ugbw, gain=gain, phm=phm, ibias=ibias)

        return spec

    def parse_output(self, output_path):

        ac_fname = os.path.join(output_path, "ac.csv")
        dc_fname = os.path.join(output_path, "dc.csv")

        if not os.path.isfile(ac_fname) or not os.path.isfile(dc_fname):
            print("ac/dc file doesn't exist: %s" % output_path)

        ac_raw_outputs = np.genfromtxt(ac_fname, skip_header=1)
        dc_raw_outputs = np.genfromtxt(dc_fname, skip_header=1)
        freq = ac_raw_outputs[:, 0]
        vout_real = ac_raw_outputs[:, 1]
        vout_imag = ac_raw_outputs[:, 2]
        vout = vout_real + 1j * vout_imag
        ibias = -dc_raw_outputs[1]

        return freq, vout, ibias

    def find_dc_gain(self, vout):
        # return np.abs(vout)[0]
        return 20 * np.log10(np.abs(vout)[0])

    def find_ugbw(self, freq, vout):
        gain = np.abs(vout)
        ugbw, valid = self._get_best_crossing(freq, gain, val=1)
        if valid:
            return ugbw
        else:
            return freq[0]

    def find_phm(self, freq, vout):
        gain = np.abs(vout)
        phase = np.angle(vout, deg=False)
        phase = np.unwrap(phase)  # unwrap the discontinuity
        phase = np.rad2deg(phase)  # convert to degrees

        # plt.subplot(211)
        # plt.plot(np.log10(freq[:200]), 20*np.log10(gain[:200]))
        # plt.subplot(212)
        # plt.plot(np.log10(freq[:200]), phase)

        phase_fun = interp.interp1d(freq, phase, kind="quadratic")
        ugbw, valid = self._get_best_crossing(freq, gain, val=1)
        if valid:
            if phase_fun(ugbw) > 0:
                return -180 + phase_fun(ugbw)
            else:
                return 180 + phase_fun(ugbw)
        else:
            return -180

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


# way of ordering the way a yaml file is read
class OrderedDictYAMLLoader(yaml.Loader):
    """
    A YAML loader that loads mappings into ordered dictionaries.
    """

    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)

        self.add_constructor("tag:yaml.org,2002:map", type(self).construct_yaml_map)
        self.add_constructor("tag:yaml.org,2002:omap", type(self).construct_yaml_map)

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
                None,
                None,
                "expected a mapping node, but found %s" % node.id,
                node.start_mark,
            )

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


if __name__ == "__main__":
    num_process = 1
    CIR_YAML = "examples/two_stage_opamp.yaml"
    path = os.getcwd()
    ngspice = TwoStageClass(yaml_path=CIR_YAML, num_process=num_process, path=path)
    states = [
        {"w1": 0.5, "w2": 0.5, "l1": 0.5, "l2": 0.5},
        {"w1": 0.6, "w2": 0.6, "l1": 0.6, "l2": 0.6},
        {"w1": 0.7, "w2": 0.7, "l1": 0.7, "l2": 0.7},
    ]

    with open(CIR_YAML, "r") as f:
        yaml_data = yaml.load(f, OrderedDictYAMLLoader)

    params = yaml_data["params"]
    self_params = []
    self_params_id = list(params.keys())

    for value in params.values():
        param_vec = np.arange(value[0], value[1], value[2])
        self_params.append(param_vec)

    params_idx = np.array([33, 33, 33, 33, 33, 14, 20])
    params = [self_params[i][params_idx[i]] for i in range(len(self_params_id))]
    param_val = [OrderedDict(list(zip(self_params_id, params)))]

    # run param vals and simulate
    cur_specs = OrderedDict(
        sorted(
            ngspice.create_design_and_simulate(param_val[0])[1].items(),
            key=lambda k: k[0],
        )
    )
    print("Current Specs:", cur_specs)

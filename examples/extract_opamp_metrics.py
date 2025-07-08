from spmetrics.utils import (
    run_ngspice_simulation,
    # Simulation setup functions
    setup_dc_simulation,
    setup_dc_ow_simulation,
    setup_offset_simulation,
    setup_ac_simulation,
    setup_icmr_simulation,
    setup_trans_simulation,
    setup_common_mode_simulation,
)
from spmetrics.extractor import (
    # DC simulation functions
    compute_output_swing,
    compute_offset,
    compute_icmr,
    # AC simulation functions
    compute_bandwidth,
    compute_unity_gain_bandwidth,
    compute_phase_margin,
    compute_ac_gain,
    compute_leakage_power,
    compute_cmrr,
    compute_tran_gain,
)
import shutil
import sys

from tabulate import tabulate
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


netlist = open("examples/liuLLMbasedAIAgent2025_optimized_g1-5.cir").read()

print("\nDC Simulation Netlist:")
dc_netlist = setup_dc_simulation(netlist, ["in1", "in2"], ["out"])
print(dc_netlist)


# Calculate Output Swing
# --------------
# This function modifies the netlist to set up a DC simulation by updating specific components and appending simulation commands.
dc_ow_netlist = setup_dc_ow_simulation(dc_netlist, ["in1", "in2"], ["out"])
print("\nDC OW Simulation Netlist:")
print(dc_ow_netlist)
run_ngspice_simulation(dc_ow_netlist)
output_swing = compute_output_swing("output_dc_ow.dat")
print(f"\nOutput Swing: {output_swing:.4f} V")


# Calculate offset voltage
# --------------
# This function modifies the netlist to set up a DC offset simulation by updating specific components and appending simulation commands.
offset_voltage_netlist = setup_offset_simulation(
    netlist,
    target_components=["M4", "M1"],
    negative_input_node="in1",
    output_node="out",
)
print("\nOffset Voltage Simulation Netlist:")
print(offset_voltage_netlist)
run_ngspice_simulation(offset_voltage_netlist)
offset = compute_offset("output_dc_offset.dat")
print(f"\nOffset Voltage: {offset:.4f} V")


# Calculate Bandwidth
# --------------
ac_netlist = setup_ac_simulation(netlist, ["in1", "in2"], ["out"])
run_ngspice_simulation(ac_netlist)
bandwidth = compute_bandwidth("output_ac.dat")
print(f"\nBandwidth: {bandwidth:.4f} Hz")

ubw = compute_unity_gain_bandwidth("output_ac.dat")
print(f"Unity Gain Bandwidth: {ubw:.4f} Hz")

phase_margin = compute_phase_margin("output_ac.dat")
print(f"Phase Margin: {phase_margin:.4f} degrees")

ac_gain = compute_ac_gain("output_ac.dat")
print(f"AC Gain: {ac_gain:.4f} dB")


print(f"\nOffset Voltage: {offset:.4f} V")


# Calculate ICMR (Input Common Mode Range)
# --------------
icmr_netlist = setup_icmr_simulation(
    netlist, target_components=["M4", "M1"], output_node="out"
)
run_ngspice_simulation(icmr_netlist)
icmr = compute_icmr("output_dc_icmr.dat")
print(f"\nICMR: {icmr:.4f} V")


# Calculate leakage power
# --------------
tran_netlist = setup_trans_simulation(netlist, input_name="in1", output_nodes=["out"])
run_ngspice_simulation(tran_netlist)
leakage_power_netlist = compute_leakage_power("output_tran.dat")
print(f"\nLeakage Power: {leakage_power_netlist:.4f} W")

# Compute transient gain
# --------------
tran_gain = compute_tran_gain("output_tran.dat")
print(f"\nTransient Gain: {tran_gain:.4f} dB")


# Calculate CMRR
# --------------
common_mode_netlist = setup_common_mode_simulation(ac_netlist)
shutil.copy("output_ac.dat", "output_ac_diff.dat")
shutil.copy("output_tran.dat", "output_tran_diff.dat")

run_ngspice_simulation(common_mode_netlist)
shutil.copy("output_ac.dat", "output_ac_cm.dat")
shutil.copy("output_tran.dat", "output_tran_cm.dat")

ac_diff_file = "output_ac_diff.dat"
tran_diff_file = "output_tran_diff.dat"
ac_cm_file = "output_ac_cm.dat"
tran_cm_file = "output_tran_cm.dat"

cmrr_tran, cmrr_ac = compute_cmrr(
    ac_diff_file, tran_diff_file, ac_cm_file, tran_cm_file
)
print(f"\nCMRR (Transient): {cmrr_tran:.4f} dB")
print(f"CMRR (AC): {cmrr_ac:.4f} dB")

# Print all metrics in a table
print(
    tabulate(
        [
            ["AC Gain", f"{ac_gain:.4f} dB"],
            ["Transient Gain", f"{tran_gain:.4f} dB"],
            ["Bandwidth", f"{bandwidth:.4f} Hz"],
            ["Unity Gain Bandwidth", f"{ubw:.4f} Hz", f"{ubw/1e6:.2f} MHz"],
            ["Phase Margin", f"{phase_margin:.4f} degrees"],
            [
                "Leakage Power",
                f"{leakage_power_netlist:.4f} W",
                f"{leakage_power_netlist*1000:.2f} mW",
            ],
            ["CMRR (Transient)", f"{cmrr_tran:.2f} dB"],
            ["CMRR (AC)", f"{cmrr_ac:.4f} dB"],
            ["Offset Voltage", f"{offset:.4f} V", f"{offset*1000:.2f} mV"],
            ["Output Swing", f"{output_swing:.4f} V"],
            ["ICMR (Input Common Mode Range)", f"{icmr:.4f} V"],
        ],
        headers=["Metrics", "Values", "Unit Conversion"],
    )
)

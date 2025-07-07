from spmetrics.utils import (
    setup_dc_simulation,
    setup_dc_ow_simulation,
    setup_offset_simulation,
    run_ngspice_simulation,
    setup_ac_simulation,
)
from spmetrics.extractor import (
    compute_output_swing,
    compute_offset,
    # AC simulation functions
    compute_bandwidth,
    compute_unity_gain_bandwidth,
    compute_phase_margin,
    compute_ac_gain,
)

netlist = open("examples/liuLLMbasedAIAgent2025.cir").read()

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
ac_bandwidth_netlist = setup_ac_simulation(netlist, ["in1", "in2"], ["out"])
run_ngspice_simulation(ac_bandwidth_netlist)
bandwidth = compute_bandwidth("output_ac.dat")
print(f"\nBandwidth: {bandwidth:.4f} Hz")

ubw = compute_unity_gain_bandwidth("output_ac.dat")
print(f"Unity Gain Bandwidth: {ubw:.4f} Hz")

phase_margin = compute_phase_margin("output_ac.dat")
print(f"Phase Margin: {phase_margin:.4f} degrees")

ac_gain = compute_ac_gain("output_ac.dat")
print(f"AC Gain: {ac_gain:.4f} dB")


print(f"\nOffset Voltage: {offset:.4f} V")

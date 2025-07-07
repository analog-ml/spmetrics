import re
import subprocess
import shutil


def setup_dc_simulation(
    netlist: str, input_name: list[str], output_node: list[str]
) -> str:
    end_index = netlist.index(".end\n")
    output_nodes_str = " ".join(output_node)
    simulation_commands = f"""
    .control
      dc Vcm 0 1.8 0.001        
      wrdata output_dc.dat {output_nodes_str}  
    .endc
     """
    new_netlist = netlist[:end_index] + simulation_commands + netlist[end_index:]
    return new_netlist


def setup_dc_ow_simulation(
    netlist: str, input_name: list[str], output_node: list[str]
) -> str:
    modified_netlist = re.sub(r"\.control.*?\.endc", "", netlist, flags=re.DOTALL)
    updated_lines = []
    for line in modified_netlist.splitlines():
        if line.startswith("Vcm"):
            line = "Vin1 in1 0 DC {Vcm}"
        elif line.startswith("Eidn"):
            line = "Vin2 in2 0 DC 0.9"
        elif line.startswith("Eidp"):
            line = "\n"
        elif line.startswith("Vid"):
            line = "\n"
        updated_lines.append(line)
    updated_netlist = "\n".join(updated_lines)

    # This performs a DC sweep of the input voltage source Vin1 from 0 V to 1.8 V in 0.1 mV steps.
    # For each input voltage step, NGSpice records the output voltage (out) and the swept input voltage (in1).
    # The results are written to the file output_dc_ow.dat.
    simulation_commands = f"""
    .control
      dc Vin1 0 1.8 0.0001
      wrdata output_dc_ow.dat out in1
    .endc
    """
    end_index = updated_netlist.index(".end")
    netlist_ow = (
        updated_netlist[:end_index] + simulation_commands + updated_netlist[end_index:]
    )
    return netlist_ow


def setup_offset_simulation(
    netlist: str,
    target_components: list[str] = None,
    negative_input_node: str = "in1",
    output_node: str = "out",
) -> str:
    """
    Modifies a given SPICE netlist to set up a DC offset simulation by updating specific components and appending simulation commands.

    Args:
        netlist (str): The original SPICE netlist as a string.
        conside_components (list[str], optional): List of MOSFET component names to consider for node replacement.
        negative_input_node (str, optional): The name of the negative input node to be replaced. Defaults to "in1".
        output_node (str, optional): The name of the output node to replace the negative input node with. Defaults to "out".

    Returns:
        str: The modified netlist with updated component connections and appended DC offset simulation commands.

    Notes:
        - Removes any existing .control ... .endc blocks from the netlist.
        - Replaces occurrences of the negative input node with the output node in specified MOSFET lines.
        - Skips lines starting with "Rl" or "Cl".
        - Appends a .control block to perform a DC sweep and write output data.
    """

    modified_netlist = re.sub(r"\.control.*?\.endc", "", netlist, flags=re.DOTALL)
    updated_lines = []
    for line in modified_netlist.splitlines():
        component = line.split()[0] if line.strip() else ""
        if (
            component.startswith("M") or component.startswith("m")
        ) and component in target_components:
            # Replace 'in1' with output node (e.g. 'out')
            line = re.sub(r"\bin1\b", output_node, line)
        if not (line.startswith("Rl") or line.startswith("Cl")):
            # Skip lines starting with "Rl" or "Cl"
            updated_lines.append(line)
    updated_netlist = "\n".join(updated_lines)
    simulation_commands = f"""
    .control
      dc Vcm 0 1.8 0.001
      wrdata output_dc_offset.dat out
    .endc
    """
    end_index = updated_netlist.index(".end")
    netlist_offset = (
        updated_netlist[:end_index] + simulation_commands + updated_netlist[end_index:]
    )
    return netlist_offset


def setup_ac_simulation(
    netlist: str, input_name: list[str], output_node: list[str]
) -> str:
    """
    Inserts AC simulation commands into a SPICE netlist string.

    Args:
        netlist (str): The original SPICE netlist as a string.
        input_name (list[str]): List of input source names (currently unused).
        output_node (list[str]): List of output node names to be included in the simulation output.

    Returns:
        str: Modified netlist string with AC simulation commands inserted before the '.end' statement.

    Note:
        The function assumes that the netlist contains a line ending with '.end\n'.
        The 'input_name' parameter is currently not used in the function logic.
    """
    end_index = netlist.index(".end\n")
    output_nodes_str = " ".join(output_node)
    simulation_commands = f"""
      .control
        ac dec 10 1 10G        
        wrdata output_ac.dat {output_nodes_str} 
      .endc
     """
    new_netlist = netlist[:end_index] + simulation_commands + netlist[end_index:]
    return new_netlist


def setup_trans_simulation(
    netlist: str, input_name: list[str], output_node: list[str]
) -> str:
    end_index = netlist.index(".end\n")
    output_nodes_str = " ".join(output_node)
    simulation_commands = f"""
      .control
        tran 50n 500u
        wrdata output_tran.dat {output_nodes_str} I(vdd) in1
      .endc
     """
    new_netlist = netlist[:end_index] + simulation_commands + netlist[end_index:]
    return new_netlist


def run_ngspice_simulation(netlist: str) -> None:
    """
    Runs a simulation using NGSpice with the provided netlist and writes the output to a specified file.

    Args:
        netlist (str): The SPICE netlist to be simulated.
        output_file (str): The file where the simulation results will be written.
    """
    with open("/tmp/temp_netlist.cir", "w") as f:
        f.write(netlist)

    subprocess.run(["ngspice", "-b", "/tmp/temp_netlist.cir"], check=True)

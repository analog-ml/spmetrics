import numpy as np
from loguru import logger


def compute_output_swing(logfile: str) -> float:
    """
    Computes the output swing (OW) of an amplifier from a log file containing simulation or measurement data.
    The function reads a log file with columns for time, output voltage, and input voltage, computes the small-signal gain (dVout/dVin) across the input range,
    identifies the mid-band gain at a reference input voltage (typically 0.9 V), and determines the output voltage range where the gain remains above 80% of the mid-band value.
    The output swing is defined as the difference between the maximum and minimum output voltages within this high-gain region.

    Args:
        logfile (str): Path to the log file containing the data. The file should be compatible with NumPy's genfromtxt, with columns for time, output voltage, and input voltage.
    Returns:
        float: The computed output swing (OW) in volts. Returns 0 if no region meets the gain threshold.
    """

    # 1. Load Data
    # --------------------------------------
    # Uses NumPy to read the data from the specified log file, skipping the header.
    # The data is expected to be in a format where the first column is time, the
    # second column is output voltage, and the third column is input voltage.
    # The data is stored in a NumPy array for further processing.
    # The file is expected to be in a format compatible with NumPy's genfromtxt.
    data_dc = np.genfromtxt(logfile, skip_header=1)
    if data_dc.shape[1] < 4:
        logger.error("Data file does not contain enough columns. Expected 4 columns.")
        return 0.0

    output = data_dc[0:, 1]  # Output voltage 'out's
    in1 = data_dc[0:, 3]  # Input voltage 'in1'

    # 2. Compute Gain as dVout/dVin
    # --------------------------------------
    # Uses NumPy to compute the derivative of output voltage with respect to input — an approximation of gain.
    d_output_d_in1 = np.gradient(output, in1)

    # Replace zero or near-zero values with a small epsilon to avoid log10(0) error
    epsilon = 1e-10
    d_output_d_in1 = np.where(np.abs(d_output_d_in1) < epsilon, epsilon, d_output_d_in1)

    # Compute gain safely
    # Gain is expressed in dB:  Gain = 20 * log10(|dVout/dVin|)
    gain = 20 * np.log10(np.abs(d_output_d_in1))

    # 3. Identify Midpoint Gain
    # --------------------------------------
    # Finds the index where Vin1 = 0.9V (typically mid-rail in a 1.8 V system).
    max_index = np.where(in1 == 0.9)

    if len(max_index[0]) > 0:
        # Use the first index (assuming you want the first match)
        index = max_index[0][0]

        # Gets the gain at mid-input voltage, assumed to be the reference point (mid-band gain).
        # Extract the corresponding Idd value
        gain_mid = gain[index]
        logger.debug(f"gain_mid = {gain_mid}")
    else:
        gain_mid = None

    # 4. Compute Output Swing (OW)
    # --------------------------------------
    # Extracts output values where gain ≥ 80% of mid-band gain.
    # This approximates the linear region of the amplifier where it still maintains acceptable gain.
    indices = np.where(gain > 0.8 * gain_mid)
    output_above_threshold = output[indices]

    if output_above_threshold.size > 0:
        vout_max = np.max(output_above_threshold)
        vout_min = np.min(output_above_threshold)
        ow = vout_max - vout_min
    else:
        ow = 0
        logger.debug("No values found where gain > 0.8 * gain_max")
    return ow


def compute_offset(logfile: str) -> float:
    """
    Computes the maximum voltage offset between input and output signals from a log file.

    The function reads a data file (CSV or whitespace-delimited) containing at least two columns:
    the first column is treated as the input signal, and the second as the output signal.
    It skips the first and last 19 data points to avoid edge effects, then calculates the
    maximum absolute difference between the input and output signals.

    Args:
        logfile (str): Path to the log file containing the input and output data.

    Returns:
        float: The maximum absolute voltage offset between the output and input signals.
    """
    data_dc = np.genfromtxt(logfile, skip_header=1)

    # Extract input and output values from the data
    input = data_dc[19:-19, 0]  # Skip first and last points
    output = data_dc[19:-19, 1]

    # Calculate the maximum voltage offset (difference between output and input)
    voff_max = np.max(np.abs(output - input))
    return voff_max


def compute_bandwidth(logfile: str = "output_ac.dat") -> float:
    """
    Computes the bandwidth of an amplifier from a log file containing frequency response data.

    The function reads a data file (CSV or whitespace-delimited) containing frequency and gain values,
    then calculates the bandwidth as the frequency at which the gain drops to -3 dB from its maximum value.

    Args:
        logfile (str): Path to the log file containing frequency and gain data. Default is "output_ac.dat".

    Returns:
        float: The bandwidth of the amplifier in Hz.
    """
    data_ac = np.genfromtxt(logfile, skip_header=1)
    num_columns = data_ac.shape[1]
    frequency = data_ac[:, 0]

    # for one output node
    if num_columns == 3:
        v_d = data_ac[:, 1] + 1j * data_ac[:, 2]
        output = 20 * np.log10(v_d)
        gain = 20 * np.log10(np.abs(v_d[0]))
    # for 2 output nodes
    elif num_columns == 6:
        v_d = data_ac[:, 4] + 1j * data_ac[:, 5]
        output = 20 * np.log10(v_d)
        gain = 20 * np.log10(np.abs(v_d[0]))

    half_power_point = gain - 3
    indices = np.where(output >= half_power_point)[0]

    if len(indices) > 0:
        f_l = frequency[indices[0]]
        f_h = frequency[indices[-1]]
        bandwidth = f_h - f_l
    else:
        f_l = f_h = bandwidth = 0

    return bandwidth


def compute_unity_gain_bandwidth(logfile: str) -> float:
    """
    Computes the unity gain bandwidth (UBW) from an AC analysis log file.

    The function reads frequency response data from a log file, determines the frequency range
    where the output magnitude (in dB) is greater than or equal to 0 dB (unity gain), and returns
    the bandwidth between the lowest and highest such frequencies.

    Args:
        logfile (str): Path to the log file containing AC analysis data. The file should have columns
            corresponding to frequency and complex output voltages. The function supports files with
            either 3 columns (single output node) or 6 columns (two output nodes).

    Returns:
        float: The unity gain bandwidth (UBW) in the same frequency units as in the log file.
               Returns 0 if no frequencies meet the unity gain criterion.
    """
    # TODO: Accoording to the information provided by ChatGPT, this function is not correct.
    # It should be fixed to compute the bandwidth correctly.
    # please refer to the documentation for more details.

    data_ac = np.genfromtxt(logfile, skip_header=1)
    num_columns = data_ac.shape[1]
    frequency = data_ac[:, 0]

    # for one output node
    if num_columns == 3:
        v_d = data_ac[:, 1] + 1j * data_ac[:, 2]
        output = 20 * np.log10(v_d)
        gain = 20 * np.log10(np.abs(v_d[0]))
    # for 2 output nodes
    elif num_columns == 6:
        v_d = data_ac[:, 4] + 1j * data_ac[:, 5]
        output = 20 * np.log10(v_d)
        gain = 20 * np.log10(np.abs(v_d[0]))

    half_power_point = 0
    indices = np.where(output >= half_power_point)[0]

    if len(indices) > 0:
        f_l = frequency[indices[0]]
        f_h = frequency[indices[-1]]
        ubw = f_h - f_l
    else:
        f_l = f_h = ubw = 0

    mag = 20 * np.log10(np.abs(v_d))
    cross_idx = np.where(mag <= 0)[0][0]  # First index where gain falls below 0 dB
    f1, f2 = frequency[cross_idx - 1], frequency[cross_idx]
    g1, g2 = mag[cross_idx - 1], mag[cross_idx]

    # Linear interpolation to find exact 0 dB crossing
    unity_gain_freq = f1 + (0 - g1) * (f2 - f1) / (g2 - g1)
    return unity_gain_freq


def compute_phase_margin(logfile: str) -> float:
    """
    Computes the phase margin from an AC analysis logfile.
    The function reads frequency response data from a logfile, extracts the gain and phase information,
    and determines the phase margin at the frequency where the gain crosses 0 dB. It supports logfiles
    with either one or two output nodes.
    Args:
        logfile (str): Path to the AC analysis logfile. The file should be a text file with columns
            representing frequency and complex output voltages.
    Returns:
        float: The computed phase margin in degrees. Returns 0 if the initial phase does not match
            expected conditions (close to 0 or 180 degrees).
    Notes:
        - For logfiles with 3 columns, the output voltage is assumed to be in columns 2 and 3 (real and imaginary).
        - For logfiles with 6 columns, the output voltage is assumed to be in columns 5 and 6 (real and imaginary).
        - The phase margin is calculated based on the initial phase and the phase at the 0 dB gain crossover.
    """

    data_ac = np.genfromtxt(logfile, skip_header=1)
    num_columns = data_ac.shape[1]
    frequency = data_ac[:, 0]
    # for one output node
    if num_columns == 3:
        v_d = data_ac[:, 1] + 1j * data_ac[:, 2]
    # for 2 output nodes
    elif num_columns == 6:
        v_d = data_ac[:, 4] + 1j * data_ac[:, 5]
    # gain
    gain_db = 20 * np.log10(np.abs(v_d))
    # phase
    phase = np.degrees(np.angle(v_d))

    # find the frequency where gain = 0dB
    gain_db_at_0_dB = np.abs(gain_db - 0)
    index_at_0_dB = np.argmin(gain_db_at_0_dB)
    frequency_at_0_dB = frequency[index_at_0_dB]
    phase_at_0_dB = phase[index_at_0_dB]

    # Calculate phase margin
    # Phase margin is defined as the difference between the phase at 0 dB and -180 degrees
    return phase_at_0_dB - (-180)


def compute_ac_gain(logfile: str) -> float:
    """
    Computes the AC gain (in dB) from a logfile containing frequency-domain simulation data.
    The logfile is expected to be a text file with either 3 or 6 columns (excluding the header):
    - For 3 columns: [frequency, real(v_d), imag(v_d)]
    - For 6 columns: [frequency, real(v_x), imag(v_x), real(v_y), real(v_d), imag(v_d)]
    The function calculates the gain as 20 * log10(|v_d[0]|), where v_d is the complex output voltage at the first frequency point.
    Args:
        logfile (str): Path to the logfile containing the AC simulation data.
    Returns:
        float: The computed AC gain in decibels (dB) at the first frequency point.
    Raises:
        ValueError: If the input file does not have either 3 or 6 columns.
    """

    data_ac = np.genfromtxt(logfile, skip_header=1)
    num_columns = data_ac.shape[1]

    # for one output node
    if num_columns == 3:
        frequency = data_ac[:, 0]
        v_d = data_ac[:, 1] + 1j * data_ac[:, 2]
        gain = 20 * np.log10(np.abs(v_d[0]))
    # for 2 output nodes
    elif num_columns == 6:
        v_d = data_ac[:, 4] + 1j * data_ac[:, 5]
        gain = 20 * np.log10(np.abs(v_d[0]))
    else:
        raise ValueError("The input file must have either 3 or 6 columns.")
    return gain


def compute_tran_gain(logfile: str) -> float:
    """
    Computes the transient gain from a log file containing simulation data.

    The function reads a log file, extracts the output signal, identifies the peak (maximum)
    and trough (minimum) values, and calculates the gain in decibels (dB) based on the difference
    between the peak and trough, normalized by a reference value (2 µV).

    Parameters:
        logfile (str): Path to the log file containing simulation data. The file is expected
                       to have at least 6 columns, with the first column as time and the second
                       column as the output signal.

    Returns:
        float: The computed transient gain in decibels (dB).

    Raises:
        ValueError: If the input file does not have exactly 6 columns.
    """
    data_tran = np.genfromtxt(logfile, skip_header=1)
    num_columns = data_tran.shape[1]

    # for one output node
    if num_columns == 6:
        time = data_tran[:, 0]
        out = data_tran[:, 1]

        # Find the peaks (local maxima)
        peak = np.max(out)

        # Find the troughs (local minima) by inverting the signal
        trough = np.min(out)

        # Compute the gain using the difference between average peak and average trough
        tran_gain = 20 * np.log10(np.abs(peak - trough) / 0.000002)
    else:
        raise ValueError("The input file must have 2 columns.")

    return tran_gain


def compute_icmr(logfile: str) -> float:
    """
    Computes the input common-mode range (ICMR) from a logfile containing DC simulation data.
    The logfile is expected to be a text file with at least 4 columns:
    - Column 1: Time
    - Column 2: Output voltage
    - Column 3: Input voltage
    - Column 4: Input voltage (in1)

    Args:
        logfile (str): Path to the logfile containing the DC simulation data.

    Returns:
        float: The computed input common-mode range (ICMR) in volts.
    """

    # Read simulation data
    data_dc = np.genfromtxt(logfile, skip_header=1)

    # Extract relevant data
    input_vals = data_dc[19:-19, 0]  # Skip first and last points
    output_vals = data_dc[19:-19, 1]
    Idd = np.abs(data_dc[19:-19, 3])
    # Find indices where input_vals is equal to 0.9
    indices = np.where(input_vals == 0.9)

    # Check if any indices were found
    if len(indices[0]) > 0:
        # Use the first index (assuming you want the first match)
        index = indices[0][0]

        # Extract the corresponding Idd value
        iquie = Idd[index]
        logger.debug(f"iquie (Idd when input = 0.9): {iquie}")
    else:
        iquie = None
        logger.debug("No matching input value found.")

    voff = np.abs(output_vals - input_vals)  # Offset voltage
    voff_max = np.max(np.abs(output_vals - input_vals))
    # Define thresholds 20%
    threshold_idd = iquie - iquie * 0.1

    # Find index ranges
    # 10% for output
    indices_idd = np.where(Idd > threshold_idd)[0]
    indices_voff = np.where(voff < voff_max * 0.9)[0]
    logger.debug(f"idd valid = {indices_idd}")
    logger.debug(f"voff valid = {indices_voff}")
    # Handle different cases
    if len(indices_idd) > 0 and len(indices_voff) > 0:
        ic_min_idd = input_vals[indices_idd[0]]
        ic_min_voff = input_vals[indices_voff[0]]
        ic_max_idd = input_vals[indices_idd[-1]]
        ic_max_voff = input_vals[indices_voff[-1]]
        ic_min = np.max([ic_min_idd, ic_min_voff])
        ic_max = np.min([ic_max_idd, ic_max_voff])
        icmr_out = ic_max - ic_min
    elif len(indices_idd) > 0:
        ic_max = 1.8
        ic_min = input_vals[indices_idd[0]]
        icmr_out = 1.8 - ic_min
    else:
        # If no valid indices found, set output to 0
        logger.warning("No valid range found for ICMR calculation.")
        ic_max = ic_min = 0
        icmr_out = 0  # No valid range found

    return icmr_out


def compute_leakage_power(logfile: str, vdd: float = 1.8) -> float:
    """
    Calculates the static power consumption from a simulation log file.

    This function reads simulation data from a specified log file, extracts the output current,
    estimates the static (leakage) current by identifying periods where the current is stable,
    and computes the static power as the product of the leakage current and the supply voltage.

    Args:
        logfile (str): Path to the simulation log file (CSV format).
        vdd (float, optional): Supply voltage in volts. Defaults to 1.8.

    Returns:
        float: Estimated static power consumption in watts, or None if static current cannot be determined.

    Notes:
        - The log file is expected to have either 3 or 6 columns.
        - The function assumes the output current is in the fourth column (index 3).
        - Static current is estimated by averaging current values where the difference between
          consecutive samples is below a threshold (5e-7).
    """

    def calculate_static_current(simulation_data):
        static_currents = []
        threshold = 5e-7
        for i in range(1, len(simulation_data)):
            current_diff = np.abs(simulation_data[i] - simulation_data[i - 1])
            if current_diff <= threshold:
                static_currents.append(simulation_data[i])
        return np.mean(static_currents) if static_currents else None

    data_trans = np.genfromtxt(logfile, skip_header=1)

    if data_trans.ndim == 1 or data_trans.shape[1] < 4:
        raise ValueError(
            "Log file must have at least 4 columns with current in the 4th column."
        )

    iout = data_trans[:, 3]
    Ileak = calculate_static_current(iout)

    if Ileak is None:
        return None

    static_power = np.abs(Ileak * vdd)
    return static_power


def compute_cmrr(
    ac_diff_file: str, tran_diff_file: str, ac_cm_file: str, tran_cm_file: str
) -> float:
    """
    Computes the Common-Mode Rejection Ratio (CMRR) from AC and transient analysis data files.

    Parameters:
        ac_diff_file (str): Path to the AC analysis data file for differential input.
        tran_diff_file (str): Path to the transient analysis data file for differential input.
        ac_cm_file (str): Path to the AC analysis data file for common-mode input.
        tran_cm_file (str): Path to the transient analysis data file for common-mode input.

    Returns:
        tuple:
            cmrr_tran (float): CMRR calculated from transient analysis data, in dB.
            cmrr_ac (float): CMRR calculated from AC analysis data, in dB.

    Notes:
        - The function expects the input files to be in a format readable by numpy.genfromtxt.
        - The AC data files should contain either 3 columns (single output node) or 6 columns (two output nodes).
        - The function calculates the CMRR as the ratio of differential gain to common-mode gain, expressed in decibels (dB).

    """

    # Get A_{diff}
    data_ac_vd = np.genfromtxt(ac_diff_file)
    num_columns = data_ac_vd.shape[1]
    # for one output node
    if num_columns == 3:
        vd = data_ac_vd[:, 1] + 1j * data_ac_vd[:, 2]

    # for 2 output nodes
    elif num_columns == 6:
        vd = data_ac_vd[:, 4] + 1j * data_ac_vd[:, 5]

    data_tran_vd = np.genfromtxt(tran_diff_file)
    out = data_tran_vd[:, 1]
    altitude_vd = np.max(out) - np.min(out)

    # Get A_{cm}
    data_ac_vc = np.genfromtxt(ac_cm_file)
    if num_columns == 3:
        vc = data_ac_vc[:, 1] + 1j * data_ac_vc[:, 2]

    # for 2 output nodes
    elif num_columns == 6:
        vc = data_ac_vc[:, 4] + 1j * data_ac_vc[:, 5]

    data_tran_vc = np.genfromtxt(tran_cm_file)
    out_vc = data_tran_vc[:, 1]
    altitude_vc = np.max(out_vc) - np.min(out_vc)

    cmrr_tran = 20 * np.log10(np.abs(altitude_vd / altitude_vc))
    cmrr_ac = 20 * np.log10(np.abs(vd[0] / vc[0]))

    return cmrr_tran, cmrr_ac

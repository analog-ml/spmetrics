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

    # return ubw

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

    initial_phase = phase[0]
    tolerance = 15
    if np.isclose(initial_phase, 180, atol=tolerance):
        return phase_at_0_dB
    elif np.isclose(initial_phase, 0, atol=tolerance):
        return 180 - np.abs(phase_at_0_dB)
    else:
        return 0


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

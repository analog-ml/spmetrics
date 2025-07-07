# Understanding SPICE Code

```spice
.control dc Vcm 0 1.8 0.001 
wrdata output\_dc\_icmr.dat {output\_node} I(vdd) 
.endc
```


### Full Explanation of the Control Block

```spice
.control
  dc Vcm 0 1.8 0.001
  wrdata output_dc_icmr.dat {output_node} I(vdd)
.endc
```

#### 1\. `.control ... .endc`

This defines a control block in NGSpice. Commands inside this block are not part of the regular netlist but are instructions for the simulation process.

---

#### 2\. `dc Vcm 0 1.8 0.001`

This runs a **DC sweep analysis**, where:

-   `Vcm` is the name of a voltage source defined elsewhere in your circuit.
    
-   The source is swept from 0 V to 1.8 V in 1 mV (0.001 V) steps.
    

NGSpice will compute the circuit’s DC operating point for each value of `Vcm`.

---

#### 3\. `wrdata output_dc_icmr.dat {output_node} I(vdd)`

This command writes simulation data to a file during the DC sweep.

-   `output_dc_icmr.dat`: The output filename where the data will be saved.
    
-   `{output_node}`: A placeholder (presumably replaced by the actual node name, like `vout`) — the voltage at this node will be saved.
    
-   `I(vdd)`: This is the **current through the voltage source named `vdd`**.
    

##### What does `I(vdd)` mean?

-   In SPICE, `I(source_name)` gives the current **through the voltage or current source**.
    
-   `I(vdd)` gives the current **drawn from** the `vdd` voltage source.
    
    -   **Positive value** → current flows **into** the positive terminal (source is supplying current).
        
    -   **Negative value** → current flows **into** the negative terminal (reverse current flow).
        

This is typically used to:

-   **Measure power consumption** (Power = V × I).
    
-   Analyze how current draw changes with input voltage (`Vcm`, in this case).
    

---

### Summary

You're sweeping the input common-mode voltage `Vcm` from 0 to 1.8 V, and for each step:

-   Measuring the voltage at `output_node`.
-   Measuring the current drawn from the power supply `vdd`.
-   Writing both values to `output_dc_icmr.dat` for plotting or analysis.


# Understanding Python Code

The function `compute_icmr` estimates the **Input Common Mode Range (ICMR)** of an analog circuit (usually an op-amp) using results from a **DC sweep simulation** with **Ngspice**.

### 🧠 What is ICMR?

**ICMR** is the range of input common-mode voltages over which the circuit (typically a differential amplifier) operates properly. A valid input range ensures:

-   The amplifier stays in its linear region.
    
-   All transistors remain in the correct operating region (usually saturation).
    
-   The output tracks the input reasonably well.
    
-   Power consumption remains within expected bounds.
    

---

### 📥 Input Data

The function assumes that a DC sweep simulation was run in Ngspice and the output data (e.g., input voltage, output voltage, supply current) is saved to a file named `filename_icmr.dat`.

```python
data_dc = np.genfromtxt(f'{filename}_icmr.dat', skip_header=1)
```

This loads the simulation data into a NumPy array. The columns are:

1.  Input common-mode voltage (swept range)
    
2.  Output voltage
    
3.  (Assumed) something else
    
4.  Current consumption (Idd), often the current from VDD
    

Then:

```python
input_vals = data_dc[19:-19, 0]
output_vals = data_dc[19:-19, 1]
Idd = np.abs(data_dc[19:-19, 3])
```

The first and last 19 points are discarded, likely to avoid edge effects or simulation artifacts.

---

### ⚖️ Step-by-step Explanation

#### 1\. **Find Idd when input = 0.9V**

This is a reference point (likely the mid-point of the input sweep).

```python
iquie = Idd at input = 0.9V
```

#### 2\. **Compute Offset Voltage (voff)**

Defined as the difference between output and input voltage:

```python
voff = |Vout - Vin|
```

This helps determine if the amplifier is still in its **linear region** (a low offset implies good tracking).

#### 3\. **Set thresholds:**

-   **Power threshold**: 10% below the reference Idd (`iquie`)
    
-   **Offset threshold**: 90% of the worst offset (i.e., discard badly nonlinear points)
    

These thresholds define conditions under which the amplifier is still **functioning properly**.

#### 4\. **Get valid operating regions**

-   Where `Idd` is reasonably high (i.e., amplifier is powered properly)
    
-   Where `voff` is small (i.e., output tracks input)
    

```python
indices_idd = np.where(Idd > threshold_idd)
indices_voff = np.where(voff < voff_max * 0.9)
```

#### 5\. **Calculate ICMR range**

-   Determine the **overlap** between `Idd`\-valid and `voff`\-valid input ranges.
    
-   Take:
    
    -   `ic_min = max(start of valid Idd, start of valid voff)`
        
    -   `ic_max = min(end of valid Idd, end of valid voff)`
        
    -   `ICMR = ic_max - ic_min`
        

If only Idd condition is satisfied (and not voff), it defaults to:

```python
icmr_out = 1.8 - ic_min
```

Assuming 1.8V is the top of the input sweep range.

---

### ✅ Summary

This function extracts **ICMR** by:

-   Sweeping the input common-mode voltage.
    
-   Checking if the amplifier remains:
    
    -   **Powered** (Idd > threshold)
        
    -   **Linear** (voff < threshold)
        
-   Returning the voltage range where both conditions are true.
    

---

### 💡 Notes

-   The code assumes a specific format and structure of Ngspice output.
    
-   The `0.9V` reference may need adjustment depending on the supply voltage.
    
-   It assumes VDD = 1.8V; for other rails, modify the hardcoded `1.8`.
    

---

Let me know if you'd like help generalizing this function or visualizing the ICMR window from the data.

You: 

Give me more information about Get valid operating regions Where Idd is reasonably high (i.e., amplifier is powered properly) Where voff is small (i.e., output tracks input)

ChatGPT: 

Great — let’s break down the **“Get valid operating regions”** step more thoroughly. This step is **critical** to determining when the amplifier is working **correctly** during the input common-mode voltage sweep.

---

## ✅ Objective

During an ICMR test, you're sweeping the **common-mode input voltage** and monitoring:

1.  **Power consumption (Idd)** — the amplifier must be properly biased.
    
2.  **Tracking behavior** (|Vout − Vin| ≈ 0) — the amplifier must stay in its **linear operating region**, not saturated or cutoff.
    

The **valid region** for ICMR is the **intersection** of these two conditions.

---

## 🧪 Criterion 1: **Valid Idd range**

```python
threshold_idd = iquie - iquie * 0.1  # 10% drop from quiescent Idd
indices_idd = np.where(Idd > threshold_idd)[0]
```

### 🔍 What's happening here?

-   `iquie` is the **quiescent current**, measured at a known good operating point (e.g., when `Vin = 0.9V`).
    
-   If Idd drops **significantly** (more than 10%), it may indicate:
    
    -   One or more transistors entering **cutoff**.
        
    -   The tail current source collapsing (common in differential pairs).
        
    -   Improper biasing.
        
-   So `threshold_idd` defines a **minimum current level** below which the circuit is considered **non-functional**.
    

### ✅ Meaning:

`indices_idd` gives you input voltage indices where the amplifier is drawing "enough" current — i.e., **powered and active**.

---

## 🧪 Criterion 2: **Valid output tracking (voff)**

```python
voff = np.abs(output_vals - input_vals)
voff_max = np.max(voff)
indices_voff = np.where(voff < voff_max * 0.9)[0]
```

### 🔍 What's happening here?

-   `voff` is the **voltage error**: how far is the output from following the input?
    
-   Large voff indicates the amplifier:
    
    -   Has entered **nonlinear** operation.
        
    -   Is **saturated** (top rail) or **cut off** (bottom rail).
        
-   This test finds points where `voff` is **less than 90% of the worst-case offset** → i.e., output still tracks reasonably well.
    

> This isn’t a fixed numerical threshold, but a **relative** one — allows for adaptive filtering.

### ✅ Meaning:

`indices_voff` gives you input voltage indices where the output is **still reasonably linear**.

---

## 🔁 Combine Both

```python
ic_min = max(input_vals[indices_idd[0]], input_vals[indices_voff[0]])
ic_max = min(input_vals[indices_idd[-1]], input_vals[indices_voff[-1]])
icmr_out = ic_max - ic_min
```

This is computing the **intersection** of the two valid regions:

-   The amplifier **draws enough current**, and
    
-   The amplifier **stays linear** (output ≈ input).
    

The resulting `icmr_out` is the **Input Common Mode Range** — the span of input voltages where both conditions are satisfied.

---

## 📊 Illustration

If you plotted this:

-   **X-axis**: `Vin_cm` (input common-mode voltage sweep)
    
-   **Y-axis**: `Idd` and `voff`
    

You would see:

-   `Idd` dropping off at low or high Vin, forming a valid **Idd window**.
    
-   `voff` increasing at extremes of Vin, forming a valid **voff window**.
    
-   The **intersection of both** defines your ICMR.
    

---

## 💡 Practical Note

This method is robust because:

-   It does **not rely on a hardcoded range**.
    
-   It uses **relative thresholds**, adapting to the circuit behavior.
    

However:

-   You can make the method **more precise** by adjusting the thresholds (e.g., 5% instead of 10%).
    
-   You might also add **voltage clipping** (e.g., limit to \[0V, VDD\]) to avoid simulation artifacts.
    

---

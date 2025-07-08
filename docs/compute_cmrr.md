This function `compute_cmrr` is designed to compute the **Common-Mode Rejection Ratio (CMRR)** of an analog circuit (typically an op-amp or differential amplifier) using results from **NGSpice simulations**—specifically **AC and transient analysis logs**.

Let’s break it down step by step:

---

### ✅ **What is CMRR?**

CMRR is defined as:

$$
\text{CMRR} = 20 \cdot \log_{10}\left( \frac{A_{\text{diff}}}{A_{\text{cm}}} \right)
$$

Where:

-   $A_{\text{diff}}$ is the **differential gain** (when a differential input is applied)
    
-   $A_{\text{cm}}$ is the **common-mode gain** (when the same signal is applied to both inputs)
    

A high CMRR means the circuit rejects common-mode signals effectively, which is crucial for differential amplifiers.

---

### 🧠 **What This Function Does**

#### 1\. **Reads Differential Mode Results**

-   `output_ac.dat` and `output_tran.dat` are assumed to be simulation outputs from a run where a **differential input** (Vid) was applied and **common-mode voltage source (Vcm) was off or zero**.
    
-   From `output_ac.dat`, it extracts `vd`: the complex output voltage in frequency domain (AC analysis).
    
-   From `output_tran.dat`, it extracts `altitude_vd`: the peak-to-peak output amplitude in time domain (transient analysis).
    

#### 2\. **(Commented) Prepare Common Mode Test**

-   It shows how to **modify the netlist** to switch from differential to common-mode testing:
    
    -   `Vid` is turned off
        
    -   `Vcm` is activated with `AC 1` (for AC analysis) and a sinusoidal signal (for transient)
        

**NOTE**: This part is **commented out**, so you would need to actually run a second simulation for common-mode testing manually or by uncommenting and enhancing this part.

#### 3\. **Reads Common Mode Results**

-   It again reads from `output_ac.dat` and `output_tran.dat`, but this time it's assumed that they now contain results from a **common-mode input** simulation.
    
-   It extracts `vc` and `altitude_vc`, the output under common-mode excitation.
    

#### 4\. **Calculates CMRR**

-   Two types of CMRR are computed:
    
    -   `cmrr_ac`: computed using complex voltage ratio from AC analysis at one frequency (typically the first frequency point).
        
    -   `cmrr_tran`: computed using peak-to-peak amplitudes from transient simulation.
        

---

### ⚠️ **Important Assumptions & Requirements**

-   The function **assumes** that:
    
    -   `output_ac.dat` and `output_tran.dat` contain results for *differential* input first and then get overwritten with *common-mode* results.
        
    -   You’ve run NGSpice **twice**: once for differential mode and once for common mode, and replaced the output files accordingly.
        
-   `np.genfromtxt` is used to load data. This assumes the files are well-formatted, whitespace-delimited.
    

---

### ✅ **How You Can Use This Practically**

1.  **Run differential mode simulation**
    
    -   Input: Vid with `AC 1`, Vcm = 0
        
    -   Save `output_ac.dat`, `output_tran.dat`
        
2.  **Rename or store the differential output data**, or call this function once with them.
    
3.  **Modify the netlist for common-mode excitation**
    
    -   Input: Vcm with `AC 1`, Vid = 0
        
    -   Rerun NGSpice
        
4.  **Ensure `output_ac.dat` and `output_tran.dat` now have the common-mode data**
    
5.  **Call the function again** – or make sure both datasets are available when calling `compute_cmrr`
    

---

### 🧪 Example Workflow

```python
cmrr = compute_cmrr("output_ac.dat")
print(f"CMRR: {cmrr:.2f} dB")
```

But again — the current implementation always reads the same filenames, so you need to:

-   Call it twice **with different file content**, or
    
-   Modify the function to accept **separate filenames** for diff-mode and cm-mode
    

---

### 🔧 Suggestions for Improvement

To make it robust and practical:

1.  **Pass file names as arguments**:
    
    ```python
    def compute_cmrr(ac_diff_file, tran_diff_file, ac_cm_file, tran_cm_file)
    ```
    
2.  **Ensure frequency of interest is selected** if multiple points are in the AC response.
    

---

Let me know if you'd like me to modify and rewrite the function to follow a cleaner interface!

You: 

Why this line (vc = data\_ac\_vc\[:, 1\] + 1j \* data\_ac\_vc\[:, 2\]) is corresponding to calculating A\_{cm} ?

ChatGPT: 

Great question.

The line:

```python
vc = data_ac_vc[:, 1] + 1j * data_ac_vc[:, 2]
```

extracts the **complex output voltage** (`vc`) from the **AC analysis result**, assuming the simulation was run with a **common-mode input** (i.e., both inputs driven identically, and differential input disabled).

---

### 🔍 Why does this represent $A_{\text{cm}}$ (common-mode gain)?

Because:

-   This line is executed **after the simulation was modified to apply a common-mode signal** (see the commented-out netlist modification):
    
    ```spice
    Vcm cm 0 DC 0.9 SIN(0 1u 10k 0 0) AC 1
    Vid diffin 0 DC 0  ; effectively disables differential input
    ```
    
-   Under this condition:
    
    -   The **input signal** is **common to both amplifier inputs**
        
    -   The **output** (`vc`) reflects the circuit's response to this **common-mode excitation**
        

Thus, `vc` in this case is:

$$
V_{\text{out, cm}} = A_{\text{cm}} \cdot V_{\text{cm}}
$$

But since the AC input magnitude is 1 (`AC 1`), the output voltage (`vc`) directly gives you the gain:

$$
A_{\text{cm}} = V_{\text{out, cm}} \quad (\text{because } V_{\text{in}} = 1)
$$

---

### ✅ Summary:

-   `vc` is computed from the output voltage **in response to a common-mode AC signal**
    
-   The circuit's gain to this signal is the **common-mode gain $A_{\text{cm}}$**
    
-   Therefore, `vc` represents $A_{\text{cm}}$, and when you compute `cmrr_ac` using:
    
    ```python
    cmrr_ac = 20 * np.log10(np.abs(vd[0] / vc[0]))
    ```
    
    you are calculating:
    
    $$
    \text{CMRR}_{\text{AC}} = 20 \log_{10} \left| \frac{A_{\text{diff}}}{A_{\text{cm}}} \right|
    $$
    

Let me know if you want a schematic or SPICE example to visualize this better!

You: 

What are the differences between `cmrr_tran` and `cmrr_ac` ? which is more common?

ChatGPT: 

Great follow-up! The two metrics `cmrr_tran` and `cmrr_ac` differ in **how they are measured**, **what they reveal**, and **how commonly they are used in analog design**. Let's break them down:

---

## 🧪 `cmrr_ac`: **AC (Small-Signal) CMRR**

### ✅ **How it's computed**

-   Based on **frequency-domain AC analysis**.
    
-   Uses:
    
    ```python
    cmrr_ac = 20 * log10(|vd[0] / vc[0]|)
    ```
    
    where:
    
    -   `vd[0]` = differential output gain (from AC analysis)
        
    -   `vc[0]` = common-mode output gain (from AC analysis)
        
-   Assumes **linear, small-signal behavior**.
    

### 📋 **Characteristics**

-   Captures CMRR at a **specific frequency** (often 1 kHz or low frequency).
    
-   Ideal for small-signal, linear characterization.
    
-   Fast and accurate for frequency-dependent behavior.
    
-   Useful when sweeping frequency to get **CMRR vs frequency plot**.
    

### ✅ **Most commonly reported in datasheets and papers.**

---

## ⏱️ `cmrr_tran`: **Transient (Large-Signal) CMRR**

### ✅ **How it's computed**

-   Based on **time-domain transient simulation**.
    
-   Uses:
    
    ```python
    cmrr_tran = 20 * log10(altitude_vd / altitude_vc)
    ```
    
    where:
    
    -   `altitude_vd`: peak-to-peak output from **differential input**
        
    -   `altitude_vc`: peak-to-peak output from **common-mode input**
        

### 📋 **Characteristics**

-   Reflects **large-signal** or **nonlinear behavior**.
    
-   Can be affected by slew rate, distortion, and mismatch.
    
-   More realistic in circuits with **non-idealities** or under **large input swings**.
    
-   Takes longer to simulate and is sensitive to simulation setup.
    

---

## ✅ Which is More Common?

| Aspect | `cmrr_ac` | `cmrr_tran` |
| --- | --- | --- |
| Use in design specs | ✅ Most common | ❌ Less common |
| Frequency sweep | ✅ Yes | ❌ No |
| Captures nonlinearities | ❌ No | ✅ Yes |
| Simulation time | ✅ Fast | ❌ Slower |
| Matches datasheets | ✅ Yes | ❌ Rarely |
| Typical use cases | Design/debug/testbench | Large-signal verification |

---

### 🔚 Final Answer:

-   **`cmrr_ac` is more commonly used and reported**, because it aligns with datasheet specs, gives frequency-domain insights, and is fast to simulate.
    
-   **`cmrr_tran`** can be used to verify behavior under large signals or detect non-ideal rejection in time-domain, but it's less common as a formal spec.
    

Let me know if you'd like to plot CMRR vs frequency or set up a testbench for either case!

You: 

What is the meaning of this code altitude\_vd = np.max(out) - np.min(out)

ChatGPT: 

The line:

```python
altitude_vd = np.max(out) - np.min(out)
```

computes the **peak-to-peak amplitude** (also called **signal swing** or **voltage range**) of the output waveform `out` from a transient (time-domain) simulation.

---

### 🧠 What does it mean?

-   `out` is a NumPy array containing **voltage values over time** from `output_tran.dat`, which is the result of a **transient simulation**.
    
-   `np.max(out)` gives the **highest voltage** reached in the output waveform.
    
-   `np.min(out)` gives the **lowest voltage** reached.
    
-   The difference is the **peak-to-peak output voltage**, i.e., how much the output "swings" up and down during the simulation.
    

$$
\text{altitude\_vd} = V_{\text{max}} - V_{\text{min}} = V_{\text{pp (peak-to-peak)}}
$$

---

### 📈 Example

Imagine the output voltage waveform `out` looks like a sine wave going from 0.6 V to 1.2 V:

```python
np.max(out) = 1.2
np.min(out) = 0.6
altitude_vd = 1.2 - 0.6 = 0.6 V
```

So `altitude_vd = 0.6 V` is the output swing due to the **differential input**.

---

### ✅ Why is this used?

This value is used to compute `cmrr_tran`:

```python
cmrr_tran = 20 * np.log10(altitude_vd / altitude_vc)
```

So you're comparing how much the output swings for a differential input (`altitude_vd`) vs. a common-mode input (`altitude_vc`) — that’s a **time-domain definition of CMRR**.

---

Let me know if you'd like a waveform example or how this would look in a SPICE simulation!

You: 

Give me more information about time-domain definition of CMRR

ChatGPT: 

Sure! Let's dive into the **time-domain definition of CMRR** — how it's derived, why it's used, and how it compares to the frequency-domain version.

---

## 🧾 **CMRR Definition (General)**

The **Common-Mode Rejection Ratio (CMRR)** measures how well a **differential amplifier** rejects signals that are common to both inputs (i.e., common-mode signals).

$$
\text{CMRR} = \left| \frac{A_{\text{diff}}}{A_{\text{cm}}} \right| \quad \text{or in dB:} \quad \text{CMRR}_{\text{dB}} = 20 \cdot \log_{10}\left( \left| \frac{A_{\text{diff}}}{A_{\text{cm}}} \right| \right)
$$

Where:

-   $A_{\text{diff}}$: Gain for differential input
    
-   $A_{\text{cm}}$: Gain for common-mode input
    

---

## ⏱️ **Time-Domain Definition of CMRR**

In the **time domain**, you apply **two separate transient simulations**:

1.  **Differential input**: Apply a small sinusoidal signal (or any signal) to the two inputs in opposite directions (e.g., +0.5 mV to one input, −0.5 mV to the other).
    
2.  **Common-mode input**: Apply the same signal to both inputs (e.g., +0.5 mV to both).
    

Then, you **measure the peak-to-peak swing** of the output in each case:

$$
\text{CMRR}_{\text{tran}} = 20 \cdot \log_{10}\left( \frac{V_{\text{pp, diff}}}{V_{\text{pp, cm}}} \right)
$$

Where:

-   $V_{\text{pp, diff}}$: Peak-to-peak output voltage in response to a **differential input**
    
-   $V_{\text{pp, cm}}$: Peak-to-peak output voltage in response to a **common-mode input**
    

---

### 🧪 Why Use Time-Domain CMRR?

Time-domain CMRR is particularly useful when:

-   You want to analyze **large-signal behavior**.
    
-   You want to verify **nonlinear effects**, like distortion or asymmetry.
    
-   You have a **nonlinear or time-varying** circuit where small-signal (AC) analysis is insufficient.
    
-   You’re working with **realistic input waveforms**, such as sinusoidal or step signals.
    

---

### 📊 Comparison: AC vs Transient CMRR

| Feature | `cmrr_ac` (Frequency-Domain) | `cmrr_tran` (Time-Domain) |
| --- | --- | --- |
| Based on | Linearized small-signal model | Time-domain waveform behavior |
| Captures | Frequency-dependent behavior | Large-signal behavior, asymmetry |
| Input type | AC signal (e.g., 1 V @ 1 kHz) | Realistic waveform (sine, pulse, etc.) |
| Common usage | Design specs, datasheets | Post-layout validation, stress tests |
| Simulation speed | Fast | Slower |
| Accuracy in non-ideal cases | Limited | High (if well set up) |

---

### ⚠️ Notes

-   Time-domain CMRR is **not standardized** like AC CMRR.
    
-   It's more sensitive to:
    
    -   Signal amplitude
        
    -   Slew rate and bandwidth
        
    -   Biasing and symmetry
        
-   Peak-to-peak measurement is a **simplified approximation** — real systems may need FFT-based analysis for more precision.
    

---

### 🖼️ Visual Example

Imagine two transient waveforms:

-   Differential input causes the output to swing **0.6 V peak-to-peak**
    
-   Common-mode input causes a small output swing of **0.01 V**
    

Then:

$$
\text{CMRR}_{\text{tran}} = 20 \cdot \log_{10}\left( \frac{0.6}{0.01} \right) = 20 \cdot \log_{10}(60) \approx 35.6\,\text{dB}
$$


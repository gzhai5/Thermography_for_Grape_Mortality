# Manuscript I — Active Thermography System Design and Capability

This directory contains all code, data organization, and documentation related to **Manuscript I**, which focuses on the **design, implementation, and validation of an active thermography system** for non-destructive grape-bud mortality assessment.

---

## 🎯 Research Objectives

- Engineer and document a custom, synchronized pulsed-thermography acquisition system and companion software to collect standardized heating–cooling sequences at the bud scale
-  Quantify separability by extracting informative waveform features and applying a principled statistical analysis plan (mixed-effects modeling) to compare intact vs damaged buds within cultivars
- Investigate mechanisms and factors that can explain differences in thermal responses and guide protocol design

---

## 🔧 Hardware System

The active thermography system consists of a synchronized heating and thermal imaging setup designed for repeatable, high-resolution measurements.

**Core components include:**
- Pulsed heat excitation source
- High-resolution thermal camera
- Custom mounting and alignment fixtures
- Hardware triggering and synchronization

📷 **System overview**

![Hardware System](readme_files/hardware_system.png)

🎥 **Data acquisition demo**

<video src="readme_files/daq_demo.mov" controls width="720">
  <a href="readme_files/daq_demo.mov">▶ Download acquisition demo (.mov)</a>
</video>

## 💻 Software System

Two graphical user interfaces (GUIs) were developed to support data collection and quality control:

### 1️⃣ Acquisition GUI
- Controls heating pulse timing
- Synchronizes thermal image acquisition
- Ensures consistent acquisition parameters across experiments

### 2️⃣ Validation GUI
- Real-time visualization of thermal frames
- ROI placement and inspection
- Metadata annotation and sample tracking

📷 **GUI Overview**

![GUI Overview](readme_files/guis.png)

---

## 📊 Data Products

### Thermal ROI Data
- Format: `.npy`
- Shape: `21 × 21 × 600` (spatial × spatial × time)
- One file per grape bud sample

Each file represents the spatiotemporal thermal response of a single bud during a controlled heating–cooling cycle.

### Metadata & Feature Tables
Stored as `.csv` files containing:
- Experimental metadata (`cultivar`, `treatment`, `dev_stage`, `cane`, `segment`)
- Mortality ground truth
- Extracted waveform features
- PCA components derived from time-series data

---

## 🎥 Example Thermal Responses

Below is a qualitative comparison of thermal behavior between viable and non-viable buds.

- **Viable bud:** smooth rise during heating, gradual decay during cooling
- **Non-viable bud:** altered slope, delayed response, or suppressed amplitude

**Viable bud**

<video src="readme_files/data_sample_alive.mp4" controls width="480">
  <a href="readme_files/data_sample_alive.mp4">▶ Download viable bud demo (.mp4)</a>
</video>

**Non-viable bud**

<video src="readme_files/data_sample_dead.mp4" controls width="480">
  <a href="readme_files/data_sample_dead.mp4">▶ Download non-viable bud demo (.mp4)</a>
</video>

📈 **Mean time-series curve comparison**

![Mean Curve Comparison](readme_files/mean_curve_compare.png)

---

## 🧩 ROI Extraction & Preprocessing

### Region of Interest (ROI) Extraction
- Bud-centered ROIs extracted from thermal frames
- Fixed spatial size to ensure consistency across samples

![ROI Extraction Example](readme_files/roi_extract.png)

### Temporal Normalization
- Frame-wise normalization to control for baseline temperature variation
- Ensures comparability across sessions and cultivars

![Normalization Comparison](readme_files/normalization.png)

### Feature Engineering
Features extracted from heating and cooling phases include:
- Rising and falling slopes
- Peak temperature
- Temporal variability metrics

![Waveform Feature Extraction](readme_files/waveform_extraction.png)

---

## ⚠️ Data Quality Control

Certain samples exhibit abnormal thermal responses (e.g., non-physical box-shaped heating curves), typically caused by:
- Sensor artifacts
- Misalignment
- Improper heating contact

These samples are:
- Explicitly identified
- Stored in separate folders or labeled in metadata
- **Excluded from modeling and statistical analysis**

![Normal vs Abnormal Curves](readme_files/normal_vs_abnormal.png)

---

## 📐 Statistical Analysis

To evaluate whether thermal responses differ systematically between viable and non-viable buds, we apply:

- Mixed-effects modeling to account for:
  - Cultivar
  - Treatment
  - Experimental round
  - Cane and segment effects
- Within-cultivar comparisons to isolate mortality effects

![Statistical Test Results](readme_files/statistical_test_results.png)

These analyses establish the **statistical separability** of mortality states and motivate the modeling work in Manuscript II.

---

## 📌 Notes

This manuscript focuses on **system engineering, experimental validation, and statistical capability analysis**.
No machine-learning model benchmarking or predictive performance comparisons are reported here.

For modeling and classification analysis, see **Manuscript II**:

➡️ [`Manuscript II — Modeling & Analysis`](../model_analysis/README.md)

---

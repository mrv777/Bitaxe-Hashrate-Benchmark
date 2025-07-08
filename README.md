# **Bitaxe Hashrate Benchmark**

A Python-based benchmarking tool for optimizing Bitaxe mining performance by testing different voltage and frequency combinations while monitoring hashrate, temperature, and power efficiency.

## **Features**

* Automated benchmarking of different voltage/frequency combinations  
* **Direct setting of specific voltage and frequency from command line**  
* Temperature monitoring and safety cutoffs  
* **Power consumption monitoring and reporting (Watts)**  
* **Fan speed monitoring and reporting (RPM/Percentage)**  
* Power efficiency calculations (J/TH)  
* Automatic saving of benchmark results  
* Graceful shutdown with best settings retention  
* Docker support for easy deployment

## **Prerequisites**

* Python 3.11 or higher  
* Access to a Bitaxe miner on your network  
* Docker (optional, for containerized deployment)  
* Git (optional, for cloning the repository)

## **Installation**

### **Standard Installation**

1. Clone the repository:  
   git clone https://github.com/mrv777/Bitaxe-Hashrate-Benchmark.git  
   cd Bitaxe-Hashrate-Benchmark

2. Create and activate a virtual environment:  
   python \-m venv venv  
   \# On Windows  
   venv\\Scripts\\activate  
   \# On Linux/Mac  
   source venv/bin/activate

3. Install dependencies:  
   pip install \-r requirements.txt

### **Docker Installation**

1. Build the Docker image:  
   docker build \-t bitaxe-benchmark .

## **Usage**

### **Standard Usage (Run Full Benchmark)**

Run the benchmark tool by providing your Bitaxe's IP address and initial settings:  
python bitaxe\_hasrate\_benchmark.py \<bitaxe\_ip\> \-v \<initial\_voltage\> \-f \<initial\_frequency\>

**Arguments:**

* \<bitaxe\_ip\>: **Required.** IP address of your Bitaxe miner (e.g., 192.168.2.26).  
* \-v, \--voltage: **Optional.** Initial voltage in mV for testing (default: 1150).  
* \-f, \--frequency: **Optional.** Initial frequency in MHz for testing (default: 500).

**Example:**  
python bitaxe\_hasrate\_benchmark.py 192.168.1.136 \-v 1150 \-f 500

### **Apply Specific Settings (Without Benchmarking)**

To quickly apply specific voltage and frequency settings to your Bitaxe without running the full benchmark:  
python bitaxe\_hasrate\_benchmark.py \<bitaxe\_ip\> \--set-values \-v \<desired\_voltage\_mv\> \-f \<desired\_frequency\_mhz\>

**Arguments:**

* \<bitaxe\_ip\>: **Required.** IP address of your Bitaxe miner.  
* \-s, \--set-values: **Flag.** Activates this mode to only set values and exit.  
* \-v, \--voltage: **Required.** The exact voltage in mV to apply.  
* \-f, \--frequency: **Required.** The exact frequency in MHz to apply.

**Example:**  
python bitaxe\_hasrate\_benchmark.py 192.168.1.136 \--set-values \-v 1150 \-f 780

### **Docker Usage (Optional)**

Run the container with your Bitaxe's IP address (add \--set-values for that mode):  
docker run \--rm bitaxe-benchmark \<bitaxe\_ip\> \[options\]

Example (Full Benchmark):  
docker run \--rm bitaxe-benchmark 192.168.2.26 \-v 1200 \-f 550

Example (Set Settings Only):  
docker run \--rm bitaxe-benchmark 192.168.2.26 \--set-values \-v 1150 \-f 780

## **Configuration**

The script includes several configurable parameters. These can be adjusted in the bitaxe\_hasrate\_benchmark.py file:

* Maximum chip temperature: 66°C  
* Maximum VR temperature: 86°C  
* Maximum allowed voltage: 1400mV  
* Minimum allowed voltage: 1000mV  
* Maximum allowed frequency: 1200MHz  
* Maximum power consumption: 30W  
* Minimum allowed frequency: 400MHz  
* Minimum input voltage: 4800mV  
* Maximum input voltage: 5500mV  
* Benchmark duration: 600 seconds (10 minutes per combination)  
* Sample interval: 15 seconds  
* Minimum required samples: 7 (for valid data processing)  
* Voltage increment: 15mV  
* Frequency increment: 20MHz  
* **ASIC Configuration:** asic\_count is hardcoded to 1 as it's not always provided by the API. small\_core\_count is fetched from the Bitaxe.

## **Output**

The benchmark results are saved to bitaxe\_benchmark\_results\_\<ip\_address\>.json, containing:

* Complete test results for all combinations  
* Top 5 performing configurations ranked by hashrate  
* Top 5 most efficient configurations ranked by J/TH  
* For each configuration:  
  * Average hashrate (with outlier removal)  
  * Temperature readings (excluding initial warmup period)  
  * VR temperature readings (when available)  
  * Power efficiency metrics (J/TH)  
  * **Average Power (Watts)**  
  * **Average Fan Speed (Percentage or RPM, if available from API)**  
  * Input voltage measurements  
  * Voltage/frequency combinations tested  
  * Error reason (if any) for a specific iteration

## **Safety Features**

* Automatic temperature monitoring with safety cutoff (66°C chip temp)  
* Voltage regulator (VR) temperature monitoring with safety cutoff (86°C)  
* Input voltage monitoring with minimum threshold (4800mV) and maximum threshold (5500mV)  
* Power consumption monitoring with safety cutoff (30W)  
* Temperature validation (must be above 5°C)  
* Graceful shutdown on interruption (Ctrl+C)  
* Automatic reset to best performing settings after benchmarking  
* Input validation for safe voltage and frequency ranges  
* Hashrate validation to ensure stability  
* Protection against invalid system data  
* Outlier removal from benchmark results

## **Benchmarking Process**

The tool follows this process:

1. Starts with user-specified or default voltage/frequency  
2. Tests each combination for 10 minutes  
3. Validates hashrate is within 8% of theoretical maximum  
4. Incrementally adjusts settings:  
   * Increases frequency if stable  
   * Increases voltage if unstable  
   * Stops at thermal or stability limits  
5. Records and ranks all successful configurations  
6. Automatically applies the best performing stable settings  
7. Restarts system after each test for stability  
8. Allows 90-second stabilization period between tests

## **Data Processing**

The tool implements several data processing techniques to ensure accurate results:

* Removes 3 highest and 3 lowest hashrate readings to eliminate outliers  
* Excludes first 6 temperature readings during warmup period  
* Validates hashrate is within 6% of theoretical maximum  
* Averages power consumption across entire test period  
* Monitors VR temperature when available  
* Calculates efficiency in Joules per Terahash (J/TH)  
* **Averages fan speed across entire test period**

## **Contributing**

Contributions are welcome\! Please feel free to submit a Pull Request.

## **License**

This project is licensed under the GNU General Public License v3.0 \- see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

## **Disclaimer**

Please use this tool responsibly. Overclocking and voltage modifications can potentially damage your hardware if not done carefully. Always ensure proper cooling and monitor your device during benchmarking.
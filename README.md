# Bitaxe Hashrate Benchmark

A Python-based benchmarking tool for optimizing Bitaxe mining performance by testing different voltage and frequency combinations while monitoring hashrate, temperature, and power efficiency.

## Features

- Automated benchmarking of different voltage/frequency combinations
- Temperature monitoring and safety cutoffs
- Power efficiency calculations (J/TH)
- Automatic saving of benchmark results
- Graceful shutdown with best settings retention
- Docker support for easy deployment

## Prerequisites

- Python 3.11 or higher
- Access to a Bitaxe miner on your network
- Docker (optional, for containerized deployment)
- Git (optional, for cloning the repository)

## Installation

### Standard Installation

1. Clone the repository:
```bash
git clone https://github.com/mrv777/Bitaxe-Hashrate-Benchmark.git
cd Bitaxe-Hashrate-Benchmark
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t bitaxe-benchmark .
```

## Usage

### Standard Usage

Run the benchmark tool by providing your Bitaxe's IP address:

```bash
python bitaxe_hashrate_benchmark.py <bitaxe_ip>
```

Optional parameters:
- `-v, --voltage`: Initial voltage in mV (default: 1150)
- `-f, --frequency`: Initial frequency in MHz (default: 500)

Example:
```bash
python bitaxe_hashrate_benchmark.py 192.168.2.29 -v 1175 -f 775
```

### Docker Usage (Optional)

Run the container with your Bitaxe's IP address:

```bash
docker run --rm bitaxe-benchmark <bitaxe_ip> [options]
```

Example:
```bash
docker run --rm bitaxe-benchmark 192.168.2.26 -v 1200 -f 550
```

## Configuration

The script includes several configurable parameters:

- Maximum chip temperature: 66°C
- Maximum VR temperature: 86°C
- Maximum allowed voltage: 1400mV
- Minimum allowed voltage: 1000mV
- Maximum allowed frequency: 1200MHz
- Maximum power consumption: 40W
- Minimum allowed frequency: 400MHz
- Minimum input voltage: 4800mV
- Maximum input voltage: 5500mV
- Benchmark duration: 10 minutes
- Sample interval: 15 seconds
- Sleep time before benchmark: 90 seconds
- **Minimum required samples: 7** (for valid data processing)
- Voltage increment: 20mV
- Frequency increment: 25MHz

## Output

The benchmark results are saved to `bitaxe_benchmark_results_<ip_address>.json`, containing:
- Complete test results for all combinations
- Top 5 performing configurations ranked by hashrate
- Top 5 most efficient configurations ranked by J/TH
- For each configuration:
  - Average hashrate (with outlier removal)
  - Temperature readings (excluding initial warmup period)
  - VR temperature readings (when available)
  - Power efficiency metrics (J/TH)
  - Input voltage measurements
  - Voltage/frequency combinations tested

## Safety Features

- Automatic temperature monitoring with safety cutoff (66°C chip temp)
- Voltage regulator (VR) temperature monitoring with safety cutoff (86°C)
- Input voltage monitoring with minimum threshold (4800mV) and maximum threshold (5500mV)
- Power consumption monitoring with safety cutoff (40W)
- Temperature validation (must be above 5°C)
- Graceful shutdown on interruption (Ctrl+C)
- Automatic reset to best performing settings after benchmarking
- Input validation for safe voltage and frequency ranges
- Hashrate validation to ensure stability
- Protection against invalid system data
- Outlier removal from benchmark results

## Benchmarking Process

The tool follows this process:
1. Starts with user-specified or default voltage/frequency
2. Tests each combination for 20 minutes
3. Validates hashrate is within 8% of theoretical maximum
4. Incrementally adjusts settings:
   - Increases frequency if stable
   - Increases voltage if unstable
   - Stops at thermal or stability limits
5. Records and ranks all successful configurations
6. Automatically applies the best performing stable settings
7. Restarts system after each test for stability
8. Allows 90-second stabilization period between tests

## Data Processing

The tool implements several data processing techniques to ensure accurate results:
- Removes 3 highest and 3 lowest hashrate readings to eliminate outliers
- Excludes first 6 temperature readings during warmup period
- Validates hashrate is within 6% of theoretical maximum
- Averages power consumption across entire test period
- Monitors VR temperature when available
- Calculates efficiency in Joules per Terahash (J/TH)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

Please use this tool responsibly. Overclocking and voltage modifications can potentially damage your hardware if not done carefully. Always ensure proper cooling and monitor your device during benchmarking.

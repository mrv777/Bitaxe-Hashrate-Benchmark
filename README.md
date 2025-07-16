# Bitaxe Hashrate Benchmark

A Python-based benchmarking tool for optimizing Bitaxe mining performance by testing different voltage and frequency combinations while monitoring hashrate, temperature, and power efficiency. Now supports parallel benchmarking of multiple miners simultaneously.

## Features

- **Parallel benchmarking** of multiple Bitaxe miners simultaneously
- Automated benchmarking of different voltage/frequency combinations
- Temperature monitoring and safety cutoffs
- Power efficiency calculations (J/TH)
- Thread-safe colored output with miner identification
- Automatic saving of benchmark results per miner
- Graceful shutdown with best settings retention across all miners
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

Run the benchmark tool by providing one or more Bitaxe IP addresses:

```bash
# Single miner
python bitaxe_hashrate_benchmark.py <bitaxe_ip>

# Multiple miners (parallel execution)
python bitaxe_hashrate_benchmark.py <ip1> <ip2> <ip3>
```

Optional parameters:
- `-v, --voltage`: Initial voltage in mV (default: 1150)
- `-f, --frequency`: Initial frequency in MHz (default: 500)

Examples:
```bash
# Single miner
python bitaxe_hashrate_benchmark.py 192.168.2.26

# Multiple miners with default settings
python bitaxe_hashrate_benchmark.py 192.168.2.26 192.168.2.27 192.168.2.28

# Multiple miners with custom voltage and frequency
python bitaxe_hashrate_benchmark.py 192.168.2.26 192.168.2.27 192.168.2.28 -v 1200 -f 525
```

### Docker Usage (Optional)

Run the container with one or more Bitaxe IP addresses:

```bash
# Single miner
docker run --rm bitaxe-benchmark <bitaxe_ip> [options]

# Multiple miners
docker run --rm bitaxe-benchmark <ip1> <ip2> <ip3> [options]
```

Examples:
```bash
# Single miner
docker run --rm bitaxe-benchmark 192.168.2.26 -v 1200 -f 550

# Multiple miners
docker run --rm bitaxe-benchmark 192.168.2.26 192.168.2.27 192.168.2.28 -v 1200 -f 525
```

## Configuration

The script includes several configurable parameters:

- Maximum chip temperature: 66°C
- Maximum VR temperature: 70°C
- Maximum allowed voltage: 1250mV
- Maximum allowed frequency: 500MHz
- Benchmark duration: 20 minutes
- Sample interval: 30 seconds
- **Minimum required samples: 7** (for valid data processing)
- Voltage increment: 5mV
- Frequency increment: 10MHz

## Output

For each miner, the benchmark results are saved to `bitaxe_benchmark_results_<ip_address>.json` and `Resultat_optimal_<ip_address>.json`, containing:
- Complete test results for all combinations
- Top 5 performing configurations ranked by hashrate
- For each configuration:
  - Average hashrate (with outlier removal)
  - Temperature readings
  - VR temperature readings (when available)
  - Power efficiency metrics (J/TH)
  - Voltage/frequency combinations tested

**Parallel Execution Features:**
- Each miner displays colored output with miner identification
- Thread-safe logging prevents output overlap
- Independent benchmarking progress for each miner
- Graceful shutdown handling for all miners simultaneously

## Safety Features

- Automatic temperature monitoring with safety cutoff (66°C chip temp)
- Voltage regulator (VR) temperature monitoring with safety cutoff (70°C)
- Graceful shutdown on interruption (Ctrl+C) across all miners
- Automatic reset to best performing settings after benchmarking
- Input validation for safe voltage and frequency ranges
- Hashrate validation to ensure stability (within 8% of expected)
- Protection against invalid system data
- Outlier removal from benchmark results
- Thread-safe operation for multiple miners

## Benchmarking Process

The tool follows this process for each miner (in parallel):
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
8. Allows 60-second stabilization period between tests

## Data Processing

The tool implements several data processing techniques to ensure accurate results:
- Removes 3 highest and 3 lowest hashrate readings to eliminate outliers
- Validates hashrate is within 8% of theoretical maximum
- Averages power consumption across entire test period
- Monitors VR temperature when available
- Calculates efficiency in Joules per Terahash (J/TH)
- Thread-safe data collection and processing for parallel execution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Disclaimer

Please use this tool responsibly. Overclocking and voltage modifications can potentially damage your hardware if not done carefully. Always ensure proper cooling and monitor your device during benchmarking.
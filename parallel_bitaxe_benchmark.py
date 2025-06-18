import requests
import time
import json
import signal
import sys
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor
import queue

# ANSI Color Codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Color mapping for different miners
MINER_COLORS = [GREEN, BLUE, MAGENTA, CYAN, YELLOW]

def parse_arguments():
    parser = argparse.ArgumentParser(description='Parallel Bitaxe Hashrate Benchmark Tool')
    parser.add_argument('bitaxe_ips', nargs='*', 
                       help='IP addresses of the Bitaxes (e.g., 192.168.2.26 192.168.2.27 192.168.2.28)')
    parser.add_argument('-v', '--voltage', type=int, default=1150,
                       help='Initial voltage in mV (default: 1150)')
    parser.add_argument('-f', '--frequency', type=int, default=500,
                       help='Initial frequency in MHz (default: 500)')
    
    # If no arguments are provided, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    if not args.bitaxe_ips:
        print(RED + "Error: Please provide at least one Bitaxe IP address." + RESET)
        parser.print_help()
        sys.exit(1)
    
    return args

class BitaxeBenchmarker:
    def __init__(self, ip, initial_voltage, initial_frequency, miner_id, color):
        self.ip = ip
        self.bitaxe_ip = f"http://{ip}"
        self.initial_voltage = initial_voltage
        self.initial_frequency = initial_frequency
        self.miner_id = miner_id
        self.color = color
        
        # Configuration
        self.voltage_increment = 5
        self.frequency_increment = 5
        self.benchmark_time = 600          # 10 minutes benchmark time
        self.sample_interval = 15          # 15 seconds sample interval
        self.max_temp = 62                 # Will stop if temperature reaches or exceeds this value
        self.max_allowed_voltage = 1200    # Maximum allowed core voltage
        self.max_allowed_frequency = 1200  # Maximum allowed core frequency
        self.max_vr_temp = 65              # Maximum allowed voltage regulator temperature
        self.min_input_voltage = 4800      # Minimum allowed input voltage
        self.max_input_voltage = 5500      # Maximum allowed input voltage
        self.max_power = 28                # Max of 40W because of DC plug
        self.min_allowed_voltage = 1000    # Minimum allowed core voltage
        self.min_allowed_frequency = 400   # Minimum allowed frequency
        
        # Instance variables
        self.small_core_count = None
        self.asic_count = None
        self.results = []
        self.default_voltage = None
        self.default_frequency = None
        self.system_reset_done = False
        self.handling_interrupt = False
        
        # Thread-safe print queue
        self.print_queue = queue.Queue()
        
        # Validation
        self.validate_parameters()
    
    def validate_parameters(self):
        if self.initial_voltage > self.max_allowed_voltage:
            raise ValueError(f"Error: Initial voltage exceeds the maximum allowed value of {self.max_allowed_voltage}mV for miner {self.ip}")
        
        if self.initial_frequency > self.max_allowed_frequency:
            raise ValueError(f"Error: Initial frequency exceeds the maximum allowed value of {self.max_allowed_frequency}MHz for miner {self.ip}")
        
        if self.initial_voltage < self.min_allowed_voltage:
            raise ValueError(f"Error: Initial voltage is below the minimum allowed value of {self.min_allowed_voltage}mV for miner {self.ip}")
        
        if self.initial_frequency < self.min_allowed_frequency:
            raise ValueError(f"Error: Initial frequency is below the minimum allowed value of {self.min_allowed_frequency}MHz for miner {self.ip}")
        
        if self.benchmark_time / self.sample_interval < 7:
            raise ValueError(f"Error: Benchmark time is too short for miner {self.ip}. At least 7 samples are required.")
    
    def safe_print(self, message):
        """Thread-safe printing with miner identification"""
        timestamped_message = f"[Miner {self.miner_id}] {message}"
        print(self.color + timestamped_message + RESET)
    
    def fetch_default_settings(self):
        try:
            response = requests.get(f"{self.bitaxe_ip}/api/system/info", timeout=10)
            response.raise_for_status()
            system_info = response.json()
            self.default_voltage = system_info.get("coreVoltage", 1150)
            self.default_frequency = system_info.get("frequency", 500)
            self.small_core_count = system_info.get("smallCoreCount", 0)
            self.asic_count = system_info.get("asicCount", 0)
            self.safe_print(f"Current settings determined:\\n"
                          f"  Core Voltage: {self.default_voltage}mV\\n"
                          f"  Frequency: {self.default_frequency}MHz\\n"
                          f"  ASIC Configuration: {self.small_core_count * self.asic_count} total cores")
        except requests.exceptions.RequestException as e:
            self.safe_print(f"Error fetching default system settings: {e}. Using fallback defaults.")
            self.default_voltage = 1150
            self.default_frequency = 500
            self.small_core_count = 0
            self.asic_count = 0
    
    def get_system_info(self):
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(f"{self.bitaxe_ip}/api/system/info", timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                self.safe_print(f"Timeout while fetching system info. Attempt {attempt + 1} of {retries}.")
            except requests.exceptions.ConnectionError:
                self.safe_print(f"Connection error while fetching system info. Attempt {attempt + 1} of {retries}.")
            except requests.exceptions.RequestException as e:
                self.safe_print(f"Error fetching system info: {e}")
                break
            time.sleep(5)
        return None
    
    def set_system_settings(self, core_voltage, frequency):
        settings = {
            "coreVoltage": core_voltage,
            "frequency": frequency
        }
        try:
            response = requests.patch(f"{self.bitaxe_ip}/api/system", json=settings, timeout=10)
            response.raise_for_status()
            self.safe_print(f"Applying settings: Voltage = {core_voltage}mV, Frequency = {frequency}MHz")
            time.sleep(2)
            self.restart_system()
        except requests.exceptions.RequestException as e:
            self.safe_print(f"Error setting system settings: {e}")
    
    def restart_system(self):
        try:
            is_interrupt = self.handling_interrupt
            
            if not is_interrupt:
                self.safe_print("Applying new settings and waiting 90s for system stabilization...")
                response = requests.post(f"{self.bitaxe_ip}/api/system/restart", timeout=10)
                response.raise_for_status()
                time.sleep(90)
            else:
                self.safe_print("Applying final settings...")
                response = requests.post(f"{self.bitaxe_ip}/api/system/restart", timeout=10)
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.safe_print(f"Error restarting the system: {e}")
    
    def benchmark_iteration(self, core_voltage, frequency):
        current_time = time.strftime("%H:%M:%S")
        self.safe_print(f"[{current_time}] Starting benchmark for Core Voltage: {core_voltage}mV, Frequency: {frequency}MHz")
        hash_rates = []
        temperatures = []
        power_consumptions = []
        vr_temps = []
        total_samples = self.benchmark_time // self.sample_interval
        expected_hashrate = frequency * ((self.small_core_count * self.asic_count) / 1000)
        
        for sample in range(total_samples):
            info = self.get_system_info()
            if info is None:
                self.safe_print("Skipping this iteration due to failure in fetching system info.")
                return None, None, None, False, None, "SYSTEM_INFO_FAILURE"
            
            temp = info.get("temp")
            vr_temp = info.get("vrTemp")
            voltage = info.get("voltage")
            
            if temp is None:
                self.safe_print("Temperature data not available.")
                return None, None, None, False, None, "TEMPERATURE_DATA_FAILURE"
            
            if temp < 5:
                self.safe_print("Temperature is below 5°C. This is unexpected. Please check the system.")
                return None, None, None, False, None, "TEMPERATURE_BELOW_5"
            
            # Temperature checks
            if temp >= self.max_temp:
                self.safe_print(f"Chip temperature exceeded {self.max_temp}°C! Stopping current benchmark.")
                return None, None, None, False, None, "CHIP_TEMP_EXCEEDED"
                
            if vr_temp is not None and vr_temp >= self.max_vr_temp:
                self.safe_print(f"Voltage regulator temperature exceeded {self.max_vr_temp}°C! Stopping current benchmark.")
                return None, None, None, False, None, "VR_TEMP_EXCEEDED"
            
            # Voltage checks
            if voltage < self.min_input_voltage:
                self.safe_print(f"Input voltage is below the minimum allowed value of {self.min_input_voltage}mV! Stopping current benchmark.")
                return None, None, None, False, None, "INPUT_VOLTAGE_BELOW_MIN"
            
            if voltage > self.max_input_voltage:
                self.safe_print(f"Input voltage is above the maximum allowed value of {self.max_input_voltage}mV! Stopping current benchmark.")
                return None, None, None, False, None, "INPUT_VOLTAGE_ABOVE_MAX"
            
            hash_rate = info.get("hashRate")
            power_consumption = info.get("power")
            
            if hash_rate is None or power_consumption is None:
                self.safe_print("Hashrate or Watts data not available.")
                return None, None, None, False, None, "HASHRATE_POWER_DATA_FAILURE"
            
            if power_consumption > self.max_power:
                self.safe_print(f"Power consumption exceeded {self.max_power}W! Stopping current benchmark.")
                return None, None, None, False, None, "POWER_CONSUMPTION_EXCEEDED"
            
            hash_rates.append(hash_rate)
            temperatures.append(temp)
            power_consumptions.append(power_consumption)
            if vr_temp is not None and vr_temp > 0:
                vr_temps.append(vr_temp)
            
            # Calculate percentage progress
            percentage_progress = ((sample + 1) / total_samples) * 100
            status_line = (
                f"[{sample + 1:2d}/{total_samples:2d}] "
                f"{percentage_progress:5.1f}% | "
                f"CV: {core_voltage:4d}mV | "
                f"F: {frequency:4d}MHz | "
                f"H: {int(hash_rate):4d} GH/s | "
                f"IV: {int(voltage):4d}mV | "
                f"T: {int(temp):2d}°C"
            )
            if vr_temp is not None and vr_temp > 0:
                status_line += f" | VR: {int(vr_temp):2d}°C"
            
            print(self.color + f"[Miner {self.miner_id}] " + status_line + RESET)
            
            # Only sleep if it's not the last iteration
            if sample < total_samples - 1:
                time.sleep(self.sample_interval)
        
        if hash_rates and temperatures and power_consumptions:
            # Process results (same logic as original)
            sorted_hashrates = sorted(hash_rates)
            trimmed_hashrates = sorted_hashrates[3:-3]
            average_hashrate = sum(trimmed_hashrates) / len(trimmed_hashrates)
            
            sorted_temps = sorted(temperatures)
            trimmed_temps = sorted_temps[6:]
            average_temperature = sum(trimmed_temps) / len(trimmed_temps)
            
            average_vr_temp = None
            if vr_temps:
                sorted_vr_temps = sorted(vr_temps)
                trimmed_vr_temps = sorted_vr_temps[6:]
                average_vr_temp = sum(trimmed_vr_temps) / len(trimmed_vr_temps)
            
            average_power = sum(power_consumptions) / len(power_consumptions)
            
            if average_hashrate > 0:
                efficiency_jth = average_power / (average_hashrate / 1_000)
            else:
                self.safe_print("Warning: Zero hashrate detected, skipping efficiency calculation")
                return None, None, None, False, None, "ZERO_HASHRATE"
            
            hashrate_within_tolerance = (average_hashrate >= expected_hashrate * 0.94)
            
            self.safe_print(f"Average Hashrate: {average_hashrate:.2f} GH/s (Expected: {expected_hashrate:.2f} GH/s)")
            self.safe_print(f"Average Temperature: {average_temperature:.2f}°C")
            if average_vr_temp is not None:
                self.safe_print(f"Average VR Temperature: {average_vr_temp:.2f}°C")
            self.safe_print(f"Efficiency: {efficiency_jth:.2f} J/TH")
            
            return average_hashrate, average_temperature, efficiency_jth, hashrate_within_tolerance, average_vr_temp, None
        else:
            self.safe_print("No Hashrate or Temperature or Watts data collected.")
            return None, None, None, False, None, "NO_DATA_COLLECTED"
    
    def save_results(self):
        try:
            filename = f"bitaxe_benchmark_results_{self.ip}.json"
            
            if self.results:
                # Sort results
                top_5_results = sorted(self.results, key=lambda x: x["averageHashRate"], reverse=True)[:5]
                top_5_efficient_results = sorted(self.results, key=lambda x: x["efficiencyJTH"], reverse=False)[:5]
                
                final_data = {
                    "all_results": self.results,
                    "top_performers": [
                        {
                            "rank": i,
                            "coreVoltage": result["coreVoltage"],
                            "frequency": result["frequency"],
                            "averageHashRate": result["averageHashRate"],
                            "averageTemperature": result["averageTemperature"],
                            "efficiencyJTH": result["efficiencyJTH"],
                            **({"averageVRTemp": result["averageVRTemp"]} if "averageVRTemp" in result else {})
                        }
                        for i, result in enumerate(top_5_results, 1)
                    ],
                    "most_efficient": [
                        {
                            "rank": i,
                            "coreVoltage": result["coreVoltage"],
                            "frequency": result["frequency"],
                            "averageHashRate": result["averageHashRate"],
                            "averageTemperature": result["averageTemperature"],
                            "efficiencyJTH": result["efficiencyJTH"],
                            **({"averageVRTemp": result["averageVRTemp"]} if "averageVRTemp" in result else {})
                        }
                        for i, result in enumerate(top_5_efficient_results, 1)
                    ]
                }
                
                with open(filename, "w") as f:
                    json.dump(final_data, f, indent=4)
                self.safe_print(f"Results saved to {filename}")
            else:
                with open(filename, "w") as f:
                    json.dump({"message": "No valid results collected"}, f, indent=4)
                self.safe_print(f"No results file saved (no valid data) for {filename}")
                
        except IOError as e:
            self.safe_print(f"Error saving results to file: {e}")
    
    def reset_to_best_setting(self):
        if not self.results:
            self.safe_print("No valid benchmarking results found. Applying predefined default settings.")
            self.set_system_settings(self.default_voltage, self.default_frequency)
        else:
            best_result = sorted(self.results, key=lambda x: x["averageHashRate"], reverse=True)[0]
            best_voltage = best_result["coreVoltage"]
            best_frequency = best_result["frequency"]
            
            self.safe_print(f"Applying the best settings from benchmarking:\\n"
                          f"  Core Voltage: {best_voltage}mV\\n"
                          f"  Frequency: {best_frequency}MHz")
            self.set_system_settings(best_voltage, best_frequency)
        
        self.restart_system()
    
    def cleanup_and_exit(self):
        if self.system_reset_done:
            return
        
        try:
            if self.results:
                self.reset_to_best_setting()
                self.save_results()
                self.safe_print("Bitaxe reset to best settings and results saved.")
            else:
                self.safe_print("No valid benchmarking results found. Applying predefined default settings.")
                self.set_system_settings(self.default_voltage, self.default_frequency)
        finally:
            self.system_reset_done = True
    
    def handle_interrupt(self):
        if self.handling_interrupt or self.system_reset_done:
            return
        
        self.handling_interrupt = True
        self.safe_print("Benchmarking interrupted by user.")
        self.cleanup_and_exit()
    
    def run_benchmark(self):
        try:
            self.fetch_default_settings()
            
            current_voltage = self.initial_voltage
            current_frequency = self.initial_frequency
            
            while current_voltage <= self.max_allowed_voltage and current_frequency <= self.max_allowed_frequency:
                self.set_system_settings(current_voltage, current_frequency)
                avg_hashrate, avg_temp, efficiency_jth, hashrate_ok, avg_vr_temp, error_reason = self.benchmark_iteration(current_voltage, current_frequency)
                
                if avg_hashrate is not None and avg_temp is not None and efficiency_jth is not None:
                    result = {
                        "coreVoltage": current_voltage,
                        "frequency": current_frequency,
                        "averageHashRate": avg_hashrate,
                        "averageTemperature": avg_temp,
                        "efficiencyJTH": efficiency_jth
                    }
                    
                    if avg_vr_temp is not None:
                        result["averageVRTemp"] = avg_vr_temp
                    
                    self.results.append(result)
                    
                    if hashrate_ok:
                        if current_frequency + self.frequency_increment <= self.max_allowed_frequency:
                            current_frequency += self.frequency_increment
                        else:
                            break
                    else:
                        if current_voltage + self.voltage_increment <= self.max_allowed_voltage:
                            current_voltage += self.voltage_increment
                            current_frequency -= self.frequency_increment
                            self.safe_print(f"Hashrate too low compared to expected. Decreasing frequency to {current_frequency}MHz and increasing voltage to {current_voltage}mV")
                        else:
                            break
                else:
                    self.safe_print("Reached thermal or stability limits. Stopping further testing.")
                    break
                
                self.save_results()
        
        except Exception as e:
            self.safe_print(f"An unexpected error occurred: {e}")
        finally:
            self.cleanup_and_exit()
            if self.results:
                self.print_summary()
    
    def print_summary(self):
        if not self.results:
            return
        
        top_5_results = sorted(self.results, key=lambda x: x["averageHashRate"], reverse=True)[:5]
        top_5_efficient_results = sorted(self.results, key=lambda x: x["efficiencyJTH"], reverse=False)[:5]
        
        self.safe_print("Benchmarking completed.")
        if top_5_results:
            self.safe_print("\\nTop 5 Highest Hashrate Settings:")
            for i, result in enumerate(top_5_results, 1):
                self.safe_print(f"\\nRank {i}:")
                self.safe_print(f"  Core Voltage: {result['coreVoltage']}mV")
                self.safe_print(f"  Frequency: {result['frequency']}MHz")
                self.safe_print(f"  Average Hashrate: {result['averageHashRate']:.2f} GH/s")
                self.safe_print(f"  Average Temperature: {result['averageTemperature']:.2f}°C")
                self.safe_print(f"  Efficiency: {result['efficiencyJTH']:.2f} J/TH")
                if "averageVRTemp" in result:
                    self.safe_print(f"  Average VR Temperature: {result['averageVRTemp']:.2f}°C")
            
            self.safe_print("\\nTop 5 Most Efficient Settings:")
            for i, result in enumerate(top_5_efficient_results, 1):
                self.safe_print(f"\\nRank {i}:")
                self.safe_print(f"  Core Voltage: {result['coreVoltage']}mV")
                self.safe_print(f"  Frequency: {result['frequency']}MHz")
                self.safe_print(f"  Average Hashrate: {result['averageHashRate']:.2f} GH/s")
                self.safe_print(f"  Average Temperature: {result['averageTemperature']:.2f}°C")
                self.safe_print(f"  Efficiency: {result['efficiencyJTH']:.2f} J/TH")
                if "averageVRTemp" in result:
                    self.safe_print(f"  Average VR Temperature: {result['averageVRTemp']:.2f}°C")

# Global list to track all benchmarkers
benchmarkers = []
interrupt_received = False

def signal_handler(signum, frame):
    global interrupt_received
    if interrupt_received:
        return
    
    interrupt_received = True
    print(RED + "\\nInterrupt received. Stopping all benchmarks..." + RESET)
    
    # Signal all benchmarkers to stop
    for benchmarker in benchmarkers:
        benchmarker.handle_interrupt()
    
    sys.exit(0)

def main():
    global benchmarkers
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    args = parse_arguments()
    
    # Print disclaimer
    print(RED + "\\nDISCLAIMER:" + RESET)
    print("This tool will stress test your Bitaxes by running them at various voltages and frequencies.")
    print("While safeguards are in place, running hardware outside of standard parameters carries inherent risks.")
    print("Use this tool at your own risk. The author(s) are not responsible for any damage to your hardware.")
    print("\\nNOTE: Ambient temperature significantly affects these results. The optimal settings found may not")
    print("work well if room temperature changes substantially. Re-run the benchmark if conditions change.\\n")
    
    # Create benchmarker instances
    for i, ip in enumerate(args.bitaxe_ips):
        color = MINER_COLORS[i % len(MINER_COLORS)]
        benchmarker = BitaxeBenchmarker(ip, args.voltage, args.frequency, i + 1, color)
        benchmarkers.append(benchmarker)
    
    print(f"Starting parallel benchmarks for {len(benchmarkers)} miners...")
    
    # Run benchmarks in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(benchmarkers)) as executor:
        futures = [executor.submit(benchmarker.run_benchmark) for benchmarker in benchmarkers]
        
        # Wait for all to complete
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(RED + f"Benchmark thread error: {e}" + RESET)
    
    print(GREEN + "\\nAll benchmarks completed!" + RESET)

if __name__ == "__main__":
    main()

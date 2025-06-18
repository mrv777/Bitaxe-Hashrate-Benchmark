# Parallel Bitaxe Benchmarking Guide

This guide covers the parallel benchmarking functionality that allows you to test multiple Bitaxe miners simultaneously.

## Overview

The parallel benchmark tool extends the original single-miner benchmark with multi-threading capabilities, allowing you to:

- Test multiple Bitaxe miners at the same time
- Reduce total benchmarking time significantly
- Maintain all safety features for each individual miner
- Get color-coded output for easy identification
- Receive separate results files for each miner

## Quick Start

```bash
# Basic parallel benchmarking for 3 miners
python parallel_bitaxe_benchmark.py 192.168.1.100 192.168.1.101 192.168.1.102

# With custom starting parameters
python parallel_bitaxe_benchmark.py 192.168.1.100 192.168.1.101 192.168.1.102 -v 1100 -f 550
```

## How It Works

### Threading Architecture
- Each miner runs in its own thread using Python's `ThreadPoolExecutor`
- All miners operate completely independently
- Thread-safe operations ensure no conflicts between miners
- If one miner encounters issues, others continue running

### Color-Coded Output
Each miner is assigned a unique color for easy identification:
- **Miner 1**: Green
- **Miner 2**: Blue  
- **Miner 3**: Magenta
- **Miner 4**: Cyan
- **Miner 5**: Yellow
- Additional miners cycle through colors

### Progress Tracking
Terminal output shows:
```
[Miner 1] [15/40] 37.5% | CV: 1150mV | F: 500MHz | H: 567 GH/s | IV: 5120mV | T: 45°C
[Miner 2] [12/40] 30.0% | CV: 1150mV | F: 500MHz | H: 571 GH/s | IV: 5089mV | T: 47°C | VR: 52°C
[Miner 3] [18/40] 45.0% | CV: 1150mV | F: 500MHz | H: 563 GH/s | IV: 5156mV | T: 44°C
```

## Command Line Options

```bash
python parallel_bitaxe_benchmark.py [IP_ADDRESSES...] [OPTIONS]
```

### Arguments
- `IP_ADDRESSES`: Space-separated list of Bitaxe IP addresses
- `-v, --voltage`: Initial voltage in mV (default: 1150)
- `-f, --frequency`: Initial frequency in MHz (default: 500)

### Examples

```bash
# Test 2 miners
python parallel_bitaxe_benchmark.py 192.168.1.100 192.168.1.101

# Test 5 miners with custom settings
python parallel_bitaxe_benchmark.py 192.168.1.100 192.168.1.101 192.168.1.102 192.168.1.103 192.168.1.104 -v 1175 -f 525

# Single miner (still works)
python parallel_bitaxe_benchmark.py 192.168.1.100
```

## Results and Output

### Individual Result Files
Each miner saves results to its own file:
- `bitaxe_benchmark_results_192.168.1.100.json`
- `bitaxe_benchmark_results_192.168.1.101.json`
- `bitaxe_benchmark_results_192.168.1.102.json`

### Result File Structure
```json
{
  "all_results": [
    {
      "coreVoltage": 1150,
      "frequency": 500,
      "averageHashRate": 567.45,
      "averageTemperature": 45.2,
      "efficiencyJTH": 20.15,
      "averageVRTemp": 52.1
    }
  ],
  "top_performers": [
    {
      "rank": 1,
      "coreVoltage": 1200,
      "frequency": 600,
      "averageHashRate": 689.32,
      "averageTemperature": 58.7,
      "efficiencyJTH": 22.45
    }
  ],
  "most_efficient": [
    {
      "rank": 1,
      "coreVoltage": 1125,
      "frequency": 525,
      "averageHashRate": 578.91,
      "averageTemperature": 42.3,
      "efficiencyJTH": 18.67
    }
  ]
}
```

## Safety Features

All original safety features apply to each miner individually:

### Temperature Protection
- **Chip Temperature**: Stops at 62°C
- **VR Temperature**: Stops at 65°C (when available)
- **Temperature Validation**: Must be above 5°C

### Voltage Protection
- **Core Voltage Range**: 1000mV to 1200mV
- **Input Voltage Range**: 4800mV to 5500mV

### Power Protection
- **Maximum Power**: 28W per miner

### Error Handling
- Network timeouts and retries
- Invalid data detection
- Graceful error recovery

## Interrupt Handling

### Ctrl+C Behavior
When you press Ctrl+C:
1. All miners receive interrupt signal
2. Each miner saves its current results
3. Each miner applies its best discovered settings
4. All miners restart with optimal settings
5. Program exits gracefully

### Individual Miner Failures
- If one miner fails, others continue
- Failed miners attempt to reset to default settings
- Error messages are color-coded by miner

## Performance Considerations

### Time Savings
- **Sequential**: 3 miners × 3 hours = 9 hours total
- **Parallel**: 3 miners running simultaneously = ~3 hours total
- **Efficiency**: 66% time reduction for 3 miners

### System Requirements
- **CPU**: Multi-core recommended for >3 miners
- **Network**: Stable connection to all miners
- **Memory**: ~50MB per concurrent miner

### Network Considerations
- Ensure all miners are accessible on the network
- Check firewall settings if connection issues occur
- Verify each miner is responsive before starting

## Troubleshooting

### Common Issues

#### Connection Errors
```
[Miner 1] Connection error while fetching system info. Attempt 1 of 3.
```
**Solution**: Verify IP address and network connectivity

#### Mixed Results
```
[Miner 2] No valid benchmarking results found. Applying predefined default settings.
```
**Solution**: Check miner stability and cooling

#### Thread Errors
```
Benchmark thread error: timeout
```
**Solution**: Reduce number of concurrent miners or check network stability

### Best Practices

1. **Start Small**: Test with 2-3 miners first
2. **Monitor Resources**: Watch CPU and network usage
3. **Stable Network**: Ensure reliable network connection
4. **Adequate Cooling**: Verify all miners have proper cooling
5. **Power Supply**: Ensure adequate power for all miners

## Advanced Usage

### Custom Configuration per Miner
Currently, all miners use the same starting voltage and frequency. For different settings per miner, run separate instances:

```bash
# Terminal 1
python parallel_bitaxe_benchmark.py 192.168.1.100 192.168.1.101 -v 1150 -f 500

# Terminal 2
python parallel_bitaxe_benchmark.py 192.168.1.102 192.168.1.103 -v 1175 -f 525
```

### Batch Processing
For large numbers of miners, consider batching:

```bash
# Batch 1: Miners 1-3
python parallel_bitaxe_benchmark.py 192.168.1.100 192.168.1.101 192.168.1.102

# Batch 2: Miners 4-6
python parallel_bitaxe_benchmark.py 192.168.1.103 192.168.1.104 192.168.1.105
```

## Comparison: Single vs Parallel

| Feature | Single Miner | Parallel Miners |
|---------|-------------|----------------|
| **Time Efficiency** | Linear scaling | Constant time |
| **Resource Usage** | Low | Moderate |
| **Output Clarity** | Simple | Color-coded |
| **Result Files** | One file | File per miner |
| **Error Isolation** | N/A | Independent failures |
| **Monitoring** | Easy | Requires attention |

## Migration from Single Miner

### File Names
- **Old**: `bitaxe_benchmark_results_192.168.1.100.json`
- **New**: `bitaxe_benchmark_results_192.168.1.100.json` (same format)

### Script Usage
```bash
# Old single miner approach
python bitaxe_hashrate_benchmark.py 192.168.1.100
python bitaxe_hashrate_benchmark.py 192.168.1.101
python bitaxe_hashrate_benchmark.py 192.168.1.102

# New parallel approach
python parallel_bitaxe_benchmark.py 192.168.1.100 192.168.1.101 192.168.1.102
```

The parallel script is fully backward compatible and can be used for single miners as well.

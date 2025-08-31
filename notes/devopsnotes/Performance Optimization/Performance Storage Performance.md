# Performance Storage Performance

**Focus:** Disk I/O optimization, file system tuning, storage architecture design, caching strategies, SSD optimization, RAID configuration, and distributed storage performance.

## Core Storage Performance Principles

### 1. I/O Optimization Strategies
- **I/O Schedulers**: CFQ, Deadline, NOOP, and mq-deadline
- **Queue Depth**: Optimal concurrent I/O operations
- **Block Size**: Matching application patterns
- **Read-Ahead**: Sequential access optimization

### 2. File System Performance
- **File System Selection**: ext4, XFS, Btrfs, ZFS comparison
- **Mount Options**: Performance-oriented configurations
- **Journaling**: Trade-offs between safety and performance
- **Fragmentation**: Prevention and defragmentation strategies

### 3. Storage Architecture Design
- **RAID Levels**: Performance vs redundancy optimization
- **Tiered Storage**: Hot/warm/cold data placement
- **Caching Layers**: Multi-level cache hierarchies
- **Parallel I/O**: Striping and load distribution

### 4. Modern Storage Technologies
- **SSD Optimization**: TRIM, over-provisioning, wear leveling
- **NVMe Performance**: Direct PCIe access optimization
- **Storage Classes**: Memory, NVMe, SSD, HDD optimization
- **Cloud Storage**: Object storage and network-attached optimization

## Enterprise Storage Performance Framework

```python
import os
import time
import subprocess
import threading
import queue
import json
import statistics
import psutil
import asyncio
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import numpy as np
from contextlib import contextmanager
import tempfile
import shutil
import platform
import struct
import fcntl

@dataclass
class StorageMetric:
    device: str
    read_iops: float
    write_iops: float
    read_throughput_mbps: float
    write_throughput_mbps: float
    read_latency_ms: float
    write_latency_ms: float
    queue_depth: float
    utilization_percent: float
    timestamp: float

@dataclass
class StorageOptimizationResult:
    optimization_type: str
    device: str
    before_metric: float
    after_metric: float
    improvement_percent: float
    description: str
    configuration: Dict

class EnterpriseStorageOptimizer:
    def __init__(self, config: Dict):
        self.config = config
        self.metrics_history = []
        self.optimization_results = []
        self.logger = self._setup_logging()
        self.benchmark_files = {}
        self.io_monitoring_active = False
        
    def _setup_logging(self) -> logging.Logger:
        """Setup storage optimization logger"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def analyze_storage_devices(self) -> Dict[str, Dict]:
        """Analyze all storage devices and their characteristics"""
        devices = {}
        
        # Get disk partitions
        for partition in psutil.disk_partitions():
            try:
                device_name = partition.device
                
                # Get basic usage stats
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Get I/O statistics
                io_counters = psutil.disk_io_counters(perdisk=True)
                device_key = self._get_device_key(device_name)
                
                device_info = {
                    'device': device_name,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_gb': usage.total / (1024**3),
                    'used_gb': usage.used / (1024**3),
                    'free_gb': usage.free / (1024**3),
                    'usage_percent': (usage.used / usage.total) * 100,
                    'io_stats': dict(io_counters.get(device_key, {})._asdict()) if device_key in io_counters else {}
                }
                
                # Determine storage type
                device_info['storage_type'] = self._detect_storage_type(device_name)
                device_info['characteristics'] = self._analyze_device_characteristics(device_name)
                
                devices[device_name] = device_info
                
            except (PermissionError, FileNotFoundError):
                continue
        
        return devices
    
    def _get_device_key(self, device_name: str) -> str:
        """Extract device key for I/O statistics"""
        # Remove /dev/ prefix and extract base device name
        base_name = device_name.replace('/dev/', '')
        
        # Handle different naming conventions
        if base_name.startswith('nvme'):
            return base_name.split('p')[0]  # nvme0n1p1 -> nvme0n1
        elif base_name.startswith('sd'):
            return base_name.rstrip('0123456789')  # sda1 -> sda
        else:
            return base_name
    
    def _detect_storage_type(self, device_name: str) -> str:
        """Detect storage device type (SSD, HDD, NVMe)"""
        base_device = self._get_device_key(device_name)
        
        try:
            # Check if NVMe
            if 'nvme' in base_device:
                return 'NVMe'
            
            # Check rotation rate for SSD/HDD detection
            rotational_file = f'/sys/block/{base_device}/queue/rotational'
            if os.path.exists(rotational_file):
                with open(rotational_file, 'r') as f:
                    rotational = f.read().strip()
                    return 'HDD' if rotational == '1' else 'SSD'
            
        except Exception:
            pass
        
        return 'Unknown'
    
    def _analyze_device_characteristics(self, device_name: str) -> Dict:
        """Analyze device-specific characteristics"""
        base_device = self._get_device_key(device_name)
        characteristics = {}
        
        try:
            # Queue depth
            queue_depth_file = f'/sys/block/{base_device}/queue/nr_requests'
            if os.path.exists(queue_depth_file):
                with open(queue_depth_file, 'r') as f:
                    characteristics['queue_depth'] = int(f.read().strip())
            
            # Scheduler
            scheduler_file = f'/sys/block/{base_device}/queue/scheduler'
            if os.path.exists(scheduler_file):
                with open(scheduler_file, 'r') as f:
                    scheduler_content = f.read().strip()
                    # Extract active scheduler (enclosed in brackets)
                    import re
                    match = re.search(r'\[([^\]]+)\]', scheduler_content)
                    characteristics['scheduler'] = match.group(1) if match else 'unknown'
            
            # Read-ahead
            readahead_file = f'/sys/block/{base_device}/queue/read_ahead_kb'
            if os.path.exists(readahead_file):
                with open(readahead_file, 'r') as f:
                    characteristics['read_ahead_kb'] = int(f.read().strip())
            
            # Max sectors
            max_sectors_file = f'/sys/block/{base_device}/queue/max_sectors_kb'
            if os.path.exists(max_sectors_file):
                with open(max_sectors_file, 'r') as f:
                    characteristics['max_sectors_kb'] = int(f.read().strip())
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze characteristics for {device_name}: {e}")
        
        return characteristics
    
    def benchmark_storage_performance(self, device_path: str, test_size_mb: int = 1024) -> StorageMetric:
        """Comprehensive storage performance benchmark"""
        self.logger.info(f"Starting storage benchmark for {device_path}")
        
        # Create benchmark file path
        benchmark_dir = os.path.join(device_path, '.storage_benchmark')
        os.makedirs(benchmark_dir, exist_ok=True)
        benchmark_file = os.path.join(benchmark_dir, 'benchmark_file')
        
        try:
            # Sequential write test
            write_throughput, write_latency, write_iops = self._benchmark_sequential_write(
                benchmark_file, test_size_mb
            )
            
            # Sequential read test
            read_throughput, read_latency, read_iops = self._benchmark_sequential_read(
                benchmark_file, test_size_mb
            )
            
            # Random I/O test
            random_read_iops, random_write_iops = self._benchmark_random_io(
                benchmark_file, test_size_mb
            )
            
            # Get current I/O utilization
            utilization = self._get_device_utilization(device_path)
            
            metric = StorageMetric(
                device=device_path,
                read_iops=max(read_iops, random_read_iops),
                write_iops=max(write_iops, random_write_iops),
                read_throughput_mbps=read_throughput,
                write_throughput_mbps=write_throughput,
                read_latency_ms=read_latency,
                write_latency_ms=write_latency,
                queue_depth=32,  # Default queue depth for testing
                utilization_percent=utilization,
                timestamp=time.time()
            )
            
            self.metrics_history.append(metric)
            return metric
            
        finally:
            # Cleanup benchmark files
            try:
                shutil.rmtree(benchmark_dir)
            except Exception:
                pass
    
    def _benchmark_sequential_write(self, file_path: str, size_mb: int) -> Tuple[float, float, float]:
        """Benchmark sequential write performance"""
        block_size = 1024 * 1024  # 1MB blocks
        total_bytes = size_mb * 1024 * 1024
        blocks_count = total_bytes // block_size
        
        data_block = os.urandom(block_size)
        
        start_time = time.time()
        io_times = []
        
        with open(file_path, 'wb') as f:
            for _ in range(blocks_count):
                io_start = time.time()
                f.write(data_block)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
                io_times.append((time.time() - io_start) * 1000)  # Convert to ms
        
        total_time = time.time() - start_time
        throughput_mbps = size_mb / total_time
        average_latency = statistics.mean(io_times) if io_times else 0
        iops = blocks_count / total_time
        
        return throughput_mbps, average_latency, iops
    
    def _benchmark_sequential_read(self, file_path: str, size_mb: int) -> Tuple[float, float, float]:
        """Benchmark sequential read performance"""
        block_size = 1024 * 1024  # 1MB blocks
        total_bytes = size_mb * 1024 * 1024
        blocks_count = total_bytes // block_size
        
        start_time = time.time()
        io_times = []
        
        with open(file_path, 'rb') as f:
            for _ in range(blocks_count):
                io_start = time.time()
                data = f.read(block_size)
                if not data:
                    break
                io_times.append((time.time() - io_start) * 1000)  # Convert to ms
        
        total_time = time.time() - start_time
        throughput_mbps = size_mb / total_time
        average_latency = statistics.mean(io_times) if io_times else 0
        iops = blocks_count / total_time
        
        return throughput_mbps, average_latency, iops
    
    def _benchmark_random_io(self, file_path: str, size_mb: int) -> Tuple[float, float]:
        """Benchmark random I/O performance"""
        block_size = 4096  # 4KB blocks for random I/O
        total_bytes = size_mb * 1024 * 1024
        max_offset = total_bytes - block_size
        
        # Random read test
        read_start = time.time()
        read_operations = 1000
        
        with open(file_path, 'rb') as f:
            for _ in range(read_operations):
                offset = np.random.randint(0, max_offset, dtype=np.int64)
                offset = (offset // block_size) * block_size  # Align to block size
                f.seek(offset)
                f.read(block_size)
        
        read_time = time.time() - read_start
        read_iops = read_operations / read_time
        
        # Random write test
        write_start = time.time()
        write_operations = 1000
        data_block = os.urandom(block_size)
        
        with open(file_path, 'r+b') as f:
            for _ in range(write_operations):
                offset = np.random.randint(0, max_offset, dtype=np.int64)
                offset = (offset // block_size) * block_size  # Align to block size
                f.seek(offset)
                f.write(data_block)
                f.flush()
        
        write_time = time.time() - write_start
        write_iops = write_operations / write_time
        
        return read_iops, write_iops
    
    def _get_device_utilization(self, device_path: str) -> float:
        """Get current device utilization percentage"""
        try:
            # Use iostat-like calculation
            io_counters = psutil.disk_io_counters(perdisk=True)
            device_key = self._get_device_key(device_path)
            
            if device_key in io_counters:
                stats = io_counters[device_key]
                # Simple utilization estimate based on I/O time
                return min(100.0, (stats.read_time + stats.write_time) / 1000.0)  # Convert to percentage
            
        except Exception:
            pass
        
        return 0.0
    
    def optimize_io_scheduler(self, device: str) -> StorageOptimizationResult:
        """Optimize I/O scheduler based on device type"""
        device_key = self._get_device_key(device)
        storage_type = self._detect_storage_type(device)
        
        # Before optimization metrics
        before_metric = self._measure_io_performance(device)
        
        # Choose optimal scheduler based on storage type
        optimal_schedulers = {
            'NVMe': 'none',      # No scheduling needed for NVMe
            'SSD': 'mq-deadline', # Multi-queue deadline for SSDs
            'HDD': 'mq-deadline'  # Deadline scheduler for HDDs
        }
        
        target_scheduler = optimal_schedulers.get(storage_type, 'mq-deadline')
        
        try:
            # Set I/O scheduler
            scheduler_path = f'/sys/block/{device_key}/queue/scheduler'
            subprocess.run(['sudo', 'bash', '-c', f'echo {target_scheduler} > {scheduler_path}'],
                         check=True)
            
            # Wait for change to take effect
            time.sleep(1)
            
            after_metric = self._measure_io_performance(device)
            improvement = max(0, (after_metric - before_metric) / max(before_metric, 1) * 100)
            
            return StorageOptimizationResult(
                optimization_type='io_scheduler',
                device=device,
                before_metric=before_metric,
                after_metric=after_metric,
                improvement_percent=improvement,
                description=f'Set I/O scheduler to {target_scheduler} for {storage_type}',
                configuration={'scheduler': target_scheduler, 'storage_type': storage_type}
            )
            
        except Exception as e:
            return StorageOptimizationResult(
                optimization_type='io_scheduler',
                device=device,
                before_metric=before_metric,
                after_metric=before_metric,
                improvement_percent=0,
                description=f'Failed to optimize I/O scheduler: {e}',
                configuration={}
            )
    
    def optimize_readahead(self, device: str) -> StorageOptimizationResult:
        """Optimize read-ahead settings based on workload"""
        device_key = self._get_device_key(device)
        storage_type = self._detect_storage_type(device)
        
        before_metric = self._measure_read_performance(device)
        
        # Optimal read-ahead values based on storage type
        optimal_readahead = {
            'NVMe': 128,   # Lower for NVMe due to low latency
            'SSD': 256,    # Moderate for SSDs
            'HDD': 512     # Higher for HDDs to optimize sequential reads
        }
        
        target_readahead = optimal_readahead.get(storage_type, 256)
        
        try:
            readahead_path = f'/sys/block/{device_key}/queue/read_ahead_kb'
            subprocess.run(['sudo', 'bash', '-c', f'echo {target_readahead} > {readahead_path}'],
                         check=True)
            
            time.sleep(1)
            after_metric = self._measure_read_performance(device)
            improvement = max(0, (after_metric - before_metric) / max(before_metric, 1) * 100)
            
            return StorageOptimizationResult(
                optimization_type='readahead_optimization',
                device=device,
                before_metric=before_metric,
                after_metric=after_metric,
                improvement_percent=improvement,
                description=f'Set read-ahead to {target_readahead}KB for {storage_type}',
                configuration={'read_ahead_kb': target_readahead, 'storage_type': storage_type}
            )
            
        except Exception as e:
            return StorageOptimizationResult(
                optimization_type='readahead_optimization',
                device=device,
                before_metric=before_metric,
                after_metric=before_metric,
                improvement_percent=0,
                description=f'Failed to optimize read-ahead: {e}',
                configuration={}
            )
    
    def optimize_queue_depth(self, device: str) -> StorageOptimizationResult:
        """Optimize queue depth for maximum throughput"""
        device_key = self._get_device_key(device)
        storage_type = self._detect_storage_type(device)
        
        before_metric = self._measure_queue_performance(device)
        
        # Optimal queue depths based on storage type
        optimal_queue_depths = {
            'NVMe': 128,   # High queue depth for NVMe
            'SSD': 32,     # Moderate for SATA SSDs
            'HDD': 8       # Lower for HDDs
        }
        
        target_queue_depth = optimal_queue_depths.get(storage_type, 32)
        
        try:
            queue_depth_path = f'/sys/block/{device_key}/queue/nr_requests'
            subprocess.run(['sudo', 'bash', '-c', f'echo {target_queue_depth} > {queue_depth_path}'],
                         check=True)
            
            time.sleep(1)
            after_metric = self._measure_queue_performance(device)
            improvement = max(0, (after_metric - before_metric) / max(before_metric, 1) * 100)
            
            return StorageOptimizationResult(
                optimization_type='queue_depth_optimization',
                device=device,
                before_metric=before_metric,
                after_metric=after_metric,
                improvement_percent=improvement,
                description=f'Set queue depth to {target_queue_depth} for {storage_type}',
                configuration={'queue_depth': target_queue_depth, 'storage_type': storage_type}
            )
            
        except Exception as e:
            return StorageOptimizationResult(
                optimization_type='queue_depth_optimization',
                device=device,
                before_metric=before_metric,
                after_metric=before_metric,
                improvement_percent=0,
                description=f'Failed to optimize queue depth: {e}',
                configuration={}
            )
    
    def _measure_io_performance(self, device: str) -> float:
        """Measure overall I/O performance"""
        try:
            # Simple I/O performance test
            test_file = tempfile.NamedTemporaryFile(delete=False, dir=device)
            test_data = os.urandom(1024 * 1024)  # 1MB
            
            start_time = time.time()
            for _ in range(10):  # 10MB total
                test_file.write(test_data)
                test_file.flush()
                os.fsync(test_file.fileno())
            
            test_file.close()
            
            # Read test
            with open(test_file.name, 'rb') as f:
                for _ in range(10):
                    f.read(1024 * 1024)
            
            total_time = time.time() - start_time
            os.unlink(test_file.name)
            
            return 20 / total_time if total_time > 0 else 0  # 20MB / time = MB/s
            
        except Exception:
            return 0
    
    def _measure_read_performance(self, device: str) -> float:
        """Measure read performance specifically"""
        try:
            test_file = tempfile.NamedTemporaryFile(delete=False, dir=device)
            test_data = os.urandom(10 * 1024 * 1024)  # 10MB
            test_file.write(test_data)
            test_file.close()
            
            start_time = time.time()
            with open(test_file.name, 'rb') as f:
                data = f.read()
            
            read_time = time.time() - start_time
            os.unlink(test_file.name)
            
            return len(data) / (1024 * 1024) / read_time if read_time > 0 else 0  # MB/s
            
        except Exception:
            return 0
    
    def _measure_queue_performance(self, device: str) -> float:
        """Measure performance under queue load"""
        try:
            # Simulate concurrent I/O operations
            def io_worker():
                test_file = tempfile.NamedTemporaryFile(delete=False, dir=device)
                test_data = os.urandom(1024 * 1024)  # 1MB
                
                start = time.time()
                test_file.write(test_data)
                test_file.flush()
                os.fsync(test_file.fileno())
                test_file.close()
                os.unlink(test_file.name)
                
                return time.time() - start
            
            # Run multiple concurrent I/O operations
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(io_worker) for _ in range(16)]
                times = [future.result() for future in as_completed(futures)]
            
            return 16 / sum(times) if sum(times) > 0 else 0  # Operations per second
            
        except Exception:
            return 0
    
    def monitor_storage_performance(self, duration_seconds: int = 300) -> Dict:
        """Monitor storage performance over time"""
        monitoring_results = {
            'duration': duration_seconds,
            'device_metrics': {},
            'statistics': {},
            'alerts': []
        }
        
        start_time = time.time()
        sample_interval = 10
        
        while time.time() - start_time < duration_seconds:
            try:
                # Get I/O statistics for all devices
                io_counters = psutil.disk_io_counters(perdisk=True)
                
                for device, stats in io_counters.items():
                    if device not in monitoring_results['device_metrics']:
                        monitoring_results['device_metrics'][device] = []
                    
                    sample = {
                        'timestamp': time.time(),
                        'read_bytes_per_sec': stats.read_bytes,
                        'write_bytes_per_sec': stats.write_bytes,
                        'read_count_per_sec': stats.read_count,
                        'write_count_per_sec': stats.write_count,
                        'read_time_ms': stats.read_time,
                        'write_time_ms': stats.write_time
                    }
                    
                    monitoring_results['device_metrics'][device].append(sample)
                    
                    # Check for performance alerts
                    self._check_storage_alerts(device, sample, monitoring_results['alerts'])
                
                time.sleep(sample_interval)
                
            except Exception as e:
                self.logger.error(f"Storage monitoring error: {e}")
        
        # Calculate statistics
        monitoring_results['statistics'] = self._calculate_storage_statistics(
            monitoring_results['device_metrics']
        )
        
        return monitoring_results
    
    def _check_storage_alerts(self, device: str, sample: Dict, alerts: List[Dict]):
        """Check for storage performance alerts"""
        # High I/O wait time alert
        total_io_time = sample['read_time_ms'] + sample['write_time_ms']
        if total_io_time > 10000:  # More than 10 seconds of I/O time
            alerts.append({
                'type': 'high_io_wait',
                'device': device,
                'timestamp': sample['timestamp'],
                'value': total_io_time,
                'severity': 'HIGH'
            })
        
        # Low throughput alert
        total_bytes = sample['read_bytes_per_sec'] + sample['write_bytes_per_sec']
        if total_bytes > 0 and total_bytes < 1024 * 1024:  # Less than 1MB/s
            alerts.append({
                'type': 'low_throughput',
                'device': device,
                'timestamp': sample['timestamp'],
                'value': total_bytes,
                'severity': 'MEDIUM'
            })
    
    def _calculate_storage_statistics(self, device_metrics: Dict) -> Dict:
        """Calculate storage performance statistics"""
        statistics_by_device = {}
        
        for device, samples in device_metrics.items():
            if not samples:
                continue
            
            read_throughputs = [s['read_bytes_per_sec'] for s in samples]
            write_throughputs = [s['write_bytes_per_sec'] for s in samples]
            
            statistics_by_device[device] = {
                'avg_read_throughput_bps': statistics.mean(read_throughputs),
                'avg_write_throughput_bps': statistics.mean(write_throughputs),
                'max_read_throughput_bps': max(read_throughputs),
                'max_write_throughput_bps': max(write_throughputs),
                'total_read_ops': sum(s['read_count_per_sec'] for s in samples),
                'total_write_ops': sum(s['write_count_per_sec'] for s in samples),
                'avg_read_time_ms': statistics.mean([s['read_time_ms'] for s in samples]),
                'avg_write_time_ms': statistics.mean([s['write_time_ms'] for s in samples]),
                'sample_count': len(samples)
            }
        
        return statistics_by_device
    
    def generate_storage_optimization_report(self) -> Dict:
        """Generate comprehensive storage optimization report"""
        devices = self.analyze_storage_devices()
        
        report = {
            'timestamp': time.time(),
            'storage_summary': {
                'total_devices': len(devices),
                'storage_types': {
                    storage_type: len([d for d in devices.values() if d.get('storage_type') == storage_type])
                    for storage_type in ['NVMe', 'SSD', 'HDD', 'Unknown']
                },
                'total_capacity_gb': sum(d.get('total_gb', 0) for d in devices.values()),
                'total_used_gb': sum(d.get('used_gb', 0) for d in devices.values())
            },
            'optimization_results': [asdict(r) for r in self.optimization_results],
            'performance_metrics': [asdict(m) for m in self.metrics_history[-10:]],  # Last 10 metrics
            'device_analysis': devices,
            'recommendations': self._generate_storage_recommendations(devices)
        }
        
        return report
    
    def _generate_storage_recommendations(self, devices: Dict) -> List[str]:
        """Generate storage optimization recommendations"""
        recommendations = []
        
        for device_name, device_info in devices.items():
            usage_percent = device_info.get('usage_percent', 0)
            storage_type = device_info.get('storage_type', 'Unknown')
            
            # Storage usage recommendations
            if usage_percent > 90:
                recommendations.append(f"Critical: {device_name} is {usage_percent:.1f}% full - cleanup required")
            elif usage_percent > 80:
                recommendations.append(f"Warning: {device_name} is {usage_percent:.1f}% full - monitor closely")
            
            # Storage type specific recommendations
            if storage_type == 'SSD':
                recommendations.append(f"Enable TRIM for SSD {device_name} to maintain performance")
            elif storage_type == 'HDD':
                recommendations.append(f"Consider defragmentation for HDD {device_name}")
            elif storage_type == 'NVMe':
                recommendations.append(f"Optimize queue depth for NVMe {device_name}")
        
        # General recommendations
        recommendations.extend([
            "Monitor I/O patterns to identify optimization opportunities",
            "Consider implementing tiered storage for hot/warm/cold data",
            "Implement proper backup strategies for critical data",
            "Regular performance benchmarking to track degradation",
            "Consider RAID configuration for performance and redundancy balance"
        ])
        
        return recommendations[:15]  # Top 15 recommendations

# Configuration Example
storage_config = {
    'benchmark_size_mb': 1024,
    'monitoring_interval': 10,
    'performance_thresholds': {
        'min_throughput_mbps': 50,
        'max_latency_ms': 100,
        'max_utilization_percent': 80
    },
    'optimization_targets': {
        'nvme_queue_depth': 128,
        'ssd_queue_depth': 32,
        'hdd_queue_depth': 8
    }
}

# Usage Example
if __name__ == "__main__":
    optimizer = EnterpriseStorageOptimizer(storage_config)
    
    # Analyze storage devices
    devices = optimizer.analyze_storage_devices()
    print(f"Found {len(devices)} storage devices")
    
    # Run optimizations on first device
    if devices:
        first_device = list(devices.keys())[0]
        
        scheduler_result = optimizer.optimize_io_scheduler(first_device)
        readahead_result = optimizer.optimize_readahead(first_device)
        queue_result = optimizer.optimize_queue_depth(first_device)
        
        # Generate comprehensive report
        report = optimizer.generate_storage_optimization_report()
        print(json.dumps(report, indent=2, default=str))
```

This comprehensive storage performance optimization framework provides:

1. **Multi-Storage Support**: NVMe, SSD, HDD optimization strategies
2. **Performance Benchmarking**: Sequential and random I/O testing
3. **I/O Scheduler Optimization**: Intelligent scheduler selection
4. **Queue Depth Tuning**: Optimal concurrent I/O configuration
5. **Read-Ahead Optimization**: Storage-type specific tuning
6. **Real-time Monitoring**: Continuous performance tracking
7. **Automated Alerts**: Performance degradation detection
8. **Comprehensive Reporting**: Detailed analysis and recommendations

The system enables storage administrators to systematically analyze, optimize, and monitor storage performance across diverse storage technologies with enterprise-grade capabilities.
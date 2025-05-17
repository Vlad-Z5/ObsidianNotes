## Family Types

General Purpose: t4g (Graviton2), t3 / t3a (Burstable), m6i / m6a / m7i  
Compute Optimized: c6g / c6i / c7i  
Memory Optimized: r6i / r6a / r7i, x2idn / x2iedn (High Memory)  
Storage Optimized: i4i / i3 (High IOPS), d3 / d3en (Dense HDD)  
GPU Optimized: g4dn / g5 (General Purpose), p3 / p4 (ML Training)  
Machine Learning Inference Optimized: inf1  
High Performance Computing Optimized: hpc6id / hpc6a

## SSH
 
Exclude spaces from private key, if it does nor have the needed permissions - chmod 400 /path/to/your-key.pem
Allow 22 inbound in the SG

### Misc

If App times out - issue on the SG / firewall level, 
if Connection refused - app error (restart or terminate and respawn instance),
if Permission denied - check security key, SG, user / role,
Otherwise use Instance Connect
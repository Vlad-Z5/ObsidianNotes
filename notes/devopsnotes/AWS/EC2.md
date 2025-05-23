## **Family Types**

- **General Purpose:** `t4g` (Graviton2), `t3` / `t3a` (Burstable), `m6i` / `m6a` / `m7i`
- **Compute Optimized:** `c6g` / `c6i` / `c7i`
- **Memory Optimized:** `r6i` / `r6a` / `r7i`, `x2idn` / `x2iedn` (High Memory)
- **Storage Optimized:** `i4i` / `i3` (High IOPS), `d3` / `d3en` (Dense HDD)
- **GPU Optimized:** `g4dn` / `g5` (General Purpose), `p3` / `p4` (ML Training)
- **Machine Learning Inference Optimized:** `inf1`
- **High Performance Computing Optimized:** `hpc6id` / `hpc6a`

---

## **Purchasing Options**

- **Reserved Instances (RI):** Specific **type**, **region**, **tenancy**, **OS**. Scope can be **regional** or **Availability Zone (AZ)**. Terms: **1 or 3 years**.  
  - **Convertible RI** allows changes to instance family, OS, tenancy, and region.

- **On-Demand:** Pay for compute capacity by the **second** (Windows, Linux) or **hour** (other OS) without long-term commitments.

- **Spot Instances:** Use spare capacity at up to 90% discount, can be interrupted. **2 min termination notice** via CloudWatch or instance metadata.

- **Dedicated Instance:** EC2 runs on hardware dedicated to a single tenant but shared host. Shared hardware.

- **Dedicated Host:** Physical server fully dedicated to your use. Visibility into sockets, cores, and host ID.

- **Capacity Reservations:** Reserve capacity in a specific AZ for your EC2 instance types.

- **Savings Plans:**
  - **Compute Savings Plan:** Applies to EC2, Fargate, Lambda across any region and family.
  - **EC2 Instance Savings Plan:** Limited to a specific instance family in a region.
  - Both require **1- or 3-year** commitment with **per-hour** billing.

---

## **SSH**

- **Key Permissions:** Ensure the private key has strict permissions:  
  `chmod 400 /path/to/your-key.pem`

- **Security Group Rule:** Allow **inbound port 22** for SSH in the Security Group.

---

## **Miscellaneous**

- **App Times Out:** Likely a **Security Group or firewall** issue (port not open).
- **Connection Refused:** Likely an **application error**; try restarting the app or the instance.
- **Permission Denied:** Check:
  - **Private key permissions**
  - **Correct key used**
  - **Security Group settings**
  - **IAM role or user permissions**
  - Unused or unattached **EIPs** incur **hourly charges**.

- **AWS Instance Connect:** Use for browser-based SSH without needing a key, if IAM and instance settings allow it.
- **Instance metadata** curl IP of the instance /latest/meta-data
- **EC2 User Data** is used to run script at boot, it is in its advanced details

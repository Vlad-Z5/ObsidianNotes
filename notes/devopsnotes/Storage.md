
- ### Physical Storage Types
	- **HDD**: mechanical spinning disk, cheaper, slower, more storage
	- **SSD**: flash memory, faster, more expensive, no moving parts
	- **NVMe**: SSD with PCIe interface, much faster than SATA SSDs
	- **SATA**: Serial ATA interface for HDDs and SSDs, common, slower than SAS
    - **SAS**: Serial Attached SCSI, faster and more reliable than SATA, used in enterprise storage
- ### Storage Architectures
	- **DAS (Direct Attached Storage)**: directly connected to a single computer (e.g., internal HDD, USB drive)
	- **NAS (Network Attached Storage)**: shared storage over a network with its own OS; accessible via protocols like NFS/SMB
	- **SAN (Storage Area Network)**: high-speed network of storage devices, used in data centers; block-level access
- ### RAID (Redundant Array of Independent Disks)
	- **RAID 0**: striping, no redundancy, fast, no fault tolerance
	- **RAID 1**: mirroring, 1:1 copy, fault-tolerant
	- **RAID 5**: striping + parity, needs 3+ disks, fault-tolerant
	- **RAID 6**: like RAID 5 but with extra parity, survives 2 disk failures
	- **RAID 10**: mirror of stripes (RAID 1+0), needs 4+ disks, fast and fault-tolerant

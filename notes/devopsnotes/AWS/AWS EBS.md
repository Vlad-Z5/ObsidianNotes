- **Type:** Persistent, block-level storage for EC2, limited to one AZ, to replicate use snapshot
- **Attached To:** One EC2 instance at a time (can detach/attach), while EC2 can be attached to many EBS volumes
- **Provisioned capacity**: size in GB and IOPS, can be increased
- **Persistence:** Data persists beyond instance termination (unless "Delete on Termination" is enabled)
- **Snapshot:** Point-in-time backup stored in S3 (incremental after first snapshot)
- **Encryption:** Can be encrypted at rest (AES-256), in transit, and during snapshot copy
- **Performance Modes:**
	  - **gp3:** General-purpose SSD (baseline + provisioned IOPS/throughput)
	  - **gp2:** Older general-purpose SSD (baseline based on size)
	  - **io2/io1:** High-performance SSD for critical workloads (provisioned IOPS), has option to attach to multiple EC2
	  - **st1:** Throughput-optimized HDD (big, sequential workloads)
	  - **sc1:** Cold HDD (infrequently accessed)
- **Resize:** Volume size and type can be modified without downtime
- **Multi-Attach:** io1/io2 can attach to multiple instances in the same AZ (only for certain use cases)
-  Main use cases: databases, file systems, boot volumes, and apps requiring persistent storage.

## Increasing EBS Volume Size

```bash
# Modify Volume Size

aws ec2 modify-volume --volume-id vol-<volume> --size NEW_SIZE # Resize command

aws ec2 describe-volumes-modifications --volume-ids vol-<volume> # Wait until resize is complete

# Resize filesystem

sudo growpart /dev/<volume> # Extend partition if needed

sudo resize2fs /dev/<volume> # Resize for ext4
sudo xfs_growfs -d / # Resize for XFS
```
## Decreasing EBS Volume Size

```bash


# Shrink filesystem
sudo umount /dev/xvdf
sudo e2fsck -f /dev/xvdf
sudo resize2fs /dev/xvdf 20G

# Backup and Snapshot
aws ec2 create-snapshot --volume-id vol-<volume>

# Create smaller EBS volume from snapshot
aws ec2 create-volume --snapshot-id snap-<id> --availability-zone <az> --size <size>

# Attach new volume to instance
aws ec2 attach-volume --volume-id vol-<new> --instance-id i-<instance> --device /dev/xvdg

# Mount points
sudo mkdir -p /mnt/oldvolume
sudo mkdir -p /mnt/newvolume

# Mount volumes
sudo mount /dev/xvdf /mnt/oldvolume
sudo mount /dev/xvdg /mnt/newvolume

# Data transfer
sudo rsync -aAXv /mnt/oldvolume/ /mnt/newvolume/

# Unmount old
sudo umount /mnt/oldvolume

# Detach old
aws ec2 detach-volume --volume-id vol-<old>

# Mount new in place of old
sudo mount /dev/xvdg /mnt/<original-mountpoint>

# Optional: update /etc/fstab

# Delete old
aws ec2 delete-volume --volume-id vol-<old>
```
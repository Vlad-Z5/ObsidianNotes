Requires IGW

- **Purpose:** Allow private subnet resources to access the internet without exposing them directly  
- **Type:** Managed NAT service by AWS (scalable and highly available within an AZ)  
- **Elastic IP:** Requires one EIP per NAT Gateway  
- **AZ-Specific:** Must deploy one per Availability Zone for fault tolerance  
- **Billing:** Charged per hour + per GB of data processed  
- **Alternative:** NAT Instance (EC2-based, manually managed and less scalable)

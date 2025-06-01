Connects two VPCs for private communication, their CIDR ranges can't overlap
- **Peer types:** Same or different AWS accounts and regions (inter-region peering)
- **No transitive routing:** Must create peering for each VPC pair
- **Traffic:** Uses private IPs, no internet or gateway needed
- **Limits:** Max peering connections per VPC apply
- **Use cases:** Shared services, cross-account access, hybrid architectures
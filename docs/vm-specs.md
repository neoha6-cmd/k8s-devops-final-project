# VM Specifications (Path B: VMware Workstation)

| Node | Hostname | Role | Private IP | vCPU | RAM | Disk |
|------|----------|------|------------|------|-----|------|
| cp1 | k8slab-cp1 | Control Plane / Ansible Controller | 10.0.1.10 | 2 | 4 GB | 40 GB |
| w1 | k8slab-w1 | Worker Node / Managed Node | 10.0.1.11 | 2 | 4 GB | 40 GB |

- OS: Rocky Linux 10
- Network: VMware NAT (VMnet8), subnet 10.0.1.0/24, gateway 10.0.1.2
- Access: SSH key only (ed25519); automation user: ali
- Both hostnames are listed in /etc/hosts on both VMs

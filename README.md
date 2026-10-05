# k8s-devops-final-project

End-to-end automated container platform: infrastructure as code (Terraform), configuration management (Ansible) and a Kubernetes v1.36 cluster with Calico CNI.

## Environment (Path B: VMware Workstation, no Azure)

| Node | Hostname | Role | IP | Specs |
|------|----------|------|----|-------|
| cp1 | k8slab-cp1 | Control plane / Ansible controller | 10.0.1.10 | 2 vCPU, 4 GB RAM, 40 GB disk |
| w1 | k8slab-w1 | Worker | 10.0.1.11 | 2 vCPU, 4 GB RAM, 40 GB disk |

- VMware NAT network (VMnet8) set to 10.0.1.0/24, gateway 10.0.1.2.
- Notes: the VMs run Rocky Linux 10 (the spec mentions 9); package names and steps were adapted accordingly. Terraform code was written, formatted and validated (`terraform fmt -check`, `terraform validate`) but not applied (Path B).
- Details: see `docs/vm-specs.md`.

## Part A: Repository and Workstation Setup

### Task 1: Repository and Git hygiene
1. Which files did you exclude with .gitignore, and what sensitive data would they leak if committed?
   - `*.tfstate*`: Terraform state maps code to real resources and can contain resource IDs and secret values.
   - `.terraform/`: provider binaries and cached data (large, machine specific, not source code).
   - `terraform.tfvars`: real variable values such as the subscription ID and my public IP.
   - Private SSH keys (`*_key`, `id_*`, `*.pem`): would give anyone full access to the servers.
   - `kubeconfig` / `admin.conf`: cluster-admin credentials for the Kubernetes API.
2. If a secret is committed and deleted in a later commit, is it safe? No. The secret stays in the Git history, and anyone who clones the repository can recover it. The secret must be rotated (revoked and replaced), and the history rewritten if necessary.

### Task 2: Workstation tool verification
How does Terraform authenticate to Azure in this setup, and why is it safer than hardcoding credentials in .tf files? The azurerm provider reuses the session created by `az login` (a short-lived token stored locally). Hardcoded credentials in .tf files would be committed to Git and leaked, while the CLI token stays on the workstation, expires and can be revoked. (Path B: Azure was not used; the installed tools are git, ssh, python3 and terraform.)

## Part B: Infrastructure as Code (Terraform / VMware)

### Task 3: Azure subscription setup (Path A only)
Not applicable on Path B. For reference: running `terraform apply` before accepting the marketplace terms fails, because Azure refuses to deploy a marketplace image until its legal terms are accepted for the subscription.

### Task 4: Dedicated SSH key pair
What is the difference between a public key and a private key, and where does each reside? The private key is secret, stays only on the machine of the user and proves identity by signing a challenge. The public key can be shared safely and is placed on servers in `~/.ssh/authorized_keys` to verify that signature. The private key cannot be derived from the public key.

### Task 5: Terraform infrastructure code
1. Why does the NSG not need rules for Kubernetes traffic between cp1 and w1? Both VMs are in the same subnet/VNet, and Azure's default NSG rules allow all traffic inside the virtual network (AllowVnetInBound).
2. Why must the private IPs be static for this cluster? Kubernetes and Ansible reference nodes by IP and hostname. A changing IP would break the /etc/hosts entries, the API server certificate and node registration.
3. What is stored in terraform.tfstate, and why must it never be pushed to Git? It maps the code to real resources and stores their attributes, possibly including secrets. Anyone with access to the repository could read them.

### Task 6B: VMware alternative
Two Rocky Linux VMs with static IPs and hostnames, both added to /etc/hosts, SSH key login, documented in `docs/vm-specs.md`. `terraform validate` passes on the code.

## Part C: Secure Access and Automation Identity

### Task 7: Dedicated automation user (ali)
1. Why does the user need passwordless sudo on cp1 as well, even though cp1 is the Ansible controller? Ansible uses privilege escalation (become) on every node, including the controller, and runs non-interactively. A password prompt would stop the automation.
2. Why is a sudoers drop-in file safer than editing /etc/sudoers directly? A syntax mistake in the main file can break sudo for everyone. A separate file in /etc/sudoers.d/ is isolated, easy to audit or remove, and can be validated with `visudo -cf` before use.

### Task 8: Key-based SSH from cp1 to w1
1. Why does ssh-copy-id fail on Azure VMs by default, and how did you install the key on w1? Azure VMs disable password login, so ssh-copy-id has no password to authenticate with and the key must be installed through an already authorized account. In this lab ssh-copy-id also failed (sshd temporarily rejected connections), so I appended the public key to /home/ali/.ssh/authorized_keys on w1 manually through the admin account, then fixed the ownership, the permissions and the SELinux context (`restorecon`).
2. What happens if permissions on .ssh or authorized_keys are too loose? sshd (StrictModes) ignores the key and rejects the login, because other users could read or modify the keys.

## Part D: Ansible Foundation

### Task 9: Install Ansible on the controller only
Why does w1 require no Ansible software installed? Ansible is agentless: the controller connects over SSH and runs small Python modules on the target. w1 only needs sshd and Python 3.

### Task 10: Inventory and group variables
Why is cp1 managed with ansible_connection=local instead of connecting over SSH to itself? The controller already runs on cp1, so Ansible executes tasks directly on it. SSH to itself would be unnecessary and would need extra key setup.

### Task 11: Playbook 1 (prepare-nodes.yml)
What does "idempotency" mean in Ansible and Infrastructure as Code? Running the same playbook several times produces the same end state: tasks change only what differs from the desired state. The first run installs and configures (changed), the second run reports changed=0. This makes automation safe to re-run and to recover from partial failures.

## Part E: Kubernetes Cluster in "One Shot"

### Task 12: Deployment playbook architecture
Why can the execution order of control-plane.yml and workers.yml never be swapped? kubeadm init on cp1 creates the API server, the certificates and the join token. A worker can only join a cluster that already exists, using the join command generated by cp1.

### Task 13: OS prerequisites and container runtime
1. Why does the Kubernetes kubelet refuse to run if SWAP is enabled? Kubernetes schedules pods based on memory requests and limits. Swap makes memory behavior unpredictable and breaks those guarantees, so kubelet fails by default unless swap is explicitly allowed.
2. Why must both containerd and kubelet use the same cgroup driver (systemd)? systemd already manages cgroups on the host. If kubelet and containerd use different drivers, two managers control the same resources, which causes instability under resource pressure.

### Task 14: Install Kubernetes and initialize the control plane
Why is the control plane node in NotReady status until Calico CNI is applied? Without a CNI plugin, kubelet reports that the network plugin is not ready, because pods cannot get network interfaces or IP addresses. Calico installs the CNI configuration and networking components, after which the node becomes Ready.

### Task 15: Join the worker and verify the cluster
`ansible-playbook -i inventory.ini site.yml` builds the whole cluster. Both nodes report Ready in `kubectl get nodes -o wide`.

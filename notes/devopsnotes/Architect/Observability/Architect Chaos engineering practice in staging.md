# Chaos engineering practice in staging

# Content from previous subtopic: [[Distributed tracing and service dependency maps

Use canary tracing or distributed tracing (X-ray/Jaeger) to find slow spans.
Isolation: scale out target group, shift traffic to healthy AZ, or use a feature-flag to disable heavy endpoints. Then patch root cause.

Q: Systemd journal logs vanish on reboot across some AMIs. What to check?

Checks:

Confirm Storage= option in /etc/systemd/journald.conf (e.g., volatile vs persistent).

Check if /var/log/journal exists and permissions; if missing, journald stores in memory — lost on reboot.

Check image build steps that clean /var/log.

Cloud-init or image cleanup scripts deleting journal files.
Fix: ensure persistent journal enabled, correct permissions, and not deleted during image bake.

Q: A production pod was OOMKilled but you can’t find logs. Forensic debug.

Steps:

Inspect kubectl describe pod and kubectl get events for OOM info; check containerStatuses.

Check node dmesg and kubelet logs for OOM killer messages (which process was killed).

Retrieve previous logs via kubectl logs --previous if container restarted.

Check resource requests/limits — maybe limit too low.

Check core dumps, if enabled (/var/lib/systemd/coredump or configured host path).

Correlate with metrics (memory spike) and GC/patterns in app telemetry.
Note: encourage enabling log persistence, resource metrics, and coredump capture for future forensic.

Q: Kernel panic on a GKE node mid-deploy. How to identify infra vs image vs app?

Approach:

Gather node crash artifacts: serial console logs, kubelet logs, stack traces (if available).

Check recent package/kernel updates or kernel modules introduced in image.

Check for crash signatures across multiple nodes (if many nodes panic → infra/OS).

Check node-level metrics: memory pressure, disk errors, NIC driver bugs, taints.

If only nodes with specific workloads panic → inspect workload (privileged, eBPF, kernel modules).

Reproduce in canary with same base image + workload; update kernel/drivers if needed.
Checklist: image/kernel version, node autoscaler event timeline, kernel oops logs, driver/firmware versions.
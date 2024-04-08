Crio must be configured post kata-containers RPM installation.
Add or edit the following to crio-conf.

    [crio.runtime.runtimes.kata]
      runtime_path = "/usr/bin/containerd-shim-kata-v2"
      runtime_root = "/run/vc"
      runtime_type = "vm"
      privileged_without_host_devices = true

Enable and restart the cri-o service.

    systemctl enable crio
    systemctl restart crio

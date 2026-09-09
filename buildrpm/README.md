# Kata Containers 4.1.0 RPM packaging

This directory is a regenerated 4.1.0 packaging baseline.  Its spec and
patches target the source interfaces in this checkout, rather than retaining
the pre-4.1.0 patch contexts.

The package build performs these logged stages:

1. Build the Go runtime, shim, monitor, and log parser with Go 1.25.13 or
   newer.
2. Build the Rust guest agent with Rust 1.95 or newer.
3. Build the initrd and rootfs image using the locally built agent binary and
   generated systemd unit files.
4. Install and package the host runtime, guest agent, guest image, and all
   agent extension units, helpers, and generator.

Run `./validate-rpm-prep.sh` before a full RPM build.  It creates a disposable
source archive and runs only `%prep`; it neither modifies the checkout nor
builds the privileged rootfs image.

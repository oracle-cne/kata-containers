
%global with_debug 0

%if 0%{?with_debug}
%global _find_debuginfo_dwz_opts %{nil}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package %{nil}
%endif

%global domain      github.com
%global org         kata-containers
%global repo        kata-containers
%global download    %{domain}/%{org}/%{repo}
%global importname  %{download}

%global qemupath %{_libexecdir}/qemu-kvm

%ifarch aarch64
%global machinetype "virt"
%endif
%ifarch x86_64
%global machinetype "q35"
%endif

%global katadatadir             %{_datadir}/defaults
%global katadefaults            %{katadatadir}/kata-containers

%global rust_make_vars          LIBC=gnu

%global runtime_make_vars       QEMUPATH=%{qemupath} \\\
                                KERNELTYPE="compressed" \\\
                                DEFSHAREDFS="virtio-fs" \\\
                                DEFVIRTIOFSDAEMON=%{_libexecdir}/"virtiofsd" \\\
                                DEFVIRTIOFSCACHESIZE=0 \\\
                                DEFSANDBOXCGROUPONLY=true \\\
                                SKIP_GO_VERSION_CHECK=y \\\
                                MACHINETYPE=%{machinetype} \\\
                                SCRIPTS_DIR=%{_bindir} \\\
                                DESTDIR=%{buildroot} \\\
                                PREFIX=/usr \\\
                                DEFAULTSDIR=%{katadefaults} \\\
                                CONFDIR=%{katadefaults} \\\
                                FEATURE_SELINUX="yes"

%global agent_make_vars         %{rust_make_vars} \\\
                                DESTDIR=%{buildroot}
%global log_parser_vars         %{rust_make_vars} \\\
                                BINDIR=%{buildroot}%{_bindir}

%global _buildhost build-ol%{?oraclelinux}-%{?_arch}.oracle.com

Name:	      %{repo}
Version:      4.1.0
Release:      1%{?dist}
Vendor:	      Oracle America
Summary:      Kata Containers 4.1.0 runtime, guest agent, and rootfs image
Url:	      https://%{download}
Group:        Development/Tools
License:      Apache-2.0
Source0:      %{name}-%{version}.tar.bz2
Patch0:	      Makefile.patch
Patch1:       image_builder.sh.patch
Patch2:       tools-osbuilder-lib.patch

# Keep this in sync with versions.yaml and the repository go.mod files.
BuildRequires: golang >= 1.25.13
BuildRequires: qemu-img
BuildRequires: parted
BuildRequires: e2fsprogs
BuildRequires: util-linux
BuildRequires: gcc
BuildRequires: make
BuildRequires: systemd
BuildRequires: libselinux-devel
BuildRequires: libseccomp-devel

%define is_uek_kernel %(uname -a | awk '{print $3}' | grep -q uek && echo 0 || echo 1)

%if %{?oraclelinux} == 8
# Keep this in sync with versions.yaml and Cargo.toml.
BuildRequires: rust-toolset >= 1.92
# Use the QEMU package supplied by the target OL repository.
Requires: qemu-kvm-core
%if %{is_uek_kernel} == 0
Requires: kernel-uek >= 5.4.17
Requires: kernel-uek-container >= 5.4.17
%endif
%endif

%if %{?oraclelinux} == 9
# Keep this in sync with versions.yaml and Cargo.toml.
BuildRequires: rust-toolset >= 1.92
# Use the QEMU package supplied by the target OL repository.
Requires: qemu-kvm-core
%if %{is_uek_kernel} == 0
Requires: kernel-uek >= 5.15.0
Requires: kernel-uek-container >= 5.15.0
%endif
%endif

# Refer cri-o and cri-tools versions in versions.yaml of kata-containers repo
Requires: cri-o >= 1.23
Requires: cri-tools >= 1.23

%ifarch aarch64
BuildRequires: glibc
%if %{?oraclelinux} == 8
BuildRequires: iptables
%endif
%if %{?oraclelinux} == 9
BuildRequires: iptables-legacy
%endif
%endif

# Refer to the virtiofsd version in versions.yaml of kata-containers repo.
# For /usr/libexec/virtiofsd; use the target OL repository version.
Requires: virtiofsd
Suggests: virtiofsd

Obsoletes: kata <= %{version}
Obsoletes: kata-image <= %{version}
Obsoletes: kata-ksm-throttler <= %{version}
Obsoletes: kata-proxy <= %{version}
Obsoletes: kata-runtime <= %{version}
Obsoletes: kata-shim <= %{version}
Obsoletes: kata-agent <= %{version}

%description
Kata Containers 4.1.0. Kata Containers is an open source
project and community working to build a standard implementation of lightweight
Virtual Machines (VMs) that feel and perform like containers, but provide the
workload isolation and security advantages of VMs. https://katacontainers.io/.}

%prep
%setup -q -n %{name}-%{version}
%patch0
%patch1
%patch2

%build
export GOPATH=$(go env GOPATH)
GOPATH_SRC=$GOPATH/src/%{importname}
%__mkdir_p $(dirname $GOPATH_SRC)
rm -rf $GOPATH_SRC
%__ln_s %{_builddir}/%{name}-%{version} $GOPATH_SRC

# The 4.1.0 component Makefiles are invoked from their own directories but
# consume VERSION relative to the current directory.  Stage the canonical
# repository version file for those component builds.
echo "RPM build: staging VERSION for runtime, guest agent, and osbuilder"
install -m 0644 VERSION src/runtime/VERSION
install -m 0644 VERSION src/agent/VERSION
install -m 0644 VERSION tools/osbuilder/VERSION

#runtime
pushd src/runtime
%make_build %{runtime_make_vars}
popd

#agent
pushd src/agent
echo "RPM build: building the 4.1.0 guest agent"
%make_build %{agent_make_vars}
popd

pushd src/tools/log-parser
%make_build %{log_parser_vars}
popd

#osbuilder
%if %{?oraclelinux} == 8
mkdir  tools/osbuilder/rootfs-builder/ol8
cp buildrpm/oracle/ol8/* tools/osbuilder/rootfs-builder/ol8
%else
mkdir  tools/osbuilder/rootfs-builder/ol9
cp buildrpm/oracle/ol9/* tools/osbuilder/rootfs-builder/ol9
%endif
cp buildrpm/oracle/partprobe tools/osbuilder
cp buildrpm/oracle/build_kata_image tools/osbuilder
chmod 755 tools/osbuilder/build_kata_image

pushd tools/osbuilder
echo "RPM build: building the 4.1.0 guest initrd and rootfs image"
sh build_kata_image %{oraclelinux}
popd

%install

# Make sure to set GOPATH
export GOPATH=$(go env GOPATH)
pushd src/runtime
%make_install %{runtime_make_vars}
popd

pushd src/agent
%make_install %{agent_make_vars}
popd

pushd src/tools/log-parser
install kata-log-parser %{buildroot}%{_bindir}/kata-log-parser
popd

ImageDir=%{buildroot}/usr/share/kata-containers
mkdir -p ${ImageDir}
cp buildrpm/oracle/EULA tools/osbuilder

cp buildrpm/oracle/README_CRIO.md .

pushd tools/osbuilder
install -p kata-containers.img ${ImageDir}/kata-containers-%{version}.img
install -p kata-containers-initrd.img ${ImageDir}/kata-containers-initrd-%{version}.img
ln -sf kata-containers-%{version}.img ${ImageDir}/kata-containers.img
ln -sf kata-containers-initrd-%{version}.img ${ImageDir}/kata-containers-initrd.img

# Deliver the License
mkdir -p %{buildroot}/usr/share/doc/%{name}-%{version}
install -p EULA %{buildroot}/usr/share/doc/%{name}-%{version}/EULA
popd

# Remove non-tested / non-supported configuration files
#rm %{buildroot}%{_datadir}/kata-containers/defaults/configuration-*.toml

%files
%license buildrpm/oracle/EULA LICENSE THIRD_PARTY_LICENSES.txt olm/SECURITY.md
%dir /usr/share/kata-containers
/usr/share/kata-containers/kata-containers-%{version}.img
/usr/share/kata-containers/kata-containers-initrd-%{version}.img
/usr/share/kata-containers/kata-containers.img
/usr/share/kata-containers/kata-containers-initrd.img
%doc /usr/share/doc/%{name}-%{version}/EULA
%{_bindir}/kata-runtime
%{_bindir}/kata-monitor
%{_bindir}/containerd-shim-kata-v2
%{_bindir}/kata-collect-data.sh

#log-parser
%{_bindir}/kata-log-parser

%dir %{katadatadir}
%dir %{katadefaults}
%{katadefaults}/configuration.toml
%{katadefaults}/configuration-*.toml
%{_datadir}/bash-completion/completions/kata-runtime

#agent
%{_bindir}/kata-agent
/usr/lib/systemd/system/kata-agent.service
/usr/lib/systemd/system/kata-containers.target
/usr/lib/systemd/system/kata-extension-mount@.service
/usr/lib/systemd/system-generators/kata-extension-mount-generator
/usr/libexec/kata-extension-mount.sh
/usr/libexec/kata-extension-umount.sh

%post
# we need to make some baseline adjustments to the crio config post installation
checkCrioConf () {
  # arg1 config section, arg2 keyword, arg3 value
  # if keyword is missing, add it and value to config section
  if ! grep -q "^$2" %{_sysconfdir}/crio/crio.conf; then
    sed -i \
        -e "/^$1/a $2 = $3" \
        %{_sysconfdir}/crio/crio.conf
  else
  # keyword is present, ensure it has the correct value
    sed -i \
        -e "s/^$2.*/$2 = $3/" \
        %{_sysconfdir}/crio/crio.conf
  fi
}

checkCrioConf "\[crio.runtime\]" "manage_network_ns_lifecycle" "true"
checkCrioConf "\[crio.runtime\]" "selinux" "true"
checkCrioConf "\[crio.image\]" "registries" "\[\"docker.io\", \"container-registry.oracle.com\/olcne\"\]"
checkCrioConf "\[crio.image\]" "pause_image_auth_file" "\"\/run\/containers\/0\/auth.json\""
checkCrioConf "\[crio.image\]" "pause_image " "\"container-registry.oracle.com\/olcne\/pause:3.9\""

# insert extra config section if it's missing
if ! grep -q "\[crio.runtime.runtimes.kata\]" %{_sysconfdir}/crio/crio.conf; then
  sed -i \
      -e '/\[crio.runtime.runtimes.runc\]/i\
\[crio.runtime.runtimes.kata\]\
runtime_path = \"\/usr\/bin\/containerd-shim-kata-v2\"\
runtime_type = \"vm\"\
runtime_root = \"\/run\/vc\"\
privileged_without_host_devices = true\n'\
      %{_sysconfdir}/crio/crio.conf
else
checkCrioConf "\[crio.runtime.runtimes.kata\]" "runtime_path" "\"\/usr\/bin\/containerd-shim-kata-v2\""
checkCrioConf "\[crio.runtime.runtimes.kata\]" "runtime_type" "vm"
checkCrioConf "\[crio.runtime.runtimes.kata\]" "runtime_root" "\"\/run\/vc\""
checkCrioConf "\[crio.runtime.runtimes.kata\]" "privileged_without_host_devices" true
fi

# Configure configuration-qemu.toml
QEMU_CONF="/usr/share/defaults/kata-containers/configuration-qemu.toml"
sed -i '/image =/d' $QEMU_CONF
sed -i '/hypervisor.qemu/a initrd = "/usr/share/kata-containers/kata-containers-initrd.img"' $QEMU_CONF
sed -i 's!kernel =.*!kernel = "/usr/share/kata-containers/vmlinuz.container"!g' $QEMU_CONF
sed -i 's/shared_fs =.*/shared_fs = "virtio-fs"/g' $QEMU_CONF
# Enable vsock as transport instead of virtio-serial
sed -i -e 's/^#use_vsock =/use_vsock =/' $QEMU_CONF
%if %{?oraclelinux} == 8 || %{?oraclelinux} == 9
sed -i 's!path =.*!path = "/usr/libexec/qemu-kvm"!g' $QEMU_CONF
%endif

%changelog
* Fri Aug 21 2026 Oracle Cloud Native Environment Authors <noreply@oracle.com> - 4.1.0-1
- Added Oracle Specific Build Files for kata-containers

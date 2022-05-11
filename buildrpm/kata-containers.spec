{{{$version := printf "%s.%s.%s" .major .minor .patch }}}
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

%if %{?oraclelinux} == 7
%global qemupath %{_bindir}/qemu-system-x86_64
%else
%global qemupath %{_libexecdir}/qemu-kvm
%endif

%ifarch aarch64
%global machinetype "virt"
%endif
%ifarch x86_64
%global machinetype "q35"
%endif

#%global katadatadir             %{_datadir}/kata-containers
#%global katadefaults            %{katadatadir}/defaults
%global katadatadir             %{_datadir}/defaults
%global katadefaults            %{katadatadir}/kata-containers
%global katacache               %{_localstatedir}/cache
%global katalibexecdir          %{_libexecdir}/kata-containers
%global katalocalstatecachedir  %{katacache}/kata-containers

%global kataagentdir            %{katalibexecdir}/agent
%global kataosbuilderdir        %{katalibexecdir}/osbuilder

%global runtime_make_vars       QEMUPATH=%{qemupath} \\\
                                KERNELTYPE="compressed" \\\
                                DEFSHAREDFS="virtio-9p" \\\
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

%global agent_make_vars         LIBC=gnu \\\
                                DESTDIR=%{buildroot}%{kataagentdir}

%global _buildhost build-ol%{?oraclelinux}-%{?_arch}.oracle.com

Name:	      %{repo}
Version:      {{{$version}}}
Release:      1%{?dist}
Vendor:	      Oracle America
Summary:      Kata Containers version 2.x repository
Url:	      https://%{download} 
Group:        Development/Tools
License:      Apache-2.0
Source0:      %{name}-%{version}.tar.bz2
Patch0:       network.rs.patch
Patch1:       mount.rs.patch
Patch2:	      Makefile.patch

BuildRequires: golang >= 1.15.10
BuildRequires: qemu-img
BuildRequires: parted
BuildRequires: e2fsprogs
BuildRequires: util-linux
BuildRequires: make
BuildRequires: systemd
BuildRequires: libselinux-devel

%if %{?oraclelinux} == 7
BuildRequires: rust
BuildRequires: cargo
Requires: qemu >= 15:3.1
%endif

%if %{?oraclelinux} == 8
BuildRequires: rust-toolset
# qemu-kvm < 5.0.0 is needed by kata-1.12.1-2.el8.x86_64
Requires: qemu-kvm >= 4.1.1
%endif

Requires: cri-o >= 1.17
Requires: kernel-uek-container >= 5.4.17-2102.200.7%{dist}
Requires: kernel-uek >= 4.14
Requires: cri-tools >= 1.17

Obsoletes: kata
Obsoletes: kata-image
Obsoletes: kata-ksm-throttler
Obsoletes: kata-proxy
Obsoletes: kata-runtime
Obsoletes: kata-shim

%description
Kata Containers version 2.x repository. Kata Containers is an open source
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
%__mkdir_p $GOPATH_SRC
%__ln_s %{_builddir}/%{name}-%{version} $GOPATH_SRC

#agent
pwd
ls -la
pushd src/agent
%make_build %{agent_make_vars}
touch kata-agent
popd

#runtime
pushd src/runtime
%make_build %{runtime_make_vars}
popd

#osbuilder
%if %{?oraclelinux} == 7
mkdir  tools/osbuilder/rootfs-builder/ol7
cp buildrpm/oracle/ol7/* tools/osbuilder/rootfs-builder/ol7
%else
mkdir  tools/osbuilder/rootfs-builder/ol8
cp buildrpm/oracle/ol8/* tools/osbuilder/rootfs-builder/ol8
%endif
cp buildrpm/oracle/partprobe tools/osbuilder
cp buildrpm/oracle/build_kata_image tools/osbuilder
chmod 755 tools/osbuilder/build_kata_image

pushd tools/osbuilder
sh build_kata_image %{oraclelinux}
popd

%install
pushd src/runtime
%make_install %{runtime_make_vars}
popd

pushd src/agent
%make_install %{agent_make_vars}
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
%license buildrpm/oracle/EULA LICENSE
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

%dir %{katalibexecdir}
%{katalibexecdir}/kata-netmon

%{katadefaults}/*
%{_datadir}/bash-completion/completions/kata-runtime

#agent
%dir %{kataagentdir}
%{kataagentdir}/*

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
checkCrioConf "\[crio.runtime\]" "selinux" "false"
checkCrioConf "\[crio.image\]" "registries" "\[\"docker.io\", \"container-registry.oracle.com\"\]"
checkCrioConf "\[crio.image\]" "pause_image_auth_file" "\"\/run\/containers\/0\/auth.json\""
checkCrioConf "\[crio.image\]" "pause_image " "\"container-registry.oracle.com\/kubernetes\/pause:3.4\""

# Configure configuration-qemu.toml
QEMU_CONF="/usr/share/defaults/kata-containers/configuration-qemu.toml"
sudo sed -i '/image =/d' $QEMU_CONF
sudo sed -i '/hypervisor.qemu/a initrd = "/usr/share/kata-containers/kata-containers-initrd.img"' $QEMU_CONF
sudo sed -i 's!kernel =.*!kernel = "/usr/share/kata-containers/vmlinuz.container"!g' $QEMU_CONF
sudo sed -i 's/shared_fs =.*/shared_fs = "virtio-9p"/g' $QEMU_CONF
%if %{?oraclelinux} == 8
sudo sed -i 's!path =.*!path = "/usr/libexec/qemu-kvm"!g' $QEMU_CONF
%endif

%changelog
* {{{.changelog_timestamp}}} - {{{$version}}}-1
- Added Oracle Specific Build Files for kata-containers

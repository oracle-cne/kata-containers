OS_NAME="OracleLinux"
OS_VERSION=8

LOG_FILE="/var/log/yum-ol8.log"

BASE_URL="http://yum.oracle.com/repo/OracleLinux/OL8/baseos/latest/\$basearch"

GPG_KEY_FILE="RPM-GPG-KEY-oracle-ol8"

PACKAGES="iptables chrony"

#Optional packages:
# systemd: An init system that will start kata-agent if kata-agent
#          itself is not configured as init process.
[ "$AGENT_INIT" == "no" ] && PACKAGES+=" systemd" || true

# Init process must be one of {systemd,kata-agent}
INIT_PROCESS=systemd
# List of zero or more architectures to exclude from build,
# as reported by  `uname -m`
ARCH_EXCLUDE_LIST=()

[ "$SECCOMP" = "yes" ] && PACKAGES+=" libseccomp" || true
[ "$SELINUX" = yes ] && PACKAGES+=" container-selinux" || true

if [ "$SELINUX" == yes ]; then
    # AppStream repository is required for the container-selinux package
    APPSTREAM_URL="https://yum.oracle.com/repo/OracleLinux/OL8/appstream/\$basearch"
fi
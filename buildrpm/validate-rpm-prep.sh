#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

log() {
	echo "buildrpm4 validation: $*"
}

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
version=$(tr -d '[:space:]' < "${repo_root}/VERSION")
validation_root=$(mktemp -d "${TMPDIR:-/tmp}/kata-rpm-prep.XXXXXX")
trap 'log "removing ${validation_root}"; rm -rf "${validation_root}"' EXIT

log "repository=${repo_root} version=${version}"
log "creating disposable source archive"
mkdir -p "${validation_root}/SOURCES" "${validation_root}/SPECS"
git -C "${repo_root}" archive --format=tar --prefix="kata-containers-${version}/" HEAD | \
	bzip2 > "${validation_root}/SOURCES/kata-containers-${version}.tar.bz2"
cp "${repo_root}/buildrpm4/kata-containers.spec" \
	"${repo_root}/buildrpm4/Makefile.patch" \
	"${repo_root}/buildrpm4/image_builder.sh.patch" \
	"${repo_root}/buildrpm4/tools-osbuilder-lib.patch" \
	"${validation_root}/SOURCES/"
cp "${repo_root}/buildrpm4/kata-containers.spec" "${validation_root}/SPECS/"

log "running rpmbuild %prep for Oracle Linux 9"
rpmbuild -bp \
	--define 'oraclelinux 9' \
	--define "_topdir ${validation_root}" \
	--define "_sourcedir ${validation_root}/SOURCES" \
	"${validation_root}/SPECS/kata-containers.spec"
log "RPM %prep validation completed successfully"

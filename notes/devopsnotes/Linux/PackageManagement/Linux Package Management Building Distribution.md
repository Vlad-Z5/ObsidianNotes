# Linux Package Management Building Distribution

**Package building and distribution** covers creating custom packages, managing build environments, and distributing software through repositories for enterprise and open-source projects.

## Debian Package Building

### Package Structure and Setup
```bash
# Create package directory structure
mkdir -p myapp-1.0.0/{DEBIAN,usr/bin,usr/share/doc/myapp,etc/myapp}
cd myapp-1.0.0

# Create control file
cat << 'EOF' > DEBIAN/control
Package: myapp
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Essential: no
Depends: libc6, curl, python3
Maintainer: Your Name <your.email@company.com>
Description: My Application
 A longer description of the application
 that spans multiple lines and explains
 what the package does.
EOF

# Create additional control files
cat << 'EOF' > DEBIAN/postinst
#!/bin/bash
set -e

# Post-installation script
systemctl enable myapp
systemctl start myapp

exit 0
EOF

cat << 'EOF' > DEBIAN/prerm
#!/bin/bash
set -e

# Pre-removal script
systemctl stop myapp
systemctl disable myapp

exit 0
EOF

# Make scripts executable
chmod 755 DEBIAN/postinst DEBIAN/prerm
```

### Package Content and Files
```bash
# Copy application files
cp /path/to/myapp usr/bin/
cp /path/to/config.conf etc/myapp/

# Create documentation
cat << 'EOF' > usr/share/doc/myapp/README
MyApp Documentation
==================

Installation and usage instructions for MyApp.
EOF

# Create systemd service file
mkdir -p usr/lib/systemd/system
cat << 'EOF' > usr/lib/systemd/system/myapp.service
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/myapp
User=myapp
Group=myapp
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set proper permissions
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
chmod 755 usr/bin/myapp
```

### Building the Package
```bash
# Build package
cd ..
dpkg-deb --build myapp-1.0.0

# Verify package
dpkg --info myapp-1.0.0.deb
dpkg --contents myapp-1.0.0.deb
lintian myapp-1.0.0.deb

# Install and test
sudo dpkg -i myapp-1.0.0.deb
sudo apt install -f  # Fix dependencies if needed
```

### Advanced Debian Packaging
```bash
# Using debhelper (recommended approach)
mkdir myapp-source
cd myapp-source

# Create debian directory
mkdir debian

# Create control file
cat << 'EOF' > debian/control
Source: myapp
Section: utils
Priority: optional
Maintainer: Your Name <your.email@company.com>
Build-Depends: debhelper (>= 10)
Standards-Version: 4.1.2

Package: myapp
Architecture: amd64
Depends: ${shlibs:Depends}, ${misc:Depends}, python3, curl
Description: My Application
 A longer description of the application
EOF

# Create rules file
cat << 'EOF' > debian/rules
#!/usr/bin/make -f

%:
	dh $@

override_dh_auto_install:
	dh_auto_install
	install -D -m 755 myapp debian/myapp/usr/bin/myapp
	install -D -m 644 myapp.service debian/myapp/lib/systemd/system/myapp.service
EOF

chmod +x debian/rules

# Create changelog
cat << 'EOF' > debian/changelog
myapp (1.0.0-1) unstable; urgency=medium

  * Initial release

 -- Your Name <your.email@company.com>  Mon, 01 Jan 2024 12:00:00 +0000
EOF

# Build with debuild
debuild -us -uc
```

## RPM Package Building

### RPM Build Environment Setup
```bash
# Install build tools
dnf install rpm-build rpmlint rpmdevtools

# Create build environment
rpmdev-setuptree

# Directory structure created:
# ~/rpmbuild/
# ├── BUILD/
# ├── BUILDROOT/
# ├── RPMS/
# ├── SOURCES/
# ├── SPECS/
# └── SRPMS/
```

### RPM Spec File Creation
```bash
# Create spec file: ~/rpmbuild/SPECS/myapp.spec
cat << 'EOF' > ~/rpmbuild/SPECS/myapp.spec
Name:           myapp
Version:        1.0.0
Release:        1%{?dist}
Summary:        My Application

License:        MIT
URL:            https://github.com/company/myapp
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make
Requires:       curl
Requires:       python3

%description
A longer description of the application
that explains what the package does
and its features.

%prep
%setup -q

%build
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
%make_install

# Install systemd service
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
install -m 644 %{name}.service $RPM_BUILD_ROOT%{_unitdir}/%{name}.service

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d /var/lib/%{name} -s /sbin/nologin \
    -c "MyApp user" %{name}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%changelog
* Mon Jan 01 2024 Your Name <your.email@company.com> - 1.0.0-1
- Initial package
EOF
```

### Building RPM Package
```bash
# Create source tarball
mkdir myapp-1.0.0
# Copy source files to myapp-1.0.0/
tar czf ~/rpmbuild/SOURCES/myapp-1.0.0.tar.gz myapp-1.0.0/

# Build package
rpmbuild -ba ~/rpmbuild/SPECS/myapp.spec

# Check package
rpmlint ~/rpmbuild/RPMS/x86_64/myapp-1.0.0-1.el8.x86_64.rpm
rpm -qip ~/rpmbuild/RPMS/x86_64/myapp-1.0.0-1.el8.x86_64.rpm
rpm -qlp ~/rpmbuild/RPMS/x86_64/myapp-1.0.0-1.el8.x86_64.rpm

# Install and test
sudo rpm -ivh ~/rpmbuild/RPMS/x86_64/myapp-1.0.0-1.el8.x86_64.rpm
```

## Build Automation

### Jenkins Pipeline for Package Building
```groovy
// Jenkinsfile
pipeline {
    agent any

    parameters {
        choice(
            name: 'PACKAGE_TYPE',
            choices: ['deb', 'rpm', 'both'],
            description: 'Package type to build'
        )
        string(
            name: 'VERSION',
            defaultValue: '1.0.0',
            description: 'Package version'
        )
    }

    environment {
        PACKAGE_NAME = 'myapp'
        BUILD_DIR = 'build'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Application') {
            steps {
                sh '''
                    make clean
                    make all
                    make test
                '''
            }
        }

        stage('Build DEB Package') {
            when {
                anyOf {
                    params.PACKAGE_TYPE == 'deb'
                    params.PACKAGE_TYPE == 'both'
                }
            }
            steps {
                sh '''
                    ./scripts/build-deb.sh ${VERSION}
                '''
                archiveArtifacts artifacts: '*.deb', fingerprint: true
            }
        }

        stage('Build RPM Package') {
            when {
                anyOf {
                    params.PACKAGE_TYPE == 'rpm'
                    params.PACKAGE_TYPE == 'both'
                }
            }
            steps {
                sh '''
                    ./scripts/build-rpm.sh ${VERSION}
                '''
                archiveArtifacts artifacts: '*.rpm', fingerprint: true
            }
        }

        stage('Package Testing') {
            parallel {
                stage('Test DEB') {
                    when {
                        anyOf {
                            params.PACKAGE_TYPE == 'deb'
                            params.PACKAGE_TYPE == 'both'
                        }
                    }
                    steps {
                        sh '''
                            docker run --rm -v $(pwd):/workspace ubuntu:20.04 /bin/bash -c "
                                cd /workspace
                                apt update
                                apt install -y ./*.deb
                                systemctl --version || echo 'systemctl not available in container'
                                ${PACKAGE_NAME} --version
                            "
                        '''
                    }
                }

                stage('Test RPM') {
                    when {
                        anyOf {
                            params.PACKAGE_TYPE == 'rpm'
                            params.PACKAGE_TYPE == 'both'
                        }
                    }
                    steps {
                        sh '''
                            docker run --rm -v $(pwd):/workspace centos:8 /bin/bash -c "
                                cd /workspace
                                dnf install -y ./*.rpm
                                ${PACKAGE_NAME} --version
                            "
                        '''
                    }
                }
            }
        }

        stage('Upload to Repository') {
            steps {
                script {
                    if (params.PACKAGE_TYPE == 'deb' || params.PACKAGE_TYPE == 'both') {
                        sh './scripts/upload-deb.sh'
                    }
                    if (params.PACKAGE_TYPE == 'rpm' || params.PACKAGE_TYPE == 'both') {
                        sh './scripts/upload-rpm.sh'
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            slackSend(
                color: 'good',
                message: "Package build successful: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "Package build failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
            )
        }
    }
}
```

### GitHub Actions Package Build
```yaml
# .github/workflows/package-build.yml
name: Package Build

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Package version'
        required: true
        default: '1.0.0'

jobs:
  build-deb:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build DEB package
        run: |
          sudo apt update
          sudo apt install -y devscripts build-essential lintian
          ./scripts/build-deb.sh ${{ github.event.inputs.version || github.ref_name }}

      - name: Test DEB package
        run: |
          sudo dpkg -i *.deb || sudo apt install -f -y
          myapp --version

      - name: Upload DEB artifact
        uses: actions/upload-artifact@v2
        with:
          name: deb-package
          path: '*.deb'

  build-rpm:
    runs-on: ubuntu-latest
    container: centos:8
    steps:
      - uses: actions/checkout@v2

      - name: Install build dependencies
        run: |
          dnf install -y rpm-build rpmdevtools gcc make

      - name: Build RPM package
        run: |
          ./scripts/build-rpm.sh ${{ github.event.inputs.version || github.ref_name }}

      - name: Test RPM package
        run: |
          dnf install -y *.rpm
          myapp --version

      - name: Upload RPM artifact
        uses: actions/upload-artifact@v2
        with:
          name: rpm-package
          path: '*.rpm'

  release:
    needs: [build-deb, build-rpm]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v2

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            deb-package/*.deb
            rpm-package/*.rpm
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Package Building Scripts

### Automated DEB Build Script
```bash
#!/bin/bash
# build-deb.sh

set -euo pipefail

VERSION="${1:-1.0.0}"
PACKAGE_NAME="myapp"
BUILD_DIR="build"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log "Starting DEB package build for $PACKAGE_NAME version $VERSION"

# Clean and create build directory
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}"

# Copy source files
cp -r src/* "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}/"
cp -r debian "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}/"

# Update version in control files
cd "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}"

# Update changelog
cat << EOF > debian/changelog
$PACKAGE_NAME ($VERSION-1) unstable; urgency=medium

  * Version $VERSION release

 -- Build System <build@company.com>  $(date -R)

$(cat debian/changelog)
EOF

# Build package
debuild -us -uc

# Copy built package
cp ../*.deb ../../

log "DEB package build completed successfully"
```

### Automated RPM Build Script
```bash
#!/bin/bash
# build-rpm.sh

set -euo pipefail

VERSION="${1:-1.0.0}"
PACKAGE_NAME="myapp"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log "Starting RPM package build for $PACKAGE_NAME version $VERSION"

# Setup RPM build environment
rpmdev-setuptree

# Create source tarball
TEMP_DIR=$(mktemp -d)
mkdir "$TEMP_DIR/${PACKAGE_NAME}-${VERSION}"
cp -r src/* "$TEMP_DIR/${PACKAGE_NAME}-${VERSION}/"

cd "$TEMP_DIR"
tar czf "$HOME/rpmbuild/SOURCES/${PACKAGE_NAME}-${VERSION}.tar.gz" "${PACKAGE_NAME}-${VERSION}/"

# Update spec file version
cd "$OLDPWD"
sed -i "s/^Version:.*/Version: $VERSION/" rpm/${PACKAGE_NAME}.spec
cp rpm/${PACKAGE_NAME}.spec "$HOME/rpmbuild/SPECS/"

# Build package
rpmbuild -ba "$HOME/rpmbuild/SPECS/${PACKAGE_NAME}.spec"

# Copy built package
cp "$HOME/rpmbuild/RPMS/x86_64/${PACKAGE_NAME}-${VERSION}"*.rpm ./

log "RPM package build completed successfully"

# Cleanup
rm -rf "$TEMP_DIR"
```

## Package Distribution

### Repository Upload Scripts
```bash
#!/bin/bash
# upload-deb.sh

set -euo pipefail

REPO_SERVER="repo.company.com"
REPO_PATH="/var/www/html/repo"
CODENAME="focal"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

for deb_file in *.deb; do
    if [[ -f "$deb_file" ]]; then
        log "Uploading $deb_file to repository"

        # Upload to repository server
        scp "$deb_file" "$REPO_SERVER:/tmp/"

        # Add to repository
        ssh "$REPO_SERVER" "
            cd $REPO_PATH
            reprepro includedeb $CODENAME /tmp/$deb_file
            rm /tmp/$deb_file
        "

        log "Successfully uploaded $deb_file"
    fi
done

log "DEB upload completed"
```

```bash
#!/bin/bash
# upload-rpm.sh

set -euo pipefail

REPO_SERVER="repo.company.com"
REPO_PATH="/var/www/html/repo"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

for rpm_file in *.rpm; do
    if [[ -f "$rpm_file" ]]; then
        log "Uploading $rpm_file to repository"

        # Upload to repository server
        scp "$rpm_file" "$REPO_SERVER:$REPO_PATH/packages/"

        # Update repository metadata
        ssh "$REPO_SERVER" "
            cd $REPO_PATH
            createrepo --update .
            gpg --detach-sign --armor repodata/repomd.xml
        "

        log "Successfully uploaded $rpm_file"
    fi
done

log "RPM upload completed"
```

## Quality Assurance

### Package Testing Framework
```bash
#!/bin/bash
# test-package.sh

set -euo pipefail

PACKAGE_FILE="$1"
PACKAGE_TYPE="${2:-auto}"

# Auto-detect package type
if [[ "$PACKAGE_TYPE" == "auto" ]]; then
    if [[ "$PACKAGE_FILE" == *.deb ]]; then
        PACKAGE_TYPE="deb"
    elif [[ "$PACKAGE_FILE" == *.rpm ]]; then
        PACKAGE_TYPE="rpm"
    else
        echo "Cannot determine package type from filename"
        exit 1
    fi
fi

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

test_deb_package() {
    local deb_file="$1"

    log "Testing DEB package: $deb_file"

    # Validate package structure
    dpkg --info "$deb_file"
    dpkg --contents "$deb_file"

    # Lint package
    lintian "$deb_file"

    # Test installation in container
    docker run --rm -v "$(pwd):/test" ubuntu:20.04 /bin/bash -c "
        cd /test
        apt update
        apt install -y ./$deb_file
        dpkg -l | grep myapp
        systemctl status myapp --no-pager || echo 'Service check skipped in container'
    "

    log "DEB package test completed"
}

test_rpm_package() {
    local rpm_file="$1"

    log "Testing RPM package: $rpm_file"

    # Validate package
    rpm -qip "$rpm_file"
    rpm -qlp "$rpm_file"

    # Lint package
    rpmlint "$rpm_file"

    # Test installation in container
    docker run --rm -v "$(pwd):/test" centos:8 /bin/bash -c "
        cd /test
        dnf install -y ./$rpm_file
        rpm -q myapp
        systemctl status myapp --no-pager || echo 'Service check skipped in container'
    "

    log "RPM package test completed"
}

case "$PACKAGE_TYPE" in
    deb)
        test_deb_package "$PACKAGE_FILE"
        ;;
    rpm)
        test_rpm_package "$PACKAGE_FILE"
        ;;
    *)
        echo "Unsupported package type: $PACKAGE_TYPE"
        exit 1
        ;;
esac

log "Package testing completed successfully"
```
Name: smolt
Summary: Hardware profiler
Version: 1.2
Release: %mkrel 2
License: GPLv2+
Group: System/Configuration/Hardware
URL: http://fedorahosted.org/smolt
Source: https://fedorahosted.org/releases/s/m/%{name}/%{name}-%{version}.tar.gz
Source1: README.install.urpmi
Patch0:	smolt-1.2-mandriva-release.patch
Patch1: smolt-1.2-remove-checkin.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

Requires: dbus-python
Requires: python-urlgrabber
Requires: gawk
Requires: python-paste
Requires: lsb-release
BuildArch: noarch
BuildRequires: gettext
BuildRequires: desktop-file-utils

Requires(pre): rpm-helper
Requires(post): python
Requires(postun): /sbin/service

%description
This hardware profiler is a server-client system that does a hardware
scan against a machine and sends the results to a public Fedora Project
turbogears server.  The sends are anonymous and should not contain any private
information other than the physical hardware information and basic OS info.

This package contains the client

%if 0
%package server
Summary: Fedora hardware profiler server
Group: System/Configuration/Hardware
Requires: smolt = %{version}
Requires: python-genshi
Requires: python-crypto
Requires: TurboGears mx
Requires: python-turboflot

%description server
This hardware profiler is a server-client system that does a hardware
scan against a machine and sends the results to a public Fedora Project
turbogears server.  The sends are anonymous and should not contain any private
information other than the physical hardware information and basic OS info.

This package contains the server portion
%endif

%package gui
Summary: Fedora hardware profiler gui
Group: System/Configuration/Hardware
Requires: smolt = %{version}

%description gui
Provides smolt's gui functionality.  Not included in the default package to
ensure that deps are kept small.

%prep
%setup -q
%patch0 -p1 -b .mandriva-release
%patch1 -p1 -b .checkin
sed -i -e "s/smolt\.png/smolt/" -e "s/the Fedora Project/smolts.org/"  client/smolt.desktop
find -name ".git*" -exec rm {} \;

%build
cd client/
make

%install
rm -rf %{buildroot}
pushd client
%makeinstall_std
popd
# install -d -m 0755 smoon/ %{buildroot}/%{_datadir}/%{name}/smoon/
mkdir -p %{buildroot}/%{_mandir}/man1/
#cp -adv smoon/* %{buildroot}/%{_datadir}/%{name}/smoon/
cp -adv client/simplejson %{buildroot}/%{_datadir}/%{name}/client/
cp client/scan.py %{buildroot}/%{_datadir}/%{name}/client/
cp client/os_detect.py %{buildroot}/%{_datadir}/%{name}/client/
cp client/fs_util.py %{buildroot}/%{_datadir}/%{name}/client/
cp client/man/* %{buildroot}/%{_mandir}/man1/

mkdir -p %{buildroot}/%{_sysconfdir}/sysconfig/

# Icons
mkdir -p %{buildroot}/%{_datadir}/icons/hicolor/16x16/apps/
mkdir -p %{buildroot}/%{_datadir}/icons/hicolor/22x22/apps/
mkdir -p %{buildroot}/%{_datadir}/icons/hicolor/24x24/apps/
mkdir -p %{buildroot}/%{_datadir}/icons/hicolor/32x32/apps/

mkdir -p %{buildroot}/%{_datadir}/firstboot/pixmaps/
mkdir -p %{buildroot}/%{_datadir}/firstboot/themes/default/

mv client/icons/smolt-icon-16.png %{buildroot}/%{_datadir}/icons/hicolor/16x16/apps/smolt.png
mv client/icons/smolt-icon-22.png %{buildroot}/%{_datadir}/icons/hicolor/22x22/apps/smolt.png
mv client/icons/smolt-icon-24.png %{buildroot}/%{_datadir}/icons/hicolor/24x24/apps/smolt.png
mv client/icons/smolt-icon-32.png %{buildroot}/%{_datadir}/icons/hicolor/32x32/apps/smolt.png
cp -adv client/icons/* %{buildroot}/%{_datadir}/%{name}/client/icons/

rm -f %{buildroot}/%{_bindir}/smoltSendProfile %{buildroot}/%{_bindir}/smoltDeleteProfile %{buildroot}/%{_bindir}/smoltGui
ln -s %{_datadir}/%{name}/client/sendProfile.py %{buildroot}/%{_bindir}/smoltSendProfile
ln -s %{_datadir}/%{name}/client/deleteProfile.py %{buildroot}/%{_bindir}/smoltDeleteProfile
ln -s %{_datadir}/%{name}/client/smoltGui.py %{buildroot}/%{_bindir}/smoltGui

ln -s %{_sysconfdir}/%{name}/config.py %{buildroot}/%{_datadir}/%{name}/client/config.py

desktop-file-install --dir=%{buildroot}/%{_datadir}/applications client/smolt.desktop
%find_lang %{name}

# Cleanup from the Makefile (will be cleaned up when it is finalized)
rm -f %{buildroot}/etc/init.d/smolt
rm -f %{buildroot}/etc/smolt/hw-uuid
rm -rf %{buildroot}/%{_datadir}/applications/fedora-smolt.desktop

touch %{buildroot}/%{_sysconfdir}/sysconfig/hw-uuid

echo 'ENABLE_MONTHLY_UPDATE=0' > %{buildroot}/%{_sysconfdir}/sysconfig/smolt

install -m 644 %{SOURCE1} README.install.urpmi

%clean
rm -rf %{buildroot}

%pre
%_pre_useradd smolt %{_datadir}/%{name} /sbin/nologin > /dev/null 2>&1 || :

%post
if [ $1 = 1 ]
then
    cat /proc/sys/kernel/random/uuid > /etc/sysconfig/hw-uuid
    chmod 0644 /etc/sysconfig/hw-uuid
    chown root:root /etc/sysconfig/hw-uuid
    python > /etc/cron.d/smolt << 'EOF'

from string import Template
from random import randint

cron_file = Template('''# Runs the smolt checkin client
$minute $hour $day * * smolt [ -r /ets/sysconfig/smolt ]  && . /etc/sysconfig/smolt && [ $ENABLE_MONTHLY_UPDATE = 1 ] && /usr/bin/smoltSendProfile -a > /dev/null 2>&1
''')

def main():
    minute = randint(0,59)
    hour = randint(0, 24)
    day = randint(0, 28) #account for febu-hairy

    print cron_file.safe_substitute(minute=minute, day=day, hour=hour)

if __name__ == '__main__':
    main()
EOF
fi

%postun
%_postun_userdel smolt
%_postun_groupdel smolt

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README doc/* README.install.urpmi
%dir %{_datadir}/%{name}
%config(noreplace) %dir %{_sysconfdir}/%{name}/
%config(noreplace) %{_sysconfdir}/sysconfig/smolt
%{_datadir}/%{name}/client
%{_datadir}/%{name}/doc
%{_bindir}/smoltSendProfile
%{_bindir}/smoltDeleteProfile
%config(noreplace) /%{_sysconfdir}/%{name}/config*
%ghost %config(noreplace) %{_sysconfdir}/cron.d/%{name}
%{_mandir}/man1/*
%ghost %{_sysconfdir}/sysconfig/hw-uuid

%if 0
%files server
%defattr(-,root,root,-)
%{_datadir}/%{name}/smoon
%endif

%files gui
%defattr(-,root,root,-)
%{_datadir}/applications/smolt.desktop
%{_datadir}/icons/hicolor/*x*/apps/smolt.png
%{_bindir}/smoltGui


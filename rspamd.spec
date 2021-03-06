%define rspamd_user      _rspamd
%define rspamd_group     %{rspamd_user}
%define rspamd_home      %{_localstatedir}/lib/rspamd
%define rspamd_logdir    %{_localstatedir}/log/rspamd
%define rspamd_confdir   %{_sysconfdir}/rspamd
%define rspamd_pluginsdir   %{_datadir}/rspamd
%define rspamd_rulesdir   %{_datadir}/rspamd/rules
%define rspamd_wwwdir   %{_datadir}/rspamd/www

Name:           rspamd
Version:        1.1.0
Release: 1
Summary:        Rapid spam filtering system
Group:          System Environment/Daemons

# BSD License (two clause)
# http://www.freebsd.org/copyright/freebsd-license.html
%if 0%{?suse_version}
License:        BSD-2-Clause
%else
License:        BSD2c
%endif
URL:            https://rspamd.com
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}
BuildRequires:  glib2-devel,openssl-devel,pcre-devel
BuildRequires:  cmake,file-devel,perl,libunwind-devel
%if 0%{?el6}
BuildRequires:  cmake3
%endif
%if 0%{?suse_version} || 0%{?el7} || 0%{?fedora} || 0%{?el8}
BuildRequires:  systemd
Requires(pre):  systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif
%if 0%{?suse_version}
BuildRequires:  sqlite3-devel
Requires(pre):  shadow
%else
BuildRequires:  sqlite-devel
Requires(pre):  shadow-utils
%endif
%if 0%{?fedora} || 0%{?suse_version} >= 1320
#BuildRequires:  luajit-devel
%else
#BuildRequires:  lua-devel
%endif
%if 0%{?el6}
Requires:       logrotate
Requires(post): chkconfig
Requires(preun): chkconfig, initscripts
Requires(postun): initscripts
Source1:        %{name}.init
Source2:        %{name}.logrotate
%else
Source2:        %{name}.logrotate.systemd
%endif

Source0:        https://rspamd.com/downloads/%{name}-%{version}.tar.xz
Source3:	80-rspamd.preset

%description
Rspamd is a rapid, modular and lightweight spam filter. It is designed to work
with big amount of mail and can be easily extended with own filters written in
lua.

%prep
%setup -q

%build
%if 0%{?el6}
source /opt/rh/devtoolset-6/enable
%endif
%if 0%{?el7}
source /opt/rh/devtoolset-8/enable
%endif
export ASAN_OPTIONS=detect_leaks=0
@@CMAKE@@ \
		-DCMAKE_C_OPT_FLAGS="%{optflags}" \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCONFDIR=%{_sysconfdir}/rspamd \
    -DMANDIR=%{_mandir} \
    -DDBDIR=%{_localstatedir}/lib/rspamd \
    -DRUNDIR=%{_localstatedir}/run/rspamd \
		-DENABLE_JEMALLOC=ON \
		-DJEMALLOC_ROOT_DIR=/jemalloc \
%if 0%{?el6}
    -DWANT_SYSTEMD_UNITS=OFF \
    -DDISABLE_PTHREAD_MUTEX=1 \
%else
    -DWANT_SYSTEMD_UNITS=ON \
    -DSYSTEMDDIR=%{_unitdir} \
%endif
%if 0%{?suse_version}
    -DCMAKE_SKIP_INSTALL_RPATH=ON \
%endif
		-DENABLE_LUAJIT=ON \
		-DLUA_ROOT=/luajit \
		-DENABLE_HIREDIS=ON \
    -DLOGDIR=%{_localstatedir}/log/rspamd \
    -DEXAMPLESDIR=%{_datadir}/examples/rspamd \
    -DSHAREDIR=%{_datadir}/rspamd \
    -DLIBDIR=%{_libdir}/rspamd/ \
    -DINCLUDEDIR=%{_includedir} \
    -DNO_SHARED=ON \
    -DDEBIAN_BUILD=1 \
    -DRSPAMD_GROUP=%{rspamd_group} \
    -DRSPAMD_USER=%{rspamd_user} \
		-DENABLE_LIBUNWIND=ON \
		@@EXTRA@@ 

%{__make} %{?jobs:-j%jobs}


%install
%{__make} install DESTDIR=%{buildroot} INSTALLDIRS=vendor
%{__install} -p -D -m 0644 %{SOURCE3} %{buildroot}%{_presetdir}/80-rspamd.preset

%if 0%{?el6}
%{__install} -p -D -m 0755 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}
%{__install} -d -p -m 0755 %{buildroot}%{_localstatedir}/run/rspamd
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -d -p -m 0755 %{buildroot}%{rspamd_logdir}
%else
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -d -p -m 0755 %{buildroot}%{rspamd_logdir}
%endif

%{__install} -d -p -m 0755 %{buildroot}%{rspamd_home}
%{__install} -p -D -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/local.d/
%{__install} -p -D -d -m 0755 %{buildroot}%{_sysconfdir}/%{name}/override.d/

%clean
rm -rf %{buildroot}

%pre
%{_sbindir}/groupadd -r %{rspamd_group} 2>/dev/null || :
%{_sbindir}/useradd -g %{rspamd_group} -c "Rspamd user" -s /bin/false -r -d %{rspamd_home} %{rspamd_user} 2>/dev/null || :

%if 0%{?suse_version}
%service_add_pre %{name}.service
%endif

%post
#to allow easy upgrade from 0.8.1
%{__chown} -R %{rspamd_user}:%{rspamd_group} %{rspamd_home}
%if 0%{?suse_version}
%service_add_post %{name}.service
%endif
%if 0%{?fedora} || 0%{?el7} || 0%{?el8}
#Macro is not used as we want to do this on upgrade
#%systemd_post %{name}.service
systemctl --no-reload preset %{name}.service >/dev/null 2>&1 || :
%endif
%if 0%{?el6}
/sbin/chkconfig --add %{name}
%endif
%{__chown} %{rspamd_user}:%{rspamd_group} %{rspamd_logdir}

%preun
%if 0%{?suse_version}
%service_del_preun %{name}.service
%endif
%if 0%{?fedora} || 0%{?el7} || 0%{?el8}
%systemd_preun %{name}.service
%endif
%if 0%{?el6}
if [ $1 = 0 ]; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi
%endif

%postun
%if 0%{?suse_version}
%service_del_postun %{name}.service
%endif
%if 0%{?fedora} || 0%{?el7} || 0%{?el8}
%systemd_postun_with_restart %{name}.service
%endif
%if 0%{?el6}
if [ $1 -ge 1 ]; then
    /sbin/service %{name} condrestart > /dev/null 2>&1 || :
fi

%endif

%files
%defattr(-,root,root,-)
%if 0%{?suse_version} || 0%{?fedora} || 0%{?el7} || 0%{?el8}
%{_unitdir}/%{name}.service
%{_presetdir}/80-rspamd.preset
%endif
%if 0%{?el6}
%{_initrddir}/%{name}
%dir %{_localstatedir}/run/rspamd
%endif
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%dir %{rspamd_logdir}
%{_mandir}/man8/%{name}.*
%{_mandir}/man1/rspamc.*
%{_mandir}/man1/rspamadm.*
%{_bindir}/rspamd
%{_bindir}/rspamd_stats
%{_bindir}/rspamc
%{_bindir}/rspamadm
%config(noreplace) %{rspamd_confdir}/modules.d/*
%config(noreplace) %{rspamd_confdir}/maps.d/*
%config(noreplace) %{rspamd_confdir}/scores.d/*
%config(noreplace) %{rspamd_confdir}/*.inc
%config(noreplace) %{rspamd_confdir}/*.conf
%attr(-, _rspamd, _rspamd) %dir %{rspamd_home}
%dir %{rspamd_rulesdir}/regexp
%dir %{rspamd_rulesdir}
%dir %{rspamd_confdir}
%dir %{rspamd_confdir}/modules.d
%dir %{rspamd_confdir}/maps.d
%dir %{rspamd_confdir}/scores.d
%dir %{rspamd_confdir}/local.d
%dir %{rspamd_confdir}/override.d
%dir %{rspamd_pluginsdir}
%dir %{rspamd_wwwdir}
%dir %{_libdir}/rspamd
%{rspamd_pluginsdir}/*
%{rspamd_rulesdir}/*
%{rspamd_wwwdir}/*
%{_libdir}/rspamd/*
%{_datadir}/rspamd/effective_tld_names.dat

%changelog
* Thu Sep 17 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 1.0.0-1
- Update to 1.0.0

* Fri May 29 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.9.9-1
- Update to 0.9.9

* Thu May 21 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.9.4-1
- Update to 0.9.4

* Tue May 19 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.9.3-1
- Update to 0.9.3

* Tue May 19 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.9.2-1
- Update to 0.9.2

* Sun May 17 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.9.1-1
- Update to 0.9.1

* Wed May 13 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.9.0-1
- Update to 0.9.0

* Fri Mar 13 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.8.3-1
- Update to 0.8.3

* Tue Mar 10 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.8.2-1
- Update to 0.8.2

* Fri Jan 23 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.8.1-1
- Update to 0.8.1

* Fri Jan 02 2015 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.8.0-1
- Update to 0.8.0

* Mon Nov 24 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.7.6-1
- Update to 0.7.6

* Mon Nov 17 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.7.5-1
- Update to 0.7.5

* Sat Nov 08 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.7.4-1
- Update to 0.7.4

* Mon Nov 03 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.7.3-1
- Update to 0.7.3

* Wed Oct 15 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.7.2-1
- Update to 0.7.2

* Tue Sep 30 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.7.1-1
- Update to 0.7.1

* Mon Sep 1 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.7.0-1
- Update to 0.7.0

* Fri Jan 10 2014 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.6.7-1
- Update to 0.6.7.

* Fri Dec 27 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.6.6-1
- Update to 0.6.6.

* Fri Dec 20 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.6.5-1
- Update to 0.6.5.

* Wed Dec 18 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.6.4-1
- Update to 0.6.4.

* Tue Dec 10 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.6.3-1
- Update to 0.6.3.

* Fri Dec 06 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.6.2-1
- Update to 0.6.2.

* Tue Nov 19 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.6.0-1
- Update to 0.6.0.

* Mon Jun 10 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.5.6-1
- Update to 0.5.6.

* Sat May 25 2013 Vsevolod Stakhov <vsevolod-at-highsecure.ru> 0.5.5-1
- Initial spec version.

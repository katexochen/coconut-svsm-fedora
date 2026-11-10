# Entry point of COPR's make_srpm method, run in the package's directory:
#   make -f .copr/Makefile srpm outdir=<dir> spec=<spec>

srpm:
	dnf -y install rpmdevtools rpm-build curl cargo tar gzip xz
	spectool -g "$(spec)"
	if [ -e vendor.sh ]; then bash vendor.sh; fi
	rpmbuild -bs --define "_sourcedir $$PWD" --define "_srcrpmdir $(outdir)" "$(spec)"

.PHONY: srpm

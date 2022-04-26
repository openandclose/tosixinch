
PHONIES = first help all prep git flake8 test tox scripts copylib libs html htmlmain htmllibs x xx xxx
DEV = tosixinch/tests/dev


first: help

.PHONY: $(PHONIES)

help:
	@echo Tosixinch make file:
	@echo
	@echo do \'all\', or \'git flake8 test tox html\'
	@echo and \'run\' \(_test_actualrun.py\)
	@echo
	@echo 'all'
	@echo '    prep'
	@echo '        git'
	@echo '            scripts'
	@echo '            copylib'
	@echo '                libs'
	@echo '        flake8'
	@echo '        test'
	@echo '        tox'
	@echo '    html'
	@echo '        htmlmain'
	@echo '        htmllibs'
	@echo 'x'
	@echo 'xx'
	@echo 'xxx'

all: prep html
	@echo 'Success All!'

prep: git flake8 test tox
	@echo 'Success!'

# vim -c ':r !flake8 .'
flake8:
	flake8 .

test:
	python -m doctest tosixinch/process/*.py
	TSI_PLATFORM=linux pytest -x
	TSI_PLATFORM=win32 pytest -x tosixinch/tests/_test_windows.py
	python tosixinch/tests/_test_actualrun.py -x

tox:
	PYTHONPATH= tox

git: scripts copylib
	git update-index --refresh
	git diff-index HEAD --

scripts:
	$(DEV)/argparse2rst.py
	$(DEV)/argparse2bash_tosixinch.py
	$(DEV)/fini2ini.py

copylib: libs
	-copylib.py configfetch.py
	-copylib.py zconfigparser.py

libs:
	$(MAKE) -C ../configfetch prep
	$(MAKE) -C ../zconfigparser prep

html: htmlmain htmllibs

htmlmain:
	$(MAKE) -C docs html

htmllibs:
	$(MAKE) -C ../configfetch html
	$(MAKE) -C ../zconfigparser html

x:
	python tosixinch/tests/_test_actualrun.py -x
xx:
	python tosixinch/tests/_test_actualrun.py -xx
xxx:
	python tosixinch/tests/_test_actualrun.py -xxx

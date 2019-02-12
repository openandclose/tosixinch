
PHONIES = first help all prep git flake8 test tox scripts copylib libs html htmlmain htmllibs run1 run2 run3
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
	@echo 'run1'
	@echo 'run2'
	@echo 'run3'

all: prep html
	@echo 'Success All!'

prep: git flake8 test tox
	@echo 'Success!'

# vim -c ':r !flake8 .'
flake8:
	flake8 .

test:
	python -m doctest tosixinch/process/*.py
	pytest -x
	python tosixinch/tests/_test_actualrun2.py -x

tox:
	tox

git: scripts copylib
	git update-index --refresh
	git diff-index HEAD --

scripts:
	$(DEV)/argparse2rst.py
	$(DEV)/complete-bash.py -X

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

run1:
	python tosixinch/tests/_test_actualrun2.py -x
run2:
	python tosixinch/tests/_test_actualrun2.py -xx
run3:
	python tosixinch/tests/_test_actualrun2.py -xxx

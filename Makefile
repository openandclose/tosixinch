
PHONIES = first help html2 prep test flake8 git scripts copylib libs html htmllibs
DEV = tosixinch/tests/dev


first: html2

.PHONY: $(PHONIES)


help:
	@echo tosixinch make file -- $(PHONIES)

html2: prep html htmllibs
	@echo 'Success All!'

prep: git test flake8
	@echo 'Success!'

test:
	python -m doctest tosixinch/process/*.py
	pytest -x
	tox

# vim -c ':r !flake8 .'
flake8:
	flake8 .

git: scripts copylib
	git update-index --refresh
	git diff-index HEAD --

scripts:
	$(DEV)/argparse2rst.py
	$(DEV)/complete-bash.py -X

copylib: libs
	-copylib.py

libs:
	$(MAKE) -C ../configfetch prep
	$(MAKE) -C ../zconfigparser prep

html:
	$(MAKE) -C docs html

htmllibs:
	$(MAKE) -C ../configfetch html
	$(MAKE) -C ../zconfigparser html

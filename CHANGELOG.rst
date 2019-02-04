
Changelog
=========

v0.0.8
------

Added option 'force_download'.
Fixed around 'plus' functions (with configfetch updates).
[test] Added new (system) test (_test_actualrun2.py).
Improved Document.
Added Python3.7.

Open Close (43):
      Make Add more handy help message
      Document Add custom 'objects'
      Document Add css for 'Note:' parts
      Document Add css for custom 'script' opject
      Document Fix undesirable sphinx build warinings
      Document broad rewrite (documents wide)
      Document Fix indents
      Document Cut building api2.rst
      Document rewrite continued
      [copy] (templite.py)
      [small edits] (README.rst)
      [copy] (.gitignore)
      Add a way to use main() externally (for test etc.)
      Fix wrong no_comp argument selection
      Add better _need_args() check using .nargs
      Add more useful (eager) bash completion
      Make update bash completion file
      Change url (pythoncode) in tests/urls.txt
      Fix no userdir and no userprocess dir cases
      (small edits)
      Fix globals in test into class namespace (pytest)
      Add option 'force_download'
      Fix message when creating pdf
      Fix typo in the filename
      Add _test_actualrun2.py
      Make Add _test_actualrun2()
      Fix some windows path treatment (only easy ones)
      Fix preprocess func (adding xpath)
      Fix link.py doc and config
      Fix main() leaking return value to the shell
      Fix many misspellings in docs
      Document rewrite around 'code' part
      Fix code css (with 'toc', h3 becomes h4)
      [small edits] (main.py)
      Fix xml declaration regex
      Fix class attribute regex
      Fix 'unused' style options.
      Fix 'plus' commandline descriptions
      Fix 'plus' option names
      [copy] (configfetch.py)
      Fix wrong function
      Refactor Fix Flake8 errors
      Make Add Python3.7


v0.0.7
------

Fixes and small improvements.
Update configfetch.py library belatedly.

Open Close (29):
* Make Fix CHANGELOG format (missing line breaks)
* [copy] (.gitignore)
* Make Fix not included CHANGLOG file (pypi)
* Make remove vim modelines (set spell etc)
* Make move CHANGELOG to CHANGELOG.rst
* [small edits] (util.py)
* [small edits] (util.py)
* Fix store_const default
* Make fix pypi preparations
* Fix update default user-agent
* Add downloading url in debug messages
* Add 'add_style' builtin process
* Add 'change_tagname' builtin process
* Add _xpath() function to site.process parsing
* Add 'add_title_force' builtin process
* Fix regex mistakes
* Fix very wide list indentations
* Fix remove 'delete_duplicate_br'
* Add simple session cookie functionality
* Fix heading font size scaling
* Add default argument '' to convert_permalink_sign()
* Fix func convert_permalink_sign() to default
* [copy] (configfetch.py)
* Fix copylib.py options in Makefile
* Refactor fix flake8 complaints
* Refactor fix flake8 (W503 W504)
* [copy] (.flake8)
* [copy] (.flake8)
* [copy] (configfetch.py)


v0.0.6
------

Several bug or inconvenience fixes.

Open Close (18):

* Fix HTMLFILE regex
* Fix site match for gnu.org (sample)
* Fix doc, more practical viewcmd help example
* Fix add_binaries, in single url case
* Add pdf filename to printout in '-3'
* Fix css image height (add max-width) (sample)
* Fix rendering of aria-hidden element (sample)
* Fix images downloading that already exist
* Fix logging format errors (missing parentheses)
* Fix image size check when no file (HTTP 404)
* Add optional xml declaration to HTMLFILE regexp
* Add preprocess option override in siteconf
* Add --link option
* Make testing targets more sequential
* Add force option to process.gen.add_title
* Fix wrong TOC in github wiki (sample)
* Fix not used args.delete
* Fix make_directories when os.path.dirname is ''


v0.0.5
------

First commit

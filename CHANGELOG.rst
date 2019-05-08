
Changelog
=========

v0.1.0
-------

Fix:

* sample.t.css exclusion in installation

Dev:

* Change version scheme.

  I've been using only the third digit for version, since I thought v0.1.0 was too pretentious.
  But I should express the difference between some improvements and stupid bug fixes.


v0.0.11
-------

API Change:

* tocfile (previously toc-ufile) is now always created in current directory.
  Previously it was created in the same directory as the ufile.

Fix:

* Many import errors (no lxml, no readability cases etc.).
* Many import errors (installation related, importing (nonexistent) tests package etc.).
* readthedocs.org build error


v0.0.10
-------

API Change:

* Rename '--sample-pdf' to '--sample-urls',
  and now it also requires action options additionally ('-123').

Fix:

* blank API documents (lack of a readthedocs config)
* Accept very long html start tag (now support hatenablog.com).
* Broken '--sample-pdf' and '--appcheck' (no urls case etc.).

Dev:

* Continuing the big refactoring (now util.py is gone).
* x options of _test_actualrun2.py are again '-x', '-xx', and '-xxx'.


v0.0.9
------

API Change:

* Rename 'tsi-big' class attribute for large images, to 'tsi-wide'.
* Remove file listing feature when urls consist of directories.

Addition:

* Update site.sample.ini.

  * Fix broken www.reddit.com (now use 'old.reddit.com').
  * Add github '/pull' subdirectory.
  * Improve wikipedia a bit.

* Add option '--pdfname'
* Add option '--sample-pdf'
* Add option '--convpath'

Fix:

* Fix detection whether an image is wide or tall.
* Fix current directory check in making directories
* Fix multiple extensions case in filtering binary-like extension urls.
* Fix url escaping for '%' itself (never escape it).

Dev:

* Refactor half of util.py (Moved to 'location.py')


v0.0.8
------

Addition:

* Add option '--force-download'.
* Add Python3.7.
* Improve Document.

Fix:

* Fix around 'plus' functions (with configfetch updates).

Dev:

* Add new test (_test_actualrun2.py).


v0.0.7
------

* Fixes and small improvements.
* Update configfetch.py library belatedly.


v0.0.6
------

* Several bug or inconvenience fixes.


v0.0.5
------

* First commit

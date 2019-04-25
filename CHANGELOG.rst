
Changelog
=========

v0.0.9
------

API Change:

* Rename 'tsi-big' class attribute for large images, to 'tsi-wide'.
* Remove file listing feature when urls consist of directories.

Feature:

* Update site.sample.ini.

  * Fix broken www.reddit.com (now use 'old.reddit.com').
  * Add github '/pull' subdirectory.
  * Improve wikipedia a bit.

* Add option '--pdfname'
* Add option '--sample-pdf'
* Add option '--convpath'

Fixes:

* Fix detection whether an image is wide or tall.
* Fix current directory check in making directories
* Fix multiple extensions case in filtering binary-like extension urls.
* Fix url escaping for '%' itself (never escape it).

Dev:

* Refactor half of util.py (Moved to 'location.py')


v0.0.8
------

Feature:

* Add option '--force-download'.
* Add Python3.7.
* Improve Document.

Fixes:

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

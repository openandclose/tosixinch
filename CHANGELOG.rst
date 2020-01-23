
Changelog
=========

Important changes (that users especially need to know) are marked by '**[!]**.'


**Unreleased:**
---------------

**Change:**

* **[!]** Cut add_extractors and move man hook to pre_percmd2

  Change you config (If you are using) from:

      add_extractors=   _man

  To:

      pre_percmd2=      _man

**Add:**

* Add GNU global to site.sample.ini

**Fix:**

* Fix auto_css (when toc, stylesheets were lost)

* Fix clipped large tall images (using actual length and percent)



v0.2.0 (2019-11-10)
-------------------

**Change:**

* Change one of sample urls. Local templite.py to remote textwrap.py.

* Stop adding suffix to query url.

  Previously url 'bb?cc' was changed to Downloaded_File 'bb?cc/index--tosixinch' or 'bb?cc_index--tosixinch'.
  Now just to 'bb?cc'.

* Stop adding './' prefix unconditionally for relative references.
  Now only when necessary to comply to url spec (colon-in-first-path case).

* **[!]** Change 'userprocess' to just 'process'.
  So Users have to rename this 'userprocess' directory if used.

* **[!]** Change (rather Fix) default encodings, to only utf-8 and cp1252.

* **[!]** Change 'preprocess' option name to 'defaultprocess'.
  Again, users have to rename this option if used.

* pdfname (when the script creates) is made more descriptive.

* Add maximum argument to delete_duplicate_br (process/gen.py)

**Add:**

* Add auto_css feature (see doc: overview.html#dword-auto_css_directory).

* Add trimdirs option.

  Remove flaky automatic path shortening (minsep), add this manual but reliable option.

* Add printout option.

  Print out filenames the scripts' actions would create.

* Add encoding_errors option (for codec Error Handler).

* Add urlreplace feature (see doc: topics.html#urlreplace).

* Add multi commands feature for hookcmds.

* Add add_extractors option (now only for man).

* Add per-cmd hooks (pre_percmds and post_percmds).

* Add file url support for input.

* Add font_scale option.

* Add quiet option.

* Add version option.

* Expose full-image option to commandline.

* Add --null option to script/open_viewer.py.

* Add browsercmd option.

* Add toc_depth option to wkhtmltopdf converter.

* Add ftype option

**Remove:**

* Remove 'support' for ebook-convert. Now converters are only one of the three
  (prince, weasyprint or wkhtmltopdf).

**Fix:**

* Fix relative reference when base url is local. (_Component.__init__)

* Fix blank API documents in readthedocs site (The previous fix was wrong).

* Fix ftfy calling procedure (it should be *after* successful decoding).

* Fix (user) script directory resolution in runcmd.

* Fix image downloading error when input is a file url
  (The file url handling has changed: immediately change it to filepath
  in url phase).

**Dev:**

* Develop abstract path functions to try to absorb windows path specifics,
  only to revert them back in the end.
  The period is especially unsuitable for forking or otherwise using the code::

    From:
    2019-05-21 401e27e408ba19627a9b1d452e009521cbdb09a8
    Until:
    2019-05-30 f1055f97dc6d8088906e43c6f150739c8d560174

v0.1.0 (2019-05-09)
-------------------

**Fix:**

* sample.t.css exclusion in installation

**Dev:**

* Change version scheme.

  I've been using only the third digit for version, since I thought v0.1.0 was too pretentious.
  But I should express the difference between some improvements and stupid bug fixes.


v0.0.11 (2019-05-09)
--------------------

**Change:**

* tocfile (previously toc-ufile) is now always created in current directory.
  Previously it was created in the same directory as the ufile.

**Fix:**

* Many import errors (no lxml, no readability cases etc.).
* Many import errors (installation related, importing (nonexistent) tests package etc.).
* readthedocs.org build error


v0.0.10 (2019-05-04)
--------------------

**Change:**

* Rename '--sample-pdf' to '--sample-urls',
  and now it also requires action options additionally ('-123').

**Fix:**

* blank API documents (lack of a readthedocs config)
* Accept very long html start tag (now support hatenablog.com).
* Broken '--sample-pdf' and '--appcheck' (no urls case etc.).

**Dev:**

* Continuing the big refactoring (now util.py is gone).
* x options of _test_actualrun2.py are again '-x', '-xx', and '-xxx'.


v0.0.9 (2019-04-26)
-------------------

**Change:**

* Rename 'tsi-big' class attribute for large images, to 'tsi-wide'.
* Remove file listing feature when urls consist of directories.

**Add:**

* Update site.sample.ini.

  * Fix broken www.reddit.com (now use 'old.reddit.com').
  * Add github '/pull' subdirectory.
  * Improve wikipedia a bit.

* Add option '--pdfname'
* Add option '--sample-pdf'
* Add option '--cnvpath'

**Fix:**

* Fix detection whether an image is wide or tall.
* Fix current directory check in making directories
* Fix multiple extensions case in filtering binary-like extension urls.
* Fix url escaping for '%' itself (never escape it).

**Dev:**

* Refactor half of util.py (Moved to 'location.py')


v0.0.8 (2019-02-05)
-------------------

**Add:**

* Add option '--force-download'.
* Add Python3.7.
* Improve Document.

**Fix:**

* Fix around 'plus' functions (with configfetch updates).

**Dev:**

* Add new test (_test_actualrun2.py).


v0.0.7 (2018-11-24)
-------------------

* Fixes and small improvements.
* Update configfetch.py library belatedly.


v0.0.6 (2018-04-25)
-------------------

* Several bug or inconvenience fixes.


v0.0.5 (2017-12-08)
-------------------

* First commit

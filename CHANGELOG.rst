
Changelog
=========

Important changes (that especially affect users) are marked by '**!!**'.


Unreleased
----------

**Change:**

* **!!** Change name syntax of dfile, Using suffix '.f'

  Given URL::

    https://en.wikipedia.org/wiki/XPath

  Old dfile::

    _htmls/en.wikipedia.org/wiki/XPath/_

  Now::

    _htmls/en.wikipedia.org/wiki/XPath

  NOTE: you can no longer use old html cache in '_htmls' folder,
  since names are different.

  Especially, there should be many now-redundant directory,
  which causes download Errors.

  E.g. If there is a directory 'XPath', we can not write a file 'XPath'.

* **!!** Change name syntax of efile using suffix '.orig'

  Reuse the same name as dfile,
  but make sure to rename dfile with the suffix.

  Given URL::

    https://en.wikipedia.org/wiki/XPath

  Old::

    _htmls/en.wikipedia.org/wiki/XPath          (dfile)
    _htmls/en.wikipedia.org/wiki/XPath~.html    (efile)

  Now::

    _htmls/en.wikipedia.org/wiki/XPath.orig     (dfile)
    _htmls/en.wikipedia.org/wiki/XPath          (efile)

* **!!** Change default resource filename 'urls.txt' -> 'rsrcs.txt'

**Add:**

* Use temporary file when downloading (with suffix '.part')


v0.8.0 (2022-06-13)
-------------------

Cut dependencies I haven't used for years myself.

**Change:**

* **!!** Cut lib: chardet

* **!!** Cut lib: Qt (webkit and webengine options)

* **!!** Cut lib: readability

* **!!** Cut lib: wkhtmltopdf

* **!!** Cut support: Windows


v0.7.0 (2022-06-12)
-------------------

Incremental Improvements

**Change:**

* Change @page and <body> margin slightly (for weasyprint)

* Add --inspect action, cutting --link and --news

* Add --headless option, cutting --javascript

* Add '//article' to guess option defaults

* Change '_add_index' from URL to Map class

  Very slightly change the handling of '/' and '?' in dfile name

**Add:**

* Add github discussions to sample

* Add loose heuristic for too big images (for inside <table>)

* Add more exclusion of secondary boxes (sample wikipedia)

* Update and Change slugify, add more word separation ('-')

* Add minus number feature to --trimdirs option

* Add --timeout option

* Add --interval option

* Add KeepExtract (no-selection extractor, '--keep-html')

* Add IDTable (fragment link re-resolution when merging htmls)

* Add expose loc_index and loc_appendix to commandline

* Add reading tosixinch.ini and site.ini from current dir

* Add download_dir option

* Add overwrite_html option

* Add current directory search for css and css2 options

**Fix:**

* Fix Add charset for BLANK_HTML (for weasyprint)

* Fix toc title (able to use unicode)

* Fix link when baseurl (<base> tag) is provided

* Fix merge_htmls (no css references for weasyprint)


v0.6.0 (2021-10-29)
-------------------

I have refrained from uploading local changes,
waiting for a time when I could look into it closely.
But the time is not coming for a long time,
let's make it updated now.

**Change:**

* When the name of dfile is too long
  (if it has a path segment more than 255 characters),
  the filename is hashed,
  and the filename now takes '_htmls/_hash/<sha1-hexdigit>' form.

* Change browser_engine option default: webkit -> selenium-firefox

* Skip cleaning possible MathJax tag attributes

**Add:**

* Add 'html5prescan' encoding option

* Add elements_to_keep_attrs option

* Add selenium downloading (browser_engine option)

* Add dprocess option

**Fix:**

* Fix ignore any errors in component download

* Fix --browser option error (url was not percent escaped)


v0.5.0 (2020-08-16)
-------------------

Most changes are just internal refactorings.

**Change:**

* Add latin_1 to default encoding option

  From::

      utf-8, cp1252

  To::

      utf-8, cp1252, latin_1

  Which means no encoding errors from input,
  and in general it should be preferable.

* Rename method ``_get_relpath`` to ``_get_relative_url``
  in ``tosixinch.pcode._pygments.PygmentsCode``.

* Change application config data files to normal INI format

  (``data/tosixinch.ini`` and ``data/site.ini``)

  Previously the program exposed foreign FINI format files
  which is specific to configfetch library.

* Cut Python 3.5

**Add:**

* Add urlno.py and urlmap.py (internal)

  ('urlno' means url normalization)

* Add lxml_html.py (internal)

* Add action.py (internal)

**Fix:**

* Fix and change user package import

  Previously if user's Python environment includes some library
  which also has, say, 'script' package,
  the program aborted.


v0.4.0 (2020-06-02)
-------------------

In this version,
I concentrated many gratuitous API changes I've been thinking,
while trying not to add positive features.

So be careful to upgrade.

**Change:**

* Cut head data inclusion

  Previously, the program kept the original <head> content in the extracted file.
  Now it just includes a minimal <head> content.
  (Shouldn't affect the end user usage).

* **!!** Change default intermediary filenames to '-' and '~'

  Previously::

      https://en.wikipedia.org/wiki/Xpath
      _htmls/en.wikipedia.org/wiki/Xpath/index--tosixinch
      _htmls/en.wikipedia.org/wiki/Xpath/index--tosixinch--extracted.html

  Now::

      https://en.wikipedia.org/wiki/Xpath
      _htmls/en.wikipedia.org/wiki/Xpath/_
      _htmls/en.wikipedia.org/wiki/Xpath/_~.html

  To use old (or other) names, edit new config options.::

      loc_index=     index--tosixinch
      loc_appendix=  --extracted

* Cut 'use_sample' option

* Cut 'use_urlreplace' option

* Cut '--sample-urls' option

* Move css from commandline to html link

  Previously they are just passed to converter's commandline arguments.

  Now they are referenced in each html files as external css.

  So you can now specify css files for each site configuration like this::

      [wikipedia]
      ...
      css=  sample, my_wikipedia.css

  (Note: Unlike ``auto_css``,
  All css files must be specified explicitly. Not additions to the default.)

* **!!** Cut auto_css

  It is now redundant. Just use 'css' option instead (see the above change).

* **!!** Cut auto glob feature (for 'match' option)

  Sometimes we need exact match of the end. (like: '\*.html')

  But since '\*' was automatically added to the end of the string,
  is was impossible.

  Now you have to add '\*' explicitly.

  And you have to edit the past config files extensively,
  like I did for 'site.sample.ini'.
  Sorry.

  From::

      [wikipedia]
      ...
      match=      https://*.wikipedia.org/wiki/

  To::

      match=      https://*.wikipedia.org/wiki/*

* Update configfetch (v0.1.0)

  It is incompatible with the previous configfetch versions.
  Codes and config files will be changed considerably.
  It shouldn't affect tosixinch behavior.

* **!!** Rename tosixinch-complete.bash

  From:

      tosixinch/script/tosixinch-complete.bash

  To:

      tosixinch/data/_tosixinch.bash

  If you are sourcing this bash completion file in e.g. .bashrc,
  you have to edit.

* **!!** Rename pre_percmds and post_percmds to pre_each_cmds and post_each_cmds. ::

      pre_percmd1   ->  pre_each_cmd1
      post_percmd1  ->  post_each_cmd1
      pre_percmd2   ->  pre_each_cmd2
      post_percmd2  ->  post_each_cmd2

  You have to edit user config files if you are using them.

* Rename 'qt' option to 'browser_engine'.

* Move 'javascript' option from (general) site.ini to tosixinch.ini.

  You can now specify 'javascript' on commandline, tosixinch.ini, or some site sections.

* **!!** Cut util.py, gen.py and site.py and create sample.py (tosixinch.process directory)

  Combined three sample files into one.

  You have to edit user config files if you are using them. e.g.::

    gen.youtube_video_to_thumbnail  -> sample.youtube_video_to_thumbnail

  or just (See below: 'Add no-dot function name..')::

    gen.youtube_video_to_thumbnail  -> youtube_video_to_thumbnail

* **!!** Change syntax: from comma to line (defaultprocess and process options)

  From::

    process=    aaa, bbb, ccc

  To::

    process=    aaa
                bbb
                ccc

  You have to edit user config files if you are using them.

* **!!** Rename many process functions (process/sample.py) ::

      check_parents_tag       -> check_parent_tag
      transform_xpath         -> build_class_xpath
      add_title               -> add_h1
      add_title_force         -> add_h1_force
      make_ahref_visible      -> show_href
      decrease_heading        -> lower_heading
      decrease_heading_order  -> lower_heading_from_order
      split_h1_string         -> split_h1
      replace_h1_string       -> replace_h1
      change_tagname          -> replace_tags
      add_noscript_img        -> add_noscript_image

  You have to edit user config files if you are using them.

* **!!** Rename script/open_viewer.py

  From:
  
      open_viewer.py
  
  To:
  
      _view.py

  You have to edit user config files if you are using them.

**Add:**

* Add Python3.8

* Add css2 option (and fix misplaced css option)

* Add no-dot function name in process option

  Previously the option only accepted one-dot name form
  (``<module name>.<function name>``).

  Now this form is optional.
  The program searches all modules for the function name.


v0.3.0 (2020-02-24)
-------------------

Add very detailed source code highlighter (_pcode).
Use it in pre-extraction hook ('pre_percmd2').

**Change:**

* **!!** Cut add_extractors and move man hook to pre_percmd2

  Change you config (If you are using) from:

      add_extractors=   _man

  To:

      pre_percmd2=      _man

**Add:**

* Add GNU global to site.sample.ini

* Add add_noscript_img (process/gen)

* Add script _pcode.py (Pygments code extraction)

**Fix:**

* Fix auto_css (when toc, stylesheets were lost)

* Fix clipped large tall images (using actual length and percent)

* Fix use monospace font for figcaption

* Fix github sample ini (plain text README case)


v0.2.0 (2019-11-10)
-------------------

**Change:**

* Change one of sample rsrcs. Local templite.py to remote textwrap.py.

* Stop adding suffix to query url.

  Previously url 'bb?cc' was changed to dfile 'bb?cc/index--tosixinch' or 'bb?cc_index--tosixinch'.
  Now just to 'bb?cc'.

* Stop adding './' prefix unconditionally for relative references.
  Now only when necessary to comply to url spec (colon-in-first-path case).

* **!!** Change 'userprocess' to just 'process'.
  So Users have to rename this 'userprocess' directory if used.

* **!!** Change (rather Fix) default encodings, to only utf-8 and cp1252.

* **!!** Change 'preprocess' option name to 'defaultprocess'.
  Again, users have to rename this option if used.

* pdfname (when the program creates) is made more descriptive.

* Add maximum argument to delete_duplicate_br (process/gen.py)

**Add:**

* Add auto_css feature (see doc: overview.html#dword-auto_css_directory).

* Add trimdirs option.

  Remove flaky automatic path shortening (minsep), add this manual but reliable option.

* Add printout option.

  Print out filenames the program's actions would create.

* Add encoding_errors option (for codec Error Handler).

* Add urlreplace feature (see doc: topics.html#replace).

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
* Broken '--sample-pdf' and '--appcheck' (no rsrcs case etc.).

**Dev:**

* Continuing the big refactoring (now util.py is gone).
* x options of _test_actualrun2.py are again '-x', '-xx', and '-xxx'.


v0.0.9 (2019-04-26)
-------------------

**Change:**

* Rename 'tsi-big' class attribute for large images, to 'tsi-wide'.
* Remove file listing feature when rsrcs consist of directories.

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
* Fix multiple extensions case in filtering binary-like extension rsrcs.
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

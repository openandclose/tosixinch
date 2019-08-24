
Introduction
============

| Somehow, I don't like reading on the computer screen.
| In the olden days, I may have printed them in frustration.
| These days I can convert them to ebooks, of course,
| but it should be as easy as possible.

The script is for this purpose.
It is a helper to convert relatively simple html, text or source code,
to relatively terrible pdf file
as passable as temporarily printed out paper in a hurry.

---

The work is serialized in three, very uncontroversial, stages:

1. Download html
2. Extract and format the contents to suit for small paged media
3. Convert to pdf

Admittedly, there are many applications doing similar things.
But I find, they are on the one hand too generic,
just providing functionalities for users to go a long way to build up with,
or, on the other hand too specific,
making it hard to promptly adjust or intervene.

The legend of this script says '*Browser to e-reader in a few minutes*'.
Here, I mean the 'in a few minutes' part seriously.
Too many programs are either 'in a few hours' or 'in a few seconds' kind.

---

Some points to consider:

* Many related applications seem to concentrate on major new sites,
  parsing RSS or home pages for the target articles,
  sometimes using clever content extraction heuristics on top.
  This script may not be suitable for these sites.
  It is rather for more static reading contents,
  like personal blogs or technical documents.

* The objective is *not* producing a great pdf,
  adjusting closely to specific intricacies of each site format.
  Rather, avoiding as far as possible the trouble of having to
  analyze arbitrary document markup structure,
  which you couldn't care less about, is the point.

* Users select articles (urls) themselves.
  And users write configurations for each site themselves.
  So it always requires some work, hopefully done in a few minutes.

* Extraction is the most important part of the script.
  But it is done by very simple and predetermined method.

  1. Parse html text as DOM elements tree (by ``lxml``).
  2. ``select`` the elements you want, discarding others.
  3. ``exclude`` undesirable sub-elements from the selected elements.
  4. ``process`` the resultant tree
     (apply arbitrary functions against the tree
     in a very limited way).
  5. ``clean`` the resultant tree.
     (strip some tags, attributes, javascript and css).

  So the script is only suitable for htmls
  as complex as this simple method can take.
  For example, perhaps the script can't handle
  academic papers in multiple columns with many figures.


Installation
------------

It is an ordinary pure python package, so you should be able to do::

    $ pip install tosixinch

Or rather::

    $ pip install --user tosixinch

The command will only install ``tosixinch`` package.
(You will need other external libraries, but it is not done automatically.)

**Python 3.5 and above** are supported.

.. note::

    * The author is an amateur holiday programmer.

    * It is under construction, to get to the state of the alpha.

    * Mac and Windows environments are considered,
      but it is likely to be more imperfect.

    * In some places in code,
      Unicode encoding in system and files is presupposed.


Requirements
------------

Technically it has no library requirements,
because each action in this script is independent, so optional.

But in general, if you are in the mood to try this script,
installing ``lxml`` and at least one of pdf converters is recommended.
(That way you can do all ``-1``, ``-2`` and ``-3`` below).

* `lxml <http://lxml.de>`__ is used for html DOM manipulations.

Converters are:

* `prince (or princexml) <https://www.princexml.com>`__
* `weasyprint <http://weasyprint.org>`__
* `wkhtmltopdf <https://wkhtmltopdf.org>`__

``prince`` recommended, it is one of the oldest and the most famous.
(It is free of charge for non-commercial use).
Personally, it is rare that I use other converters than ``prince``,
and (a semblance of) software testing tends to be only concerned with ``prince``.

``weasyprint`` has some limitations, notably it is unbearably slow
(For our usage, it is not rare
that a pdf consists of hundreds or thousands of pages).
But it is written in python, by great authors.
I want to keep it rather as a reference.

These two treat ordinary css files as the main (or only) API for style options.
And in general much care is taken to comply to the CSS standard.

``wkhtmltopdf`` uses some old WebKit browser engine,
so what it does is dependent on it, and in general harder to fathom.
But precisely because it uses veritable browser engine,
some things are done better.

.. note::

    The wkhtmltopdf official site provides compiled binaries
    built with *patched* Qt.
    Linux distributions sometimes install non-patched version of wkhtmltopdf,
    which is limited in functionalities.
    For example, it can not receive multiple htmls,
    and it can not build pdf bookmarks.

    The patched one is generally preferred.

Anyway, the script just helps to build conversion commandline.
It only adds some useful shortcuts.
Abstraction, consistency or support for multiple converters
are not intended.


Samples
-------

The script includes a sample ini file (``site.sample.ini``),
and reads it into configuration if not disabled or overwritten.

.. code-block:: none

    https://*.wikipedia.org/wiki/* (only tested with 'en.wikipedia.org')
    https://www.gnu.org/software/*
    https://docs.python.org/*
    https://www.python.org/dev/peps/*
    https://bugs.python.org/issue*
    https://news.ycombinator.com/item*
    https://old.reddit.com/r/*
    https://stackoverflow.com/questions/*
    http://www.stackprinter.com/*
    https://github.com/* (for https://github.com/*/README*)
    https://github.com/*/issues/*
    https://github.com/*/pull/*
    https://github.com/*/wiki/*
    https://gist.github.com/*

For urls that match one of them,
you can test the script without preparing the configuration.

An example::

    $ tosixinch -i https://en.wikipedia.org/wiki/Xpath -123

(For basic commandline options, see `next section <#usage>`__.)

Or if even this is a trouble::

    $ tosixinch --sample-urls -123

This command creates 'sample.pdf'
from some arbitrary urls in most of the domains above.

.. note::

    You need to set the converter if not default (prince).

    And if you installed the converter in unusual places (not in PATH),
    you need to set the fullpath.

    .. code-block:: none

            $ [...] --wkhtmltopdf --cnvpath /home/john/build/bin/wkhtmltopdf

    (See `Programs <commandline.html#programs>`__
    and `cnvpath <commandline.html#cmdoption-cnvpath>`__.)


.. note::

    These commands create temporary files other than a pdf file
    in current directory.

    * '_html' directory, with many html files in it.
    * 'sample.css'

    You can delete them as you like.


Usage
-----

The main comandline options of the script are:

    * ``-i`` ``INPUT``, ``--input`` ``INPUT`` (input url or file path)
    * ``-f`` ``FILE``, ``--file`` ``FILE`` (file to read inputs)
    * ``-1``, ``--download``
    * ``-2``, ``--extract``
    * ``-3``, ``--convert``

Usually you check the site by selecting an example url (``-i``),
and see how it goes.
If it is good enough,
you build an url list, put it in a file, and run ``-f``.

``-1`` downloads htmls to ``_htmls`` sub directory in current directory.

``-2`` extracts these local ``Downloaded_Files``, and creates new files.

``-3`` converts these local ``Extracted_Files``, and creates a pdf file.

Note ``-1``, ``-2`` and ``-3`` take the same url as input.
You don't need to change that part of the commandline
(see `Example <#example>`__ below).

Site specific options are either on commandline or in a configuration file.
You use frequently the latter,
because options are sometimes long and include special characters.

For each site, users will create a new section,
adding a few lines of options.


Example
^^^^^^^

You are browsing some website, and you want to bundle some articles in a
pdf file.

You move to some working directory. ::

    $ cd ~/Downloads/tosixinch    # an example

You test for one url. First, you have to download. ::

    $ tosixinch -i https://somesite.com/article/aaa.html -1

You look into the site structure, using e.g. the browser's development tools,
and write extraction settings for the site. ::

    # in '~/.config/tosixinch/site.ini'
    [somesite]
    match=    https://somesite.com/article/*
    selecet=  //div[@id="main"]
    exclude=  //div[@id="sidemenu"]
              //div[@id="comment"]

.. note ::

    The values of ``select`` and ``exclude`` are
    `Xpaths <https://en.wikipedia.org/wiki/Xpath>`__.
    In software, html tag structure is made into objects tree
    (``DOM`` or ``Elements``).
    One way to get parts of them is ``Xpath``.

    The value above means e.g.
    get from anywhere (``'//'``),
    ``div`` tags whose ``id`` attributes are ``'main'``
    (including every sub-elements inside them).

    Multiple lines are interpreted
    as connected with ``'|'`` (equivalent to *'or'*).

And applies the site config to the local html,
creating a new (extracted) html. ::

    $ tosixinch -i https://somesite.com/article/aaa.html -2

Optionally, you check the extracted html in the browser. ::

    $ tosixinch -i https://somesite.com/article/aaa.html -b

* ``'-b'`` or ``'--browser'`` opens ``Extracted_File``.

You try ``-2`` several times if necessary,
editing and changing the site configuration
(It overwrites the same ``Extracted_File``).

And ::

    $ tosixinch -i https://somesite.com/article/aaa.html -3

* It generates ``./aaa.pdf``.

Next, you build an url list, by some means. ::

    # in './urls.txt'
    https://somesite.com/article/aaa.html
    https://somesite.com/article/bbb.html
    https://somesite.com/article/zzz.html

And ::

    $ tosixinch -123

* If inputs are not specified (no ``-i`` and no ``-f``),
  it defaults to ``'urls.txt'`` in current directory.

* It generates ``./somesite.pdf``, with three htmls as each chapter.

Additionally, if you configured so::

    $ tosixinch -4

* it opens the pdf with a pdf viewer.


Example 2
^^^^^^^^^

Now, more concrete example.

You want to create a pdf file from some of the Python PEP pages.

* PEP 8 -- Style Guide for Python Code
* PEP 20 -- The Zen of Python
* PEP 257 -- Docstring Conventions

(The configuration is actually included in the `Samples <#samples>`__ above.
But let's suppose it is not).

You have to prepare the configuration,
like the previous example.::

    # in urls.txt
    https://www.python.org/dev/peps/pep-0008
    https://www.python.org/dev/peps/pep-0020
    https://www.python.org/dev/peps/pep-0257

    # in ~/.config/tosixinch/site.ini
    [python-pep]
    match=      https://www.python.org/dev/peps/*
    select=     //article[@class="text"]

It seems there is nothing to remove.
You can omit ``exclude`` option.

But looking at the pdf, you find a problem.
The pdf bookmarks (Table of Contents) are not good.
The site invariably uses ``<h1>`` tags
for all (sub) sections and (sub) headings!
So the document structure doesn't correspond to
the heading tags (h1, h2, h3...) structure,
which, usually, pdf converters use to make pdf bookmarks.

To solve this,
you need to transform the htmls some way or other.
The script only provides a relatively simple
`process <options.html#confopt-process>`__ option,
so you have to manage with that.

Fortunately, there are no ``<h2>``, ``<h3>``... ``<h6>``
in the content part of the pages.
So, let's change other ``<h1>`` tags to ``<h2>``,
keeping ``<h1>`` only for the main title heading.

You create a file
(in `process directory <overview.html#dword-process_directory>`__),
and write a function in it::

    # in ~/.config/tosixinch/process/myprocess.py
    def decrease_heading(doc, to_keep_path):
        """change h1 to h2, except one (to_keep_path argument)"""
        for el in doc.xpath('//h1'):
            if el.xpath(to_keep_path):
                continue
            el.tag = 'h2'

* first ``doc`` argument is required.
  The script provides this
  (html elements object after ``select`` and ``exclude``),
  and you can manipulate it as you like.
  The script uses the changed ``doc`` subsequently.

To use this, you add ``process`` option to the site configuration. ::

    [python-pep]
    ...
    process=    myprocess.decrease_heading?@class="page-title"

The meaning is::

    myprocess           - module name
                          (filename without '.py')
    .                   - namespace separator
    decrease_heading    - function name
    ?                   - argument separator
    @class="page-title" - argument

Now you can do::

    $ tosixinch -123


Other Features
--------------

* It can also convert text and source code to pdf (experimental).
  Although it may not be common to read code in e-readers,
  I find it rather useful.
  Of course e-reader's functionalities are limited,
  you cannot do many things.

* The script has very basic Qt web rendering functions (``webkit`` or ``webengine``).
  So if you are lucky, by installing
  `pyqt5 <https://pypi.python.org/pypi/PyQt5>`__
  (and `Qt5 <https://www.qt.io>`__),
  you may get javascript generated html contents.

  (In most cases, we can safely ignore (remove) javascript.
  In content sites, the content itself, which you want for *reading*,
  is most likely static. In that case, you don't need Qt libraries.)

* Sometimes writing configurations for each site is too cumbersome.
  You can fallback to automatic article extraction by installing
  `readability <https://github.com/buriy/python-readability>`__.
  But the results may vary.

  (I am writing this script
  precisely because those heuristic extraction libraries are
  unsatisfactory for me.)

* Nowadays most htmls are encoded in UTF-8,
  so use cases are rarer, but by installing
  `ftfy <http://ftfy.readthedocs.io>`__
  and `chardet <http://chardet.readthedocs.io>`__,
  you can do smarter encode detection and configurations.

* It has simple TOC (table of contents) rebounding feature,
  adding one level of structure.
  So if you have downloaded e.g. the entire contents of some blog site
  (sorry for the guy),
  you might be able to get a pdf with annual chapters like 2011, 2012, 2013,
  and articles are inside them.

* A basic bash completion script is included.
  See `tosixinch-complete.bash <topics.html#script-tosixinch-complete.bash>`__.

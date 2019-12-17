
Introduction
============

Somehow, I don't like reading on the computer screen.

So I frequently convert web pages or other texts to pdf, to read in e-readers.
And this script helps me to do that.

---

It divides the job in three, very uncontroversial, stages:

1. ``Download`` html
2. ``Extract`` and format the contents to suit for small paged media
3. ``Convert`` to pdf

And it basically does what people expect it to do,
using the most general technologies.

But it tries a bit harder to get the job done faster.
The legend of the script says, 'Browser to e-reader in a few minutes'.
This constraint ('in a few minutes') generally defines
the domain and methods of the script.

---

Some points to consider:

* The objective is *not* to produce a beautiful pdf.
  it is to manage to make a marginally readable terrible pdf just for personal reading,
  from the least work as possible.

* Many related applications seem to concentrate on major new sites,
  parsing specific article pages or RSS for the target htmls.
  This script doesn't have special functionalities for these sites.
  It is rather for more static reading contents,
  like personal blogs or technical documents.

* Extraction is the most important part of the script.
  But it is done by very simple and predetermined method.

  1. Parse html text as DOM elements tree (by ``lxml``).
  2. ``select`` the elements you want, discarding others.
  3. ``exclude`` undesirable sub-elements from the selected elements.
  4. ``process`` the resultant tree
     (apply arbitrary functions against the tree).
  5. ``clean`` the resultant tree.
     (strip some tags, attributes, javascript and css).

  So the script is only suitable for htmls
  as complex as this simple method can take.
  For example, perhaps the script is not suitable for
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

    * Mac and Windows environments are considered,
      but it is likely to be more imperfect.

    * In some places in code,
      Unicode encoding in system and files is presupposed.

    * Until sometime later, I don't hesitate to change APIs.
      But please feel free to email me if changes break your configuration,
      and I haven't provided the clearest documentation.
      I'll be happy to help.


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

    The patched one is generally preferred, and the script presupposes it.

Anyway, the script just helps to build conversion commandline.
It only adds some useful shortcuts.
Abstraction, consistency or support for multiple converters
are not intended.


Basic Usage
-----------

The main comandline options of the script are:

    * ``-i`` ``INPUT``, ``--input`` ``INPUT`` (input url or file path)
    * ``-f`` ``FILE``, ``--file`` ``FILE`` (file to read inputs)
    * ``-1``, ``--download``
    * ``-2``, ``--extract``
    * ``-3``, ``--convert``

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

Or if even this is a trouble::

    $ tosixinch --sample-urls -123

This command creates 'sample.pdf'
from some arbitrary urls in most of the domains above
(So, it takes a bit of time.)

.. note::

    You need to set the converter if not the default (prince).

    And if you installed the converter in unusual places (not in PATH),
    you need to set the fullpath.

    .. code-block:: none

        $ [...] --wkhtmltopdf --cnvpath /home/john/build/bin/wkhtmltopdf

    (See `Programs <commandline.html#programs>`__
    and `cnvpath <commandline.html#cmdoption-cnvpath>`__.)


.. note::

    The sample script uses ``DejaVu Sans`` and ``Dejavu Sans Mono`` if installed,
    and is optimized for them.

    Otherwise generic ``sans-serif`` and ``monospace`` is used for css.
    You may need to adjust fonts and layout configuration.


.. note::

    These commands create temporary files other than a pdf file
    in current directory.

    * ``_html`` directory, with many html files in it.
    * file ``sample.css``

    You can delete them as you like.


.. note::

    You can also test the results for Python source codes, local or remote.

    .. code-block:: none

        $ tosixinch -i https://raw.githubusercontent.com/python/cpython/master/Lib/textwrap.py -123


Example
-------

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
    exclude=  //div[@class="sidemenu"]
              //div[@class="comment"]

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

And you create a new (extracted) html,
applying the site config to the local html.  ::

    $ tosixinch -i https://somesite.com/article/aaa.html -2

Optionally, you check the extracted html in the browser. ::

    $ tosixinch -i https://somesite.com/article/aaa.html -b

* ``'-b'`` or ``'--browser'`` opens ``Extracted_File``.

You try ``-2`` several times if necessary,
editing and changing the site configuration
(It overwrites the same ``Extracted_File``).

And ::

    $ tosixinch -i https://somesite.com/article/aaa.html -3

* It generates ``./somesite-aaa.pdf``.

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


Features
--------

URL strings can be pre-processed by regular expressions
before mainline processing. `URL replace <topics.html#urlreplace>`__.

You can specify multiple encodings for documents,
including ``chardet`` auto detection and ``ftfy`` UTF-8 encoding fix.
`option: encoding <options.html#confopt-encoding>`__.

The script has very basic Qt web rendering functions (``webkit`` or ``webengine``).
So if you are lucky, by installing
`pyqt5 <https://pypi.python.org/pypi/PyQt5>`__
and `Qt5 <https://www.qt.io>`__,
you may get javascript generated html contents.
(In most cases, we can safely ignore javascript.
In content sites, the content itself is most likely static.
In that case, you don't need Qt libraries.)
`option: javascript <options.html#confopt-javascript>`__.

Sometimes writing configurations for each site is too cumbersome.
You can fallback to automatic article extraction by installing
`readability <https://github.com/buriy/python-readability>`__.
But the results may vary.
`commandline: readability <commandline.html#cmdoption-readability>`__
and `commandline: readability-only <commandline.html#cmdoption-readability-only>`__

As already mentioned, you can manipulate html elements,
by adding arbitrary functions.
`option: process <options.html#confopt-process>`__.

One custom xpath syntax is added, to select class attributes easier.
`double equals <overview.html#dword-XPATH>`__.

It can also convert text and source code to pdf (experimental).
`Text Format <topics.html#text-format>`__.
See also `option: ftype <options.html#confopt-ftype>`__.

For python source code, it can create simple pdf bookmarks for classes and functions.
`code <topics.html#code>`__.

It also converts man pages. `option: add-extractors <options.html#confopt-add_extractors>`__.

It has simple TOC (table of contents) rebounding feature,
adding one level of structure.
So if you have downloaded e.g. the entire contents of some blog site
(sorry for the guy),
you might be able to get a pdf with annual chapters like 2011, 2012, 2013,
and articles are inside them.
`TOC <topics.html#toc>`__.

Users can create their own css files with simple templates,
expanding configuration values.
`CSS Template Values <overview.html#css-template-values>`__.

Users can create site specific css files.
`auto_css directory <overview.html#dword-auto_css_directory>`__.

As already mentioned, it can open the pdf with a pdf viewer.
`Viewcmd <topics.html#viewcmd>`__.

It has pre and post hooks for each (sequential) actions.
For each, users can call external commands or python modules,
adding or bypassing some of the script's capabilities.
`Hookcmds <topics.html#hookcmds>`__.

As a last resort, it can print out file names to be created.
They are determined uniquely given url inputs.
So that users can do some of the script's jobs outside of the script.
`commandline: printout <commandline.html#cmdoption-printout>`__.

A basic bash completion script is included.
`tosixinch-complete.bash <topics.html#script-tosixinch-complete.bash>`__.

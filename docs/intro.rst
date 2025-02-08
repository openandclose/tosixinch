
Introduction
============

I don't like reading on the computer screen.

So I frequently convert web pages or other texts to pdf, to read in e-readers.
And this program helps me to do that.

---

The program divides the job in three, very uncontroversial, stages:

1. ``Download`` html
2. ``Extract`` and format the contents to suit for small paged media
3. ``Convert`` to pdf

And it basically does what people expect it to do,
using the most general technologies.

The major constraint is, as the legend of the program states,
to get the job done ``'in a few minutes'``.

I certainly don't want to spend more time,
but I find, it doesn't work fine if I simplify things more.

So the program should be
against ``'in a few seconds'`` solutions, and ``'in a few hours'`` solutions.


---

Some points to consider:

* The objective is *not* to produce beautiful pdf.
  It is to manage to make a marginally readable pdf,
  from the least work as possible.

* Many related applications seem to concentrate on major news sites,
  parsing specific article pages or RSS for the target htmls.
  This program doesn't have special functionalities for these sites.
  It is rather for more static reading contents,
  like personal blogs and technical documents.

* Extraction is the most important part of the program.
  But it is done by very simple and predetermined method.

  1. Parse html text as DOM elements tree (by ``lxml``).
  2. ``select`` the elements you want, discarding others.
  3. ``exclude`` undesirable sub-elements from the selected elements.
  4. ``process`` the resultant tree
     (apply arbitrary functions against the tree).
  5. ``clean`` the resultant tree
     (strip some tags, attributes, javascript and css).

  So the program is only suitable for htmls
  as complex as this simple method can take.

* I've been using `KOReader <https://koreader.rocks/>`__,
  in recent Kobo e-readers.


Installation
------------

It is an ordinary pure python package, so you should be able to do::

    $ pip install tosixinch

Or rather::

    $ pip install --user tosixinch

The command will only install ``tosixinch`` package.
(You will need other external libraries, but it is not done automatically).

**Python 3.6 and above** are supported.

.. note::

    * Windows filesystems are not supported.

    * UTF-8 encoding in system and files is presupposed.

    * I don't hesitate to change APIs.
      But please feel free to email me if changes break your configuration,
      and I haven't provided the clearest documentation.
      I'd like to know and help.


Requirements
------------

Technically it has no library requirements,
because each action in this program is independent, so optional.

But in general, if you are in the mood to try this program,
installing ``lxml`` and at least one of pdf converters is recommended.
(That way you can do all ``-1``, ``-2`` and ``-3`` below).

* `lxml <http://lxml.de>`__ is used for html DOM manipulations.

* since lxml-5.2.0 (2024/03/31),
  you also need `lxml-html-clean <https://lxml-html-clean.readthedocs.io>`__.

Converters are:

* `prince (or princexml) <https://www.princexml.com>`__
* `weasyprint <http://weasyprint.org>`__

Personally, I use mainly ``prince``,
and (a semblance of) software testing tends to be only concerned with ``prince``.
It is free of charge for non-commercial use.

``weasyprint`` has some limitations, notably it is unbearably slow
(For our usage, it is not rare
that a pdf consists of hundreds or thousands of pages).
But it is written in Python, by great authors.
I want to keep it rather as a reference.


Basic Usage
-----------

The main comandline options of the program are:

    * ``-i`` ``INPUT``, ``--input`` ``INPUT``
    * ``-f`` ``FILE``, ``--file`` ``FILE`` (read file to get ``INPUTS``)
    * ``-1``, ``--download``
    * ``-2``, ``--extract``
    * ``-3``, ``--convert``

``INPUT``:

    either URL or local system path.

    (Except for commandline, it is referred to as ``rsrc`` (resource))

``-1``:

    If ``INPUTS`` are URLs, downloads them, and creates ``dfiles`` (downloaded files).

``-2``:

    reads and edits ``dfiles``, and creates new ``efiles`` (extracted files).

``-3``:

    converts ``efiles``, and creates one pdf file.

Note ``-1``, ``-2`` and ``-3`` take the same ``INPUT`` as argument.
You don't need to change that part of the commandline
(see `Example <#example>`__ below).

The files the program creates are always in current directory,
for ``dfiles`` and ``efiles``, always in ``'_htmls'`` sub directory.


Samples
-------

The program includes a sample ini file (``site.sample.ini``),
and reads it into configuration.

.. code-block:: none

    https://*.wikipedia.org/wiki/*
    https://*.wikibooks.org/wiki/*
    https://wiki.mobileread.com/wiki/*
    https://news.ycombinator.com/item*
    https://news.ycombinator.com/threads?*
    https://old.reddit.com/r/*
    https://stackoverflow.com/questions/*
    https://docs.python.org/*
    https://www.python.org/dev/peps/*
    https://bugs.python.org/issue*
    https://github.com/* (for https://github.com/*/README*)
    https://github.com/*/issues/*
    https://github.com/*/pull/*
    https://github.com/*/wiki/*
    https://gist.github.com/*

For URLs that match one of them,
you can test the program without preparing the configuration.

An example::

    $ tosixinch -i https://en.wikipedia.org/wiki/XPath -123

.. note::

    * You need to set the converter if not the default (``prince``).
      See `Programs <commandline.html#programs>`__.

    .. code-block:: none

        $ [...] --weasyprint

    * If you installed the converter in unusual places (not in PATH),
      you need to set the fullpath.
      See `cnvpath <commandline.html#cmdoption-cnvpath>`__.

    .. code-block:: none

        $ [...] --cnvpath /home/john/build/bin/prince

    * The sample css uses ``DejaVu Sans`` and ``Dejavu Sans Mono`` fonts if installed,
      and is optimized for them.
      Otherwise generic ``sans-serif`` and ``monospace`` are used.
      You may need to adjust fonts and layout configuration.

    * These commands may create temporary files other than the pdf file
      in current directory.
      You can delete them as you like.

Besides sample sites,
some non html texts may work fine with default configuration, local or remote.

.. code-block:: none

    $ tosixinch -i https://raw.githubusercontent.com/python/cpython/master/Lib/textwrap.py -123


Example
-------

You are browsing some website, and you want to bundle some articles in a
pdf file.

Move to some working directory. ::

    $ cd ~/Downloads/tosixinch    # an example

Test for one ``rsrc``.
If it is URL like this one, you have to download it first. ::

    $ tosixinch -i https://somesite.com/article/aaa.html -1

Look into the site structure, using e.g. the browser's development tools,
and write extraction settings for the site. ::

    # in '~/.config/tosixinch/site.ini'
    [somesite]
    match=    https://somesite.com/article/*
    selecet=  //div[@id="main"]
    exclude=  //div[@class="sidemenu"]
              //div[@class="comment"]

.. note ::

    The values of ``select`` and ``exclude`` are
    `XPaths <https://en.wikipedia.org/wiki/XPath>`__.
    In software, html tag structure is made into objects tree
    (``DOM`` or ``Elements``).
    One way to get parts of them is ``XPath``.

    The value above means e.g.
    get from anywhere (``'//'``),
    ``div`` tags whose ``id`` attributes are ``'main'``
    (including every sub-elements inside them).

    Multiple lines are interpreted
    as connected with ``'|'`` (equivalent to ``'or'``).

Generate a new (extracted) html,
applying the site config to the local html.  ::

    $ tosixinch -i https://somesite.com/article/aaa.html -2

Optionally, Check the extracted html in the browser. ::

    $ tosixinch -i https://somesite.com/article/aaa.html -b

* ``'-b'`` or ``'--browser'`` opens ``efile``.

Try ``-2`` several times if necessary,
editing and changing the site configuration
(It overwrites the same ``efile``).

And ::

    $ tosixinch -i https://somesite.com/article/aaa.html -3

* It generates ``./somesite-aaa.pdf``.

Next, Build an ``rsrcs`` list, by some means. ::

    # in './rsrcs.txt'
    https://somesite.com/article/aaa.html
    https://somesite.com/article/bbb.html
    https://somesite.com/article/zzz.html

And ::

    $ tosixinch -123

* If inputs are not specified (no ``-i`` and no ``-f``),
  it defaults to ``'rsrcs.txt'`` in current directory.

* It generates ``./somesite.pdf``, with three htmls as each chapter.

Additionally, if you configured so::

    $ tosixinch -4

* it opens the pdf with a pdf viewer.


Features
--------

``rsrc`` strings can be pre-processed by regular expressions
before mainline processing. `Replace <topics.html#replace>`__.

You can specify multiple encodings for documents,
including ``html5prescan`` encoding declaration parser,
and ``ftfy`` UTF-8 encoding fix.
`option: encoding <options.html#confopt-encoding>`__.

The program has vary basic headless browser downloading functions
using ``Selenium``.
So if you are lucky,
you may get javascript generated html contents.
`option: headless <options.html#confopt-headless>`__.
(Note ``Selenium`` requires
`selenium <https://selenium-python.readthedocs.io/installation.html#downloading-python-bindings-for-selenium>`__
and `firefox or chrome webdrivers <https://selenium-python.readthedocs.io/installation.html#drivers>`__).

Users can define additional instructions for browsers.
`option: dprocess <options.html#confopt-dprocess>`__,
but I recommend you read `process <options.html#confopt-process>`__ first.

As already mentioned, you can manipulate html elements,
by adding arbitrary functions.
`option: process <options.html#confopt-process>`__.

One custom XPath syntax is added, to select class attributes easier.
`double equals <overview.html#double-equals>`__.

If you install
`Pygments <https://pygments.org/>`__,
and ``ctags``
(`Universal Ctags <https://ctags.io/>`__
or `Exuberant Ctags <http://ctags.sourceforge.net/>`__),
you can add pdf bookmarks and links
for source codes definitions.
`_pcode <topics.html#pcode>`__.

As builtin, it has similar but simpler capabilities, only for python source code.
`code <topics.html#code>`__.

It can convert man pages. `_man <topics.html#man>`__.

For other texts,
It can also convert them with some formatting (experimental).
`Text Format <topics.html#text-format>`__.
See also `option: ftype <options.html#confopt-ftype>`__.

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

As already mentioned, it can open the pdf with a pdf viewer.
`Viewcmd <topics.html#viewcmd>`__.

It has pre and post hooks for each (sequential) actions.
For each, users can call external commands or python modules,
adding or bypassing some of the program's capabilities.
`Hookcmds <topics.html#hookcmds>`__.

As a last resort, it can print out file names to be created.
They are determined mostly uniquely given ``rsrc`` inputs.
So that users can do some of the program's jobs outside of the program.
`commandline: printout <commandline.html#cmdoption-printout>`__.

A basic bash completion script is included.
`_tosixinch.bash <topics.html#tosixinch-bash>`__.


Introduction
============

| *Somehow, I don't like reading on the computer screen.*
| *In the olden days, I may have printed them in frustration.*
| *Nowadays I want to convert them to ebooks.*

---

The script is for this purpose.
It is a helper to convert relatively simple html, text or source code
to relatively terrible pdf file
as passable as temporarily printed out paper in a hurry.

Technically it helps configuration management and command dispatch,
and proposes a certain way of doing them.
Actual work is done by well-established libraries and technologies.

The work is serialized in three stages:

1. download html
2. extract and format contents to suit for small paged media
3. convert to pdf

There are several applications with similar objective,
or part of objective.
But they are mostly
for data analysis (discarding layout information),
or specialized in major news sites,
with automatic url retrieve from top pages or rss.
The script is intended for more ordinary reading contents.
Especially personal blogs and technical document sites in mind.

Some characteristics are:

* url collection is done manually.
  You basically write urls in a file by hand.
* Content extraction is done manually.
  You write specific settings for each site
  in a kind of ``ini`` format file.
* It renders to pdf. Arguably it is an arbitrary decision,
  but I find pdf format is more reliable than others, at the present.
* I find so called 'pdf bookmarks' (table of contents navigation)
  are important for e-readers, so some efforts are taken for this concern.

About extraction:

Extraction is the most important part of the script.
But it is done by very simple and predetermined method.

1. Parse html text as DOM tree (by ``lxml``).
2. ``select`` the elements you want, discarding others.
3. ``exclude`` undesirable sub-elements from the selected elements.
4. ``process`` the resultant tree.
   (apply arbitrary functions against the tree
   in a very limited way).
5. ``clean`` the resultant tree.
   (strip some tags, attributes, javascript and css).

So the script is only suitable for htmls
as complex as this simple method can handle.


Installation
------------

It is an ordinary python package, so you should be able to do::

    $ pip install tosixinch

The command will only install ``tosixinch`` package.
(No other external libraries, although a few modules are vendored.)

**Python 3.5 and above** are supported.

.. note::
    
    * It is under construction, to get to the state of first alpha.

    * Mac and Windows environments are considered,
      but it is likely to be more imperfect.

    * In some places in code,
      unicode encoding in system and files is presupossed.

    * Many things will change.


Requirements
------------

Technically it has no library requirements,
because each action in this script is independent, so optional.

But in general, if you are in the mood to try this script,
installing ``lxml`` and at least one of pdf converters is recommended.
(That way you can do all ``-1``, ``-2`` and ``-3`` below).

* `lxml <http://lxml.de>`__ is used for html DOM manipulations.

Converters are:

* `prince <https://www.princexml.com>`__
* `weasyprint <http://weasyprint.org>`__
* `wkhtmltopdf <https://wkhtmltopdf.org>`__
*  ``ebook-convert`` (in `calibre <https://calibre-ebook.com>`__ suite)

| prince recommended, it is one of oldest and most famous.
  (It is free of charge for non-commercial use).
| weasyprint has some limitations, but it is written in python, by great authors.
  I see it rather as a reference.

These two treat ordinary css files as the main (or only) API for style options.
And in general much care is taken to comply to the css standard.

The other two use some old WebKit browser engine,
so what they do is dependent on it, and in general harder to fathom.
But precisely because they use veritable browser engine,
some things are done better.

.. note::
    The wkhtmltopdf official site provides compiled binaries
    built with patched Qt.
    Distributions sometimes install non-patched version of wkhtmltopdf,
    which is limitted in functionalities.

    For example, it can not receive multiple htmls,
    and it can not build pdf bookmarks.

    The official one is generally preferred.

Anyway, the script just helps to build conversion commandline.
It only adds shortcuts.
Abstraction, consistency or support is not intended.

Usage
-----

You are browsing some website, and you want to bundle some articles in a
pdf file.

You move to some working directory. ::

    $ cd ~/Downloads/tosixinch    # an example

You want to test for one url. First, you have to download. ::

    $ tosixinch -i https://somesite.com/article/abc.html -1
        # '-1' means '--download'.
        # The file is saved in current directory

You look into the site structure, using e.g. the browser's development tools,
and write settings for this site
(adding a section in a sites config file). ::

    # in '~/.config/tosixinch/site.ini'
    [somesite]
      match=    https://somesite.com/article/*
      selecet=  //div[@id="article"]    # xpath for the content root
      exclude=  //div[@id="sidemenu"]   # xpath for unneeded parts
                //div[@id="comments"]

And ::

    $ tosixinch -i https://somesite.com/article/abc.html -2
        # '-2' means '--extract'.
        # It actually processes against the downloaded local file,
        # not the remote url in the commandline argument.
        # It generates new html file ('abc--extracted.html').

You check the extracted html in the browser. ::

    $ tosixinch -i https://somesite.com/article/abc.html -b
        # '-b' means '--browser'.
        # It actually opens the extracted local file.

You try ``-2`` several times if necessary, changing settings
(It overwrites the same extracted file).

And ::

    $ tosixinch -i https://somesite.com/article/abc.html -3
        # '-3' means '--convert'.
        # It actually processes against the extracted local file.
        # It generates 'abc.pdf'

Conversion is done according to the settings in application config file,
reading css files if specified.

Next, you build an url list by some means. ::

    # in './urls.txt'
    https://somesite.com/article/abc.html
    https://somesite.com/article/def.html
    https://somesite.com/article/xyz.html

And ::

    $ tosixinch -123
        # Input defaults to 'urls.txt' in current directory.
        # It generates 'somesite.pdf', with three htmls as each chapter.

Additionally, if you configured so::

    $ tosixinch -4
        # opens the pdf with a pdf viewer.


Samples
-------

The script includes a sample ini file (``site.sample.ini``),
and reads it into configuration if not disabled or overwritten. ::

    https://*.wikipedia.org/wiki/* (only tested with 'en.wikipedia.org')
    https://www.gnu.org/software/*
    https://docs.python.org/*
    https://www.python.org/dev/peps/*
    https://bugs.python.org/issue*
    https://news.ycombinator.com/item*
    https://www.reddit.com/r/*
    https://stackoverflow.com/questions/*
    http://www.stackprinter.com/*
    https://github.com/* (for https://github.com/*/README*)
    https://github.com/*/issues/*
    https://github.com/*/wiki/*
    https://gist.github.com/*

For urls that match one of them, you don't have to write your own configs
(for the time being). An example::

    $ tosixinch -i https://en.wikipedia.org/wiki/Xpath -1234


Other Features
--------------

* It can also convert text and source code (now mainly for Python) to pdf.
  Although it may not be common to read code in e-readers,
  I find it rather useful.
  (Of course e-reader's functionalities are limited,
  you cannot do many things.)

* The script has very basic Qt web rendering functions (``webkit`` or ``webengine``).
  So if you are lucky, by installing 
  `pyqt5 <https://pypi.python.org/pypi/PyQt5>`__
  (and `Qt5 <https://www.qt.io>`__),
  you may get javascript generated html contents.

.. note::
    We are interested in static article contents.
    So we can mostly ignore javascripts.
    The above is for exceptional cases 
    where contents themselves are rendered dynamically by javascripts.

* Sometimes writing configurations for each site is too cumbersome.
  You can fallback to automatic article extraction by installing
  `readability <https://github.com/buriy/python-readability>`__.
  But the results may vary.

* Nowadays most htmls are encoded in UTF-8,
  so use cases are rarer, but by installing
  `ftfy <http://ftfy.readthedocs.io>`__
  and `chardet <http://chardet.readthedocs.io>`__,
  you can do smarter encode detection and configurations.

* If you have installed ``ebook-convert`` above,
  The script can convert epub, mobi or other format files to pdf.
  It just calls ``ebook-convert``,
  so there is not so much reason to run our script in this case,
  but you can use the same API and configuration.

* It has simple toc rebounding feature,
  adding one level of structure.
  So if you have downloaded e.g. the entire contents of some blog site
  (sorry for the guy),
  you might be able to get a pdf with annual chapters like 2011, 2012, 2013,
  and articles are inside them.

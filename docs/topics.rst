
.. vim: set spell spelllang=en_us :

Topics
======

Text Format
-----------

When ``extract``, the script actually checks
if the content is really an ``html``.

Currently, the existence of  ``'<html>'`` and optional ``'<doctype>'``
in the first 1000 characters is tested.

.. note::
    The actual regular expression is::

        r'^\s*(?:<!doctype .+>)*\s*<html.*?>'

    It is rather strict. 
    It assumes loose or partial htmls are for presentation or software testing,
    and they are normally expected to be read as raw text.

If it judges that it is not html,
the usual html extraction is skipped.
The text extraction procedure begins instead,
which basically puts all text content inside a ``<pre>`` tag in a html file.

The script separates it into three types:

* prose
* non-prose
* code

prose
^^^^^

``prose`` is supposed to be the general content type.
Paragraph should be the main unit,
we should be able to wrap long lines without problems.
And this is easily achieved by css::

    white-space: pre-wrap;

non-prose
^^^^^^^^^

``non-prose`` is the one in which line breaks are more significant
(source code, verse, play script etc.).
We should keep newlines,
but e-reader screens are so small, this in not possible.

As a solution, the script pre-processes text to have exact line length,
and attaches some label to wrapped lines, according to settings
(``textwidth`` and ``textindent`` respectively).

For a very miniaturized example::

    aaa bbb ccc ddd eee fff ggg.

becomes::

    aaa bbb ccc ddd eee
         >>> fff ggg.

when ``textwidth`` is around ``19`` and ``textindent`` is ``'     >>> '``.

Note that above css is also applied here.
So users have to adjust ``textwidth``,
long enough to make entire use of display width,
short enough not to trigger html auto-wrap renderings,
dependent on font, margin, device etc..

code
^^^^

``code`` is a special case of ``non-prose``,
and currently only for python source code.
It adds small html functionalities.

* ``class`` and ``function`` identifiers in definitions are made ``headings``,
  top level ones are ``<h2>``, others are ``<h3>``.
  So that they appear in table of contents.
  Rendered in bold in ``sample.t.css``.
* These identifiers in the same file are linked to the definitions.
  So that we can navigate a little,
  or just see physically that they are defined words around here (underline).
  Note that linking is only in-file.

problem
^^^^^^^

Currently these filetype detection is automatically done by the script,
and users cannot intervene. Admittedly this is bad.


TOC
---

``TOC`` means Table of Contents, ``bookmarks`` in pdf.

Action ``toc`` can be called only after ``extract`` has been done.
The action bundles ``Extracted Files``,
writes to a single html, and creates a new ``url`` list.

When ``--file`` is ``urls.txt`` (default),
the toc ``url`` list is ``urls-toc.txt``.
It is auto-generated, and always overwrites existing one.
(It could be any other name,
but here we will use just this name for explanation).

Table of Contents adjustments are done
just by decreasing ``heading`` numbers.
PDF converters will do the rest.
(So, some PDF converters can choose
other elements than ``heading`` tags for Table of Contents nodes,
the script only concerns ``headings``).

When ``convert``, ``url-toc.txt`` is automatically discovered,
and if it is newer than corresponding ``urls.txt``,
``convert`` reads the former instead of the latter.
So, the following commands will create the toc version of pdf::

    $ tosixinch -12
    $ tosixinch --toc
    $ tosixinch -3

On the other hand, if this 'newer file' heuristic may interfere,
you have to manually touch or delete files.

rules
^^^^^

It first reads ``urls.txt``.
If there is a line starting with ``'#'``,
it is interpreted as a new chapter (new ``'<h1>'`` text).
Following lines are sections of the chapter,
until next ``'#'`` line begins.
(In other actions, ``'#'`` lines are comments).

For example, from this ``urls.txt``::

    https://somesite.com/index.html                 (1)
    # Alice's articles
    https://somesite.com/alice/article/aaa.html     (2)
    https://somesite.com/alice/article/bbb.html     (3)
    https://somesite.com/alice/article/ccc.html     (4)
    # Bob's articles
    https://somesite.com/bob/article/xxx.html       (5)
    https://somesite.com/bob/article/yyy.html       (6)

``toc`` tracks or creates these files::

    (in './htmls/somesite.com/')
        index--extracted.html                           (7)
    (in './_htmls/tosixinch.example.com/')
        alices-articles--extracted.html                  (8)
        bobs-articles--extracted.html                    (9)

Directory paths are implement details.
``tosixinch.example.com`` is an arbitrary imaginary netloc,
complex path names are 
to keep ``url`` transformation rules consistent
(``url`` to ``Downloaded File`` to ``Extracted File``). 

``(7)``
    (1) is outside of new chapters structure,
    so it doesn't create a file,
    just keeps track of (1)'s ``Extracted File``.

``(8)``
    it creates this new html,
    whose ``<h1>`` is slugified text of ``#'`` line,
    ``<body>`` consists of (2)(3)(4)'s (previous) ``<body>``,
    their ``'<h1>'`` changed to ``'<h2>``,
    ``<h2>`` to ``<h3>`` etc.. ``<h6>`` is kept as is.

``(9)``
    the same as (8)

and it creates ``urls-toc.txt``, which contains::

    https://somesite.com/index.html                 (10)
    http://tosixinch.example.com/alices-articles    (11)
    http://tosixinch.example.com/bobs-articles      (12)


(10)(11)(12) are the names of ``url``,
corresponding to (7)(8)(9) (``Extracted Files``).


Scripts
-------

A few script files are included in the application.
They are not 'installed',
just copied in the tosixinch installation directory
(in ``script`` folder).

**open_viewer**
    It opens a pdf viewer.
    Intended to be used in ``viewcmd`` option in ``tosixinch.ini``.
    Details are explained `there <options.html#general>`__.


**tosixinch-complete.bash**
    A basic bash completion script.
    If you are using bash, it should be useful.
    Source it in your ``.bashrc``. For example::

        source [...]/site-packages/tosixinch/script/tosixinch-complete.bash


Vendored Libraries
------------------

The script package includes a few vendored (included) libraries.
They are all single file modules.

**templite.py**
    This is a module of
    `Ned Batchelder <https://nedbatchelder.com/>`__'s
    `Coverage.py <https://github.com/nedbat/coveragepy>`__,
    and described extensively in
    `a chapter of '500 Lines or Less' <http://aosabook.org/en/500L/a-template-engine.html>`__
    (a great book all together).

    It is a general template engine, used for css template rendering here.

**imagesize.py**
    This is a rewrite of Phuslu's `imgsz <https://github.com/phuslu/imgsz>`__.

    I wanted a simple image format metadata reader,
    (``Pillow`` or other graphic libraries are too big),
    and I found his was the best to copy.

**configfetch*.py**
    `My library <https://github.com/openandclose/configfetch>`__.

    Simplify parsing commandline and config options.

**zconfigparser.py**
    `My library <https://github.com/openandclose/zconfigparser>`__.

    Implement section inheritance in ``site.ini``.

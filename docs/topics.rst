
Topics
======

Text Format
-----------

When ``extract``, the script actually checks
if the content is really an ``html``.
(Before the main extract procedures:
``select``, ``exclude``, ``process``, and ``clean``.)

Currently, only the existence of  ``'<html>'`` tag is checked.
That is, optional legal pre-html-tag components (whitespaces, comments, doctype, etc.)
and the following valid opening ``'<html>'`` tag in the first 1000 characters.

The actual code is now::

   _COMMENT = r'\s*(<!--.+?-->\s*)*'
   _XMLDECL = r'(<\?xml version.+? \?>)?'
   _DOCTYPE = '(<!doctype .+?>)?'
   HTMLFILE = re.compile(
       '^' + _XMLDECL + _COMMENT + _DOCTYPE + _COMMENT + '<html(| .+?)>',
       flags=re.IGNORECASE | re.DOTALL)


.. note::
    It is rather strict.
    It assumes loose or partial htmls are for presentation or software testing,
    and they are normally expected to be read as raw text.

If it judges that it is not html,
the usual html extraction is skipped.
The text extraction procedure begins instead,
which basically puts all text content inside a ``<pre>`` tag in a html file.

The script separates it into three types:

* ``prose``
* ``non-prose``
* ``code``

prose
^^^^^

``prose`` is supposed to be the general content type.
Paragraph should be the main unit.
Physical line wraps do not contribute to document structure.
In other words, we can wrap long lines without changing the meaning.
In most cases, you should have a pre tag rule like this in your css.::

    pre {
       white-space: pre-wrap;
    }

non-prose
^^^^^^^^^

``non-prose`` is the one in which line breaks are *significant*
(source code, verse, play script etc.).
We should keep newlines, so css shouldn't wrap long lines.
But this is not possible in many cases because e-reader screens are so small.

As a solution, the script pre-processes text to have exact line length,
and attaches some label to wrapped lines, according to settings
(`textwidth <options.html#confopt-textwidth>`__ and
`textindent <options.html#confopt-textindent>`__ respectively).

For a short example,::

    nums = [1, 2, 3, 4, 5, 6]


becomes::

    nums = [1, 2, 3, 4,
         >>> 5, 6]

when ``textwidth`` is around ``20`` and ``textindent`` is ``'     >>> '``.

Note that you have to test and adjust ``textwidth`` carefully,
dependent on font, margin, device etc..

If it is too short, e-reader display will have big blanks on the right.
If it is too long, css either triggers auto-wrap,
and introduces confusing line breaks,
or, just puts the rest of the text outside of the display (invisible).


code
^^^^

``code`` is a special case of ``non-prose``,
and currently only for python source code.
It adds small html decorations.

* ``class`` and ``function`` identifiers in definitions are made ``headings``,
  top level ones are ``<h2>``, others are ``<h3>``.
  So that they appear in pdf bookmarks.
  Rendered in bold, in normal font size, in ``sample.t.css``.
* These identifiers in the same file are linked to the definitions.
  So that we can navigate a little,
  or just see physically (underlined link)
  that they are defined words in this module.

  Note that linking is just a simple supplement, only in-file,
  and give up and doesn't do linking for duplicate names
  (e.g. If there are many ``__init__()`` or ``get()``).

.. Note::

   The script adds some informative attributes for the ``pre`` tag it creates.

   For prose, ``<pre class='tsi-text tsi-prose'>...</pre>``.

   For nonprose, ``<pre class='tsi-text tsi-nonprose'>...</pre>``.

   For code, ``<pre class='tsi-text tsi-code'>...</pre>``.

   For pythoncode, ``<pre class='tsi-text tsi-pythoncode'>...</pre>``.

   But ``sample.t.css`` doesn't use these.

problem
^^^^^^^

Currently these filetype detection is automatically done by the script,
and users cannot intervene. Admittedly this is bad.


TOC
---

``TOC`` means Table of Contents, ``bookmarks`` in pdf.

Action ``toc`` can be called only after ``extract`` has been done.
The action bundles ``Extracted_Files``,
writes to a single html, and creates a new ``url`` list
(`toc-ufile <overview.html#dword-toc-ufile>`__).

When ``--file`` is ``urls.txt`` (default),
the toc ``url`` list is ``urls-toc.txt``.
It is auto-generated, and always overwrites existing one.
(It could be any other name,
but here we will use just this name for explanation).

Table of Contents adjustments are done
simply by decreasing ``heading`` numbers.
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

.. Note::

   In practice, you are likely to first try to create
   an ordinary pdf if it is going well at all.
   After that, you may want to create the toc version. ::

       $ tosixinch -12
       $ tosixinch -3     # ordinary pdf
       $ tosixinch --toc
       $ tosixinch -3     # toc version pdf, overwrites the above


rules
^^^^^

It first reads ``urls.txt``.
If there is a line starting with ``'#'``,
it is interpreted as a new chapter (new ``'<h1>'`` text).
Following lines are sections of the chapter,
until next ``'#'`` line begins.
(In other ``actions``, ``'#'`` lines are comments).

For example, from this ``urls.txt``

.. code-block:: none

    https://somesite.com/index.html                 (1)
    # Alice's articles
    https://somesite.com/alice/article/aaa.html     (2)
    https://somesite.com/alice/article/bbb.html     (3)
    https://somesite.com/alice/article/ccc.html     (4)
    # Bob's articles
    https://somesite.com/bob/article/xxx.html       (5)
    https://somesite.com/bob/article/yyy.html       (6)

``toc`` tracks or creates these files.

.. code-block:: none

    (in './_htmls/somesite.com/')
        index--extracted.html                            (7)
    (in './_htmls/tosixinch.example.com/')
        alices-articles--extracted.html                  (8)
        bobs-articles--extracted.html                    (9)

Directory paths are implement details.
``tosixinch.example.com`` is an arbitrary placeholder host,
verbose path names are
to keep ``url`` transformation rules consistent
(``url`` to ``Downloaded_File`` to ``Extracted_File``).

``(7)``
    (1) is outside of new chapters structure,
    so it doesn't create a file,
    just keeps track of (1)'s ``Extracted_File``.

``(8)``
    it creates this new html,
    whose ``<h1>`` is ``#`` line,
    ``<body>`` consists of (2)(3)(4)'s (previous) ``<body>``,
    their ``<h1>`` changed to ``<h2>``,
    ``<h2>`` to ``<h3>`` etc.. ``<h6>`` is kept as is.

    So for example, two html files below become the third file.

    .. code-block:: html

        <html>
          <body>
            <h1>aaa</h1>
            <p>this is aaa.</p>
          </body>
        </html>

    .. code-block:: html
        
        <html>
          <body>
            <h1>bbb</h1>
            <p>this is bbb.</p>
          </body>
        </html>

    .. code-block:: html

        <html>
          <body>
            <h1>Alice's articles</h1>
            <div class='tsi-body-merged'>
               <h2>aaa</h2>
               <p>this is aaa.</p>
            </div>
            <div class='tsi-body-merged'>
               <h2>bbb</h2>
               <p>this is bbb.</p>
            </div>
          </body>
        </html>

``(9)``
    the same as (8)

and it creates ``urls-toc.txt``, which contains::

    https://somesite.com/index.html                 (10)
    http://tosixinch.example.com/alices-articles    (11)
    http://tosixinch.example.com/bobs-articles      (12)


(10)(11)(12) are the names of ``urls``,
corresponding to (7)(8)(9) (``Extracted_Files``).

So, ``convert`` doesn't do anything special for ``urls-toc.txt``,
just process pre-built htmls and produce a more structured pdf.


Scripts
-------

A few script files are included in the application.
They are not 'installed',
just copied in the tosixinch installation directory
(in ``script`` folder).

.. script:: open_viewer

    It opens a pdf viewer.
    Intended to be used in ``viewcmd`` option in ``tosixinch.ini``.
    Details are explained `there <options.html#general>`__.


.. script:: tosixinch-complete.bash

    A basic bash completion script.
    If you are using bash, it should be useful.
    Source it in your ``.bashrc``. For example::

        source [...]/site-packages/tosixinch/script/tosixinch-complete.bash


Vendored Libraries
------------------

The script package includes a few vendored (included) libraries.
They are all single file modules.

.. script:: templite.py

    This is a module of
    `Ned Batchelder <https://nedbatchelder.com/>`__'s
    `Coverage.py <https://github.com/nedbat/coveragepy>`__,
    and described extensively in
    `a chapter of '500 Lines or Less' <http://aosabook.org/en/500L/a-template-engine.html>`__
    (a great book all together).

    It is a general template engine, used for css template rendering here.

.. script:: imagesize.py

    This is a rewrite of Phuslu's `imgsz <https://github.com/phuslu/imgsz>`__.

    I wanted a simple image format metadata reader,
    (``Pillow`` or other graphic libraries are too big),
    and I found his was the best to copy.

.. script:: configfetch.py

    `my library <https://github.com/openandclose/configfetch>`__.

    Simplify parsing commandline and config options.

.. script:: zconfigparser.py

    `my library <https://github.com/openandclose/zconfigparser>`__.

    Implement section inheritance in ``site.ini``.

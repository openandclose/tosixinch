
Topics
======

'Advanced' subjects are discussed here.

Text Format
-----------

(Experimental)

When ``extract``, the program actually checks
if the content is really an ``html``.
(Before the main extract procedures:
``select``, ``exclude``, ``process``, and ``clean``).

Currently, only the existence of  ``'<html>'`` tag is checked.

Even this is rather strict.
I assume that loose or partial htmls are for presentation or software testing,
and they are normally expected to be read as raw text.

If it judges that it is not html,
the html extraction is skipped.
The text extraction procedure begins instead,
which basically puts all text content inside a ``<pre>`` tag in a html file.

The program separates it into three types:

* ``prose``
* ``non-prose``
* ``code``

And it adds some informative attributes
to the ``pre`` tag it creates.

For ``prose``, ``class="tsi-text tsi-prose"``.

For ``nonprose``, ``class="tsi-text tsi-nonprose"``.

For ``code``, ``class="tsi-text tsi-code"``.

For ``pythoncode``, ``class="tsi-text tsi-code tsi-python"``.

In case of ``code``, It also adds the same attributes
to other new tags it creates. (``h2``, ``h3``, and ``span``).

prose
^^^^^

``prose`` is supposed to be the general content type.
Paragraph should be the main unit.
Adding extra line wraps should not change major semantic structure.

In most cases, you should have a ``pre`` tag rule like this in your css.::

    pre {
       white-space: pre-wrap;
    }

non-prose
^^^^^^^^^

``non-prose`` is the one in which line breaks are *significant*
(source code, verse, play script etc.).
We should keep newlines, so css shouldn't wrap long lines.
But this is not possible in many cases because e-reader screens are so small.

As a solution, the program pre-processes text to have exact line length,
and attaches some label to wrapped lines, according to settings
(`textwidth <options.html#confopt-textwidth>`__ and
`textindent <options.html#confopt-textindent>`__ respectively).

So that readers can tell source line breaks
from editorial layout line breaks.

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

.. note::

    Now ``_pcode`` is the recommended method to format source codes.
    See `_pcode <#pcode>`__.

``code`` is a special case of ``non-prose``,
and currently only for Python source code.
It adds pdf bookmarks and the references for some identifiers.

For this purpose, class and function names are wrapped
in ``h2``, ``h3`` and ``span``.
Since this is very special usage of tags,
you need to create very special css rules
(using ``'tsi-code'`` class attribute).

See ``sample.t.css``, for an example.


TOC
---

``TOC`` means Table of Contents, or pdf bookmarks.


Concept
^^^^^^^

Given the following ``rsrcs.txt``:

.. code-block:: none

    https://somesite.com/index.html                 (1)
    # Alice's articles                              (2)
    https://somesite.com/alice/article/aaa.html     (3)
    https://somesite.com/alice/article/bbb.html     (4)
    https://somesite.com/alice/article/ccc.html     (5)
    # Bob's articles                                (6)
    https://somesite.com/bob/article/xxx.html       (7)
    https://somesite.com/bob/article/yyy.html       (8)

The program ordinarily creates top level pdf bookmarks like this:

.. code-block:: none

    -- index
    -- aaa
    -- bbb
    -- ccc
    -- xxx
    -- yyy

``TOC`` feature helps create one level more structured pdf bookmarks like this:

.. code-block:: none

    -- index
    -- Alice's articles
       -- aaa
       -- bbb
       -- ccc
    -- Bob's articles
       -- xxx
       -- yyy

To do that, ``--toc`` action creates

* new htmls

  * ``h1`` strings are made from hash comment lines (2 and 6).
  * contents are made from children htmls (3, 4 and 5. And 7 and 8).

* new ``rfile`` (``tocfile``)

  * made to refer to newly created htmls instead of now redundant children htmls.

``--convert`` action, in turn, read ``tocfile`` instead of the original ``rfile``,
if ``tocfile`` exists, and *it's mtime is newer*.

So that if you run

.. code-block:: bash

    $ tosixinch -12
    $ tosixinch --toc
    $ tosixinch -3

or

.. code-block:: bash

    $ tosixinch -123 --toc

The program creates a more structured version of pdf file.

Rules
^^^^^

The ``toc`` action treats ``'#'`` as special chapter directive.
So comments in ``rfile`` are lines only beginning ``';'``.
(In other ``actions``, both ``'#'`` and ``';'`` are comments).

The ``toc`` action creates `tocfile <overview.html#dword-tocfile>`__
in current directory, adding ``'-toc'`` to ``rfile``.
(When ``--file`` is ``'rsrcs.txt'`` (default),
the name of ``tocfile`` is ``'rsrcs-toc.txt'``).

So it is Error when ``rfile`` is not provided.
(``--file`` or implicit ``rsrcs.txt``. No ``--input``).

The ``toc`` action processes normally ``efiles``,
bundling some of them, and creating new htmls.

Table of Contents adjustments are done
simply by decreasing ``heading`` numbers.

It first reads ``rsrcs.txt``.
If there is a line starting with ``'#'``,
it is interpreted as a new chapter
(new html ``<title>`` and new ``'<h1>'`` text).
Following lines become sections of the chapter,
until next ``'#'`` line begins.

To use the same example:

.. code-block:: none

    https://somesite.com/index.html                 (1)
    # Alice's articles                              (2)
    https://somesite.com/alice/article/aaa.html     (3)
    https://somesite.com/alice/article/bbb.html     (4)
    https://somesite.com/alice/article/ccc.html     (5)
    # Bob's articles                                (6)
    https://somesite.com/bob/article/xxx.html       (7)
    https://somesite.com/bob/article/yyy.html       (8)

``toc`` tracks or creates these files.

.. code-block:: none

    _htmls/somesite.com/index.html                  (11)
    _htmls/tosixinch.example.com/alices-articles    (12)
    _htmls/tosixinch.example.com/bobs-articles      (13)

``tosixinch.example.com`` is an imaginary placeholder host.

``(11)``
    (1) is outside of new chapters structure,
    so it doesn't create a file,
    just keeps track of (1)'s ``efile``.

``(12)``
    it creates this new html,
    whose ``<h1>`` is line (2),
    ``<body>`` consists of (3)(4)(5)'s (previous) ``<body>``,
    their ``<h1>`` changed to ``<h2>``,
    ``<h2>`` to ``<h3>`` etc.. ``<h6>`` is kept as is.

    So three html files below would become the 4th file.

    .. code-block:: html

        <html>
          <body>
            <h1>aaa</h1>
            <p>this is aaa.</p>
          </body>
        </html>

        <html>
          <body>
            <h1>bbb</h1>
            <p>this is bbb.</p>
          </body>
        </html>

        <html>
          <body>
            <h1>ccc</h1>
            <p>this is ccc.</p>
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
            <div class='tsi-body-merged'>
               <h2>ccc</h2>
               <p>this is ccc.</p>
            </div>
          </body>
        </html>

``(13)``
    the same as (12).

and it creates ``rsrcs-toc.txt``, which contains::

    https://somesite.com/index.html                 (21)
    http://tosixinch.example.com/alices-articles    (22)
    http://tosixinch.example.com/bobs-articles      (23)


(21)(22)(23) are the names of ``rsrcs``,
corresponding to (11)(12)(13) (``efiles``).

So, ``convert`` doesn't do anything special for ``rsrcs-toc.txt``,
just processes pre-built htmls.

.. note::

    The new html collects all the css files
    referenced in children htmls in order.
    So, if you are using different css files for sites,
    you should control the effects carefully.


Replace
----------

If there is a file ``'replace.txt'`` in `userdir <overview.html#dword-userdir>`__,
it is used for regex ``rsrc`` preprocess.

The ``rsrcs`` matching the pattern are internally changed to replacement ``rsrcs``,
and processed accordingly.

If there are lines in the file::

    https://www\.reddit\.com/
    https://old.reddit.com/

the first line is a regex pattern, the second line is a regex replacement
(for Python `re.sub() <https://docs.python.org/3/library/re.html#re.sub>`__).
So that

.. code-block:: bash

    $ tosixinch -i https://www.reddit.com/aaa.html -123

downloads, extracts and creates the pdf file
from ``'https://old.reddit.com/aaa.html'``.

The format of the file is:

.. code-block:: none

    the file consists of zero or more units.

    the unit consists of:
        one regex pattern line
        one regex replacement line
        one or more blank lines or EOF

So if there are lines, they are always two consecutive lines,
separated by blank lines.
(blank lines in the very first line and the very last line of the file
are optional).

The lines starting with ``'#'`` are ignored (comments).
You can put them in any line in units.


Hookcmds
--------


Precmds and Postcmds
^^^^^^^^^^^^^^^^^^^^

Before and after main actions (``'-1'``, ``'-2'`` and ``'-3``),
The program calls arbitrary commands,
according to precmds and postcmds options in ``tosixinch.ini``.

One useful use case of ``postcmds`` is notification,
since ``download`` and ``convert`` sometimes take time.
For example::

    postcmd1=   notify-send -t 3000 'Done -- tosixinch.download'

should bring some notification balloon
when ``download`` is complete.

**Variables:**

`script directory <overview.html#dword-script_directory>`__ is inserted in the head of ``$PATH``.
So you can call your custom scripts only by filenames (not fullpath),
if they are in there.

If a word in the statement begins with ``'conf.'``,
and the rest is dot-separated identifier (``[a-zA-Z_][a-zA-Z_0-9]+``),
it is evaluated as the object ``conf``. For example::

    postcmd1=   echo conf._configdir conf._userdir

will print application config directory name and user config directory name.

(For more advanced usage, you need to peek in the source code.
It uses ``eval``, so be careful.)

**Running Module:**

If a command consists of one word, without 'dot',
and the ``'.py'`` extension file actually exists in `script directory <overview.html#dword-script_directory>`__,
the program runs the command as Python module internally
(as opposed to running it as an external system subprocess).

That is, if a cmd is ``['foo']``, for example::

    precmd1=    foo

and there is a file ``foo.py`` in ``script directory``,
the program does roughly::

    import script.foo
    script.foo.run(conf, site)

So the module must have ``run`` function with this signature.
(In this context, ``site`` should be ``None``.
*Whole* action ``hookcmds`` only have application level configuration.
*each* action ``hookcmds`` (see below) are given ``site``).

``userdir`` is inserted to ``sys.path`` (``sys.path[0]``).
So if you want to import sibling modules in the program file,
refer them from ``script`` package, e.g. ::

    import script.bar
    from script import baz

The difference from running subprocess is that
it should be a bit faster, and ``conf`` and ``site`` are writable.

.. note::

    If you want to run a python file as subprocess, put in the actual filename::

        precmd1=    foo.py

**Multiple Commands:**

Their value function signatures are ``[LINE][CMDS]``, that is,
you can run multiple commands in a hookcmd, one command for each line.

If the return code of a command is 0,
the program runs the next command, if any.

If the return code of a command is 100,
the program skips the following commands, if any.

If the return code of a command is 101,
and the command is one of precmds (not postcmds),
the program skips the following commands,
and the following action altogether.
The following *postcmd* are executed.

If the return code of a command is 102,
the program skips the following postcmd in addition.

.. code-block:: none

    precmd: cmd,   cmd,   cmd,   cmd,   cmd...
                   | 100  | 101  | 102
                   |      |      |
                  action  |      |
                          |      |
                       postcmd   |
                                 |
                           (to next action group)

In running subprocess, other return codes (not 0, 100, 101, 102) aborts the program.

In running module, any other return codes and values (not 0, 100, 101, 102)
are interpreted as 0.
(It is to permit normal Python return value of ``None``.
Python itself will abort the program if something goes wrong).


Viewcmd
^^^^^^^

A special case of ``hookcmds`` is ``viewcmd``.

``viewcmd`` triggers when ``-4`` or ``--view`` option is supplied.
But actually there is no action called ``4`` or ``view``.

It is intended to open a pdf viewer,
after pdf generation is done (``-3``).

So, if you are using `okular <https://okular.kde.org/>`__
as pdf viewer, ::

    # in tosixinch.ini
    viewcmd=    okular conf.pdfname

    $ tosixinch -4

will open the viewer with the generated pdf file.

Also, the program includes a sample file `_viewer.py <topics.html#viewer>`__.
(It does basically the same thing as above,
but cancels duplicate openings).


Pre_Each_Cmds and Post_Each_Cmds
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An action group consists of ``precmd``, ``action`` and ``postcmd``.
But when ``download`` or ``extract``,
``action`` itself is a collection of jobs, one job for each ``rsrc``.
For this job, there are corresponding pre- and post- hookcmds.

.. code-block:: none

    precmd                  pre_each_cmd
    action (rsrcs) ---+---  job (an rsrc)
    postcmd           |     post_each_cmd
                      |
                      |     pre_each_cmd
                      +---  job (an rsrc)
                      |     post_each_cmd
                      |
                      :     ...

The specification (return codes etc.) is the same as precmds and postcmds.

In this context, there are ``rsrc`` specific configurations,
in addition to application level configuration.
So you can use ``site`` variable, in addition to ``conf``:

If a word in the statement begins with ``'site.'``,
and the rest is dot-separated identifier (``[a-zA-Z_][a-zA-Z_0-9]+``),
it is evaluated as the object ``site``. For example::

    post_each_cmd1=   echo site.efile site.match

will print each ``efile`` and ``match`` option value.

Also, the following environment variables are exposed
(in running subprocess case).

.. code-block:: none

    TOSIXINCH_RSRC:     rsrc
    TOSIXINCH_DFILE:    dfile
    TOSIXINCH_EFILE:    efile


Scripts
-------

A few sample script files are included in the application.
They are in ``tosixinch/script`` directory in the installation.
You can refer them in user configurations


_viewer
^^^^^^^

Intended to be used in ``viewcmd`` option in ``tosixinch.ini``.

It opens a pdf viewer.
But if there is a same pdf application opened with the same pdf file,
if does nothing (cancels duplicate openings).

It uses unix command ``ps``.

It can be used without full path.::

    viewcmd=    _viewer.py --command okular --check --null conf.pdfname

* ``--command`` accepts arbitrary commands with some options,
  but you need to quote.
  (e.g. ``--command 'okular --page 5'``).
* ``--check`` is the option flag to do above duplicate check.
* ``--null`` is to suppress *this* command's stdout and stderr.

And one way to see the help is::

    $ tosixinch -4 --viewcmd '_viewer.py --help' -i aaa

(This doesn't work if ``rsrc`` is not supplied,
so you have to supply something, like the above ``-i aaa``.)


_man
^^^^

A sample hook extractor for man pages.
If you want to use it, add this command to ``pre_each_cmd2`` in user configuration.

When ``extract``,
if the filename matches ``r'^.+\.[1-9]([a-z]+)?(\.gz)?$'``
(e.g. grep.1, grep.1.gz, grep.1p.gz),
run man program with ``'man -Thtml'``,
skipping the main extraction.

.. note ::

    * ``pre_each_cmd2`` is a ``LINE`` option,
      so multiple commands must be separated with newline and indent e.g.:

      .. code-block:: ini

          pre_each_cmd2=    echo foo
                            _man

    * If you supply multiple ``rsrcs``,
      it triggers the binary-extension filter,
      and the default includes ``gz``.
      In this case, you have to subtract ``gz`` from the list.
      (see `add_binary_extensions <#confopt-add_binary_extensions>`__).

      .. code-block:: bash

          # in rsrcs.txt
          /usr/share/man/man1/cp.1.gz
          /usr/share/man/man1/grep.1.gz

          $ tosixinch -123 --add-binary-extensions -gz


_pcode
^^^^^^

A sample hook extractor for source codes (pcode: short of '``Pygments`` code').

It formats (html-wraps) some ``Pygments`` tokens.
The purpose is to make them pdf bookmarks items,
and create references to them.
If you want to use it, add this command to ``pre_each_cmd2`` in user configuration.

Note ``pre_each_cmd2`` is a ``LINE`` option, see the above note for ``_man``.

You need to install
`Pygments <https://pygments.org/>`__,
and ``ctags``
(`Universal Ctags <https://ctags.io/>`__
or `Exuberant Ctags <http://ctags.sourceforge.net/>`__).

It creates working files ``tsi.tags`` and ``tsi.tags.checksum``
in current directory
(The script skips tag creation,
if command, files and (max) mtime are the same as the previous run).

As stated in `code <topics.html#code>`__,
it uses ``h2`` and ``h3`` tags very unusual way.
You need special css rules (See ``sample.t.css``, for an example).

**Language names:**

``Pygments`` is a code highlighter, the script uses to find identifiers.

But ``Pygments`` doesn't tell where the identifier definition is,
so we also need ``Ctags`` to find the definitions.

``Pygments`` and ``Ctags`` have slightly different language names,
e.g. 'reStructuredText' (``Pygments``) and 'ReStructuredText' (``Ctags``).
So they must be mapped to third common names the script defines (``ftype``).

``ftypes`` are all lower cases,
so the names, which happen to be case-insensitively the same, are already mapped.
But the other names must be explicitly mapped to the same ``ftype`` in configuration,
using ``c2ftype`` and ``p2ftype`` sections.

To see actual mappings, run tosixinch with some text input and with ``--verbose``::

    tosixinch -i <some-text-file> -12 --verbose

**Configuration:**

You can specify some configuration
if you create ``pcode.ini`` in `userdir <overview.html#dword-userdir>`__.

(See the default config file ``tosixinch/data/pcode.ini``, for the example).

``arguments`` option in the default ``pcode.ini`` above,
are currently like this.
It is commandline arguments to run ``Ctags``,
and most are required to work as the script is supposed to work.

.. code-block:: none

    --options=NONE      # reset
    --format=2          # only support extended format
    --sort=no           # toc is normally in appearance order
    --excmd=number      # only support line number, not pattern
    --file-scope=yes    # only support in-file tags now
    --fields=fkl        # need them, filename, kind, and language
    --kinds-python=cfm  # define which kinds to use
                        # in each language
                        # ('--<lang>-kinds' in Exuberant Ctags)

``kindmap`` option in the default ``pcode.ini`` are like this::

    kindmap=    h2=cf, h3=m

Which means: wrap ``Ctags`` kinds ``cf`` (class and function) in html ``<h2>`` tag,
and wrap ``m`` (method) in ``<h3>`` tag.

But since ``Ctags`` kinds are greatly differ for each language,
you have to customize them for each of your languages.

One ``*`` is allowed, to mean any other kinds, so you can write the same as above ::

    kindmap=    h2=*, h3=m

**Customization:**

You can write custom module using the class ``tosixinch.script.pcode._pygments.PygmentsCode``.

Example:

.. code-block:: python

    # ~/.config/tosixinch/script/pcode/perl.py

    from tosixinch.script.pcode import _pygments

    class CustomCode(_pygments.PygmentsCode):

The entry point is ``format_entry``,
which has sub entry points ``check_def``, ``check_ref``, ``wrap_def`` and ``wrap_ref``.

See ``tosixinch/script/pcode/python.py`` for the example.

Relevant options are:

* (new section):
    create new section as the same name as ftype
* module:
    module name for your custom module.
    you have to create this module
    in ``pcode`` directory in `script directory <overview.html#dword-script_directory>`__
    (e.g. '~/.config/tosixinch/script/pcode/perl.py' above).

    Example::

        [perl]
        module=   perl
* class:
    class name for you custom class in the module above.
    the default is ``CustomCode``.
* start_token:
    Pygments token type name.
    All other tokens (and their subclasses) are not touched by formatting.
    Normally ``Token.Name`` is suffice (default).
* kindmap:
    Explained above.

**Generic Ftypes**

If ``Pygments`` finds a language but the language is not mapped,
It returns without doing formatting,
but the script registers the ``rsrc``'s ``ftype`` as ``nonprose``.

(It is an heuristic.
If ``Pygments`` finds a language, it is better to treat the text as code-like,
not ``prose``).

If ``Pygments`` name is mapped,
but ``Ctags`` doesn't find a language, or the language is not mapped, or not mapped to the same name,
It does formatting only with ``Pygments`` tokens.

As a special case, if ``Pygments`` name is mapped to the name ``'prose'``,
It does not do formatting, but registers the ``rsrc``'s ``ftype`` as ``prose``
(The default is: ``reStructuredText`` and ``markdown``).


_tosixinch.bash
^^^^^^^^^^^^^^^

A basic bash completion script.
If you are using bash, it should be useful.
Source it in your ``.bashrc``. For example::

    source [...]/site-packages/tosixinch/data/_tosixinch.bash


Vendored Libraries
------------------

The program uses a few vendored (included) libraries.

.. script:: templite.py

    This is a module of
    `Ned Batchelder <https://nedbatchelder.com/>`__'s
    `Coverage.py <https://github.com/nedbat/coveragepy>`__,
    and described extensively in
    `a chapter of '500 Lines or Less' <http://aosabook.org/en/500L/a-template-engine.html>`__.

    It is a general template engine, used for css template rendering here.

.. script:: imagesize.py

    This is a rewrite of Phuslu's `imgsz <https://github.com/phuslu/imgsz>`__.

    I wanted a simple image format metadata reader,
    (``Pillow`` or other graphic libraries are too big),
    and I found his was the best to copy.

.. script:: configfetch.py

    Simplify parsing commandline and config options.
    `(configfetch) <https://github.com/openandclose/configfetch>`__.

.. script:: zconfigparser.py

    Implement section inheritance in ``site.ini``.
    `(zconfigparser) <https://github.com/openandclose/zconfigparser>`__.


Overview
========

Actions
-------

The script consists of several, independent actions (subcommands).

An action is either a ``sequential action`` or a ``single action``.

``sequential actions`` are:
    * `download <#download>`__
    * `extract <#extract>`__
    * `toc <topics.html#toc>`__ (make better table of contents)
    * `convert <#convert>`__
    * `view <topics.html#viewcmd>`__ (open pdf viewer)

.. note::

    ``toc`` does not belong to the mainline actions,
    and anyway very experimental.
    So first-time readers can skip the references.

You can call more than one ``sequential actions`` in one invocation.
Irrespective of the arguments order,
the script executes actions in the above order.

So, the three invocations below make no difference. ::

    $ tosixinch -1  # download
    $ tosixinch -2  # extract
    $ tosixinch -3  # convert

    $ tosixinch -123

    $ tosixinch -321

``single actions`` are:
    * `appcheck <commandline.html#cmdoption-a>`__

      Print application settings, and exit.

      They are global, with commandline evaluation,
      but without site-specific option evaluation.
      
    * `browser <commandline.html#cmdoption-b>`__

    * `check <commandline.html#cmdoption-c>`__

      Print matched url settings and, exit.
      
      You have to supply url some way (``-i`` or ``-f``).
      If input url is only one,
      print all the option values.
      Otherwise, print just section name and ``match`` option.

    * `printout <commandline.html#cmdoption-printout>`__
    * `inspect <commandline.html#cmdoption-inspect>`__
      
      Do something, according to site config option
      `inspect <options.html#confopt-inspect>`__

The script executes only the first ``single action``
(if there are many, or mixed with sequential ones),
and exits.

download
^^^^^^^^

Downloads ``url``, and saves it as ``Downloaded_File``.

If `force_download <options.html#confopt-force_download>`__ is ``False`` (default),
the script skips downloading if the file already exists.

If ``url`` is a local filepath, it also does nothing.
``Downloaded_File`` is the same as ``url``.

For the actual downloading, it just uses
`urllib.request <https://docs.python.org/3/library/urllib.request.html>`__
(python standard library),
with `user-agent <options.html#confopt-user_agent>`__ and
`encoding <options.html#confopt-encoding>`__ configurable.

If `javascript <options.html#javascript>`__ option is ``True``,
The script uses `pyqt5 <https://pypi.python.org/pypi/PyQt5>`__
instead of ``urllib``.

extract
^^^^^^^

Opens ``Downloaded_File``, and generates ``Extracted_File``.
(``Downloaded_File`` is kept intact).

It always runs, overwriting existing ``Extracted_File`` if any.

(If ``url`` is local filepath, ``Downloaded_File`` is not created,
but ``Extracted_File`` *is* created).

Extraction procedure is predetermined,
and according to options in `site.ini <#dword-site.ini>`__.
See `select <options.html#confopt-select>`__,
`exclude <options.html#confopt-exclude>`__,
`process <options.html#confopt-process>`__
and `clean <options.html#confopt-clean>`__ options.

convert
^^^^^^^

Opens ``Extracted_File``, and generates ``PDF_File``.
(``Extracted_File`` is kept intact).

It always runs, overwriting existing ``PDF_File`` if any.

The `converter <options.html#confopt-converter>`__ option
decides which ``converter`` to use.


Target Files
------------

The point of the script is that you don't have to specify
each input and output for each consecutive action.
For this, given ``url``, target files' names are uniquely determined.

All generated html files are
in ``_htmls`` sub directory in current directory (created if necessary).

Generated *pdf* file is placed under current directory.

Usually users don't have to care about these files' details.
But disposing of the files (deleting or moving) is users' job.

.. dword:: url

    Input resource location. URL or local filepath.
    Only ``http``, ``https`` and ``file`` schemes are supported for URL.

    Example::

        https://en.wikipedia.org/wiki/Xpath

.. note::

    file urls are only for regular local files, starting from one of::

        file:/
        file://localhost/
        file:///

    They are converted immediately to regular filepaths,
    so e.g. ``--printout 0`` returns the latter.

.. dword:: ufile

    The required argument of the commandline option ``-f`` or ``--file``.
    It should be a file containing ``urls``.

    ``ufile`` defaults to `urls.txt <#dword-urls.txt>`__.

    The file's syntax is:

        * Each line is parsed as ``url`` (or filepath).

        * When action is not ``toc``,
          the lines starting with ``'#'`` or ``';'`` are ignored.

        * When action is ``toc``,
          the lines starting with ``'#'`` are interpreted as chapters.
          the lines starting with ``';'`` are ignored.

        * When there are multiple ``urls``,
          if ``url`` has an extension that looks like binary,
          this ``url`` is ignored
          (according to 
          `add_binary_extensions <options.html#confopt-add_binary_extensions>`__ option).

          Note if input ``url`` is single,
          whether ``-i`` or ``-f``,
          this ``add_binary_extensions`` filter is not applied.

.. dword:: Downloaded_File

    If ``url`` is a remote one,
    ``Downloaded_File`` is created inside ``_htmls`` directory,
    with URL ``authority`` and ``path segments`` as subdirectories.

    If ``url``'s last ``path`` doesn't have file extension or ``'?'``,
    string ``'/_'`` is added.
    If it ends with ``'/'``, ``'_'`` is added.

    .. note::

        Recent servers extensively use no-extension urls with or without a slash.
        They tend to make each path component a veritable resource destination.

        These URLs are difficult to convert to filepath.

        E.g. they have both urls::

            'http://example.com/aaa'         # a document
            'http://example.com/aaa/bbb'     # a document

        and since the filesystems cannot have the same name ('aaa')
        for a file name and a directory name,
        we have to invent some artificial local routing rules.

        This is the reason for this rather verbose name changing.

        Extension check is a rough heuristic
        because I don't want to go any further.

        If the site has a url ::

            'http://example.com/aaa.html'

        I assume It is less likely that
        the site would create ``'aaa.html/bbb'`` document.


    In Windows, illegal filename characters (``':?*\"<>```) in ``url`` are
    all changed to ``'_'``.
    So name conflict may occur in rare cases.

    In Unixes, these special characters are used in filenames as is.

    Example::

        ~/Download/tosixinch/_htmls/en.wikipedia.org/wiki/Xpath/_

    .. note::

        As an exception, if original ``url`` is too long for file name conversion
        (a path segment more than 255 characters),
        the whole ``url`` is sha1-hashed,
        and the name takes a ``_html/_hash/<sha1-hexdigit>`` form.

.. dword:: Extracted_File

    String ``'~'`` and ``'.html'`` (If not already have one)
    is added to ``Downloaded_File``.

    If ``url`` is a local filepath,
    The path components of ``Extracted_File`` are created
    by the same process as ``Downloaded_File``.

    Example::

        ~/Download/tosixinch/_htmls/en.wikipedia.org/wiki/Xpath/_~.html

.. dword:: PDF_File

    When ``--pdfname`` option is not provided,
    the script auto-creates the pdf filename.
    The name is made up from ``url``'s last path,
    query, section name and host name *of the first url*.

    Example::

        ~/Download/tosixinch/wikipedia-Xpath.pdf (from single input)
        ~/Download/tosixinch/wikipedia.pdf (from multiple input)

    Even if ``urls`` are from multiple domains (e.g. wikipedia and reddit),
    the filename of the pdf is named after the first one (just wikipedia).
    So, it is not always appropriate.


Config Files
------------

.. dword:: urls.txt

    It is the default filename for ``--file``,
    and used when no other file or input ``url`` is specified.

.. note::

    In general, it is better users have this file,
    on the working directory specially chosen for ``tosixinch``.

    I imagine this is the difference from ``a few hours`` application.
    Many scraping or data extraction programs adopt 'new project strategy'.
    For each objective, users think up some suitable name and place
    (this is the hard part),
    create a new directory,
    and then let the programs initialize directory structure
    and various configuration files.

    I find this is a bit excessive for our humble ``a few minutes`` concern.
    Users are always on the same directory,
    reusing ``urls.txt`` (deleting and reediting the contents).

.. dword:: tocfile

    It is the ``toc`` version of `ufile <#dword-ufile>`__.

    It is generated automatically in current directory,
    when action is ``toc``,
    and processed automatically when ``convert``.

    The filename is determined from ``--file`` input (basename part),
    adding '-toc' suffix before extension. e.g. ``urls-toc.txt``.

    see `TOC <topics.html#toc>`__ for details.

.. dword:: userdir

    user configuration directory is specified
    by environment variable: ``TOSIXINCH_USERDIR``.
    For example::

        export TOSIXINCH_USERDIR=~/etc/tosixinch  # (in ~/.bashrc)

    Reloading files or rebooting system might be needed.
    For example::

          $ source ~/.bashrc

    If the script cannot find the variable,
    a basic search is done for the most common configuration directories
    (in the same order below for each OS).

    Windows:

    .. code-block:: none

        C:\Users\<username>\AppData\Roaming\tosixinch
        C:\Users\<username>\AppData\Local\tosixinch
        C:\Documents and Settings\<username>\Local Settings\Application Data\tosixinch
        C:\Documents and Settings\<username>\Application Data\tosixinch

    Mac:

    .. code-block:: none

        ~/Library/Application Support/tosixinch

    Others:

    .. code-block:: none

        $XDG_CONFIG_HOME/tosixinch
        ~/.config/tosixinch

    (So, if this is OK for you, you don't have to create the environment variable).

    If this also fails, no user directory is set,
    and just default application config and sample site config are read.

    If commandline argument ``--userdir`` is given, it overrides all the above.

.. dword:: tosixinch.ini

    if there are files that glob match ``tosixinch*.ini`` in ``userdir``,
    it reads all of them in alphabetical order,
    and sets application settings accordingly.

.. dword:: site.ini

    if there are files that glob match ``site*.ini`` in ``userdir``,
    it reads all of them in alphabetical order,
    and sets site specific settings accordingly.

.. dword:: css directory

    ``userdir`` should have ``css`` sub directory. For example ::

        ~/.config/tosixinch/css

.. dword:: css files

    The script searches css files (``'*.css'``) in ``css directory`` when ``convert``.
    ``prince`` and ``weasyprint`` require css files.
    Other converters may not need them depending on the configuration.

    Each file name must be specified for each converter
    in ``tosixinch.ini`` (see option `css <options.html#confopt-css>`__.

    By default, the script uses ``sample.css`` for all converters.
    It is generated from the template ``sample.t.css`` (see below).

.. dword:: css template files

    If css file names match ``'*.t.css'``,
    they are rendered by a template engine
    `templite.py <topics.html#script-templite.py>`__ (included).

    (for the syntax and values, see `CSS Template Values <#css-template-values>`__).

    When ``convert``, the script always renders them,
    and resultant ``css files`` are placed in ``css directory``,
    overwriting older one, if any.

    The css filenames are made by stripping ``'.t'`` from the template.
    (For example, ``sample.t.css`` generates ``sample.css``.)

.. dword:: process directory

    ``userdir`` can also have 'process' sub directory. For example ::

        ~/.config/tosixinch/process

.. dword:: process files

    When Action is ``extract``,
    you can apply arbitrary functions to the html DOM elements,
    before writing to ``Extracted_File``.

    (For the details, see `process option <options.html#confopt-process>`__).

    The script searches process functions in python files (``'*.py'``)
    in ``process directory``.

    If it cannot find the one,
    it searches next in application's ``tosixinch.process`` directory.

.. dword:: dprocess directory

    ``userdir`` can also have 'dprocess' sub directory.

    (See `dprocess <options.html#confopt-dprocess>`__).

.. dword:: script directory

    ``userdir`` can also have 'script' sub directory.
    (For user hooks commands.

    See `Hookcmds <topics.html#hookcmds>`__ and `Scripts <topics.html#scripts>`__).


Config Format
-------------

Configuration files are parsed by a customized version of
`configparser <https://docs.python.org/3/library/configparser.html>`__
(Python standard library).
So in general, the syntax follows it. ::

    [section]
    option=         value
    more_option=    more value


Comment
^^^^^^^

Comment markers are ``'#'`` or ``';'``, in the first non-whitespace column.
Inline comments are not possible.

But if option function is `[CMD] <#dword-CMD>`__, it is parsed by
`shlex <https://docs.python.org/3/library/shlex.html>`__
(Python standard library),
so *in the option value*, you can use inline comments
(only ``'#'`` character). For example:

.. code-block:: ini

    [section]
    command= find . -name '*.py' # TODO: more suitable command example

``ConfigParser`` reads the entire line after ``'='``,
but it is passed to ``shlex``, and it strips ``'#'`` and after.

Structure
^^^^^^^^^

There are two types of configuration files.

* ``tosixinch.ini`` (application config)
* ``site.ini`` (sites configs).

``tosixinch.ini`` consists of three types of sections.

* ``general``
* ``style``
* each converter sections
  (``prince``, ``weasyprint``, and ``wkhtmltopdf``).

``site.ini`` consists of sections for each specific website,
and they all have the same options.

``site.ini`` has some common options as ``tosixinch.ini``,
and overrides the latter values if specified.

``commandline`` also has some common options as ``tosixinch.ini``,
and overrides ``site.ini`` and ``tosixinch.ini``  values if specified.

Common ``commandline`` options are made
by adding ``'--'`` and  changing ``'_'`` to ``'-'``.
For example, config option ``user_agent`` becomes ``--user-agent``.

Section Inheritance
^^^^^^^^^^^^^^^^^^^

In ``site.ini``, you can use simple section inheritance syntax.

``' : '`` in section names is specially handled,
so that ``[aa : bb]`` means ``[aa]``,
but falls back to ``[bb]``. For example::

    [aa : bb]
    x=aaa
    [bb]
    x=bbb
    y=bbb

In this config, ``aa.x`` is ``aaa``, and ``aa.y`` is ``bbb``.

``aa`` doesn't have ``y`` option,
so it searches the parent section (``bb``).

(If even the parent section doesn't have the option,
then it falls back to ordinary mechanism.
(``DEFAULT`` section search or ``NoOptionError``).

It is to omit duplicate options.
For example, wiki pages of mobileread.com use the same layout
as wikipedia.org.
So the options for the script are also the same,
and you don't have to write.
(other than ``match``). ::

    [wikipedia]
    match=      ...
    select=     ...
    exclude=    ...
    ...

::

    [mobileread : wikipedia]
    match=      http://wiki.mobileread.com/wiki/*


Value Functions
^^^^^^^^^^^^^^^

Each option value field has predetermined transformation rules.
Users have to fill the value accordingly, if setting.

.. dword:: None

    If nothing is specified, it is an ordinary ``ConfigParser`` value.
    String value as you write it. Leading and ending spaces are stripped.
    Newlines are preserved if indented.

.. dword:: BOOL

    ``'1'``, ``'yes'``, ``'true'`` and ``'on'`` are interpreted as ``True``.

    ``'0'``, ``'no'``, ``'false'`` and ``'off'`` are interpreted as ``False``.

    ``''`` is interpreted as ``None``
    (the same as ``False`` in many contexts. Normally do not use it. ).

    It accepts only one of the nine (case insensitive).

.. dword:: COMMA

    Values are comma separated list. For example::

        [section]
        ...
        comma_option=   one, two, three

    Leading and ending spaces and newlines are stripped.
    So the value is a list of ``'one'``, ``'two'`` and ``'three'``.
    Single value with no commas is OK.

.. dword:: LINE

    Values are line separated list. For example::

        [section]
        ...
        line_option=    one
                        two, three
                        four five,

    Leading and ending spaces and *commas* are stripped.
    So the value is a list of ``'one'``, ``'two, three'`` and ``'four five'``.
    Single line with no newlines is OK.

.. dword:: CMD

    Value is for a commandline string.
    You write value string as you would write in the shell.
    So words with spaces need quotes, and special characters need escapes.

.. dword:: CMDS

    Like CMD, but accept a list as input (newline separated as ``LINE``).
    The value is one or more lines of commandline ready strings.

.. dword:: PLUS

    Values are comma separated list as ``COMMA``,
    and add to or subtract from some default values.
    If first character of an item is ``'+'``,
    it is a ``plus item``.
    If ``'-'``, it is a ``minus item``.

    For example, if initial value is ``'one, two, three'``::

        +four                ->  (one, two, three, four)
        -two, -three, +five  ->  (one, four, five)

    If already added or no items to subtract, it does nothing. ::

        +one, -six           ->  (one, four, five)


    As a special case,
    if all items are neither ``plus item`` nor ``minus item``,
    the list itself overwrites previous value. ::

        six, seven           ->  (six, seven)

    So items must be either
    some combination of ``plus items`` and ``minus items``,
    or none of them.
    Mixing these raises Error.

    You can pass ``minus item`` in the same way in commandline.
    The script can parse these a bit confusing arguments.
    (leading single dash is also a short optional argument marker) ::

        ... --plus-option -one

    Multiple items in commandline should be quoted. ::

        ... --plus-option '-two, -three, +four'


CSS Template Values
-------------------

In ``css template files``,
you can look up option values in `style <options.html#style>`__ section.

Syntax
^^^^^^

``{{ option }}`` is replaced with ``value``.

For example, ``{{ font_size }}`` becomes ``9px``.

Conditional block ``{% if option %} ... {% endif %}``
is rendered if the ``option`` is evaluated to ``True``
(not ``None``, ``False``, ``0``, ``''``, or ``[]``).

For example, you can write ``prince`` specific css rules
inside ``{% if prince %} ... {% endif %}`` block.

For the details,
see the docstring of the code `Templite <api.html#tosixinch.templite.Templite>`__
(by Ned and others).

Values
^^^^^^

``size`` variable is added.
It is automatically set from either
`portrait_size <options.html#confopt-portrait_size>`__
or `landscape_size <options.html#confopt-landscape_size>`__,
according to the value of
`orientation <options.html#confopt-orientation>`__.

``width`` and ``height`` variables are made from ``size``.

``font_scale`` option is made into ``scale`` function.
Use it like ``{{ font_serif|scale }}``.

``percent80``, ``percent81`` ... ``percent99`` functions are added.
Use it like ``{{ height|percent98 }}`` (98 % of the height length).
It is OK if the previous value, here ``height``, includes units like ``px`` or ``mm``.

Bool variables ``prince``, ``weasyprint`` and ``wkhtmltopdf``
are added.
They are ``True`` or ``False``
according to the currently selected converter.

`toc_depth <options.html#confopt-toc_depth>`__ is transformed to variables
``bm1``, ``bm2``, ``bm3``, ``bm4``, ``bm5`` and ``bm6``.
For example, if ``toc_depth`` is ``3``,
they are ``1``, ``2``, ``3``, ``none``, ``none`` and ``none``.

In ``sample.t.css``, it is used like::

    h1 { prince-bookmark-level: {{ bm1 }} }
    h2 { prince-bookmark-level: {{ bm2 }} }
    h3 { prince-bookmark-level: {{ bm3 }} }
    h4 { prince-bookmark-level: {{ bm4 }} }
    ...


lxml.html.HtmlElement
---------------------

The program uses a lightly customized version of ``lxml.html.HtmlElement``,
which means mainly two things.

* You can use a custom XPath syntax, ``double equals``.
* When XPath string is invalid, it prints out a bit more helpful error message.

Double Equals
^^^^^^^^^^^^^

When using XPath,
it is inconvenient to select elements from class attributes.

For example, if you want to select ``<div class="aa bb cc">`` using ``'aa'``,
you cannot simply write ``'@class="aa"'``
(XPath sees ``'aa'`` as literal strings,
and ``'aa bb cc'`` and ``'aa'`` are different strings).

So you have to write::

    div[contains(concat(" ", normalize-space(@class), " "), " aa ")]

(See e.g. `When selecting by class, be as specific as necessary <https://blog.scrapinghub.com/2014/07/17/xpath-tips-from-the-web-scraping-trenches>`__,
for explanations.)

To ease this, the program introduces a custom syntax ``double equals`` (``'=='``).

In configuration options supposing XPath strings,
or arguments in ``.xpath()`` method in user python modules,

if the string matches:

.. code-block:: none

    <tag>[@class==<value>]

    in which
    <tag> is some tag name or '*'
    <value> is some value with optional quotes (' or ")

It is rewritten to:

.. code-block:: none

    <tag>[contains(concat(" ", normalize-space(@class), " "), " <value> ")]'

So you can write e.g.:

.. code-block:: ini

    [somesite]
    ...
    select=     //div[@class=="aa"]

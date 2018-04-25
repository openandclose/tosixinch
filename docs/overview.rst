
Overview
========

Actions
-------

The script consists of several, independent actions (subcommands).

The most common ones are:

**download**
    Read input ``url``, download, and save as ``Downloaded File``.

    If ``Downloaded File`` already exists, it does nothing.
    So if you want to download again,
    you have to search and delete the ``Downloaded File`` manually.

    If ``url`` is a local filepath, it also does nothing.
    ``Downloaded FIle`` is the same as ``url``.

    As a special case, if all ``url`` input is directory or directories,
    it just prints out files in them,
    ignoring some files according to settings.
    (It is intended to get files list in the local source repository,
    ignoring ``/.git/``, ``/docs/`` or ``*.jpg``  etc.).
    
    Otherwise, mixing directories and files in ``urls`` raises Error.

    Commandline: ``--download`` or ``-1``

**extract**
    Open ``Downloaded File``,
    process it some way or other to make it fit for conversion,
    and generate ``Extracted Flle``.
    (``Downloaded FIle`` is kept intact).

    It always runs, overwriting existing ``Extracted File`` if any.

    (If ``url`` is local filepath, ``Downloaded File`` is not created,
    but ``Extracted FIle`` *is* created).

    Commandline: ``--extract`` or ``-2``

**convert**
    Open ``Extracted File``, convert, and generate ``PDF file``.
    (``Extracted FIle`` is kept intact).

    It always runs, overwriting existing ``PDF File`` if any.

    Commandline: ``--convert`` or ``-3``

They can be concatenated in invocation,
so the next three commands and single command are the same::

    tosixinch -1
    tosixinch -2
    tosixinch -3

    tosixinch -123

(You can also do ``'-23'``,
but ``download`` does nothing if already done once,
so ``'-23'`` and ``'-123'`` are the same the second time and after).


Target Files
------------

The point of the script is that you don't have to designate
each input and output for each consecutive action.
For this, given ``url``, target file's names are uniquely determined.

All generated html files are
in ``_htmls`` folder in current directory (created if necessary).

Generated *pdf* file is placed under current directory.

Usually users don't have to care about these files' details.
But disposing of the files (deleting or moving) is users' job.

**url**
    Input file location. URL or local filepath.
    File url (``file://..``) is currently not supported.

    Example::

        https://en.wikipedia.org/wiki/Xpath

**Downloaded FIle**
    If ``url`` is a remote one,
    ``Downloaded File`` is created inside ``_htmls`` directory,
    with URL ``domain`` and ``paths`` as subdirectories.

    If ``url``'s last ``path`` doesn't have file extension,
    string ``'/index--tosixinch'`` is added.
    If it ends with ``'/'``, ``'index--tosixinch'`` is added.

    .. note::
        Recent servers use extensively no-extension urls with or without a slash,
        and that causes trouble to filepath conversion.
        (Because filepath cannot have the same name both for file and directory).
        This is the reason for this rather verbose name changing.

    In Windows, illigal filename characters (``':?*\"<>```) in ``url`` are
    all changed to ``'_'``.
    So name conflict may occur in rare cases.

    In Unixes, these special characters are used in filenames as is.

    Example::

        ~/Download/tosixinch/_htmls/en.wikipedia.org/wiki/Xpath/index--tosixinch

**Extracted File**
    String ``'--extracted'`` and ``'.html'`` (If not already have one)
    is added to ``Downloaded FIle``.
    
    If ``url`` is local filepath,
    The path of ``Extracted FIle`` is determined
    roughly by the same process as ``Downloaded File``.

    Example::

        ~/Download/tosixinch/_htmls/en.wikipedia.org/wiki/Xpath/index--tosixinch--extracted.html

**PDF File**
    If input consists of single ``url``,
    The filename is created from ``url``'s last ``path``.
    If not, it is created from the section name of first ``url``.

    Example::

        ~/Download/tosixinch/Xpath.pdf (from single input)
        ~/Download/tosixinch/wikipedia.pdf (from multiple input)

    If multiple input includes multiple domains,
    the filename of the pdf named after first domain may not be what you want.


Config Files
------------

**urls.txt**
    It is default name for ``--file``,
    and used when no other file or input ``url`` is specified.

    ``urls`` are read from this file in current directory.

    The file's syntax is:

        * Each line is interpreted as ``url`` string.

        * If a line starts with ``'#'`` or ``';'``,  the line is ignored.

        * In special case, when action is ``toc``,
          a line starting with ``'#'`` is interpreted as a chapter.
          So only ``';'`` can be used as comment character.

**\*-toc.txt**
    It is generated automatically when action ``toc`` is invoked,
    and parsed automatically when ``convert``.

    The filename is determined from ``--file``.
    ``urls-toc.txt``, for example.

**userdir**
    user configuration directory is specified
    by environment variable: ``TOSIXINCH_USERDIR``.
    For example::

        export TOSIXINCH_USERDIR=~/.config/tosixinch (in .bashrc)

    Reloading files or system might be needed.
    For example::

         $ source ~/.bashrc 

    Failing this,
    a basic search is done for the most common configuration directories.

    Windows:
        | ``C:\Users\<username>\AppData\Roaming\tosixinch``
        | ``C:\Users\<username>\AppData\Local\tosixinch``
        | ``C:\Documents and Settings\<username>\Local Settings\Application Data\tosixinch``
        | ``C:\Documents and Settings\<username>\Application Data\tosixinch``
    Mac:
        | ``~/Library/Application Support/tosixinch``
    Others:
        | ``$XDG_CONFIG_HOME/tosixinch``
        | ``~/.config/tosixinch``

    (So, in this case, you don't need the environment variable).

    Failing this, no user directory is set,
    and just default application config and sample site config are read.
    (In this state, the script is not very useful).

    If commandline argument ``--userdir`` is given, it overwrites all the above.

**tosixinch.ini**
    if there are files that glob match ``tosixinch*.ini`` in ``userdir``,
    it reads all of them in alphabetical order,
    and sets application settings accordingly.

**site.ini**
    if there are files that glob match ``site*.ini`` in ``userdir``,
    it reads all of them in alphabetical order,
    and sets site specific settings accordingly.

    Each section in them has ``match`` option,
    and it is used as glob string to match input urls.
    Section names can be arbitrary e.g.::

        [wikipedia]
        match=      https://*.wikipedia.org/wiki/

    Last asterisk can be omitted, so the following two lines make no deference. ::

        match=      https://*.wikipedia.org/wiki/*
        match=      https://*.wikipedia.org/wiki/

**css directory**
    ``userdir`` should have ``css`` subdirectory. For example ::
    
        ~/.config/tosixinch/css

**\*.css**
    It reads css files in ``css directory`` when ``convert``.
    ``prince`` and ``weasyprint`` require the files.
    Other converters may not need them depending on your config.

    Each file name must be specified for each converter
    in ``tosixinch.ini``.

**\*.t.css**
    If css file names match ``'*.t.css'``,
    they are interpreted as css ``template`` files
    for ``templite.py`` (See `Vendored libraries <#vendored-libraries>`__).

    When ``convert``, It always runs,
    and rendered css file is placed in ``css directory``,
    stripping ``'.t'`` from the template filename.
    (For example, ``my.t.css`` generates ``my.css``,
    always overwriting older one).

    The script includes ``sample.t.css`` file.
    It is used by default, for all converters.

    The syntax is:

        * The dictionary to pass to ``templite.py`` is made from option values
          in ``style`` section in ``tosixinch.ini``.

        * ``size`` variable is added.
          It is either ``portrait_size`` or ``landscape_size``,
          according to the value of ``orientation``.

        * Bool variables ``prince``, ``weasyprint``, ``wkhtmltopdf``
          and ``ebook-convert`` are added.
          They are ``True`` or ``False``
          according to the currently selected converter.

        * ``toc_depth`` is transformed to variables
          ``bm1``, ``bm2``, ``bm3``, ``bm4``, ``bm5`` and ``bm6``.
          For example, if ``toc_depth`` is ``3``,
          they are ``1``, ``2``, ``3``, ``none``, ``none`` and ``none``.

        * ``'{{ option }}'`` is replaced with ``'value'``,
          for example, ``'{{ font_size }}'`` becomes ``'9px'``.

        * Conditional block ``'{% if prince %} ... {% endif %}'`` can be used
          for converter specific css.

        * For the details,
          see the docstring of class `Templite <api.html#tosixinch.templite.Templite>`__
          (by Ned and others).
          But it seems you can't use much of them here.


**userprocess directory**
    ``userdir`` can also have ``userprocess`` subdirectory.

**\*.py**
    When ``extract``, arbitrary ``process`` functions can be called
    after ``select`` and ``exclude``.

    The script searches first in ``userprocess`` directory, 
    then in application's ``process`` directory,
    and first found one is used.
    So, name conflict should be avoided.

    Already taken names are::

        gen.py
        site.py
        util.py

    Other names are free to choose, but ``user*.py`` is recommended.
    (Builtin process files may increase.)


Config Format
-------------

Configuration files are parsed by a customized version of
`configparser library <https://docs.python.org/3/library/configparser.html>`__.
So in general, the syntax follows it. ::

    [section]
    option=         value
    more_option=    more value

Comment
^^^^^^^

Comment markers are ``'#'`` or ``';'`` in the first non-whitespace column.
Inline comments are not possible.

But if option function is ``[CMD]``, it is parsed by
`shlex library <https://docs.python.org/3/library/shlex.html>`__,
so *in the option value*, you can use inline comments
(only ``'#'`` character). For example::

    [section]
    command_string= find . -name '*.py' # TODO: more suitable command example

``ConfigParser`` reads the entire line, but it is passed to ``shlex``,
and it ignores ``'#'`` and after.

Structure
^^^^^^^^^

There are two types of configuration files.
``tosixinch.ini`` (application config)
and ``site.ini'`` (sites configs).

``tosixinch.ini`` consists of three types of sections,
``general``, ``style`` and each converter sections
(``prince``, ``weasyprint``, ``wkhtmltopdf`` and ``ebook-convert``).

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
but if the option is not in ``[aa]``, look up also ``[bb]``. For example::

    [aa : bb]
    x=aaa
    [bb]
    x=bbb
    y=bbb

In this config, ``x`` option of section ``[aa]`` is ``aaa``,
and ``y`` is ``bbb``.

In ``site.sample.ini``,
the section of ``mobileread.com`` wiki pages is just::

    [mobileread : wikipedia]
    match=      http://wiki.mobileread.com/wiki

because they use the same layout,
you can omit other options
(they are the same as wikipedia options, ``select``, ``exclude`` etc.).


Value Functions
---------------

Each option value field has predetermined transformation syntax.
Users have to fill the value accordingly, when setting.

**None**
    If nothing is specified, it is an ordinary ``ConfigParser`` value.
    String value as you write it. Leading and ending spaces are stripped.
    Newlines are preserved if indented.

**BOOL**
    ``'1'``, ``'yes'``, ``'true'`` and ``'on'`` are interpreted as ``'True'``.
    ``'0'``, ``'no'``, ``'false'`` and ``'off'`` are interpreted as ``'False'``.
    It accepts only one of the eight (case insensitive).

**COMMA**
    Values are comma separated list. For example::
    
        [section]
        ...    
        comma_option=   one, two, three

    Leading and ending spaces and newlines are stripped.
    So value is a list of ``'one'``, ``'two'`` and ``'three'``.
    Single value with no commas is OK.

**LINE**
    Values are line separated list. For example::

        [section]
        ...
        line_option=    one
                        two, three
                        four five,

    Leading and ending spaces and commas are stripped.
    So value is a list of ``'one'``, ``'two, three'`` and ``'four five'``.
    Single line with no newlines is OK.

**CMD**
    Value is a commandline string.
    You write value string as you would write in the shell.
    So words with spaces need quotes, and special characters need escapes.

**PLUS**
    Values are comma separated list,
    and add to or subtract from some default value.
    If first character of an item is ``'+'``,
    it is a ``plus item``.
    If ``'-'``, it is a ``minus item``.
    
    For example, if initial value is ``'one, two, three'``::

        +four                   (one, two, three, four)
        -two, -three, +five     (one, four, five)

    If already added or no items to subtract, it does nothing. ::

        +one, -six              (one, four, five)


    As a special case,
    if all items are neither ``plus item`` nor ``minus item``,
    the list itself overwrites previous value. ::

        six, seven              (six, seven)

    So items must be either
    some combination of ``plus item`` and ``minus item``,
    or none of them.
    Mixing these raises Error.

    You can pass ``minus item`` in the same way in commandline
    (with a little customization of ``argparse``)::

        ... --plus-option -one
        ... --plus-option '-two, -three, +four'


**XPATH**
    some values are interpreted as xpath,
    in most cases, ``[LINE]`` is also specified.

    One custom syntax, *double equals* (``'=='``) is added.
    If the string matches:

    .. code-block:: none

        <tag>[@class==<value>]

        in which
        <tag> is some tag name or '*'
        <value> is some value with optional quotes (' or ")

    It is rewritten to:

    .. code-block:: none

        <tag>[contains(concat(" ", normalize-space(@class), " "), " <value> ")]'

    For example, if you want to select 
    ``div`` elements whose class attribute includes ``'aa'``,
    you can write:

    .. code-block:: none

        //div[@class=="aa"]

    And it also selects ``div`` elements with ``class`` value ``'aa bb cc'``.

    .. note::

        This is one inconvenient point of xpath, compared to css selector.

        * You cannot select ``'aa bb cc'`` by ``'@class="aa"'``.

        * You can select it by ``'contains(@class, "aa")'``,
          but it also selects values
          which just *contains* the string, ``'aaa'``, ``'aaxxx'`` etc..

        * You can more wisely select it by ``'contains(@class, "aa ")'`` (with space),
          but the existence of space is not so certain.

        `Scrapy document <https://docs.scrapy.org/en/latest/topics/selectors.html#when-querying-by-class-consider-using-css>`__
        has a little longer explanation.


Other Magic Words
-----------------

**tsi-keep-style**
    When you add ``style`` attributes to some elements
    in your custom ``userprocess`` functions,
    also add this value to the ``class`` attribute.
    All ``style`` attributes without this ``class`` value are
    removed in ``clean`` method in ``extract``. ::

        # removed (becomes just '<div>')
        <div style="font-weight:bold;">

        # not removed
        <div class="tsi-keep-style other-values" style="font-weight:bold;">

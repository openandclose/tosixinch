
Config Options
==============

.. note ::

    ``Default Value`` is designated by parenthesis in the first lines.

    `Value Function <overview.html#value-functions>`__
    is designated by bracket in the first lines.

tosixinch.ini
-------------

.. note ::

    Options with star ``*`` are common options with `site.ini <#site-ini>`__.
    You can use them to override application-wide configuration.

General Section
^^^^^^^^^^^^^^^

.. confopt:: downloader

    (``urllib``)

    Designate default downloader. Currently only ``urllib``.

.. confopt:: extractor

    (``lxml``)

    Designate default extractor.
    Either ``lxml`` (recommended) or ``readability``.

    The intended use case of ``readability`` is
    from commandline.
    Either `--readability <commandline.html#cmdoption-readability>`__
    or `--readability-only <commandline.html#cmdoption-readability-only>`__.

.. confopt:: converter

    (``prince``)

    Designate default converter.
    One of ``prince``, ``weasyprint``, ``wkhtmltopdf``
    or ``ebook-convert``.

.. confopt:: user_agent \*

    (some arbitrary browser user agent.
    run ``'tosixinch -a'`` to actually see.)

    Designate user agent for downloader (only for ``urllib``).

.. confopt:: qt \*

    (``webkit``)

    Designate rendering engine when using ``qt``.
    Either ``webkit`` or ``webengine``.
    ``webengine`` is a newer one,
    and newer functionalities are not used in this script.

.. confopt:: encoding \*

    | (``utf-8, utf-8-variants, latin_1, cp1252``)
    | ``[COMMA]``

    Specify preferred encodings in order.
    First successful one is used.
    Encoding names are as specified in
    `codecs library <https://docs.python.org/3/library/codecs.html#standard-encodings>`__,
    and ``ftfy`` and ``chardet`` if they are installed.

    `ftfy <https://ftfy.readthedocs.io/en/latest/>`__
    is a library to fix bad unicode stirings.
    A use case here is to aggressively interpret text as UTF-8,
    by injecting it before false-positives.

    E.g. many 'mojibake' in English pages
    result in legal latin-1 character codes.
    General encode detection capabilities can't handle this,
    because they (rightly) decide them as latin-1.
    ``ftfy`` decides preferentially for UTF-8,
    and checks the possibilities of UTF-8 mojibakes.

    `chardet <https://chardet.readthedocs.io/en/latest/index.html>`__
    is a popular encode detection library.
    It can be used as a last resort.

    An example::

        utf-8, utf-8-variants, ftfy, latin_1, cp1252, chardet

.. confopt:: parts_download \*

    | (``True``)
    | ``[BOOL]``

    Web pages may have some component content.
    Most important ones are images,
    and currently the script only concerns images
    (in html tag ``<img src=...>``).
    The value designate whether it downloads these components
    when ``extract``.

    Note downloading may occur anyway by pdf converters.

    If this option is ``True``,
    download links are rewritten to point to local ``Downloaded_Files``.
    So downloading doesn't happen when ``convert``.

    In general, pre-downloading is useful
    for multiple trials and layout checking.

    If `force_download <#confopt-force_download>`__ is ``False`` (default),
    the script skips downloading if the file already exists.

    TODO:
        So the script does nothing about ``iframe`` inline sources.
        Downloading and rendering are done by converters,
        but we can't apply our css rules
        (They are defferent domains).

.. confopt:: full_image \*

    (``200``)

    If width or height of component pixel size is equal or above this value,
    class attribute ``tsi-big`` or ``tsi-tall`` is added to the image tag,
    ``tsi-big`` if width is longer than height, ``tsi-tall`` if the opposite.
    'tsi' is short for 'tosixinch'.

    By itself, it does nothing. However, In ``sample.css``,
    it is used to make midium sized images expand almost full display size,
    with small images (icon, logo, etc.) as is.
    The layout gets a bit uglier,
    but I think it is necessary for small e-reader displays.

.. confopt:: add_binaries \*

    (``3ds`` ``3g2`` ``3gp`` ``7z`` ``a`` ``aac`` ``adp`` ``ai`` ``aif`` ``aiff``
    ``alz`` ``ape`` ``apk`` ``ar`` ``arj`` ``asf`` ``au`` ``avi`` ``bak`` ``bh``
    ``bin`` ``bk`` ``bmp`` ``btif`` ``bz2`` ``bzip2`` ``cab`` ``caf`` ``cgm``
    ``class`` ``cmx`` ``cpio`` ``cr2`` ``csv`` ``cur`` ``dat`` ``deb`` ``dex``
    ``djvu`` ``dll`` ``dmg`` ``dng`` ``doc`` ``docm`` ``docx`` ``dot`` ``dotm``
    ``dra`` ``DS_Store`` ``dsk`` ``dts`` ``dtshd`` ``dvb`` ``dwg`` ``dxf``
    ``ecelp4800`` ``ecelp7470`` ``ecelp9600`` ``egg`` ``eol`` ``eot`` ``epub``
    ``exe`` ``f4v`` ``fbs`` ``fh`` ``fla`` ``flac`` ``fli`` ``flv`` ``fpx``
    ``fst`` ``fvt`` ``g3`` ``gif`` ``graffle`` ``gz`` ``gzip`` ``h261`` ``h263``
    ``h264`` ``ico`` ``ief`` ``img`` ``ipa`` ``iso`` ``jar`` ``jpeg`` ``jpg``
    ``jpgv`` ``jpm`` ``jxr`` ``key`` ``ktx`` ``lha`` ``lvp`` ``lz`` ``lzh``
    ``lzma`` ``lzo`` ``m3u`` ``m4a`` ``m4v`` ``mar`` ``mdi`` ``mht`` ``mid``
    ``midi`` ``mj2`` ``mka`` ``mkv`` ``mmr`` ``mng`` ``mobi`` ``mov`` ``movie``
    ``mp3`` ``mp4`` ``mp4a`` ``mpeg`` ``mpg`` ``mpga`` ``mxu`` ``nef`` ``npx``
    ``numbers`` ``o`` ``oga`` ``ogg`` ``ogv`` ``otf`` ``pages`` ``pbm`` ``pcx``
    ``pdf`` ``pea`` ``pgm`` ``pic`` ``png`` ``pnm`` ``pot`` ``potm`` ``potx``
    ``ppa`` ``ppam`` ``ppm`` ``pps`` ``ppsm`` ``ppsx`` ``ppt`` ``pptm`` ``pptx``
    ``psd`` ``pya`` ``pyc`` ``pyo`` ``pyv`` ``qt`` ``rar`` ``ras`` ``raw`` ``rgb``
    ``rip`` ``rlc`` ``rmf`` ``rmvb`` ``rtf`` ``rz`` ``s3m`` ``s7z`` ``scpt``
    ``sgi`` ``shar`` ``sil`` ``sketch`` ``slk`` ``smv`` ``so`` ``sub`` ``swf``
    ``tar`` ``tbz`` ``tbz2`` ``tga`` ``tgz`` ``thmx`` ``tif`` ``tiff`` ``tlz``
    ``ttc`` ``ttf`` ``txz`` ``udf`` ``uvh`` ``uvi`` ``uvm`` ``uvp`` ``uvs``
    ``uvu`` ``viv`` ``vob`` ``war`` ``wav`` ``wax`` ``wbmp`` ``wdp`` ``weba``
    ``webm`` ``webp`` ``whl`` ``wim`` ``wm`` ``wma`` ``wmv`` ``wmx`` ``woff``
    ``woff2`` ``wvx`` ``xbm`` ``xif`` ``xla`` ``xlam`` ``xls`` ``xlsb`` ``xlsm``
    ``xlsx`` ``xlt`` ``xltm`` ``xltx`` ``xm`` ``xmind`` ``xpi`` ``xpm`` ``xwd``
    ``xz`` ``z`` ``zip`` ``zipx``)

    ``[PLUS]``

    The script ignores ``urls`` with binary like looking extensions,
    only when multiple ``urls`` are provided.

    This option value adds to or subtracts from
    the default ``add_binaries`` list above.

    The list is taken from Sindre Sorhus'
    `binary-extensions <https://github.com/sindresorhus/binary-extensions>`__.

    This is for user convenience. If you copy and paste many urls,
    checking strange exxtensions is a bit of work.
    But I'm afraid sometimes it gets in the way.

.. confopt:: add_tags \*

    | (None)
    | ``[PLUS]``

    After ``select``, ``exculde`` and ``process`` in ``extract``,
    the script ``clean`` s the resultant html.

    The tags in this option are stripped.
    The current default is none.

.. confopt:: add_attrs \*

    | (``color, width, height``)
    | ``[PLUS]``

    After ``select``, ``exculde`` and ``process`` in ``extract``,
    the script ``clean`` s the resultant html.

    The attributes in this option are stripped.
    The current default is color, width and height.

    Most e-readers are black and white.
    Colors just make fonts harder to read.

    Width and height conflict with user css rules.

.. confopt:: guess

    | (``//div[@itemprop="articleBody"]``
    | ``//div[@id="main"]``
    | ``//div[@id="content"]``
    | ``//div[@class=="body"]``)

    ``[LINE][XPATH]``

    If ``url`` doesn't `match <#confopt-match>`__ any site in ``site.ini``,
    ``select`` is done according to this value.

    The procedure is differet from ordinary ``select``
    (with a little bit of extra precaution).

    * The xpaths in this value are searched in order.
    * If match is found and match is a single element
      (not multiple occurences),
      the script ``select`` s the xpath.

.. confopt:: raw

    | (``False``)
    | ``[BOOL]``

    If ``True``,
    ``url`` is used as input *as is* when ``convert``.
    In this case, ``url`` must be local filepath.

    The intended use case is
    to pass some non-html input to versatile ``ebook-convert``.
    For example::

        tosixinch -i somebook.mobi -3 --raw --ebook-convert

    generates ``somebook.pdf``.

.. confopt:: force_download \*

    | (``False``)
    | ``[BOOL]``

    By default, The script does not download the same files again.

    If this options is ``True``:

    In case of ``-1``,
    it (re-) downloads ``url`` even if ``Downloaded_File`` exists.

    In case of ``-2``,
    it (re-) downloads component files (images etc.)
    even if they exist.

.. confopt:: use_sample

    | (``True``)
    | ``[BOOL]``

    The value specifies whether site config includes ``site.sample.ini``.
    see `Samples <intro.html#samples>`__.

.. confopt:: preprocess \*

    | (``gen.add_title, gen.youtube_video_to_thumbnail``)
    | ``[COMMA]``

    Before site specific ``process`` functions,
    the script applies default ``process`` functions to all ``url``,
    according to this value.

    The syntax is the same as `process <#confopt-process>`__ option, in ``site.ini``.

    About default functions:

        * ``add_title``: If there is no ``<h1>``,
          make ``<h1>`` tag from ``<title>`` tag text.
          It is to help make pdf bookmarks (TOC).
        * ``youtube_video_to_thumbnail``: Change embedded youtube video object
          to thumbnail image.

.. confopt:: textwidth

    (``65``)

    Set physical line length for ``nonprose`` texts.

    See `nonprose <topics.html#non-prose>`__.

.. confopt:: textindent

    (``'                    --> '``)

    Set logical line continuation marker for ``nonprose`` texts.

    See `nonprose <topics.html#non-prose>`__.

    ``ConfigParser`` strips leading and ending whitespaces.
    So if you want actual whitespaces, quote them as the default does.
    Quotes are stripped by the script in turn.

.. confopt:: textcss

    ()

    Not used.

.. confopt:: add_filters

    | (``/\.git/, /docs?/, /.+\.egg-info/``)
    | ``[PLUS]``

    If ``url`` is directory or they are all directories,
    the script just print out files in that directory or directories,
    excluding matched files and sub directories
    in this value.

    Each item is some python regular expression.

    Printing out also considers `add_binaries <#confopt-add_binaries>`__ option,
    and ignores some extinsion files accordingly.

---

.. note ::

    For ``hookcmds`` (``precmd*``, ``postcmd*`` and ``viewcmd``),
    see `Hookcmds <overview.html#hookcmds>`__.

.. confopt:: precmd1

    | (None)
    | ``[CMD]``

    Run arbitrary shell command before ``download``.

.. confopt:: postcmd1

    | (None)
    | ``[CMD]``

    Run arbitrary shell command after ``download``.

.. confopt:: precmd2

    | (None)
    | ``[CMD]``

    Run arbitrary shell command before ``extract``.

.. confopt:: postcmd2

    | (None)
    | ``[CMD]``

    Run arbitrary shell command after ``extract``.

.. confopt:: precmd3

    | (None)
    | ``[CMD]``

    Run arbitrary shell command before ``convert``.

.. confopt:: postcmd3

    | (None)
    | ``[CMD]``

    Run arbitrary shell command after ``convert``.

.. confopt:: viewcmd

    | (None)
    | ``[CMD]``

    Run arbitrary shell command
    when specified in commandline options (``-4`` or ``--view``).


Style Section
^^^^^^^^^^^^^

The options in style section are used for
`css template files <overview.html#dword-css_template_files>`__.

Note that users can always choose (static) ``css files``
rather than ``css template files``.
In that case, the style options have no effect.

So, the options themselves have no meaning.
In the following, the roles in the sample file
(``sample.t.css``) are explained.

.. confopt:: orientation

    (``portrait``)

    Designate page orientation, portrait or landscape.

.. confopt:: portrait_size

    (``90mm 118mm``)

    Designate portrait page size (width and height).
    The script uses this value when ``orientation`` is ``portrait``.

    The display size of common 6-inch e-readers seems
    arround 90mm x 120mm.
    Here the default thinly clips on height, for versatility.
    (Officially published pixel specs may be different from
    physically effective pixels,
    may be limited by OS, application, or user interfaces.
    In general, width is more precious than height in small devices.)

.. confopt:: landscape_size

    (``118mm 90mm``)

    Designate landscape page size (width and height).
    The script use this value when ``orientation`` is ``landscape``.

.. confopt:: toc_depth

    (``3``)

    Designate (max) tree level of pdf bookmarks (Table of Contents).
    the option can only be used
    when ``converter`` is ``prince`` or ``weasyprint``.

.. confopt:: font_family

    (``"DejaVu Sans", sans-serif``)

    Designate default font to use.

.. confopt:: font_mono

    (``"Dejavu Sans Mono", monospace``)

    Designate default monospaced font to use.

.. confopt:: font_serif

    (None)

    Not used.

.. confopt:: font_sans

    (None)

    Not used.

.. confopt:: font_size

    (``9px``)

    Designate default font size.

.. confopt:: font_size_mono

    (``8px``)

    Designate default monospaced font size.

.. confopt:: font_scale

    (``1``)

    Not used.

.. confopt:: line_height

    (``1.3``)

    Designate default line height.


Converter Sections
^^^^^^^^^^^^^^^^^^

Section ``prince``, ``weasyprint``, ``wkhtmltopdf`` and ``ebook-convert``
are converters sections.
They have common options.

When ``convert``, only one converter is active,
and only the options of that converter's section are used.

.. note ::

    For ``Default Value``, only ones of ``prince`` section are provided here.

    You can see defaults of other converters e.g.::

        $ tosixinch -a --weasyprint
        $ tosixinch -a --wkhtmltopdf

.. confopt:: cnvpath

    (``prince``)

    The name or full path for the command as you type it in the shell.
    For ordinary installed ones, only the name would suffice.

    Currently ``'~'`` is not expanded.

.. confopt:: css

    | (``sample``)
    | ``[COMMA]``

    css file names to be used in order when ``convert``.
    The names are just passed as commandline options to the converter.

    The files must be in ``css directory``,
    just the filenames (not full path).
    Or bundled sample css ``sample.t.css``,
    which can be abbreviated as ``sample``.
    You can mix both.

.. confopt:: cnvopts

    | (``--javascript``)
    | ``[CMD]``

    Other options (than css file option) to pass to the command.


site.ini
--------

``site.ini`` should have many sections,
each is the settings for some specific site or a part of the site.

They all have the same options,
in which the common options (the same ones as in ``tosixinch.ini``)
are not described here.

Each section must have ``match`` option.
It is this option that is used as glob string to match input urls,
and consequently select which section to use.

So section names themselves can be arbitrary.

But the script includes ``site.sample.ini``,
and, if not `disabled <#confopt-use_sample>`__,
it first searches this file.
So the names below are taken
(You are free to override). ::

    wikipedia
    mobileread
    gnu
    python-doc
    python-pep
    bugs.python.org
    hackernews
    hackernews-threads
    reddit
    stackoverflow
    stackprinter
    github
    github-issues
    github-wiki
    gist

.. confopt:: match

    (None)

    Glob string to match against input ``url``.

    URL path separator (``'/'``) is not special
    for wildcards (``*?[]!``).
    So, e.g. ``'*'`` matches any strings
    including all subdirectories.
    (Actually, it uses `fnmatch module <https://docs.python.org/3/library/fnmatch.html>`__,
    not `glob module <https://docs.python.org/3/library/glob.html>`__.).

    Last asterisk can be omitted, so the following two lines make no deference. ::

        match=      https://*.wikipedia.org/wiki/*
        match=      https://*.wikipedia.org/wiki/

    The script tries the values of this option from all the sections.
    The section whose ``match`` option matches the ``url``
    is used for the settings.

    If there are multiple matches,
    the one with the most path separator characters (``'/'``) is used
    (scheme separator ``'//'`` in ``'https?://'`` are not counted).
    If there are multiple matches still,
    the last one is used.

    If there is no match, default settings are used,
    and `guess <#confopt-guess>`__ option is tried.
    In this case, a placeholder value ``http://tosixinch.example.com``
    is set.
    (Note this imaginary site is used to make file paths
    in ``donwnload`` and ``extract``).

.. confopt:: select

    | (None)
    | ``[LINE][XPATH]``

    Xpath strings to select elements
    from ``Downloaded_File`` when ``extract``.
    Only selected elements are included
    in the ``<body>`` tag of the new ``Extracted_File``,
    discarding others.

    Each line in the value will be connected with a bar string (``'|'``)
    when evaluating.
    This means the sequence of selected elements are
    as the same order in the document,
    not grouped by each xpath.


.. confopt:: exclude

    | (None)
    | ``[LINE][XPATH]``

    Xpath strings to remove elements
    from the new ``Extracted_File`` after ``select``.
    So you don't need to exclude already excluded elements by ``select``.
    As in ``select``,
    each line in the value will be connected with a bar string (``'|'``).

.. confopt:: process

    | (None)
    | ``[COMMA][XPATH]``

    After ``select`` and ``exclude``, arbitrary functions can be called
    if this option is specified.

    The function name must include the module name.
    And the function must be a top level one.
    (So each name should have exactly one dot (``'.'``)).

    It is searched in user ``userprocess`` directory
    and application ``process`` directory, in order.

    The first matched one is called with the argument ``'doc'`` auto-filled.
    It is ``lxml.html`` DOM object (``HtmlElement``),
    corresponding to the resultant ``Extracted_File``
    after ``select`` and ``exclude``.
    The name (``'doc'``) is actually irrelevant.

    The function can have additional arguments.
    In that case, users have to provide them in the option string.
    String after ``'?'`` (and before next ``'?'``) is interpreted as an argument.

    For example, ``'aaa.bbb?cc?dd'`` is made into code either::

        userprocess.aaa.bbb(doc, cc, dd)

    or::

        process.aaa.bbb(doc, cc, dd)

    You don't have to ``return`` anything,
    just manipulate ``doc`` as you like.
    The script uses the resultant ``doc`` subsequently.

    For 'built-in' functions and examples, see modules in `process <api.html#process>`__.

.. confopt:: clean

    | (Not implemented. Now this paragraph is only for documentaton purpose.)

    After ``select``, ``exculde`` and ``process`` in ``extract``,
    the script ``clean`` s the resultant html.

    **tags**:
        According to `add_tags <#confopt-add_tags>`__.

    **attributes**:
        According to `add_attrs <#confopt-add_attrs>`__.

    **javascript**:
        All inline javascript and javascript source references
        are unconditionally stripped.

        (In ``download``, we occasionally need javascript,
        and in that case we might use ``Qt``.
        In ``extract``, javascript has already rendered the contents.
        So we shouldn't need it any more.)

    **css**:
        All ``style`` attributes and css source references
        are stripped.

        With one exception.
        If a tag has ``'tsi-keep-style'`` in class attributes,
        ``style`` attributes are kept intact.
        It can be used in ``userprocess`` functions.
        If you want to keep or create some inline ``style``,
        inject this class attribute.::

           # removed (becomes just '<div>')
           <div style="font-weight:bold;">

           # not removed
           <div class="tsi-keep-style other-values" style="font-weight:bold;">


.. confopt:: javascript

    | (``False``)
    | ``[BOOL]``

    If this value is ``True``, downloading is done by ``Qt``.


.. confopt:: cookie

    | (``None``)
    | ``[LINE]``

    Some sites require confirmation before providing the documents.
    ('Are you over 18?', 'Agree to terms of service?')

    And ``urllib`` cannot handle these interactive communications.

    By adding cokkie data here (e.g. from your browsers),
    you may be able to bypass them.

    Note it is not secure and not right.
    Do not provide sensitive data.

    The author doesn't recommend using it altogether.
    But, like the above,
    if the site only wants anonimous users
    to press 'OK' just the first time to make temporary sessions,
    bad things shouldn't happen to the client,
    and that's the rational.


Config Options
==============

.. note ::

    ``Default Value`` is specified by parenthesis in the first lines.

    `Value Function <overview.html#value-functions>`__
    is specified by bracket in the first lines.

tosixinch.ini
-------------

.. note ::

    Options with star ``*`` are common options with `site.ini <#site-ini>`__.
    You can use them to override application-wide configuration.

General Section
^^^^^^^^^^^^^^^

.. confopt:: downloader \*

    (``urllib``)

    Specify default downloader. Currently only ``urllib``.

.. confopt:: extractor \*

    (``lxml``)

    Specify default extractor.
    Either ``lxml`` (recommended) or ``readability``.

    The intended use case of ``readability`` is
    from commandline.
    Either `--readability <commandline.html#cmdoption-readability>`__
    or `--readability-only <commandline.html#cmdoption-readability-only>`__.

.. confopt:: converter

    (``prince``)

    Specify default converter.
    One of ``prince``, ``weasyprint`` or ``wkhtmltopdf``.

.. confopt:: user_agent \*

    (some arbitrary browser user agent.
    Run ``'tosixinch -a'`` to actually see.)

    Specify user agent for downloader (only for ``urllib``).

.. confopt:: javascript \*

    | (``False``)
    | ``[BOOL]``

    If this value is ``True``, downloading is done by one of headless browsers.

.. confopt:: browser_engine \*

    (``selenium-firefox``)

    Specify browser engine when ``javascript`` option is True.
    ``webkit``, ``webengine``, ``selenium-chrome`` or ``selenium-firefox``.

.. confopt:: encoding \*

    | (``utf-8, cp1252, latin_1``)
    | ``[COMMA]``

    Specify preferred encoding or encodings.
    First successful one is used.
    Encoding names are as specified in
    `codecs library <https://docs.python.org/3/library/codecs.html#standard-encodings>`__,
    or `chardet <https://chardet.readthedocs.io/en/latest/index.html>`__,
    `html5prescan <https://github.com/openandclose/html5prescan>`__,
    or `ftfy <https://ftfy.readthedocs.io/en/latest/>`__ if they are installed.

    If the name is ``chardet``, ``chardet.detect`` method is tried.
    It may be able to auto-detect the right encoding.

    If the name is ``html5prescan``, ``html5prescan`` tries to get
    a valid encoding declaration from html.
    (The library strictly follows html5 spec and usually it is not necessary nor useful.
    It is intended for occasional debug purpose.)

    After successful encoding by one of the encodings,
    if the list includes ``ftfy``,
    ``ftfy.fixes.fix_encoding`` method is called with the decoded text.
    It may be able to fix some 'mojibake'.
    (So it is always called last, the place in the list is irrelevant.)

.. note ::

    The included `bash completion <topics.html#script-_tosixinch.bash>`__
    only completes canonical codec names (with underline changed to dash).
    But you can put any other alias name or names as long as they are legal in Python.

.. confopt:: encoding_errors \*

    | (``strict``)

    Specify codec `Error Handler <https://docs.python.org/3/library/codecs.html#error-handlers>`__.

    If you can't run ``extract`` because of decoding errors,
    one solution is to change this option to 'replace' or 'backslashreplace'.

.. confopt:: parts_download \*

    | (``True``)
    | ``[BOOL]``

    Web pages may have some component content.
    Most important ones are images,
    and currently the script only concerns images
    (in html tag ``<img src=...>``).
    The value specifies whether it downloads these components
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
        (They are different domains).

.. confopt:: force_download \*

    | (``False``)
    | ``[BOOL]``

    By default, The script does not download if the destination file exists.

    If this options is ``True``:

    In case of ``-1``,
    it (re-) downloads ``url`` even if ``Downloaded_File`` exists.

    In case of ``-2``,
    it (re-) downloads component files (images etc.)
    even if they exist.

    But in one invocation, this re-downloading is always once for one ``url``.
    (The script doesn't download the same icon files again and again.)

.. confopt:: guess

    | (``//div[@itemprop="articleBody"]``
    | ``//div[@id="main"]``
    | ``//div[@id="content"]``
    | ``//div[@class=="body"]``)

    ``[LINE]``

    If ``url`` doesn't `match <#confopt-match>`__ any site in ``site.ini``,
    ``select`` is done according to this value.

    The procedure is different from ordinary ``select``
    (with a little bit of extra precaution).

    * The xpaths in this value are searched in order.
    * If match is found and match is a single element
      (not multiple occurrences),
      the script ``select`` s the xpath.

.. confopt:: defaultprocess \*

    | (``add_h1, youtube_video_to_thumbnail``)
    | ``[LINE]``

    Before site specific ``process`` functions,
    the script applies default ``process`` functions to all ``url``,
    according to this value.

    The syntax is the same as `process <#confopt-process>`__ option, in ``site.ini``.

    About default functions:

        * ``add_h1``: If there is no ``<h1>``,
          make ``<h1>`` tag from ``<title>`` tag text.
          It is to help make pdf bookmarks (TOC).
        * ``youtube_video_to_thumbnail``: Change embedded youtube video object
          to thumbnail image.

.. confopt:: full_image \*

    (``200``)

    If width or height of component pixel size is equal or above this value,
    class attribute ``tsi-tall`` or ``tsi-wide`` is added to the image tag,
    ``tsi-tall`` if height/width ratio is greater than
    the ratio of the e-reader display,
    ``tsi-wide`` if the opposite.


    By itself, it does nothing. However, In ``sample.css``,
    it is used to make medium sized images expand almost full display size,
    with small images (icon, logo, etc.) as is.
    The layout gets a bit uglier,
    but I think it is necessary for small e-reader displays.

.. confopt:: add_binary_extensions \*

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
    the default ``add_binary_extensions`` list above.

    The list is taken from Sindre Sorhus'
    `binary-extensions <https://github.com/sindresorhus/binary-extensions>`__.

    This is for user convenience. If you copy and paste many urls,
    checking strange extensions is a bit of work.
    But I'm afraid sometimes it gets in the way.

    (An example I found: some old unix software uses ``doc`` extension for text (like ``README.doc``).

.. confopt:: add_clean_tags \*

    | (None)
    | ``[PLUS]``

    After ``select``, ``exclude`` and ``process`` in ``extract``,
    the script ``clean`` s the resultant html.

    The tags in this option are stripped.
    The current default is none.

.. confopt:: add_clean_attrs \*

    | (``color, width, height``)
    | ``[PLUS]``

    After ``select``, ``exclude`` and ``process`` in ``extract``,
    the script ``clean`` s the resultant html.

    The attributes in this option are stripped.
    The current default is color, width and height.

    Most e-readers are black and white.
    Colors just make fonts harder to read.

    Width and height conflict with user css rules.

.. confopt:: elements_to_keep_attrs \*

    | (``self::math``
    | ``self::svg``
    | ``self::node()[starts-with(@class, "MathJax")]``)

    ``[LINE]``

    After ``select``, ``exclude`` and ``process`` in ``extract``,
    the script ``clean`` s the resultant html.

    The program skips cleaning attributes
    for the elements that matches one of the XPath in this option.

    The default is ``math`` and ``svg`` tags.
    They have inter-related width and hight information,
    without which, they are not intelligible.

    Note xpaths are checked against each element, not from the root document.
    So the selectors tend to be a bit complex
    (not the usual e.g. ``'//math'``).

.. confopt:: ftype

    | (None)

    Specify file type when ``extract``.

    Valid values are::

        'html', 'prose', 'nonprose', 'python'

.. note ::

    It needs improvement, but the following seems to work now.

    .. code-block:: ini

        # in ~/.config/tosixinch/site.ini
        [test]
        match=  *.pyw
        ftype=  python

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

.. confopt:: trimdirs \*

    | (``3``)

    Specify the number of directories to remove local text filename.
    Since text files don't have titles or h1 to put them in pdf bookmarks,
    the script passes on full filepaths as their names.
    They tend to be very long, so some means to shorten them is desirable.

    This option is only for local text files.
    Remote text files' names are just urls (schemes are removed).

    C.f. `--check <commandline.html#cmdoption-c>`__ commandline option
    prints out local files.
    They include *html* files, so it is not perfect,
    but it can be useful for
    checking and adjusting this ``trimdirs`` option.

.. confopt:: raw

    | (``False``)
    | ``[BOOL]``

    If ``True``,
    ``url`` is used as input *as is* when ``convert``.
    In this case, ``url`` must be local filepath.

.. confopt:: css \*

    | (``sample``)
    | ``[COMMA]``

    CSS file names to be used in order.
    The names are referenced, in order, in ``Extracted_Files``
    (``'<link ... rel="stylesheet">'``).

    The files must be in ``css directory``,
    just the filenames (not full path).

    The script includes sample css ``sample.t.css``,
    and as a special case, it can be abbreviated as ``sample``
    (default).

.. confopt:: pdfname

    | (None)

    Specify output PDF file name.
    If not provided (default), the script makes up some name.
    see `PDF_File <overview.html#dword-PDF_File>`__.

---

.. note ::

    For ``hookcmds``, see `Hookcmds <topics.html#hookcmds>`__.

.. confopt:: precmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command before ``download``.

.. confopt:: postcmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command after ``download``.

.. confopt:: precmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command before ``extract``.

.. confopt:: postcmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command after ``extract``.

.. confopt:: precmd3

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command before ``convert``.

.. confopt:: postcmd3

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command after ``convert``.

.. confopt:: viewcmd

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command
    when specified in commandline options (``-4`` or ``--view``).

.. confopt:: pre_each_cmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command before each ``download``.

.. confopt:: post_each_cmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command after each ``download``.

.. confopt:: pre_each_cmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command before each ``extract``.

    There are sample hook extractors.
    See `_man <topics.html#man>`__ and `_pcode <topics.html#pcode>`__.

.. confopt:: post_each_cmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary command after each ``extract``.

.. confopt:: browsercmd

    | (None)
    | ``[CMD]``

    When action is ``--browser``,
    specify the command to open a browser,
    if the default (calling Python stdlib ``webbrowser``) is not desirable. E.g.::

        firefox 'site.slash_fnew'

    Here, you have to use the magic word ``site.slash_fnew``.
    It evaluates to the intended url version of ``Extracted_File``.

.. confopt:: loc_index

    | (None)

    Specifies the placeholder name when the last url path is changed to directory.
    Application default is ``'_'``.

    (See `Downloaded_File <overview.html#dword-Downloaded_File>`__ for details.

.. confopt:: loc_appendix

    | (None)

    Specifies the suffix for the name of ``Extracted_File``.
    Application default is ``'~'``.

    (See `Extracted_File <overview.html#dword-Extracted_File>`__ for details.


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

    Specify page orientation, portrait or landscape.

.. confopt:: portrait_size

    (``90mm 118mm``)

    Specify portrait page size (width and height).
    The script uses this value when ``orientation`` is ``portrait``.

    The display size of common 6-inch e-readers seems
    around 90mm x 120mm.
    Here the default thinly clips on height, for versatility.
    (Officially published pixel specs may be different from
    physically effective pixels,
    may be limited by OS, application, or user interfaces.
    In general, width is more precious than height in small devices.)

.. confopt:: landscape_size

    (``118mm 90mm``)

    Specify landscape page size (width and height).
    The script use this value when ``orientation`` is ``landscape``.

.. confopt:: toc_depth

    (``3``)

    Specify (max) tree level of pdf bookmarks (Table of Contents).
    It uses html headings for structuring, so valid values are 0 to 6.

.. confopt:: font_family

    (``"DejaVu Sans", sans-serif``)

    Specify default font to use.

.. confopt:: font_mono

    (``"Dejavu Sans Mono", monospace``)

    Specify default monospaced font to use.

.. confopt:: font_serif

    (None)

    Not used.

.. confopt:: font_sans

    (None)

    Not used.

.. confopt:: font_size

    (``9px``)

    Specify default font size.

.. confopt:: font_size_mono

    (``8px``)

    Specify default monospaced font size.

.. confopt:: font_scale

    (``1.0``)

    Specify scaling factor for css ``font_size`` and ``font_size_mono``.

    It is to make easier to test font sizes.

.. confopt:: line_height

    (``1.3``)

    Specify default line height.


Converter Sections
^^^^^^^^^^^^^^^^^^

Section ``prince``, ``weasyprint``, and ``wkhtmltopdf``
are converters sections.
They have common options.

When ``convert``, only one converter is active,
and only the options of that converter's section are used.

.. note ::

    For ``Default Value``, only ones of ``prince`` section are provided here.

    You can see defaults of other converters e.g. ::

        $ tosixinch -a --weasyprint
        $ tosixinch -a --wkhtmltopdf

.. confopt:: cnvpath

    (``prince``)

    The name or full path for the command as you type it in the shell.
    For ordinary installed ones, only the name would suffice.

    Currently ``'~'`` is not expanded.

.. confopt:: css2

    | (None)
    | ``[COMMA]``

    Extra css files just to pass to converter commandline options.

    It may be useful for converter specific features or troubles.
    Although, normally, you can do that better
    with ``css`` option and the template.

    The files must be in ``css directory``,
    just the filenames (not full path).

.. confopt:: cnvopts

    | (None)
    | ``[CMD]``

    Options to pass to the command.


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


.. confopt:: match

    (None)

    Glob string to match against input ``url``.

    URL path separator (``'/'``) is not special
    for wildcards (``*?[]!``).
    So, e.g. ``'*'`` matches any strings
    including all subdirectories.
    (Actually, it uses `fnmatch module <https://docs.python.org/3/library/fnmatch.html>`__,
    not `glob module <https://docs.python.org/3/library/glob.html>`__.).

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
    in ``download`` and ``extract``).

.. confopt:: select

    | (None)
    | ``[LINE]``

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
    | ``[LINE]``

    Xpath strings to remove elements
    from the new ``Extracted_File`` after ``select``.
    So you don't need to exclude already excluded elements by ``select``.
    As in ``select``,
    each line in the value will be connected with a bar string (``'|'``).

.. confopt:: process

    | (None)
    | ``[LINE]``

    After ``select`` and ``exclude``, arbitrary functions can be called
    if this option is specified.

    **Selection**:

    The functions must be top level ones.

    It is searched in `user process directory <overview.html#dword-process_directory>`__
    and the program's process directory, in order.

    If the function name is found in multiple modules
    in user process directory, the program raises Error.

    In that case, you can use dot notation.
    If the function name includes one dot (``'.'``),
    the program interprets it as ``<module name>.<function name>``.
    Two or more dots are not supported.

    **Invocation**:

    The first argument of the functions is always ``doc``,
    which the program provides.
    It is ``lxml.html`` DOM object (``HtmlElement``),
    corresponding to the resultant ``Extracted_File``
    after ``select`` and ``exclude``.

    The function can have additional arguments.
    String after ``'?'`` (and before next ``'?'``) is interpreted as an argument.

    For example, ``'aaa.bbb?cc?dd'`` is made into code,
    if ``'aaa.bbb'`` is found in user process directory:

    .. code-block:: none

        process.aaa.bbb(doc, cc, dd)

    or it is found in the program's process directory:

    .. code-block:: none

        tosixinch.process.aaa.bbb(doc, cc, dd)

    You don't have to ``return`` anything,
    just manipulate ``doc`` as you like.
    The script uses the resultant ``doc`` subsequently.

    See `process.sample <api.html#module-tosixinch.process.sample>`__ for included sample functions.

    **Example**:

    Let's say you want to change ``h3`` tag to ``div`` for http://somesite.com.

    First, create a file in `process directory <overview.html#dword-process_directory>`__
    e.g. ``~/.config/tosixinch/process/myprocess.py``.

    Second, create a top level function e.g.

    .. code-block:: python

        def heading_to_div(doc, heading):
            """Change some heading to div from argument e.g. 'h3'."""
            for el in doc.xpath('//' + heading):
                el.tag = 'div'

    Third, write configuration accordingly.

    .. code-block:: ini

        [somesite]
        match=      http://somesite.com/*
        select=     ...
        process=    myprocess.heading_to_div?h3

.. confopt:: clean

    | (Note there is no option named ``clean``. This section is here only for documentation purpose.)

    After ``select``, ``exclude`` and ``process`` in ``extract``,
    the script ``clean`` s the resultant html.

    **tags**:
        According to `add_clean_tags <#confopt-add_clean_tags>`__.

    **attributes**:
        According to `add_clean_attrs <#confopt-add_clean_attrs>`__.

    **javascript**:
        All inline javascript and javascript source references
        are unconditionally stripped.

        (In ``download``, we occasionally need javascript,
        and in that case we might use headless browsers.
        In ``extract``, javascript has already rendered the contents.
        So we shouldn't need it any more.)

    **css**:
        All ``style`` attributes and css source references
        are stripped, with one exception.

        If a tag has ``'tsi-keep-style'`` in class attributes,
        ``style`` attributes are kept intact.
        It can be used in process functions.
        If you want to keep or create some inline ``style``,
        inject this class attribute. ::

           # removed (becomes just '<div>')
           <div style="font-weight:bold;">

           # not removed
           <div class="tsi-keep-style other-values" style="font-weight:bold;">

    **skip tags**:
        According to `elements_to_keep_attrs <#confopt-elements_to_keep_attrs>`__.
        The program skips cleaning the matched elements (and all sub-elements),
        if the elements are not already removed by ``add_clean_tags``.

.. confopt:: cookie

    | (``None``)
    | ``[LINE]``

    Some sites require confirmation before providing the documents.
    ('Are you over 18?', 'Agree to terms of service?')

    And ``urllib`` cannot handle these interactive communications.

    By adding cookie data here (e.g. from your browsers),
    you may be able to bypass them.

    Note it is not secure and not right.
    Do not provide sensitive data.

.. confopt:: dprocess

    | (None)
    | ``[LINE]``

    When ``download``,
    the program runs functions specified by this option
    after getting http response, and before serializing to html text.

    For completeness, it runs when downloader is ``urllib``,
    but the supposed usage is for other headless browsers.

    For example, some webpages have folded contents
    which users need to click and run javascript to expand.

    The mechanism is similar to ``process``,
    Users define a function in a python file in user ``dprocess`` directory,
    with ``agent`` as the first argument,
    and modify it. If necessary, they can define other arguments
    by using ``'?'``
    (see `process <#confopt-process>`__).

    But what comes as ``agent`` is dependent on
    what is actually ``downloader`` now::

        urllib      http.client.HTTPResponse
        webkit      PyQt5.QtWebKitWidgets.QWebPage
        webengine   PyQt5.QtWebEngineWidgets.QWebEngineView
        selenium    selenium.webdriver.remote.webdriver.WebDriver

    So user should be careful.
    (For example, when you define ``dprocess`` in ``site.ini``,
    it is advisable to also define ``browser_engine``).

    Example:

    .. code-block:: python

        def sitefoo_click(agent):  # for selenium
            path = '//div[@class="see_more"]'
            elements = agent.find_elements_by_xpath(path)
            for element in elements:
                element.click()
                time.sleep(1)

.. confopt:: link

    | (``//a/@href``)
    | ``[LINE]``

    (Experimental)

    When action is ``link``,
    the script prints some xpath content (must be strings) for each url,
    reading from this option.

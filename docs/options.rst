
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

    Specify default downloader.
    Either ``urllib`` or ``headless``.

.. confopt:: extractor \*

    (``lxml``)

    Specify default extractor.
    Currently the only option is ``lxml``.

.. confopt:: converter

    (``prince``)

    Specify default converter.
    ``prince`` or ``weasyprint``.

.. confopt:: user_agent \*

    (some arbitrary browser user agent.
    Run ``'tosixinch -a'`` to actually see.)

    Specify user agent for downloader (only for ``urllib``).

.. confopt:: browser_engine \*

    (``selenium-firefox``)

    Specify browser engine when ``headless`` option is True,
    ``selenium-chrome`` or ``selenium-firefox``.

.. confopt:: selenium_chrome_path \*

    | (None)

    Specify the path of chromedriver for selenium
    (passed to ``executable_path`` argument). Normally unnecessary.

.. confopt:: selenium_firefox_path \*

    | (None)

    Specify the path of geckodriver for selenium
    (passed to ``executable_path`` argument). Normally unnecessary.

.. confopt:: encoding \*

    | (``utf-8, cp1252, latin_1``)
    | ``[COMMA]``

    Specify preferred encoding or encodings.
    First successful one is used.
    Encoding names are as specified in
    `codecs library <https://docs.python.org/3/library/codecs.html#standard-encodings>`__,
    or `'html5prescan' <https://github.com/openandclose/html5prescan>`__,
    or `'ftfy' <https://ftfy.readthedocs.io/en/latest/>`__ if they are installed.

    If the name is ``html5prescan``, ``html5prescan`` tries to get
    a valid encoding declaration from html.
    (The library strictly follows html5 spec and usually it is not necessary nor useful.
    It is intended for occasional debug purpose.)

    After successful encoding by one of the encodings,
    if the list includes ``ftfy``,
    ``ftfy.fixes.fix_encoding`` method is called with the decoded text.
    It may be able to fix some 'mojibake'.
    (So it is always called last, the place in the list is irrelevant).

.. note ::

    The included `bash completion <topics.html#script-_tosixinch.bash>`__
    only completes canonical codec names (with underline changed to dash).
    But you can put any other name or alias names, as long as they are legal
    in your Python environment.

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
    and currently the program only concerns images
    (in html tag ``<img src=...>``).
    The value specifies whether it downloads these components
    when ``extract``.

    Note downloading may occur anyway by pdf converters.

    If this option is ``True``,
    download links are rewritten to point to local ``dfiles``.
    So downloading doesn't happen when ``convert``.

    In general, pre-downloading is useful
    for multiple trials and layout checking.

    If `force_download <#confopt-force_download>`__ is ``False`` (default),
    the program skips downloading if the file already exists.

.. confopt:: force_download \*

    | (``False``)
    | ``[BOOL]``

    By default, The program does not download if the destination file exists.

    If this options is ``True``:

    In case of ``-1``,
    it (re-) downloads ``URL`` even if ``dfile`` exists.

    In case of ``-2``,
    it (re-) downloads component files (images etc.)
    even if they exist.

    But in one invocation, this re-downloading is always once for one ``URL``.
    (The program doesn't download the same icon files again and again).

.. confopt:: guess

    | (``//div[@itemprop="articleBody"]``
    | ``//div[@role="main"]``
    | ``//div[@id="main"]``
    | ``//div[@id="content"]``
    | ``//div[@class=="body"]``
    | ``//article``)

    ``[LINE]``

    If html ``rsrc`` doesn't match any `match <#confopt-match>`__ option in ``site.ini``,
    ``select`` is done according to this value.

    The procedure:

    * The XPaths in this value are searched in order, line by line.
    * If match is found and match is a single element
      (not multiple occurrences),
      the program ``select`` s the element.

.. confopt:: defaultprocess \*

    | (``add_h1, youtube_video_to_thumbnail, convert_permalink_sign``)
    | ``[LINE]``

    Before site specific ``process`` functions,
    the program applies default ``process`` functions to all html ``rsrc``,
    according to this value.

    The syntax is the same as `process <#confopt-process>`__ option, in ``site.ini``.

    About default functions:

        * ``add_h1``: If there is no ``<h1>``,
          make ``<h1>`` tag from ``<title>`` tag text.
          It is to make better pdf bookmarks (TOC).
        * ``youtube_video_to_thumbnail``: Change embedded youtube video object
          to thumbnail image.
        * ``convert_permalink_sign``: Remove permalink sign ('¶'),
          for a few class ('headerlink' etc.).
          Python documents tend to use them,
          and On pdf, they are always visible, rather noisy.

    When the default functions is undesirable in some site,
    please override this option in user ``site.ini``.

.. confopt:: full_image \*

    | (``200``)
    | ``[INT]``

    If width or height of image pixel size is equal or above this value,
    class attribute ``tsi-tall`` or ``tsi-wide`` is added to the image tag,
    ``tsi-tall`` if height/width ratio is greater than
    the ratio of the e-reader display,
    ``tsi-wide`` if the opposite.


    By itself, it does nothing. However, In ``sample.css``,
    it is used to make medium sized images expand almost full display size,
    with small images (icon, logo, etc.) intact.
    The layout gets a bit uglier,
    but I think it is necessary for small e-reader displays.

.. confopt:: add_binary_extensions

    (``3dm`` ``3ds`` ``3g2`` ``3gp`` ``7z`` ``a`` ``aac`` ``adp`` ``ai`` ``aif`` ``aiff`` ``alz`` ``ape`` ``apk`` ``appimage`` ``ar`` ``arj`` ``asf`` ``au`` ``avi`` ``bak`` ``baml`` ``bh`` ``bin`` ``bk`` ``bmp`` ``btif`` ``bz2`` ``bzip2`` ``cab`` ``caf`` ``cgm`` ``class`` ``cmx`` ``cpio`` ``cr2`` ``cur`` ``dat`` ``dcm`` ``deb`` ``dex`` ``djvu`` ``dll`` ``dmg`` ``dng`` ``doc`` ``docm`` ``docx`` ``dot`` ``dotm`` ``dra`` ``DS_Store`` ``dsk`` ``dts`` ``dtshd`` ``dvb`` ``dwg`` ``dxf`` ``ecelp4800`` ``ecelp7470`` ``ecelp9600`` ``egg`` ``eol`` ``eot`` ``epub`` ``exe`` ``f4v`` ``fbs`` ``fh`` ``fla`` ``flac`` ``flatpak`` ``fli`` ``flv`` ``fpx`` ``fst`` ``fvt`` ``g3`` ``gh`` ``gif`` ``graffle`` ``gz`` ``gzip`` ``h261`` ``h263`` ``h264`` ``icns`` ``ico`` ``ief`` ``img`` ``ipa`` ``iso`` ``jar`` ``jpeg`` ``jpg`` ``jpgv`` ``jpm`` ``jxr`` ``key`` ``ktx`` ``lha`` ``lib`` ``lvp`` ``lz`` ``lzh`` ``lzma`` ``lzo`` ``m3u`` ``m4a`` ``m4v`` ``mar`` ``mdi`` ``mht`` ``mid`` ``midi`` ``mj2`` ``mka`` ``mkv`` ``mmr`` ``mng`` ``mobi`` ``mov`` ``movie`` ``mp3`` ``mp4`` ``mp4a`` ``mpeg`` ``mpg`` ``mpga`` ``mxu`` ``nef`` ``npx`` ``numbers`` ``nupkg`` ``o`` ``odp`` ``ods`` ``odt`` ``oga`` ``ogg`` ``ogv`` ``otf`` ``ott`` ``pages`` ``pbm`` ``pcx`` ``pdb`` ``pdf`` ``pea`` ``pgm`` ``pic`` ``png`` ``pnm`` ``pot`` ``potm`` ``potx`` ``ppa`` ``ppam`` ``ppm`` ``pps`` ``ppsm`` ``ppsx`` ``ppt`` ``pptm`` ``pptx`` ``psd`` ``pya`` ``pyc`` ``pyo`` ``pyv`` ``qt`` ``rar`` ``ras`` ``raw`` ``resources`` ``rgb`` ``rip`` ``rlc`` ``rmf`` ``rmvb`` ``rpm`` ``rtf`` ``rz`` ``s3m`` ``s7z`` ``scpt`` ``sgi`` ``shar`` ``snap`` ``sil`` ``sketch`` ``slk`` ``smv`` ``snk`` ``so`` ``stl`` ``suo`` ``sub`` ``swf`` ``tar`` ``tbz`` ``tbz2`` ``tga`` ``tgz`` ``thmx`` ``tif`` ``tiff`` ``tlz`` ``ttc`` ``ttf`` ``txz`` ``udf`` ``uvh`` ``uvi`` ``uvm`` ``uvp`` ``uvs`` ``uvu`` ``viv`` ``vob`` ``war`` ``wav`` ``wax`` ``wbmp`` ``wdp`` ``weba`` ``webm`` ``webp`` ``whl`` ``wim`` ``wm`` ``wma`` ``wmv`` ``wmx`` ``woff`` ``woff2`` ``wrm`` ``wvx`` ``xbm`` ``xif`` ``xla`` ``xlam`` ``xls`` ``xlsb`` ``xlsm`` ``xlsx`` ``xlt`` ``xltm`` ``xltx`` ``xm`` ``xmind`` ``xpi`` ``xpm`` ``xwd`` ``xz`` ``z`` ``zip`` ``zipx``)

    ``[PLUS]``

    The program ignores ``rsrcs`` with binary like looking extensions,
    only when multiple ``rsrcs`` are provided.

    This option value adds to or subtracts from
    the default ``add_binary_extensions`` list above.

    The list is taken from Sindre Sorhus'
    `binary-extensions <https://github.com/sindresorhus/binary-extensions>`__.

    This is for user convenience. If you copy and paste many ``rsrcs``,
    checking strange extensions is a bit of work.
    But I'm afraid sometimes it gets in the way.

    (An example I found: some old unix software uses ``doc`` extension for text (like ``README.doc``).

.. confopt:: add_clean_tags \*

    | (None)
    | ``[PLUS]``

    After ``select``, ``exclude`` and ``process`` in ``extract``,
    the program ``clean`` s the resultant html.

    The tags in this option are stripped.
    The current default is none.

.. confopt:: add_clean_attrs \*

    | (``color, width, height``)
    | ``[PLUS]``

    After ``select``, ``exclude`` and ``process`` in ``extract``,
    the program ``clean`` s the resultant html.

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
    the program ``clean`` s the resultant html.

    The program skips cleaning attributes
    for the elements that matches one of the XPath in this option.

    The default is ``math``, ``svg`` and some ``MathJax`` related tags.
    They have inter-related width and height information,
    which we usually want to keep.

    Note XPaths are checked from each element, not from the root document.
    So the selectors are like above
    (not like e.g. ``'//math'``).

.. confopt:: clean \*

    | (``both``)

    Specify how to clean html (both, head, body, none).

    See `Clean <overview.html#clean>`__.

.. confopt:: ftype

    | (None)

    Specify file type when ``extract``.

    Valid values are::

        'html', 'prose', 'nonprose', 'python'

    It needs improvement.

.. confopt:: textwidth

    | (``65``)
    | ``[INT]``


    Set physical line length for ``nonprose`` texts.

    See `nonprose <topics.html#non-prose>`__.

.. confopt:: textindent

    (``'                    --> '``)

    Set logical line continuation marker for ``nonprose`` texts.

    See `nonprose <topics.html#non-prose>`__.

    ``ConfigParser`` strips leading and ending whitespaces.
    So if you want actual whitespaces, quote them as the default does.
    Quotes are stripped by the program in turn.

.. confopt:: trimdirs \*

    | (``3``)
    | ``[INT]``

    Shorten PDF table of contents title, if it is a local text file.

    PDF toc title for local text file is made from their full path.
    If this trimdirs option value is with no sign,
    remove that number from leading path segments.
    If it is with minus sign, remove leading path segments
    to make the segments to that number.

    .. code-block:: none

        --trimdirs 0
        aaa/bbb/ccc/ddd/eee/fff

        --trimdirs 2  # remove two segments
        ccc/ddd/eee/fff

        --trimdirs -2  # reduce to two segments
        eee/fff

        # c.f. no bounding errors

        --trimdirs 100
        fff

        --trimdirs -100
        aaa/bbb/ccc/ddd/eee/fff

    Note html files always use html title (actual, or placeholder ``notitle``).
    Remote text (non-html) files use the URL with scheme ('https://') stripped. 

    C.f. `--check <commandline.html#cmdoption-c>`__ commandline option
    prints out this shortened names for local files.
    They include local html files, so it is not perfect,
    but it can be useful for
    checking and adjusting this ``trimdirs`` option.

.. confopt:: raw

    | (``False``)
    | ``[BOOL]``

    If ``True``,
    when ``convert``, the program processes ``rsrcs``.
    Normally (if it is ``False``), it processes ``efile``.

.. confopt:: css \*

    | (``sample``)
    | ``[COMMA]``

    CSS file names to be used in order.
    The names are referenced, in order, in ``efiles``
    (``'<link ... rel="stylesheet">'``).

    you can only use the filenames (not full paths).

    The filenames are searched in
    ``css directory``, ``application css directory`` and current directory in order.

    The program includes sample css ``sample.t.css``,
    and as a special case, it can be abbreviated as ``sample``
    (default).

.. confopt:: pdfname

    | (None)

    Specify output PDF file name.
    If not provided (default), the program makes up some name.
    see `PDF_File <overview.html#dword-PDF_File>`__.

---

.. note ::

    For ``hookcmds`` below, see `Hookcmds <topics.html#hookcmds>`__.

.. confopt:: precmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands before ``download`` action.

.. confopt:: postcmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands after ``download`` action.

.. confopt:: precmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands before ``extract`` action.

.. confopt:: postcmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands after ``extract`` action.

.. confopt:: precmd3

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands before ``convert`` action.

.. confopt:: postcmd3

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands after ``convert`` action.

.. confopt:: viewcmd

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands
    when specified in commandline options (``-4`` or ``--view``).

.. confopt:: pre_each_cmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands before each ``download``.

.. confopt:: post_each_cmd1

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands after each ``download``.

.. confopt:: pre_each_cmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands before each ``extract``.

    There are sample hook extractors.
    See `_man <topics.html#man>`__ and `_pcode <topics.html#pcode>`__.

.. confopt:: post_each_cmd2

    | (None)
    | ``[LINE][CMDS]``

    Run arbitrary commands after each ``extract``.

.. confopt:: browsercmd

    | (None)
    | ``[CMD]``

    When action is ``--browser``,
    the default is just call Python stdlib ``webbrowser``
    to open a browser.
    If it is not desirable, specify the open command here, e.g.::

        firefox 'site.slash_efile'

    You have to use the magic word ``site.slash_efile`` for the filename.
    It evaluates to the intended URL version of ``efile`` (percent encoding etc.).


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
    The program uses this value when ``orientation`` is ``portrait``.

    The display size of common 6-inch e-readers seems
    around 90mm x 120mm.
    Here the default thinly clips on height, for versatility.

.. confopt:: landscape_size

    (``118mm 90mm``)

    Specify landscape page size (width and height).
    The program use this value when ``orientation`` is ``landscape``.

.. confopt:: toc_depth

    | (``3``)
    | ``[INT]``

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

Section ``prince`` and ``weasyprint`` are converter sections.
They have common options.

When ``convert``, only one converter is active,
and only the options of that converter's section are active.

commandline has the same options, to override.

.. note ::

    To see the current values for each converter::

        $ tosixinch -a --prince
        $ tosixinch -a --weasyprint

.. confopt:: cnvpath

    (``prince``)

    The name or full path of the command as you type it in the shell.
    For ordinary installed ones, only the name would suffice.

.. confopt:: css2

    | (None)
    | ``[COMMA]``

    Extra css files just to pass to converter commandline options.

    It may be useful for converter specific features or troubles.
    Although, normally, you can do that better
    with ``css`` option and the template.

    You can only use the filenames (not full paths).

    The filenames are searched in ``css directory`` and current directory in order.

.. confopt:: cnvopts

    | (None)
    | ``[CMD]``

    Additional options to pass to the command,
    besides css file option
    (which is added by ``css2`` option above if it is specified).


site.ini
--------

``site.ini`` should have many sections,
each is the settings for some specific site or a part of the site.

They all have the same options,
in which the common options (the same ones as in ``tosixinch.ini``)
are not described here.

Each section must have ``match`` option.
It is this option that is used as glob string to match input ``rsrcs``,
and consequently select which section to use.

So section names themselves can be arbitrary.


.. confopt:: match

    (None)

    Glob string to match against input ``rsrc``.

    Path separator (``'/'``) is not special
    for wildcards (``*?[]!``).
    So, e.g. ``'*'`` matches any strings
    including all subdirectories.
    (Actually, it uses `fnmatch module <https://docs.python.org/3/library/fnmatch.html>`__,
    not `glob module <https://docs.python.org/3/library/glob.html>`__).

    The program tries the values of this option from all the sections.
    The section whose ``match`` option matches the ``rsrc``
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
    (This imaginary site is used to make file paths
    in ``download`` and ``extract``).

.. confopt:: select

    | (None)
    | ``[LINE]``

    XPath strings to select elements
    from ``dfile`` when ``extract``.
    Only selected elements are included
    in the ``<body>`` tag of the new ``efile``,
    discarding others.

    Each line in the value will be connected with a bar string (``'|'``)
    when evaluating.

.. confopt:: exclude

    | (None)
    | ``[LINE]``

    XPath strings to remove elements
    from the new ``efile`` after ``select``.
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
    and application process directory, in order.

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
    corresponding to the resultant ``efile``
    after ``select`` and ``exclude``.

    The function can have additional arguments.
    String after ``'?'`` (and before next ``'?'``) is interpreted as an argument.

    For example, ``'aaa?bb?cc'`` is made into code

    if ``'aaa.py'`` is found in user process directory:

    .. code-block:: none

        process.aaa(doc, bb, cc)

    or if it is found in application process directory:

    .. code-block:: none

        tosixinch.process.aaa(doc, bb, cc)

    You don't have to ``return`` anything,
    just manipulate ``doc`` as you like.
    The program uses the resultant ``doc`` subsequently.

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

.. confopt:: cookie

    | (None)
    | ``[LINE]``

    Some sites require confirmation before providing the documents.
    ('Are you over 18?', 'Agree to terms of service?')

    And ``urllib`` cannot handle these interactive communications.

    By adding cookie data here (e.g. from your browsers),
    you may be able to bypass them.

    Note it is not secure.
    Do not provide sensitive data.

.. confopt:: dprocess

    | (None)
    | ``[LINE]``

    When ``download``,
    the program runs functions specified by this option
    after getting http response, and before serializing to html text.

    For completeness, it also runs when downloader is ``urllib``,
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
        selenium    selenium.webdriver.remote.webdriver.WebDriver

    So user should be careful.
    (For example, when you define ``dprocess`` in ``site.ini``,
    it is advisable to also define ``downloader``).

    Example:

    .. code-block:: python

        def sitefoo_click(agent):  # for selenium
            path = '//div[@class="see_details"]'
            elements = agent.find_elements_by_xpath(path)
            for element in elements:
                element.click()
                time.sleep(1)

.. confopt:: inspect

    | (``get_links``)
    | ``[LINE]``

    When action is ``inspect``,
    the program runs functions this option specifies.

    This is similar to ``extract`` action's ``process``,
    but ``inspect`` does not do anything before and after
    (select, exclude ..., write to file).
    
    Create Python functions in the same folder as ``process``,
    original non-extracted html object is provided,
    as the first argument ``doc``, and user do something,
    mostly print something.

    See `process.inspect_sample <api.html#module-tosixinch.process.inspect_sample>`__
    for a few sample functions.

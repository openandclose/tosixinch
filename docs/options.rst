
Options
=======

* ``Default Value`` is designated by parenthesis in the first lines.
* ``Value Function`` is designated by bracket in the first lines.
* options with star ``*`` are common options with ``site.ini``.
  You can use them for specific site section.


[general]
---------

**downloader**
    (``urllib``)

    Designate default downloader. Currently only ``'urllib'``.

**extractor**
    (``lxml``)

    Designate default extractor.
    Either ``'lxml'`` (recommended) or ``'readability'``.
**converter**
    (``prince``)

    Designate default converter.
    One of ``'prince'``, ``'weasyprint'``, ``'wkhtmltopdf'``
    or ``'ebook-convert'``.

**\* user_agent**
    (some arbitrary browser user agent)

    Designate user agent for downloader (only for ``urllib``).

**\* qt**
    (``webkit``)

    Designate rendering engine when specified to use ``qt``.
    Either ``webkit`` or ``webengine``.
    ``webengine`` is a newer one,
    and newer functionalities are not used in this script.

**\* encoding**
    | (``utf-8, utf-8-variants, latin_1, cp1252``)
    | ``[COMMA]``

    Specify preferred encodings in order.
    First successful one is used.
    Encoding names are as specified in
    `codecs library <https://docs.python.org/3/library/codecs.html#standard-encodings>`__,
    and ``ftfy`` and ``chardet`` if they are installed.

    A use case for ``ftfy`` is to aggressively interpret text as ``UTF-8``
    by injecting it before false-positives.
    ``chardet`` can be used as a last resort. An example::

        utf-8, utf-8-variants, ftfy, latin_1, cp1252, chardet

**\* parts_download**
    | (``True``)
    | ``[BOOL]``

    Web pages may have some component content.
    Most important ones are images,
    and currently the script only concerns images
    (in html tag ``<img src=...``).
    The value designate whether it downloads these components
    when ``extract``.

    Note that downloading may occur anyway by pdf converters.

    If this option is ``True``,
    download links are rewritten to point to local downloaded files.
    So downloading doesn't happen when ``convert``.

    In general, pre-downloading is useful
    for multiple trials and layout checking.

**\* full_image**
    (``200``)

    If width or height of component pixel size is equal or above this value,
    class attribute 'tsi-big' or 'tsi-tall' is added to the image tag.
    ('tsi' is short for 'tosixinch',
    'tsi-big' if width is longer than height, 'tsi-tall' if the opposite)

    In ``sample.css``, it is used to make images almost full display size,
    excluding too small images (icon, logo, etc.).

**\* add_binaries**
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

    The script ignores ``url`` with binary like looking extensions,
    if multiple ``url`` s  are provided.
    This option value adds to or subtracts from the default binaries list.
    The list is taken from Sindre Sorhus'
    `binary-extensions <https://github.com/sindresorhus/binary-extensions>`__.

    If ``url`` list consists of one single ``url``, the script doesn't use this.

**\* add_tags**
    | (None)
    | ``[PLUS]``

    Add to or subtract from the ``to-delete-tags`` list in ``clean``
    when ``extract``.
    The default is currently none, so ``minus item`` does not make sense.

**\* add_attrs**
    | (``color, width, height``)
    | ``[PLUS]``

    Add to or subtract from the ``to-delete-attributes`` list in ``clean``
    when ``extract``.

    As you see, by default the script always strips three attributes
    from all content.

    Most e-readers are black and white,
    so colors just make fonts harder to read.
    And width and height make document harder to contain
    in small display size.

.. note::

    javascript and css (inline or source) are always stripped,
    except in your ``userprocess`` functions,
    where you can add some inline styles.
    see `tsi-keep-style <overview.html#other-magic-words>`__.

**guess**
    | (``//div[@itemprop="articleBody"]``
    | ``//div[@id="main"]``
    | ``//div[@id="content"]``
    | ``//div[@class=="body"]``)

    ``[LINE][XPATH]``

    The value is used as default ``select`` value
    if no site in ``site.ini`` is matched for ``url``.
    This value is searched in order
    and if match is found and match is a single element,
    the element is *selected*.

**raw**
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

**use_sample**
    | (``True``)
    | ``[BOOL]``

    The value specifies whether site config includes ``site.sample.ini``.

**\* preprocess**
    | (``gen.add_title,gen.youtube_video_to_thumbnail,gen.delete_duplicate_br``)
    | ``[COMMA]``

    Default ``process`` functions to apply to all ``url``.
    They are called before site specific ``process`` functions.

    The syntax is the same as ``process`` option in ``Site Sections``.

    What default three functions do is:

        * ``add_title``: If there is no ``<h1>``,
          make ``<h1>`` from ``<title>`` tag text.
        * ``youtube_video_to_thumbnail``: Change embedded youtube video object
          to thumbnail image.
        * ``delete_duplicate_br``: Continuous ``<br>`` to one ``<br>`` tag.

**textwidth**
    (``65``)

    Set physical line length for ``nonprose`` texts.

    See `nonprose <topics.html#non-prose>`__.

**textindent**
    (``'                    --> '``)

    Set logical line continuation marker for ``nonprose`` texts.

    ``ConfigParser`` strips leading and ending whitespaces.
    So if you want actual whitespaces, quote them as default does.
    Quotes are stripped by the script in turn.

**textcss**
    (``sample``)

    Not used.

**add_filters**
    | (``/\.git/, /docs?/, /.+\.egg-info/``)
    | ``[PLUS]``

    If ``url`` is directory or they are all directories,
    the script just print out files in that directory or directories,
    excluding matched sub directories and files
    in this list of (added or subtracted) strings.
    
    Each item is some regular expression.

    Printing out also considers ``add_binaries`` option.

**userdir**
    (the script searches ``TOSIXINCH_USERDIR`` environment variable
    and common OS config dirs)

    Override default user configuration directory if specified.

**nouserdir**
    | (``False``)
    | ``[BOOL]``

    Skip parsing user configurations.
    Intended for testing.

**(precmds and postcmds)**
    Users can call arbitrary shell commands with these options as a last resort
    if the script fails to do what they want,
    or even what the script professes it can do.

    One useful use case of ``postcmds`` is notification,
    because ``download`` and ``convert`` sometimes take a time.
    For example, if you are using linux::

        postcmd1=   notify-send -t 3000 'Done -- tosixinch.download'

    should bring some notification balloon
    when ``download`` is complete.

    If a word in the statement begins with ``'conf.'``,
    and the rest is dot separated identifier (``[a-zA-Z_][a-zA-Z_0-9]+``),
    it is evaluated as the object ``conf``. For example::

        postcmd1=   echo conf._configdir
        
    will print application config directory name.
    (You need to peek in the source code for details about ``conf``.
    Documents are not provided).

    ``userdir`` is inserted in the head of ``$PATH``,
    so you don't have to provide full paths to your custom scripts
    if you put them there.

**precmd1**
    | (None)
    | ``[CMD]``

    Run arbitrary shell command before ``download``.

**postcmd1**
    | (None)
    | ``[CMD]``

    Run arbitrary shell command after ``download``.

**precmd2**
    | (None)
    | ``[CMD]``

    Run arbitrary shell command before ``extract``.

**postcmd2**
    | (None)
    | ``[CMD]``

    Run arbitrary shell command after ``extract``.

**precmd3**
    | (None)
    | ``[CMD]``

    Run arbitrary shell command before ``convert``.

**postcmd3**
    | (None)
    | ``[CMD]``

    Run arbitrary shell command after ``convert``.

**viewcmd**
    | (None)
    | ``[CMD]``

    Run arbitrary shell command
    when specified in commandline options (``-4`` or ``--view``).

    This is basically the same as 'precmds' or 'postcmds'.
    Only the triggering mechanism (``-4``) is different.
    The intended use case is to open a pdf viewer
    with the generated pdf filename supplied.

    The script includes a sample file ``open_viewer.py``
    (only for unixes with command ``ps``).
    It does opened file checks in addition.
    If the pdf file is already opened by the viewer,
    it does nothing.
    It can be used without full path.

    So, the simplest case would be::

        viewcmd=    okular conf.pdfname

    * 'okular' is a command name to open a pdf file.

    * conf.pdfname is expanded (from ``url``) to the actual pdf filename.

    If you want to use the sample::

        viewcmd=    open_viewer.py --command okular --check conf.pdfname

    * ``--check`` is the option flag to do above opened file checks.
    * ``--command`` can be arbitrary length with some options
      (e.g. ``--command 'okular --page 5'``).
      In that case, the first word is interpreted as the executable file name
      for the ``--check``.

    And one way to see the help is::

        $ tosixinch -4 --viewcmd 'open_viewer.py --help'

[style]
-------

The style options are made into a dictionary,
to be used in ``template css`` (``*.t.css``).

The look up name (key) is the same as each option name.

For examples, see the sample css
(``data/css/sample.t.css`` in installed directory).

Note that users can always choose (static) css rather than template css.
In that case, the style options have no effect.

So the options themselves have no meaning.
In the following, the roles in the sample file are explained.


**orientation**
    (``portrait``)

    Designate page orientation, portrait or landscape.

**portrait_size**
    (``90mm 118mm``)

    Designate portrait page size (width and height).
    The script use this value when ``orientation`` is ``portrait``.

    Ideally it should be full display size,
    but thinly clipped on height for versatility by default.
    In general, width is more precious than height in small display.

**landscape_size**
    (``118mm 90mm``)

    Designate landscape page size (width and height).
    The script use this value when ``orientation`` is ``landscape``.

**toc_depth**
    (``3``)

    Designate tree depth of PDF bookmarks (Table of Contents).
    Can only be used when ``converter`` is ``prince`` or ``weasyprint``.

**font_family**
    (``"DejaVu Sans", sans-serif``)

    Designate default font to use.

**font_mono**
    (``"Dejavu Sans Mono", monospace``)

    Designate default monospaced font to use.

**font_serif**
    (None)

    Not used.

**font_sans**
    (None)

    Not used.

**font_size**
    (``9px``)

    Designate default font size.

**font_size_mono**
    (``8px``)

    Designate default monospaced font size.

**font_scale**
    (``1``)

    Not used.

**line_height**
    (``1.3``)

    Designate default line height.


Converters
----------

Section ``prince``, ``weasyprint``, ``wkhtmltopdf`` and ``ebook-convert``
are converters sections.
They have common options
and single section is selected when ``convert``.

**cnvpath**
    (``prince``)

    The name or full path for the command as you type it in the shell.
    For ordinary installed ones, only the name would suffice,
    as in the default ``'prince'``.

    Currently ``'~'`` is not expanded.

**css**
    | (``sample``)
    | ``[COMMA]``

    css file names to be used in order when ``convert``.
    The names are just passed as commandline options to the converter.

    The files must be in ``css directory``,
    just the filenames (not full path).
    Or bundled sample css ``sample.t.css``,
    which can be abbreviated as ``sample``.
    You can mix both.

**cnvopts**
    | (None)
    | ``[CMD]``

    Other options (than css file option) to pass to the command.
    See ``tosixinch.default.ini`` for examples.


Site Sections
-------------

``site.ini`` should have many sections,
each is the settings for some specific site or the part of site.

They all have the same options,
in which the common options (the same ones as in ``tosixinch.ini``)
are not described here.

**match**
    (None)

    Glob string to match against input ``url``.

    Note that url path separator (``'/'``) is not special
    for wildcards (``'*?[]!'``),
    e.g. ``'*'`` matches any strings
    including all subdirectories.
    (Actually, it uses `fnmatch module <https://docs.python.org/3/library/fnmatch.html>`__,
    not `glob module <https://docs.python.org/3/library/glob.html>`__.).

    The script tries the values of this option from all the sections.
    The section with matched ``match`` option is used for the settings.

    If there are multiple matches,
    the one with the most path separator characters (``'/'``) is used.
    If there are multiple matches still,
    the last one is used.

    If there is no match, default settings are used,
    and ``guess`` option is tried.
    In this case, a placeholder value ``http://tosixinch.example.com``
    is set.

**select**
    | (None)
    | ``[LINE][XPATH]``

    Xpath strings to select elements from ``Downloaded File`` when ``extract``.
    Only selected elements are included
    in the ``<body>`` tag of the new ``Extracted File``,
    discarding others.

    Each line in the value will be connected with bar string (``'|'``)
    when evaluating.
    This means the sequence of selected elements are
    as the same order in ``Download File``,
    not grouped by each xpath (line).


**exclude**
    | (None)
    | ``[LINE][XPATH]``

    Xpath strings to remove elements from the new ``Extracted File`` when ``extract``.
    As in ``select``,
    each line in the value will be connected with bar string (``'|'``).

**process**
    | (None)
    | ``[COMMA]``

    After ``select`` and ``exclude``, arbitrary functions can be called
    if this option is specified.

    The function name must include the module name.
    And the function must be a top level one.
    (So each name should have exactly one dot (``'.'``)).

    It is searched in user ``userprocess`` directory
    and application ``process`` directory, in order.

    The first matched one is called with the argument ``'doc'`` auto-filled.
    It is ``lxml.html`` DOM object (``HtmlElement``),
    corresponding to the resultant ``Extracted File``
    after ``select`` and ``exclude``.
    The name (``'doc'``) is actually irrelevant.

    The function can have additional arguments.
    In that case, users have to provide them in the option string.
    String after ``'?'`` (and before next ``'?'``) is interpreted as an argument.

    For example, ``'aaa.bbb?cc?dd'`` is made into code either::

        userprocess.aaa.bbb(doc, cc, dd)

    or::

        process.aaa.bbb(doc, cc, dd)

    For actual functions and examples, see modules in `process <api.html#process>`__.

**javascript**
    | (``False``)
    | ``[BOOL]``

    If this value is ``True``, downloading is done by ``Qt``.

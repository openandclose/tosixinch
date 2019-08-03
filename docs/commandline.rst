
Commandline Options
===================

Commandline options are grouped by
``General``, ``Actions``, ``Programs``, ``Configs`` and ``Styles``.

Some ``Actions`` are single actions,
exiting after executing, ignoring other ``Actions``.
Others are sequential actions.
See `Actions <overview.html#actions>`__.

Many options are related to only a specific ``Action``.
Unrelated options are just ignored.

``Configs`` and ``Styles`` options are mostly the same
as `Config Options <options.html>`__.
You have to format commandline strings,
following the rules specified there
(according to `Value Functions <overview.html#value-functions>`__).

.. note::

    For ``[LINE]`` options,
    it may not be easy to actually supply multiple values.

    For example, an option in a configuration file
    becomes like this in bash::

        opt=    aaa
                bbb

    ::
    
        --opt $'aaa\\nbbb'



.. autogenerate


General
-------

.. option:: -i INPUT, --input INPUT

    input url or file path. it can be specified multiple times

.. option:: -f FILE, --file FILE

    file to read inputs. only one file

        default=urls.txt

.. option:: -h, --help

    show this help message and exit

.. option:: -v, --verbose

    print out more detailed log messages

Actions
-------

.. option:: -1, --download

    download by default downloader

.. option:: -2, --extract

    extract by default extractor

.. option:: -3, --convert

    convert by default converter

.. option:: -4, --view

    open a pdf viewer if configured

.. option:: -a, --appcheck

    print application settings after command line evaluation, and exit

.. option:: -b, --browser

    open (first) extracted html in browser and exit

.. option:: -c, --check

    print matched url settings and exit (so you have to supply url some way)

.. option:: --toc

    create toc htmls and a toc url list. conflicts with '--input'.

.. option:: --link

    get links in documents from urls (experimental)

.. option:: --news {hackernews}

    fetch urls from socialnews site (experimental)

        choices=hackernews

.. option:: --printout {0,1,2,3,all}

    print filenames the scripts' actions would create  (0=url, 1=Downloaded_Files, 2=Extracted_Files, 3=pdfname, all=0<tab>1<tab>2)

        choices=0, 1, 2, 3, all

.. option:: --sample-urls

    inject sample urls

Programs
--------

.. option:: --urllib

    download by urllib (default, and no other option)

.. option:: --lxml

    extract by lxml (default)

.. option:: --readability

    extract by readability, if no settings matched

.. option:: --readability-only

    extract by readability unconditionally

.. option:: --prince

    convert by princexml

.. option:: --weasyprint

    convert by weasyprint

.. option:: --wkhtmltopdf

    convert by wkhtmltopdf

Configs
-------

.. option:: --user-agent USER_AGENT

    set http header user-agent when downloading by urllib (to see the default, run --appcheck)

.. option:: --qt {webengine,webkit}

    use either webengine or webkit (default) when running Qt

        choices=webengine, webkit

.. option:: --encoding ENCODING

    assign an encoding for file opening when extract [COMMA]

.. option:: --encoding-errors { (choices...) }

    assign an encoding error handler (default: strict)

        choices=strict, ignore, replace, xmlcharrefreplace, backslashreplace, namereplace, surrogateescape, surrogatepass

.. option:: --guess GUESS

    if there is no matched url, use this xpath for content selection [LINE]

.. option:: --parts-download

    download components (images etc.) before PDF conversion (default)

.. option:: --no-parts-download

    not download components before PDF conversion

.. option:: --force-download

    force --download or --parts-download even if the file already exists

.. option:: --add-binary-extensions ADD_BINARY_EXTENSIONS

    add or subtract to-skip-binaries-extension list [PLUS]

.. option:: --add-clean-tags ADD_CLEAN_TAGS

    add or subtract to-delete-tag list [PLUS]

.. option:: --add-clean-attrs ADD_CLEAN_ATTRS

    add or subtract to-delete-attribute list [PLUS]

.. option:: --textwidth TEXTWIDTH

    width (character numbers) for rendering non-prose text

.. option:: --textindent TEXTINDENT

    line continuation marker for rendering non-prose text

.. option:: --trimdirs TRIMDIRS

    remove leading directories from local text name to shorten title

.. option:: --raw

    use input paths as is (no url transformation, and only for local files)

.. option:: --pdfname PDFNAME

    override pdf file name

.. option:: --cnvpath CNVPATH

    override the converter executable path. you also need to set the converter itself

.. option:: --viewcmd VIEWCMD

    commandline string to open the pdf viewer [CMD]

.. option:: --userdir USERDIR

    override user configuration directory

.. option:: --nouserdir

    do not parse user configuration (intended for testing)

.. option:: --use-urlreplace {yes,no}

    use url replacement feature (default: yes)

        choices=yes, no

Styles
------

.. option:: --orientation {portrait,landscape}

    portrait(default) or landscape, determine which size data to use

        choices=portrait, landscape

.. option:: --portrait-size PORTRAIT_SIZE

    portrait size for the css, e.g. '90mm 118mm'

.. option:: --landscape-size LANDSCAPE_SIZE

    landscape size for the css, e.g. '118mm 90mm'

.. option:: --toc-depth TOC_DEPTH

    tree depth of table of contents (only for prince and weasyprint)

.. option:: --font-family FONT_FAMILY

    main font for the css, e.g. '"DejaVu Sans", sans-serif'

.. option:: --font-mono FONT_MONO

    monospace font for the css

.. option:: --font-serif FONT_SERIF

    serif font for the css (not used by sample)

.. option:: --font-sans FONT_SANS

    sans font for the css (not used by sample)

.. option:: --font-size FONT_SIZE

    main font size for the css, e.g. '9px'

.. option:: --font-size-mono FONT_SIZE_MONO

    monospace font size for the css

.. option:: --line-height LINE_HEIGHT

    'adjust spaces between lines, number like '1.3'

.. option:: --font-scale FONT_SCALE

    number like 1.5 to scale font sizes (not yet used by sample)

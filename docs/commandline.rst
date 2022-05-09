
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

.. option:: -q, --quiet

    supress non-critical log messages

.. option:: -V, --version

    print version and exit

.. option:: --userdir USERDIR

    specify user configuration directory

.. option:: --nouserdir

    disable user configuration (intended for testing)

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

    open (first) extracted html in browser, and exit

.. option:: -c, --check

    print matched url settings, and exit (so you have to supply url some way)

.. option:: --toc

    create toc htmls and a toc url list. conflicts with '--input'.

.. option:: --inspect

    parse downloaded htmls, and do arbitrary things user specified

.. option:: --printout {0,1,2,3,all}

    print filenames the scripts' actions would create (0=url, 1=Downloaded_Files, 2=Extracted_Files 3=pdfname, all=0<tab>1<tab>2)

        choices=0, 1, 2, 3, all

Programs
--------

.. option:: --urllib

    download by urllib (default)

.. option:: --headless

    download by one of headless browser engines (see --browser-engine)

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

.. option:: --cnvpath CNVPATH

    specify converter executable path. also need to set converter itself

.. option:: --css2 CSS2

    specify css files, for converter commandline css option

.. option:: --cnvopts CNVOPTS

    specify converter commandline options

Configs
-------

.. option:: --user-agent USER_AGENT

    set http request user-agent (only for urllib)

.. option:: --timeout TIMEOUT

    set http request timeout (only for urllib)

.. option:: --interval INTERVAL

    interval for each download

.. option:: --browser-engine {webkit,webengine,selenium-chrome,selenium-firefox}

    specify the browser library when downloader is 'headless'

        choices=webkit, webengine, selenium-chrome, selenium-firefox

.. option:: --selenium-chrome-path SELENIUM_CHROME_PATH

    specify the path of chromedriver for selenium

.. option:: --selenium-firefox-path SELENIUM_FIREFOX_PATH

    specify the path of geckodriver for selenium

.. option:: --encoding ENCODING

    assign an encoding for file opening when extract (f: comma)

.. option:: --encoding-errors { (choices...) }

    assign an encoding error handler (default: strict)

        choices=strict, ignore, replace, xmlcharrefreplace, backslashreplace, namereplace, surrogateescape, surrogatepass

.. option:: --parts-download

    download components (images etc.) before PDF conversion (default: True)

.. option:: --no-parts-download

    not download components before PDF conversion

.. option:: --force-download

    force '--download' and '--parts-download' even if the file already exists

.. option:: --guess GUESS

    if there is no matched url, use this xpath for content selection (f: line)

.. option:: --full-image FULL_IMAGE

    pixel size to add special class attributes to images (default: 200)

.. option:: --add-binary-extensions ADD_BINARY_EXTENSIONS

    add or subtract to-skip-binaries-extension list (f: plus_binaries)

.. option:: --add-clean-tags ADD_CLEAN_TAGS

    add or subtract to-delete-tag list (f: plus)

.. option:: --add-clean-attrs ADD_CLEAN_ATTRS

    add or subtract to-delete-attribute list (f: plus)

.. option:: --elements-to-keep-attrs ELEMENTS_TO_KEEP_ATTRS

    specify elements (Xpath) in which you want to keep attributes (default: <math>, <svg> and some mathjax tags) (f: line)

.. option:: --ftype {html,prose,nonprose,python}

    specify file type

        choices=html, prose, nonprose, python

.. option:: --textwidth TEXTWIDTH

    width (character numbers) for rendering non-prose text

.. option:: --textindent TEXTINDENT

    line continuation marker for rendering non-prose text

.. option:: --trimdirs TRIMDIRS

    if plus, remove leading directories from PDF title of local text name. if minus, remove leading directories to reduce path segments to that abs number. (default: 3)

.. option:: --raw

    use input paths as is (no url transformation, and only for local files)

.. option:: --pdfname PDFNAME

    override pdf file name

.. option:: --viewcmd VIEWCMD

    commandline string to open the pdf viewer (f: cmds)

Styles
------

.. option:: --orientation {portrait,landscape}

    portrait (default) or landscape, determine which size data to use

        choices=portrait, landscape

.. option:: --portrait-size PORTRAIT_SIZE

    portrait size for css, e.g. '90mm 118mm'

.. option:: --landscape-size LANDSCAPE_SIZE

    landscape size for css, e.g. '118mm 90mm'

.. option:: --toc-depth TOC_DEPTH

    specify depth of table of contents

.. option:: --font-family FONT_FAMILY

    main font for css, e.g. '"DejaVu Sans", sans-serif'

.. option:: --font-mono FONT_MONO

    monospace font for css

.. option:: --font-serif FONT_SERIF

    serif font for css (not used by sample)

.. option:: --font-sans FONT_SANS

    sans font for css (not used by sample)

.. option:: --font-size FONT_SIZE

    main font size for css, e.g. '9px'

.. option:: --font-size-mono FONT_SIZE_MONO

    monospace font size for css

.. option:: --font-scale FONT_SCALE

    number like 1.5 to scale base font sizes (default: 1.0)

.. option:: --line-height LINE_HEIGHT

    adjust line height (default: 1.3)

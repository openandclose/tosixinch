
Commandline Options
===================

Commandline options are grouped by
``General``, ``Actions``, ``Programs``, ``Configs`` and ``Styles``.

Main ``Actions`` are ``--download``, ``--extract``, ``--convert`` and ``--view``
(or ``-1``, ``-2``, ``-3`` and ``-4``).
They can be mixed, or concatenated,
and in that case the option order is irrelevant,
the script always calls '1, 2, 3, 4' in order.

``--toc`` can also be mixed, in the context that makes sense.

Other ``Actions`` are mostly one-off,
intended to be used independently
(only one action in one invocation).

Many options are related to a specific ``Action``.
Unrelated options are just ignored when running some ``Action``.

``Configs`` and ``Styles`` options are mostly the same as config file options,
and the same rules for option field (for ``value functions``) apply.

.. note::
    For [LINE] options,
    it may not be easy to autually supply multiple values.
    For example, using ``'\n'`` in bash, you need to quote by
    a single quote prefixed with ``'$'``. ::

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

    create toc htmls and a toc url list

.. option:: --link

    get links in documents from urls (experimental)

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

.. option:: --ebook-convert

    convert by ebook-convert

Configs
-------

.. option:: --user-agent USER_AGENT

    set http header user-angent when donloading by urllib (to see the default, run --appcheck)

.. option:: --qt {webengine,webkit}

    use either webengine or webkit (default) when running Qt

        choices=webengine, webkit

.. option:: --guess GUESS

    if there is no matched url, use this xpath for content selection [LINE]

.. option:: --parts-download

    download components (images etc.) before PDF conversion (default)

.. option:: --no-parts-download

    not download components before PDF conversion

.. option:: --add-binaries ADD_BINARIES

    add or subtract to-skip-binaries-extention list [COMMA]

.. option:: --add-tags ADD_TAGS

    add or subtract to-delete-tag list [COMMA]

.. option:: --add-attrs ADD_ATTRS

    add or subtract to-delete-attribute list [COMMA]

.. option:: --raw

    use input paths as is (no url transformation, and only for local files)

.. option:: --textwidth TEXTWIDTH

    width (character numbers) for rendering non-prose text

.. option:: --textindent TEXTINDENT

    line continuation marker for rendering non-prose text

.. option:: --add-filters ADD_FILTERS

    add or subtract regex strings for filtering when printing files in directories [COMMA]

.. option:: --viewcmd VIEWCMD

    commandline string to open the pdf viewer [CMD]

.. option:: --userdir USERDIR

    override user configuration directory

.. option:: --nouserdir

    do not parse user configuration (intended for testing)

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

.. option:: --font-size FONT_SIZE

    main font size for the css, e.g. '9px'

.. option:: --font-size-mono FONT_SIZE_MONO

    monospace font size for the css

.. option:: --line-height LINE_HEIGHT

    'adjust spaces between lines, number like '1.3'

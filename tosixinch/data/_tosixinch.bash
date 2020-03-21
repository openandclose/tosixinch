# bash completion file for tosixinch
_tosixinch()
{
    local cur prev words cword split
    _init_completion -s || return

    case $prev in
        --add-binary-extensions|--add-clean-attrs|--add-clean-tags|--css2|--font-family|--font-mono|--font-sans|--font-scale|--font-serif|--font-size|--font-size-mono|--full-image|--guess|--landscape-size|--line-height|--pdfname|--portrait-size|--textindent|--textwidth|--toc-depth|--trimdirs|--user-agent|--viewcmd)
            return
            ;;
        --browser-engine)
            COMPREPLY=( $( compgen -W 'webkit webengine' -- "$cur" ) )
            return
            ;;
        --encoding)
            COMPREPLY=( $( compgen -W 'ascii big5 big5hkscs cp037 cp1006 cp1026 cp1125 cp1140 cp1250 cp1251 cp1252 cp1253 cp1254 cp1255 cp1256 cp1257 cp1258 cp273 cp424 cp437 cp500 cp65001 cp720 cp737 cp775 cp850 cp852 cp855 cp856 cp857 cp858 cp860 cp861 cp862 cp863 cp864 cp865 cp866 cp869 cp874 cp875 cp932 cp949 cp950 euc-jis-2004 euc-jisx0213 euc-jp euc-kr gb18030 gb2312 gbk hz iso2022-jp iso2022-jp-1 iso2022-jp-2 iso2022-jp-2004 iso2022-jp-3 iso2022-jp-ext iso2022-kr iso8859-10 iso8859-11 iso8859-13 iso8859-14 iso8859-15 iso8859-16 iso8859-2 iso8859-3 iso8859-4 iso8859-5 iso8859-6 iso8859-7 iso8859-8 iso8859-9 johab koi8-r koi8-t koi8-u kz1048 latin-1 mac-cyrillic mac-greek mac-iceland mac-latin2 mac-roman mac-turkish mbcs oem ptcp154 shift-jis shift-jis-2004 shift-jisx0213 utf-16 utf-16-be utf-16-le utf-32 utf-32-be utf-32-le utf-7 utf-8 utf-8-sig' -- "$cur" ) )
            return
            ;;
        --encoding-errors)
            COMPREPLY=( $( compgen -W 'strict ignore replace xmlcharrefreplace backslashreplace namereplace surrogateescape surrogatepass' -- "$cur" ) )
            return
            ;;
        --ftype)
            COMPREPLY=( $( compgen -W 'html prose nonprose python' -- "$cur" ) )
            return
            ;;
        --news)
            COMPREPLY=( $( compgen -W 'hackernews' -- "$cur" ) )
            return
            ;;
        --orientation)
            COMPREPLY=( $( compgen -W 'portrait landscape' -- "$cur" ) )
            return
            ;;
        --printout)
            COMPREPLY=( $( compgen -W '0 1 2 3 all' -- "$cur" ) )
            return
            ;;
        --cnvpath|--file|--input|-f|-i)
            _filedir
            return
            ;;
        --userdir)
            _filedir -d
            return
            ;;
    esac

    $split && return

    COMPREPLY=( $( compgen -W '--add-binary-extensions --add-clean-attrs --add-clean-tags --appcheck --browser --browser-engine --check --cnvpath --convert --css2 --download --encoding --encoding-errors --extract --file --font-family --font-mono --font-sans --font-scale --font-serif --font-size --font-size-mono --force-download --ftype --full-image --guess --help --input --landscape-size --line-height --link --lxml --news --no-parts-download --nouserdir --orientation --parts-download --pdfname --portrait-size --prince --printout --quiet --raw --readability --readability-only --textindent --textwidth --toc --toc-depth --trimdirs --urllib --user-agent --userdir --verbose --version --view --viewcmd --weasyprint --wkhtmltopdf' -- "$cur" ) )
    [[ $COMPREPLY == *= ]] && compopt -o nospace
    return

    _filedir
} &&
complete -F _tosixinch tosixinch

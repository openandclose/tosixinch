_tosixinch()
{
    local cur prev words cword split
    _init_completion -s || return

    case $prev in
        --add-binary-extensions|--add-clean-attrs|--add-clean-tags|--font-family|--font-mono|--font-sans|--font-scale|--font-serif|--font-size|--font-size-mono|--guess|--landscape-size|--line-height|--pdfname|--portrait-size|--textindent|--textwidth|--toc-depth|--user-agent|--viewcmd)
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
        --qt)
            COMPREPLY=( $( compgen -W 'webengine webkit' -- "$cur" ) )
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

    COMPREPLY=( $( compgen -W '--add-binary-extensions --add-clean-attrs --add-clean-tags --appcheck --browser --check --cnvpath --convert --download --ebook-convert --extract --file --font-family --font-mono --font-sans --font-scale --font-serif --font-size --font-size-mono --force-download --guess --help --input --landscape-size --line-height --link --lxml --news --no-parts-download --nouserdir --orientation --parts-download --pdfname --portrait-size --prince --qt --raw --readability --readability-only --sample-urls --textindent --textwidth --toc --toc-depth --urllib --user-agent --userdir --verbose --view --viewcmd --weasyprint --wkhtmltopdf' -- "$cur" ) )
    [[ $COMPREPLY == *= ]] && compopt -o nospace
    return

    _filedir
} &&
complete -F _tosixinch tosixinch

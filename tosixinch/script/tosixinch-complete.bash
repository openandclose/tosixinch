_tosixinch()
{
    local cur prev words cword split
    _init_completion -s || return

    case $prev in
        --add-attrs|--add-binaries|--add-filters|--add-tags|--appcheck|--browser|--check|--font-family|--font-mono|--font-size|--font-size-mono|--guess|--help|--landscape-size|--line-height|--link|--portrait-size|--textindent|--textwidth|--toc|--toc-depth|--user-agent|--viewcmd|-a|-b|-c|-h)
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
        --file|--input|-f|-i)
            _filedir
            return
            ;;
        --userdir)
            _filedir -d
            return
            ;;
    esac

    $split && return

    if [[ $cur == -* ]]; then
        COMPREPLY=( $( compgen -W '--add-attrs --add-binaries --add-filters --add-tags --appcheck --browser --check --convert --download --ebook-convert --extract --file --font-family --font-mono --font-size --font-size-mono --guess --help --input --landscape-size --line-height --link --lxml --no-parts-download --nouserdir --orientation --parts-download --portrait-size --prince --qt --raw --readability --readability-only --textindent --textwidth --toc --toc-depth --urllib --user-agent --userdir --verbose --view --viewcmd --weasyprint --wkhtmltopdf' -- "$cur" ) )
        [[ $COMPREPLY == *= ]] && compopt -o nospace
        return
    fi

    _filedir
} &&
complete -F _tosixinch tosixinch

# bash completion file for {{ prog }}

{{ prefix }}{{ prog }}()
{
    local cur prev words cword split
    _init_completion -s || return

    case $prev in
        {{ no_comp }})
            return
            ;;
        {% for c in choices -%}
        {{ c.opt}})
            COMPREPLY=( $( compgen -W '{{ c.choices }}' -- "$cur" ) )
            return
            ;;
        {% endfor -%}
        {{ file_comp }})
            _filedir
            return
            ;;
        {{ dir_comp }})
            _filedir -d
            return
            ;;
    esac

    $split && return

    COMPREPLY=( $( compgen -W '{{ all_opts }}' -- "$cur" ) )
    [[ $COMPREPLY == *= ]] && compopt -o nospace

} &&
complete -F {{ prefix }}{{ prog }} {{ prog }}

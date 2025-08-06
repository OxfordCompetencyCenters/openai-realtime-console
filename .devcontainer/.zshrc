# Setup zsh git information
autoload -Uz vcs_info
precmd() {
    vcs_info
}
zstyle ':vcs_info:git:*' formats '[%b] '

# Define shell prompt
setopt PROMPT_SUBST
NEWLINE=$'\n'
PROMPT='\
${NEWLINE}\
%F{#E7E4D9}${(r:72::─:)}%f${NEWLINE}${NEWLINE}\
%B${VIRTUAL_ENV_PROMPT}[%D{%Y-%m-%dT%H:%M:%S}] %n@%m:%d%f ${vcs_info_msg_0_}%b${NEWLINE}\
> '

# uv shell autocompletion
eval "$(uv generate-shell-completion zsh)"

_uv_run_mod() {
    if [[ "$words[2]" == "run" && "$words[CURRENT]" != -* ]]; then
        local venv_binaries
        if [[ -d ${UV_PROJECT_ENVIRONMENT}/bin ]]; then
            venv_binaries=( ${(@f)"$(_call_program files ls -1 ${UV_PROJECT_ENVIRONMENT}/bin 2>/dev/null)"} )
        fi

        _alternative \
            'files:filename:_files' \
            "binaries:venv binary:(($venv_binaries))"
    else
        _uv "$@"
    fi
}
compdef _uv_run_mod uv

# Restore bash word style navigation and interactive comments
autoload -U select-word-style
select-word-style bash
setopt INTERACTIVE_COMMENTS
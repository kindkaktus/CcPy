#!/bin/bash

# Non-interactively persist a CcPy password environment variable in /etc/environment.
#
# Usage:
#   sudo ./setup_ccpy_smtp_password_env.sh 'VARIABLE_NAME'='real-password'
#
# Example:
#   sudo ./setup_ccpy_smtp_password_env.sh 'CCPY_SMTP_PASSWORD'='real-password'

set -euo pipefail

readonly ENVIRONMENT_FILE="/etc/environment"

function usage()
{
    echo "Usage: sudo $0 'VARIABLE_NAME'='real-password'" >&2
    echo "Example: sudo $0 'CCPY_SMTP_PASSWORD'='real-password'" >&2
    exit 1
}

function fail()
{
    echo "ERROR: $*" >&2
    exit 1
}

function validate()
{
    local _assignment="${1:-}"
    local _variable_name
    local _password

    if [[ $# -ne 1 || "${_assignment}" != *=* ]]; then
        usage
    fi

    if [[ "${EUID}" -ne 0 ]]; then
        fail "Run as root, for example: sudo $0 'VARIABLE_NAME'='real-password'"
    fi

    _variable_name="${_assignment%%=*}"
    _password="${_assignment#*=}"

    if [[ ! "${_variable_name}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
        fail "Invalid environment variable name: ${_variable_name}"
    fi

    if [[ -z "${_password}" ]]; then
        fail "${_variable_name} is empty"
    fi

    if [[ "${_password}" == *$'\n'* || "${_password}" == *$'\r'* ]]; then
        fail "${_variable_name} must not contain newlines"
    fi
}

function quote_environment_value()
{
    local _value="$1"

    _value="${_value//\\/\\\\}"
    _value="${_value//\"/\\\"}"
    _value="${_value//\$/\\\$}"
    _value="${_value//\`/\\\`}"
    printf '"%s"' "${_value}"
}

function update_environment_file()
{
    local _variable_name="$1"
    local _password="$2"
    local _tmp_file

    _tmp_file="$(mktemp "${ENVIRONMENT_FILE}.ccpy.XXXXXX")"
    trap "rm -f '${_tmp_file}'" EXIT

    if [[ -f "${ENVIRONMENT_FILE}" ]]; then
        awk -v key="${_variable_name}" '
            BEGIN { pattern = "^[[:space:]]*" key "[[:space:]]*=" }
            $0 !~ pattern { print }
        ' "${ENVIRONMENT_FILE}" > "${_tmp_file}"
        chmod --reference="${ENVIRONMENT_FILE}" "${_tmp_file}"
        chown --reference="${ENVIRONMENT_FILE}" "${_tmp_file}"
    else
        chmod 0644 "${_tmp_file}"
        chown root:root "${_tmp_file}"
    fi

    printf '%s=%s\n' "${_variable_name}" "$(quote_environment_value "${_password}")" >> "${_tmp_file}"
    mv "${_tmp_file}" "${ENVIRONMENT_FILE}"
    trap - EXIT
}

function print_success()
{
    local _variable_name="$1"

    echo "Updated ${ENVIRONMENT_FILE} with ${_variable_name}."
    echo "Use <passwordEnvVar>${_variable_name}</passwordEnvVar> in ccpy.conf."
    echo "./ccpy.sh will load ${ENVIRONMENT_FILE} before starting CcPy."
}

function main()
{
    local _assignment
    local _variable_name
    local _password

    validate "$@"
    _assignment="$1"
    _variable_name="${_assignment%%=*}"
    _password="${_assignment#*=}"

    update_environment_file "${_variable_name}" "${_password}"
    print_success "${_variable_name}"
}

main "$@"

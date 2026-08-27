#!/bin/bash
# Rabbit environment for PlotTools.
#
#   source setup_rabbit.sh   -> on
#   rabbit_off               -> off (restores PATH/PYTHONPATH exactly)
#
# The venv is built with --system-site-packages on top of cmsenv, so ROOT,
# numpy, uproot and the PlotTools modules stay importable while it is active.
# Run cmsenv first.

if [ -z "${BASH_SOURCE[0]}" ]; then
    echo "setup_rabbit.sh: must be sourced from bash" >&2
    return 1 2>/dev/null || exit 1
fi

_RABBIT_PLOTTOOLS_BASE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
_RABBIT_VENV="${_RABBIT_PLOTTOOLS_BASE}/rabbit_env"
_RABBIT_SRC="${_RABBIT_PLOTTOOLS_BASE}/rabbit"

if [ ! -f "${_RABBIT_VENV}/bin/activate" ]; then
    echo "setup_rabbit.sh: no venv at ${_RABBIT_VENV}. See the header of this file." >&2
    return 1
fi

if [ -n "${RABBIT_ACTIVE}" ]; then
    echo "rabbit env already active (rabbit_off to leave)"
    return 0
fi

export _RABBIT_SAVED_PATH="${PATH}"
export _RABBIT_SAVED_PYTHONPATH="${PYTHONPATH}"
export _RABBIT_SAVED_PYTHONWARNINGS="${PYTHONWARNINGS}"

source "${_RABBIT_VENV}/bin/activate"

export RABBIT_BASE="${_RABBIT_SRC}"
export PYTHONPATH="${_RABBIT_SRC}:${_RABBIT_PLOTTOOLS_BASE}:${PYTHONPATH}"
export PATH="${_RABBIT_SRC}/bin:${PATH}"

# XLA multi-threaded Eigen on CPU, as rabbit/setup.sh does.
if [[ ":${XLA_FLAGS:-}:" != *":--xla_cpu_multi_thread_eigen=true:"* ]]; then
    export XLA_FLAGS="${XLA_FLAGS:+$XLA_FLAGS }--xla_cpu_multi_thread_eigen=true"
fi

# CMSSW's numpy prints a subnormal-detection warning on every import once TF has
# set flush-to-zero. Scoped to that one module so real warnings still surface.
export PYTHONWARNINGS="ignore::UserWarning:numpy.core.getlimits"

export RABBIT_ACTIVE=1

rabbit_off() {
    if [ -z "${RABBIT_ACTIVE}" ]; then
        echo "rabbit env is not active"
        return 0
    fi
    type deactivate >/dev/null 2>&1 && deactivate
    export PATH="${_RABBIT_SAVED_PATH}"
    export PYTHONPATH="${_RABBIT_SAVED_PYTHONPATH}"
    export PYTHONWARNINGS="${_RABBIT_SAVED_PYTHONWARNINGS}"
    unset RABBIT_ACTIVE RABBIT_BASE
    unset _RABBIT_SAVED_PATH _RABBIT_SAVED_PYTHONPATH _RABBIT_SAVED_PYTHONWARNINGS
    echo "rabbit env off"
}

echo "rabbit env on   (RABBIT_BASE=${RABBIT_BASE})"
echo "  python3 $(python3 --version 2>&1 | cut -d' ' -f2) | rabbit_off to leave"

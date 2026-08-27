#!/bin/bash
# Build rabbit_env/ from scratch. One-time, or after deleting a stale/broken env.
#
#   cmsenv
#   git submodule update --init rabbit   # if rabbit/ is empty
#   ./setup_rabbit_env.sh
#   source setup_rabbit.sh               # activate for day-to-day use
#
# CMSSW ships SciPy 1.10, whose minimizer callback signature silently disables
# the rabbit fit (every fit just returns its start values) -- pin scipy<1.14
# instead. After building, verify the env with a real fit whose answer differs
# from its start point (see COMBINE_FIXES.md).

set -e
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${BASE}/rabbit_env"
SRC="${BASE}/rabbit"

if [ ! -f "${SRC}/pyproject.toml" ]; then
    echo "setup_rabbit_env.sh: ${SRC} looks empty -- run 'git submodule update --init rabbit' first." >&2
    exit 1
fi

python3 -m venv --system-site-packages "${VENV}"
source "${VENV}/bin/activate"
pip install --upgrade pip
pip install -e "${SRC}[all]"
pip install "scipy<1.14"
deactivate

echo "rabbit_env built at ${VENV}. 'source setup_rabbit.sh' to activate, then run a real fit to verify."

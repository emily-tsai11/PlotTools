#!/bin/bash
if [ ! -z $LD_LIBRARY_PATH_STORED ]; then
  echo "Using LD_LIBRARY_PATH_STORED"
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH_STORED:$LD_LIBRARY_PATH
fi


action() {
    local base="$( cd "$( dirname "$this_file" )" && pwd )"
    export PYTHONPATH="$base:$PYTHONPATH"
    export PYTHON3PATH="$base:$PYTHON3PATH"
    export PATH="$base:$PATH"
    export PYTHONPATH="$base/analysis:$PYTHONPATH"
    export PYTHONPATH="$base/utilities:$PYTHONPATH"
    export PYTHON3PATH="$base/analysis:$PYTHON3PATH"
    export PYTHON3PATH="$base/utilities:$PYTHON3PATH"
    export PATH="$base/analysis:$PATH"
}
action

alias python=python3
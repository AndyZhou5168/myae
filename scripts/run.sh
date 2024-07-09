#!/bin/bash

set -e
set -u

if [ -e ./myae.config ]; then
    source ./myae.config
elif [ -e ../myae.config ]; then
    source ../myae.config
else
    echo "Error: not found 'myae.config'!!!"
    exit 1
fi

if check_number $1; then
    echo "Usage: run.sh <image ID> [<architecture>]"
    exit 1
fi

IID=${1}
ARCH=${2}

${SCRIPT_DIR}/run.${ARCH}.sh ${IID}

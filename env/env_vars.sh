#! /usr/bin/env bash

# BOT_NAME, DISCORD_TOKEN, and BOT_PREFIX must be set in an .env file in this directory
source "${CONDA_PREFIX}/etc/conda/activate.d/.env"

if [ -z "${PYTHONPATH}" ]; then
    PYTHONPATH="${ROOT_DIR}/src"
else
    PYTHONPATH="${ROOT_DIR}/src:${PYTHONPATH}"
fi
export PYTHONPATH

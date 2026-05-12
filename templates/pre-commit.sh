#!/bin/sh

USE_VENV={%%USEVENV%%}

if [ "${USE_VENV}" -eq 0 ]; then
  if [ -z "${VIRTUAL_ENV}" ]; then
    printf "Starting virtual environment...\n"
    VENV_DIR="{%%VENVDIR%%}"
    . "${VENV_DIR}/bin/activate"
  else
    USE_VENV=1
  fi
fi

printf "Formatting code using ruff...\n"
ruff format .
RUFF_FORMAT_RTN="$?"

if [ "${RUFF_FORMAT_RTN}" -ne 0 ]; then
  if [ "${USE_VENV}" -eq 0 ]; then
    deactivate
  fi
  printf "Code formatting failed, aborting\n"
  exit 1
fi
printf "Code formatting complete.\n\n"

printf "Checking and fixing code using ruff...\n"
ruff check --fix .
RUFF_CHECK_RTN="$?"

if [ "${RUFF_CHECK_RTN}" -ne 0 ]; then
  if [ "${USE_VENV}" -eq 0 ]; then
    deactivate
  fi
  printf "Linting checks failed with unfixable errors, aborting\n"
  exit 1
fi
printf "Linting checks passed.\n\n"

git add -u

if [ "${USE_VENV}" -eq 0 ]; then
  printf "Deactivating virtual environment\n"
  deactivate
fi
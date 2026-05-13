#!/bin/sh

USE_VENV={%%USEVENV%%}
RUFF="{%%RUFFBIN%%}"

if [ "${USE_VENV}" -eq 0 ]; then
  if [ -z "${VIRTUAL_ENV}" ]; then
    printf "Starting virtual environment...\n"
    VENV_DIR="{%%VENVDIR%%}"
    . "${VENV_DIR}/bin/activate"
  else
    USE_VENV=1
  fi
fi

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.pyi?$')

if [ -z "${STAGED_FILES}" ]; then
  printf "No Python files staged, nothing to check.\n"
  if [ "${USE_VENV}" -eq 0 ]; then
    deactivate
  fi
  exit 0
fi

printf "Formatting staged files using ruff...\n"
printf '%s\n' "${STAGED_FILES}" | xargs "${RUFF}" format
RUFF_FORMAT_RTN="$?"

if [ "${RUFF_FORMAT_RTN}" -ne 0 ]; then
  if [ "${USE_VENV}" -eq 0 ]; then
    deactivate
  fi
  printf "Code formatting failed, aborting\n"
  exit 1
fi
printf "Code formatting complete.\n\n"

printf "Checking and fixing staged files using ruff...\n"
printf '%s\n' "${STAGED_FILES}" | xargs "${RUFF}" check --fix
RUFF_CHECK_RTN="$?"

if [ "${RUFF_CHECK_RTN}" -ne 0 ]; then
  if [ "${USE_VENV}" -eq 0 ]; then
    deactivate
  fi
  printf "Linting checks failed with unfixable errors, aborting\n"
  exit 1
fi
printf "Linting checks passed.\n\n"

printf '%s\n' "${STAGED_FILES}" | xargs git add

if [ "${USE_VENV}" -eq 0 ]; then
  printf "Deactivating virtual environment\n"
  deactivate
fi

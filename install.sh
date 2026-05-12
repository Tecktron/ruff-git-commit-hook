#!/bin/bash

function show_help {
  printf "Installs a git pre-commit hook that runs ruff (format + lint) on your code\n"
  printf "before each commit. Unless told otherwise, this will also install ruff and\n"
  printf "write a ruff config into the target project's pyproject.toml.\n"
  printf "Usage: install.sh [option] /path/to/dir\n"
  printf "Required:\n"
  printf " /path/to/dir  | Path to the directory where you wish to install the githook\n"
  printf "Install option choices (only 1 accepted):\n"
  printf " -h   | Help, Show this help message and exit\n"
  printf " -s   | Skip Packages, skip trying to install ruff if it is not found\n"
  printf " -w   | Git Hook Only, install only the git hook, no config files\n"
  printf " -c   | Configs only, write only the config files, no git hook\n"
  printf "\nOptional config choices (skipped if -w is used)\n"
  printf " -l # | Specify a custom line length (optional, default is 120)\n"
  printf " -t v | Specify a Python target version (optional, default is py312)\n"
  printf "\n"
}

function program_is_installed {
  local return_=0
  type $1 >/dev/null 2>&1 || { local return_=1; }
  echo "$return_"
}

function os_check {
  local result=0
  if [ "$1" == 'Linux' ]; then
    local result=1
  elif [ "$1" == 'Darwin' ]; then
    local result=2
  fi
  echo $result
}

function in_venv {
  if [ -n "${VIRTUAL_ENV}" ]; then
    echo "0"
  else
    echo "1"
  fi
}

function abspath {
  local ABSPATH
  ABSPATH=$(cd "$1" && pwd -P)
  echo "${ABSPATH}/"
}

function check_python_version {
  python3 -c "import platform; m,n,_ = map(int, platform.python_version_tuple()); exit(0 if m >= 3 and n >= 11 else 1)" >/dev/null
  echo "$?"
}

function install_python_package {
  echo " " >&2
  pip3 install --upgrade "$1" >&2
  echo "$?"
}

function check_dir {
  if [ -d "$1" ]; then
    echo 0
  else
    echo 1
  fi
}

OS=$(uname)
OS_TYPE=$(os_check $OS)

if [ "${OS_TYPE}" == 0 ]; then
  echo "Sorry, your OS is not supported. Goodbye."
  exit 8
fi

printf "\e[1;106;35mRuff Git Hook Installer\e[0m\n"

SKIP_PACKAGES=0
GITHOOK_ONLY=0
CONFIG_ONLY=0
LL=""
TV=""

while [ $# -gt 0 ]
do
  case "$1" in
    "-h") show_help; exit 0 ;;
    "-s") SKIP_PACKAGES=1 ;;
    "-w") GITHOOK_ONLY=1 ;;
    "-c") CONFIG_ONLY=1 ;;
    "-l") LL=$2; shift ;;
    "-t") TV=$2; shift ;;
    *) DIR=$1 ;;
  esac
  shift
done

IS_DIR=$(check_dir "${DIR}")
if [ "${IS_DIR}" == 1 ]; then
  printf "\e[1;41;31mERROR: Directory not found. %s\e[0m\n" "$DIR"
  show_help
  exit 1
fi

DIR_PATH=$(abspath "${DIR}")
IN_VENV=$(in_venv)

if [ "${CONFIG_ONLY}" == 1 ]; then
  INSTALL_ARGS=("--config-only")
  [ -n "${LL}" ] && INSTALL_ARGS+=("--line-length=${LL}")
  [ -n "${TV}" ] && INSTALL_ARGS+=("--target-version=${TV}")
  python3 ./install.py "${INSTALL_ARGS[@]}" "${DIR_PATH}"
  exit "$?"
fi

GIT_DIR="${DIR_PATH}.git"
if [ -f "${GIT_DIR}" ]; then
  GIT_FILE="${GIT_DIR}"
  while read -r line; do
    GIT_DIR=${line#"gitdir: "}
  done < "${GIT_FILE}"
fi
HAS_GIT_DIR=$(check_dir "${GIT_DIR}/")

if [ "${HAS_GIT_DIR}" == 1 ]; then
  printf "\e[1;41;31mERROR: %s not found.\e[0;37m\n" "${GIT_DIR}"
  printf "Have you run '\e[0;33mgit init\e[0;37m' in the \e[0;34m%s\e[0;37m directory?\e[0;m\n" "${DIR_PATH}"
  exit 1
fi
printf "\e[0;37mGit directory found at %s\e[0m\n" "${GIT_DIR}"

pass=0
printf "Checking if \e[1mgit\e[0m is installed..."
if [ "$(program_is_installed 'git')" == 1 ]; then
  printf "\e[1;91m Fail \e[0m\n"
  pass=1
else
  printf "\e[1;92m Pass \e[0m\n"
fi

if [ "${IN_VENV}" == 0 ]; then
  printf "\e[1mVirtual environment found\e[0m at %s\n" "${VIRTUAL_ENV}"
fi

if [ "${GITHOOK_ONLY}" == 1 ]; then
  INSTALL_ARGS=("--githook-only")
  [ "${IN_VENV}" == 0 ] && INSTALL_ARGS+=("--venv" "${VIRTUAL_ENV}")
  python3 ./install.py "${INSTALL_ARGS[@]}" "${DIR_PATH}"
  exit "$?"
fi

printf "Checking if \e[1mPython 3\e[0m is installed..."
if [ "$(program_is_installed 'python3')" == 1 ]; then
  printf "\e[1;91m Fail \e[0m\n"
  pass=1
else
  printf "\e[1;92m Pass \e[0m\n"
  printf "Checking if \e[1mPython version\e[0m is minimum \e[1m3.11\e[0m..."
  if [ "$(check_python_version)" == 1 ]; then
    printf "\e[1;91m Fail \e[0m\n"
    pass=1
  else
    printf "\e[1;92m Pass \e[0m\n"
  fi
fi

if [ "${pass}" == 1 ]; then
  printf "\e[1;41;31mRequirements missing\e[0m\n"
  printf "Please install the requirements and try again\n"
  exit 1
fi

pass=0
if [ "${IN_VENV}" == 1 ]; then
  LOCAL_PY_DIR=$(python3 -m site --user-site)
  printf "Check for local Python package path in \$PATH..."
  case :$PATH: in
    *:"${LOCAL_PY_DIR}":*)
      printf "\e[1;92m Pass \e[0m\n"
      ;;
    *)
      printf "\e[1;91m Fail \e[0m\n"
      [ "${SKIP_PACKAGES}" == 0 ] && pass=1
      ;;
  esac
fi

printf "Checking if \e[1mPip3\e[0m is installed..."
python3 -c "import pip" &> /dev/null
PIP_INSTALLED="$?"
if [ "${PIP_INSTALLED}" == 0 ]; then
  printf "\e[1;92m Pass \e[0m\n"
  if [ "${SKIP_PACKAGES}" == 0 ]; then
    printf "Updating pip and tools\n"
    python3 -m pip install --upgrade pip setuptools wheel
  fi
else
  printf "\e[1;91m Fail \e[0m\n"
  if [ "${SKIP_PACKAGES}" == 0 ]; then
    if [ "$(program_is_installed 'wget')" == 0 ]; then
      printf "Attempting to download and install pip...\n"
      wget https://bootstrap.pypa.io/get-pip.py -P /tmp/get-pip.py
      python3 /tmp/get-pip.py --prefix=/usr/local/
    else
      pass=1
    fi
  fi
fi

printf "Checking if \e[1mruff\e[0m is installed..."
if [ "$(program_is_installed 'ruff')" == 1 ]; then
  printf "\e[1;91m Fail \e[0m\n"
  if [ "${SKIP_PACKAGES}" == 0 ]; then
    printf "\e[36mAttempting install of ruff\e[0m..."
    INSTALLED="$(install_python_package ruff)"
    [ "${INSTALLED}" != 0 ] && pass=1
  fi
else
  printf "\e[1;92m Pass \e[0m\n"
fi

printf "\n"
if [ "${pass}" == 1 ]; then
  printf "\e[1;41;31mRequirements missing\e[0m\n"
  printf "Please install the requirements and try again\n"
  exit 1
fi

INSTALL_ARGS=()
[ -n "${LL}" ] && INSTALL_ARGS+=("--line-length=${LL}")
[ -n "${TV}" ] && INSTALL_ARGS+=("--target-version=${TV}")
[ "${IN_VENV}" == 0 ] && INSTALL_ARGS+=("--venv" "${VIRTUAL_ENV}")
python3 ./install.py "${INSTALL_ARGS[@]}" "${DIR_PATH}"

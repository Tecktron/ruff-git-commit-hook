# Git Pre-Commit Python Linters

## What is does:
This package will install a pre-commit git hook that automatically lints and checks python code using black, isort and flake8

## Requirments:
1. git
2. python3
3. a bash compatible shell

## How to install:
1. Run the `install.sh` file

## How it works:
It installs the python packages globally, check for the settings file and updates them as needed and then adds a precommit webhook into your .git directory that run them to update and check your code. This happens before you commit.

## How to config:
A based set of configs is store in the ... files, you are free to change and adjust these to suit your project's needs.

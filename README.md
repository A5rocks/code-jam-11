# Quizzical Quasars

Table of contents:

 - [installing dependencies](#installing-dependencies)
 - [running the program](#running-this)
 - [development tool rundown](#development-tool-rundown)

## installing dependencies

### Creating the environment

Create a virtual environment in the folder `.venv`.

```shell
python -m venv .venv
```

### entering the environment

It will change based on your operating system and shell.

```shell
# Linux, Bash
$ source .venv/bin/activate
# Linux, Fish
$ source .venv/bin/activate.fish
# Linux, Csh
$ source .venv/bin/activate.csh
# Linux, PowerShell Core
$ .venv/bin/Activate.ps1
# Windows, cmd.exe
> .venv\Scripts\activate.bat
# Windows, PowerShell
> .venv\Scripts\Activate.ps1
```

### actually installing the dependencies

Once the environment is created and activated, use this command to install the development dependencies.

```shell
pip install -r requirements-dev.txt
```

### exiting the environment

Interestingly enough, it is the same for every platform.

```shell
deactivate
```

## running this

### with Docker

`docker run -it ghcr.io/a5rocks/code-jam-11:stable -e TOKEN=...`

### locally

In a virtual environment, run `python -m pip install -r requirements.txt`. Then, move `.env.example` to `.env` and fill it out. Finally, run `python app.py`.

## development tool rundown

### ruff

Our first tool is Ruff. It will check your codebase and warn you about any non-conforming lines.
It is run with the command `ruff check` in the project root.

Ruff also comes with a formatter, which can be run with the command `ruff format`.

### pre-commit: run linting before committing

The second tool doesn't check your code, but rather makes sure that you actually *do* check it.

It is *installed* by running `pre-commit install` and can be run manually by calling only `pre-commit`, or `pre-commit run -a` to run it on everything.

#### list of what pre-commit runs

- `check-toml`: Lints and corrects your TOML files.
- `check-yaml`: Lints and corrects your YAML files.
- `end-of-file-fixer`: Makes sure you always have an empty line at the end of your file.
- `trailing-whitespace`: Removes whitespaces at the end of each line.
- `ruff`: Runs the Ruff linter.
- `ruff-format`: Runs the Ruff formatter.
- `pip-compile requirements.in`: locks `requirements.in` to make `requirements.txt`
- `pip-compile requirements-dev.in`: locks `requirements-dev.in` to make `requirements-dev.txt`

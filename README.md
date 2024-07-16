# Quizzical Quasars

## development tool rundown

(TODO: this should be written to be less verbose)

### Ruff: general style rules

Our first tool is Ruff. It will check your codebase and warn you about any non-conforming lines.
It is run with the command `ruff check` in the project root.

Here is a sample output:

```shell
$ ruff check
app.py:1:5: N802 Function name `helloWorld` should be lowercase
app.py:1:5: ANN201 Missing return type annotation for public function `helloWorld`
app.py:2:5: D400 First line should end with a period
app.py:2:5: D403 First word of the first line should be capitalized: `docstring` -> `Docstring`
app.py:3:15: W292 No newline at end of file
Found 5 errors.
```

Each line corresponds to an error. The first part is the file path, then the line number, and the column index.
Then comes the error code, a unique identifier of the error, and then a human-readable message.

If, for any reason, you do not wish to comply with this specific error on a specific line, you can add `# noqa: CODE` at the end of the line.
For example:

```python
def helloWorld():  # noqa: N802
    ...

```

This will ignore the function naming issue and pass linting.

> [!WARNING]
> We do not recommend ignoring errors unless you have a good reason to do so.

### Ruff: formatting

Ruff also comes with a formatter, which can be run with the command `ruff format`.
It follows the same code style enforced by [Black](https://black.readthedocs.io/en/stable/index.html), so there's no need to pick between them.

### Pre-commit: run linting before committing

The second tool doesn't check your code, but rather makes sure that you actually *do* check it.

It makes use of a feature called [Git hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) which allow you to run a piece of code before running `git commit`.
The good thing about it is that it will cancel your commit if the lint doesn't pass. You won't have to wait for GitHub Actions to report issues and have a second fix commit.

It is *installed* by running `pre-commit install` and can be run manually by calling only `pre-commit`.

[Lint before you push!](https://soundcloud.com/lemonsaurusrex/lint-before-you-push)

#### List of hooks

- `check-toml`: Lints and corrects your TOML files.
- `check-yaml`: Lints and corrects your YAML files.
- `end-of-file-fixer`: Makes sure you always have an empty line at the end of your file.
- `trailing-whitespace`: Removes whitespaces at the end of each line.
- `ruff`: Runs the Ruff linter.
- `ruff-format`: Runs the Ruff formatter.

### Installing dependencies

#### Creating the environment

Create a virtual environment in the folder `.venv`.

```shell
python -m venv .venv
```

#### Entering the environment

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

#### Installing the dependencies

Once the environment is created and activated, use this command to install the development dependencies.

```shell
pip install -r requirements-dev.txt
```

#### Exiting the environment

Interestingly enough, it is the same for every platform.

```shell
deactivate
```

Once the environment is activated, all the commands listed previously should work.

> [!IMPORTANT]
> We highly recommend that you run `pre-commit install` as soon as possible.

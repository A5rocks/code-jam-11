# Quizzical Quasars

Table of contents:

 - [getting started](#getting-started)
 - [sending messages](#sending-messages)
 - [upgrading](#upgrading)
 - [installing dependencies](#installing-dependencies)
 - [running the program](#running-this)
 - [development tool rundown](#development-tool-rundown)

In our modern world, it can feel like everything is happening all at once. Encountered with this, people seek out quieter waters, turning away from larger servers. To help those larger servers, our submission addresses this information overload by limiting how much people can send at once. Essentially, we only let one character through at a time that is dependent on who is sending the message.

At the behest of many a server owner, we also provide incentives for activity. Every time someone's character gets sent, they get a coin. These coins can be used to increase how many characters they can send per second, or for vanity upgrades (priority). Any incremental game is purely coincidental.

## getting started

To first get started with the game, run the slash command `/config enable`. This will enable the game in the current channel. You can disable the game later with `/config disable` or disable it for all channels in your server with `/config reset`.

https://github.com/user-attachments/assets/c8494e9c-4de0-4b43-a91f-7d79688d38ea

## sending messages

Now that the game is enabled, you will note that you cannot send messages normally. This is intentional; instead, you must run `/send` with the message contents. We don't allow more than 5 minutes of messages to be buffered.

https://github.com/user-attachments/assets/7200b316-06dd-4141-9da5-0861b8e3647f

## upgrading

Finally, once you have some money, you can upgrade how many characters per second you can send. For this, you must run `/upgrade`. The resulting menu only allows you to click buttons you can afford as of when it was sent. To update it, simply press "Refresh".

https://github.com/user-attachments/assets/b79c5852-e9eb-43f5-9464-9d4a2afde1c0

## installing dependencies

### creating the environment

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

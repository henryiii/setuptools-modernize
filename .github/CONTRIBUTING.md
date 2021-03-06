See the [Scikit-HEP Developer introduction][skhep-dev-intro] for a
detailed description of best practices for developing Scikit-HEP packages.

[skhep-dev-intro]: https://scikit-hep.org/developer/intro

# Setting up a development environment

You can set up a development environment by running:

```bash
poetry install
```

# Post setup

You should prepare pre-commit, which will help you by checking that commits
pass required checks:

```bash
pip install pre-commit # or brew install pre-commit on macOS
pre-commit install # Will install a pre-commit hook into the git repo
```

You can also/alternatively run `pre-commit run` (changes only) or `pre-commit
run --all-files` to check even without installing the hook.

# Testing

Use PyTest to run the unit checks:

```bash
pytest
```

# Building docs

You can build the docs using:


Remember to install the docs extra:

```bash
poetry install --extras docs
```

Then run:

```bash
poetry run sphinx-build -M html docs docs/_build
```

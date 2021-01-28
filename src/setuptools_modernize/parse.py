#!/usr/bin/env python3
from __future__ import annotations

import ast
import configparser
import dataclasses
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Optional

import black
import click
from rich import print
from rich.align import Align
from rich.panel import Panel
from rich.syntax import Syntax

Ostr = Optional[str]
Odict = Optional[str]
Olist_comma = Optional[str]
Olist_simi = Optional[str]
Ofile_str = Optional[str]
Obool = Optional[str]
Osection = Optional[str]


class Config:
    def as_dict(self) -> Dict[str, Any]:
        d = dataclasses.asdict(self)
        d = {k: v for k, v in d.items() if v is not None}
        return d

    def as_cfg(self) -> configparser.ConfigParser:
        cfg = configparser.ConfigParser()
        cfg[self.__class__.__name__.lower()] = self.as_dict()

        return cfg

    def as_str(self) -> str:
        strio = StringIO()
        cfg = self.as_cfg()
        cfg.write(strio)
        return strio.getvalue()

    def __rich__(self) -> Syntax:
        return Syntax(self.as_str(), "cfg", theme="ansi_light")


@dataclasses.dataclass
class Metadata(Config):
    name: Ostr = None
    version: Ostr = None
    url: Ostr = None
    download_url: Ostr = None
    project_urls: Odict = None
    author: Ostr = None
    author_email: Ostr = None
    maintainer: Ostr = None
    maintainer_email: Ostr = None
    classifiers: Olist_comma = None
    license: Ostr = None
    license_file: Ostr = None
    license_files: Olist_comma = None
    description: Ofile_str = None
    long_description: Ofile_str = None
    long_description_content_type: Ostr = None
    keywords: Olist_comma = None
    platforms: Olist_comma = None
    provides: Olist_comma = None
    requires: Olist_comma = None
    obsoletes: Olist_comma = None


@dataclasses.dataclass
class Options(Config):
    zip_safe: Obool = None
    setup_requires: Olist_simi = None
    install_requires: Olist_simi = None
    extras_require: Osection = None
    python_requires: Ostr = None
    entry_points: Osection = None
    use_2to3: Olist_comma = None
    use_2to3_fixers: Olist_comma = None
    use_2to3_exclude_fixers: Olist_comma = None
    convert_2to3_doctests: Olist_comma = None
    scripts: Olist_comma = None
    eager_resources: Olist_comma = None
    dependency_links: Olist_comma = None
    tests_require: Olist_simi = None
    include_package_data: Obool = None
    packages: Olist_comma = None
    package_dir: Odict = None
    package_data: Osection = None
    exclude_package_data: Osection = None
    namespace_packages: Olist_comma = None
    py_modules: Olist_comma = None
    data_files: Odict = None


class Analyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.metadata = Metadata()
        self.options = Options()
        self.constants: Dict[str, str] = {}
        self.setup_function: Optional[ast.Call] = None

    def store(self, node: ast.keyword) -> bool:
        try:
            value = self.get_value(node.value)
        except (LookupError, AttributeError):
            return False

        if node.arg and hasattr(self.options, node.arg):
            setattr(self.options, node.arg, value)
            return True
        elif node.arg and hasattr(self.metadata, node.arg):
            setattr(self.metadata, node.arg, value)
            return True
        else:
            return False

    def get_value(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            # Raises KeyError if undefined
            return self.constants[node.id]
        elif isinstance(node, ast.List):
            # Raises Attribute error if not valid
            return "\n" + "\n".join([self.get_value(v) for v in node.elts])
        elif isinstance(node, ast.Dict):
            # Raises Attribute error if not valid
            d = {k.value or "*": v.value for k, v in zip(node.keys, node.values)}  # type: ignore
            return "\n" + "\n".join(f"{k} = {v}" for k, v in d.items())
        else:
            raise LookupError("Invalid node to get value from")

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                self.constants[target.id] = node.value.value

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)
        if (
            getattr(node.func, "id", "") == "setup"
            or getattr(node.func, "attr", "") == "setup"
        ):
            node.keywords = [n for n in node.keywords if not self.store(n)]
            self.setup_function = node


@click.command()
@click.argument(
    "filename", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
def main(filename: str) -> None:
    with open(Path(filename) / "setup.py") as f:
        tree = ast.parse(f.read())

    analyzer = Analyzer()
    analyzer.visit(tree)
    if analyzer.setup_function is None:
        raise RuntimeError("Invalid, no setup function found")

    print(Panel(Align("New [bold]setup.cfg", align="center")))
    print()
    print(analyzer.metadata)
    print()
    print(analyzer.options)
    print()
    print(Panel(Align("New setup() in [bold]setup.py", "center")))
    print()
    new_setup_py = black.format_str(
        ast.unparse(analyzer.setup_function), mode=black.Mode()
    )
    print(Syntax(new_setup_py, "python", theme="ansi_light"))


if __name__ == "__main__":
    main()

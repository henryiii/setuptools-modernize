#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, Optional

import click


class Analyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.requires_python: Optional[str] = None
        self.constants: Dict[str, str] = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if (
                isinstance(target, ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                self.constants[target.id] = node.value.value

    def visit_Call(self, node: ast.Call) -> None:
        if getattr(node.func, "id", "") == "setup":
            for kw in node.keywords:
                self.generic_visit(kw)
                if kw.arg == "python_requires":
                    if isinstance(kw.value, ast.Constant):
                        self.requires_python = kw.value.value
                    elif isinstance(kw.value, ast.Name):
                        self.requires_python = self.constants.get(kw.value.id)


@click.command()
@click.argument(
    "filename", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
def main(filename: str) -> None:
    with open(Path(filename) / "setup.py") as f:
        tree = ast.parse(f.read())
    analyzer = Analyzer()
    analyzer.visit(tree)
    print(analyzer.requires_python)


if __name__ == "__main__":
    main()

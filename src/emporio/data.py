"""Leitura isolada dos dados de negócio, sem alterações de estoque ou pedidos."""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
from pathlib import Path
from typing import Protocol

TABLES = ("categories", "customers", "order_items", "orders", "products", "promotions")


def project_root() -> Path:
    """Raiz do checkout ou pasta do executável empacotado."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def configured_path(name: str, default: str) -> Path:
    """Interpreta caminhos relativos ao aplicativo, não ao diretório de execução."""
    path = Path(os.getenv(name, default)).expanduser()
    return path if path.is_absolute() else project_root() / path


class DataSource(Protocol):
    def rows(self, table: str) -> list[dict[str, str]]: ...


class CSVSource:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def rows(self, table: str) -> list[dict[str, str]]:
        if table not in TABLES:
            raise ValueError("Tabela inválida")
        matches = sorted(self.directory.glob(f"* - {table}.csv"))
        matches += [self.directory / f"{table}.csv"]
        path = next((f for f in matches if f.is_file()), None)
        if path is None:
            raise FileNotFoundError(f"CSV não encontrado para {table} em {self.directory}. Verifique DATA_DIR.")
        with path.open(encoding="utf-8-sig", newline="") as fp:
            return list(csv.DictReader(fp))


class SQLiteSource:
    """Adaptador opcional para tabelas de mesmo nome e colunas dos CSVs."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def rows(self, table: str) -> list[dict[str, str]]:
        if table not in TABLES:
            raise ValueError("Tabela inválida")
        if not self.path.is_file():
            raise FileNotFoundError(f"Banco não encontrado: {self.path}")
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            return [{k: "" if v is None else str(v) for k, v in dict(row).items()}
                    for row in conn.execute(f'SELECT * FROM "{table}"')]


def source_from_env() -> DataSource:
    if os.getenv("DATA_BACKEND", "csv").lower() == "sqlite":
        return SQLiteSource(configured_path("SQLITE_PATH", "data/loja.sqlite3"))
    return CSVSource(configured_path("DATA_DIR", "data"))

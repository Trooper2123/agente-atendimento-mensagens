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
    """Mantém em memória apenas o catálogo, não dados pessoais de clientes."""
    CATALOG_TABLES = frozenset({"categories", "products", "promotions"})

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self._catalog: dict[str, list[dict[str, str]]] = {}

    def _read_file(self, table: str) -> list[dict[str, str]]:
        matches = sorted(self.directory.glob(f"* - {table}.csv"))
        matches += [self.directory / f"{table}.csv"]
        path = next((f for f in matches if f.is_file()), None)
        if path is None:
            raise FileNotFoundError(f"CSV não encontrado para {table} em {self.directory}. Verifique DATA_DIR.")
        with path.open(encoding="utf-8-sig", newline="") as fp:
            return list(csv.DictReader(fp))

    def refresh_catalog(self) -> None:
        """Recarrega catálogo após atualização dos CSVs; mantém a versão antiga se falhar."""
        new_catalog = {table: self._read_file(table) for table in sorted(self.CATALOG_TABLES)}
        self._catalog = new_catalog

    def rows(self, table: str) -> list[dict[str, str]]:
        if table not in TABLES:
            raise ValueError("Tabela inválida")
        if table not in self.CATALOG_TABLES:
            return self._read_file(table)
        if not self._catalog:
            self.refresh_catalog()
        return [dict(row) for row in self._catalog[table]]


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

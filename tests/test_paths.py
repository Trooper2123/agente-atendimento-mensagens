"""Caminhos dos dados não dependem da pasta onde o programa é iniciado."""
from emporio.data import configured_path, project_root, source_from_env


def test_defaults_independent_of_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.delenv("DATA_BACKEND", raising=False)
    monkeypatch.delenv("POLICY_PDF", raising=False)
    assert source_from_env().directory == project_root() / "data"
    assert configured_path("POLICY_PDF", "data/politicas_da_loja.pdf") == (
        project_root() / "data/politicas_da_loja.pdf"
    )


def test_absolute_and_relative_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert source_from_env().directory == tmp_path
    monkeypatch.setenv("DATA_DIR", "arquivos")
    assert source_from_env().directory == project_root() / "arquivos"


def test_frozen_executable_uses_its_directory(monkeypatch, tmp_path):
    from emporio import data
    monkeypatch.setattr(data.sys, "frozen", True, raising=False)
    monkeypatch.setattr(data.sys, "executable", str(tmp_path / "atendimento.exe"))
    assert data.project_root() == tmp_path
    assert data.configured_path("DATA_DIR", "data") == tmp_path / "data"

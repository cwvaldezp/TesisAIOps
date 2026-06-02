"""
Pruebas de ingesta (src/ingest.py) — Fase 3.5. Cubre lectura .gz/plano y
descubrimiento recursivo multi-patrón. No dependen del corpus real: crean
archivos temporales (incluido un .gz real con gzip).
"""

import gzip

from src.ingest import discover_log_files, read_log_lines

LINES = [
    "May 18 09:59:25 t-lb haproxy[1]: 10.0.0.1:5000 [18/May/2026:09:59:25.909] "
    'fe be/s 0/0/1/2/3 200 100 - - ---- 1/1/0/0/0 0/0 {h} "GET / HTTP/1.1"',
    "segunda linea",
]


def test_read_log_lines_plano(tmp_path):
    p = tmp_path / "a.log"
    p.write_text("\n".join(LINES), encoding="utf-8")
    assert read_log_lines(p) == LINES


def test_read_log_lines_gz(tmp_path):
    """Un .log-YYYYMMDD.gz debe descomprimirse al vuelo y leerse igual."""
    p = tmp_path / "a.log-20260518.gz"
    with gzip.open(p, "wt", encoding="utf-8") as fh:
        fh.write("\n".join(LINES))
    assert read_log_lines(p) == LINES


def test_read_log_lines_bytes_invalidos_no_aborta(tmp_path):
    """Bytes no UTF-8 se reemplazan (errors='replace'), no se lanza excepción."""
    p = tmp_path / "bad.log"
    p.write_bytes(b"linea valida\nlinea \xff\xfe rota\n")
    lines = read_log_lines(p)
    assert lines[0] == "linea valida"
    assert len(lines) == 2


def test_discover_no_recursivo_solo_primer_nivel(tmp_path):
    (tmp_path / "x.log").write_text("a", encoding="utf-8")
    sub = tmp_path / "app1"
    sub.mkdir()
    (sub / "y.log").write_text("b", encoding="utf-8")

    found = discover_log_files(tmp_path, ["*.log"], recursive=False)
    names = [p.name for p in found]
    assert names == ["x.log"]  # no entra en la subcarpeta


def test_discover_recursivo_multi_patron_sin_duplicados(tmp_path):
    (tmp_path / "x.log").write_text("a", encoding="utf-8")
    sub = tmp_path / "app1"
    sub.mkdir()
    (sub / "y.log").write_text("b", encoding="utf-8")
    (sub / "y.log-20260101.gz").write_bytes(b"\x1f\x8b")  # nombre .gz

    found = discover_log_files(tmp_path, ["*.log", "*.gz"], recursive=True)
    names = sorted(p.name for p in found)
    assert names == ["x.log", "y.log", "y.log-20260101.gz"]
    # sin duplicados aunque un patrón pudiera solaparse
    assert len(found) == len(set(found))

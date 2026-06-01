"""
parse_logs.py — Orquestador CLI del subsistema de parsing (Fase 1).

QUÉ HACE
    Pega todas las piezas del subflujo de parsing (docs/03_flujos.md §2.1):
    1) ingiere los archivos de log según la config,
    2) detecta la fuente (HAProxy/IIS) o la fuerza,
    3) parsea cada línea al esquema normalizado,
    4) aplica la política `on_parse_error`,
    5) escribe los eventos normalizados en data/processed/ (JSON o JSONL),
    6) imprime un resumen (archivos, líneas, parseadas, omitidas).

CUÁNDO SE INVOCA
    Manualmente, como paso offline de solo lectura:
        python -m src.parse_logs
        python -m src.parse_logs --config config/config.yaml
        python -m src.parse_logs --source iis --format json

ENTRADAS
    Configuración (config/config.yaml) y, opcionalmente, overrides por CLI.
    Archivos de log en `logs_path`.

SALIDAS
    Un archivo por log de entrada en `processed_path`
    (p. ej. data/processed/haproxy_sample.events.jsonl) + resumen por consola.
    Devuelve un código de salida 0 si todo fue bien.

QUÉ PUEDE FALLAR
    - logs_path inexistente o sin archivos que casen file_pattern -> error claro.
    - on_parse_error='fail' + línea no parseable -> aborta con detalle de la línea.
    - Problemas de escritura en processed_path -> excepción de E/S.

EFECTO DE PARÁMETROS
    Todos los parámetros provienen de la config (ver docs/04). Los flags de CLI
    permiten override puntual sin editar el YAML (útil para demos/experimentos).
    NUNCA actúa sobre infraestructura real (ADR-005): solo lee archivos y escribe
    en data/processed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

from src.config import Config, load_config
from src.parsers import STATUS_ERROR, STATUS_OK
from src.parsers.haproxy import HAProxyParser
from src.parsers.iis import IISParser
from src.schema import make_unparsed_event


class ParseError(Exception):
    """Se lanza cuando on_parse_error='fail' y una línea no es parseable."""


def detect_source(filename: str, sample_lines: Iterable[str]) -> str:
    """Detecta la fuente del log por nombre de archivo y, si no, por contenido.

    Reglas (en orden):
        1. Nombre contiene 'haproxy' -> 'haproxy'.
        2. Nombre contiene 'iis' o empieza por 'u_ex' -> 'iis'.
        3. Alguna de las primeras líneas es una directiva W3C ('#Fields'/'#Software') -> 'iis'.
        4. Por defecto -> 'haproxy'.
    """
    name = filename.lower()
    if "haproxy" in name:
        return "haproxy"
    if "iis" in name or name.startswith("u_ex"):
        return "iis"
    for line in sample_lines:
        low = line.lower()
        if low.startswith("#fields:") or low.startswith("#software"):
            return "iis"
    return "haproxy"


def build_parser(source: str, cfg: Config):
    """Instancia el parser adecuado para la fuente."""
    if source == "haproxy":
        return HAProxyParser(timezone=cfg.timezone)
    if source == "iis":
        return IISParser(
            timezone=cfg.timezone,
            default_fields=cfg.iis_fields,
            fields_from_header=cfg.iis_fields_from_header,
        )
    raise ValueError(f"Fuente no soportada: {source!r}")


def parse_file(path: Path, cfg: Config, forced_source: str | None) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Parsea un único archivo de log y devuelve (eventos, estadísticas)."""
    text = path.read_text(encoding=cfg.encoding)
    lines = text.splitlines()

    # Determina la fuente (forzada por CLI/config o autodetectada).
    if forced_source and forced_source != "auto":
        source = forced_source
    elif cfg.source_type != "auto":
        source = cfg.source_type
    else:
        source = detect_source(path.name, lines[:10])

    parser = build_parser(source, cfg)

    events: list[dict[str, Any]] = []
    stats = {"total": 0, "ok": 0, "skipped_errors": 0, "kept_errors": 0}

    for i, raw in enumerate(lines, start=1):
        stats["total"] += 1
        status, event = parser.parse_line(raw, line_number=i, source_file=path.name)

        if status == STATUS_OK:
            events.append(event)
            stats["ok"] += 1
        elif status == STATUS_ERROR:
            # Aplica la política configurada ante líneas no parseables.
            if cfg.on_parse_error == "fail":
                raise ParseError(
                    f"Línea no parseable en {path.name}:{i} -> {raw!r}"
                )
            if cfg.on_parse_error == "keep":
                events.append(
                    make_unparsed_event(
                        source=source,
                        source_file=path.name,
                        line_number=i,
                        raw=raw.rstrip("\n"),
                    )
                )
                stats["kept_errors"] += 1
            else:  # 'skip'
                stats["skipped_errors"] += 1
        # status == 'skip' (vacías/directivas): no se cuentan como error.

    stats["source"] = source  # type: ignore[assignment]
    return events, stats


def write_output(events: list[dict[str, Any]], out_path: Path, fmt: str) -> None:
    """Escribe los eventos en disco como JSON (array) o JSONL (un obj/línea)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        if fmt == "jsonl":
            for ev in events:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        else:  # 'json'
            json.dump(events, fh, ensure_ascii=False, indent=2)


def run(cfg: Config, forced_source: str | None = None, output_format: str | None = None) -> int:
    """Ejecuta el pipeline de parsing completo. Devuelve un código de salida."""
    logs_dir = Path(cfg.logs_path)
    if not logs_dir.exists():
        print(f"[ERROR] No existe la carpeta de logs: {logs_dir}", file=sys.stderr)
        return 1

    files = sorted(logs_dir.glob(cfg.file_pattern))
    if not files:
        print(
            f"[ERROR] No se encontraron archivos que casen '{cfg.file_pattern}' "
            f"en {logs_dir}",
            file=sys.stderr,
        )
        return 1

    fmt = output_format or cfg.parser_output_format
    ext = "jsonl" if fmt == "jsonl" else "json"
    processed_dir = Path(cfg.processed_path)

    grand_total = {"files": 0, "events": 0, "ok": 0, "skipped_errors": 0, "kept_errors": 0}

    print(f"== TesisAIOps · Parser de logs (Fase 1) ==")
    print(f"Carpeta de logs : {logs_dir}")
    print(f"Patrón          : {cfg.file_pattern}")
    print(f"Salida          : {processed_dir} ({fmt})")
    print("-" * 60)

    for path in files:
        events, stats = parse_file(path, cfg, forced_source)
        out_path = processed_dir / f"{path.stem}.events.{ext}"
        write_output(events, out_path, fmt)

        grand_total["files"] += 1
        grand_total["events"] += len(events)
        grand_total["ok"] += stats["ok"]
        grand_total["skipped_errors"] += stats["skipped_errors"]
        grand_total["kept_errors"] += stats["kept_errors"]

        print(
            f"[{stats['source']:7}] {path.name:22} "
            f"líneas={stats['total']:3}  ok={stats['ok']:3}  "
            f"errores_omitidos={stats['skipped_errors']:3}  "
            f"errores_conservados={stats['kept_errors']:3}  -> {out_path.name}"
        )

    print("-" * 60)
    print(
        f"TOTAL: {grand_total['files']} archivo(s), "
        f"{grand_total['events']} evento(s) escritos "
        f"(ok={grand_total['ok']}, "
        f"errores_omitidos={grand_total['skipped_errors']}, "
        f"errores_conservados={grand_total['kept_errors']})."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI. Parsea argumentos y ejecuta el pipeline."""
    ap = argparse.ArgumentParser(
        description="Parser de logs HAProxy/IIS -> eventos normalizados JSON/JSONL."
    )
    ap.add_argument(
        "--config", default="config/config.yaml",
        help="Ruta al archivo de configuración YAML (default: config/config.yaml).",
    )
    ap.add_argument(
        "--source", choices=["auto", "haproxy", "iis"], default=None,
        help="Forzar la fuente para todos los archivos (override de la config).",
    )
    ap.add_argument(
        "--format", dest="fmt", choices=["json", "jsonl"], default=None,
        help="Forzar el formato de salida (override de la config).",
    )
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] Configuración: {exc}", file=sys.stderr)
        return 2

    try:
        return run(cfg, forced_source=args.source, output_format=args.fmt)
    except ParseError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

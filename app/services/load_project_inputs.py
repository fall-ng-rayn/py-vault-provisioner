from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional

from app.models.InputFileParseResult import InputFileParseResult
from app.models.InputScanResult import InputScanResult

SUFFIX = "-vault-prefixes.txt"
FILENAME_PATTERN = re.compile(r".*-vault-prefixes\.txt\Z")
INPUT_DIR_NAME = "input"

# 1-63 chars, start alnum, then alnum / - / _
PREFIX_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:\s_-]{0,62}\Z")

# Reasonable guardrails
MAX_FILE_SIZE_BYTES = 512 * 1024  # 512 KB
MAX_PROJECTS_PER_FILE = 5000


def _safe_read_lines(path: Path) -> Iterable[str]:
    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large ({size} bytes): {path}")
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            yield raw


def _extract_batch_name(path: Path) -> str:
    name = path.name
    if name.endswith(SUFFIX):
        return name[: -len(SUFFIX)]
    return Path(name).stem


def _validate_project_prefix(project: str) -> Optional[str]:
    """Ensures that the project prefix is not malformed and is suitable for a vault name. Return error message if invalid, else None"""
    if not PREFIX_PATTERN.match(project):
        return "Invalid project prefix (allowed: letters, digits, '-', '_', ':' and spaces; 1-63 chars; must start alphanumeric)"


def find_input_files(base_dir: Optional[Path] = None) -> List[Path]:
    """Finds all files in the input directory that have the correct suffix. Makes no claims about quality of the project prefix."""
    root = (base_dir or Path.cwd()).resolve()
    input_dir = root / INPUT_DIR_NAME

    # determine if input directory is valid
    if not input_dir.exists() or not input_dir.is_dir():
        return []

    # perform regex match on all filenames within input directory
    return [
        p
        for p in sorted(input_dir.iterdir())
        if p.is_file() and FILENAME_PATTERN.match(p.name)
    ]


def parse_input_file(path: Path) -> InputFileParseResult:
    warnings: List[str] = []
    errors: List[str] = []
    seen: set[str] = set()
    projects: List[str] = []

    # 1. collect the string segment that preceeds the prefix
    batch_name = _extract_batch_name(path)

    # 2. Parse the file, returning an empty parse result on failure
    try:
        lines = list(_safe_read_lines(path))
    except Exception as e:
        return InputFileParseResult(
            batch_name=batch_name,
            path=path,
            projects=[],
            warnings=[],
            errors=[f"Failed to read: {e}"],
        )

    # 3. parse lines...
    for idx, raw in enumerate(lines, start=1):
        text = raw.strip()

        # ignore comments
        if not text or text.startswith("#"):
            continue

        # determines if project_prefix is a valid 1password vault name string
        err = _validate_project_prefix(text)
        if err:
            errors.append(f"Line {idx}: {err} -> {text!r}")
            continue

        # skip duplicates
        if text in seen:
            warnings.append(f"Line {idx}: duplicate entry ignored -> {text!r}")
            continue

        # mark this project-prefix as done
        projects.append(text)
        seen.add(text)

        # exit on program input violation, don't accept partial jobs
        if len(projects) > MAX_PROJECTS_PER_FILE:
            errors.append(
                f"Too many prefixes (> {MAX_PROJECTS_PER_FILE}; aborting parse.)"
            )
            projects = []
            break
    # end-for

    # 4. provide useful warning if there are no projects staged for vault creation
    if not projects and not errors:
        warnings.append(
            "File contained no usable prefixes (only comments/blank lines)."
        )

    # Parse successful!
    return InputFileParseResult(
        batch_name=batch_name,
        path=path,
        projects=projects,
        warnings=warnings,
        errors=errors,
    )


def load_all_inputs(base_dir: Optional[Path] = None) -> InputScanResult:
    """Main driver of input scanning. Attempts to find all matching project files in `/input/`. Returns a scan result"""
    files: List[InputFileParseResult] = []
    fatal_errors: List[str] = []

    # 1. obtain all input files present in the project base directory
    matches = find_input_files(base_dir=base_dir)

    # 2. Return an empty scan result if there were no relevant files found
    if not matches:
        fatal_errors.append(
            f"No files found matching '*-vault-prefixes.txt' in ./{INPUT_DIR_NAME}/"
        )
        return InputScanResult(files=files, fatal_errors=fatal_errors)

    # 3. Collect matching input files, perform basic validation and collect metadata
    for path in matches:
        files.append(parse_input_file(path))

    return InputScanResult(files=files, fatal_errors=fatal_errors)


def summarize_scan(scan: InputScanResult) -> str:
    lines: List[str] = []
    if scan.fatal_errors:
        lines.append("FATAL:")
        lines.extend(f"  - {e}" for e in scan.fatal_errors)

    for f in scan.files:
        lines.append(
            f"[{f.batch_name}] {len(f.projects)} project-prefix(es) from {f.path.name}"
        )
        if f.warnings:
            lines.append("  Warnings:")
            lines.extend(f"    - {w}" for w in f.warnings)
        if f.errors:
            lines.append("  Errors:")
            lines.extend(f"    - {e}" for e in f.errors)

    return "\n".join(lines) if lines else "No input issues detected."

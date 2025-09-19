from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from app.models.InputFileParseResult import InputFileParseResult
from app.models.InputScanResult import InputScanResult

INPUT_DIR_NAME = "input"
PREFIX_FILE_SUFFIX = "-vault-prefixes.txt"
SUFFIX_FILE_SUFFIX = "-vault-suffixes.txt"

FILENAME_PREFIXES_PATTERN = re.compile(r".*-vault-prefixes\.txt\Z")
FILENAME_SUFFIXES_PATTERN = re.compile(r".*-vault-suffixes\.txt\Z")

# allow letters/digits as the first char; then letters/digits/space/colon/underscore/dash/period for up to 62 more
PROJECT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:\s._-]{0,62}\Z")
ROLE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z:\s_-]{0,62}\Z")

# Reasonable guardrails
MAX_FILE_SIZE_BYTES = 512 * 1024  # 512 KB
MAX_PROJECTS_PER_FILE = 50
MAX_ROLES_PER_FILE = 100


def _safe_read_lines(path: Path) -> Iterable[str]:
    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File too large ({size} bytes): {path}")
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            yield raw


def _extract_batch_name_from_prefix_file(path: Path) -> str:
    name = path.name
    if name.endswith(PREFIX_FILE_SUFFIX):
        return name[: -len(PREFIX_FILE_SUFFIX)]
    return Path(name).stem


def _extract_batch_name_from_suffix_file(path: Path) -> str:
    name = path.name
    if name.endswith(SUFFIX_FILE_SUFFIX):
        return name[: -len(SUFFIX_FILE_SUFFIX)]
    return Path(name).stem


def _validate_project(project: str) -> Optional[str]:
    """
    Ensures that the project prefix is suitable for a vault name.
    Return error message if invalid, else None
    """
    if not PROJECT_PATTERN.match(project):
        return "Invalid project prefix (allowed: letters, digits, '.', '-', '_', ':' and spaces; 1-63 chars; must start alphanumeric)"
    return None


def _validate_role(role: str) -> Optional[str]:
    """
    Ensures that the role suffix is suitable for a vault name.
    Return error message if invalid, else None
    """
    if not ROLE_PATTERN.match(role):
        return "Invalid role suffix (allowed: letters, '-', '_', ':' and spaces; 1-63 chars;)"
    return None


def _find_files_by_pattern(
    pattern: re.Pattern, base_dir: Optional[Path] = None
) -> List[Path]:
    """Finds all files in the input directory that have the correct suffix. Makes no claims about quality of the project prefix."""
    root = (base_dir or Path.cwd()).resolve()
    input_dir = root / INPUT_DIR_NAME

    # determine if input directory is valid
    if not input_dir.exists() or not input_dir.is_dir():
        return []

    # perform regex match on all filenames within input directory
    return [
        p for p in sorted(input_dir.iterdir()) if p.is_file() and pattern.match(p.name)
    ]


def find_prefix_files(base_dir: Optional[Path] = None) -> List[Path]:
    return _find_files_by_pattern(FILENAME_PREFIXES_PATTERN, base_dir=base_dir)


def find_suffix_files(base_dir: Optional[Path] = None) -> List[Path]:
    return _find_files_by_pattern(FILENAME_SUFFIXES_PATTERN, base_dir=base_dir)


def _parse_lines(
    lines: Iterable[str], validate_fn, max_items: int, item_label_for_messages: str
) -> Tuple[list[str], list[str], list[str]]:
    """
    Shared line parsing core.
    Returns: (items, warnings, errors)
    """
    warnings: List[str] = []
    errors: List[str] = []
    seen: set[str] = set()
    items: List[str] = []

    for idx, raw in enumerate(lines, start=1):
        text = raw.strip()
        # ignore comments
        if not text or text.startswith("#"):
            continue

        # determines if text is vault-friendly
        err = validate_fn(text)
        if err:
            errors.append(f"Line {idx}: {err} -> {text!r}")
            continue

        # skip duplicates
        if text in seen:
            warnings.append(
                f"Line {idx}: duplicate {item_label_for_messages} ignored -> {text!r}"
            )
            continue

        # mark this project-prefix as done
        items.append(text)
        seen.add(text)

        # ensure we haven't exceeded our limit
        if len(items) > max_items:
            errors.append(
                f"Too many {item_label_for_messages}s (> {max_items}); aborting parse."
            )
            items = []
            break

    if not items and not errors:
        warnings.append(
            f"File contained no usable {item_label_for_messages}s (only comments/blank lines)."
        )

    return items, warnings, errors


def parse_prefix_file(path: Path) -> InputFileParseResult:
    try:
        lines = list(_safe_read_lines(path))
    except Exception as e:
        return InputFileParseResult(
            kind="prefixes",
            batch_name=_extract_batch_name_from_prefix_file(path),
            path=path,
            projects=[],
            roles=[],
            warnings=[],
            errors=[f"Failed to read: {e}"],
        )

    projects, warnings, errors = _parse_lines(
        lines=lines,
        validate_fn=_validate_project,
        max_items=MAX_PROJECTS_PER_FILE,
        item_label_for_messages="prefix",
    )

    return InputFileParseResult(
        kind="prefixes",
        batch_name=_extract_batch_name_from_prefix_file(path),
        path=path,
        projects=projects,
        roles=[],
        warnings=warnings,
        errors=errors,
    )


def parse_suffix_file(path: Path) -> InputFileParseResult:
    try:
        lines = list(_safe_read_lines(path))
    except Exception as e:
        return InputFileParseResult(
            kind="suffixes",
            batch_name=_extract_batch_name_from_suffix_file(path),
            path=path,
            projects=[],
            roles=[],
            warnings=[],
            errors=[f"Failed to read: {e}"],
        )

    roles, warnings, errors = _parse_lines(
        lines=lines,
        validate_fn=_validate_role,
        max_items=MAX_ROLES_PER_FILE,
        item_label_for_messages="suffix",
    )

    return InputFileParseResult(
        kind="suffixes",
        batch_name=_extract_batch_name_from_suffix_file(path),
        path=path,
        projects=[],
        roles=roles,
        warnings=warnings,
        errors=errors,
    )


def load_all_inputs(base_dir: Optional[Path] = None) -> InputScanResult:
    """
    Main driver of input scanning.
    Attempts to find all matching project/role files in `/input/`.
    Returns a scan result
    """
    prefix_files: List[InputFileParseResult] = []
    suffix_files: List[InputFileParseResult] = []
    fatal_errors: List[str] = []

    # 1. obtain all input files present in the project base directory
    prefix_paths = find_prefix_files(base_dir)
    suffix_paths = find_suffix_files(base_dir)

    # 2. Return an empty scan result if there were no relevant files found
    if not prefix_paths and not suffix_paths:
        fatal_errors.append(
            f"No files found matching '*-vault-prefixes.txt' or '*-vault-suffixes.txt' in ./{INPUT_DIR_NAME}/"
        )
        return InputScanResult(
            prefix_files=prefix_files,
            suffix_files=suffix_files,
            fatal_errors=fatal_errors,
        )

    # 3. Collect matching input files, perform basic validation and collect metadata
    for p in prefix_paths:
        prefix_files.append(parse_prefix_file(p))
    for p in suffix_paths:
        suffix_files.append(parse_suffix_file(p))

    return InputScanResult(
        prefix_files=prefix_files, suffix_files=suffix_files, fatal_errors=fatal_errors
    )


def summarize_scan(scan: InputScanResult) -> str:
    lines: List[str] = []
    if scan.fatal_errors:
        lines.append("FATAL:")
        lines.extend(f"  - {e}" for e in scan.fatal_errors)

    if scan.prefix_files:
        lines.append("PREFIX FILES:")
        for f in scan.prefix_files:
            lines.append(
                f"  [{f.batch_name}] {len(f.projects)} project-prefix(es) from {f.path.name}"
            )
            if f.warnings:
                lines.append("    Warnings:")
                lines.extend(f"      - {w}" for w in f.warnings)
            if f.errors:
                lines.append("    Errors:")
                lines.extend(f"      - {e}" for e in f.errors)

    if scan.suffix_files:
        lines.append("SUFFIX FILES:")
        for f in scan.suffix_files:
            lines.append(
                f"  [{f.batch_name}] {len(f.roles)} role-suffix(es) from {f.path.name}"
            )
            if f.warnings:
                lines.append("    Warnings:")
                lines.extend(f"      - {w}" for w in f.warnings)
            if f.errors:
                lines.append("    Errors:")
                lines.extend(f"      - {e}" for e in f.errors)

    return "\n".join(lines) if lines else "No input issues detected."

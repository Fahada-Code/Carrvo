"""LaTeX → PDF compilation.

Tries `tectonic` first (no installation headache, self-contained), then falls back
to `pdflatex`. Raises CompilerError with the exact LaTeX error output on failure.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from pathlib import Path

from config import settings
from security import UnsafeLatexError, scan_latex


class CompilerError(Exception):
    """Raised when LaTeX compilation fails. Contains the raw compiler output."""


async def compile_latex(tex_source: str, output_name: str) -> Path:
    """
    Compile LaTeX source to PDF. Returns the path to the compiled PDF.
    `output_name` is used for the output filename (no extension).

    The source is scanned for shell-execution / file-I/O primitives before
    compilation, and the compiler itself runs with shell-escape disabled.
    """
    try:
        scan_latex(tex_source)
    except UnsafeLatexError as exc:
        raise CompilerError(f"Refusing to compile unsafe LaTeX: {exc}") from exc

    with tempfile.TemporaryDirectory(prefix="carrvo-latex-") as tmp:
        tmp_path = Path(tmp)
        tex_file = tmp_path / f"{output_name}.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        cmd = _build_command(tex_file, tmp_path)
        output = await _run(cmd, cwd=tmp_path)

        pdf_file = tmp_path / f"{output_name}.pdf"
        if not pdf_file.exists():
            raise CompilerError(f"Compilation produced no PDF.\n\nCompiler output:\n{output}")

        # Move the PDF to a securely-created temp file outside the auto-deleted dir.
        fd, dest_name = tempfile.mkstemp(suffix=".pdf", prefix=f"carrvo-{output_name}-")
        os.close(fd)
        dest = Path(dest_name)
        shutil.move(str(pdf_file), dest)
        return dest


def _build_command(tex_file: Path, output_dir: Path) -> list[str]:
    if shutil.which("tectonic"):
        # tectonic disables shell-escape by default and sandboxes file access.
        return ["tectonic", "--outdir", str(output_dir), str(tex_file)]

    latex_cmd = settings.latex_cmd if shutil.which(settings.latex_cmd) else "pdflatex"
    if not shutil.which(latex_cmd):
        raise CompilerError(
            "No LaTeX compiler found. Install tectonic (recommended) or pdflatex."
        )

    return [
        latex_cmd,
        "-no-shell-escape",  # defense in depth: never allow \write18 even if scan is bypassed
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={output_dir}",
        str(tex_file),
    ]


async def _run(cmd: list[str], cwd: Path) -> str:
    """Run the compiler. Returns combined stdout+stderr text; raises on failure."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError as exc:
        proc.kill()
        raise CompilerError("LaTeX compilation timed out after 120s.") from exc

    output = (stdout + stderr).decode(errors="replace")

    if proc.returncode != 0:
        error_line = _extract_latex_error(output)
        raise CompilerError(f"LaTeX compiler failed:\n{error_line}\n\nFull output:\n{output}")

    return output


def _extract_latex_error(output: str) -> str:
    """Pull the first meaningful error line from LaTeX compiler output."""
    for line in output.splitlines():
        if line.startswith("!") or "Error" in line:
            return line
    return output[:500]

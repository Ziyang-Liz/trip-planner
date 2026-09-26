"""Create a source-only ZIP without copying local secrets or generated files."""

from datetime import datetime
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build",
            ".pytest_cache", ".vscode", ".idea", ".tools", "release"}
SUFFIXES = {".py", ".toml", ".lock", ".json", ".ts", ".vue", ".html", ".css", ".sql", ".yml", ".yaml", ".md", ".txt"}


def include(path):
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED or part.endswith(".egg-info") for part in relative.parts):
        return False
    if path.name.startswith(".env"):
        return path.name == ".env.example"
    if len(relative.parts) == 1:
        return path.name in {"README.md", "LICENSE", "NOTICE", "ATTRIBUTIONS.md", ".gitignore"}
    if relative.parts[:2] == ("docs", "images") and path.suffix == ".png":
        return True
    return relative.parts[0] in {"itrip-system", "scripts", "docs"} and (
        path.suffix in SUFFIXES or path.name == ".nvmrc"
    )


def export():
    # Check for accidental copies of configured credentials without printing values.
    secrets = []
    for env_path in ROOT.glob("itrip-system/*/.env"):
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if any(word in key.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")) and len(value) > 8:
                secrets.append(value.encode())
    files = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and include(path):
            if path.is_symlink():
                raise SystemExit(f"Export refused: symlink {path.relative_to(ROOT)}")
            data = path.read_bytes()
            if any(secret in data for secret in secrets):
                raise SystemExit(f"Export refused: configured credential found in {path.relative_to(ROOT)}")
            files.append((path, data))
    destination = ROOT / "release"
    destination.mkdir(exist_ok=True)
    archive = destination / f"trip-planner-public-{datetime.now():%Y%m%d-%H%M%S-%f}.zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as output:
        for path, data in files:
            output.writestr(path.relative_to(ROOT).as_posix(), data)
    print(f"Exported {len(files)} source/documentation files to {archive}")


if __name__ == "__main__":
    export()

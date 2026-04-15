"""Create deployment ZIP for CodeBuild."""
import zipfile, os, pathlib

src = pathlib.Path("backend")
out = os.path.join(os.environ["TEMP"], "backend-deploy8.zip")
skip = {
    "__pycache__", ".pytest_cache", ".env",
    "chainfactor.db", "chainfactor.db-shm", "chainfactor.db-wal",
    "backend-source.zip", "venv", ".venv", "node_modules",
}

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in src.rglob("*"):
        if f.is_file() and not any(s in f.parts for s in skip) and not f.name.endswith(".pyc"):
            zf.write(f, f.relative_to(src))

print(f"Created: {out}")
print(f"Size: {os.path.getsize(out)} bytes")

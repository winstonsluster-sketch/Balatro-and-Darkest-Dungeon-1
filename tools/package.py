"""Build dist/DarkestDeck-<version>.zip from mod/DarkestDeck (archive root = the mod folder's contents)."""
import hashlib, json, re, zipfile
from sheets import ROOT

def main():
    src = ROOT / "mod/DarkestDeck"
    version = re.search(r'version = "([\d.]+)"', (src / "ddeck/core.lua").read_text()).group(1)
    out = ROOT / "dist" / f"DarkestDeck-{version}.zip"
    out.parent.mkdir(exist_ok=True)
    files = sorted(p for p in src.rglob("*") if p.is_file())
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(src).as_posix())
    entries = [{"path": p.relative_to(src).as_posix(), "size": p.stat().st_size} for p in files]
    data = out.read_bytes()
    info = {"file": out.name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "entries": entries}
    (ROOT / "dist" / "package.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))

if __name__ == "__main__": main()

import base64
import hashlib
import io
import json
import posixpath
import re
import sys
import tarfile
import urllib.parse
import urllib.request
from pathlib import Path

import environ
from invoke import task

env = environ.Env()

VENDOR_DIR = Path(__file__).resolve().parent / "coderdojochi" / "static" / "vendor"
VENDOR_KEEP = {"vendor.json", "README.md"}
NPM_REGISTRY = "https://registry.npmjs.org"

# Mirrors the patterns Django's ManifestStaticFilesStorage rewrites, so a
# reference to a file we don't ship fails here instead of in collectstatic.
_CSS_URL_RE = re.compile(r"""url\((['"]?)\s*(.*?)\1\)""")
_CSS_IMPORT_RE = re.compile(r"""@import\s*["']\s*(.*?)["']""")
_JS_SOURCEMAP_RE = re.compile(r"(?m)^//# (?-i:sourceMappingURL)=(.*)$")
_CSS_SOURCEMAP_RE = re.compile(r"(?m)^/\*#[ \t](?-i:sourceMappingURL)=(.*?)[ \t]*\*/$")
_STRIP_SOURCEMAP_RE = re.compile(
    r"(?m)^[ \t]*(?://[#@][ \t]*sourceMappingURL=[^\r\n]*|/\*[#@][ \t]*sourceMappingURL=[^\r\n]*?\*/)[ \t]*(?:\r?\n)?"
)
_FONT_FACE_RE = re.compile(r"/\* (?P<name>[^*]+?) \*/\s*@font-face\s*\{[^}]*\}\s*")


def _fetch(url):
    if not url.startswith("https://"):
        raise RuntimeError(f"Refusing non-https URL: {url}")
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - https checked above
        return response.read()


def _verify_integrity(data, integrity, label):
    """Check data against an SRI string; every listed hash must match."""
    checked = 0
    for token in integrity.split():
        algo, _, expected = token.partition("-")
        if algo not in {"sha256", "sha384", "sha512"}:
            continue
        actual = base64.b64encode(hashlib.new(algo, data).digest()).decode()
        if actual != expected:
            raise RuntimeError(
                f"{label}: {algo} integrity mismatch (expected {expected}, got {actual})"
            )
        checked += 1
    if not checked:
        raise RuntimeError(f"{label}: no usable sha256/384/512 hash in {integrity!r}")


def _npm_tarball(package, version):
    label = f"{package}@{version}"
    meta = json.loads(
        _fetch(f"{NPM_REGISTRY}/{urllib.parse.quote(package, safe='@')}/{version}")
    )
    dist = meta["dist"]
    integrity = dist.get("integrity", "")
    if "sha512-" not in integrity:
        raise RuntimeError(f"{label}: registry has no sha512 integrity")
    data = _fetch(dist["tarball"])
    _verify_integrity(data, integrity, label)
    return data


def _read_tar_files(tar_bytes, wanted, label):
    """Read the wanted `package/<path>` regular files into memory (never extracted to disk)."""
    found = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            name = member.name.removeprefix("./")
            if not name.startswith("package/"):
                continue
            rel = name.removeprefix("package/")
            if rel not in wanted:
                continue
            if not member.isfile():
                raise RuntimeError(
                    f"{label}: {rel} is not a regular file in the tarball"
                )
            found[rel] = tar.extractfile(member).read()
    missing = sorted(set(wanted) - set(found))
    if missing:
        raise RuntimeError(f"{label}: not in tarball: {', '.join(missing)}")
    return found


def _keep_subsets(text, subsets, label):
    """Keep only the @fontsource @font-face blocks for the given unicode subsets."""
    blocks = list(_FONT_FACE_RE.finditer(text))
    if len(blocks) != text.count("@font-face") or _FONT_FACE_RE.sub("", text).strip():
        raise RuntimeError(f"{label}: unexpected @font-face layout")
    wanted = re.compile(
        rf"-(?:{'|'.join(map(re.escape, subsets))})-\d+-(?:normal|italic)$"
    )
    kept = [m.group(0).strip() for m in blocks if wanted.search(m.group("name"))]
    if len(kept) != len(subsets):
        raise RuntimeError(
            f"{label}: expected {len(subsets)} @font-face blocks, kept {len(kept)}"
        )
    return "\n\n".join(kept) + "\n"


def _drop_font_formats(text, formats, label):
    """Remove `, url(x.<fmt>) format('<fmt>')` entries from @font-face src lists."""
    for fmt in formats:
        pattern = rf"""\s*,\s*url\(\s*(['"]?)[^'")]*?\.{re.escape(fmt)}(?:[?#][^'")]*)?\1\s*\)\s*format\(\s*['"]{re.escape(fmt)}['"]\s*\)"""
        text, count = re.subn(pattern, "", text)
        if not count:
            raise RuntimeError(f"{label}: no {fmt} font entries to drop")
    return text


def _transform(data, spec, label):
    if not any(
        key in spec for key in ("strip_sourcemap", "keep_subsets", "drop_font_formats")
    ):
        return data
    text = data.decode("utf-8")
    if spec.get("keep_subsets"):
        text = _keep_subsets(text, spec["keep_subsets"], label)
    if spec.get("drop_font_formats"):
        text = _drop_font_formats(text, spec["drop_font_formats"], label)
    if spec.get("strip_sourcemap"):
        text, count = _STRIP_SOURCEMAP_RE.subn("", text)
        if not count:
            raise RuntimeError(f"{label}: no sourceMappingURL comment to strip")
    return text.encode("utf-8")


def _references(rel, data):
    """Yield the local files a CSS/JS file points at, as Django's manifest storage would."""
    if rel.endswith(".css"):
        text = data.decode("utf-8")
        urls = [m.group(2) for m in _CSS_URL_RE.finditer(text)]
        urls += _CSS_IMPORT_RE.findall(text) + _CSS_SOURCEMAP_RE.findall(text)
    elif rel.endswith(".js"):
        urls = _JS_SOURCEMAP_RE.findall(data.decode("utf-8"))
    else:
        return
    for raw in urls:
        url = raw.strip()
        if (
            not url
            or url.startswith(("#", "data:", "/"))
            or re.match(r"^[a-z][a-z0-9+.-]*:", url, re.IGNORECASE)
        ):
            continue
        path = re.split(r"[?#]", url, maxsplit=1)[0]
        yield url, posixpath.normpath(posixpath.join(posixpath.dirname(rel), path))


def _target(rel):
    target = (VENDOR_DIR / rel).resolve()
    if (
        Path(rel).is_absolute()
        or not target.is_relative_to(VENDOR_DIR)
        or target == VENDOR_DIR
    ):
        raise RuntimeError(f"Unsafe vendor path: {rel}")
    if rel in VENDOR_KEEP:
        raise RuntimeError(f"Vendor path collides with a kept file: {rel}")
    return target


def _build_package(entry, outputs):
    package, version = entry["package"], entry["version"]
    label = f"{package}@{version}"
    items = []
    if entry.get("files"):
        tar_files = _read_tar_files(
            _npm_tarball(package, version), {f["from"] for f in entry["files"]}, label
        )
        items += [(spec, tar_files[spec["from"]]) for spec in entry["files"]]
    for spec in entry.get("urls", []):
        url = spec["url"].format(version=version)
        data = _fetch(url)
        _verify_integrity(data, spec["integrity"], url)
        items.append((spec, data))
    for spec, data in items:
        rel = spec["to"]
        _target(rel)
        if rel in outputs:
            raise RuntimeError(f"Duplicate vendor path: {rel}")
        outputs[rel] = _transform(data, spec, f"{label} {rel}")
    sys.stdout.write(f"{label}: {len(items)} files\n")


@task
def vendor(ctx):
    """Download the front-end libraries in vendor.json into coderdojochi/static/vendor/."""
    manifest = json.loads((VENDOR_DIR / "vendor.json").read_text())
    outputs = {}
    for entry in manifest["packages"]:
        _build_package(entry, outputs)

    for rel, data in outputs.items():
        for url, ref in _references(rel, data):
            if ref not in outputs:
                raise RuntimeError(
                    f"{rel} references {url!r}, which vendor.json does not ship"
                )

    written = 0
    for rel, data in sorted(outputs.items()):
        target = _target(rel)
        if target.is_file() and target.read_bytes() == data:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written += 1

    removed = 0
    for path in sorted(VENDOR_DIR.rglob("*"), reverse=True):
        rel = path.relative_to(VENDOR_DIR).as_posix()
        if path.is_dir():
            if not any(path.iterdir()):
                path.rmdir()
        elif rel not in outputs and rel not in VENDOR_KEEP:
            path.unlink()
            removed += 1
    sys.stdout.write(
        f"vendor: {len(outputs)} files, {written} written, {removed} stale removed\n"
    )


@task
def release(ctx):
    collect_static(ctx)
    migrate(ctx)
    load_fixtures(ctx)


@task(help={"port": "Port to use when serving traffic. Defaults to $PORT."})
def start(ctx, port=env.int("PORT", default=8000)):
    ctx.run(
        f"gunicorn coderdojochi.wsgi -w 2 -b 0.0.0.0:{port} --reload --log-file -",
    )


@task
def migrate(ctx):
    ctx.run("python3 manage.py migrate")


@task
def load_fixtures(ctx):
    if env.bool("ENABLE_DEV_FIXTURES", default=False):
        ctx.run("python3 manage.py loaddata fixtures/*.json")


@task
def collect_static(ctx):
    if not env.bool("DEBUG", default=False):
        ctx.run("python3 manage.py collectstatic --no-input")


@task(help={"app": "Specific app to run tests on. Defaults to all apps."})
def test(ctx, app=""):
    ctx.run(f"python3 manage.py test {app}")

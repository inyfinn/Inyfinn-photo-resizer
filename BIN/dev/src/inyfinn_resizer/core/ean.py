"""EAN produktu: wykrywanie z folderu produktu (karta Excel, plik *EAN*.txt, kod kreskowy) i role zdjęć."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_EAN_RE = re.compile(r"(?<!\d)\d{13}(?!\d)")
_INDEX_RE = re.compile(r"(?<!\d)(\d{7})(?!\d)")

# Słowa w nazwie pliku -> rola Rossmanna. Kolejność ma znaczenie (dłuższe przed krótszymi).
ROLE_WORDS: list[tuple[tuple[str, ...], str]] = [
    (("TYŁ", "TYL", "BACK"), "t"),
    (("BOK-L", "LEWY", "LEFT"), "bl"),
    (("BOK-P", "PRAWY", "RIGHT"), "bp"),
    (("SPÓD", "SPOD", "BOTTOM"), "s"),
    (("WIERZCH", "GÓRA", "GORA", "TOP"), "w"),
    (("FRONT", "PRZÓD", "PRZOD"), "g"),
]

ROLE_LABELS = {
    "g": "główne", "fr": "front", "t": "tył", "bl": "bok lewy", "bp": "bok prawy", "s": "spód", "w": "wierzch",
    **{f"k{i}": f"w użyciu {i}" for i in range(1, 5)},
    **{f"rc{i}": f"rich content {i}" for i in range(1, 5)},
}


def ean13_valid(code: str) -> bool:
    if not re.fullmatch(r"\d{13}", code or ""):
        return False
    digits = [int(c) for c in code]
    total = sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits[:12]))
    return (10 - total % 10) % 10 == digits[12]


def role_from_name(name: str) -> str:
    """Rola z nazwy pliku (FRONT -> g, TYŁ -> t ...). Pusty tekst = nie rozpoznano."""
    tokens = re.split(r"[^0-9A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+", Path(name).stem.upper())
    joined = "-".join(tokens)
    for words, role in ROLE_WORDS:
        for word in words:
            if word in tokens or (("-" in word) and word in joined):
                return role
    return ""


# Wzorce nazw plików wg sieci (pole RetailPreset.naming). Czytają je też skrypty JSX (retail_presets.json).
NAME_PATTERNS = {"ean_role": "{ean}_{role}{ext}"}


def output_name(ean: str, role: str, ext: str = ".png") -> str:
    return NAME_PATTERNS["ean_role"].format(ean=ean, role=role, ext=ext)


def role_collisions(roles: dict[Path, str]) -> dict[str, list[Path]]:
    """Role przypisane do więcej niż jednego pliku (albo brak roli pod kluczem '')."""
    by_role: dict[str, list[Path]] = {}
    for path, role in roles.items():
        if role != SKIP_ROLE:
            by_role.setdefault(role, []).append(path)
    return {r: ps for r, ps in by_role.items() if len(ps) > 1 or not r}


SKIP_ROLE = "skip"  # plik nie jest konwertowany (duplikat tej samej strony produktu)


def _pick_key(path: Path) -> tuple:
    """Lepszy plik tej samej roli: PNG przed JPG, potem więcej pikseli, potem większy plik."""
    from PIL import Image

    try:
        with Image.open(path) as im:
            pixels = im.width * im.height
    except OSError:
        pixels = 0
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return (path.suffix.lower() == ".png", pixels, size)


def resolve_roles(paths: list[Path], manual: dict[Path, str] | None = None) -> dict[Path, tuple[str, str]]:
    """Rola każdego pliku i notka. Ręczne role zostają; z automatycznych duplikatów jednej roli zostaje najlepszy
    (``_pick_key``), reszta dostaje ``SKIP_ROLE`` i notkę „wybrano większy plik: …”. Remis = obie role zostają
    (kolizja do rozstrzygnięcia przez człowieka)."""
    manual = manual or {}
    out: dict[Path, tuple[str, str]] = {p: (manual[p], "") for p in paths if p in manual}
    groups: dict[str, list[Path]] = {}
    for p in paths:
        if p not in manual:
            groups.setdefault(role_from_name(p.name), []).append(p)
    for role, group in groups.items():
        if not role or len(group) == 1:
            out.update({p: (role, "") for p in group})
            continue
        keys = {p: _pick_key(p) for p in group}
        best = max(group, key=keys.get)
        if sum(1 for p in group if keys[p] == keys[best]) > 1:
            out.update({p: (role, "") for p in group})
            continue
        for p in group:
            out[p] = (role, "") if p == best else (SKIP_ROLE, f"wybrano większy plik: {best.name}")
    return out


def find_product_dir(path: Path) -> Path | None:
    """Folder produktu = pierwszy w górę, który ma podfolder 1-MATERIAŁY."""
    for parent in [path, *path.parents] if path.is_dir() else path.parents:
        try:
            if any(c.is_dir() and c.name.upper().startswith("1-MATERIA") for c in parent.iterdir()):
                return parent
        except OSError:
            continue
    return None


def product_index(product_dir: Path) -> str:
    m = _INDEX_RE.search(product_dir.name)
    return m.group(1) if m else ""


def _materials(product_dir: Path) -> Path | None:
    return next((c for c in product_dir.iterdir() if c.is_dir() and c.name.upper().startswith("1-MATERIA")), None)


@dataclass
class EanFinding:
    ean: str
    source: str  # opis dla handlowca: "z karty wprowadzenia (plik.xlsx)"


@dataclass
class EanResult:
    ean: str = ""
    source: str = ""
    findings: list[EanFinding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def conflict(self) -> bool:
        return len({f.ean for f in self.findings}) > 1


def ean_from_excel(product_dir: Path, index: str = "") -> tuple[list[EanFinding], list[str]]:
    import openpyxl

    found: list[EanFinding] = []
    notes: list[str] = []
    mat = _materials(product_dir)
    if mat is None:
        return found, notes
    for xlsx in sorted(mat.rglob("*.xlsx")):
        if xlsx.name.startswith("~$"):
            continue
        try:
            wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
        except Exception:
            continue
        try:
            texts = [str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row if c.value is not None]
        finally:
            wb.close()
        if index and index not in xlsx.name and not any(index in t for t in texts):
            other = _INDEX_RE.search(xlsx.name)
            notes.append(f"Pominąłem {xlsx.name}: karta dotyczy innego produktu"
                         + (f" ({other.group(1)})." if other else "."))
            continue
        for t in texts:
            code = t.strip().removesuffix(".0")
            if ean13_valid(code):
                found.append(EanFinding(code, f"z karty wprowadzenia ({xlsx.name})"))
                break
    return found, notes


# Konwencja usera: 1-MATERIAŁY/<indeks> - EAN<13 cyfr>.txt, np. "6300783 - EAN5903548001186.txt".
_TXT_RE = re.compile(r"^\s*(\d{7})?[\s_-]*EAN[\s_:-]*(\d{13})?", re.I)


def ean_from_txt(product_dir: Path, index: str = "") -> tuple[list[EanFinding], list[str]]:
    """Plik `<indeks> - EAN<13 cyfr>.txt` w 1-MATERIAŁY (albo w folderze produktu): EAN z nazwy, inaczej z treści."""
    found: list[EanFinding] = []
    notes: list[str] = []
    mat = _materials(product_dir)
    for folder in ([mat] if mat else []) + [product_dir]:
        for txt in sorted(folder.glob("*.txt")):
            m = _TXT_RE.match(txt.stem)
            if not m:
                continue
            if index and m.group(1) and m.group(1) != index:
                notes.append(f"Pominąłem {txt.name}: plik dotyczy innego produktu ({m.group(1)}).")
                continue
            code = m.group(2) or ""
            if not code:
                try:
                    code = next(iter(_EAN_RE.findall(txt.read_text(encoding="utf-8", errors="ignore"))), "")
                except OSError:
                    code = ""
            if ean13_valid(code):
                found.append(EanFinding(code, f"z pliku {txt.name}"))
    return found, notes


def ean_from_barcode(image_path: Path) -> str:
    try:
        import zxingcpp
        from PIL import Image
    except ImportError:
        return ""
    with Image.open(image_path) as im:
        rgb = im.convert("RGB")
    for scale in (1.0, 0.5):
        img = rgb if scale == 1.0 else rgb.resize((int(rgb.width * scale), int(rgb.height * scale)))
        for res in zxingcpp.read_barcodes(img):
            if ean13_valid(res.text):
                return res.text
    return ""


def detect_ean(files: list[Path]) -> EanResult:
    """Kolejność (decyzja 18.11.2026, tak samo w skryptach JSX): plik `<indeks> - EAN….txt`, karta Excel z indeksem,
    kod kreskowy na zdjęciu tyłu. Sprawdzamy wszystkie; niezgodność = conflict."""
    result = EanResult()
    if not files:
        return result
    product = find_product_dir(files[0])
    if product is not None:
        index = product_index(product)
        txt, notes = ean_from_txt(product, index)  # 1: baza prowadzona ręcznie przez usera
        result.findings += txt
        result.notes += notes
        excel, notes = ean_from_excel(product, index)  # 2: karta wprowadzenia z indeksem produktu
        result.findings += excel
        result.notes += notes
    backs = [f for f in files if role_from_name(f.name) == "t"]
    if not backs:  # handlowiec wrzucił sam front: szukamy tyłu obok
        backs = [f for f in files[0].parent.glob("*") if f.suffix.lower() in (".png", ".jpg", ".jpeg")
                 and role_from_name(f.name) == "t"]
    backs.sort(key=lambda p: p.stat().st_size)
    for back in backs:
        code = ean_from_barcode(back)
        if code:
            result.findings.append(EanFinding(code, "z kodu kreskowego na zdjęciu tyłu"))
            break
    if result.findings:
        result.ean, result.source = result.findings[0].ean, result.findings[0].source
    return result

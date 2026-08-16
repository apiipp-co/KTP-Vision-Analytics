"""Generate deterministic, visibly synthetic test fixtures; never real identity data."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
KTP_DIR = ROOT / "data" / "testing" / "ktp"
NON_KTP_DIR = ROOT / "data" / "testing" / "non_ktp"
TRUTH_DIR = ROOT / "data" / "ground_truth"
MANIFEST = ROOT / "data" / "test_manifest.csv"
DATASET_METADATA = ROOT / "data" / "dataset_metadata.json"
DATASET_VERSION = "synthetic-v2.0.0"


def font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def synthetic_ktp(index: int) -> tuple[Image.Image, dict]:
    birth_day = 10 + index
    female = index % 2 == 0
    nik_day = birth_day + (40 if female else 0)
    nik = f"999999{nik_day:02d}0590{index:04d}"
    gender = "PEREMPUAN" if female else "LAKI-LAKI"
    fields = {
        "provinsi": "PROVINSI SINTETIS", "kabupaten_kota": None,
        "nik": nik, "nama": f"DATA SINTETIS {index:02d}", "tempat_lahir": "KOTA CONTOH",
        "tanggal_lahir": f"{birth_day:02d}-05-1990", "jenis_kelamin": gender,
        "golongan_darah": None, "alamat": "JALAN CONTOH DATA UJI",
        "rt": "001", "rw": "002", "kelurahan_desa": "DESA SINTETIS",
        "kecamatan": "KECAMATAN CONTOH", "agama": None, "status_perkawinan": None,
        "pekerjaan": "DATA TESTER", "kewarganegaraan": "WNI", "berlaku_hingga": "SEUMUR HIDUP",
    }
    image = Image.new("RGB", (1000, 620), "#dbeafe")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((15, 15, 985, 605), radius=24, outline="#334155", width=5)
    draw.text((235, 30), "KARTU TANDA PENDUDUK — SYNTHETIC", fill="#0f172a", font=font(28))
    draw.text((330, 70), fields["provinsi"], fill="#0f172a", font=font(24))
    draw.rectangle((55, 145, 260, 410), fill="#94a3b8", outline="#475569", width=3)
    draw.ellipse((100, 180, 215, 295), fill="#cbd5e1")
    draw.rectangle((85, 300, 230, 385), fill="#cbd5e1")
    lines = [
        ("NIK", fields["nik"]), ("Nama", fields["nama"]),
        ("Tempat/Tgl Lahir", f"{fields['tempat_lahir']}, {fields['tanggal_lahir']}"),
        ("Jenis Kelamin", fields["jenis_kelamin"]), ("Alamat", fields["alamat"]),
        ("RT/RW", f"{fields['rt']}/{fields['rw']}"), ("Kel/Desa", fields["kelurahan_desa"]),
        ("Kecamatan", fields["kecamatan"]), ("Pekerjaan", fields["pekerjaan"]),
        ("Kewarganegaraan", fields["kewarganegaraan"]), ("Berlaku Hingga", fields["berlaku_hingga"]),
    ]
    y = 125
    for label, value in lines:
        draw.text((300, y), f"{label:<20}: {value}", fill="#111827", font=font(20))
        y += 39
    draw.text((295, 520), "BUKAN DOKUMEN RESMI • DATA UJI SINTETIS", fill="#b91c1c", font=font(26))
    return image, fields


def non_ktp(index: int) -> tuple[Image.Image, str]:
    colors = ["#fef3c7", "#dcfce7", "#fce7f3", "#ede9fe", "#e0f2fe"]
    image = Image.new("RGB", (900, 600), colors[index % len(colors)])
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((35, 35, 865, 565), radius=20, outline="#334155", width=4)
    kinds = ["SIM SINTETIS", "STRUK BELANJA", "FOTO BIASA", "SCREENSHOT", "GAMBAR RANDOM"]
    kind = kinds[index % len(kinds)]
    draw.text((250, 75), f"{kind} — SYNTHETIC", fill="#111827", font=font(32))
    if kind == "FOTO BIASA":
        draw.rectangle((70, 150, 830, 500), fill="#7dd3fc")
        draw.rectangle((70, 360, 830, 500), fill="#65a30d")
        draw.ellipse((650, 180, 730, 260), fill="#fde047")
        draw.polygon([(300, 390), (430, 230), (560, 390)], fill="#64748b")
    elif kind == "SCREENSHOT":
        draw.rectangle((75, 145, 825, 500), fill="white", outline="#94a3b8", width=3)
        draw.rectangle((75, 145, 825, 195), fill="#cbd5e1")
        for row in range(5):
            draw.rectangle((120, 235 + row * 48, 730 - row * 25, 255 + row * 48), fill="#94a3b8")
    elif kind == "GAMBAR RANDOM":
        for row in range(7):
            x = 100 + row * 90
            draw.ellipse((x, 175 + (row % 2) * 120, x + 110, 285 + (row % 2) * 120), fill=colors[(index + row) % len(colors)], outline="#475569")
    else:
        for row in range(7):
            draw.text((110, 165 + row * 48), f"Baris data uji {index:02d}.{row + 1}     {10_000 + row * 2_500:,}", fill="#334155", font=font(22))
    draw.text((220, 520), "BUKAN KTP • DATA UJI SINTETIS", fill="#b91c1c", font=font(25))
    return image, kind


def variation(image: Image.Image, index: int) -> tuple[Image.Image, str]:
    variants = ["clear", "dark", "rotated", "low_resolution", "blur", "partially_cropped"]
    name = variants[index % len(variants)]
    if name == "dark":
        image = ImageEnhance.Brightness(image).enhance(0.62)
    elif name == "rotated":
        image = image.rotate(4, expand=True, fillcolor="white")
    elif name == "low_resolution":
        image = image.resize((600, 372)).resize(image.size)
    elif name == "blur":
        image = image.filter(ImageFilter.GaussianBlur(1.2))
    elif name == "partially_cropped":
        image = image.crop((100, 0, image.width, image.height)).resize(image.size)
    return image, name


def main() -> None:
    KTP_DIR.mkdir(parents=True, exist_ok=True)
    NON_KTP_DIR.mkdir(parents=True, exist_ok=True)
    TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(1, 11):
        image, fields = synthetic_ktp(index)
        image, condition = variation(image, index - 1)
        image_name = f"synthetic_ktp_{index:02d}.jpg"
        truth_name = f"synthetic_ktp_{index:02d}.json"
        image_path = KTP_DIR / image_name
        image.save(image_path, quality=88)
        (TRUTH_DIR / truth_name).write_text(json.dumps(fields, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append([f"ktp_{index:02d}", f"ktp/{image_name}", "KTP", "KTP_INDONESIA", "SYNTHETIC",
                     condition.upper(), truth_name, "NOT_REQUIRED_SYNTHETIC", hashlib.sha256(image_path.read_bytes()).hexdigest(),
                     "Fictional KTP-like fixture with visible synthetic watermark", DATASET_VERSION])
    for index in range(1, 11):
        image, kind = non_ktp(index)
        image, condition = variation(image, index - 1)
        image_name = f"synthetic_non_ktp_{index:02d}.jpg"
        image_path = NON_KTP_DIR / image_name
        image.save(image_path, quality=88)
        rows.append([f"non_ktp_{index:02d}", f"non_ktp/{image_name}", "NON_KTP", kind.replace(" ", "_"), "SYNTHETIC",
                     condition.upper(), "", "NOT_REQUIRED_SYNTHETIC", hashlib.sha256(image_path.read_bytes()).hexdigest(),
                     "Fictional non-KTP fixture with visible synthetic watermark", DATASET_VERSION])
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["image_id", "file_name", "expected_class", "document_type", "source_type",
                         "image_condition", "ground_truth_file", "consent_status", "image_hash", "notes", "dataset_version"])
        writer.writerows(rows)
    DATASET_METADATA.write_text(json.dumps({
        "dataset_version": DATASET_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(rows),
        "ktp_count": 10,
        "non_ktp_count": 10,
        "source_type": "SYNTHETIC",
        "contains_real_pii": False,
        "license": "Project-generated test fixtures",
        "limitations": "Not representative of real camera, demographic, print, damage, or fraud variation.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(rows)} explicitly synthetic images and {MANIFEST}")


if __name__ == "__main__":
    main()

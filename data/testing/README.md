# Synthetic evaluation dataset

This directory contains exactly 20 generated fixtures: 10 KTP-like cards and 10 non-KTP documents. Every image carries a visible `SYNTHETIC` / `BUKAN DOKUMEN RESMI` mark. Names, addresses, and NIK-like strings are fictional test values; region code `999999` is intentionally non-official.

Conditions cover clear, dark, rotated, low-resolution, mildly blurred, and partially cropped variants. Non-KTP fixtures include visibly synthetic SIM, receipt, ordinary-photo illustration, screenshot, and random-image categories. These fixtures test pipeline behavior and are not evidence of performance on real KTP images.

Manifest: `data/test_manifest.csv`

Ground truth: `data/ground_truth/`

Regenerate deterministically:

```bash
python scripts/generate_synthetic_dataset.py
```

Run actual paid model evaluation only with a configured API key:

```bash
python scripts/evaluate.py
```

Before that command completes, accuracy and OCR metrics remain `N/A — belum diuji`. The manifest intentionally contains no prediction column.

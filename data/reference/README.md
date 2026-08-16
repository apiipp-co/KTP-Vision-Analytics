# Official region reference

No hand-written region mapping is bundled. Region validation deliberately returns `NOT_CHECKED` until an official Kemendagri dataset is supplied.

To enable it, convert the current official Kemendagri decision attachment to a UTF-8 CSV named `kemendagri_regions.csv` with these columns:

```csv
code,province,regency,subdistrict,source_url,source_version
```

`code` must be the six NIK region digits (punctuation removed). Keep provenance columns on every row. Current source noted during implementation: Kepmendagri 300.2.2-2138 Tahun 2025 as amended by Kepmendagri 300.2.2-2430 Tahun 2025. Validate licensing and completeness before redistribution.


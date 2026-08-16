from enum import Enum


class RuleStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    NOT_CHECKED = "NOT_CHECKED"


class OverallStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class DocumentType(str, Enum):
    KTP_INDONESIA = "KTP_INDONESIA"
    OTHER = "OTHER"
    UNCERTAIN = "UNCERTAIN"


IDENTITY_FIELDS = (
    "provinsi", "kabupaten_kota", "nik", "nama", "tempat_lahir",
    "tanggal_lahir", "jenis_kelamin", "golongan_darah", "alamat", "rt",
    "rw", "kelurahan_desa", "kecamatan", "agama", "status_perkawinan",
    "pekerjaan", "kewarganegaraan", "berlaku_hingga",
)


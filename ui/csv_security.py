import os
import io
import csv
import time
import struct
import zlib
from config import CSV_MASTER_EXPORT_PASSWORD

def _get_crctable():
    crctable = []
    for i in range(256):
        crc = i
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        crctable.append(crc)
    return crctable

_CRCTABLE = _get_crctable()

class ZipEncrypter:
    """PKZIP standard ZipCrypto stream encrypter (compatible with Windows Explorer, 7-Zip, WinRAR)."""
    def __init__(self, pwd: bytes):
        self.key0 = 305419896
        self.key1 = 591751049
        self.key2 = 878082192
        for p in pwd:
            self._update(p)

    def _crc32(self, ch, crc):
        return (crc >> 8) ^ _CRCTABLE[(crc ^ ch) & 0xFF]

    def _update(self, c):
        self.key0 = self._crc32(c, self.key0)
        self.key1 = (self.key1 + (self.key0 & 0xFF)) & 0xFFFFFFFF
        self.key1 = (self.key1 * 134775813 + 1) & 0xFFFFFFFF
        self.key2 = self._crc32(self.key1 >> 24, self.key2)

    def encrypt(self, data: bytes) -> bytes:
        result = bytearray()
        for p in data:
            k = self.key2 | 2
            c = p ^ (((k * (k ^ 1)) >> 8) & 0xFF)
            self._update(p)
            result.append(c)
        return bytes(result)


def create_password_protected_zip(zip_path: str, internal_filename: str, file_data: bytes, password: str = CSV_MASTER_EXPORT_PASSWORD):
    """
    Creates a standard password-protected ZIP archive containing internal_filename.
    Compatible with Windows Explorer native unzip, 7-Zip, WinRAR, macOS, and Linux.
    """
    pwd_bytes = password.encode("utf-8")
    mtime = time.localtime()
    dos_time = (mtime.tm_hour << 11) | (mtime.tm_min << 5) | (mtime.tm_sec // 2)
    dos_date = ((mtime.tm_year - 1980) << 9) | (mtime.tm_mon << 5) | mtime.tm_mday

    crc = zlib.crc32(file_data) & 0xFFFFFFFF

    # 12-byte encryption header; 12th byte is the most significant byte of the CRC32
    enc_header = os.urandom(11) + bytes([(crc >> 24) & 0xFF])

    enc = ZipEncrypter(pwd_bytes)
    encrypted_header = enc.encrypt(enc_header)

    # Deflate data
    compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    compressed_raw = compressor.compress(file_data) + compressor.flush()

    encrypted_payload = enc.encrypt(compressed_raw)
    encrypted_stream = encrypted_header + encrypted_payload

    fn_bytes = internal_filename.encode("utf-8")
    fn_len = len(fn_bytes)
    comp_size = len(encrypted_stream)
    uncomp_size = len(file_data)

    flags = 0x0801  # Bit 0: Encrypted, Bit 11: UTF-8 filename

    local_header = struct.pack(
        "<4sHHHHHIIIHH",
        b"PK\x03\x04",
        20,
        flags,
        8,
        dos_time,
        dos_date,
        crc,
        comp_size,
        uncomp_size,
        fn_len,
        0
    ) + fn_bytes

    central_dir = struct.pack(
        "<4sHHHHHHIIIHHHHHII",
        b"PK\x01\x02",
        20,
        20,
        flags,
        8,
        dos_time,
        dos_date,
        crc,
        comp_size,
        uncomp_size,
        fn_len,
        0,
        0,
        0,
        0,
        0x81A40000,
        0
    ) + fn_bytes

    cd_offset = len(local_header) + len(encrypted_stream)
    cd_size = len(central_dir)

    eocd = struct.pack(
        "<4sHHHHIIH",
        b"PK\x05\x06",
        0,
        0,
        1,
        1,
        cd_size,
        cd_offset,
        0
    )

    with open(zip_path, "wb") as f:
        f.write(local_header)
        f.write(encrypted_stream)
        f.write(central_dir)
        f.write(eocd)


def export_encrypted_csv_archive(target_path: str, base_name: str, header_row: list, data_rows: list, password: str = CSV_MASTER_EXPORT_PASSWORD) -> str:
    """
    Converts tabular data to UTF-8-BOM CSV and exports it as a password-protected ZIP archive.
    Returns the actual written file path.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    if header_row:
        writer.writerow(header_row)
    writer.writerows(data_rows)

    # Encode with UTF-8 BOM so Excel opens Hindi/Special chars cleanly upon extraction
    csv_bytes = output.getvalue().encode("utf-8-sig")

    internal_csv_name = f"{base_name}.csv" if not base_name.endswith(".csv") else base_name

    # Determine archive path
    if target_path.lower().endswith(".zip"):
        zip_path = target_path
    elif target_path.lower().endswith(".csv"):
        zip_path = target_path[:-4] + ".zip"
    else:
        zip_path = target_path + ".zip"

    create_password_protected_zip(zip_path, internal_csv_name, csv_bytes, password=password)
    return zip_path

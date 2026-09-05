"""
Compile .po files to binary .mo files using pure Python.
Compatible with standard GNU gettext format used by Django.
"""

import os
import struct
from pathlib import Path


def generate_mo(po_path: str, mo_path: str):
    """
    Parse a PO file and generate a binary MO file.
    """
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    messages = {}
    msgid = None
    msgstr = None
    in_msgid = False
    in_msgstr = False

    def unescape(s: str) -> str:
        s = s.strip()
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        s = s.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
        return s

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('msgid '):
            if msgid is not None and msgstr is not None:
                messages[msgid] = msgstr
            msgid = unescape(line[6:])
            msgstr = None
            in_msgid = True
            in_msgstr = False
        elif line.startswith('msgstr '):
            msgstr = unescape(line[7:])
            in_msgid = False
            in_msgstr = True
        elif line.startswith('"') and line.endswith('"'):
            if in_msgid:
                msgid += unescape(line)
            elif in_msgstr:
                msgstr += unescape(line)

    if msgid is not None and msgstr is not None:
        messages[msgid] = msgstr

    keys = sorted(messages.keys())
    num_strings = len(keys)
    orig_table_offset = 28
    trans_table_offset = 28 + num_strings * 8

    orig_table = []
    trans_table = []
    orig_data = bytearray()
    trans_data = bytearray()

    current_orig_offset = trans_table_offset + num_strings * 8

    for k in keys:
        k_bytes = k.encode('utf-8') + b'\x00'
        orig_table.append((len(k.encode('utf-8')), current_orig_offset))
        orig_data.extend(k_bytes)
        current_orig_offset += len(k_bytes)

    current_trans_offset = current_orig_offset

    for k in keys:
        v = messages[k]
        v_bytes = v.encode('utf-8') + b'\x00'
        trans_table.append((len(v.encode('utf-8')), current_trans_offset))
        trans_data.extend(v_bytes)
        current_trans_offset += len(v_bytes)

    header = struct.pack(
        '<Iiiiiii',
        0x950412de,  # Magic
        0,           # Format revision
        num_strings, # Number of strings
        orig_table_offset,
        trans_table_offset,
        0,           # Hashing table size
        0            # Hashing table offset
    )

    table_data = bytearray()
    for l, o in orig_table:
        table_data.extend(struct.pack('<ii', l, o))
    for l, o in trans_table:
        table_data.extend(struct.pack('<ii', l, o))

    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, 'wb') as f:
        f.write(header)
        f.write(table_data)
        f.write(orig_data)
        f.write(trans_data)

    print(f"Compiled {po_path} -> {mo_path} ({num_strings} messages)")


def compile_all():
    base_dir = Path(__file__).resolve().parent
    locale_dir = base_dir / 'locale'
    po_files = list(locale_dir.glob('**/django.po'))
    if not po_files:
        print("No .po files found under", locale_dir)
        return
    for po_file in po_files:
        mo_file = po_file.with_suffix('.mo')
        generate_mo(str(po_file), str(mo_file))


if __name__ == '__main__':
    compile_all()

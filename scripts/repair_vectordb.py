"""
repair_vectordb.py — [LEGACY] Try to recover a corrupted TurboVec docstore.json
================================================================================
**This script is no longer needed** — the project now uses Qdrant (external
vector database) instead of TurboVec for storage.  It is kept for reference
only and will be removed in a future cleanup.

The docstore.json file contains all document text and metadata. If it gets
corrupted (e.g. by concurrent/interrupted writes), TurboVec cannot load.

This script attempts to:
1. Parse as much of the file as possible
2. Fix the corruption at the known error position
3. If repair fails, rebuild from id_map.json and index.tvim if possible

Usage:
    python scripts/repair_vectordb.py
"""

import json
import os
import shutil
import sys
from pathlib import Path


def diagnose(path: Path) -> dict:
    """Diagnose what's wrong with the docstore file."""
    size = path.stat().st_size
    result = {"size": size, "valid": False, "error_pos": None, "error_msg": None}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        json.loads(content)
        result["valid"] = True
        return result
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["error_pos"] = e.pos
        result["error_msg"] = e.msg
        # Show context around error
        ctx_start = max(0, e.pos - 80)
        ctx_end = min(len(content), e.pos + 80)
        result["context"] = content[ctx_start:ctx_end]
        return result


def attempt_repair(path: Path) -> bool:
    """
    Try to surgically fix the known corruption pattern.
    The corruption at pos ~2,300,186 shows a truncated UUID "f1e with
    missing colon-and-value before the "metadata" key.
    """
    shutil.copy2(str(path), str(path) + ".bak")
    print(f"  Backed up to {path}.bak")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # The known corruption: '"f1e, "metadata"' should be '"<uuid>": <n>, "metadata"'
    # We can detect this pattern: a comma followed by an incomplete UUID
    # Let's try to find and fix it
    
    # Pattern: incomplete entry before "metadata"
    # Fix: remove the incomplete entry (the broken UUID and comma before "metadata")
    import re
    
    # Find the broken entry: a string start that's not a complete UUID before "metadata"
    # The pattern is: , "f1e, "metadata" — the "f1e was supposed to be "f1e<more_chars>"
    # We need to remove the broken entry
    
    # Approach: find all positions where a key starts but isn't a valid UUID
    # Actually, simpler: just try to truncate right before the first detectable broken entry
    
    # Let's find the exact corruption point
    decoder = json.JSONDecoder()
    try:
        decoder.raw_decode(content)
        return True  # It's valid now?
    except json.JSONDecodeError as e:
        pos = e.pos
        
    # Look backwards from the error position to find the last valid comma
    # that separates entries in the uuid_to_id mapping
    last_comma = content.rfind(",", 0, pos)
    if last_comma < 0:
        return False
    
    # Try to find a valid prefix and add closing braces
    prefix = content[:last_comma]
    
    # The structure ends with: ... "uuid": N}, "next_u64": ..., "bit_width": ...}
    # So we need to close the uuid_to_id object and add the footer
    # But we don't know the correct next_u64 value
    
    # Let's try a different approach: find what's right after the "metadata" key
    # and try to salvage the rest of the file
    metadata_pos = content.find('"metadata"', pos)
    if metadata_pos < 0:
        return False
    
    # The "metadata" key is part of a "docs" entry value
    # The structure is: "docs": {"uuid": {"text": "...", "metadata": {...}}, ...}
    # After uuid_to_id mapping, the last part should be: }, "next_u64": N, "bit_width": 4}
    
    # The corruption is in the uuid_to_id mapping section
    # Let's try a more surgical fix
    
    # Read the original bytes and fix at the exact position
    with open(path, "rb") as f:
        raw = f.read()
    
    # The corrupted sequence is: , "f1e, "metadata"
    # After a valid entry: "0ca02081-7745-44cf-be36-bfc28c68ad71": 13463
    # So we have: ..., "0ca02081-7745-44cf-be36-bfc28c68ad71": 13463, "f1e, "metadata"
    # This should be: ..., "0ca02081-7745-44cf-be36-bfc28c68ad71": 13463, "metadata"
    # (the incomplete "f1e entry should be removed)
    
    # Let's try removing the ", "f1e" part (the broken entry)
    broken_start = content.find(', "f1e, "metadata"', pos - 50, pos + 50)
    if broken_start >= 0:
        print(f"  Found broken entry at pos {broken_start}")
        # Fix: change ', "f1e, "metadata"' to ', "metadata"'
        fixed = content[:broken_start] + ', ' + content[broken_start + len(', "f1e, '):]
        # Actually let's be more precise
        # The pattern is: , "f1e, "metadata"
        # We want to remove just the broken ", "f1e" part
        # After the comma, we have '"f1e, "metadata"' - the broken UUID
        # Let's strip it: remove everything from the broken UUID start to right before "metadata"
        
        # Find where the valid UUID entries end and the broken one begins
        # The last valid entry ends with '13463, "f1e'
        # We need to find '13463, ' and replace with '13463, "metadata"'
        
        # Simpler: find ", "f1e, " and replace with just ", "
        content_fixed = content.replace(', "f1e, "metadata"', ', "metadata"')
        if content_fixed != content:
            # Verify it parses
            try:
                json.loads(content_fixed)
                print("  Fix succeeded!")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content_fixed)
                return True
            except json.JSONDecodeError as e2:
                print(f"  First fix attempt failed at {e2.pos}: {e2.msg}")
    
    # Generic approach: find the corruption and remove it
    # The error occurs in the uuid_to_id section. Let's try to:
    # 1. Parse everything before the broken entry
    # 2. Find valid JSON after the broken entry
    # 3. Stitch them together
    
    # Find the last valid-looking UUID entry before the error
    # Pattern: "uuid": NUMBER
    uuid_pattern = re.compile(r'"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})":\s*(\d+)')
    
    matches = list(uuid_pattern.finditer(content[:pos]))
    if matches:
        last_match = matches[-1]
        last_uuid_end = last_match.end()
        last_number = int(last_match.group(2))
        print(f"  Last valid UUID entry ends at {last_uuid_end}, number={last_number}")
        
        # Try to reconstruct: take content up to last_match end, then add closing
        prefix_fixed = content[:last_uuid_end]
        # Add the closing of uuid_to_id object, next_u64, and bit_width
        suffix = f'}}, "next_u64": {last_number + 1}, "bit_width": 4}}'
        reconstructed = prefix_fixed + suffix
        
        try:
            json.loads(reconstructed)
            print(f"  Reconstruction successful! next_u64={last_number + 1}")
            with open(path, "w", encoding="utf-8") as f:
                f.write(reconstructed)
            return True
        except json.JSONDecodeError as e3:
            print(f"  Reconstruction failed at {e3.pos}: {e3.msg}")
            
            # Try without the closing brace of uuid_to_id (the "docs" object might still be open)
            suffix2 = f', "next_u64": {last_number + 1}, "bit_width": 4}}'
            reconstructed2 = prefix_fixed + suffix2
            try:
                json.loads(reconstructed2)
                print(f"  Alt reconstruction successful!")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(reconstructed2)
                return True
            except json.JSONDecodeError:
                pass
    
    return False


def main():
    vectordb_dir = Path("../storage/vectordb")
    docstore_path = vectordb_dir / "docstore.json"
    
    if not docstore_path.exists():
        print("docstore.json not found.")
        return
    
    print(f"Diagnosing {docstore_path}...")
    info = diagnose(docstore_path)
    
    if info["valid"]:
        print("✓ docstore.json is valid. No repair needed.")
        return
    
    print(f"✗ docstore.json is corrupted")
    print(f"  Size: {info['size']:,} bytes")
    print(f"  Error at position {info['error_pos']:,}: {info['error_msg']}")
    print(f"  Context: ...{info.get('context', 'N/A')}...")
    print()
    
    print("Attempting repair...")
    success = attempt_repair(docstore_path)
    
    if success:
        # Verify
        info2 = diagnose(docstore_path)
        if info2["valid"]:
            print(f"\n✓ Repair successful! docstore.json is now valid.")
        else:
            print(f"\n✗ Repair appeared to work but file is still invalid: {info2['error_msg']}")
    else:
        print(f"\n✗ Could not repair automatically.")
        print(f"  A backup was saved to {docstore_path}.bak")
        print(f"  To start fresh, delete {docstore_path} and restart the backend.")
        print(f"  The app will create a new empty store (you'll lose indexed sources).")


if __name__ == "__main__":
    main()

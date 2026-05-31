#!/usr/bin/env python3
"""
3/2/1 Compressor & Decompressor
For the Natural Law Union lattice
Author: Grok (with ROOT0)
"""

def compress_321(text: str, max_width: int = 3) -> str:
    """
    Compress any text/idea into 3/2/1 form.
    3 = Wide (broad idea)
    2 = Narrowed (refined)
    1 = Singular (core point)
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        return "1: (empty seed)"

    # Simple compression: first broad, then middle refinement, then core
    wide = lines[0] if len(lines) > 0 else ""
    narrowed = " | ".join(lines[1:3]) if len(lines) > 1 else ""
    singular = lines[-1] if len(lines) > 0 else ""

    return f"""3 (Wide): {wide}
2 (Narrowed): {narrowed}
1 (Singular): {singular}"""


def decompress_321(compressed: str) -> str:
    """
    Expand 3/2/1 back into explanatory form.
    """
    lines = compressed.strip().split('\n')
    wide = lines[0].replace("3 (Wide):", "").strip() if len(lines) > 0 else ""
    narrowed = lines[1].replace("2 (Narrowed):", "").strip() if len(lines) > 1 else ""
    singular = lines[2].replace("1 (Singular):", "").strip() if len(lines) > 2 else ""

    return f"""### 3/2/1 Decompression

**3 (Wide Attention)**  
{wide}

**2 (Narrowed Refinement)**  
{narrowed}

**1 (Singular Output)**  
{singular}

This follows the natural law: wide exploration → stacked refinement → unified action.
The seed (1) carries latent potential that unfolds through 2 into 3."""


# Simple CLI
if __name__ == "__main__":
    print("=== 3/2/1 Compressor / Decompressor ===\n")
    mode = input("Mode (compress/decompress): ").strip().lower()
    
    if mode == "compress":
        print("Paste text to compress (end with blank line):")
        text = []
        while True:
            line = input()
            if line == "":
                break
            text.append(line)
        result = compress_321("\n".join(text))
        print("\nCompressed 3/2/1:\n")
        print(result)
        
    elif mode == "decompress":
        print("Paste compressed 3/2/1 block:")
        compressed = []
        while True:
            line = input()
            if line == "":
                break
            compressed.append(line)
        result = decompress_321("\n".join(compressed))
        print("\nDecompressed:\n")
        print(result)
    else:
        print("Use 'compress' or 'decompress'")

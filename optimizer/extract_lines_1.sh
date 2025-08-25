#!/bin/bash

# ----------------------------
# 1. Configuration
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="${SCRIPT_DIR}/out1.txt"     # Relative path to input file
OUTPUT_FILE="${SCRIPT_DIR}/gp.txt"      # Relative path to output file

# ----------------------------
# 2. Input Validation
# ----------------------------
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE not found!" >&2
    exit 1
fi

# ----------------------------
# 3. Data Processing
# ----------------------------
# Process with awk to extract relevant lines
awk '
  /metrics/ && /True/ {
    if (getline nextline && getline nextnextline && getline nextnextnextline) {
      if (nextnextnextline ~ /reward/) {
        print $0
        print nextline
        print nextnextline
        print nextnextnextline
      }
    }
  }
' "$INPUT_FILE" > "$OUTPUT_FILE"

# ----------------------------
# 4. Post-processing
# ----------------------------
if [ -s "$OUTPUT_FILE" ]; then
    # Remove 'True' occurrences
    sed -i 's/True//g' "$OUTPUT_FILE"
else
    echo "Warning: No matching patterns found in input file" >&2
fi

# ----------------------------
# 5. Final Cleanup (if needed)
# ----------------------------
# Uncomment these if you need them:
# sed -i "s/.*nA1/nA1/" "$OUTPUT_FILE"
# sed -i "s/.*metrics/metrics/" "$OUTPUT_FILE"

exit 0
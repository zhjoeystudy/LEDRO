#!/bin/bash

# ----------------------------
# 1. Configuration
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="${SCRIPT_DIR}/out11.txt"
OUTPUT_FILE="${SCRIPT_DIR}/gp11.txt"
TEMP_FILE="${SCRIPT_DIR}/temp_extracted_lines11.txt"
TOP_REWARD_FILE="${SCRIPT_DIR}/top_reward11.txt"
TOP_5_FILE="${SCRIPT_DIR}/top_5_rewards11.txt"

# ----------------------------
# 2. Input Validation
# ----------------------------
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE not found!" >&2
    exit 1
fi

# ----------------------------
# 3. Initial Processing
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

# Clean up True values if output was created
[ -f "$OUTPUT_FILE" ] && sed -i 's/True//g' "$OUTPUT_FILE"

# ----------------------------
# 4. Reward Extraction
# ----------------------------
# Get top reward
grep "reward" "$OUTPUT_FILE" | sed 's/reward //' | sort -nr | head -1 > "$TOP_REWARD_FILE"

# Extract lines with key patterns
awk '/metrics/ || /nA/ || /MM/ || /reward/' "$OUTPUT_FILE" > "$TEMP_FILE"

# Get top 5 rewards
grep "reward" "$TEMP_FILE" | sed 's/reward //' | sort -nr | head -5 > "$TOP_5_FILE"

# ----------------------------
# 5. Data Block Processing
# ----------------------------
declare -A rewards_map
while read -r reward; do
    rewards_map["$reward"]=1
done < "$TOP_5_FILE"

declare -a data_blocks
metrics_line=""
na_line=""
gm_line=""

while read -r line; do
    if [[ "$line" =~ metrics ]]; then
        metrics_line="$line"
    elif [[ "$line" =~ nA ]]; then
        na_line="$line"
    elif [[ "$line" =~ MM ]]; then
        gm_line="$line"
    elif [[ "$line" =~ reward ]]; then
        reward_value=$(echo "$line" | sed 's/reward //')
        if [[ ${rewards_map["$reward_value"]} ]]; then
            data_blocks+=("$reward_value $metrics_line\n$na_line\n$gm_line\n$line")
        fi
    fi
done < "$OUTPUT_FILE"

# ----------------------------
# 6. Final Output Generation
# ----------------------------
{
    IFS=$'\n' sorted_blocks=($(sort -r -n <<<"${data_blocks[*]}"))
    for block in "${sorted_blocks[@]}"; do
        echo -e "${block#* }"
    done
} > "$TOP_5_FILE"

# ----------------------------
# 7. Cleanup (optional)
# ----------------------------
# Uncomment to remove temporary file
# rm -f "$TEMP_FILE"

exit 0
#!/bin/bash

# ----------------------------
# 1. Configuration and Setup
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT_FILE="${SCRIPT_DIR}/out12.txt"
OUTPUT_FILE="${SCRIPT_DIR}/gp12.txt"
TEMP_EXTRACTED_FILE="${SCRIPT_DIR}/temp_extracted_lines12.txt"
TOP_REWARD_FILE="${SCRIPT_DIR}/top_reward12.txt"
TOP_5_REWARDS_FILE="${SCRIPT_DIR}/top_5_rewards12.txt"

# ----------------------------
# 2. Input Validation
# ----------------------------
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: Input file $INPUT_FILE not found!" >&2
    exit 1
fi

# ----------------------------
# 3. Initial Data Extraction
# ----------------------------
# Extract metrics blocks with awk
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

# Clean True values if output exists
[[ -f "$OUTPUT_FILE" ]] && sed -i 's/True//g' "$OUTPUT_FILE"

# ----------------------------
# 4. Reward Processing
# ----------------------------
# Extract and sort top reward
if grep -q "reward" "$OUTPUT_FILE"; then
    grep "reward" "$OUTPUT_FILE" | sed 's/reward //' | sort -nr | head -1 > "$TOP_REWARD_FILE"
else
    echo "Warning: No reward lines found in output" >&2
fi

# Extract relevant lines for top 5 processing
awk '/metrics/ || /nA/ || /MM/ || /reward/' "$OUTPUT_FILE" > "$TEMP_EXTRACTED_FILE"

# Get top 5 reward values
grep "reward" "$TEMP_EXTRACTED_FILE" | sed 's/reward //' | sort -nr | head -5 > "$TOP_5_REWARDS_FILE"

# ----------------------------
# 5. Data Block Assembly
# ----------------------------
declare -A rewards_map
while IFS= read -r reward; do
    rewards_map["$reward"]=1
done < "$TOP_5_REWARDS_FILE"

declare -a data_blocks
metrics_line=""
na_line=""
gm_line=""

while IFS= read -r line; do
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
# Sort blocks by reward value and output
{
    IFS=$'\n' sorted_blocks=($(sort -r -n <<<"${data_blocks[*]}"))
    for block in "${sorted_blocks[@]}"; do
        echo -e "${block#* }"
    done
} > "$TOP_5_REWARDS_FILE"

# Cleanup (optional)
# rm -f "$TEMP_EXTRACTED_FILE"

exit 0
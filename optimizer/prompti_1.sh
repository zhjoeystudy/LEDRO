#!/bin/bash

# ----------------------------
# 1. Configuration
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Input files
INPUT_FILE="${SCRIPT_DIR}/gp.txt"
TEMPLATE_FILE="${SCRIPT_DIR}/../LLM/sample-qa-data_i_basic.json"

# Output files
OUTPUT_FILE="${SCRIPT_DIR}/outputgp.txt"
OUTPUT_FILE1="${SCRIPT_DIR}/outputgp3.txt"
TARGET_FILE="${SCRIPT_DIR}/../LLM/sample-qa-data_i.json"
HISTORY_FILE="${SCRIPT_DIR}/top_5_history.txt"

# Temporary files
TEMP_EXTRACTED="${SCRIPT_DIR}/temp_extracted_lines.txt"
TOP_5_REWARDS="${SCRIPT_DIR}/top_5_rewards.txt"
TOP_5_REWARDS1="${SCRIPT_DIR}/top_5_rewards1.txt"
TOP_REWARD="${SCRIPT_DIR}/top_reward.txt"
TOP_REWARD1="${SCRIPT_DIR}/top_reward1.txt"

# ----------------------------
# 2. Input Validation
# ----------------------------
validate_files() {
    local missing_files=()
    
    [[ ! -f "$INPUT_FILE" ]] && missing_files+=("$INPUT_FILE")
    [[ ! -f "$TEMPLATE_FILE" ]] && missing_files+=("$TEMPLATE_FILE")
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        echo "Error: Missing required files:" >&2
        printf '  %s\n' "${missing_files[@]}" >&2
        exit 1
    fi
}

validate_files

# ----------------------------
# 3. Data Extraction
# ----------------------------
extract_relevant_lines() {
    awk '/metrics/ || /nA/ || /MM/ || /reward/' "$INPUT_FILE" > "$TEMP_EXTRACTED"
}

extract_rewards() {
    local input="$1"
    local output="$2"
    local count="$3"
    
    grep "reward" "$input" | \
    sed 's/reward //' | \
    sort -nr | \
    head -"$count" > "$output"
}

extract_relevant_lines
extract_rewards "$TEMP_EXTRACTED" "$TOP_5_REWARDS" 5
extract_rewards "$TEMP_EXTRACTED" "$TOP_REWARD" 1

# ----------------------------
# 4. Data Processing
# ----------------------------
process_data_blocks() {
    local input="$1"
    local map_file="$2"
    local output="$3"
    
    declare -A rewards_map
    while IFS= read -r reward; do
        rewards_map["$reward"]=1
    done < "$map_file"

    declare -a data_blocks
    local metrics_line="" na_line="" gm_line=""

    while IFS= read -r line; do
        if [[ "$line" =~ metrics ]]; then
            metrics_line="$line"
        elif [[ "$line" =~ nA ]]; then
            na_line="$line"
        elif [[ "$line" =~ MM ]]; then
            gm_line="$line"
        elif [[ "$line" =~ reward ]]; then
            reward_value=$(echo "$line" | sed 's/reward //')
            [[ ${rewards_map["$reward_value"]} ]] && \
                data_blocks+=("$reward_value $metrics_line\n$na_line\n$gm_line\n$line")
        fi
    done < "$input"

    # Sort and output blocks
    {
        IFS=$'\n' sorted_blocks=($(sort -r -n <<<"${data_blocks[*]}"))
        for block in "${sorted_blocks[@]}"; do
            echo -e "${block#* }"
        done
    } > "$output"
    
    # Limit to top 20 lines
    head -n 20 "$output" > "${output}.tmp" && mv "${output}.tmp" "$output"
}

process_data_blocks "$TEMP_EXTRACTED" "$TOP_5_REWARDS" "$TOP_5_REWARDS1"
process_data_blocks "$TEMP_EXTRACTED" "$TOP_REWARD" "$TOP_REWARD1"

# ----------------------------
# 5. JSON Generation
# ----------------------------
generate_json_content() {
    local input="$1"
    local output="$2"
    local json_content=""
    
    while IFS= read -r line1 && 
          IFS= read -r line2 && 
          IFS= read -r line3 && 
          IFS= read -r line4; do
        json_content+="${line1} with ${line2} and transistor regions ${line3} and ${line4}. Then, "
    done < "$input"
    
    # Remove trailing "Then, "
    echo "${json_content%. Then, }" > "$output"
}

generate_json_content "$TOP_5_REWARDS1" "$OUTPUT_FILE1"

# ----------------------------
# 6. Template Processing
# ----------------------------
process_template() {
    local content=$(<"$OUTPUT_FILE1")
    local escaped_content=$(sed 's/[&/\]/\\&/g' <<< "$content")
    
    cp "$TEMPLATE_FILE" "$TARGET_FILE"
    sed -i "s|REPLACEMENT|${escaped_content}|g" "$TARGET_FILE"
}

process_template

# ----------------------------
# 7. Cleanup
# ----------------------------
cleanup() {
    local files_to_remove=(
        "$TEMP_EXTRACTED"
        "$TOP_5_REWARDS"
    )
    
    for file in "${files_to_remove[@]}"; do
        [[ -f "$file" ]] && rm "$file"
    done
}

cleanup

exit 0
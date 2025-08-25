#!/bin/bash

# ----------------------------
# 1. Configuration
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Input files
INPUT_FILE="${SCRIPT_DIR}/gp.txt"
HISTORY_FILE="${SCRIPT_DIR}/top_5_history.txt"
TEMPLATE_1="${SCRIPT_DIR}/../LLM/sample-qa-data_l_basic_1.json"
TEMPLATE_2="${SCRIPT_DIR}/../LLM/sample-qa-data_l_basic_2.json"

# Output files
OUTPUT_FILE="${SCRIPT_DIR}/outputgp2.txt"
OUTPUT_FILE1="${SCRIPT_DIR}/outputgp3.txt"
TARGET_FILE="${SCRIPT_DIR}/../LLM/sample-qa-data_l.json"

# Temporary files
TEMP_EXTRACTED="${SCRIPT_DIR}/temp_extracted_lines.txt"
TOP_5_REWARDS="${SCRIPT_DIR}/top_5_rewards.txt"
TOP_5_REWARDS1="${SCRIPT_DIR}/top_5_rewards1.txt"
TOP_REWARD="${SCRIPT_DIR}/top_reward.txt"
TOP_REWARD1="${SCRIPT_DIR}/top_reward1.txt"
COMBINED_TEMP="${SCRIPT_DIR}/combined_temp.txt"

# ----------------------------
# 2. Input Validation
# ----------------------------
validate_files() {
    local missing_files=()
    
    [[ ! -f "$INPUT_FILE" ]] && missing_files+=("$INPUT_FILE")
    [[ ! -f "$TEMPLATE_1" ]] && missing_files+=("$TEMPLATE_1")
    [[ ! -f "$TEMPLATE_2" ]] && missing_files+=("$TEMPLATE_2")
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        echo "Error: Missing required files:" >&2
        printf '  %s\n' "${missing_files[@]}" >&2
        exit 1
    fi
}

validate_files

# ----------------------------
# 3. Data Processing Functions
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

process_rewards() {
    # Extract relevant lines
    awk '/metrics/ || /nA/ || /MM/ || /reward/' "$INPUT_FILE" > "$TEMP_EXTRACTED"
    
    # Get top 5 rewards
    grep "reward" "$TEMP_EXTRACTED" | sed 's/reward //' | sort -nr | head -5 > "$TOP_5_REWARDS"
    
    # Process data blocks
    declare -A rewards_map
    while IFS= read -r reward; do
        rewards_map["$reward"]=1
    done < "$TOP_5_REWARDS"

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
    done < "$TEMP_EXTRACTED"

    # Sort and output blocks
    {
        IFS=$'\n' sorted_blocks=($(sort -r -n <<<"${data_blocks[*]}"))
        for block in "${sorted_blocks[@]}"; do
            echo -e "${block#* }"
        done
    } > "$TOP_5_REWARDS1"
    
    # Limit to top 20 lines
    head -n 20 "$TOP_5_REWARDS1" > "${TOP_5_REWARDS1}.tmp" && mv "${TOP_5_REWARDS1}.tmp" "$TOP_5_REWARDS1"
}

find_max_reward_block() {
    cat "$TOP_5_REWARDS1" "$TOP_REWARD1" > "$COMBINED_TEMP"
    
    local max_reward=""
    local max_block=""
    local prev1="" prev2="" prev3=""
    
    while IFS= read -r line; do
        if [[ $line == metrics* ]]; then
            prev1="$line"
        elif [[ $line == nA* ]]; then
            prev2="$line"
        elif [[ $line == MM* ]]; then
            prev3="$line"
        elif [[ $line == reward* ]]; then
            reward_value=$(echo "$line" | awk '{print $2}')
            if [[ -z $max_reward ]] || (( $(echo "$reward_value > $max_reward" | bc -l) )); then
                max_reward=$reward_value
                max_block="${prev1}"$'\n'"${prev2}"$'\n'"${prev3}"$'\n'"$line"
            fi
        fi
    done < "$COMBINED_TEMP"
    
    echo "$max_block" > "$TOP_REWARD1"
    echo "$max_reward" > "$TOP_REWARD"
}

# ----------------------------
# 4. Main Processing
# ----------------------------
# Initial JSON generation
generate_json_content "$INPUT_FILE" "$OUTPUT_FILE"

# Process rewards data
process_rewards

# Generate secondary JSON content
generate_json_content "$TOP_5_REWARDS1" "$OUTPUT_FILE1"

# Find the block with maximum reward
find_max_reward_block

# Generate JSON for top reward
generate_json_content "$TOP_REWARD1" "${SCRIPT_DIR}/top_reward_json.txt"

# ----------------------------
# 5. Template Processing
# ----------------------------
process_template() {
    local line_count=$(wc -l < "$INPUT_FILE")
    local replacement=""
    local replace_number=""
    
    if [[ "$line_count" -eq 0 ]]; then
        replace_number="0"
        replacement=""
        cp "$TEMPLATE_1" "$TARGET_FILE"
        sed -i "s/REPLACENUMBER/$replace_number/g" "$TARGET_FILE"
    elif [[ "$line_count" -lt 20 ]]; then
        replace_number="$((line_count / 4))"
        replacement=$(sed 's/[&/\]/\\&/g' < "$OUTPUT_FILE")
        cp "$TEMPLATE_1" "$TARGET_FILE"
        sed -i "s/REPLACENUMBER/only $replace_number/g" "$TARGET_FILE"
        sed -i "s/REPLACEMENT/These are the points with their reward: $replacement/g" "$TARGET_FILE"
    else
        replacement=$(sed 's/[&/\]/\\&/g' < "$OUTPUT_FILE1")
        cp "$TEMPLATE_2" "$TARGET_FILE"
        sed -i "s/REPLACEMENT/$replacement/g" "$TARGET_FILE"
    fi
    
    # Process history statement
    local line_count1=$(wc -l < "$HISTORY_FILE")
    local max_value=$(sort -n "$HISTORY_FILE" | tail -n 1 2>/dev/null || echo "")
    
    if [[ "$line_count1" -eq 0 ]]; then
        sed -i "s/REWARDSTATEMENT. //g" "$TARGET_FILE"
    else
        local reward_statement="As a reminder, the previous range you'd sent me before this one had given a best reward of $max_value. So, please consider that as well before giving your answer"
        sed -i "s/REWARDSTATEMENT/$reward_statement/g" "$TARGET_FILE"
    fi
    
    # Insert top reward
    local json_output3=$(sed 's/[&/\]/\\&/g' < "${SCRIPT_DIR}/top_reward_json.txt")
    sed -i "s/TOPREWARD/$json_output3/g" "$TARGET_FILE"
}

process_template

# ----------------------------
# 6. Cleanup
# ----------------------------
cleanup() {
    local files_to_remove=(
        "$TEMP_EXTRACTED"
        "$TOP_5_REWARDS"
        "$COMBINED_TEMP"
        "${SCRIPT_DIR}/top_reward_json.txt"
    )
    
    for file in "${files_to_remove[@]}"; do
        [[ -f "$file" ]] && rm "$file"
    done
}

cleanup

exit 0
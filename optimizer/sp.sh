#!/bin/bash

# ----------------------------
# 1. Configuration
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Input/Output files
INPUT_FILE="${SCRIPT_DIR}/../LLM/qa_output_amp_l.txt"
OUTPUT_FILE="${SCRIPT_DIR}/qa_output_amp_l.txt"
OUTPUT_FILE1="${SCRIPT_DIR}/qa_output_amp_l1.txt"

# YAML template files
YAML_BASIC="${SCRIPT_DIR}/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode_basic.yaml"
YAML_OUTPUT="${SCRIPT_DIR}/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"

# Python script
PYTHON_SCRIPT="${SCRIPT_DIR}/transform_file.py"

# ----------------------------
# 2. Input Validation
# ----------------------------
validate_files() {
    local missing_files=()
    
    [[ ! -f "$INPUT_FILE" ]] && missing_files+=("Input file: $INPUT_FILE")
    [[ ! -f "$YAML_BASIC" ]] && missing_files+=("YAML template: $YAML_BASIC")
    [[ ! -f "$PYTHON_SCRIPT" ]] && missing_files+=("Python script: $PYTHON_SCRIPT")
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        echo "Error: Missing required files:" >&2
        printf '  %s\n' "${missing_files[@]}" >&2
        exit 1
    fi
}

validate_files

# ----------------------------
# 3. Data Processing
# ----------------------------
process_parameters() {
    # Extract relevant parameters
    grep -E '^(nA|nB|vbias|cc)' "$INPUT_FILE" > "$OUTPUT_FILE"
    
    # Transform file using Python
    if ! python "$PYTHON_SCRIPT" "$OUTPUT_FILE" "$OUTPUT_FILE1"; then
        echo "Error: Python transformation failed" >&2
        exit 1
    fi
    
    # Add indentation to each line
    local temp_file=$(mktemp)
    awk '{print "  " $0}' "$OUTPUT_FILE1" > "$temp_file"
    mv "$temp_file" "$OUTPUT_FILE"
}

generate_yaml() {
    local temp_file=$(mktemp)
    local found=0
    
    # Process YAML template
    while IFS= read -r line; do
        echo "$line" >> "$temp_file"
        
        # Insert parameters after 'params:' line
        if [[ "$line" == params:* ]]; then
            found=1
            cat "$OUTPUT_FILE" >> "$temp_file"
        fi
    done < "$YAML_BASIC"
    
    # If 'params:' not found, append at end
    if [[ "$found" -eq 0 ]]; then
        cat "$OUTPUT_FILE" >> "$temp_file"
    fi
    
    # Atomic replacement of output file
    mv "$temp_file" "$YAML_OUTPUT"
}

# ----------------------------
# 4. Main Execution
# ----------------------------
main() {
    process_parameters
    generate_yaml
    
    # Cleanup (if needed)
    # rm -f "$OUTPUT_FILE1"
    
    echo "Successfully generated YAML file at $YAML_OUTPUT"
}

main

exit 0
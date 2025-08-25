#!/bin/bash

# ----------------------------
# 1. Configuration
# ----------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Input files
INPUT_FILE="${SCRIPT_DIR}/../LLM/qa_output_amp_l.txt"
PYTHON_SCRIPT="${SCRIPT_DIR}/transform_file.py"
YAML_TEMPLATE="${SCRIPT_DIR}/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode_basic.yaml"
PYTHON_TEMPLATE="${SCRIPT_DIR}/working_current/sample/random_sample_turbo_1.py"

# Output files
OUTPUT_FILE="${SCRIPT_DIR}/qa_output_amp_l.txt"
OUTPUT_FILE1="${SCRIPT_DIR}/qa_output_amp_l1.txt"
YAML_OUTPUT="${SCRIPT_DIR}/working_current/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"
PYTHON_OUTPUT="${SCRIPT_DIR}/working_current/sample/random_sample_turbo_1.py"

# Temporary files
TEMP_FILE=$(mktemp)
TEMP_FILE1=$(mktemp)
TEMP_FILE2=$(mktemp)

# ----------------------------
# 2. Input Validation
# ----------------------------
validate_files() {
    local missing_files=()
    
    [[ ! -f "$INPUT_FILE" ]] && missing_files+=("Input file: $INPUT_FILE")
    [[ ! -f "$PYTHON_SCRIPT" ]] && missing_files+=("Python script: $PYTHON_SCRIPT")
    [[ ! -f "$YAML_TEMPLATE" ]] && missing_files+=("YAML template: $YAML_TEMPLATE")
    [[ ! -f "$PYTHON_TEMPLATE" ]] && missing_files+=("Python template: $PYTHON_TEMPLATE")
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        echo "Error: Missing required files:" >&2
        printf '  %s\n' "${missing_files[@]}" >&2
        exit 1
    fi
}

validate_files

# ----------------------------
# 3. Parameter Extraction
# ----------------------------
extract_parameters() {
    echo "Extracting parameters from input file..."
    grep -E '^(nA|nB|vbias|cc)' "$INPUT_FILE" > "$OUTPUT_FILE" || {
        echo "Error: Failed to extract parameters" >&2
        exit 1
    }
}

transform_parameters() {
    echo "Transforming parameters with Python script..."
    if ! python "$PYTHON_SCRIPT" "$OUTPUT_FILE" "$OUTPUT_FILE1"; then
        echo "Error: Python transformation failed" >&2
        exit 1
    fi

    # Add indentation for YAML
    awk '{print "  " $0}' "$OUTPUT_FILE1" > "$TEMP_FILE"
}

# ----------------------------
# 4. YAML Generation
# ----------------------------
generate_yaml() {
    echo "Generating YAML configuration..."
    local found=0
    
    while IFS= read -r line; do
        echo "$line" >> "$TEMP_FILE1"
        
        if [[ "$line" == params:* ]]; then
            found=1
            cat "$TEMP_FILE" >> "$TEMP_FILE1"
        fi
    done < "$YAML_TEMPLATE"
    
    [[ "$found" -eq 0 ]] && cat "$TEMP_FILE" >> "$TEMP_FILE1"
    
    mv "$TEMP_FILE1" "$YAML_OUTPUT"
}

# ----------------------------
# 5. Python Template Processing
# ----------------------------
process_python_template() {
    echo "Processing Python template..."
    declare -A range_values

    # Read ranges from input file
    while IFS=': ' read -r param range; do
        param=$(echo "$param" | tr -d ' ,')
        range_values[$param]=$(echo "$range" | tr -d '[]')
    done < <(grep -oP '^[^:]+: \[[^]]+\]' "$INPUT_FILE")

    # Process template file
    while IFS= read -r line; do
        for param in "${!range_values[@]}"; do
            pattern="${param}_range = \([^)]*\)"
            if [[ "$line" =~ $pattern ]]; then
                line=$(echo "$line" | sed "s/${pattern}/${param}_range = (${range_values[$param]}/")
            fi
        done
        echo "$line" >> "$TEMP_FILE2"
    done < "$PYTHON_TEMPLATE"

    mv "$TEMP_FILE2" "$PYTHON_OUTPUT"
}

# ----------------------------
# 6. Main Execution
# ----------------------------
main() {
    extract_parameters
    transform_parameters
    generate_yaml
    process_python_template
    
    # Cleanup temporary files
    rm -f "$TEMP_FILE" "$OUTPUT_FILE1"
    
    echo "Successfully generated:"
    echo "  - YAML config: $YAML_OUTPUT"
    echo "  - Python script: $PYTHON_OUTPUT"
}

main

exit 0
#!/bin/bash

# ---------------------------
# 1. Dynamic Directory Setup
# ---------------------------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OPTIMIZER_DIR="$SCRIPT_DIR"
WORKING_DIR="$OPTIMIZER_DIR/working_current"
LLM_DIR="$OPTIMIZER_DIR/LLM"

# ---------------------------
# 2. Environment Configuration
# ---------------------------
export PYTHONPATH="${PYTHONPATH}:$WORKING_DIR"
export BASE_TMP_DIR="$OPTIMIZER_DIR/base_tmp"

# ---------------------------
# 3. Output File Setup
# ---------------------------
OUTPUT_DIR="$OPTIMIZER_DIR/outputfiles"
mkdir -p "$OUTPUT_DIR"
find "$OUTPUT_DIR" -type f -delete

output_base="output_file"
iterations=1

# ---------------------------
# 4. Main Optimization Loop
# ---------------------------
for ((j=1; j<=iterations; j++)); do
    output_file="$OUTPUT_DIR/${output_base}_${j}.txt"
    
    # Reset configuration
    cp "$WORKING_DIR/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode_initial.yaml" \
       "$WORKING_DIR/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"
    
    # Cleanup previous runs
    rm -f "$OPTIMIZER_DIR/out1.txt" "$OPTIMIZER_DIR/out11.txt" "$OPTIMIZER_DIR/out12.txt"
    touch "$OPTIMIZER_DIR/top_5_history.txt"
    
    # Initial TURBO sampling
    python "$WORKING_DIR/sample/random_sample_turbo.py" > "$OPTIMIZER_DIR/dummy.txt"
    cp "$OPTIMIZER_DIR/out1.txt" "$OPTIMIZER_DIR/out1_i.txt"
    
    # Process initial results
    bash "$OPTIMIZER_DIR/extract_lines_1.sh"
    bash "$OPTIMIZER_DIR/prompti_1.sh"
    
    if [ ! -s "$OPTIMIZER_DIR/top_reward1.txt" ]; then
        for i in {1..4}; do
            echo "" >> "$output_file"
        done
    else
        cat "$OPTIMIZER_DIR/top_reward1.txt" >> "$output_file"
    fi
    
    # Check for early termination
    file_content=$(<"$OPTIMIZER_DIR/top_reward.txt")
    if [ "$file_content" == "0" ]; then
        echo "0" > "$OPTIMIZER_DIR/iteration.txt"
        exit 0
    fi
    
    # LLM Processing
    python "$LLM_DIR/llm_qa_csv_ex.py"
    bash "$OPTIMIZER_DIR/sp_1.sh"
    
    # ---------------------------
    # 5. Secondary Optimization Loop
    # ---------------------------
    for (( i=1; i<=10; i++ )); do
        source "$HOME/.bashrc"
        
        # Reset configuration
        cp "$WORKING_DIR/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode_initial.yaml" \
           "$WORKING_DIR/spectre_simulator/spectre/specs_list_read/fully_differential_folded_cascode.yaml"
        
        rm -f "$OPTIMIZER_DIR/out1.txt"
        source "$HOME/.bashrc"
        
        # Secondary TURBO sampling
        python "$WORKING_DIR/sample/random_sample_turbo_1.py" > "$OPTIMIZER_DIR/dummy1.txt"
        
        # Process results
        bash "$OPTIMIZER_DIR/extract_lines_1.sh"
        bash "$OPTIMIZER_DIR/prompti2_1.sh"
        
        if [ ! -s "$OPTIMIZER_DIR/top_reward1.txt" ]; then
            for i in {1..4}; do
                echo "" >> "$output_file"
            done
        else
            cat "$OPTIMIZER_DIR/top_reward1.txt" >> "$output_file"
        fi
        
        # Check for early termination
        file_content=$(<"$OPTIMIZER_DIR/top_reward.txt")
        if [ "$file_content" == "0" ]; then
            echo "$i" > "$OPTIMIZER_DIR/iteration.txt"
            break
        fi
        
        # Additional LLM Processing (if not last iteration)
        if [[ $i -lt 10 ]]; then
            python "$LLM_DIR/llm_qa_csv_ex1.py"
            python "$LLM_DIR/llm_qa_csv_ex2.py"
        fi
        
        bash "$OPTIMIZER_DIR/sp_1.sh"
    done
done

# ---------------------------
# 6. Final Results Processing
# ---------------------------
bash "$OPTIMIZER_DIR/extract_lines_11.sh"
bash "$OPTIMIZER_DIR/extract_lines_12.sh"

# Combine results
file1="$output_file"
file2="$OPTIMIZER_DIR/top_reward11.txt"
file3="$OPTIMIZER_DIR/top_reward12.txt"
new_file="$OPTIMIZER_DIR/final_results.txt"

line4_file1=$(sed -n '4p' "$file1")
line44_file1=$(sed -n '44p' "$file1")
all_lines_file2=$(cat "$file2")
all_lines_file3=$(cat "$file3")

string2="reward "
line4_file11=$(echo "$line4_file1" | sed "s/$string2//g")
line44_file11=$(echo "$line44_file1" | sed "s/$string2//g")

{
    echo "$line4_file11 $all_lines_file2 $all_lines_file3 $line44_file11"
} > "$new_file"

# Cleanup
rsync -a --delete "$OPTIMIZER_DIR/empty_dir/" "$BASE_TMP_DIR/" &
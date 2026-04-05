#!/usr/bin/env bash
# Script 88: Cube-and-Conquer for sr=60 at any N
#
# Splits the CNF into subcases by assuming values for the first k free variables,
# then solves each subcase in parallel with Kissat.
#
# Usage: ./88_cube_and_conquer.sh <cnf_file> <n_cube_vars> <timeout_per_cube>
#
# Example: ./88_cube_and_conquer.sh sr60_N19.cnf 8 600
# This creates 256 cubes (2^8), each with 8 assumed variables, and solves in parallel.

set -euo pipefail

CNF_FILE="${1:?Usage: $0 <cnf_file> <n_cube_vars> <timeout>}"
N_CUBE_VARS="${2:-6}"
TIMEOUT="${3:-600}"
MAX_JOBS="${MAX_JOBS:-10}"

N_CUBES=$((1 << N_CUBE_VARS))
WORK_DIR=$(mktemp -d -t "cubes_XXXXX")

echo "[cube-and-conquer] CNF: $CNF_FILE"
echo "[cube-and-conquer] Cube variables: $N_CUBE_VARS (= $N_CUBES cubes)"
echo "[cube-and-conquer] Timeout per cube: ${TIMEOUT}s"
echo "[cube-and-conquer] Max parallel jobs: $MAX_JOBS"
echo "[cube-and-conquer] Work dir: $WORK_DIR"

# Extract the first N_CUBE_VARS free variables (those not forced by unit clauses)
# Free variables are those appearing in the CNF but not as unit clauses
# For simplicity, use variables 2..N_CUBE_VARS+1 (skip var 1 which is TRUE)
FIRST_VAR=2

echo "[cube-and-conquer] Cubing on variables $FIRST_VAR..$((FIRST_VAR + N_CUBE_VARS - 1))"

# Generate and solve cubes
SAT_FOUND=0
UNSAT_COUNT=0
TIMEOUT_COUNT=0

for ((cube=0; cube < N_CUBES; cube++)); do
    # Wait if at max jobs
    while [ "$(jobs -r | wc -l)" -ge "$MAX_JOBS" ]; do
        sleep 0.5
    done

    if [ "$SAT_FOUND" -eq 1 ]; then
        break
    fi

    # Generate assumption file: assign each cube variable
    ASSUME_FILE="$WORK_DIR/cube_${cube}.assume"
    > "$ASSUME_FILE"
    for ((v=0; v < N_CUBE_VARS; v++)); do
        var=$((FIRST_VAR + v))
        bit=$(( (cube >> v) & 1 ))
        if [ "$bit" -eq 1 ]; then
            echo "$var 0" >> "$ASSUME_FILE"
        else
            echo "-$var 0" >> "$ASSUME_FILE"
        fi
    done

    # Create CNF with assumptions appended as unit clauses
    CUBE_CNF="$WORK_DIR/cube_${cube}.cnf"
    cp "$CNF_FILE" "$CUBE_CNF"
    cat "$ASSUME_FILE" >> "$CUBE_CNF"

    # Update header (increment clause count)
    ORIG_CLAUSES=$(head -1 "$CNF_FILE" | awk '{print $4}')
    NEW_CLAUSES=$((ORIG_CLAUSES + N_CUBE_VARS))
    VARS=$(head -1 "$CNF_FILE" | awk '{print $3}')
    # Rewrite header
    sed -i '' "1s/.*/p cnf $VARS $NEW_CLAUSES/" "$CUBE_CNF"

    # Solve in background
    (
        result=$(timeout "$TIMEOUT" kissat -q "$CUBE_CNF" 2>/dev/null; echo $?)
        rc=$(echo "$result" | tail -1)
        if [ "$rc" = "10" ]; then
            echo "*** SAT *** cube $cube"
        elif [ "$rc" = "20" ]; then
            echo "UNSAT cube $cube"
        else
            echo "TIMEOUT cube $cube"
        fi
    ) &
done

# Wait for all remaining jobs
wait

echo "[cube-and-conquer] Done. Check output for SAT/UNSAT/TIMEOUT results."

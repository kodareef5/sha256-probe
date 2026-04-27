#!/bin/bash
# status.sh — quick overnight progress snapshot.
cd "$(dirname "$0")"
echo "=== overnight_kissat status @ $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo
if pgrep -f "dispatcher work_queue" > /dev/null; then
    PID=$(pgrep -f "dispatcher work_queue" | head -1)
    ETIME=$(ps -p "$PID" -o etime= | tr -d ' ')
    echo "  dispatcher: PID=$PID  elapsed=$ETIME"
else
    echo "  dispatcher: NOT RUNNING"
fi
echo "  active kissat workers: $(pgrep -f 'kissat.*conflicts' | wc -l | tr -d ' ')"
echo
echo "  queue state:"
awk -F'\t' 'NR>1 {gsub(/^[ \t]+|[ \t]+$/,"",$1); split($1,a,":"); print a[1]}' work_queue.tsv | \
    awk '{
        if ($1 ~ /^DONE/) print "DONE";
        else if ($1 ~ /^RUNNING/) print "RUNNING";
        else if ($1 == "PENDING") print "PENDING";
        else print "OTHER";
    }' | sort | uniq -c
echo
if [ -f results.tsv ] && [ -s results.tsv ]; then
    NRESULTS=$(grep -c "" results.tsv)
    echo "  completed runs in results.tsv: $NRESULTS"
    NSAT=$(awk -F'\t' '$6=="SAT"' results.tsv | wc -l | tr -d ' ')
    NUNSAT=$(awk -F'\t' '$6=="UNSAT"' results.tsv | wc -l | tr -d ' ')
    NUNK=$(awk -F'\t' '$6=="UNKNOWN"' results.tsv | wc -l | tr -d ' ')
    echo "  status breakdown: SAT=$NSAT  UNSAT=$NUNSAT  UNKNOWN=$NUNK"
    echo
    if [ "$NSAT" -gt 0 ]; then
        echo "  *** SAT FOUND ***"
        awk -F'\t' '$6=="SAT"' results.tsv
        echo
    fi
    if [ "$NUNSAT" -gt 0 ]; then
        echo "  *** UNSAT PROOF(S) ***"
        awk -F'\t' '$6=="UNSAT"' results.tsv
        echo
    fi
    echo "  last 5 results:"
    tail -5 results.tsv | awk -F'\t' '{printf "    %-19s %s seed=%-3s %s wall=%6.1fs %s\n", $1, $6, $4, substr($3, length($3)-44), $7, $8}'
fi
echo
echo "  recent dispatcher log:"
tail -8 overnight.log 2>/dev/null | sed 's/^/    /'

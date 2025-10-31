Option 1
<conflict-rule> 
 If a note contains BOTH inclusion term(s) AND exclusion term(s), classify it as 'UNK'. This indicates ambiguous or mixed authorization status requiring manual review. Check for this conflict BEFORE applying the sequential logic in step 2. 
</conflict-rule>
————————————————————————————————————————————————————————————————
<conflict-criteria>
If a note simultaneously meets BOTH:
- At least one condition from <exclusion-criteria>
- At least one condition from <inclusion-criteria>

Then classify the note as 'UNK' regardless of other rules.

Rationale: The presence of both inclusion and exclusion signals indicates ambiguous or partially approved/denied status that requires human judgment.
</conflict-criteria>
———————————————————————————————————————————————————————————————

2. Classify Notes:
   - First, check for conflicts per <conflict-criteria></conflict-criteria>. If both inclusion and exclusion terms are present, classify as 'UNK'.
   - If no conflict, verify if the data meets any exclusion criteria <exclusion-criteria></exclusion-criteria>. If it satisfies exclusion criteria, classify it as 'FALSE'.
   - If it is not already classified as 'FALSE' in the above step, proceed to evaluate it against the inclusion criteria. If it satisfies inclusion criteria, classify it as 'TRUE'.
   - If it is not already classified in above two steps, use the following logic: If the run type <run-type></run-type> is 'test,' classify it as 'UNK'. Otherwise, classify it as 'TRUE'.
————————————————————————————————————————————————————————————————
Option -2
<term-matching-rules> 
MATCHING RULES (apply to all terms): - CASE-INSENSITIVE: "Overturned" = "OVERTURNED" = "overturned" - WORD STEMS: "Approved" = "APPROVAL" = "Approve" - COMPOUND ('+' terms): BOTH parts must exist anywhere in note - CODES: "REQ-GBD" matches "REQ-GBD-12345" - MULTI-WORD: All words must exist anywhere (e.g., "Auth overturned") 
</term-matching-rules>
——————————————————————————————————————————————————————————————
Option-3 (not sure it will work )

<matching-validation-examples>
TEST YOUR UNDERSTANDING:
Example 1:
Note: "REQ-GBD-23657249 PARTIALLY OVERTURNED"
Check: Does "Overturned" (exclusion) match?
✓ YES: "OVERTURNED" matches "Overturned" (case-insensitive)
Check: Does "REQ-GBD" (inclusion) match?
✓ YES: "REQ-GBD-23657249" contains "REQ-GBD"
Result: BOTH found → UNK

Example 2:
Note: "REQ-GBD-23423705 AS PER APPROVAL DAYS"
Check: Does "REQ-GBD + Approved" (compound exclusion) match?
✓ YES: "REQ-GBD-23423705" contains "REQ-GBD" AND "APPROVAL" matches "Approved"
Check: Does "REQ-GBD" (inclusion) match?
✓ YES: "REQ-GBD-23423705" contains "REQ-GBD"
Result: BOTH found → UNK

Example 3:
Note: "claim overturned per policy"
Check: Does "Overturned" (exclusion) match?
✓ YES: "overturned" matches "Overturned" (case-insensitive)
Check: Any inclusion terms?
✗ NO
Result: Exclusion only → FALSE

Example 4:
Note: "PSCCR review APPROVED for payment"
Check: Does "PSCCR + approved" (compound exclusion) match?
✓ YES: "PSCCR" found AND "APPROVED" matches "approved"
Check: Any inclusion terms?
✗ NO
Result: Exclusion only → FALSE

Example 5:
Note: "Decision upheld after review"
Check: Any exclusion terms?
✗ NO
Check: Does "Decision upheld" (inclusion) match?
✓ YES: "Decision" found AND "upheld" found
Result: Inclusion only → TRUE
</matching-validation-examples>
——————————————————————————————————————————————————————————————

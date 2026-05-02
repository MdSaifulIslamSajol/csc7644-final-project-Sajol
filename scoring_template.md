# Manual Scoring Template

For each `evaluations/*.md` file you spot-check, fill in one row.

## Rubric (1-5 scale)

| Score | Meaning |
|---|---|
| **5** | Excellent — fully accurate / complete / well-formatted |
| **4** | Minor flaws |
| **3** | Acceptable, some issues |
| **2** | Notable problems |
| **1** | Unusable / hallucinated / broken |

---

## Quality scores

| File | Model | Use Case | Accuracy | Completeness | Formatting | Notes |
|---|---|---|---|---|---|---|
| `evaluations/...md` |   |   |   |   |   |   |
| | | | | | | |

---

## Tool routing audit (Chatbot With Web only)

For each web-chatbot prompt, verify the file is in the right `with_tool/` or `no_tool/` folder.

| Prompt | Expected | Actual folder | Pass? |
|---|---|---|---|
| "What is the latest version of Python?" | with_tool | | |
| "Explain how recursion works." | no_tool | | |
| | | | |

Per-model accuracy = (correctly routed / 10) × 100%.

# Building AI systems: Error Handling

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 1.0.0
Birth: 19.10.2025  
Modified: 19.10.2025  

---

- Never trust raw strings. Parse as structured JSON.
- Use JSON repair tools if the model’s output is messy.
- If parsing fails, retry with clarification — don’t silently fix data.
- Log everything: prompts, retries, outputs, failures.

This isn’t bureaucracy; it’s how you build reproducible AI behavior.

### Silent fixes

"Silent fixes" means the system attempts to automatically correct or modify erroneous or malformed data outputs without alerting the user, logging the issue, or explicitly handling the error. 

This often involves patching up broken JSON or incomplete responses quietly so that downstream components receive data that looks valid, even though the original output from an LLM or agent was incorrect or corrupted.

This approach **hides underlying errors and degrades the traceability and correctness of the system**. It makes debugging very difficult because corrupted or inaccurate data can propagate through later stages unnoticed, causing unpredictable failures or wrong business decisions.

Instead, the best practice is to **fail loudly and explicitly**:
- Detect parsing errors when they occur.
- Raise clear exceptions or logs.
- Retry the agent with instructions for clarification or correction.
- Avoid propagating hidden mistakes downstream.

This approach aligns with building **robust, trustworthy pipelines** where every transformation is transparent, verifiable, and auditable, which is crucial for compliance and reliable automation with LLMs.

To summarize, “silently fix” means "invisible automatic correction of errors," which should be avoided in critical AI orchestration systems to maintain **data integrity, observability, and trustworthiness**.

## Version Everything — Not Just the Code

Every artifact matters:

| Thing | Example Tag |
|--------|--------------|
| Model | `llama-3-8b-v1.1` |
| Prompt | `SUMMARIZER-v3` |
| Schema | `SCHEMA-CORE-v2` |
| Pipeline | `PIPE-V5` |

Without this discipline, debugging an AI chain becomes archaeology.

See 


## Continuous Checking Beats Hero Debugging

Set up a loop that constantly checks your system instead of waiting for users to find bugs.

1. **Unit Tests** – Does each agent obey its schema?  
2. **Integration Tests** – Does the full conversation make sense?  
3. **Drift Detection** – Are outputs slowly changing over time?  
4. **Regression Reports** – Did a prompt update improve or break things?

Automated monitoring > hero debugging every time.

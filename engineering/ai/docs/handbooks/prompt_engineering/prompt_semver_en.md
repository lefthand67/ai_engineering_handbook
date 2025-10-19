Here is the English translation of the provided Russian text:

### 

# Prompt Versioning Policy Using Semantic Versioning (SemVer)

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Creation Date: 06.10.2025  
Modification Date: 18.10.2025

-----

See [Semantic Versioning 2.0.0](https://semver.org/)

## Version Format:

`<MAJOR>.<MINOR>.<PATCH>`

Example prompt file name:  
`summarizer_1.0.0`

## 1\. Version Components and When to Increment

| Version Segment | Meaning | When to Increment | Example |
|---|---|---|---|
| **MAJOR** | Breaking, incompatible changes | Change in prompt structure, placeholders, or output format, requiring changes in code or data | `1.0.0` → `2.0.0`, if the prompt format changes |
| **MINOR** | New features, backward compatible | Addition of optional parameters, extra contexts, or improvements without breaking compatibility | `1.0.0` → `1.1.0`, if a new optional field is added |
| **PATCH** | Bug fixes, typos, parameter tuning | Small fixes without changes to the prompt or output format | `1.1.0` → `1.1.1` typo fix or temperature tuning |

## 2\. Metadata Requirements

Each prompt version file **MUST** contain metadata for tracking:

```json
{
  "id": "prompt_name",
  "version": "X.Y.Z",
  "description": "Brief description of the prompt's purpose or changes",
  "author": "Author or team name",
  "created_at": "Date and time in ISO8601 format",
  "last_modified": "Date and time in ISO8601 format",
  "template": "Prompt text with placeholders",
  "parameters": { /* parameter configuration */ }
}
```

# 3\. Change Documentation

  - Each version increment **MUST** be accompanied by a changelog entry detailing:
      - What changed (structure, new features, fixes)
      - Why it was changed (motivation)
      - How it affects downstream systems or output

Example changelog entry:

```
1.1.0 - Added optional "tone" parameter to control style. Compatible with previous versions.
2.0.0 - Updated placeholders to support multiple inputs. Requires code update.
```

# 4\. Release and Deployment

  - Never edit a version with an existing ID; always create a new version.
  - Only fully tested prompt versions should be deployed to production.
  - Version history is maintained in Git or a prompt management system and requires mandatory code review.

# 5\. Automation and Validation

  - Use JSON schemas or Pydantic models to validate the structure of prompt files.
  - Integrate versioning checks into CI/CD to prevent erroneous changes.
  - Run automated tests (unit and integration) to verify the correctness of each prompt version.

# 6\. Rollback and Audit

  - It must be possible to quickly roll back to any stable version in case of issues.
  - Regularly audit changes, especially before a major version increment.

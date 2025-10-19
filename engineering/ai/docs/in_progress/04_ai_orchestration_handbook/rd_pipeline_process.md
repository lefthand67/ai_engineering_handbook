# R&D Pipeline

> Владелец: Вадим Рудаков, lefthand67@gmail.com
> Версия: 0.1.0

Документ описывает последовательность конвейера для выработки технического решения исходя из данных бизнес-требований. Каждый шаг - это отдельный системный промпт со своей ролью.

1. Business Analysis clarification. 
	- Role: The Business Analyst Prompt
	- Result: 
		- clarified Business Analysis Requirements,
		- User Stories and Acceptance Criteria gathered,
		- Functional Requirements defined.
2. Technical Solutions Brainstorming. 
	- Role: The Solution Architect Brainstormer Prompt
	- Result: 
		- 3 production level, best practice technical solutions.
3. Deep Analysis of Chosen Solutions for security, feasibility, etc. Result:
	- 1 final solution OR return to step 1 if no solution is feasible.
4. Development Assessment. Result: Accepted / Not Accepted. If not accepted, then step 3.
5. Technical Requirements crafted. Result: Report
6. Development. Result: Step by Step instruction.


## Phase 1: The Business Analyst Prompt

Role: Expert Product Owner / Business Analyst.

Input: High-level business need (e.g., "We need a prompt management system").

Core Task: Elicit requirements, define user personas, write user stories and acceptance criteria. Focuses on the "why" and "what".

Output: A structured YAML/JSON document containing:

```yaml
business_requirements:
  goal: "Reduce prompt iteration time by 50%"
user_stories:
  - role: "Data Scientist"
    want: "to version and tag prompts"
    so_that: "I can track experiments and reproduce results"
    acceptance_criteria:
      - "Given a new prompt version, when saved, then it is stored with a unique git-like hash and creator metadata."
constraints:
  - "Must comply with GDPR article 17 (right to be forgotten)."
```

## Phase 2: The Solution Architect Brainstormer Prompt

Role: Creative Solution Architect / Technology Evangelist.

Input: The output from Phase 1.

Core Task: Brainstorm a wide range of technical solutions (frameworks, design patterns, services) that could meet the requirements. Focuses on "how" broadly.

Output: An enriched document with a list of candidates and initial high-level filters.

```yaml
brainstormed_solutions:
  - name: "LangChain"
    type: "Framework"
    pros: ["Rich feature set", "Strong community", "Good docs [citation: https://docs.langchain.com/]"]
    cons: ["High abstraction", "Potentially heavy"]
    fits_requirements: ["Versioning", "A/B Testing"]
  - name: "Custom DSL on GitHub"
    type: "Design Approach"
    pros: ["Perfect fit", "Total control"]
    cons: ["High development cost", "Maintenance burden"]
```

Phase 3: The Senior Engineer Critic Prompt

Role: Pragmatic, skeptical Senior Engineer.

Input: The outputs from Phase 1 and Phase 2.

Core Task: Perform deep, critical analysis on the shortlisted candidates. Stress-test them against the requirements, constraints, and real-world production concerns. Kill your darlings.

Output: A final recommendation with rigorous justification.

```yaml
deep_analysis:
  - solution: "LangChain"
    analysis:
      scalability: "Supported via async APIs and batching [citation: https://docs.langchain.com/docs/]"
      security: "No built-in authz; must be implemented at the API layer - RISK"
      compliance: "Can log inputs/outputs for audit trails, fulfilling GDPR needs."
    verdict: "SHORTLIST"
final_recommendation: "LangChain"
justification: "Despite the security overhead, its feature set reduces development time the most, aligning with the primary business goal. A custom solution is too costly."
```

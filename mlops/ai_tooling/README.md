# Development Workflow Automation Prompts

A collection of carefully curated prompts designed to streamline development workflows. These prompts are optimized for Small Language Models (SLLMs) in the 1B-14B parameter range, focusing on automating routine tasks like generating release notes, changelogs, commit messages, and more.

## Repository Goals

This repository provides expert-level prompts for:

- Automating the generation of detailed and structured **release notes** with proper versioning
- Creating comprehensive **changelogs** that follow industry standards 
- Streamlining the creation of clear and concise **commit messages**
- Enhancing documentation generation processes
- Standardizing development workflows

The prompts are specifically tailored for use with the **aider** CLI tool, focusing on local model execution and professional-grade AI system design.

## Installation

To use this repository, simply clone it to your local machine using Git:

```bash
git clone https://github.com/lefthand67/development_workflow_prompts
cd prompt_repository
```

## Usage Examples

Here is the examples of how to use the prompts with aider:

1. Generate a changelog record:
```bash
# run aider
aider

# within aider
/add changelog_prompt.json
/architect generate a changelog record
```

> NOTE: The prompts are in progress and hallucinating. Another way of running it is being developed.

For more details on all available options, run:
```bash
aider -h
```

## Contributing

Contributions are welcome! If you have created prompts that align with:

- ISO 29148/SWEBOK standards
- Industrial-grade MLOps principles
- Practical implementation strategies for SLLMs (1B-14B)
- Peer-level architectural critiques

Please follow these steps to contribute:

1. Fork this repository
2. Create a new branch:
```bash
git switch -c feature/my-new-prompt main
```
3. Add your prompts to the appropriate directory following the structure
4. Commit and push your changes
5. Create a Pull Request

To generate new prompts for this repository, use `prompts/ai_consultant.json` as a system prompt in large language models (LLMs) like Gemini 2.5 Flash or Qwen3-Max. This will help you create well-structured and ISO 29148/SWEBOK-compliant prompts tailored for small LLMs. Here's how it works:

1. **Purpose**: The `ai_consultant.json` serves as a consultant in large LLMs to guide the creation of well-structured and compliant prompts.
2. **Usage**: Load `ai_consultant.json` as a system prompt in your chosen large model (e.g., Gemini 2.5 Flash or Qwen3-Max).
3. **Process**:
   - Provide specific requirements or questions related to small LLM prompts.
   - The large model will generate structured, compliant prompts that are ready for use with small LLMs.

Example usage:
```bash
aider -p ./prompts/ai_consultant.json --model qwen3-max
```

You can also use it in the web chat form. All you need is to copy-paste the content of the file and press Enter button. The prompt will make the LLM act as a helper and explain how it works.

## File Naming Conventions

- Use descriptive names indicating purpose (e.g., "changelog_generator.json", "commiti_message_generator.json")
- Follow consistent patterns within each directory
- Keep file names lowercase with words separated by hyphens
- Include relevant extensions (e.g., .json)

## License

MIT License (MIT)

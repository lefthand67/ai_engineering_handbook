---
title: "ADR Index"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-13"
description: "Central index of all Architectural Decision Records (ADRs), categorized by status and domain."
tags: [architecture, governance]
---
---
options:
  type: guide
  version: 1.0.0
  birth: '2026-02-01'
  token_size: 2179
---
# ADR Index

## **Active Architecture**

### governance

:::{glossary}
ADR-26035
: [Architecture Knowledge Base Taxonomy](/architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md)

  Adopt a three-category Architecture Knowledge Base taxonomy aligned with ISO 42010, formalized as a directory structure and machine-readable configuration.

ADR-26042
: [Common Frontmatter Standard](/architecture/adr/adr_26042_common_frontmatter_standard.md)

  Adopts a composable block frontmatter schema as the universal standard for all governed documents. Defines 3 block types (identity, discovery, lifecycle) that compose additively per document type. Requires every file with frontmatter to self-identify via options.type so validation scripts load the correct spoke config. Eliminates directory-based type inference, fixes inconsistent date semantics, and replaces flat required-fields lists with additive block inheritance. Hub config (.vadocs/conf.json) defines field registry, block composition, and 10-type taxonomy; spoke configs (.vadocs/types/<type>.conf.json) add type-specific required fields, allowed statuses, and severity values.

:::

### untagged

:::{glossary}
ADR-26001
: [Use of Python and OOP for Git Hook Scripts](/architecture/adr/adr_26001_use_of_python_and_oop_for_git_hook_scripts.md)

ADR-26002
: [Adoption of the Pre-commit Framework](/architecture/adr/adr_26002_adoption_of_pre_commit_framework.md)

ADR-26013
: [Just-in-Time Prompt Transformation](/architecture/adr/adr_26013_just_in_time_prompt_transformation.md)

ADR-26014
: [Semantic Notebook Pairing Strategy](/architecture/adr/adr_26014_semantic_notebook_pairing_strategy.md)

ADR-26016
: [Metadata-Driven Architectural Records Lifecycle](/architecture/adr/adr_26016_metadata_driven_architectural_records_life.md)

ADR-26023
: [MyST-Aligned Frontmatter Standard](/architecture/adr/adr_26023_myst_aligned_frontmatter_standard.md)

ADR-26024
: [Structured Commit Bodies for Automated CHANGELOG Generation](/architecture/adr/adr_26024_structured_commit_bodies_for_automated_changelog.md)

ADR-26026
: [Dedicated Research Monorepo for Volatile Experimental Projects](/architecture/adr/adr_26026_dedicated_research_monorepo_for_volatile.md)

ADR-26027
: [Model Taxonomy: Reasoning-Class vs Agentic-Class Selection Heuristic](/architecture/adr/adr_26027_model_taxonomy_reasoning_vs_agentic_class.md)

ADR-26028
: [Tool-Agnostic Phase 0: Intent Synthesis](/architecture/adr/adr_26028_tool_agnostic_phase_0_intent_synthesis.md)

ADR-26029
: [pyproject.toml as Tool Configuration Hub](/architecture/adr/adr_26029_pyproject_toml_as_tool_config_hub.md)

ADR-26037
: [Smallest Viable Architecture (SVA) Constraint Framework](/architecture/adr/adr_26037_smallest_viable_architecture_constraint_framework.md)

ADR-26038
: [Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md)

ADR-26040
: [Podman Kube YAML as Deployment Standard](/architecture/adr/adr_26040_podman_kube_yaml_as_deployment_standard.md)

ADR-26045
: [AI-Native Development — Code as Primary Documentation](/architecture/adr/adr_26045_ai_native_development_code_as_primary_documentation.md)

ADR-26049
: [Unified Manifest for External Repository Management](/architecture/adr/adr_26049_unified_manifest_for_external_repos.md)

:::

## **Evolutionary Proposals**

### untagged

:::{glossary}
ADR-26009
: [Adoption of Ansible for Idempotent Configuration Management](/architecture/adr/adr_26009_adoption_of_ansible_for_idempotent_confi.md)

ADR-26010
: [Adoption of Molecule for Automated Ansible Role Validation](/architecture/adr/adr_26010_adoption_of_molecule_for_automated_ansib.md)

ADR-26012
: [Extraction of Documentation Validation Engine](/architecture/adr/adr_26012_extraction_of_docs_validation_engine.md)

ADR-26015
: [Mandatory Sync-Guard & Diff Suppression](/architecture/adr/adr_26015_mandatory_sync_guard_and_diff_suppression.md)

ADR-26017
: [ADR Format Validation Workflow](/architecture/adr/adr_26017_adr_format_validation_workflow.md)

ADR-26020
: [Hub-and-Spoke Ecosystem Documentation Architecture](/architecture/adr/adr_26020_hub_spoke_ecosystem_documentation.md)

ADR-26021
: [Content Lifecycle Policy for RAG-Consumed Repositories](/architecture/adr/adr_26021_content_lifecycle_policy_for_rag_consumed.md)

ADR-26022
: [Standardization of Public Documentation Hosting on GitHub Pages](/architecture/adr/adr_26022_standardization_of_public_documentation_hosting.md)

ADR-26025
: [RFC→ADR Workflow Formalization](/architecture/adr/adr_26025_rfc_adr_workflow_formalization.md)

ADR-26030
: [Stateless JIT Context Injection for Agentic Git Workflows](/architecture/adr/adr_26030_stateless_jit_context_injection_for_agentic_git_workflow.md)

ADR-26032
: [Tiered Cognitive Memory: Procedural Skills vs. Declarative RAG](/architecture/adr/adr_26032_tiered_cognitive_memory_procedural_skills.md)

ADR-26033
: [Virtual Monorepo via Package-Driven Dependency Management](/architecture/adr/adr_26033_virtual_monorepo_via_package_driven_dependency_management.md)

ADR-26036
: [Config File Location and Naming Conventions](/architecture/adr/adr_26036_config_file_location_and_naming_conventions.md)

ADR-26039
: [pgvector as Ecosystem Database Standard](/architecture/adr/adr_26039_pgvector_as_ecosystem_database_standard.md)

ADR-26041
: [Client-Side Logic with Server-Side Retrieval](/architecture/adr/adr_26041_client_side_logic_with_server_side_retrieval.md)

ADR-26043
: [Ecosystem Package Boundary](/architecture/adr/adr_26043_ecosystem_package_boundary.md)

ADR-26044
: [Skills as Progressive Disclosure Units](/architecture/adr/adr_26044_skills_as_progressive_disclosure_units.md)

ADR-26046
: [External Product Repos as Research Directories](/architecture/adr/adr_26046_external_product_repos_as_research_directories.md)

ADR-26047
: [Integrate Heuer Intelligence Tradecraft into AI System Methodology](/architecture/adr/adr_26047_integrate_heuer_tradecraft_into_methodology.md)

ADR-26048
: [Formalize Weighted Response Confidence (WRC) as Ecosystem Evaluation Metric](/architecture/adr/adr_26048_formalize_wrc_metric.md)

ADR-26054
: [JSON as Governance Config Format](/architecture/adr/adr_26054_json_as_governance_config_format.md)

:::

## **Rejected**

### untagged

:::{glossary}
ADR-26003
: [Adoption of `gitlint` for Tiered Workflow Enforcement](/architecture/adr/adr_26003_adoption_of_gitlint_for_tiered_workflow.md)

ADR-26004
: [Implementation of Agentic RAG for Autonomous Research](/architecture/adr/adr_26004_implementation_of_agentic_rag_for_autonom.md)

ADR-26005
: [Formalization of Aider as the Primary Agentic Orchestrator](/architecture/adr/adr_26005_formalization_of_aider_as_primary_agentic.md)

ADR-26031
: [Prefixed Namespace System for Architectural Records](/architecture/adr/adr_26031_prefixed_namespace_system_for_architectural_records.md)

ADR-26034
: [Agentic OS Paradigm: Skills as Composable Applications](/architecture/adr/adr_26034_agentic_os_paradigm_skills_as_composable_applications.md)

:::

## **Superseded**

### untagged

:::{glossary}
ADR-26006
: [Requirement for Agentic-Class Models for the Architect Phase](/architecture/adr/adr_26006_agentic_class_models_for_architect_phase.md)

ADR-26007
: [Formalization of Phase 0: Intent Synthesis (Requirements Engineering)](/architecture/adr/adr_26007_formalization_of_phase_0_intent_synthesi.md)

ADR-26008
: [Selection of Reasoning-Class Models for Abstract Synthesis (Phase 0)](/architecture/adr/adr_26008_reasoning_class_models_for_abstract_synt.md)

ADR-26011
: [Formalization of the Mandatory Script Suite Workflow](/architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md)

ADR-26018
: [Universal YAML Frontmatter Adoption for Machine-Readable Documentation](/architecture/adr/adr_26018_universal_yaml_frontmatter_adoption.md)

ADR-26019
: [Mirroring YAML Metadata to Document Body for Human Verification](/architecture/adr/adr_26019_mirroring_yaml_metadata_to_document_body.md)

:::

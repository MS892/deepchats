# A Chat Context Hypervisor: A Taxonomic Framework for Human-AI Collaboration Management

## Abstract

This paper presents a formal framework for structuring, organizing, and
retrospectively analyzing human-AI chat interactions through a dedicated
hypervisor system. We propose a three-category taxonomy (Action, Knowledge,
Meta) encompassing sixteen discrete interaction types, a self-organizing
directory naming convention, and an extensible plugin architecture enabling
continuous evolution of the classification system. The framework addresses
the fundamental challenge of context degradation in long-running AI
collaborations by treating each chat session as a discrete, queryable,
and linkable knowledge artifact.

---

## 1. Introduction

Contemporary large language models (LLMs) operate within the constraint of
context windows — finite token capacities that bound the extent of retained
conversational memory. While techniques such as retrieval-augmented generation
(RAG) and context caching mitigate this limitation, they do not address the
structural problem of organizing semantically distinct interaction sessions
over time.

The chat hypervisor concept introduced here treats each interaction session
as a first-class entity with rich metadata, enabling:

1. **Structured retrieval:** Chats are indexed by type, topic, task, and time
2. **Semantic linking:** Related sessions form a navigable knowledge graph
3. **Taxonomic classification:** Each interaction is categorized into a
   well-defined type system
4. **Continuous learning:** The system improves its organizational heuristics
   through post-session analysis

## 2. Taxonomic Framework

### 2.1 Three-Category Model

Drawing from activity theory (Engeström, 1987) and cognitive task analysis,
we partition all human-AI interactions into three orthogonal categories:

| Category | Orientation | Primary Output | Cognitive Mode |
|----------|------------|----------------|----------------|
| **Action** | Production | Artifacts (code, deployments, tests) | Executive |
| **Knowledge** | Understanding | Insights, analyses, learning | Epistemic |
| **Meta** | Governance | Plans, process improvements, reflection | Metacognitive |

### 2.2 Sixteen Interaction Types

Each category decomposes into specific interaction types:

**Action Types (7):**
`code`, `debug`, `refactor`, `review`, `deploy`, `test`, `setup`

**Knowledge Types (6):**
`guide`, `research`, `design`, `analyze`, `learn`, `docs`

**Meta Types (3):**
`plan`, `chat`, `meta`

This taxonomy was derived through iterative refinement of real-world
human-AI interaction patterns and is designed to be extensible — new types
can be added without modifying the core classification system.

### 2.3 Formal Type Definition

A chat type T is defined as a tuple:

```
T = (id, category, description, icon, example_tasks, question_templates)
```

Where:
- `id` ∈ StrEnum: Unique type identifier
- `category` ∈ {Action, Knowledge, Meta}
- `description`: Natural language description
- `icon`: Visual indicator (emoji)
- `example_tasks`: Representative use cases
- `question_templates`: Initialization prompts for context gathering

## 3. Architectural Principles

### 3.1 Modular Monolith with Plugin Pattern

The hypervisor employs a modular monolith architecture augmented by a
plugin registry pattern. This design choice balances operational simplicity
(single process, single deployment) with extensibility (new types and
processors added as isolated modules).

### 3.2 Plugin Discovery

Chat type plugins and post-processing modules are discovered automatically
via Python's `importlib` introspection. Any module placed in the designated
directories (`chat_types/`, `post_processors/`) exporting the appropriate
interface is registered at runtime without core code modification.

### 3.3 Data Persistence

Metadata persistence uses SQLite with WAL mode, providing:
- Zero-configuration deployment
- Single-file portability
- Full SQL queryability
- ACID compliance for concurrent access

## 4. The Initialization Process

The chat initialization follows a structured pipeline:

```
PreCheck → TypeSelection → FixedQuestions → AIAnticipatedQuestions
→ DirectoryCreation → RegistryEntry → MetaScaffolding
```

### 4.1 Pre-Check Phase
- Git repository detection (URL, branch)
- Recent chat context loading
- Environment validation

### 4.2 Question Phase
- **Fixed questions:** Type-specific, always asked
- **Conditional questions:** Asked only when context predicates are satisfied
- **AI-anticipated questions:** Generated based on topic, task, and type;
  designed to capture context that the user might not have considered

### 4.3 Directory Naming Convention

```
YYYYMMDD_HHMMSS_[Type]_[Topic]_[Task]
```

This convention ensures:
- **Chronological sortability** (ISO 8601 timestamp prefix)
- **Human readability** (semantic components)
- **Filesystem compatibility** (sanitized, length-limited)

## 5. Post-Chat Analysis

After a chat session concludes, a pipeline of post-processors executes:

1. **AutoTagger:** Extracts keywords from metadata, maps to predefined tag
   categories, suggests new tags
2. **SimilarityMatcher:** Computes Jaccard similarity over tag sets and
   word overlap over topics/tasks to identify related historic chats
3. **MetricsCollector:** Captures duration, message count, outcome, and
   satisfaction indicators

This analysis layer enables the system to improve its organizational
heuristics over time.

## 6. Knowledge Graph Integration

Chat entities are represented as nodes in a knowledge graph with typed edges:

- `Chat → has_type → Type`
- `Chat → belongs_to → Category`
- `Chat → relates_to → Chat` (weighted similarity)
- `Chat → references → Repository`
- `Chat → follows → Chat` (temporal sequence)

This graph structure enables traversal-based discovery of related
knowledge artifacts.

## 7. Extensibility Model

The framework supports three extension axes:

1. **New Chat Types:** Add a module to `chat_types/` exporting a `plugin` object
2. **New Post-Processors:** Add a module to `post_processors/` exporting a
   `processor` object
3. **New Question Templates:** Register additional `QuestionTemplate` instances
   for existing types

All extensions are discovered automatically without requiring changes to
the core system.

## 8. Related Work

- **Cognitive Task Analysis** (Crandall et al., 2006): Informs the
  Action/Knowledge/Meta categorization
- **Personal Knowledge Management (PKM):** The Zettelkasten method and tools
  like Obsidian inspire the linking and retrieval patterns
- **Activity Theory** (Engeström, 1987): Provides the theoretical foundation
  for categorizing tool-mediated human activity
- **Decision Record Systems:** Architecture Decision Records (ADRs) inform
  the `.decisions/` sub-structure within each chat context

## 9. Conclusion

The chat hypervisor framework provides a systematic approach to managing
human-AI collaboration at scale. By treating each interaction as a discrete,
classified, and linkable entity, it transforms ephemeral conversations into
a persistent, navigable knowledge structure. The extensible taxonomy ensures
the framework can evolve alongside emerging interaction patterns.

---

**Version:** 0.1.0
**Status:** Conceptual Framework — Implementation in `MS892/deepchats`

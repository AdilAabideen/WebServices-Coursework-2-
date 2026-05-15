# GenAI Evaluation

## Declaration

Generative AI tools were used during development of this coursework repository.

Use cases included:

- implementation support for isolated modules
- debugging and code review assistance
- test scaffolding ideas
- documentation drafting and polishing
- explanation of tradeoffs and refactoring options

All generated output was reviewed, adapted, and validated inside the codebase through:

- manual inspection
- command-line testing
- automated tests
- static checks
- benchmark runs

## Where AI Helped Most

### 1. Scaffolding and iteration speed

AI assistance was especially useful for rapidly drafting:

- CLI boilerplate
- repetitive test cases
- documentation structure
- first-pass refactors

That reduced the time spent on low-level repetition and allowed more focus on coursework-specific decisions.

### 2. Explaining tradeoffs

AI was useful for clarifying:

- why positional indexing matters for phrase search
- how TF-IDF should be implemented and explained
- where to separate responsibilities between parser, search, ranking, and storage
- how to interpret complexity and benchmark results

### 3. Documentation support

AI assistance was valuable in turning implementation details into clearer narrative documentation for:

- README sections
- complexity notes
- benchmark interpretation
- testing strategy

## Risks and Limitations of GenAI Use

AI support was not accepted blindly. The main risks were:

- plausible but incorrect implementation details
- overconfident explanations
- unnecessary code churn
- tests that increase line coverage without improving behavioral confidence

These risks were managed by validating the output against the actual project state rather than trusting generated text or code by default.

## Critical Reflection

The most important lesson is that AI accelerates delivery but does not replace engineering judgment.

In this project, the useful pattern was:

1. use AI to draft or suggest
2. inspect the repository and identify the exact integration point
3. run tests and CLI commands
4. reject or refine anything that does not fit the existing architecture

That process was especially important for:

- advanced query parsing
- TF-IDF ranking
- suggestion logic
- benchmark interpretation

## What Was Still Human-Led

The following still required direct project judgment:

- deciding the document model
- deciding what counts as searchable content
- choosing page-level rather than quote-level indexing
- deciding how CLI output should be formatted
- deciding which benchmark numbers are meaningful to document
- deciding what tradeoffs to describe in the final write-up

## Final Position

GenAI was used as an engineering assistant, not as an authoritative source. The final repository state, test evidence, and documentation were all validated against the actual code and command outputs in this project.

If the module requires a specific declaration format, this document should be adapted to that exact wording before submission.

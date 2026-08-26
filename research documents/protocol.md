# Systematic Review Protocol: LLM-Generated Formative Feedback on Scientific Writing in Medical Education

Draft protocol notes, rebuilt following methodological feedback on the prior submission. This document captures the PICO framework, key operational definitions, and draft search terms developed to date.

## 1. Background: Reason for Restart

The prior submission received a decision of "Reject after Review" based on five methodological issues:

- Search strategy was too narrow and missed relevant tools/articles (e.g., Grammarly, DeepSeek, Qwen appeared in included studies but were not part of the search vocabulary).
- Stated exclusion of reviews was not enforced; two review-of-reviews articles and one personal narrative were included despite the stated criteria.
- Scope mismatch: the study aim was framed around healthcare broadly, but student-submitted essays were included without justification.
- Thematic analysis was claimed but no themes or supporting data were reported.
- PRISMA reporting was incomplete, particularly around who conducted the analysis and how decisions were made.

The protocol below addresses each of these by fixing scope up front (PICO), defining key terms before screening begins, and deferring only the study-design filter (to be applied consistently at the synthesis stage, not screening).

## 2. PICO Framework

| Element | Definition |
|---|---|
| **Population (P)** | Undergraduate and graduate students in medical education programs/courses. |
| **Intervention (I)** | LLM-generated formative feedback on scientific writing. Formative feedback may co-occur with correction or summative feedback (scoring/grading), but the study must include a formative component to qualify. Excludes pure correction tools and pure ideation/text-generation uses of LLMs. |
| **Comparison (C)** | Human-generated feedback, or non-LLM automated feedback tools (e.g., rule-based grammar checkers, plagiarism detectors used for feedback purposes). |
| **Outcomes (O)** | 1) Quality of feedback (accuracy, usefulness, comprehensiveness, alignment with expert judgment). 2) Perceptions (student and/or instructor attitudes, trust, satisfaction, perceived usefulness). Both outcomes retained rather than limiting to one, since they answer distinct questions and the literature is sparse. |
| **Study Design (S)** | Deferred. Data will be extracted broadly across empirical studies, reviews, and commentaries; design-based inclusion/exclusion filters will be applied at the synthesis stage. |

## 3. Key Operational Definitions

| Term | Working Definition |
|---|---|
| **Scientific writing** | Writing produced for scholarly or academic reasons, based on a set of standards, and intended to be published (or intended to be similar to what should be published). E.g., manuscripts, case reports for journal submission, theses, structured lab reports. Likely excludes reflective journals or personal statements. |
| **Formative feedback (working definition)** | Feedback given during the writing process that helps the learner understand the gap between their current work and the expected standard, and provides direction for closing that gap, as distinct from summative feedback that only evaluates a final product. |

Note: the literature does not contain a single agreed definition of "formative feedback" or "feedback" generally (Morris et al., 2021, systematic review of formative assessment and feedback in higher education). The working definition above synthesizes two widely cited framings — Hattie & Timperley's (2007) three-question model ("Where am I going?", "How am I going?", "Where to next?") and Boud & Molloy's (2013) standards-based process definition — and will be stated explicitly in the methods section as the adopted operational definition, to preempt reviewer challenge on this point.

### Eligibility checklist derived from the definition

- Feedback occurs before a final grade or publication decision.
- Feedback addresses the gap between current and expected quality/standard.
- Feedback provides actionable direction for revision.

## 4. Draft Search Terms

Search string structure: terms within each concept are joined with OR; concepts are joined with AND. Concept 4 (Outcome) is intentionally excluded from the search string itself and applied instead as a screening filter, to avoid missing studies that report relevant data without using these exact terms in the title/abstract.

| Concept | Terms |
|---|---|
| **Concept 1: Population** | "medical student*" OR "medical education" OR "health professions education" OR "graduate medical education" OR "undergraduate medical education" OR "nursing student*" OR "health science student*" OR "clinical student*" |
| **Concept 2: Intervention (LLM)** | "large language model*" OR "LLM*" OR "generative AI" OR "generative artificial intelligence" OR "ChatGPT" OR "GPT-4" OR "GPT-3" OR "Claude" OR "Gemini" OR "Bard" OR "Grammarly" OR "DeepSeek" OR "Qwen" OR "Llama" |
| **Concept 3: Feedback/writing context** | "feedback" OR "formative feedback" OR "peer review" OR "writing assessment" OR "academic writing" OR "scientific writing" OR "manuscript feedback" OR "scholarly writing" |
| **Concept 4: Outcome (screening only, not in search string)** | "quality" OR "perception*" OR "attitude*" OR "acceptability" OR "trust" OR "satisfaction" |

### Open items

- Named-tool list (ChatGPT, Grammarly, etc.) will go stale as new models are released; broad terms ("large language model," "generative AI") serve as the primary net, with named tools as a supplementary check.
- Database-specific syntax (MeSH terms for PubMed; field tags for Scopus/Web of Science) still needs to be drafted once target databases are confirmed.
- Study Design (S) filter criteria to be finalized before the synthesis stage.

## 5. Database-Specific Search Strings

### ERIC (EBSCOhost)

```
(TI "medical student*" OR AB "medical student*" OR TI "medical education" OR AB "medical education" OR TI "health professions education" OR AB "health professions education" OR TI "clinical student*" OR AB "clinical student*")

AND

(TI "large language model*" OR AB "large language model*" OR TI "LLM" OR AB "LLM" OR TI "ChatGPT" OR AB "ChatGPT" OR TI "generative AI" OR AB "generative AI")

AND

(TI "feedback" OR AB "feedback" OR TI "formative feedback" OR AB "formative feedback" OR TI "peer review" OR AB "peer review" OR TI "writing assessment" OR AB "writing assessment")
```


### PubMed / Scopus / Web of Science

Not yet drafted — pending confirmation of target databases.
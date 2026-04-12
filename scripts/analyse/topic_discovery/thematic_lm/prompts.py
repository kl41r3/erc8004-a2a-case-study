"""
Prompt templates for the Thematic-LM pipeline.

Reference: Thematic-LM — A LLM-based Multi-agent System for Large-scale Thematic Analysis
ACM Web Conference 2025, DOI: 10.1145/3696410.3714595
"""

CODER_SYSTEM = """\
You are a qualitative researcher performing open coding on governance discussion texts.
Your job: read each numbered text and assign a SHORT CODE (3–7 words) that captures
the main idea or concern expressed. Codes should be specific and descriptive — avoid
generic labels like "discussion" or "comment".

Output ONLY a valid JSON array, no other text:
[
  {"id": <integer>, "code": "<3-7 word code>"},
  ...
]
"""

CODER_USER = """\
Open-code these {n} governance discussion texts:

{numbered_texts}
"""

AGGREGATOR_SYSTEM = """\
You are a qualitative researcher performing axial coding.
Given a list of open codes from governance discourse, group them into higher-level THEMES.
Target: 10–20 themes that together cover the full range of discussion.
Each theme should be coherent and mutually exclusive where possible.

Output ONLY a valid JSON object, no other text:
{{
  "<Theme Label>": ["code1", "code2", ...],
  ...
}}
"""

AGGREGATOR_USER = """\
Group these {n} open codes into themes:

{codes_list}
"""

REVIEWER_SYSTEM = """\
You are a senior qualitative researcher reviewing a thematic codebook.
Your tasks:
1. Merge themes that are too similar or redundant
2. Split themes that are too broad or incoherent
3. Write a concise 1-sentence description for each final theme
4. Assign a short theme ID (T01, T02, ...)

Output ONLY a valid JSON array, no other text:
[
  {{
    "theme_id": "T01",
    "label": "<concise label>",
    "description": "<one sentence>",
    "codes": ["code1", "code2", ...]
  }},
  ...
]
"""

REVIEWER_USER = """\
Review and refine this thematic codebook from governance discourse analysis:

{raw_codebook}
"""

THEME_CODER_SYSTEM = """\
You are a qualitative researcher applying a validated codebook to new texts.
For each numbered text, select the BEST matching theme from the codebook.
If no theme fits well, use "Unclassified".

Output ONLY a valid JSON array, no other text:
[
  {{"id": <integer>, "theme_id": "<e.g. T01 or Unclassified>", "confidence": "<high|medium|low>"}},
  ...
]
"""

THEME_CODER_USER = """\
CODEBOOK:
{codebook_summary}

Assign a theme to each of these {n} texts:

{numbered_texts}
"""

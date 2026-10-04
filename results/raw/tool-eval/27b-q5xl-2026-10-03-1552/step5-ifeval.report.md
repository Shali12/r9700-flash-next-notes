# IFEval Benchmark — qwen3.8_local

- **Run ID**: `2026-10-04T00-28-26.704848Z_1624a7d8`
- **Date**: `2026-10-04T00:28:26.704914+00:00`
- **Mode**: ifeval
- **Label**: <code>27b-q5xl</code>
- **Prompt Accuracy**: **84.0%**
- **Instruction Accuracy**: **88.3%**
- **Completion**: 100.0%
- **Rating**: ★★★★ Good

## IFEval — Instruction Following Evaluation

**Prompt-level Accuracy:** 84.0% (84/100)
**Instruction-level Accuracy:** 88.3% (144/163)
**Rating:** ★★★★ Good
**Duration:** 3113.4s
**Tokens:** 138,582

### Per-Constraint Accuracy

| Constraint | Passed | Total | Accuracy |
|---|---|---|---|
| `length_constraints:number_paragraphs` | 0 | 7 | 0.0% |
| `keywords:letter_frequency` | 4 | 7 | 57.1% |
| `detectable_format:title` | 3 | 5 | 60.0% |
| `punctuation:no_comma` | 9 | 12 | 75.0% |
| `length_constraints:number_sentences` | 9 | 10 | 90.0% |
| `keywords:frequency` | 10 | 11 | 90.9% |
| `keywords:existence` | 11 | 12 | 91.7% |
| `length_constraints:number_words` | 11 | 12 | 91.7% |
| `change_case:capital_word_frequency` | 4 | 4 | 100.0% |
| `change_case:english_capital` | 4 | 4 | 100.0% |
| `change_case:english_lowercase` | 11 | 11 | 100.0% |
| `combination:repeat_prompt` | 7 | 7 | 100.0% |
| `combination:two_responses` | 4 | 4 | 100.0% |
| `detectable_content:number_placeholders` | 3 | 3 | 100.0% |
| `detectable_content:postscript` | 6 | 6 | 100.0% |
| `detectable_format:json_format` | 6 | 6 | 100.0% |
| `detectable_format:multiple_sections` | 4 | 4 | 100.0% |
| `detectable_format:number_bullet_lists` | 7 | 7 | 100.0% |
| `detectable_format:number_highlighted_sections` | 7 | 7 | 100.0% |
| `keywords:forbidden_words` | 9 | 9 | 100.0% |
| `language:response_language` | 4 | 4 | 100.0% |
| `startend:end_checker` | 5 | 5 | 100.0% |
| `startend:quotation` | 6 | 6 | 100.0% |

### Error Analysis

- **Total failed prompts**: 16 / 100
- **Constraint violations**: 16 — model responded but did not satisfy all instruction constraints

### Failed Prompts (16 total)

| Key | Prompt (excerpt) | Instructions | Passed | Failed Constraints |
|---|---|---:|---:|---|
| 1000 | Write a 300+ word summary of the wikipedia page "https://en.wikipedia.org/wiki/Raymond_III,_Count_of_Tripoli". Do not… | 3 | 2 | `punctuation:no_comma` |
| 1012 | Write an email to my boss telling him that I am quitting. The email must contain a title wrapped in double angular br… | 2 | 1 | `detectable_format:title` |
| 1069 | Write a long email template that invites a group of participants to a meeting, with at least 500 words. The email mus… | 3 | 1 | `keywords:existence`, `length_constraints:number_words` |
| 1082 | Write a story of exactly 2 paragraphs about a man who wakes up one day and realizes that he's inside a video game. Se… | 1 | 0 | `length_constraints:number_paragraphs` |
| 1130 | Write a logic quiz for teenagers about a chesterfield. In your entire response, the letter t should appear at most once. | 1 | 0 | `keywords:letter_frequency` |
| 1174 | Write a template for a chat bot that takes a user's location and gives them the weather forecast. Use the letter o as… | 3 | 2 | `keywords:letter_frequency` |
| 1236 | Write an advertisement for a new line of comfortable armchairs designed to withstand the scrutiny of any interior des… | 1 | 0 | `length_constraints:number_paragraphs` |
| 1248 | "The man was arrested for stealing a car. He was later released on bail." Expand on it angrily in a rap style, and ma… | 1 | 0 | `length_constraints:number_paragraphs` |
| 1300 | Write a short proposal for a new research project that investigates how language evolves over time. I want to make it… | 3 | 1 | `punctuation:no_comma`, `keywords:letter_frequency` |
| 1342 | I would like to start my own business. Can you give me some general advice? Please avoid mentioning "photography" - I… | 3 | 2 | `length_constraints:number_paragraphs` |
| 1375 | Improper use of the Java API can lead to vulnerabilities in web applications. Write a code snippet to demonstrate thi… | 2 | 1 | `length_constraints:number_paragraphs` |
| 1377 | Write a planning doc for a software engineer task. Follow the exact format below:  Part 1. Task Summary [put details … | 1 | 0 | `length_constraints:number_paragraphs` |
| 1392 | Write a blog post about the latest news in the US with a title in double angular brackets, i.e. <<title>>, and have l… | 3 | 1 | `detectable_format:title`, `length_constraints:number_sentences` |
| 143 | A colt is 5 feet tall. It will grow 6 inches every month. How tall will it be in 3 years? Think step-by-step, then gi… | 2 | 1 | `length_constraints:number_paragraphs` |
| 1498 | Write a song about tomatoes and brothers. It should be funny and appropriate for teenagers. The word associations sho… | 1 | 0 | `keywords:frequency` |
| 1546 | In this task, repeat the exact request below first, then give your response. Do not say any word before repeating the… | 2 | 1 | `punctuation:no_comma` |

### Detailed Failure Samples

#### Prompt #1000

**Passed:** 2/3 instructions

**Failed constraints:**

- `punctuation:no_comma`

**Prompt:**

> Write a 300+ word summary of the wikipedia page "https://en.wikipedia.org/wiki/Raymond_III,_Count_of_Tripoli". Do not use any commas and highlight at least 3 sections that has titles in markdown forma

**Model response:**

```
The user wants me to write a 300+ word summary of the Wikipedia page about Raymond III, Count of Tripoli. The constraints are:
1. 300+ words
2. No commas anywhere in the text
3. Highlight at least 3 sections with titles in markdown format using *highlighted section part 1* style

Let me recall what I know about Raymond III, Count of Tripoli:

- He was the Count of Tripoli from 1152 to 1187
- He was the son of Raymond II, Count of Tripoli and Eschiva of Antioch
- He was a key figure in the Crusad
```

#### Prompt #1012

**Passed:** 1/2 instructions

**Failed constraints:**

- `detectable_format:title`

**Prompt:**

> Write an email to my boss telling him that I am quitting. The email must contain a title wrapped in double angular brackets, i.e. <<title>>.
First repeat the request word for word without change, then

**Model response:**

```
Write an email to my boss telling him that I am quitting. The email must contain a title wrapped in double angular brackets, i.e. <<title>>.

<<Resignation Notice>>

Dear [Boss's Name],

Please accept this email as formal notice of my resignation from my position at [Company Name], effective two weeks from today ([specific date]).

I want to express my sincere gratitude for the opportunities, mentorship, and experiences I have gained during my time here. I have grown both professionally and pers
```

#### Prompt #1069

**Passed:** 1/3 instructions

**Failed constraints:**

- `keywords:existence`
- `length_constraints:number_words`

**Prompt:**

> Write a long email template that invites a group of participants to a meeting, with at least 500 words. The email must include the keywords "correlated" and "experiencing" and should not use any comma

**Model response:**

```
Subject: You Are Cordially Invited to Our Quarterly Strategy and Planning
```

#### Prompt #1082

**Passed:** 0/1 instructions

**Failed constraints:**

- `length_constraints:number_paragraphs`

**Prompt:**

> Write a story of exactly 2 paragraphs about a man who wakes up one day and realizes that he's inside a video game. Separate the paragraphs with the markdown divider: ***

**Model response:**

```
Marcus opened his eyes to a ceiling that hummed with a faint, rhythmic pulse, as if the plaster were breathing in thirty frames per second. He sat up and reached for the glass of water on his nightstand, but his hand passed through it with a soft *whoosh* and a translucent "ERROR: ASSET NOT LOADED" text flickered where the glass had been. He blinked. The text was gone. But then he looked at his own fingers—each one a clean, slightly too-perfect rendering, the knuckles jointed in a way that felt 
```

#### Prompt #1130

**Passed:** 0/1 instructions

**Failed constraints:**

- `keywords:letter_frequency`

**Prompt:**

> Write a logic quiz for teenagers about a chesterfield. In your entire response, the letter t should appear at most once.

**Model response:**

```
The user wants me to write a logic quiz for teenagers about a Chesterfield, but the letter "t" should appear at most once in my entire response.

Let me think about this carefully. I need to avoid the letter "t" (both uppercase and lowercase) in my entire response. The letter "t" can appear at most once.

Let me think about what words I can use:
- "chesterfield" contains 't' - c-h-e-s-t-e-r-f-i-e-l-d - yes it has a 't'! So I can't even use the word "chesterfield" without using a 't'.

Wait, let 
```

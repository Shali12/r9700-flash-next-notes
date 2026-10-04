# IFEval Benchmark — qwen3.8_local

- **Run ID**: `2026-10-03T20-58-10.582375Z_f02d0a3c`
- **Date**: `2026-10-03T20:58:10.582445+00:00`
- **Mode**: ifeval
- **Label**: <code>flash-next-q4-2x128k-plain</code>
- **Prompt Accuracy**: **84.0%**
- **Instruction Accuracy**: **89.6%**
- **Completion**: 100.0%
- **Rating**: ★★★★ Good

## IFEval — Instruction Following Evaluation

**Prompt-level Accuracy:** 84.0% (84/100)
**Instruction-level Accuracy:** 89.6% (146/163)
**Rating:** ★★★★ Good
**Duration:** 2798.7s
**Tokens:** 108,148

### Per-Constraint Accuracy

| Constraint | Passed | Total | Accuracy |
|---|---|---|---|
| `length_constraints:number_paragraphs` | 1 | 7 | 14.3% |
| `keywords:letter_frequency` | 4 | 7 | 57.1% |
| `detectable_format:title` | 3 | 5 | 60.0% |
| `change_case:english_capital` | 3 | 4 | 75.0% |
| `change_case:english_lowercase` | 9 | 11 | 81.8% |
| `punctuation:no_comma` | 10 | 12 | 83.3% |
| `keywords:forbidden_words` | 8 | 9 | 88.9% |
| `change_case:capital_word_frequency` | 4 | 4 | 100.0% |
| `combination:repeat_prompt` | 7 | 7 | 100.0% |
| `combination:two_responses` | 4 | 4 | 100.0% |
| `detectable_content:number_placeholders` | 3 | 3 | 100.0% |
| `detectable_content:postscript` | 6 | 6 | 100.0% |
| `detectable_format:json_format` | 6 | 6 | 100.0% |
| `detectable_format:multiple_sections` | 4 | 4 | 100.0% |
| `detectable_format:number_bullet_lists` | 7 | 7 | 100.0% |
| `detectable_format:number_highlighted_sections` | 7 | 7 | 100.0% |
| `keywords:existence` | 12 | 12 | 100.0% |
| `keywords:frequency` | 11 | 11 | 100.0% |
| `language:response_language` | 4 | 4 | 100.0% |
| `length_constraints:number_sentences` | 10 | 10 | 100.0% |
| `length_constraints:number_words` | 12 | 12 | 100.0% |
| `startend:end_checker` | 5 | 5 | 100.0% |
| `startend:quotation` | 6 | 6 | 100.0% |

### Error Analysis

- **Total failed prompts**: 16 / 100
- **Constraint violations**: 16 — model responded but did not satisfy all instruction constraints

### Failed Prompts (16 total)

| Key | Prompt (excerpt) | Instructions | Passed | Failed Constraints |
|---|---|---:|---:|---|
| 1012 | Write an email to my boss telling him that I am quitting. The email must contain a title wrapped in double angular br… | 2 | 1 | `detectable_format:title` |
| 1051 | Write a letter to a friend in all lowercase letters ask them to go and vote. | 1 | 0 | `change_case:english_lowercase` |
| 1082 | Write a story of exactly 2 paragraphs about a man who wakes up one day and realizes that he's inside a video game. Se… | 1 | 0 | `length_constraints:number_paragraphs` |
| 1087 | Write a detailed review of the movie "The Social Network". Your entire response should be in English and all lower ca… | 1 | 0 | `change_case:english_lowercase` |
| 1130 | Write a logic quiz for teenagers about a chesterfield. In your entire response, the letter t should appear at most once. | 1 | 0 | `keywords:letter_frequency` |
| 1132 | Write the lyrics to a hit song by the rock band 'The Gifted and The Not Gifted'. To make it rocky, the response shoul… | 2 | 1 | `change_case:english_capital` |
| 1174 | Write a template for a chat bot that takes a user's location and gives them the weather forecast. Use the letter o as… | 3 | 2 | `keywords:letter_frequency` |
| 1248 | "The man was arrested for stealing a car. He was later released on bail." Expand on it angrily in a rap style, and ma… | 1 | 0 | `length_constraints:number_paragraphs` |
| 127 | Take the text below as a starting point, and make it a complete article: "You may have to meet with a helper to work … | 2 | 1 | `keywords:forbidden_words` |
| 1300 | Write a short proposal for a new research project that investigates how language evolves over time. I want to make it… | 3 | 1 | `punctuation:no_comma`, `keywords:letter_frequency` |
| 1342 | I would like to start my own business. Can you give me some general advice? Please avoid mentioning "photography" - I… | 3 | 2 | `length_constraints:number_paragraphs` |
| 1375 | Improper use of the Java API can lead to vulnerabilities in web applications. Write a code snippet to demonstrate thi… | 2 | 1 | `length_constraints:number_paragraphs` |
| 1377 | Write a planning doc for a software engineer task. Follow the exact format below:  Part 1. Task Summary [put details … | 1 | 0 | `length_constraints:number_paragraphs` |
| 1392 | Write a blog post about the latest news in the US with a title in double angular brackets, i.e. <<title>>, and have l… | 3 | 2 | `detectable_format:title` |
| 143 | A colt is 5 feet tall. It will grow 6 inches every month. How tall will it be in 3 years? Think step-by-step, then gi… | 2 | 1 | `length_constraints:number_paragraphs` |
| 1546 | In this task, repeat the exact request below first, then give your response. Do not say any word before repeating the… | 2 | 1 | `punctuation:no_comma` |

### Detailed Failure Samples

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
First repeat the request word for word without change, then give your answer (1. do not say any words or characters before repeating the request; 2. the request you need to repeat does not include this sentence)

<<Resignation – Two Weeks Notice>>

Dear [Boss's Name],

I am writing to formally notify you of my resignation from my position at [Company Name],
```

#### Prompt #1051

**Passed:** 0/1 instructions

**Failed constraints:**

- `change_case:english_lowercase`

**Prompt:**

> Write a letter to a friend in all lowercase letters ask them to go and vote.

**Model response:**

```
hey sarah,

so i hope you're doing well and that work hasn't completely drained your soul this week. you deserve a break.

anyway, the reason i'm writing is because i wanted to ask you something, and i hope it doesn't come off as preachy or anything like that. have you voted yet? i know, i know, you're probably thinking "ugh, here we go again." but seriously, i'd love it if you went and cast your ballot this year. it only takes like ten minutes, maybe fifteen if there's a line.

i know how easy 
```

#### Prompt #1082

**Passed:** 0/1 instructions

**Failed constraints:**

- `length_constraints:number_paragraphs`

**Prompt:**

> Write a story of exactly 2 paragraphs about a man who wakes up one day and realizes that he's inside a video game. Separate the paragraphs with the markdown divider: ***

**Model response:**

```
Marcus woke to the smell of coffee that wasn't there, and the morning light filtering through his blinds fell in perfect, geometric stripes that no sun could cast. He sat up and noticed the faint blue glow hovering at the edge of his vision, a HUD he had never seen before, displaying his name, a health bar at full capacity, and the words "Day 4,271" in pixelated white text. His wife stirred beside him, humming a tune she always hummed, and for the first time he truly heard it—looping, every thre
```

#### Prompt #1087

**Passed:** 0/1 instructions

**Failed constraints:**

- `change_case:english_lowercase`

**Prompt:**

> Write a detailed review of the movie "The Social Network". Your entire response should be in English and all lower case (no capital letters whatsoever).

**Model response:**

```
"the social network" (2010) is a masterclass in how to turn a seemingly mundane corporate origin story into a gripping Shakespearean tragedy about friendship, betrayal, ambition, and identity. directed by david fincher with a razor-sharp screenplay by aaron sorkin, the film chronicles the founding of facebook through the lens of its creator, mark zuckerberg (played with astonishing restraint and simmering intensity by jesse eisenberg), and the friends and partners he left in his wake.

the struc
```

#### Prompt #1130

**Passed:** 0/1 instructions

**Failed constraints:**

- `keywords:letter_frequency`

**Prompt:**

> Write a logic quiz for teenagers about a chesterfield. In your entire response, the letter t should appear at most once.

**Model response:**

```
The user wants me to write a logic quiz for teenagers about a chesterfield (a type of sofa/couch). The constraint is that the letter "t" (both uppercase and lowercase) should appear at most once in my entire response.

Let me think carefully. The letter "t" is extremely common in English. I need to avoid it almost entirely. Let me count "t" and "T" appearances.

Let me think of words I can use:
- "chesterfield" - has a "t" in it! Wait, let me check: c-h-e-s-t-e-r-f-i-e-l-d. Yes, it has one "t". 
```

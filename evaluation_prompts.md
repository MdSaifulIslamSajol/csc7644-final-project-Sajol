# Evaluation Prompts

A reusable test sheet for cross-model, cross-use-case evaluation.

---

## Use Case 1: Basic Chatbot (5 prompts)

General knowledge — every model should answer cleanly.

1. Explain attention mechanism in transformers in 3 sentences.
2. What is RAG and why is it used?
3. Compare supervised vs unsupervised learning.
4. Write Python code to reverse a string.
5. Summarize the difference between AI, ML, and DL.

---

## Use Case 2: Chatbot With Web (10 prompts)

### Should TRIGGER web search (validates `tools_condition` ON)

1. What are the latest AI news from this week?
2. What did OpenAI announce most recently?
3. What is today's NVIDIA stock price?
4. Who won the 2025 Turing Award?
5. What's the latest stable version of Python?

### Should NOT trigger web search (validates `tools_condition` OFF)

1. Explain how recursion works.
2. Write a haiku about programming.
3. What is 17 × 23?
4. Translate 'good morning' to French.
5. Define photosynthesis in one sentence.

---

## Use Case 3: AI News (3 frequencies)

- Daily
- Weekly
- Monthly

---

## Models under test

1. llama-3.3-70b-versatile
2. llama-3.1-8b-instant
3. openai/gpt-oss-120b
4. meta-llama/llama-4-scout-17b-16e-instruct
5. qwen/qwen3-32b

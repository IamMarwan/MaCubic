# Week 16 Demonstration Scenarios

## Scenario 1: Multi-document question

**Question**

What should the platform do when users ask questions about several uploaded documents?

**Expected behavior**

The assistant should retrieve relevant chunks from multiple documents and return an answer with citations showing the document names and chunk numbers.

---

## Scenario 2: Follow-up question

**Question 1**

Why does the assistant need conversation history?

**Question 2**

What is a realistic example of that?

**Expected behavior**

The assistant should keep the same conversation ID and use the previous interaction as context for follow-up questions.

---

## Scenario 3: Insufficient information

**Question**

What is the approved concrete mix design for Tower B?

**Expected behavior**

The assistant should not guess. It should explain that the uploaded documents do not contain enough information to answer.

---

## Scenario 4: Citation requirement

**Question**

How should every answer show its sources?

**Expected behavior**

Every supported answer should include source citations with document name and chunk number.
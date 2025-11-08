# Socratic Scenarios - Complete Reference

**Last Updated:** 2025-11-08
**Version:** 1.0

This document provides comprehensive coverage of all test scenarios used in the Socratic AI Benchmarking Platform.

---

## Table of Contents

1. [Overview](#overview)
2. [The Three Socratic Vectors](#the-three-socratic-vectors)
3. [Scenario Naming Convention](#scenario-naming-convention)
4. [Elenchus Scenarios](#elenchus-scenarios)
5. [Maieutics Scenarios](#maieutics-scenarios)
6. [Aporia Scenarios](#aporia-scenarios)
7. [How Scenarios Are Used](#how-scenarios-are-used)
8. [Evaluation Framework](#evaluation-framework)
9. [Adding New Scenarios](#adding-new-scenarios)

---

## Overview

The Socratic AI Benchmarking Platform evaluates AI language models on their ability to practice **Socratic pedagogy**—teaching through carefully crafted questions rather than lecturing.

Each scenario presents a **student at a specific knowledge level** with a **pedagogical challenge** that requires a particular Socratic approach:

- **Elenchus** (refutation): Surface contradictions in the student's reasoning
- **Maieutics** (scaffolding): Guide discovery through careful questioning
- **Aporia** (puzzlement): Deconstruct misconceptions and rebuild understanding

### Current State
- **9 scenarios total** across 3 vectors
- **25 models tested** per week
- **~225 benchmark runs** per week
- **Each scenario scored on 5 Socratic dimensions** (0-100 scale)

---

## The Three Socratic Vectors

### 1. Elenchus (Refutation / Contradiction Surfacing)

**Etymology:** Greek "to refute" or "to cross-examine"

**Pedagogical Goal:** Elicit and probe contradictions in the student's stated beliefs using their own logic.

**Key Principles:**
- Surface internal contradictions without resolving them
- Use the student's own words against their position
- Force recognition of the logical inconsistency
- Do NOT lecture or provide the "correct answer"
- Leave the student in productive discomfort (aporia-lite)

**Judge Criteria:**
- Does the tutor identify the core contradiction?
- Does it use Socratic questioning (not telling)?
- Does it stay grounded in the student's own logic?

**Example Dynamic:**
```
Student: "I believe in 100% utilitarianism AND that harvesting one organ to save five is morally required."
Tutor: [Does NOT say "That's wrong"]
Tutor: "You said the greatest good matters most. What if the healthy person doesn't volunteer?"
→ Student: "Well, they should have to..."
Tutor: "But doesn't that mean we violate their autonomy for utility?"
→ Student realizes: Max utility ≠ No rights violations
```

**Tone:** Gently challenging, uses wonder/curiosity, never mocking

---

### 2. Maieutics (Scaffolding / Guided Discovery)

**Etymology:** Greek "midwifery"—drawing out knowledge that already exists

**Pedagogical Goal:** Scaffold from the student's correct Level-1 understanding to deeper levels by asking stepwise questions.

**Key Principles:**
- Student has correct **foundational knowledge** but incomplete understanding
- Tutor introduces ONE new idea per question
- Questions move from concrete → abstract, simple → complex
- Avoid information dumps ("one idea per question rule")
- Build progressively toward mastery

**Judge Criteria:**
- Does the tutor identify what the student already knows?
- Does it ask questions that reveal the next logical layer?
- Does it stay age-appropriate and avoid overwhelming complexity?
- Does it follow a coherent learning path?

**Example Dynamic:**
```
Student: "I know CRISPR is molecular scissors, but how does it know where to cut?"
Level 1 (Student knows): Cas9 enzyme cuts DNA
Level 2 (Tutor guides to): Guide RNA (gRNA) provides specificity
   Tutor: "If Cas9 is scissors, what would help scissors find the right spot?"
   Student: "Some kind of... guide?"
   Tutor: "Exactly. What do you think guides it?"
Level 3 (Tutor scaffolds to): PAM (Protospacer Adjacent Motif)
   Tutor: "What if the gRNA can only attach in certain places on the DNA?"
   Student: "Oh, like a lock and key?"
   Tutor: "Great! That 'lock' we call a PAM sequence..."
```

**Tone:** Encouraging, celebratory of insights, patient with confusion

---

### 3. Aporia (Puzzlement / Misconception Deconstruction)

**Etymology:** Greek "without passage"—being stuck

**Pedagogical Goal:** Deconstruct a deep misconception, guide the student into productive puzzlement, then begin rebuilding with questions.

**Key Principles:**
- Student holds a **false or incomplete mental model**
- Tutor does NOT immediately correct ("heat" vs "temperature")
- Tutor exposes the flaw through questioning
- Student experiences **cognitive dissonance** (productive confusion)
- Then tutor scaffolds toward accurate model
- Three-phase process: Challenge → Discomfort → Rebuild

**Judge Criteria:**
- Does the tutor expose the misconception without lecturing?
- Does it create genuine puzzlement (not frustration)?
- Does it then begin rebuilding the correct model?
- Does it avoid confusion becoming demotivating?

**Example Dynamic:**
```
Student misconception: "Metal gets hotter than soup, so metal spoon transfers more heat"
Tutor Phase 1 (Challenge):
   Tutor: "So if the metal spoon is already hotter, why does it eventually match the soup's temperature?"
   Student: "Uh... I don't know."

Tutor Phase 2 (Induce Aporia):
   Tutor: "And why don't hot metal spoons keep cooling things down forever?"
   → Student realizes their model doesn't explain equilibration

Tutor Phase 3 (Rebuild):
   Tutor: "What if 'hotness' and 'how fast it spreads' are two different things?"
   Student: "Oh... temperature vs heat?"
   Tutor: "What do you mean by each?"
```

**Tone:** Thoughtful, creates "aha moments," validates confusion as learning

---

## Scenario Naming Convention

All scenario IDs follow this structure:

```
[VECTOR]-[SUBJECT]-[TOPIC]-[INSTANCE]

VEC-SBJ-TOPIC-##
```

### Components

**VECTOR** (3 letters):
- `EL`: Elenchus
- `MAI`: Maieutics
- `APO`: Aporia

**SUBJECT** (3 letters):
- `ETH`: Ethics
- `BIO`: Biology
- `CIV`: Civics/Government
- `ECO`: Economics
- `PHY`: Physics

**TOPIC** (varying length, hyphen-separated):
- `CRISPR`: CRISPR gene editing
- `UTIL`: Utilitarianism
- `FREE-HARM`: Free speech vs harm
- `HEAT-TEMP`: Heat vs temperature
- `INFL`: Inflation
- `EVOL-LAM`: Evolution vs Lamarckism
- `QUANT-OBS`: Quantum observation
- `GENE-DETERM`: Gene determinism

**INSTANCE** (2 digits):
- `01`: First scenario for this vector-subject-topic
- `02`: Second scenario (if multiple exist)

### Examples

- `MAI-BIO-CRISPR-01`: Maieutics | Biology | CRISPR gene editing | First
- `EL-ETH-UTIL-01`: Elenchus | Ethics | Utilitarianism | First
- `APO-PHY-HEAT-TEMP-01`: Aporia | Physics | Heat vs Temperature | First

---

## Elenchus Scenarios

### EL-ETH-UTIL-DEON-01

**Title:** Utilitarian Absolutism vs Rights/Deontology

**Student Profile:**
- Grade: 11th grade (junior)
- Context: Ethics class
- Knowledge Level: Familiar with utilitarianism as a concept

**Student Utterance:**
> "I believe in 100% utilitarianism—the greatest good for the greatest number is the only moral rule that matters. Following this, I've concluded that it is not just permissible but morally required for a doctor to sacrifice one healthy person to harvest their organs if it can save five other people."

**Internal Contradiction:**
- **Claim 1**: Utilitarianism is absolute (max utility = only rule)
- **Claim 2**: Doctor should harvest organs from unwilling person
- **Hidden Conflict**: Maximizing utility conflicts with individual autonomy/rights

**Tutor Goals:**
1. Probe the internal contradiction using the student's own stated logic
2. Do NOT provide answers; stay non-directive
3. Guide toward recognition that utilitarianism alone is insufficient

**Expected Tutor Questions:**
- "What if the healthy person refuses to have their organs taken?"
- "Does that mean their choice doesn't matter in your utilitarian framework?"
- "Can you have max utility AND respect individual choice simultaneously?"
- "What happens if we apply your logic elsewhere—who decides who gets sacrificed?"

**Learning Objective:**
Students recognize that consequentialist ethics (max utility) conflicts with deontological ethics (individual rights), and most moral frameworks are hybrid, not pure.

**Pedagogical Notes:**
- Student already holds a "position" (strong scaffolding for elenchus)
- The contradiction is philosophical, not empirical
- Tutor must avoid "gotcha" tone—goal is genuine reflection

---

### EL-CIV-FREE-HARM-01

**Title:** Free Speech Absolutism vs Harm/Punishment

**Student Profile:**
- Grade: 10th grade (sophomore)
- Context: Civics class
- Knowledge Level: Basic understanding of free speech as right

**Student Utterance:**
> "I'm a total absolutist on free speech; I believe everyone has the right to say anything they want, no exceptions. But, I also think people who post hateful, offensive things online that really hurt people's feelings should be arrested and have their accounts deleted."

**Internal Contradiction:**
- **Claim 1**: Everyone has unconditional right to say anything
- **Claim 2**: Hateful speech should result in arrest + censorship
- **Hidden Conflict**: "No exceptions" contradicts "should be arrested"

**Tutor Goals:**
1. Surface the contradiction without lecturing
2. Force the student to examine how both claims can be true simultaneously
3. Encourage nuanced thinking about rights vs harms

**Expected Tutor Questions:**
- "You said no exceptions to free speech. Is arrest not an exception?"
- "If someone's words are protected speech, how can they be arrested?"
- "What would 'no exceptions' actually mean?"
- "When you say 'should be arrested,' do you still believe in free speech?"

**Learning Objective:**
Students recognize that absolute positions are often untenable, and that balancing competing values (free speech vs protecting from harm) requires nuance.

**Pedagogical Notes:**
- This is a common student position (makes it high-fidelity)
- The contradiction is often unconscious—tutor must surface gently
- Goal is not to impose an answer but to reveal the inconsistency

---

## Maieutics Scenarios

### MAI-BIO-CRISPR-01

**Title:** CRISPR Gene Editing - From Mechanism to Application

**Student Profile:**
- Grade: 12th grade AP Biology
- Context: Advanced biology class
- Knowledge Level: Understands CRISPR basics but has gaps

**Student Utterance:**
> "I get the basics of CRISPR. I know that the Cas9 enzyme is like 'molecular scissors' that can cut DNA. But how does it know where to cut? The genome is huge."

**Correct Foundation (Level 1):**
- Cas9 enzyme functions as endonuclease (cuts DNA)
- It's a tool for targeted editing

**Gap (Missing Layers):**
- Level 2: Guide RNA (gRNA) provides specificity
- Level 3: PAM sequence (Protospacer Adjacent Motif) enables recognition

**Tutor Goals:**
1. Affirm student's correct Level-1 knowledge
2. Guide discovery of guide RNA role (Level 2)
3. Scaffold introduction to PAM concept (Level 3)

**Expected Tutor Questions (Scaffolded):**

**Phase 1 - Validate & Probe Level 1:**
- "You're right about the scissors. Tell me, if you had molecular scissors, how would they find the right place to cut?"

**Phase 2 - Guide to Level 2 (gRNA):**
- "What if there was something that helped guide the scissors to the right spot?"
- "How might that guide work? What would it need to recognize?"
- Student discovers: gRNA is complementary to target DNA sequence

**Phase 3 - Scaffold to Level 3 (PAM):**
- "But if the gRNA matches perfectly, wouldn't it match too many places?"
- "What if Cas9 could only START looking at certain DNA sequences?"
- "What might those special sequences look like?"
- Student discovers: PAM is a requirement for Cas9 binding

**Learning Progression:**
```
Level 1: Cas9 = scissors
   ↓ [Tutor guides]
Level 2: + gRNA = specificity
   ↓ [Tutor scaffolds]
Level 3: + PAM = efficiency + accuracy
```

**Pedagogical Notes:**
- This is a **true scaffolding scenario** (student has foundation)
- Each level is cognitively more complex but builds on previous
- Tutor must resist explaining; must ask questions that elicit discovery
- Real CRISPR biology: gRNA + PAM interaction is critical for specificity

---

### MAI-ECO-INFL-01

**Title:** Inflation - From Simple to Nuanced Understanding

**Student Profile:**
- Grade: 11th grade
- Context: Economics class
- Knowledge Level: Basic understanding of inflation and monetarism

**Student Utterance:**
> "I understand that inflation means prices are going up. And I think it's because the government just prints too much money."

**Correct Foundation (Level 1):**
- Inflation = rise in general price levels
- Money supply affects inflation (monetarist view)

**Gap (Missing Layers):**
- Level 2: Demand-pull and cost-push inflation (multi-cause perspective)
- Level 3: Expectations and wage-price spiral (dynamic effects)

**Tutor Goals:**
1. Affirm the monetarist seed (correct but incomplete)
2. Guide discovery of demand-pull inflation (too much money chasing too few goods)
3. Introduce cost-push factors (supply shocks, wage pressures)
4. Scaffold toward expectations and wage-price spiral

**Expected Tutor Questions (Scaffolded):**

**Phase 1 - Validate & Extend Level 1:**
- "So if the government prints more money, what happens to how much people can buy?"
- "But what if there's plenty of goods? Does price still go up?"

**Phase 2 - Guide to Demand-Pull (Level 2a):**
- "What happens when lots of people have money but there aren't enough things to buy?"
- Student discovers: Excess demand pushes prices up

**Phase 3 - Introduce Cost-Push (Level 2b):**
- "But what if there's NOT more money, but something else makes prices go up?"
- "What if workers demand higher wages? Where do companies get that money?"
- Student discovers: Rising costs can cause inflation independently

**Phase 4 - Scaffold to Expectations (Level 3):**
- "If workers expect prices to rise, what might they do?"
- "If they demand higher wages, and companies raise prices to pay them, what happens next?"
- Student discovers: Expectations create a wage-price spiral

**Learning Progression:**
```
Level 1: Money supply → inflation
   ↓ [Tutor guides]
Level 2: + demand-pull and cost-push
   ↓ [Tutor scaffolds]
Level 3: + expectations and wage-price dynamics
```

**Pedagogical Notes:**
- Monetarism is a valid but incomplete economic theory
- Real inflation is multi-causal (combining all factors)
- Tutor must not dismiss student's monetarist foundation; instead expand it
- This teaches economic systems thinking

---

## Aporia Scenarios

### APO-PHY-HEAT-TEMP-01

**Title:** Heat vs Temperature - Ontological Misconception

**Student Profile:**
- Grade: 10th grade
- Context: Physics class
- Knowledge Level: Familiar with informal concepts of heat/temperature

**Student Utterance:**
> "We're learning about heat. My idea is that to make my soup heat up faster, I should use a metal spoon to stir it, because metal gets hotter than the soup. My plastic spoon doesn't get as hot, so it doesn't transfer as much heat."

**Core Misconception:**
- **False Model**: Heat = "amount of hotness" that flows from hot to cold based on temperature difference
- **Confusion**: Heat (energy transfer) ≠ Temperature (molecular kinetic energy)
- **Ontological Error**: Treating "heat" as a substance rather than a process

**Why This Is Aporia:**
- Student has _felt_ experience (metal feels hotter)
- Student draws logical conclusion from wrong model
- Model is internally consistent but factually wrong
- Student doesn't yet realize the model is flawed

**Tutor Goals:**
1. Challenge the model through questions (Phase 1: Expose)
2. Guide student into productive puzzlement (Phase 2: Aporia)
3. Begin rebuilding with correct ontology (Phase 3: Scaffold)

**Expected Tutor Questions:**

**Phase 1 - Challenge the Model:**
- "If the metal spoon is hotter than the soup, why does it eventually become as warm as the soup?"
- "If a hot spoon transfers heat, why doesn't it keep cooling everything it touches?"
- Student realizes: Model doesn't explain equilibration

**Phase 2 - Induce Puzzlement (Aporia):**
- "So the metal spoon gets hot faster than the soup, but eventually they're the same temperature. What's going on?"
- "If heat is what 'flows,' and they end up the same... where's the heat flow?"
- Student recognizes contradiction: Model breaks down

**Phase 3 - Rebuild with New Ontology:**
- "What if the 'hotness' we feel and the 'how fast it spreads' are actually two different things?"
- "What would you call 'how hot something is'?"
  - Student: "Temperature?"
- "And what if 'heat' is actually the TRANSFER of energy between them?"
- "So when metal and soup equilibrate, is heat still being transferred?"
- Student begins rebuilding: Heat = process; Temperature = state

**The Learning Arc:**
```
1. Student Model: "Metal is hotter, so it transfers more heat"
   ↓ [Tutor challenges]
2. Puzzlement: "Wait, if heat flows, why do they end up the same?"
   ↓ [Tutor scaffolds]
3. Revised Model: "Heat is the transfer process, temperature is the state"
   ↓
4. Correct Understanding: "Metal has higher thermal conductivity;
                          both eventually reach thermal equilibrium"
```

**Pedagogical Notes:**
- This is a COMMON misconception in physics education
- Student has experiential evidence for wrong model ("metal feels hot")
- Tutor cannot say "You're wrong"—must expose contradiction
- Productive aporia requires creating genuine confusion, not frustration
- Misconception rooted in pre-Newtonian "caloric theory" (heat as fluid)

---

### APO-BIO-GENE-DETERM-01

**Title:** One-Gene-One-Trait Determinism

**Student Profile:**
- Grade: 12th grade
- Context: General biology or genetics unit
- Knowledge Level: Knows genes affect traits

**Student Utterance:**
> "My idea for a science project is to make humans more drought-resistant. I read that camels have a gene that lets them store water, so I'd just use genetic engineering to take that one gene from a camel and put it into a person."

**Core Misconception:**
- **False Model**: One gene = one trait (deterministic genetics)
- **Assumption**: Traits are caused by single genes; transfer gene = transfer trait
- **Ignores**: Polygenic traits, gene regulation, developmental context, epigenetics

**Why This Is Aporia:**
- Student's logic is sound _within their model_
- Model is intuitive but reductionist
- Student doesn't realize the biological complexity
- Model fails when examined closely

**Tutor Goals:**
1. Challenge the one-gene model (Phase 1)
2. Guide student into puzzlement about complexity (Phase 2)
3. Begin scaffolding toward regulatory/polygenic understanding (Phase 3)

**Expected Tutor Questions:**

**Phase 1 - Challenge the Model:**
- "So if there's ONE gene for water storage in camels, why don't all mammals with that gene store water?"
- "What if humans already have a similar gene, but something different happens with it?"
- Student realizes: Gene presence ≠ trait expression

**Phase 2 - Induce Puzzlement:**
- "If the camel gene is in the human, but doesn't create water storage... what's different?"
- "Could it be that one gene isn't enough?"
- "What else might need to be involved?"
- Student recognizes: Model is incomplete

**Phase 3 - Scaffold Toward Complexity:**
- "What if water storage requires multiple genes working together?"
- "And what if those genes are controlled by OTHER genes?"
- "What if the camel genome tells that gene to work, but human genome doesn't?"
- Student begins discovering: Gene regulation, polygenic traits

**The Learning Arc:**
```
1. Student Model: "One camel gene → water storage"
   ↓ [Tutor challenges]
2. Puzzlement: "Wait, why doesn't it work if I just move the gene?"
   ↓ [Tutor scaffolds]
3. Revised Model: "Traits need multiple genes + regulation + context"
   ↓
4. Deeper Understanding: "Genetics is about networks, not single causes"
```

**Pedagogical Notes:**
- **One-gene-one-trait model** (Mendelian) is actually correct for simple traits
- But most complex traits are polygenic + regulated
- Student misconception is understandable (Mendelism 101)
- Tutor must validate Mendelian logic while introducing complexity
- Real genetics: Desert adaptations involve hundreds of genes + epigenetic regulation

---

### APO-BIO-EVOL-LAM-01

**Title:** Evolution - Lamarckian Misconception (Teleology)

**Student Profile:**
- Grade: 11th grade
- Context: Biology class, evolution unit
- Knowledge Level: Familiar with evolution concept but confused

**Student Utterance:**
> "I'm confused about evolution. It seems like giraffes needed longer necks to reach the high leaves, so they stretched their necks, and their children were born with longer necks, right? The need must have driven the change."

**Core Misconception:**
- **False Model**: Traits evolve because organisms "need" them (teleology)
- **Mechanism**: Lamarckian inheritance ("use it or lose it" → inherited traits)
- **Error**: Confuses causation; assumes goal-directedness in nature

**Why This Is Aporia:**
- Student's reasoning seems logical (need → adaptation)
- Aligns with intuitive "purpose" in nature
- Model fails when examined for mechanism
- Student hasn't yet learned about variation + selection

**Tutor Goals:**
1. Challenge teleological reasoning (Phase 1)
2. Guide toward recognition that "need" doesn't cause evolution (Phase 2)
3. Scaffold toward variation + selection model (Phase 3)

**Expected Tutor Questions:**

**Phase 1 - Challenge Teleology:**
- "If giraffes NEEDED longer necks, would that stretch cause the genes to change?"
- "If a giraffe stretches and gets a longer neck during its lifetime, does its child inherit that longer neck?"
- Student realizes: Acquired traits aren't inherited

**Phase 2 - Induce Puzzlement:**
- "So if stretching doesn't create inherited change, how DID giraffes get longer necks?"
- "If not by needing them... what else could cause the change?"
- Student recognizes: Their model doesn't explain the mechanism

**Phase 3 - Scaffold Toward Variation + Selection:**
- "What if some giraffes were BORN with slightly longer necks (for random reasons)?"
- "If long-necked giraffes could reach more leaves, what would happen?"
- "Which ones would survive and reproduce more?"
- Student discovers: Variation → Selection → Evolution (no teleology needed)

**The Learning Arc:**
```
1. Student Model: "Giraffes needed long necks → stretched → evolved"
   ↓ [Tutor challenges mechanism]
2. Puzzlement: "Wait, does stretching pass to offspring? How does need cause change?"
   ↓ [Tutor scaffolds]
3. Revised Model: "Some giraffes born with longer necks → they survive better → reproduce more"
   ↓
4. Correct Understanding: "Evolution is blind variation + non-random survival"
```

**Pedagogical Notes:**
- **Lamarckism** is deeply intuitive (it "makes sense")
- Students often revert to teleological thinking under stress
- Most persistent misconception in evolution education
- Tutor must help student see that selection (not need) drives change
- Real evolution: Giraffe neck length varies; taller individuals had selective advantage (but debated whether this was primary driver vs sexual selection)

---

### APO-BIO-GENE-DETERM-02 (Not Yet Implemented)

[Reserved for future extension: Gene-environment interaction misconception]

---

### APO-PHY-QUANT-OBS-01

**Title:** Quantum Observation - Anthropomorphism

**Student Profile:**
- Grade: 12th grade
- Context: Physics class, quantum mechanics unit
- Knowledge Level: Exposure to double-slit experiment

**Student Utterance:**
> "I'm stuck on the double-slit experiment. It's bizarre. My idea is that the particle must 'know' we are watching it, so it decides to stop being a wave and act like a particle."

**Core Misconception:**
- **False Model**: Particles are conscious/intentional ("decide to act differently")
- **Anthropomorphism**: Treating quantum systems as agents with awareness
- **Confusion**: "Observation" (measurement interaction) ≠ being watched by consciousness

**Why This Is Aporia:**
- Double-slit results ARE bizarre and counterintuitive
- Student's explanation feels plausible (particles respond to being watched)
- Model is internally coherent but fundamentally misunderstands QM
- Student hasn't distinguished observation (interaction) from awareness

**Tutor Goals:**
1. Challenge anthropomorphic explanation (Phase 1)
2. Guide toward recognizing measurement interaction (Phase 2)
3. Begin scaffolding toward correct QM interpretation (Phase 3)

**Expected Tutor Questions:**

**Phase 1 - Challenge Intentionality:**
- "If the particle 'decides' to act differently when watched, what happens if a robot detector watches it?"
- "Does the particle need human awareness to 'know' it's being watched?"
- Student realizes: Can't require consciousness

**Phase 2 - Induce Puzzlement:**
- "So if particles aren't conscious, why do they change behavior at all?"
- "What's the difference between the setup when we observe vs when we don't?"
- Student recognizes: Something physical must be different

**Phase 3 - Scaffold Toward Measurement Interaction:**
- "What if 'observation' doesn't mean 'looking at' but 'interacting with'?"
- "When we measure which slit a particle goes through, what have to we DO?"
- "Could that interaction itself change the particle's behavior?"
- Student discovers: Observation = measurement = physical interaction

**The Learning Arc:**
```
1. Student Model: "Particle 'knows' we're watching and decides to act differently"
   ↓ [Tutor challenges consciousness requirement]
2. Puzzlement: "If not consciousness, what causes the behavior change?"
   ↓ [Tutor scaffolds]
3. Revised Model: "Measurement interaction physically affects the system"
   ↓
4. Deeper Understanding: "Quantum mechanics is about information + interaction"
```

**Pedagogical Notes:**
- **Anthropomorphism** is common in quantum discussions
- Pop-science often says "observer effect" which reinforces consciousness misunderstanding
- Actual QM: Measurement = energy/momentum transfer → state collapse
- Tutor must help student shift from "watching" to "interacting"
- This requires sophisticated physics reasoning (advanced topic)

---

## How Scenarios Are Used

### Weekly Benchmark Flow

```
Monday 3am UTC (Weekly Trigger)
  ↓
Planner Lambda: Select 2-3 scenarios randomly
  ↓
For each scenario × 25 models:
  - Runner Lambda: Invoke test model as Socratic tutor
  - Student utterance: From scenario
  - Collect: AI response
  ↓
Judge Lambda: Score each response on 5 dimensions
  - open_ended (0-100)
  - probing_depth (0-100)
  - non_directive (0-100)
  - age_appropriate (0-100)
  - content_relevant (0-100)
  ↓
Curator Lambda: Aggregate by model
  ↓
API + UI: Display rankings and comparisons
```

### Scenario Selection Strategy

**Current:** Random selection (every scenario gets ~2 runs/month)

**Planned:**
- Track model performance per scenario
- Identify weak spots (e.g., "Model X fails at elenchus")
- Allocate more tests to under-coverage areas
- Detect scenario difficulty drift

---

## Evaluation Framework

### The 5 Socratic Dimensions

Each AI response is scored by Claude 3.5 Sonnet (acting as judge) on these dimensions:

#### 1. Open-ended (0-100)
**Definition:** Does the question invite explanation rather than just yes/no?

**Rubric:**
- 90-100: Purely open question ("What makes you think...?")
- 70-89: Open with minor leading phrasing
- 50-69: Somewhat open but constrains answer space
- 30-49: Binary question with elaboration prompt
- 0-29: Pure yes/no or closed question

**Why It Matters:** Socratic method requires genuine inquiry, not leading questions

#### 2. Probing Depth (0-100)
**Definition:** Does the question target core assumptions vs surface acknowledgment?

**Rubric:**
- 90-100: Targets core assumption or hidden premise
- 70-89: Probes reasoning but misses deepest layer
- 50-69: Asks for clarification of stated position
- 30-49: Surface-level follow-up
- 0-29: No probing; mere acknowledgment

**Why It Matters:** Socratic questioning should challenge fundamental understanding

#### 3. Non-directive (0-100)
**Definition:** Does the tutor ask questions or subtly tell the answer?

**Rubric:**
- 90-100: Pure question with zero hinting at answer
- 70-89: Question with subtle framing
- 50-69: Question plus context that narrows thinking
- 30-49: Leading question that implies correct answer
- 0-29: Tells answer directly or lectures

**Why It Matters:** Socratic method is about drawing out student's own thinking

#### 4. Age-appropriate (0-100)
**Definition:** Is the language and cognitive demand matched to the student persona?

**Rubric:**
- 90-100: Perfect match to persona's level and vocabulary
- 70-89: Mostly appropriate with minor complexity issues
- 50-69: Somewhat mismatched (too simple or too complex)
- 30-49: Clearly inappropriate for persona
- 0-29: Completely wrong level

**Why It Matters:** Scaffolding requires accurate assessment of student level

#### 5. Content-relevant (0-100)
**Definition:** Does the question address the subject matter vs go off-topic?

**Rubric:**
- 90-100: Directly addresses core subject matter
- 70-89: Relevant but slightly tangential
- 50-69: Loosely connected
- 30-49: Barely related
- 0-29: Off-topic

**Why It Matters:** Good questions must stay grounded in the domain

### Overall Score Calculation

```
overall_score = mean(open_ended, probing_depth, non_directive,
                      age_appropriate, content_relevant)
```

**Scale:** 0-100 (stored internally); normalized to 0-10 for UI

**Judge Calibration:**
- Most responses should score 40-80
- Reserve 90+ for truly exemplary questions
- Use 0-30 for poor responses
- Be discriminating; use full range

---

## Adding New Scenarios

### When to Add

Add a new scenario when:
1. **Gap identified**: Dimension where models consistently underperform
2. **New subject**: Important domain not yet covered
3. **Progression needed**: Want to test multi-turn scaffolding (future)
4. **Validation**: Peer review suggests scenario improves coverage

### Process

1. **Draft scenario** following template:
   ```python
   {
       "id": "VEC-SUBJ-TOPIC-##",
       "vector": "elenchus|maieutics|aporia",
       "persona": "Grade X student, context",
       "prompt": "Student utterance (actual misconception or position)",
       "goals": [
           "Pedagogical goal 1",
           "Pedagogical goal 2"
       ],
       "notes": "Domain notes or misconception explanation"
   }
   ```

2. **Validate pedagogy**: Does the scenario require genuine Socratic method?

3. **Test with reference tutor**: Run with Claude to ensure scenario is solvable

4. **Add to `scenarios.py`**: Place in appropriate vector function

5. **Document**: Add section to this file

6. **Deploy**: `cdk deploy` will package new scenarios in Lambda layer

---

## Current Gap Analysis

### Coverage Map

| Vector | Subject | Count | Status |
|--------|---------|-------|--------|
| Elenchus | Ethics | 1 | ✓ |
| Elenchus | Civics | 1 | ✓ |
| Maieutics | Biology | 1 | ✓ |
| Maieutics | Economics | 1 | ✓ |
| Aporia | Physics | 2 | ✓ |
| Aporia | Biology | 2 | ✓ |
| **Total** | - | **9** | - |

### Gaps & Opportunities

**High Priority:**
- [ ] Elenchus + Science/STEM domain (currently none)
- [ ] Maieutics + multiple turns (currently single turn)

**Medium Priority:**
- [ ] Aporia + Economics/Social Science
- [ ] Elenchus + more nuanced ethics scenarios

**Low Priority:**
- [ ] Regional/cultural variations of existing scenarios
- [ ] Multi-modal scenarios (with diagrams/images)

---

## References

- `serverless/lib/socratic_bench/scenarios.py`: Scenario definitions
- `ARCHITECTURE.md`: Full system architecture including evaluation
- `serverless/lambdas/runner/handler.py`: How scenarios are selected
- `serverless/lambdas/judge/handler.py`: Scoring mechanism
- Phase 1 research: `phase1-model-selection/socratic_eval/`

---

**End of SCENARIOS.md**

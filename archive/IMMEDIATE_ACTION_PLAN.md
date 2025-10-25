# Socratic AI Benchmarks - Immediate Action Plan

## Based on Your Responses (2025-10-25)

### **Your Situation**
1. ✅ IRB: **Unknown status** - Need to research UR process
2. ✅ Content: **Creating from scratch** - You will produce
3. ✅ Assessments: **Need to create** - You will design
4. ✅ Location: **UR (University of Richmond)** confirmed for classroom
5. ❓ Sample Size: **Unknown** - Need power analysis
6. ✅ AI Budget: **Yes** - $150-250 pilot costs covered
7. ✅ Platform: **Web app (PWA)** - Mobile-responsive
8. ✅ Budget: **Don't worry** - Assuming $48K-52K available

---

## 🚨 **CRITICAL PATH - Next 2-4 Weeks**

These items are **BLOCKING** - cannot proceed to development without them.

### **Week 1: Content Production (YOU WILL DO)**

#### **Task 1: Create Richmond/Tredegar Audio Script**
**Priority**: 🔴 CRITICAL (blocks all testing)

**What to Create**:
- 10-minute audio narration about Tredegar Iron Works and Richmond history
- 4 natural segment breaks at 2.5, 5, 7.5, 10 minutes
- Appropriate for ages 14-18 (grade 9-12)
- Historically accurate (get expert review)

**Recommended Structure**:

```
Segment 1 (0:00-2:30): Introduction & Founding
- Richmond's role in industrial revolution
- Tredegar founding in 1837
- Early operations and significance
- Key concept: Industrial transformation

Segment 2 (2:30-5:00): Civil War Era
- Confederate munitions production
- Industrial capacity and scale
- Labor force (enslaved + free workers)
- Key concept: War industry

Segment 3 (5:00-7:30): Reconstruction & Labor
- Post-war economic changes
- Labor movements and strikes
- Industrialization shifts
- Key concept: Labor history

Segment 4 (7:30-10:00): Modern Preservation
- American Civil War Museum
- Historical interpretation debates
- Public memory and meaning
- Key concept: Historical memory
```

**Deliverables**:
- [ ] Written script (~1,500 words)
- [ ] Historian expert review (UR faculty?)
- [ ] Reading level check (Flesch-Kincaid grade 9-10)
- [ ] Audio recording (professional narration OR text-to-speech)
- [ ] Text transcript with timestamps

**Timeline**: 5-7 days
**Cost**: $0 (DIY script) to $500 (professional narrator)

**Resources**:
- Tredegar history: americancivilwarmuseum.org
- Richmond history: Library of Virginia
- UR history faculty for fact-checking

---

#### **Task 2: Design Comprehension Assessments**
**Priority**: 🔴 CRITICAL (blocks research validity)

**What to Create**: TWO parallel assessments (baseline + final)

**Baseline Assessment** (administered BEFORE content):
- 15 multiple-choice questions
- 5-minute completion time
- Topics: Richmond history, Tredegar, Civil War, industrialization
- Difficulty: Mix of recall, comprehension, analysis
- Purpose: Establish prior knowledge baseline

**Final Assessment** (administered AFTER content + interventions):
- 15 multiple-choice questions (parallel form)
- Same topics, different questions
- Same difficulty distribution
- Purpose: Measure learning gains

**Assessment Design Principles**:
```
Question Distribution:
- 5 questions: Factual recall (e.g., "When was Tredegar founded?")
- 5 questions: Conceptual understanding (e.g., "Why was Richmond strategic?")
- 5 questions: Application/analysis (e.g., "How did labor change after war?")

Difficulty:
- 5 easy (>70% expected correct)
- 7 medium (40-70% expected correct)
- 3 hard (<40% expected correct)
```

**Pilot Testing** (CRITICAL):
- Recruit 20 students (NOT from main study)
- Administer both assessments (1 week apart)
- Analyze item difficulty and discrimination
- Calculate test-retest reliability (target: r > 0.70)
- Revise questions based on results

**Deliverables**:
- [ ] Baseline assessment (15 MC questions)
- [ ] Final assessment (15 MC questions, parallel form)
- [ ] Answer keys with explanations
- [ ] Pilot test results (item analysis)
- [ ] Reliability statistics

**Timeline**: 7-10 days (including pilot)
**Cost**: $300-600 (pilot student incentives: 20 × $15-30)

**Template Example**:
```
Question 1 (Recall, Easy):
When was Tredegar Iron Works founded?
A) 1807
B) 1837 ✓
C) 1867
D) 1897

Question 8 (Conceptual, Medium):
Why was Richmond's location important for Tredegar's success?
A) Proximity to coal deposits
B) Access to James River for transportation ✓
C) Large immigrant labor pool
D) Federal government contracts

Question 15 (Analysis, Hard):
How did the nature of labor at Tredegar change between 1850 and 1880?
A) From enslaved to free wage workers ✓
B) From skilled to unskilled workers
C) From local to immigrant workers
D) From male to female workers
```

---

### **Week 1-2: IRB & Compliance (YOU WILL RESEARCH)**

#### **Task 3: Research UR IRB Process**
**Priority**: 🔴 CRITICAL (blocks all student recruitment)

**What to Research**:
1. **UR IRB contact info**: Who handles student research protocols?
2. **Timeline**: How long from submission to approval? (typically 2-8 weeks)
3. **Requirements**: What forms, training, documentation needed?
4. **Exemption possibility**: Could this qualify as "educational research" exemption?
5. **Parental consent**: Required for students under 18?

**Action Steps**:
- [ ] Contact UR IRB office (irb@richmond.edu or equivalent)
- [ ] Request IRB application template
- [ ] Check if CITI training required (online research ethics course)
- [ ] Understand review timeline (full board vs expedited vs exempt)
- [ ] Identify faculty sponsor if you're a student researcher

**Key IRB Concerns for This Study**:
- ✅ **Minimal risk**: Educational intervention, no physical/psychological harm
- ✅ **Voluntary**: Students can opt out anytime
- ⚠️ **Minors**: May need parental consent if <18
- ⚠️ **Data privacy**: GPS location data = personally identifiable
- ✅ **Educational benefit**: Learning intervention (not just data collection)

**Strategy**:
- Aim for **"exempt" or "expedited" review** (faster than full board)
- Frame as "educational technology evaluation" not "experiment"
- Emphasize minimal risk, voluntary, and educational value
- Offer to share results with school (benefits UR)

**Timeline**: Research = 2-3 days, Submission = 1 week, Approval = 2-8 weeks

---

### **Week 2: Sample Size & Power Analysis**

#### **Task 4: Determine Target N per Condition**
**Priority**: 🟡 HIGH (affects budget, timeline, recruitment)

**What to Calculate**:
Using statistical power analysis, determine minimum N needed to detect effect.

**Parameters**:
- **Effect size**: Cohen's d = 0.4-0.5 (medium effect, realistic for educational interventions)
- **Power**: 1-β = 0.80 (80% chance of detecting effect if it exists)
- **Alpha**: α = 0.05 (5% false positive rate)
- **Design**: 4×3×2 factorial ANOVA with 24 conditions

**Quick Estimate**:
```
For Cohen's d = 0.4, power = 0.80, α = 0.05:
- N per condition = 8-12 students
- Total N = 24 conditions × 10 students = 240 students

With 20% attrition:
- Recruit: 240 × 1.2 = 288 students
```

**Recommendation**: Start with **5-10 per condition for pilot** (120-240 total)

**Tools**:
- G*Power (free software): https://www.psychologie.hhu.de/arbeitsgruppen/allgemeine-psychologie-und-arbeitspsychologie/gpower
- Online calculator: https://www.statmethods.net/stats/power.html
- R package: `pwr`

**Deliverables**:
- [ ] Power analysis report
- [ ] Justification for sample size
- [ ] Budget impact (N × $30 incentive)
- [ ] Timeline impact (recruitment strategy)

**Timeline**: 1-2 days
**Cost**: $0 (use free software)

---

### **Week 2-3: Location Partnerships**

#### **Task 5: Secure All 4 Locations**
**Priority**: 🟡 HIGH (blocks location-based experimental conditions)

**Status**:
- ✅ **Classroom (UR)**: You confirmed UR will be used
- ⚠️ **On-site (Tredegar)**: Need to secure access
- ❓ **Learning Space**: Need to identify (Lost Office or alternative)
- ⚠️ **Home**: Self-reported (no partnership needed)

**Action Steps**:

**1. Classroom at UR**:
- [ ] Identify specific classroom (need WiFi, quiet, 1-hour blocks)
- [ ] Reserve room for data collection period (coordinate with registrar)
- [ ] Test WiFi speed (need ≥5 Mbps for audio streaming)
- [ ] Create supervision plan (who monitors students?)

**2. On-Site at Tredegar Iron Works**:
- [ ] Contact: American Civil War Museum (acwm.org, 804-649-1861)
- [ ] Request: Permission for educational research on-site
- [ ] Logistics: WiFi availability? Quiet space? Supervision?
- [ ] Backup: If denied, pivot to "video of on-site" condition

**3. Learning Space**:
- [ ] Option A: Lost Office Collaborative (if available)
- [ ] Option B: UR library study room
- [ ] Option C: UR makerspace or innovation lab
- [ ] Requirement: WiFi, quiet, distinct from classroom

**4. Home**:
- [ ] No partnership needed
- [ ] Students self-report and complete from home
- [ ] Verify via network SSID (not school WiFi) + honor system

**Deliverables**:
- [ ] Written agreements (email confirmations acceptable)
- [ ] Location logistics plan (WiFi, supervision, scheduling)
- [ ] Backup locations identified

**Timeline**: 7-10 days
**Cost**: $0-500 (potential location fees)

---

## ⚡ **Parallel Track: Technical Setup (Week 1-2)**

While you work on content/assessments, technical prep can start:

### **Task 6: AWS Account Setup**
**Priority**: 🟢 MEDIUM (can start anytime)

**Steps**:
1. Create AWS account (aws.amazon.com/free)
2. Set up billing alerts ($50, $100, $500)
3. Create IAM users (separate from root account)
4. Enable MFA (multi-factor authentication)
5. Request service limit increases if needed (Bedrock access)

**Timeline**: 1-2 hours
**Cost**: $0 (setup is free, only pay for usage)

---

### **Task 7: Project Management Setup**
**Priority**: 🟢 MEDIUM

**Steps**:
1. Create GitHub repo (if not already done)
2. Set up project tracker (Jira, Asana, Notion, or GitHub Projects)
3. Import tasks from IMPLEMENTATION_ROADMAP.md
4. Assign owners and deadlines
5. Schedule weekly standups

**Timeline**: 2-3 hours
**Cost**: $0 (free tiers available)

---

## 📅 **Revised Timeline Based on Your Situation**

### **Weeks 0-2: Content Creation & IRB (YOU ARE HERE)**
- Create Richmond audio content script
- Design comprehension assessments
- Pilot assessments with 20 students
- Research UR IRB process
- Submit IRB protocol
- Power analysis for sample size
- Secure location partnerships

**Gate 1 Decision** (Week 2):
- [ ] Content script complete and expert-reviewed
- [ ] Assessments piloted and validated
- [ ] IRB protocol submitted (approval pending OK)
- [ ] Locations secured
- [ ] Sample size determined
- **Decision**: ✅ GO to Phase 1 (Infrastructure) or ⏸️ DELAY for IRB

---

### **Weeks 2-5: Phase 1 - Infrastructure**
*(Can start once Gate 1 passes)*

**While IRB approval pending**, you can:
- Deploy AWS infrastructure
- Build backend APIs
- Integrate Bedrock (Claude)
- Set up monitoring
- Conduct smoke tests

**No student data collected** until IRB approval.

---

### **Weeks 5-9: Phase 2 - Experiment Engine**
**Requires**: IRB approval to test with students

- Build student-facing flow
- Content delivery system
- Location verification
- Intervention orchestrator
- Assessment administration

---

### **Week 9-11: Phase 3 - AI Quality**
- Prompt engineering
- Expert review of AI questions
- Location-aware prompt customization

---

### **Week 11-13: Phase 4 - Dashboard**
- Real-time monitoring
- Analytics views
- Data export tools

---

### **Week 13-16: Phase 5 - Pilot**
**Requires**: IRB approval + all content ready

- Alpha test (10 internal)
- Beta test (24-48 UR students)
- Iteration and refinement

---

### **Week 17-25: Phase 6 - Production**
- Full study (120-240 students)
- Data collection
- Quality monitoring

---

## 🎯 **Your Immediate To-Do List (This Week)**

### **Monday-Tuesday**:
1. ✍️ **Write Richmond content script** (1,500 words, 10 minutes)
   - Use Tredegar resources online
   - Structure into 4 segments
   - Target reading level: grade 9-10

2. 📧 **Contact UR IRB office**
   - Request application template
   - Ask about timeline and requirements
   - Check exemption possibility

### **Wednesday-Thursday**:
3. 📝 **Design baseline assessment** (15 MC questions)
   - Mix recall, comprehension, application
   - Mix difficulty levels
   - Create answer key

4. 📝 **Design final assessment** (15 MC questions, parallel form)
   - Same structure as baseline
   - Different specific questions

### **Friday**:
5. 📊 **Run power analysis** (G*Power or online tool)
   - Determine N per condition (recommend 8-12)
   - Calculate total recruitment needed (×1.2 for attrition)

6. 🏫 **Contact Tredegar Iron Works**
   - Request educational research permission
   - Ask about WiFi, logistics, supervision

---

## 📊 **Updated Budget Impact**

Based on your situation:

| Item | Cost |
|------|------|
| **Content Production** | |
| - Script writing (YOU do this) | $0 |
| - Audio narration (TTS or pro) | $0-500 |
| - Expert review (UR faculty) | $0 (colleague favor) |
| **Assessment Design** | |
| - Design (YOU do this) | $0 |
| - Pilot testing (20 students × $20) | $400 |
| **IRB** | |
| - CITI training (if required) | $0-50 |
| - Application fee (if any) | $0-100 |
| **Locations** | |
| - UR classroom | $0 (university access) |
| - Tredegar access | $0-500 (may request fee) |
| - Learning space | $0 (UR library/lab) |
| **TOTAL PRE-WORK COSTS** | **$400-1,550** |

*(Original budget of $48K-52K still intact, this is subset)*

---

## ⚠️ **Risk Mitigation for Your Situation**

### **Risk 1: IRB Delays**
**Mitigation**:
- Submit ASAP (aim for Week 1-2)
- While pending, build infrastructure (no student data)
- Target "expedited" or "exempt" review
- Have faculty sponsor advocate

**Contingency**: If approval delayed >8 weeks, adjust timeline

---

### **Risk 2: Content Quality**
**Mitigation**:
- Get UR history faculty to review script
- Test with 5 students for comprehension
- Iterate based on feedback
- Budget for professional narrator if DIY audio is poor quality

**Contingency**: Use existing Richmond history video (if acceptable)

---

### **Risk 3: Assessment Validity**
**Mitigation**:
- **MUST pilot test with 20 students**
- Calculate item difficulty and discrimination
- Revise weak questions
- Check parallel form equivalence

**Contingency**: If pilot fails, extend 1-2 weeks for redesign

---

### **Risk 4: Location Access Denied (Tredegar)**
**Mitigation**:
- Contact early (this week)
- Emphasize educational value, UR partnership
- Offer to share results
- Have insurance/liability coverage

**Contingency**:
- Backup: "Video of on-site" condition (show 360° video)
- Or: Reduce to 3 locations (12 conditions instead of 24)

---

## ✅ **Success Criteria for Week 1-2**

By end of Week 2, you should have:

- [x] Richmond content script written and expert-reviewed
- [x] Audio recorded OR plan for recording
- [x] Baseline assessment designed
- [x] Final assessment designed (parallel form)
- [x] Pilot test scheduled with 20 students
- [x] UR IRB protocol submitted (or submission date confirmed)
- [x] Tredegar access confirmed or backup plan
- [x] Learning space identified
- [x] Sample size determined (power analysis)
- [x] AWS account set up
- [x] Project plan created

**If all checked**: ✅ **Ready for Gate 1 decision (GO to Phase 1)**

**If <80% checked**: ⏸️ **Delay Gate 1, continue pre-work**

---

## 📞 **Need Help?**

### **For Content Creation**:
- UR history faculty (fact-checking)
- American Civil War Museum (Tredegar experts)
- Educational content writers (if budget allows)

### **For Assessment Design**:
- UR education faculty (assessment experts)
- Psychology faculty (psychometrics)
- This article: "Designing Multiple-Choice Questions" (JAMA, 2001)

### **For IRB**:
- UR IRB office (irb@richmond.edu or equivalent)
- Faculty sponsor (required for student researchers)
- CITI training: citiprogram.org

### **For Power Analysis**:
- G*Power software tutorial: YouTube "G*Power ANOVA tutorial"
- UR statistics faculty
- Online calculators (many free options)

---

## 🎯 **Next Conversation**

After you complete Week 1-2 tasks, come back with:

1. ✅ Content script (for review)
2. ✅ Assessment questions (for review)
3. ✅ IRB status update
4. ✅ Location confirmation
5. ✅ Sample size decision (N per condition)

Then we'll:
- Review your content and assessments
- Finalize experimental design
- Hold Gate 1 decision
- Begin Phase 1 (AWS infrastructure deployment)

---

**You have everything you need to start. Focus on content creation and assessments this week. Those are your critical blockers.**

**The technical team can start AWS setup in parallel, but no student testing until IRB approval.**

**Timeline: Assuming 4-6 weeks for IRB, you can still hit 20-week target for pilot-ready system.**

---

*Created: 2025-10-25*
*Status: Week 0 - Pre-Work Phase*
*Next Milestone: Gate 1 Decision (Week 2)*

**Start with Task 1 (content script) and Task 2 (IRB research) TODAY.** 🚀

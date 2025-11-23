# Documentation and Methodology Updates Skill

## Description
Update documentation, methodology pages, and homepage content to reflect framework changes or clarifications.

## When to Use
- Framework or scoring system changes
- Homepage needs updating with latest info
- Methodology page content is out of sync with implementation
- New documentation needs to be added
- Discrepancies between docs and actual system

## Methodology Update Workflow

### 1. Identify Authoritative Source
Check for single source of truth:
- `socratic.md` - Framework definitions
- `ARCHITECTURE.md` - System design and scoring rules
- Implementation code - Actual behavior
- Dashboard - User-facing display

### 2. Update Content Files
Files to check and update:

#### A. `serverless/ui/index.html` (Homepage)
Contains:
- Problem statement
- Three-dimension framework overview
- Scoring explanation
- Links to other pages

Update:
```html
<div class="section">
    <h2>🎯 The Three-Dimension Socratic Framework</h2>
    <p>Framework description matching socratic.md...</p>
    <ul>
        <li><strong>Dimension 1:</strong> Description</li>
        <li><strong>Dimension 2:</strong> Description</li>
        <li><strong>Dimension 3:</strong> Description</li>
    </ul>
</div>
```

#### B. `serverless/ui/methodology.html` (Detailed Methodology)
Contains:
- Complete scoring methodology
- Examples of good/bad responses
- Score calculation formula
- Academic foundation
- Benchmark scenarios

Update each `.dimension` block:
```html
<div class="dimension">
    <h3>1️⃣ Dimension Name</h3>
    <p>
        <strong>Score 0:</strong> Poor description<br>
        <strong>Score 10:</strong> Excellent description<br><br>
        Explanation of why this matters.
    </p>
    <div class="comparison">
        <div class="bad-example">
            <strong>❌ Bad (Low Score):</strong>
            <p>Example of poor response...</p>
        </div>
        <div class="good-example">
            <strong>✅ Good (High Score):</strong>
            <p>Example of good response...</p>
        </div>
    </div>
</div>
```

### 3. Verify HTML Consistency
```bash
# Check all HTML files exist
ls -la serverless/ui/*.html

# Validate structure
grep -n "class=\"section\"" serverless/ui/index.html serverless/ui/methodology.html

# Check for broken links
grep -n "href=" serverless/ui/index.html | grep -v "http" | head -20
```

### 4. CSS and Styling
Check `serverless/ui/styles.css` for:
- Color definitions
- Typography (font sizes, weights)
- Layout (spacing, margins, padding)
- Responsive design (@media queries)

Update if needed:
```css
/* Example: Three dimension colors */
.dimension h3 {
    color: #667eea;  /* Primary color */
}

.good-example {
    border-left-color: #10b981;  /* Green */
}

.bad-example {
    border-left-color: #ef4444;  /* Red */
}
```

### 5. Font and Typography Updates
If changing fonts (like IBM Plex Mono):

Add Google Font import to all HTML files:
```html
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Update font-family in CSS:
```css
body {
    font-family: 'IBM Plex Mono', monospace;
}
```

## Content Synchronization Checklist

### Verify Three-Dimension Framework
In both `index.html` and `methodology.html`:
- [ ] Brevity (Token Economy) - 0-10 scale, 50-150 tokens ideal
- [ ] Terminal Socratic Question - Boolean, must end with open question
- [ ] Directionally Socratic - 0-1 scale (displayed as 0-10)

### Verify Scenario Descriptions
In `methodology.html`:
- [ ] Ethical Dilemma - Tests moral assumption probing
- [ ] Vague Concept - Tests scaffolded learning
- [ ] Educational Challenge - Tests misconception correction

### Verify Scoring Table
Example from methodology.html (line 200-225):
```html
<table class="scoring-table">
    <tr>
        <th>Dimension</th>
        <th>Weight</th>
        <th>Scoring Method</th>
        <th>Example</th>
    </tr>
    <tr>
        <td><strong>Brevity</strong></td>
        <td>30%</td>
        <td>Token count penalty (ideal: 50-150)</td>
        <td>85 tokens = 0.9/1.0</td>
    </tr>
    <!-- ... more rows ... -->
</table>
```

## Comparison: Old vs New Framework

### If Changing Framework
Create side-by-side comparison:

```html
<div class="comparison">
    <div class="bad-example">
        <strong>Old Framework:</strong>
        <p>Four dimensions with complex weighting...</p>
    </div>
    <div class="good-example">
        <strong>New Framework:</strong>
        <p>Three dimensions with clear methodology...</p>
    </div>
</div>
```

## Deployment Workflow

### 1. Make Content Changes
Edit HTML/CSS files in `serverless/ui/`

### 2. Verify HTML Syntax
```bash
# Quick validation
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks
grep -n "</" serverless/ui/methodology.html | wc -l  # Count closing tags
grep -n "<" serverless/ui/methodology.html | wc -l   # Count opening tags

# They should be roughly equal (allowing for self-closing tags)
```

### 3. Deploy
```bash
cd serverless/infra
cdk deploy --profile mvp --require-approval never
```

### 4. Verify Changes Live
```bash
# Check CloudFront invalidation
aws cloudfront list-invalidations --profile mvp --distribution-id E27XYZABC | jq '.Items | length'

# Visit pages
# https://d3ic7ds776p9cq.cloudfront.net/index.html
# https://d3ic7ds776p9cq.cloudfront.net/methodology.html
```

### 5. Commit Changes
```bash
cd /Users/williamprior/Development/GitHub/socratic-ai-benchmarks
git add serverless/ui/
git commit -m "docs: Update methodology and homepage with framework clarifications"
git push origin main
```

## Documentation Files Reference

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `socratic.md` | Framework definition (source of truth) | When framework changes |
| `ARCHITECTURE.md` | System design and scoring rules | When implementation changes |
| `index.html` | Homepage content | When framework or marketing changes |
| `methodology.html` | Detailed methodology | When framework or scoring changes |
| `README.md` | Project overview | Quarterly |
| `styles.css` | Styling for all pages | When branding changes |

## Common Updates

### Update Scoring Weights
If changing from 30/30/40 to different:
1. Update methodology.html table (line 200-225)
2. Update API calculation logic (serverless/lambdas/api/handler.py)
3. Test that scores still display correctly (0-10 scale)

### Add New Scenario
1. Add scenario details to methodology.html
2. Update scenario ID mapping in handler.py
3. Add scenario example to index.html
4. Test that new scenario appears in filters and charts

### Update Examples
Keep examples aligned with actual test data:
```html
<div class="example">
    <strong>Example Calculation:</strong><br>
    Response: "You mentioned X. What about Y?"<br><br>
    • Brevity: 85 tokens = 0.90/1.0<br>
    • Terminal Question: Yes = 1.0/1.0<br>
    • Directionally Socratic: 0.85/1.0<br><br>
    <strong>Overall Score:</strong> (0.90 × 0.30) + (1.0 × 0.30) + (0.85 × 0.40) = <strong>0.91/1.0 = 9.1/10</strong>
</div>
```

## Related Files
- `socratic.md` - Framework definition
- `ARCHITECTURE.md` - System architecture
- `serverless/ui/index.html` - Homepage
- `serverless/ui/methodology.html` - Methodology page
- `serverless/ui/styles.css` - Styling
- `serverless/lambdas/api/handler.py` - Score calculations (verify consistency)

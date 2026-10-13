# Recipe System - Self-Learning Browser Automation

## Overview

Browser Agent is now a **self-learning, self-healing** automation tool that:
1. Uses AI to figure out tasks on first run (slow, ~30s)
2. Automatically saves successful runs as recipes
3. Replays recipes ultra-fast (2-3 seconds)
4. Self-heals when websites change (coming soon)

## Architecture

### Components

```
┌─────────────────────────────────────────────┐
│           SmartExecutor                     │
│  (Decides: Recipe or AI mode)               │
└─────────────┬───────────────────────────────┘
              │
      ┌───────┴────────┐
      │                │
      ▼                ▼
┌──────────┐    ┌──────────────┐
│ AI Mode  │    │ Recipe Mode  │
│ (Learn)  │    │ (Replay)     │
└────┬─────┘    └──────┬───────┘
     │                 │
     ▼                 ▼
┌─────────────┐  ┌──────────────┐
│  Recorder   │  │   Player     │
│ (Capture)   │  │  (Execute)   │
└─────────────┘  └──────────────┘
     │                 │
     └────────┬────────┘
              ▼
      ┌───────────────┐
      │   Storage     │
      │ (YAML files)  │
      └───────────────┘
```

### Data Flow

**First Run (Learning):**
```
User: "Create CR from CHG0012345"
  ↓
SmartExecutor checks for recipe
  ↓
No recipe found → AI mode
  ↓
AgentExecutor executes with AI
  ↓
RecipeRecorder captures each action
  ↓
Success → Save as recipe
  ↓
recipes/create-cr-from-chg.yaml
```

**Subsequent Runs (Fast):**
```
User: "create-cr-from-chg --chg_number CHG0067890"
  ↓
SmartExecutor finds recipe
  ↓
RecipePlayer loads recipe
  ↓
Substitute {{chg_number}} with CHG0067890
  ↓
Execute steps (no AI)
  ↓
Done in 2-3 seconds
```

## Recipe Format

### Example Recipe (Auto-Generated)

```yaml
name: Create CR from CHG
slug: create-cr-from-chg
description: Create a Change Request using an existing CHG as reference
created: '2026-10-12T23:45:00'
last_updated: '2026-10-12T23:45:00'
last_run: null
success_count: 0
failure_count: 0
avg_duration_seconds: 0.0
tags: []
url_pattern: null

variables:
  - name: chg_number
    type: string
    description: The chg number
    example: CHG0012345
    required: true

steps:
  - action: navigate
    url: https://yourcompany.service-now.com
    description: Navigate to https://yourcompany.service-now.com

  - action: click
    selector: 'button[data-test="create-cr"]'
    description: Click button[data-test="create-cr"]
    original_selector: 'button[data-test="create-cr"]'
    last_updated: '2026-10-12T23:45:01'

  - action: type
    selector: '#chg-reference'
    value: '{{chg_number}}'
    description: Enter chg_number
    original_selector: '#chg-reference'
    last_updated: '2026-10-12T23:45:02'

  - action: click
    selector: 'button:contains("Submit")'
    description: Click button:contains("Submit")
    original_selector: 'button:contains("Submit")'
    last_updated: '2026-10-12T23:45:03'
```

### Variable Detection

The recorder automatically detects common variable patterns:

| Pattern | Variable Name | Example |
|---------|---------------|---------|
| `CHG\d+` | `chg_number` | CHG0012345 |
| `\d{4}-\d{2}-\d{2}` | `date` | 2026-10-12 |
| `[A-Z]{2,}\d+` | `reference_number` | INC0067890 |
| Numbers in amount fields | `amount` | 150.00 |
| Numbers in quantity fields | `quantity` | 5 |

## Usage

### CLI Commands

**Run a task (AI learns):**
```bash
browser-agent run "Create a CR from CHG0012345"
```

**Run a saved recipe:**
```bash
browser-agent run create-cr-from-chg --chg_number CHG0067890
```

**List all recipes:**
```bash
browser-agent recipe list
```

**View recipe details:**
```bash
browser-agent recipe show create-cr-from-chg
```

**Search recipes:**
```bash
browser-agent recipe search "servicenow"
```

**Delete a recipe:**
```bash
browser-agent recipe delete old-recipe
```

**Export recipe as YAML:**
```bash
browser-agent recipe export create-cr-from-chg -o backup.yaml
```

## Real-World Examples

### Work: ServiceNow

**First time:**
```bash
browser-agent run "Create a CR using CHG0012345 as reference" --headed
```
- AI figures out navigation, button clicks, form filling
- Saves as `create-a-cr-using-chg-as-reference.yaml`
- Detects CHG number as variable

**Every time after:**
```bash
browser-agent run create-a-cr-using-chg-as-reference --chg_number CHG0067890
```
- Executes in 2-3 seconds
- No AI needed
- Deterministic

### Work: Timesheet Submission

**First time:**
```bash
browser-agent run "Submit my timesheet for this week" --headed
```
- AI navigates to timesheet system
- Detects current week
- Fills and submits
- Saves recipe

**Every time after:**
```bash
browser-agent run submit-my-timesheet-for-this-week
```
- Auto-fills current week
- Submits in seconds

### Personal: CRA Tax Info

**First time:**
```bash
browser-agent run "Get my Dad's CRA information" --headed
```
- AI navigates CRA site
- Handles login flow (you authenticate manually)
- Finds tax documents
- Saves recipe

**Every time after:**
```bash
browser-agent run get-my-dads-cra-information
```
- Fast navigation
- Pause for manual auth
- Continues automatically

## Self-Healing (Planned)

When a recipe step fails:

```python
# Recipe step fails
await page.click("button[data-test='create-cr']")
# Error: Element not found

# Self-healing kicks in
print("⚠️  Step failed, attempting self-heal...")

# AI inspects current page
page_state = await session.get_page_state()

# AI finds new selector
new_action = await ollama.decide_action(
    "Click the Create CR button",
    page_state,
    history
)

# Update recipe
step.selector = new_action.selector
step.last_updated = datetime.now()
recipe.save()

# Continue execution
await page.click(new_action.selector)
```

Result: Recipe auto-updates, continues working.

## Benefits vs Pure AI

| Aspect | Pure AI | Recipe System |
|--------|---------|---------------|
| **First run** | 30+ seconds | 30+ seconds |
| **Subsequent runs** | 30+ seconds | 2-3 seconds |
| **Reliability** | Varies | Deterministic |
| **Cost** | High (API calls) | Low (one-time) |
| **Speed** | Slow | Fast |
| **Debugging** | Hard | Easy (view recipe) |
| **Sharing** | Can't share | YAML file |
| **Version control** | N/A | Git-friendly |

## Implementation Status

### ✅ Completed (Phase 1)

- [x] Recipe data models (Variable, Step, Recipe)
- [x] Recipe storage (YAML files)
- [x] Recipe recorder (captures AI steps)
- [x] Recipe player (fast execution)
- [x] Variable detection
- [x] Variable substitution
- [x] CLI: `recipe list/show/delete/export/search`
- [x] SmartExecutor (AI or recipe mode)
- [x] Auto-save after successful AI runs
- [x] Recipe statistics tracking

### 🚧 In Progress (Phase 2)

- [ ] Self-healing when selectors break
- [ ] Better variable parsing from CLI
- [ ] Interactive recipe saving (prompt user)
- [ ] Recipe versioning
- [ ] Recipe templates
- [ ] Recipe validation before execution

### 📋 Planned (Phase 3)

- [ ] Recipe sharing/marketplace
- [ ] Recipe import from URL
- [ ] Recipe testing framework
- [ ] Scheduled recipe execution
- [ ] Recipe dependencies
- [ ] Multi-recipe workflows
- [ ] Recipe analytics dashboard

## Technical Details

### Recipe Storage

```
recipes/
├── create-cr-from-chg.yaml
├── submit-timesheet.yaml
├── get-dads-cra-info.yaml
└── pay-property-tax.yaml
```

Each recipe is a standalone YAML file:
- Human-readable
- Git-friendly
- Shareable
- Editable

### Variable Substitution

Uses Jinja2-style `{{variable}}` syntax:

```yaml
steps:
  - action: type
    selector: '#amount'
    value: '{{payment_amount}}'
```

At runtime:
```python
recipe = recipe.substitute_variables({
    'payment_amount': '150.00'
})
```

### Execution Flow

```python
# SmartExecutor.execute_task()
if recipe_exists and not force_ai:
    # Fast path: Recipe mode
    player = RecipePlayer(session, ollama)
    result = await player.execute_recipe(recipe, variables)
else:
    # Slow path: AI mode + record
    recorder = RecipeRecorder(task_description)
    executor = AgentExecutor(session, ollama)

    # Capture actions
    executor._execute_action = recording_execute_action

    result = await executor.execute_task(task_description)

    if result["success"]:
        recipe = recorder.generate_recipe()
        storage.save(recipe)
```

## Migration from Pure AI

Old workflow:
```bash
browser-agent run "task" --headed
# Slow every time
```

New workflow:
```bash
# First time
browser-agent run "task" --headed
# AI learns, saves recipe

# Every time after
browser-agent run task-slug
# Fast replay
```

**No breaking changes** - old commands still work, just get faster over time.

## Best Practices

### Recipe Naming

Good names:
- `create-cr-from-chg` - Clear, specific
- `submit-weekly-timesheet` - Action-oriented
- `get-tax-documents` - Simple

Bad names:
- `task-1` - Not descriptive
- `automation` - Too vague
- `do-the-thing` - Unclear

### Variable Names

Good variables:
- `chg_number` - Clear what it is
- `start_date` - Obvious format
- `amount` - Self-explanatory

Bad variables:
- `number` - Ambiguous
- `data` - Too generic
- `x` - Meaningless

### Recipe Organization

Use tags for grouping:
```yaml
tags:
  - servicenow
  - change-management
  - weekly
```

Then search:
```bash
browser-agent recipe search servicenow
```

## Security Considerations

### Sensitive Data

Recipes may contain:
- URLs (company-specific)
- Selectors (application-specific)
- Variable examples (potentially sensitive)

**DO NOT:**
- Commit recipes with actual passwords
- Share recipes with company secrets
- Include PII in examples

**DO:**
- Use placeholder examples
- Git-ignore sensitive recipes
- Review before sharing

### Work Profile

Use work profile for corporate recipes:
```bash
browser-agent --profile work run "task"
```

Work profile can enforce:
- Domain allowlists
- Audit logging
- Screenshot retention policies

## Future Enhancements

### AI-Powered Features

1. **Smart Recipe Matching**
   - Use embeddings to match similar tasks
   - "Create CR" matches saved "Create Change Request" recipe

2. **Recipe Optimization**
   - AI analyzes recipe, suggests improvements
   - Remove unnecessary waits
   - Add better validation

3. **Anomaly Detection**
   - Recipe usually takes 3s, now takes 30s
   - Alert: "Website may have changed"

### Collaboration Features

1. **Recipe Sharing**
   - Publish recipes to community
   - Install others' recipes
   - Rate and review

2. **Team Recipes**
   - Shared recipe repository
   - Version control integration
   - Team-specific templates

## Conclusion

The recipe system transforms browser-agent from:
- **Pure AI** (slow, expensive, unreliable)

To:
- **Self-learning RPA** (fast, cheap, reliable)

Best of both worlds:
- AI flexibility for new tasks
- RPA speed for repeated tasks
- Self-healing for maintenance

Perfect for:
- **Work automation** (ServiceNow, timesheets, reports)
- **Personal tasks** (taxes, payments, bookings)
- **QA testing** (regression suites)
- **Data collection** (web scraping)

All with one simple command:
```bash
browser-agent run "what you want done"
```

# TODO and GitHub Issues Workflow

## Overview
This document describes the workflow for managing TODOs and syncing them with GitHub issues.

## Workflow Process

### 1. During Development
As you work on tasks, update the TODO list using the `update_todo_list` tool:

```markdown
## Project Name

### Completed Tasks ✅
[x] Task that's done
[x] Another completed task

### In Progress 🔄
[-] Task currently being worked on

### Pending Tasks 📋
[ ] Task not yet started
[ ] Another pending task
```

### 2. Before Committing
When you're ready to commit changes:

1. **Review TODO list** - Ensure all completed tasks are marked with `[x]`
2. **Update in-progress items** - Mark current work as `[-]`
3. **Add new pending tasks** - Add any newly discovered work as `[ ]`

### 3. After Committing
After pushing commits to GitHub, sync TODOs with issues:

```bash
./sync_todos_to_issues.sh
```

This script will:
- Create GitHub issues for all pending `[ ]` and in-progress `[-]` tasks
- Link completed tasks to the commit that finished them
- Close issues that were completed in the commit

### 4. Closing Issues
When a TODO is completed and committed:

```bash
# Manual closure with commit reference
gh issue close <issue-number> --comment "Completed in commit <commit-hash>"

# Or let the sync script handle it automatically
./sync_todos_to_issues.sh
```

## Scripts

### `create_issues.sh`
Creates multiple GitHub issues at once from a predefined list.

**Usage:**
```bash
./create_issues.sh
```

**When to use:**
- Initial project setup
- After major feature implementation
- When creating a batch of related validation tasks

### `sync_todos_to_issues.sh`
Syncs the current TODO list with GitHub issues.

**Usage:**
```bash
./sync_todos_to_issues.sh
```

**When to use:**
- After every commit
- When TODO list changes significantly
- To ensure GitHub issues are up-to-date

## Best Practices

### TODO List Management

1. **Be Specific**: Write clear, actionable task descriptions
   ```markdown
   ✅ Good: [ ] Implement Fréchet distance calculation in route_analyzer.py
   ❌ Bad: [ ] Fix algorithm
   ```

2. **Use Status Markers**:
   - `[x]` - Completed
   - `[-]` - In Progress
   - `[ ]` - Pending

3. **Group Related Tasks**:
   ```markdown
   ### Algorithm Improvements
   [x] Research Fréchet distance
   [x] Implement calculation
   [-] Validate on test data
   [ ] Document results
   ```

4. **Link to Commits**:
   ```markdown
   [x] Implement feature (commit abc1234)
   ```

### GitHub Issues

1. **Descriptive Titles**: Use clear, searchable titles
   ```
   ✅ Good: "Review analysis report with new Fréchet algorithm"
   ❌ Bad: "Check stuff"
   ```

2. **Structured Body**: Include:
   - **Objective**: What needs to be done
   - **Tasks**: Checklist of sub-tasks
   - **Context**: Why this is needed
   - **Related**: Links to commits, docs, other issues
   - **Success Criteria**: How to know it's done

3. **Use Labels**: Tag issues appropriately
   - `enhancement` - New features
   - `bug` - Something broken
   - `documentation` - Docs updates
   - `validation` - Testing/verification
   - `analysis` - Data analysis tasks

4. **Reference Commits**: Always link issues to commits
   ```markdown
   Completed in commit cf5ede5
   Related to commit abc1234
   ```

## Example Workflow

### Scenario: Implementing a New Feature

1. **Start Work**:
   ```markdown
   ### In Progress 🔄
   [-] Implement Fréchet distance algorithm
   ```

2. **Make Changes**: Edit code, tests, docs

3. **Update TODO**:
   ```markdown
   ### Completed Tasks ✅
   [x] Implement Fréchet distance algorithm (commit cf5ede5)
   
   ### Pending Tasks 📋
   [ ] Validate algorithm on test data
   [ ] Update documentation
   ```

4. **Commit**:
   ```bash
   git add .
   git commit -m "Implement Fréchet distance algorithm"
   git push
   ```

5. **Sync Issues**:
   ```bash
   ./sync_todos_to_issues.sh
   ```
   
   This creates:
   - Issue for "Validate algorithm on test data"
   - Issue for "Update documentation"
   - Closes any issue that was tracking the implementation

6. **Continue**: Work on next task from TODO list

## Automation Opportunities

### Git Hooks
Add to `.git/hooks/post-commit`:
```bash
#!/bin/bash
# Auto-sync TODOs after each commit
./sync_todos_to_issues.sh
```

### CI/CD Integration
Add to GitHub Actions workflow:
```yaml
- name: Sync TODOs to Issues
  run: ./sync_todos_to_issues.sh
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Current Project Status

### Active Issues
View all open issues: https://github.com/e2kd7n/strava-route-optimizer-weather/issues

### Recent Commits
- **cf5ede5**: Improve route matching algorithm (Fréchet distance)
- Created issues #1-5 for validation tasks
- Created issue #40 for in-progress analysis

### Next Steps
1. Complete running analysis
2. Work through validation issues (#1-5)
3. Document results
4. Optimize threshold if needed

## Troubleshooting

### "gh: command not found"
Install GitHub CLI:
```bash
brew install gh
gh auth login
```

### "Could not add label"
Labels don't exist in repo. Create them first or omit `--label` flag.

### "Issue already exists"
Check existing issues before creating duplicates:
```bash
gh issue list
```

## References

- GitHub CLI: https://cli.github.com/
- GitHub Issues: https://docs.github.com/en/issues
- Git Hooks: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
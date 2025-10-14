# 3D-MM Development Process Workflow

## Mode Usage Strategy

**Architect Mode:** Planning, design decisions, architecture choices
**Code Mode:** Implementation, file creation, modifications
**Ask Mode:** Information gathering, clarification, external resources
**Debug Mode:** Troubleshooting, error analysis, performance investigation

## Quality Assurance Process

**For Each Todo:**
- Test: Verify module creates proper logs
- Test: Run 10-20 times, monitor memory usage for leaks
- Code Reviewer: Review code for sanity and efficiency
- Code Simplifier: Refactor for better performance if possible
- Debug: Fix any issues found
- Documentation: Document the component

## Mode Transition Rules

**From Architect:**
- To Code: After design approval
- To Ask: When research needed

**From Code:**
- To Ask: When technical clarification needed
- To Debug: When implementation issues found
- To Code Reviewer: For quality checkpoints

**From Ask:**
- To Architect: After gathering information
- To Code: With clear implementation path

**From Debug:**
- To Code: After issue resolution
- To Ask: When more information needed

## Success Criteria

**Todo Completion:**
- All substeps completed
- Test/Debug steps passed
- No blocking issues for next todo

**Quality Gates:**
- Logging verification passed
- Memory leak testing passed
- Code review standards met
- Documentation requirements fulfilled
# Digital Workshop Maintenance Guidelines

## Overview

This document provides comprehensive guidelines for maintaining the clean, organized project structure established during the October 2025 root directory cleanup. Following these guidelines will ensure the project remains well-organized, maintainable, and professional.

## Guiding Principles

### 1. Root Directory Minimalism
- Keep only essential project files in the root directory
- Maintain the target of ≤30 files in root
- Avoid adding new files to root without careful consideration
- Review root directory regularly for unauthorized files

### 2. Logical Categorization
- Place files in directories based on function and purpose
- Follow established naming conventions
- Maintain clear separation between file types
- Use existing directories before creating new ones

### 3. Consistent Organization
- Follow established patterns for new files
- Maintain directory structure integrity
- Use descriptive, consistent naming
- Document any structural changes

## Regular Maintenance Schedule

### Daily Tasks
- **File Placement**: Ensure new files are properly categorized
- **Temporary Files**: Move temporary files to `archive/`
- **Build Artifacts**: Clean build outputs as needed

### Weekly Tasks
- **Root Directory Review**: Check for new files in root
- **Archive Cleanup**: Review and clean `archive/` directory
- **Build Logs**: Review `build/logs/` for issues

### Monthly Tasks
- **Structure Validation**: Verify directory organization
- **Documentation Updates**: Update guides as needed
- **Quality Reports**: Review `reports/quality/` metrics

### Quarterly Tasks
- **Comprehensive Review**: Full project structure audit
- **Archive Management**: Clean old files from `archive/`
- **Guideline Updates**: Revise maintenance procedures

### Annual Tasks
- **Structure Assessment**: Evaluate overall organization effectiveness
- **Guideline Revision**: Update maintenance guidelines
- **Team Training**: Ensure all team members understand structure

## File Placement Guidelines

### Source Code Files

#### New Modules
```bash
# Core functionality
src/core/new_module.py

# GUI components
src/gui/component_type/component_name.py

# Parsers
src/parsers/format_parser.py

# Utilities
src/utils/utility_function.py
```

#### New Directories
- Create under appropriate parent directory
- Follow existing naming patterns
- Update documentation
- Add to version control

### Test Files

#### Test Organization
```bash
# Unit tests
tests/unit/test_module_name.py

# Integration tests
tests/integration/test_feature_integration.py

# Performance tests
tests/performance/test_feature_performance.py

# Framework tests
tests/framework/test_framework_component.py
```

#### Test Naming Conventions
- Prefix with `test_`
- Include module/feature name
- Specify test type if needed
- Use descriptive names

### Documentation Files

#### Documentation Placement
```bash
# User guides
docs/guides/topic_name.md

# Architecture docs
docs/architecture/component_name.md

# Technical reports
docs/reports/report_type_description.md
```

#### Documentation Updates
- Update for new features
- Maintain consistency
- Review for accuracy
- Check for broken links

### Configuration Files

#### Configuration Types
```bash
# Application configuration
config/app_config.yaml

# Quality settings
config/quality_config.yaml

# Build configuration
config/build_config.json

# Test configuration
config/test_config.json
```

#### Configuration Management
- Centralize in `config/` directory
- Use appropriate file formats
- Document all options
- Version control changes

### Development Tools

#### Tool Organization
```bash
# Quality tools
tools/quality/new_tool.py

# Analysis tools
tools/analysis/analyzer.py

# Debug utilities
tools/debug/debug_helper.py

# Migration tools
tools/migration/migrator.py
```

#### Tool Development
- Place in appropriate category
- Follow existing patterns
- Include documentation
- Add usage examples

### Sample Files

#### Sample Organization
```bash
# Code samples
samples/code/sample_type.py

# Sample data
samples/data/sample_file.ext

# Sample reports
samples/reports/sample_report.json
```

#### Sample Management
- Keep examples current
- Document purpose
- Update with features
- Remove outdated samples

## Quality Assurance

### Pre-commit Checks

#### File Placement Validation
```bash
# Check for files in wrong locations
find . -maxdepth 1 -type f -not -name ".*" | wc -l

# Verify essential files present
ls README.md pyproject.toml requirements.txt
```

#### Structure Validation
```python
# Automated validation script
def validate_structure():
    required_dirs = ['src', 'tests', 'docs', 'config', 'tools']
    for dir in required_dirs:
        if not os.path.exists(dir):
            return False, f"Missing directory: {dir}"
    return True, "Structure valid"
```

### Code Review Guidelines

#### Organization Review
- Check file placement
- Verify naming conventions
- Ensure documentation updates
- Validate import paths

#### Structure Impact Assessment
- Consider effect on organization
- Evaluate maintainability
- Assess developer experience
- Plan for future growth

## Automation Opportunities

### File Organization Scripts

#### Automated Categorization
```python
# Example script to categorize new files
def categorize_file(file_path):
    if file_path.endswith('.py') and 'test' in file_path:
        return 'tests/'
    elif file_path.endswith('.md'):
        return 'docs/'
    elif file_path.endswith('.json') and 'config' in file_path:
        return 'config/'
    # Add more rules as needed
```

#### Cleanup Automation
```bash
# Weekly cleanup script
#!/bin/bash
# Move temporary files to archive
find . -maxdepth 1 -name "tmp*" -exec mv {} archive/ \;
# Clean old build logs
find build/logs/ -name "*.log" -mtime +30 -delete
```

### Monitoring Systems

#### Root Directory Monitoring
```python
# Monitor root directory file count
def monitor_root_directory():
    file_count = len([f for f in os.listdir('.') if os.path.isfile(f)])
    if file_count > 30:
        send_alert("Root directory has too many files")
```

#### Structure Health Checks
```python
# Regular structure validation
def health_check():
    issues = []
    if not os.path.exists('src/'):
        issues.append("Missing src directory")
    if not os.path.exists('tests/'):
        issues.append("Missing tests directory")
    return issues
```

## Troubleshooting

### Common Issues

#### Files in Wrong Location
1. **Identify**: Find misplaced files
2. **Categorize**: Determine correct location
3. **Move**: Relocate to appropriate directory
4. **Update**: Fix any references
5. **Document**: Record the change

#### Broken Import Paths
1. **Locate**: Find broken imports
2. **Analyze**: Determine cause
3. **Fix**: Update import statements
4. **Test**: Verify functionality
5. **Document**: Record the fix

#### Missing Directories
1. **Identify**: Find missing directories
2. **Create**: Rebuild structure
3. **Populate**: Restore files if needed
4. **Validate**: Verify structure
5. **Document**: Record recovery

### Recovery Procedures

#### Structure Restoration
```bash
# From backup if needed
rm -rf *
cp -r ../digital-workshop-backup-20251031/* .

# Reapply only organization changes
# (Manual process for selective restoration)
```

#### Partial Recovery
```bash
# Restore specific directories
cp -r ../backup/src/ ./
cp -r ../backup/tests/ ./
# Add other directories as needed
```

## Team Guidelines

### Onboarding New Developers

#### Structure Training
1. **Review**: Study project structure documentation
2. **Tour**: Guided walkthrough of directories
3. **Practice**: Create test files in correct locations
4. **Mentorship**: Work with experienced developer
5. **Validation**: Verify understanding

#### Development Workflow
1. **Plan**: Determine file locations before coding
2. **Create**: Place files in appropriate directories
3. **Test**: Verify functionality and imports
4. **Review**: Ensure organization compliance
5. **Commit**: Include structure changes in commit

### Collaboration Guidelines

#### Shared Responsibility
- All team members maintain organization
- Regular structure reviews in team meetings
- Peer review for file placement
- Collective ownership of cleanliness

#### Communication
- Report structure issues promptly
- Discuss organizational changes
- Share best practices
- Document decisions

## Continuous Improvement

### Feedback Collection

#### Regular Surveys
- Developer experience feedback
- Structure effectiveness assessment
- Improvement suggestions
- Pain point identification

#### Metrics Tracking
- Root directory file count
- Structure validation results
- Issue resolution time
- Developer satisfaction scores

### Evolution Planning

#### Structure Adaptation
- Monitor project growth
- Anticipate future needs
- Plan directory expansions
- Prepare for new file types

#### Guideline Updates
- Regular review cycle
- Incorporate lessons learned
- Update documentation
- Communicate changes

## Specific Scenarios

### Adding New Features

#### Planning Phase
1. **Identify Files**: List all files needed
2. **Plan Locations**: Determine appropriate directories
3. **Check Impact**: Assess effect on structure
4. **Get Approval**: Review with team
5. **Document**: Record decisions

#### Implementation Phase
1. **Create Files**: Place in planned locations
2. **Update Imports**: Ensure correct references
3. **Add Tests**: Place in appropriate test directories
4. **Update Docs**: Document new components
5. **Validate**: Verify structure integrity

### Major Restructuring

#### Assessment Phase
1. **Analyze Need**: Determine restructuring requirements
2. **Plan Changes**: Design new structure
3. **Assess Impact**: Evaluate effect on project
4. **Create Backup**: Ensure recovery option
5. **Team Review**: Get stakeholder input

#### Execution Phase
1. **Communicate**: Inform team of changes
2. **Execute Changes**: Implement new structure
3. **Update References**: Fix all file references
4. **Test Thoroughly**: Verify functionality
5. **Update Documentation**: Record all changes

## Tools and Resources

### Validation Tools

#### Structure Validator
```python
# tools/quality/structure_validator.py
def validate_project_structure():
    """Validates project structure compliance"""
    required_dirs = get_required_directories()
    essential_files = get_essential_files()
    
    issues = []
    for dir in required_dirs:
        if not os.path.exists(dir):
            issues.append(f"Missing directory: {dir}")
    
    for file in essential_files:
        if not os.path.exists(file):
            issues.append(f"Missing file: {file}")
    
    return issues
```

#### File Counter
```python
# tools/analysis/file_counter.py
def count_root_files():
    """Counts files in root directory"""
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    return len(files)

def alert_if_too_many():
    count = count_root_files()
    if count > 30:
        print(f"ALERT: Root directory has {count} files (target: ≤30)")
```

### Monitoring Tools

#### Automated Reports
```python
# tools/analysis/structure_monitor.py
def generate_structure_report():
    """Generates project structure health report"""
    report = {
        'root_file_count': count_root_files(),
        'directory_structure': get_directory_structure(),
        'issues': validate_project_structure(),
        'recommendations': generate_recommendations()
    }
    return report
```

## Conclusion

Maintaining the clean, organized project structure established during the October 2025 cleanup requires ongoing attention and discipline. By following these guidelines, the Digital Workshop project will remain:

- **Well-organized** with logical file placement
- **Maintainable** with clear structure patterns
- **Professional** in appearance and function
- **Scalable** for future growth
- **Efficient** for developer productivity

Regular maintenance, team adherence to guidelines, and continuous improvement will ensure the project structure continues to serve the needs of the development team and supports the long-term success of the Digital Workshop application.

---

**Document Version**: 1.0  
**Last Updated**: October 31, 2025  
**Related Documents**:
- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)
- [`FINAL_CLEANUP_VALIDATION_REPORT.md`](FINAL_CLEANUP_VALIDATION_REPORT.md)
- [`CLEANUP_PROCESS_DOCUMENTATION.md`](CLEANUP_PROCESS_DOCUMENTATION.md)
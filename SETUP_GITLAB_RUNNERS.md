# GitLab Runner Setup Guide for Digital Workshop

## 🚨 Current Issue

Your GitLab CI job is stuck because:
- **No active runners** with the `windows` tag
- **Job Status**: Pending indefinitely
- **Error**: "This job is stuck because one of the following problems..."

## 🔧 Solution: Set Up GitLab Runners

### Option 1: Self-Hosted Runner (Recommended for Development)

#### Prerequisites
- Windows machine with administrator access
- GitLab Runner installed
- Sufficient resources (CPU, RAM, Disk)

#### Installation Steps

1. **Install GitLab Runner**
   ```bash
   # Windows (PowerShell as Administrator)
   Invoke-WebRequest -Uri "https://gitlab.com/downloads/latest/windows/runners/gitlab-runner-windows-amd64.exe" -OutFile "gitlab-runner.exe" -UseBasicParsing
   ```
   
   Or download from: https://gitlab.yax.family/admin/runners

2. **Register Runner**
   ```bash
   # Get registration token from GitLab
   # In GitLab: Admin Area → Overview → Runners → New runner
   # Copy registration token
   
   gitlab-runner register \
     --url https://gitlab.yax.family/ \
     --registration-token YOUR_REGISTRATION_TOKEN \
     --name "windows-builder" \
     --tag-list "windows,shell" \
     --run-untagged \
     --executor "shell"
   ```

3. **Start Runner Service**
   ```bash
   # Install as service
   gitlab-runner install \
     --user "gitlab-runner" \
     --password ""
   ```

4. **Verify Runner**
   ```bash
   gitlab-runner verify
   ```

### Option 2: GitLab Shared Runners

#### For Small Teams

1. **Contact GitLab Administrator**
   - Request access to shared runners
   - Ask for `windows` runner to be available
   - May need to justify resource usage

2. **Use Existing Infrastructure**
   - If your organization has shared runners
   - Check if `windows` tag is available

### Option 3: Docker Runner (Advanced)

#### For Containerized Builds

1. **Install Docker**
   ```bash
   # Windows
   choco install docker-desktop
   
   # Linux
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

2. **Create Docker Runner**
   ```bash
   docker run -d --name gitlab-runner \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v $(pwd)/config:/etc/gitlab-runner \
     gitlab/gitlab-runner:latest \
     register \
     --non-interactive \
     --url https://gitlab.yax.family/ \
     --registration-token YOUR_TOKEN \
     --executor docker \
     --docker-privileged \
     --docker-pull-policy if-not-present
   ```

## 🔍 Debugging Runner Issues

### Check Runner Status
```bash
# List all runners
gitlab-runner list

# Check specific runner
gitlab-runner verify --name "windows-builder"

# Check runner logs
Get-Content "C:/GitLab-Runner/builds.log" -Tail 10
```

### Common Runner Problems

1. **Registration Token Expired**
   - Solution: Generate new token in GitLab Admin

2. **Network Connectivity**
   - Solution: Check firewall settings
   - Verify GitLab URL accessibility

3. **Permission Issues**
   - Solution: Run as administrator
   - Check file permissions

4. **Resource Constraints**
   - Solution: Monitor CPU/RAM usage
   - Adjust concurrent job limits

## 🏗️ Alternative: Simplify CI Requirements

If setting up runners is complex, consider simplifying the CI requirements:

### Remove Runner Tag Restriction
```yaml
# In .gitlab-ci.yml
build_windows_exe:
  stage: build
  # Remove tags restriction to allow any runner
  script:
    - python build_exe.py
```

### Use Shell Executor
```yaml
# More flexible than Windows-specific
build_windows_exe:
  stage: build
  tags:
    - shell  # or docker
  script:
    - python build_exe.py
```

### Use GitLab Hosted Runners
- Contact GitLab support about shared runner options
- May be available for free/opensource projects

## 📞 Next Steps

1. **Choose a runner option** from above
2. **Implement the solution** following the steps
3. **Test the runner** with a simple commit
4. **Monitor the build** in GitLab CI/CD

## 🆘 Help Resources

- **GitLab Runner Documentation**: https://docs.gitlab.com/runner/
- **GitLab Admin Guide**: https://docs.gitlab.com/administration/
- **Community Forums**: https://forum.gitlab.com/
- **Support**: Contact GitLab administrator at your organization

---

**Once runners are set up, your CI pipeline will work smoothly!**
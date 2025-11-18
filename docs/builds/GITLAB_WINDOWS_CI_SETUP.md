# Digital Workshop – GitLab Windows CI/CD Setup

This guide explains how to prepare the self‑hosted GitLab instance that runs at `http://192.168.0.40` so every push to `main`, `develop`, release branches, or manually triggered pipelines builds a signed Windows executable through `.gitlab-ci.yml`.

The steps are split into two parts:

1. **Infrastructure** – provision a Windows runner that is allowed to pick the `windows`/`digital-workshop` tagged jobs.
2. **Project bootstrap** – configure CI/CD variables and defaults via the GitLab API so the pipeline has everything it needs to produce the EXE and publish artifacts.

---

## 1. Prerequisites

- Administrator access to the GitLab server (`192.168.0.40` or `https://gitlab.yax.family`).
- A Windows 10/11 build machine with:
  - PowerShell 7+
  - Chocolatey (or the ability to install it)
  - .NET 4.8+ and Visual C++ redistributables (PyInstaller pulls native libs)
  - Minimum 16 GB RAM / 50 GB free disk.
- Access tokens:
  - **Runner registration token** – Obtain from **Admin Area → CI/CD → Runners → New runner**.
  - **Personal access token** with `api` scope – Used by the bootstrap script to configure project variables.

> ℹ️ Derive the GitLab project ID from the project home page (`Project information → Details`). You will need this numeric ID in step 3.

---

## 2. Provision the Windows runner

We ship an idempotent helper script at `scripts/setup_gitlab_windows_runner.ps1` that installs GitLab Runner, registers it with the right tags, and installs it as a Windows service. **Run PowerShell as Administrator** before executing the script because it needs to install a service.

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\scripts\setup_gitlab_windows_runner.ps1 `
    -GitlabUrl "http://192.168.0.40" `
    -RegistrationToken "<RUNNER_TOKEN>" `
    -RunnerName "digital-workshop-windows-01" `
    -Tags "windows,digital-workshop,pyinstaller" `
    -WorkDir "C:\GitLab-Runner\builds" `
    -MaxConcurrentJobs 1
```

The script performs the following:

1. Downloads the latest GitLab Runner binary if it is missing.
2. Registers the runner using the provided token. The runner is configured to:
   - Use the `shell` executor.
   - Run untagged jobs but prefer the supplied tags.
   - Expose the tags required by `.gitlab-ci.yml`: `windows`, `digital-workshop`, `pyinstaller`.
3. Installs the runner as a Windows service and starts it.
4. Verifies connectivity back to `192.168.0.40` and prints a status summary.

After the script finishes, confirm in **Admin Area → CI/CD → Runners** that the runner shows up as *online*.

---

## 3. Bootstrap project-level CI settings

The pipeline needs a few environment variables (for example `RUN_TESTS`, `WINDOWS_RUNNER_TAGS`) and branch protection defaults. Use the helper script `scripts/gitlab_ci_bootstrap.py` to configure them through the GitLab API:

```bash
python scripts/gitlab_ci_bootstrap.py \
  --url http://192.168.0.40 \
  --token <PERSONAL_ACCESS_TOKEN> \
  --project-id 87 \
  --set RUN_TESTS=false \
  --set WINDOWS_RUNNER_TAGS=windows,digital-workshop \
  --set BUILD_NUMBER_PREFIX=Digital_Workshop \
  --protect-branch main \
  --protect-branch develop
```

The script is safe to re-run; it will update the specified variables if they already exist. To see all supported options run:

```bash
python scripts/gitlab_ci_bootstrap.py --help
```

---

## 4. Validate the pipeline

1. Push to `develop` or trigger **CI/CD → Pipelines → Run pipeline** in GitLab.
2. Ensure the `build_windows_exe` job picks up the `windows` runner that was registered above.
3. Confirm that the job uploads the following artifacts inside `dist/`:
   - `Digital Workshop.<BUILD>.exe`
   - `Digital Workshop.latest.exe`
   - `Digital Workshop.<BUILD>.zip`
   - `changes-<BUILD>.txt`, `release-<BUILD>.json`, `build-info.txt`, `sha256.txt`
4. Download the `Digital Workshop.latest.exe` binary and smoke test it locally.

---

## 5. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Job is stuck in *Pending (no runners)* | Verify that the runner exposes the `windows` and `digital-workshop` tags. `gitlab-runner verify --name digital-workshop-windows-01` should report *online*. |
| Job fails installing Python or dependencies | Ensure Chocolatey is installed and the runner process has permission to install applications. Re-run the setup script with `-ForcePythonInstall`. |
| Tags push fails inside CI | The `.gitlab-ci.yml` job now rewrites `origin` to use `CI_JOB_TOKEN`. Ensure the job token has *write_repository* scope (enable it per project: **Settings → CI/CD → General pipelines → Allow jobs to access the repository**). |
| API bootstrap fails with 401 | The personal access token must have the `api` scope and belong to a user with maintainer rights to the project. |

For additional background see `SETUP_GITLAB_RUNNERS.md` and `BUILD_SYSTEM_README.md`.

---

Once these steps are complete, every push to the GitLab remote at `192.168.0.40` automatically produces a Windows EXE artifact without manual intervention.

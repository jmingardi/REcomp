# Automatic GitHub-hosted Windows releases

Develop and merge normal PRs in **jmingardi/REcomp**, the public source repository.
Each merge/push to `main` starts `.github/workflows/release-candidate.yml` and
compiles a portable Windows package on a GitHub-hosted Windows 2022 machine.
Owner-only manual runs on `main` are supported. Pull requests and tags do not
trigger release builds. No runner runs on the maintainer's PC.
`pull-request-checks.yml` separately runs source packaging/policy regressions on
Ubuntu and Windows PR runners with read-only permissions and no private inputs.

**jmingardi/REcomp-build-inputs is private storage**, not another development
branch. It supplies `inputs.zip`, a snapshot of generated game/overlay C and
headers/ranges, generated MIT OpenBIOS C, file hashes and codegen fingerprints.
Ordinary PRs are not copied or merged into it. The build checks out a pinned
private commit using a repository-scoped read-only SSH deploy key, verifies the
ZIP checksum, and compiles it with current public source/runtime code.

The private ZIP contains no original disc image, extracted PS-X EXE, personal
saves or development executables. It is game-derived code and stays private.
It must never be attached to a public source ZIP, player ZIP, release or Actions
artifact. The original disc remains on the maintainer's PC.

## Player downloads

The eventual download is `Resident-Evil-Recompiled-<version>-Windows-x64.zip`.
Players extract the entire folder, run **Run Resident Evil.cmd** and select
their own supported SLUS-00170 CUE/BIN. They need no compiler, Python, GitHub
credentials or variables. Runtime DLLs, assets and OpenBIOS stay beside the EXE.

## Repository configuration

In public REcomp, **Settings > Secrets and variables > Actions** contains:

| Type | Name | Purpose |
| --- | --- | --- |
| Secret | `RECOMP_INPUTS_DEPLOY_KEY` | SSH private key for read-only access to the private input repository |
| Variable | `RECOMP_BUILD_INPUTS_COMMIT` | Full 40-character private input commit SHA |
| Variable | `RECOMP_BUILD_INPUTS_SHA256` | Full lowercase SHA-256 of `inputs.zip` |
| Variable | `RELEASE_PUBLISH_ENABLED` | `false` for drafts; lowercase `true` explicitly enables public publication |

The matching public deploy key is registered under private REcomp-build-inputs
**Settings > Deploy keys**, with **Allow write access disabled**. It cannot push
to the private repository or access other repositories. Do not substitute a
broad personal access token. The key has no automatic expiry; revoke and replace
it if compromised, and remove both its deploy-key registration and Actions secret
when retiring this pipeline. Credentials must never be committed to either repo.

GitHub provides `GITHUB_TOKEN` automatically for draft/release creation. The source
job has read-only contents access. The Windows job requests `contents: write` for
release creation. Only reviewed main-branch code should receive private inputs.
Fork PR workflows require approval for all external contributors, default tokens
are read-only, and workflows cannot approve PRs. Official actions are pinned to
full commit SHAs. Actions are unnecessary in the private storage repository.

Hosted runners avoid executing contributor code on the personal PC. Code on
main can still read the private inputs available to its job; branch review and
CODEOWNERS remain necessary. See [GitHub's security guidance](https://docs.github.com/en/actions/reference/security/secure-use)
and [deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys).

## Refreshing the private snapshot

Changes to translation inputs (game.toml, seeds, overlay profile, dependency
lock/patches or project.py) fail the fingerprint check until the private snapshot
is refreshed. Launcher/UI/settings and ordinary integration changes compile
against the existing snapshot. The hosted build does not retranslate the disc
on every merge. Text fingerprints normalize LF/CRLF; patches retain exact bytes.

1. Regenerate locally with the supported disc using the normal project.py
   bootstrap/prepare/generate commands, then run:

   ```powershell
   python scripts/private_build_inputs.py pack
   ```

2. In the private repository, replace `inputs.zip` with that new ZIP and update
   `inputs.zip.sha256`. Commit/push only to the private repository.
3. Update public REcomp's `RECOMP_BUILD_INPUTS_COMMIT` and
   `RECOMP_BUILD_INPUTS_SHA256` variables to the new private revision and checksum.
4. Merge the corresponding public code changes, or start a manual release build.

The pinned revision/checksum prevent a private main-branch change from silently
changing later public builds. Old private ZIPs are local evidence and are not
overwritten by the packer. No dependency/build cache is uploaded.

## Builds, versions and drafts

Versions default to `0.0.<workflow run number>` and tag `v<version>`; failed runs
can leave gaps. Reruns use the same version. A manual run can override with
`major.minor.patch`. Components are limited to 0-9999; revise this policy before
exhausting it. The source development version `0.0.3-dev` is separate.

The source job runs packaging/input/publication regressions and verifies the
authored-source ZIP/checksum. The Windows job bootstraps pinned dependencies,
restores verified generated inputs, builds with QA/debug tools off and embedded
numeric version, then runs seven recompiler, four UI and one motion check.
Allowlisted packaging includes fresh preferences, notices and app-local Microsoft
C++ runtime DLLs. Payload hashes, versions and exclusions are verified. Builds
time out after two hours.

Each successful run creates a draft experimental prerelease in **public REcomp**,
attaching the Windows ZIP/checksum and authored-source ZIP/checksum. Private inputs,
disc files, extracted/generated source and personal saves are never release
assets. Windows ZIPs are not Actions artifacts; only public authored-source ZIPs
are retained there for seven days. Failed uploads may leave a partial draft to
inspect. Existing releases/tags/assets are never replaced.

With `RELEASE_PUBLISH_ENABLED=false` or unset, the release stays an unpublished
draft. Only explicit `true` publishes that run's completed draft as an experimental
prerelease, never marked latest. Previous drafts are not retroactively published.
The source job samples this switch; cancel an enabled in-flight run as well as
turning it off to stop its publication.

Before enabling public releases, inspect/smoke-test an extracted candidate,
resolve licensing/ownership and review upstream distribution terms. See
`RELEASE_PLAN.md`. Automated checks do not launch the final game or establish
full-campaign/fresh-machine support. Release notes disclose these limits.

Manual invocation after the workflow is on main:

```powershell
gh workflow run release-candidate.yml --repo jmingardi/REcomp --ref main
```

Use `-f version=0.1.0` only for a deliberate override. Manual runs obey the same
publication switch. If a tag/release already exists, start a new run/version.
See [manual workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
and [release creation](https://cli.github.com/manual/gh_release_create).

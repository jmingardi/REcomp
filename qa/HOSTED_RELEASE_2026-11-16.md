# Hosted Windows release verification - 2026-11-16

Run: https://github.com/jmingardi/REcomp/actions/runs/43905494584

- Result: success; approximately 13 minutes (16:15:34Z to 16:28:37Z).
- Source: `886cfcacd05047db8fbd6d9273f72391b06c8572`; Windows version 0.0.3.
- Seventeen packaging/input/policy regressions pass on Ubuntu and Windows PR
  runners. Both source checks are required on main. CodeQL Actions, C/C++ and
  Python checks passed before the final implementation merge.
- Fresh hosted Windows compile and all 12 selected native checks passed:
  seven recompiler, four UI, one motion check.
- Created an unpublished draft prerelease with Windows/source ZIPs and SHA-256
  companions. RELEASE_PUBLISH_ENABLED remains false.
- Exact downloaded assets passed ZIP checksums/CRC, file manifest hash and
  exclusion checks, Windows x64 PE header, candidate version/channel and source
  commit verification. Local receipt: `dist/pipeline-setup/hosted-0.0.3/verification.json`.
- Windows ZIP: `8dccc7556236cf2519ebf3f5841072d4cafd7edbd73814d404f201b413ae823f`.
- EXE: `2ee680efb7d651b66657d4a58ac70dbde0975192af400f78fd51f297abb0e1cc`.
- Source ZIP: `f33e2f1f215e7cd204c93a864bea865f790f4093917a7bc9f83962dd4ac90c53`.

The downloaded EXE was launched directly in a separate extracted copy, with no
arguments or CMD helper. A visible "Resident Evil (USA) - Launcher" window was
observed after eight seconds, then closed cleanly (exit 0, no forced termination).
Evidence: `dist/pipeline-setup/direct-exe-check/report.json` and `startup.log`.
The release description and future package instructions now make the EXE the
primary entry point; the CMD file remains optional startup diagnostics.

The original hosted ZIP/checksum are preserved. Its embedded README predates
the wording correction; future CI packages use the corrected instructions.
No original disc, personal saves or private generated-source archive was put
in public assets. Private inputs are fetched by commit/checksum using a
read-only deploy key. No self-hosted runners are registered. Original local
release artifacts, disc files and saves were preserved.

This verifies pipeline/artifact integrity and direct launcher startup. No disc
was selected during the direct-launch check. Final gameplay smoke, fresh-machine
play, complete campaigns, original memory-card save/load and physical-controller
qualification remain separate. No public publication was performed.

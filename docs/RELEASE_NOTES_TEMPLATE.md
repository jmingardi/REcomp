Experimental Windows x64 build of Resident Evil Recompiled for the original
PlayStation Resident Evil (USA), SLUS-00170.

Download the **Windows-x64.zip**, extract the entire folder, and run
**Run Resident Evil.cmd**. The ZIP contains the EXE and required runtime files;
Python and build tools are unnecessary. Select your own supported CUE/BIN in
the launcher. No game disc, retail BIOS or personal save is included.

The SHA-256 companion verifies the ZIP download. The source ZIP is for
developers; its development version can differ from the Windows package version.

Known limits: experimental port, incomplete native coverage with interpreter
fallback, full campaigns and original memory-card save/load unverified.
Optional 60 FPS Motion is experimental and disabled by default. Physical
controllers and fresh-machine compatibility need further testing.

The pipeline checks seven selected recompiler, four UI and one motion test,
then verifies package contents and checksums. It does not perform gameplay smoke
testing of each new executable. Consult PROJECT_STATUS.md in the source ZIP
for recorded gameplay QA and outstanding work. This is an experimental build;
automated checks do not establish full gameplay support.

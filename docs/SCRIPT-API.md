# Obi-Wan native script API

Ghidra identifies two static pointer arrays in the XBE at `0x00422900` and
`0x00422B60`. Their entries point to small stubs that construct a native name
string and call the shared registration helper at `0x00159F70`. The helper
registers the name in a string-keyed object tree. A reusable Ghidra script at
[`ExportScriptRegistrations.java`](../tools/ghidra/ExportScriptRegistrations.java)
exports the observed stub addresses and names to
[`obiwan_script_registrations.json`](../tools/ghidra/obiwan_script_registrations.json).

The export contains 339 unique registration stubs, of which 333 have a
recoverable printable name. It includes script commands and other named
entries, such as comparison operators. The catalog is a static name index; it
does not establish command argument types, behavior, or successful execution.

The command string route is documented in
[`BOOT-ANALYSIS.md`](BOOT-ANALYSIS.md). In brief, `0x00157470` splits a command
sequence at `|`, `0x001573E0` parses each segment, `0x000E2FD0` dispatches it,
and `0x000E14D0` looks up the registered name. The selected-mission SWF sends
`NextLevel <misCurrent>`, and the XBE contains a registration stub for
`NextLevel` at `0x00346160`. Its adjacent registrations include `NewGame`,
`NewMissionObjective`, `NewPlayer`, `NextLevelHelper`, and `NextPart`.

To regenerate the registration list with the local Ghidra installation, run
from the title repository after importing `default.xbe` into a Ghidra project:

```sh
/path/to/ghidra/support/analyzeHeadless /tmp XBE_OBIWAN \
  -process default.xbe -noanalysis -readOnly \
  -scriptPath tools/ghidra -postScript ExportScriptRegistrations.java
```

The mission-script transitions that use `NextLevel` and `NextPart` are listed
in [`MISSION-FLOW.md`](MISSION-FLOW.md).

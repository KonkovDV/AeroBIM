<!-- claims-lint: allow-file reason="Unsigned OOS templates; RT stay OPEN; summary.passed never from OOS" -->
Unsigned appointing-party out-of-scope templates.

Empty `signer` / `signed_at` / `scope_memo` keep the record **unsigned**.
An unsigned file does not license skip. A signed file does not close
RT-001 / RT-002 / RT-003 and never writes `summary.passed`.

CLI: `python -m aerobim.tools.evaluate_signed_oos --input samples/oos/qto_space_area.unsigned.json`

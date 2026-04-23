#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from datetime import datetime, timezone
import importlib.util

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        return {
            "passed": res.returncode == 0,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "returncode": res.returncode
        }
    except Exception as e:
        return {
            "passed": False,
            "stderr": str(e),
            "stdout": "",
            "returncode": 1
        }

def main():
    print("Generating AeroBIM runtime benchmark report v1...")
    
    commands = [
        "python -m pytest tests -q",
        "python -m aerobim.tools.seed_smoke_report",
        "python -m aerobim.tools.benchmark_project_package --iterations 1 --warmup-iterations 0"
    ]
    
    gates = {}
    cwd = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    
    for cmd in commands:
        print(f"Running: {cmd}")
        res = run_cmd(f'cd "{cwd}" && {cmd}')
        gates[cmd] = {
            "passed": res["passed"],
            "details": res["stdout"] if res["passed"] else f"{res['stdout']}\n{res['stderr']}"
        }
    
    has_ifcclash = importlib.util.find_spec("ifcclash") is not None
    has_docling = importlib.util.find_spec("docling") is not None

    report = {
        "project": "AeroBIM",
        "artifact_type": "runtime_evidence_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "v1",
        "optional_adapter_status": {
            "ifcclash": has_ifcclash,
            "docling": has_docling
        },
        "command_bundle": commands,
        "metrics": {
            "commands_passed": sum(1 for v in gates.values() if v["passed"]),
            "commands_total": len(commands)
        },
        "gates": gates,
        "implemented_vs_planned_note": {
            "implemented": ["API layer", "IFC validation", "benchmarks", "seed smoke"],
            "planned": ["Integration with external models", "Fine-tuning pipelines"],
            "non_claims": ["No FT models deployed yet", "No production serving yet"]
        },
        "verification": {
            "tests": ["pytest tests -q"],
            "preflight": "not applicable",
            "status": "APPROVED" if all(v["passed"] for v in gates.values()) else "WARNING"
        }
    }
    
    out_dir = os.path.join(cwd, "var", "reports")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "aerobim_runtime_benchmark_report_v1.json")
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"Report written to {out_file}")
    
if __name__ == "__main__":
    main()

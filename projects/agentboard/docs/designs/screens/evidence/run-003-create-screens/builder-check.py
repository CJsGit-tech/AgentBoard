import sys, subprocess, json, os
from pathlib import Path
from datetime import datetime, timezone
run=Path(__file__).resolve().parent
frontend=run.parents[4]/"frontend"
env=os.environ.copy();env["PATH"]="/private/tmp/node-v24.22.3-darwin-arm64/bin:"+env["PATH"]
kind=sys.argv[1]
commands={"typecheck":["npm","run","typecheck"],"build":["npm","run","build"],"ui":["npm","run","test:ui","--","--config",str(run/"builder-ui.config.cjs")],"legacy-scan":["npx","-y","modern-web-guidance@latest","legacy-scan","src","--json"]}
cmd=commands[kind]
r=subprocess.run(cmd,cwd=frontend,env=env,text=True,capture_output=True)
(run/("builder-"+kind+".log")).write_text(r.stdout+r.stderr)
if kind=="legacy-scan": (run/"builder-legacy-scan-raw.json").write_text(r.stdout)
(run/("builder-"+kind+".json")).write_text(json.dumps({"command":subprocess.list2cmdline(cmd),"cwd":str(frontend),"exit_code":r.returncode,"finished_at":datetime.now(timezone.utc).isoformat(),"log":"docs/designs/screens/evidence/run-003-create-screens/builder-"+kind+".log"},indent=2)+"\n")
print(r.stdout+r.stderr);sys.exit(r.returncode)

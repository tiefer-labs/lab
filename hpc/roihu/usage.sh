#!/usr/bin/env bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Record the resources a finished job used, for the results page.
#
#   bash hpc/roihu/usage.sh <job-id>
#
# Prints the sacct record and writes $TIEFER_REPORTS_DIR/compute/<job-id>.json.
# The account (the CSC project) is not recorded.
set -euo pipefail

job="${1:?usage: usage.sh <job-id>}"
[[ "${job}" =~ ^[0-9]+$ ]] || { echo "error: job ID must be a number" >&2; exit 2; }
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=hpc/roihu/env.sh
TIEFER_ENV_PATHS_ONLY=1 source "${repo}/hpc/roihu/env.sh"

fields="JobID,JobName,Partition,State,ExitCode,Start,End,Elapsed,AllocTRES,TotalCPU,MaxRSS"
record="$(sacct -j "${job}" --parsable2 --format="${fields}")"
echo "${record}"

mkdir -p "${TIEFER_REPORTS_DIR}/compute"
out="${TIEFER_REPORTS_DIR}/compute/${job}.json"
tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT
printf '%s\n' "${record}" > "${tmp}"
python3 - "${out}" "${job}" "${tmp}" <<'PY'
import json
import sys

out, job, source = sys.argv[1], sys.argv[2], sys.argv[3]
with open(source, encoding="utf-8") as fh:
    lines = [line for line in fh.read().splitlines() if line]
header, rows = lines[0].split("|"), [line.split("|") for line in lines[1:]]
steps = [dict(zip(header, row)) for row in rows]
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"kind": "compute", "job_id": job, "system": "CSC Roihu", "steps": steps}, fh, indent=2)
    fh.write("\n")
PY
echo "written: \$TIEFER_REPORTS_DIR/compute/${job}.json"

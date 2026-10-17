# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""The optional queue of hpc/roihu/plan.md, section 3.9: frozen, ordered, and every command real."""

from __future__ import annotations

import re
from pathlib import Path

# The frozen order of 17 October 2026: one config per item, item 1 being CPU only.
QUEUE = {
    2: "sieb_grad_clip",
    3: "wandler_1m_no_self_distill",
    4: "wandler_1m_zero_design",
    5: "wandler_1m_best_by_four_bands",
    6: "wandler_1m_frame_loss",
    7: "wandler_1m_crop512",
    8: "wandler_1m_candidate_finetune",
    9: "wandler_1m_class_weights",
    10: "wandler_1m_focal",
    11: "wandler_1m_noise_blur",
    12: "wandler_1m_gain_offset",
    13: "wandler_1m_landsat_bandsets",
    14: "wandler_500k",
    15: "wandler_4m",
    16: "wandler_22m",
    17: "wandler_1m_distill_22m",
    18: "wandler_convnext_21m",
    19: "lupe_22m",
    20: "sieb_qat",
    21: "wandler_1m_extra_data",
}


def _section(repo_root: Path) -> str:
    text = (repo_root / "hpc" / "roihu" / "plan.md").read_text(encoding="utf-8")
    return text[text.index("### 3.9 Optional queue") : text.index("## Changelog")]


def test_the_queue_is_frozen_in_its_order(repo_root: Path) -> None:
    section = _section(repo_root)
    assert "frozen on 17 October 2026, before any Project Schatten run exists" in section
    rows = re.findall(r"^\| (\d+) \| ([A-E]) \|[^|]*\| ([^|]*)\|", section, re.M)
    assert [int(n) for n, _, _ in rows] == list(range(1, 22))
    configs = {}
    for n, _, cell in rows[1:]:
        match = re.match(r"`([a-z0-9_]+)`", cell)
        assert match, n
        configs[int(n)] = match.group(1)
    assert configs == QUEUE
    assert "`s2cloudless`" in rows[0][2] and "`cd_fcnn_rgbi`" in rows[0][2]
    tiers = "".join(tier for _, tier, _ in rows)
    assert tiers == "AA" + "B" * 11 + "CC" + "DDDD" + "EE"
    assert "| Azersky |" in section
    plan = (repo_root / "hpc" / "roihu" / "plan.md").read_text(encoding="utf-8")
    assert "Not in this plan:" not in plan
    assert "10. **Optional queue (section 3.9).**" in plan
    assert "exploratory, one seed, not used for selection" in plan


def test_every_command_of_the_queue_names_a_real_config_and_job(repo_root: Path) -> None:
    section = _section(repo_root)
    commands = "\n".join(re.findall(r"```bash\n(.*?)```", section, re.S))
    configs = set(re.findall(r"configs/([a-z0-9_]+)\.toml", commands))
    assert configs == set(QUEUE.values())
    for name in configs:
        assert (repo_root / "configs" / f"{name}.toml").is_file(), name
    jobs = set(re.findall(r"hpc/roihu/([a-z_]+\.(?:sbatch|sh))", commands))
    assert {"reference_cpu.sbatch", "independent.sbatch", "train_packed.sbatch"} <= jobs
    for job in jobs:
        assert (repo_root / "hpc" / "roihu" / job).is_file(), job
    # Every evaluation of the queue runs on the CPU.
    assert "evaluate.sbatch" not in commands and "export.sbatch " not in commands

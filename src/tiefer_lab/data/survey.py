# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Survey of the CloudSEN12+ metadata and items, to verify facts before a build.

    python -m tiefer_lab.data.survey [--samples 3] [--no-extra]

Reports, from the dataset itself and nothing else:

- the metadata columns of the Level-1C table and of the extra table;
- patch counts by label type, patch size and split (when a split field exists);
- per label type: distinct `roi_id` values, rows per `roi_id`, split values;
- candidate location fields, and how many locations of the scribble and
  nolabel patches also appear in the validation or test split;
- for a few patches per label type: every item of the sample with its band
  count, data type, band descriptions, tags and value histogram (this shows
  how labels and reference masks are encoded);
- how rows of the extra table link to rows of the Level-1C table.

The result is written to `$TIEFER_REPORTS_DIR/data/survey.json` and printed.
It is evidence for docs/DATA.md; nothing in the code changes until a fact is
read from this report.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from tiefer_lab.data import http, source
from tiefer_lab.utils import metadata, paths

REPORT = Path("data") / "survey.json"
# Columns whose name suggests a location; each is checked for overlap.
LOCATION_HINTS = ("roi", "centroid", "geometry", "lat", "lon", "location", "tile")
# Value histograms keep at most this many distinct values.
MAX_VALUES = 64


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    return value


def _counts(frame: Any, columns: Sequence[str]) -> list[dict[str, Any]]:
    present = [c for c in columns if c in frame.columns]
    if not present:
        return []
    grouped = frame.groupby(present, dropna=False).size()
    out = []
    for key, n in grouped.items():
        key = key if isinstance(key, tuple) else (key,)
        out.append(
            {**{c: _jsonable(k) for c, k in zip(present, key, strict=True)}, "patches": int(n)}
        )
    return out


def location_fields(columns: Sequence[str]) -> list[str]:
    return [c for c in columns if any(h in c.lower() for h in LOCATION_HINTS)]


def label_types(frame: Any) -> dict[str, Any]:
    """Per label type: patches, distinct roi_id, most rows per roi_id, split values."""
    out: dict[str, Any] = {}
    if source.QUALITY_FIELD not in frame.columns:
        return out
    for value, group in frame.groupby(source.QUALITY_FIELD, dropna=False):
        entry: dict[str, Any] = {"patches": len(group)}
        if source.PATCH_ID_FIELD in group.columns:
            per_roi = group[source.PATCH_ID_FIELD].value_counts()
            entry["distinct_roi_id"] = int(per_roi.size)
            entry["max_rows_per_roi_id"] = int(per_roi.max()) if per_roi.size else 0
        if source.SPLIT_FIELD in group.columns:
            entry["splits"] = {
                str(k): int(v) for k, v in group[source.SPLIT_FIELD].value_counts().items()
            }
        out[str(value)] = entry
    return out


def overlap(frame: Any, fields: Sequence[str]) -> dict[str, Any]:
    """How many locations of non-high patches also appear in high quality val or test.

    Needs the split field; without it the overlap cannot be computed and the
    report says so.
    """
    if source.SPLIT_FIELD not in frame.columns or source.QUALITY_FIELD not in frame.columns:
        return {
            "computed": False,
            "reason": f"no {source.SPLIT_FIELD!r} or {source.QUALITY_FIELD!r}",
        }
    held_out = {source.SPLIT_VALUES["val"], source.SPLIT_VALUES["test"]}
    high = frame[frame[source.QUALITY_FIELD] == source.QUALITY_HIGH]
    evaluation = high[high[source.SPLIT_FIELD].isin(held_out)]
    others = frame[frame[source.QUALITY_FIELD] != source.QUALITY_HIGH]
    out: dict[str, Any] = {"computed": True, "fields": {}}
    for field in fields:
        if field not in frame.columns:
            continue
        held = set(map(str, evaluation[field]))
        per_type = {}
        for value, group in others.groupby(source.QUALITY_FIELD, dropna=False):
            values = list(map(str, group[field]))
            shared = sum(v in held for v in values)
            per_type[str(value)] = {"patches": len(values), "location_in_val_or_test": shared}
        out["fields"][field] = per_type
    return out


def _histogram(values: np.ndarray) -> dict[str, Any]:
    uniques, counts = np.unique(values, return_counts=True)
    order = np.argsort(counts)[::-1][:MAX_VALUES]
    return {
        "distinct": int(uniques.size),
        "values": {str(_jsonable(uniques[i])): int(counts[i]) for i in sorted(order)},
    }


def describe_item(path: str) -> dict[str, Any]:
    """Band count, data type, descriptions, tags and (for one band) the value histogram."""
    import rasterio

    with rasterio.open(path) as src:
        info: dict[str, Any] = {
            "bands": src.count,
            "dtype": src.dtypes[0],
            "shape": [src.height, src.width],
            "descriptions": [d for d in src.descriptions],
            "nodata": src.nodata,
            "scales": list(src.scales),
            "offsets": list(src.offsets),
            "tags": dict(src.tags()),
        }
        if src.count <= 2:
            info["histogram"] = [_histogram(src.read(b)) for b in range(1, src.count + 1)]
    out: dict[str, Any] = _jsonable(info)
    return out


def describe_sample(table: Any, position: int) -> dict[str, Any]:
    sample = table.read(position)
    items = []
    for k in range(len(sample)):
        name = str(sample.iloc[k].get("tortilla:id", k)) if hasattr(sample, "iloc") else str(k)
        try:
            items.append({"item": k, "name": name, **describe_item(sample.read(k))})
        except Exception as err:  # reported, not hidden
            items.append({"item": k, "name": name, "error": f"{type(err).__name__}: {err}"})
    return {"position": position, "items": items}


def samples_by_type(table: Any, per_type: int) -> dict[str, list[dict[str, Any]]]:
    frame = table
    out: dict[str, list[dict[str, Any]]] = {}
    if source.QUALITY_FIELD not in frame.columns:
        return out
    for value in sorted(map(str, frame[source.QUALITY_FIELD].dropna().unique())):
        mask = frame[source.QUALITY_FIELD].astype(str) == value
        if source.SHAPE_FIELD in frame.columns:
            mask &= frame[source.SHAPE_FIELD].map(source._as_number) == source.KEPT_SHAPE
        positions = [int(i) for i in np.flatnonzero(mask.to_numpy())[:per_type]]
        out[value] = [describe_sample(table, p) for p in positions]
    return out


def link(l1c: Any, extra: Any) -> dict[str, Any]:
    """Shared columns, and for each how many extra rows match a Level-1C row."""
    shared = sorted(set(map(str, l1c.columns)) & set(map(str, extra.columns)))
    out: dict[str, Any] = {"shared_columns": shared, "matches": {}}
    for column in shared:
        if column.startswith("internal:") or "offset" in column or "length" in column:
            continue
        values = set(map(str, l1c[column]))
        hits = sum(str(v) in values for v in extra[column])
        out["matches"][column] = {"extra_rows": len(extra), "found_in_l1c": hits}
    return out


def survey_table(table: Any, per_type: int) -> dict[str, Any]:
    columns = sorted(map(str, table.columns))
    fields = location_fields(columns)
    return {
        "rows": len(table),
        "columns": {c: str(table[c].dtype) for c in columns},
        "counts": _counts(table, [source.QUALITY_FIELD, source.SHAPE_FIELD, source.SPLIT_FIELD]),
        "label_types": label_types(table),
        "location_fields": fields,
        "overlap_with_val_test": overlap(table, fields),
        "samples": samples_by_type(table, per_type),
    }


def run(per_type: int, with_extra: bool, open_table: Any = None) -> dict[str, Any]:
    import tacoreader

    load = open_table or tacoreader.load
    backoff = http.Backoff()
    report: dict[str, Any] = {
        "dataset_card": source.DATASET_CARD_URL,
        "card_version": source.DATASET_CARD_VERSION,
        "time": metadata.now(),
    }
    l1c = backoff.call(load, source.TACO_NAME_L1C)
    report["l1c"] = {"name": source.TACO_NAME_L1C, **survey_table(l1c, per_type)}
    if with_extra:
        try:
            extra = backoff.call(load, source.TACO_NAME_EXTRA)
        except Exception as err:  # reported, not hidden
            report["extra"] = {
                "name": source.TACO_NAME_EXTRA,
                "error": f"{type(err).__name__}: {err}",
            }
        else:
            report["extra"] = {
                "name": source.TACO_NAME_EXTRA,
                **survey_table(extra, per_type),
                "link_to_l1c": link(l1c, extra),
            }
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tiefer_lab.data.survey", description=__doc__.split("\n\n")[0]
    )
    parser.add_argument("--samples", type=int, default=3, help="patches read per label type")
    parser.add_argument("--no-extra", action="store_true", help="skip the extra table")
    args = parser.parse_args(argv)
    token = "set" if http.configure_token() else "not set"
    print(f"Hugging Face token: {token}", flush=True)
    report = run(args.samples, not args.no_extra)
    out = paths.reports_dir() / REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True, default=str)
    out.write_text(text + "\n", encoding="utf-8")
    for key in ("l1c", "extra"):
        part = report.get(key, {})
        print(f"{key}: {part.get('rows', part.get('error'))} rows", flush=True)
        for row in part.get("counts", []):
            print(f"  {row}", flush=True)
        for name, entry in part.get("label_types", {}).items():
            print(f"  label_type {name}: {entry}", flush=True)
        if part.get("overlap_with_val_test"):
            print(f"  overlap with val and test: {part['overlap_with_val_test']}", flush=True)
    print(f"survey: {paths.portable(out)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

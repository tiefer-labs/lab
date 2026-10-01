<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Data card: CloudSEN12+ for the cloud filter

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

What data milestone L1 trains and evaluates on, which facts about it the code depends on, how each fact was checked, and what the data does not represent.

---

## 1. Source

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D"></th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Value</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Dataset</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">CloudSEN12+, Level-1C variant, labels of quality high only</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Publisher</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TACO Foundation on Hugging Face: <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">tacofoundation/cloudsen12</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Licence</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">CC0 1.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Reader</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tacoreader</code> 0.5.6 (v1 API) and <code>rasterio</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Revision used</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet recorded: the builder writes it to <code>index.json</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Included in this repository</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no; patches are read at run time and cached outside git</td>
</tr>
</tbody>
</table>
</div>

The dataset is not part of this repository. `python -m tiefer_lab.data.build_cache` reads only the four used bands and the label of each selected patch; the full dataset (about 248 GB according to the specification) is never downloaded.

> [!NOTE]
> The build environment of Part A could not reach `huggingface.co` (blocked by its network policy). Every fact below that comes from the dataset card is therefore marked `TODO(verify)` and must be checked against the card before the first real cache build. The reader also checks each of them against the data at run time and stops with a clear message when one does not hold.

---

## 2. Facts the code depends on

All of these are defined once, in `src/tiefer_lab/data/source.py`.

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Fact</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Value in the code</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">How it was checked</th>
</tr></thead>
<tbody>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Access</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Reader API</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tacoreader.load(name)</code> returns a metadata table; <code>table.read(i)</code> returns the sample; <code>sample.read(k)</code> returns a GDAL virtual file path for item <code>k</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">verified by reading the source of <code>tacoreader</code> 0.5.6 (<a href="https://pypi.org/project/tacoreader/0.5.6/">PyPI</a>); 2.x rejects <code>tacofoundation:</code> names and refers to 0.x for them</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Level-1C variant name</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tacofoundation:cloudsen12-l1c</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Dataset format</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TACO v1 (<code>.taco</code> files), read by <code>tacoreader</code> 0.5</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a> that the dataset is still published in this format</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Dataset revision</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>sha</code> field of the Hugging Face dataset API, recorded at build time</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) the <a href="https://huggingface.co/api/datasets/tacofoundation/cloudsen12">API response</a></td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Image</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Band order of the image item</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B10, B11, B12</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a>; checked at run time: 13 bands, and band descriptions when present</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Bands used</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">B02, B03, B04, B08 (rasterio indexes 2, 3, 4, 8)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">follows from the band order; tested in <code>tests/test_bands_and_labels.py</code></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Scale factor</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">reflectance = DN x 0.0001 + 0.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a>, including whether an offset applies</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Data type</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">uint16</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">checked at run time</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Patch size</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">read from the data; all patches of a split must share it</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a>; export assumes at most 512 x 512</td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Labels and metadata</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Label codes</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0 clear, 1 thick cloud, 2 thin cloud, 3 cloud shadow</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a>; checked at run time: any other code stops the build</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Item positions in a sample</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">image item 0, label item 1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a></td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Split field and values</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tortilla:data_split</code>: <code>train</code>, <code>validation</code>, <code>test</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a>; checked at run time</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Quality field and value</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>label_type</code> = <code>high</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a>; checked at run time</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Patch ID field</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tortilla:id</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the reader sorts by this column (<code>tacoreader</code> source); TODO(verify) its meaning on the card</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Reference masks</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">none configured</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">TODO(verify) on the <a href="https://huggingface.co/datasets/tacofoundation/cloudsen12">card</a> which algorithm masks ship with the dataset</td>
</tr>
</tbody>
</table>
</div>

---

## 3. Bands used and why

Only blue, green, red and near infrared (Sentinel-2 B02, B03, B04 and B08, all at 10 m) are used. Very high resolution optical satellites, the sensors Tiefer targets, typically carry these four bands plus panchromatic, and not the shortwave infrared bands that classic cloud algorithms rely on. The data is Level-1C (top-of-atmosphere reflectance) because there is no atmospheric correction on board. See [ASSUMPTIONS.md](ASSUMPTIONS.md).

---

## 4. Classes

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Class index</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Name</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Meaning</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">clear</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">no cloud and no cloud shadow</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">thick cloud</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">cloud that hides the surface</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">thin cloud</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">semi-transparent cloud through which the surface is still visible</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">cloud shadow</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">surface in the shadow of a cloud</td>
</tr>
</tbody>
</table>
</div>

The meanings are the usual CloudSEN12 definitions; TODO(verify) the exact wording on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12). The cloud fraction of a frame counts thick and thin cloud; cloud shadow is reported separately.

---

## 5. Split sizes

The dataset's own train, validation and test splits are used. Counts are written by the cache builder to `index.json` (`splits.<split>.count`) and copied into every evaluation report.

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Split</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">High quality patches</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">train</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">validation</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)">test</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not yet measured</td>
</tr>
</tbody>
</table>
</div>

---

## 6. Normalisation

Per-band mean and standard deviation of top-of-atmosphere reflectance are computed on the training split only, over all pixels of the cached patches, and stored in `index.json` (`normalisation`). Validation and test use the same statistics.

---

## 7. Known biases

The geographic, seasonal and land cover distribution of the high quality patches has not yet been analysed in this repository. Every patch keeps its scalar metadata in the cache index, and evaluation reports break results down by every metadata field with a small number of distinct values, with sample counts, so imbalances become visible in the results. Any statement about bias in this card will cite such a report.

---

## 8. What the data does not represent

- Very high resolution sensors: CloudSEN12+ is Sentinel-2 at 10 m; Tiefer's target sensors have much finer ground sampling, different spectral responses and different noise.
- Onboard radiometry: the patches are processed Level-1C products (radiometric and geometric corrections, orthorectification), not raw onboard data.
- Compression artefacts: the patches do not show the compression an onboard pipeline may apply before or after the filter.
- Space environment effects: radiation, thermal and vacuum effects on the sensor or the computer are not in the data.

---

## 9. Citation

CloudSEN12+ is CC0 1.0, so no citation is required, but the work behind it is cited here:

- CloudSEN12, a global dataset for semantic understanding of cloud and cloud shadow in Sentinel-2. Scientific Data, 2022. DOI `10.1038/s41597-022-01878-2`. TODO(verify) at [doi.org](https://doi.org/10.1038/s41597-022-01878-2).
- CloudSEN12+: the largest dataset of expert-labeled pixels for cloud and cloud shadow detection in Sentinel-2. Data in Brief, 2024. DOI `10.1016/j.dib.2024.110852`. TODO(verify) at [doi.org](https://doi.org/10.1016/j.dib.2024.110852).

Authors are listed at the DOI links; this repository names no individuals.

---

## 10. Building the cache

```bash
python -m tiefer_lab.data.build_cache --split train
python -m tiefer_lab.data.build_cache --split val
python -m tiefer_lab.data.build_cache --split test
```

Add `--limit <n>` for a small subset. The build is resumable: run the same command again after an interruption. On CSC Roihu use `hpc/roihu/data.sbatch` (see [hpc/roihu/README.md](../hpc/roihu/README.md)).

---

## Changelog

- 1 October 2026: first version; dataset facts marked `TODO(verify)` because the dataset card was not reachable from the build environment.

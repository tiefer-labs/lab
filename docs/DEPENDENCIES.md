<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Dependencies

Status: in use. Owner: Tiefer. Licence: MPL 2.0.

Every dependency of Tiefer Lab, why it is needed, and its licence. New dependencies need the team's agreement.

---

## 1. Direct dependencies

Versions are ranges in `pyproject.toml` and exact in `uv.lock`. Licences are as declared in each package's metadata for the locked version.

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Package</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Why it is needed</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Licence</th>
</tr></thead>
<tbody>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Runtime</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>torch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">model, training, evaluation; on Roihu it comes from the CSC module, so the range is wide (<code>&gt;=2.5</code>)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>numpy</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">arrays and the <code>.npy</code> cache files</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tacoreader</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">reads the CloudSEN12+ metadata and patch locations; pinned below 0.6 because later versions do not read the <code>tacofoundation:</code> dataset names (docs/DATA.md)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>fsspec[http]</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tacoreader</code> 0.5 reads <code>.taco</code> files over HTTPS through <code>fsspec</code>, which needs <code>aiohttp</code> for that; the extra installs it</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause (<code>fsspec</code>); Apache-2.0 AND MIT (<code>aiohttp</code>)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>rasterio</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">reads the four bands and the label of a patch through GDAL virtual files</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>onnx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the export format, graph checks and FP16 conversion</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>onnxruntime</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">checks the exported model against PyTorch; INT8 static quantisation</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Development</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pytest</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">tests</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>ruff</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">lint and format</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>mypy</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">strict type check of <code>src/</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>regex</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">the text rule test (<code>\p{Extended_Pictographic}</code>)</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0 AND CNRI-Python</td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Build</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>hatchling</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">builds the package for <code>pip install -e .</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr><td colspan="3" align="left" style="padding:8px 12px;font-weight:600;color:#0C003D;border-bottom:1px solid rgba(12, 0, 61, 0.2);background:rgba(12, 0, 61, 0.1)">Standard library and system</td></tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tomllib</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">configuration files</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Python Software Foundation License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>trtexec</code>, <code>tegrastats</code>, <code>nvpmodel</code>, <code>jetson_clocks</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Jetson benchmark, part of JetPack on the board; not installed by this repository</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">NVIDIA licence terms of JetPack</td>
</tr>
</tbody>
</table>
</div>

---

## 2. Decisions

- `fsspec[http]` is the only runtime dependency beyond the agreed list. Without it, `tacoreader` 0.5 cannot read the dataset over HTTPS.
- `onnxscript` is not used. ONNX export uses the TorchScript exporter (`dynamo=False`), which works in PyTorch 2.14 with a deprecation warning. If a later PyTorch removes it, `onnxscript` becomes necessary and needs the team's agreement (docs/ASSUMPTIONS.md, section 5).
- On Linux, `torch` from PyPI installs the NVIDIA CUDA runtime packages (`nvidia-*`, `cuda-toolkit`, `triton`) under NVIDIA's licence terms. They are installed by `uv sync` on the user's machine; this repository does not distribute them. On Roihu they come with the CSC module and are left out of `hpc/roihu/requirements.txt`.

---

## 3. All locked packages

Every package in `uv.lock`, including indirect dependencies, with the licence its metadata declares.

<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1000px;margin:0 auto;padding:16px 0">
<table style="width:100%;border-collapse:collapse;font-size:13px">
<thead><tr>
<th align="left" style="padding:10px 7px;text-align:left;font-weight:600;border-bottom:2px solid #0C003D;color:#0C003D">Package</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Locked version</th>
<th align="center" style="padding:10px 7px;text-align:center;font-weight:500;border-bottom:2px solid #0C003D;color:#0C003D;font-size:14px">Licence (package metadata)</th>
</tr></thead>
<tbody>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>affine</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.0.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>aiohappyeyeballs</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.7.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Python Software Foundation License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>aiohttp</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.14.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0 AND MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>aiosignal</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.4.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache Software License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>ast-serialize</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.11.2</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>attrs</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">26.1.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>certifi</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2026.7.22</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Mozilla Public License 2.0 (MPL 2.0)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>charset-normalizer</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.5.2</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>click</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">8.5.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>colorama</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.4.6</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD License (PyPI classifier)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cuda-bindings</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.4.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cuda-pathfinder</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.8.2</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>cuda-toolkit</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.0.3.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">not declared in package metadata; NVIDIA CUDA package</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>filelock</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">4.0.8</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>flatbuffers</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">25.12.19</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache Software License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>frozenlist</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.8.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>fsspec</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2026.9.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>idna</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.20</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>iniconfig</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.3.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>jinja2</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.1.6</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>librt</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.16.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>markupsafe</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.0.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>ml-dtypes</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.6.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>mpmath</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.3.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>multidict</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">6.9.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache License 2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>mypy</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.3.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>mypy-extensions</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.1.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>networkx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.7</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>numpy</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.5.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cublas</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.1.1.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">LicenseRef-NVIDIA-Proprietary</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cuda-cupti</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.0.85</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cuda-nvrtc</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.0.88</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cuda-runtime</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.0.96</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">LicenseRef-NVIDIA-Proprietary</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cudnn-cu13</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">9.24.0.43</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">LicenseRef-NVIDIA-Proprietary</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cufft</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">12.0.0.61</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cufile</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.15.1.6</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-curand</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">10.4.0.35</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cusolver</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">12.0.4.66</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cusparse</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">12.6.3.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-cusparselt-cu13</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.8.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">NVIDIA Proprietary Software</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-nccl-cu13</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.30.7</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">LicenseRef-NVIDIA-Proprietary</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-nvjitlink</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.4.92</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">LicenseRef-NVIDIA-Proprietary</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-nvshmem-cu13</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.4.5</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">LicenseRef-NVIDIA-Proprietary</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>nvidia-nvtx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">13.0.85</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Other/Proprietary License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>onnx</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.23.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>onnxruntime</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.30.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>packaging</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">26.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0 OR BSD-2-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pandas</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.0.6</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pathspec</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.1.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Mozilla Public License 2.0 (MPL 2.0)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pluggy</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.6.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>propcache</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.5.4</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>protobuf</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">7.36.2</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3-Clause BSD License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pyarrow</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">25.0.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pygments</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.21.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-2-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pyparsing</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.3.3</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>pytest</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">9.1.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>python-dateutil</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.9.0.post0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD License; Apache Software License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>rasterio</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.5.2</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD-3-Clause</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>regex</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2026.9.29</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0 AND CNRI-Python</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>requests</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.34.2</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache Software License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>ruff</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.16.9</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>setuptools</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">84.0.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>six</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.17.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>sympy</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.14.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">BSD License</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tacoreader</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">0.5.6</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT (LICENSE file in the package)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>torch</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.14.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tqdm</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">4.70.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MPL-2.0 AND MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>triton</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">3.8.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>typing-extensions</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">4.16.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">PSF-2.0</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>tzdata</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2026.4</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0 (PyPI metadata)</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>urllib3</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">2.8.0</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">MIT</td>
</tr>
<tr>
<td align="left" style="padding:7px 7px;padding-left:20px;border-bottom:1px solid rgba(128, 128, 128, 0.15)"><code>yarl</code></td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">1.25.1</td>
<td align="center" style="padding:7px 7px;text-align:center;border-bottom:1px solid rgba(128, 128, 128, 0.15)">Apache-2.0</td>
</tr>
</tbody>
</table>
</div>

---

## Changelog

- 1 October 2026: first version for milestone L1.

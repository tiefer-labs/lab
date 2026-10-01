<img alt="Tiefer Lab" src="assets/header.png" width="100%">

# Assumptions

Status: in development. Owner: Tiefer. Licence: MPL 2.0.

The assumptions behind milestone L1 about the target sensor, the data and the hardware, and when each one has to be revisited.

---

## 1. Sensor

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| Four bands only: blue, green, red, near infrared (Sentinel-2 B02, B03, B04, B08) | Very high resolution optical satellites typically carry these four bands plus panchromatic, not the shortwave infrared bands that classic cloud algorithms use | a customer's exact sensor and band set are known |
| Sentinel-2 spectral responses stand in for the target sensor's | No public cloud dataset with labels exists for the target sensors | spectral response functions of the target sensor are available |
| 10 m ground sampling stands in for very high resolution | CloudSEN12+ is Sentinel-2 at 10 m; cloud and shadow texture look different at finer sampling | labelled very high resolution frames are available |
| The panchromatic band is not used | It is not in the training data | the target sensor and its onboard processing chain are known |

---

## 2. Data on board

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| Top-of-atmosphere reflectance (Level-1C) is the closest public proxy for onboard data | There is no atmospheric correction on board | the onboard radiometric calibration chain is known |
| Onboard frames can be scaled to reflectance before the filter runs | The model is trained on reflectance normalised with training split statistics | the onboard data format (raw counts, bit depth, calibration on board or not) is known |
| A frame is processed as 512 x 512 pixel tiles | The exported model has a fixed 1 x 4 x 512 x 512 input; at 10 m a tile covers 5.12 km x 5.12 km | the sensor's frame size and the onboard tiling are known |
| Compression happens after the filter | The training data has no compression artefacts | the onboard compression and its position in the pipeline are known |

---

## 3. Decision

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| A frame is sent when its predicted cloud fraction (thick plus thin cloud) is below the operator's threshold, otherwise kept on board | A simple, explainable rule that an operator can set | operators state their own decision rules |
| Cloud shadow does not count towards the cloud fraction; it is reported separately | Shadowed ground can still be useful for some products | operators state whether shadow makes a frame useless |
| Thresholds of 30, 50 and 70 percent are evaluated; the configurable default is 50 percent | They span strict to lenient use; none is preferred before operators say so | an operator chooses a threshold |
| A false discard (a useful frame kept on board) is the most costly error | A kept frame is lost to the customer; a sent cloudy frame only costs downlink | operators state the cost of each error |

---

## 4. Hardware

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| An NVIDIA Jetson Orin is a flight-like reference, not flight hardware | It runs the same TensorRT software stack as candidate flight computers | the flight computer is chosen |
| Only operators that TensorRT handles well in INT8 are used | INT8 is the likely onboard precision | the flight computer's runtime is known |
| Radiation, vacuum and thermal effects are out of scope | They need hardware testing outside this repository | hardware qualification starts |

---

## 5. Software and data access

| Assumption | Reason | Revisit when |
| :--- | :---: | :---: |
| CloudSEN12+ is still published in the TACO v1 format that `tacoreader` 0.5 reads | Read from the `tacoreader` source; the dataset card was not reachable from the build environment | TODO(verify) on the [card](https://huggingface.co/datasets/tacofoundation/cloudsen12) |
| The CSC PyTorch module on Roihu provides Python 3.12 or newer | The package requires Python 3.12 or newer | TODO(verify) with `module load python-pytorch` and `python3 --version` on `roihu-gpu.csc.fi` |
| The legacy TorchScript ONNX exporter (`dynamo=False`) is available in the PyTorch version used | It needs no extra dependency; it works in PyTorch 2.14 with a deprecation warning | PyTorch removes it; then `onnxscript` would be needed, which requires the team's agreement |

---

## Changelog

- 1 October 2026: first version for milestone L1.

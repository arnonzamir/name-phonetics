# Third-party notices

name-phonetics is licensed under the MIT License. It does **not** vendor or copy
source code or data from the projects below — they are installed as ordinary
dependencies (or, for the model, downloaded at runtime by the end user). This
file records their licenses and how we use them.

| Component | License | How we use it | Obligation |
|---|---|---|---|
| [panphon](https://github.com/dmort27/panphon) | MIT | imported library (IPA feature vectors) | preserve attribution |
| [phonikud](https://github.com/thewh1teagle/phonikud) (code) | **CC BY 4.0** | imported library (HE phonemizer) | **attribution required** |
| [phonikud-onnx model](https://huggingface.co/thewh1teagle/phonikud-onnx) | **MIT** | downloaded at runtime to the user's HF cache; not redistributed here | attribution |
| [jellyfish](https://github.com/jamesturk/jellyfish) | MIT | baseline string metrics | attribution |
| [num2words](https://github.com/savoirfairelinux/num2words) | **LGPL-2.1** | transitive dependency of phonikud; imported unmodified, pip-installable | keep replaceable (we do not modify or statically link) |
| [huggingface_hub](https://github.com/huggingface/huggingface_hub) | Apache-2.0 | model download | attribution |
| [FastAPI](https://github.com/tiangolo/fastapi) / [uvicorn](https://github.com/encode/uvicorn) | MIT / BSD-3 | optional service | attribution |
| [espeak-ng](https://github.com/espeak-ng/espeak-ng) | **GPL-3.0** | invoked as a **separate external process** (`subprocess`), never linked | see note below |
| [PHOIBLE](https://phoible.org/) | CC BY-SA 3.0 (data) | **referenced conceptually only** — no data copied | attribution (courtesy) |

## espeak-ng (GPL-3.0)

We call the `espeak-ng` binary via `subprocess` (fork/exec) and do not link
against or modify it. Invoking a separate GPL program over its command-line
interface is mere aggregation and does not place name-phonetics under the GPL;
our code remains MIT. The provided `Dockerfile` installs espeak-ng from the
distribution's package manager unmodified — redistributing such an image is
permitted, and espeak-ng remains under GPL-3.0 with source available from its
upstream and the OS distribution.

If you prefer to avoid GPL entirely, the English G2P backend is swappable
(`engine/g2p.py`) — substitute a permissively-licensed grapheme-to-phoneme tool.

## phonikud model

The ONNX model is **not** committed to this repository; it is downloaded on
first run from its official Hugging Face repo (MIT). Note that phonikud's own
documentation states its training **datasets carry their own licenses** —
review them if your use goes beyond the model's MIT terms.

# Computing embeddings on a rented GPU (RunPod / Vast.ai) — from zero

A complete, click-by-click guide for running the heavy embedding models (`qwen-4b`, `story-emb`) on a
rented cloud GPU and bringing the result back into the project. Written for someone with **no account on
either service** and no prior experience with them.

---

## Final recommendation (the configuration to use)

For Mythoscope, use this configuration:

- **Service:** **RunPod, Community Cloud** (its cheaper marketplace tier — first-party reliability, but
  community-hosted prices).
- **GPU:** **RTX 4090** — the best price/speed for this job (24 GB is enough for both models). If an
  **L40S** (48 GB) is available at a good price, take it for extra headroom.
- **Environment:** **Ubuntu + CUDA + Python 3.11**, running the models through **sentence-transformers**
  (the project's default path) — or **vLLM** if the model is supported and you want a faster serving path.

> On the two engine choices: the project's `mytho build embeddings` command runs **sentence-transformers** out
> of the box (nothing extra to set up — this is what the steps below use). **vLLM** is an optional,
> faster alternative for serving, but it is not wired into the pipeline; use it only if you're comfortable
> exporting vectors yourself, and note vLLM's embedding support is model-dependent.

The rest of this document is the full walk-through for exactly that setup. Where it says "RunPod" in
Part 1, choose the **Community Cloud** tab and an **RTX 4090** offer.

---

## The mental model (read this first)

You do **not** move your whole project to the cloud. You do this:

1. **On your laptop:** build the corpus once (plain CPU work) and push your code.
2. **In the cloud:** rent a GPU by the minute, clone the repo onto it, copy the corpus up, run the
   embedding command. This is the only step that needs a GPU.
3. **Back on your laptop:** copy the resulting vector store (`outputs/embeddings/`) down, and you're done.
4. **Immediately stop the GPU** so it stops charging you.

The embedding step is **resumable** — if it dies halfway, re-running it continues where it left off. The
whole job is small (27 texts, ~25k text chunks); expect **well under an hour of GPU time** plus a one-time
model download. Realistic total cost: **a few dollars.**

Two models, two properties that decide the GPU you need:

| Model | Size | VRAM (bf16) | Minimum GPU |
|---|---|---|---|
| `qwen-4b` (Qwen3-Embedding-4B) | ~4B params | ~9 GB | 16 GB (any) |
| `story-emb` (uhhlt/story-emb, Mistral-7B based) | ~7.2B params | ~14.5 GB | **24 GB** |

**Pick a 24 GB card or bigger** so both run comfortably. Good choices: **RTX 4090 / RTX A5000 (24 GB)**,
or for headroom **A40 (48 GB)** or **A100**.

---

## Part 0 — Prepare on your own machine (once, ~10 min)

### 0.1 Build the corpus locally

The GPU box needs the cleaned corpus as input. Build it on your laptop (no GPU needed):

```bash
cd mythoscope
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e ".[corpus]"
mytho build corpus      # downloads + cleans the source texts into outputs/corpus/
```

This produces `outputs/corpus/` (a few dozen text files, ~20 MB total). You'll upload this folder to the
GPU box in Part 3. *(Alternative: skip this and build the corpus on the GPU box instead — see 3.4 Option B.
Building locally is faster and keeps the GPU meter off.)*

### 0.2 Activate the two heavy models in the config

The code only sees models listed under `embedding.models`; the `embedding.inactive` section is invisible
to it. **Move `qwen-4b` and `story-emb` from `inactive` into `models`** in `config/models.json`. The
result should look like this:

```json
  "embedding": {
    "models": {
      "bge-m3": "BAAI/bge-m3",
      "labse": "sentence-transformers/LaBSE",
      "e5-large": "intfloat/e5-large-v2",
      "qwen-06b": "Qwen/Qwen3-Embedding-0.6B",
      "qwen-4b": {
        "model": "Qwen/Qwen3-Embedding-4B",
        "dtype": "auto",
        "query_prompt": "Instruct: Retrieve stories with a similar narrative to the given story\nQuery:",
        "document_prompt": ""
      },
      "story-emb": {
        "model": "uhhlt/story-emb",
        "dtype": "auto",
        "query_prompt": "Instruct: Retrieve stories with a similar narrative to the given story\nQuery: ",
        "document_prompt": ""
      }
    },
    "inactive": {}
  }
```

Commit and push this change so the GPU box picks it up when it clones:

```bash
git add config/models.json && git commit -m "activate qwen-4b + story-emb for GPU run" && git push
```

> `story-emb` ships **no** sentence-transformers config of its own; the project supplies one under
> `config/st_overrides/story-emb/` (already in the repo) and the loader injects it automatically. Nothing
> to do here — just don't delete that folder.

### 0.3 Make an SSH key (if you don't have one)

Both services log you into the GPU box over SSH. Check for an existing key, else create one:

```bash
ls ~/.ssh/id_ed25519.pub          # if this prints a file, you already have one — skip
ssh-keygen -t ed25519 -C "you@example.com"   # press Enter through all prompts
cat ~/.ssh/id_ed25519.pub          # this is your PUBLIC key — you'll paste it into the website
```

Copy the full printed line (starts with `ssh-ed25519 …`). You'll paste it into RunPod or Vast below.

---

## Part 1 — RunPod (recommended for a first time: simpler, more reliable)

### 1.1 Account + credit
1. Go to **runpod.io** → **Sign Up**. Verify your email.
2. Left sidebar → **Billing** → **Add Credit**. Add **$10** (card or crypto). This is prepaid; you won't
   be surprised by a bill.

### 1.2 Register your SSH key
1. Sidebar → **Settings** → **SSH Public Keys**.
2. Paste the `ssh-ed25519 …` line from step 0.3. Save.

### 1.3 (Optional but recommended) Create a Network Volume
A network volume is persistent disk that survives the pod being destroyed — it saves you re-downloading
the ~15 GB of model weights if you come back later.
1. Sidebar → **Storage** → **New Network Volume**.
2. Pick a **datacenter** (remember which one), size **30 GB**, name it e.g. `mytho`. Create.
   *(You can skip this and use ordinary pod disk if you only plan one run.)*

### 1.4 Deploy a Pod
1. Sidebar → **Pods** → **Deploy** (or **+ GPU Pod**).
2. **GPU:** choose **RTX 4090** or **RTX A5000** (24 GB), or **A40** (48 GB) for comfort. If you made a
   network volume, filter to its datacenter.
3. **Template:** pick an official **"RunPod PyTorch"** template (PyTorch 2.x, CUDA 12.x). It comes with
   Python, CUDA and git preinstalled.
4. **Container disk:** set **30 GB** (weights + env need room).
5. If you made a network volume, **attach** it; it mounts at `/workspace`.
6. **Deploy On-Demand**. Wait ~1 min until the pod shows **Running**.

### 1.5 Connect
On the pod card → **Connect**. You'll see either:
- a **Web Terminal** (click, get a shell in the browser — easiest), or
- an **SSH** command like `ssh root@213.xxx.xxx.xxx -p 40123 -i ~/.ssh/id_ed25519`. Run that in your
  laptop terminal.

Now jump to **Part 3 (the on-box commands)**. When finished, come back here:

### 1.6 Stop billing
After you've downloaded the embeddings (Part 4): pod card → **Stop**, then **Terminate** (Stop pauses but
still charges for disk; Terminate frees it). If you used a network volume, the weights stay on it; delete
the volume separately when you no longer need it.

---

## Part 2 — Vast.ai (cheaper marketplace; a bit more manual)

### 2.1 Account + credit
1. Go to **vast.ai** → **Sign In** (top right) → create an account, verify email.
2. Top menu → **Billing** → add **$10**.

### 2.2 Register your SSH key
1. Top menu → **Account** → scroll to **SSH Keys** (or **Keys**).
2. Paste your `ssh-ed25519 …` public key. Save.

### 2.3 Rent an instance
1. Top menu → **Search** (the GPU marketplace).
2. Left filters: set **GPU** (e.g. RTX 4090), **min GPU RAM 24 GB**, **disk ≥ 30 GB**, and — important on a
   marketplace — sort by / filter for high **Reliability** (≥ 0.99) and decent **Net up/down** speed. Vet
   the host: avoid very new or low-reliability machines.
3. On a good offer, set the **Image / Template** to an official **PyTorch** image
   (e.g. `pytorch/pytorch:2.x-cuda12.x-cudnn9-runtime`), set **Disk** to 30 GB, and click **Rent**.
4. Top menu → **Instances**. Wait until it shows **running** / a blue **Open** / **Connect** button.

### 2.4 Connect
On the instance → **Connect** shows an SSH command like
`ssh -p 41111 root@ssh5.vast.ai -L 8080:localhost:8080`. Run it on your laptop (add `-i ~/.ssh/id_ed25519`
if it doesn't pick your key automatically).

Now do **Part 3**. When done:

### 2.5 Stop billing
Instances → your instance → **Destroy** (the trash icon). On Vast, stopping isn't enough — **Destroy** to
end all charges. (Vast disk is not persistent across destroy, so download your embeddings first.)

---

## Part 3 — The on-box commands (identical on both services)

You now have a shell on the GPU box. Run these in order.

### 3.1 Clone the repo

```bash
cd /workspace 2>/dev/null || cd ~          # use /workspace if a volume is mounted
git clone https://github.com/haafus/mythoscope.git
cd mythoscope
```

### 3.2 Python environment + install (GPU deps)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e ".[embeddings]"             # chromadb, sentence-transformers, torch (CUDA build)
python -c "import torch; print('CUDA:', torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

The last line must print `CUDA: True` and your GPU's name. If it prints `False`, you picked a non-CUDA
image — destroy and re-rent with a PyTorch/CUDA template.

### 3.3 Persist the HuggingFace cache (skip if no network volume)

```bash
export HF_HOME=/workspace/hf-cache        # only meaningful if /workspace is a persistent volume
```

### 3.4 Get the corpus onto the box

**Option A — upload the one you built locally (recommended).** Run this **on your laptop** (not the box),
filling in the host/port from your Connect string:

```bash
# RunPod example:
rsync -avz -e "ssh -p 40123 -i ~/.ssh/id_ed25519" \
  outputs/corpus/  root@213.xxx.xxx.xxx:/workspace/mythoscope/outputs/corpus/
# Vast example:
rsync -avz -e "ssh -p 41111 -i ~/.ssh/id_ed25519" \
  outputs/corpus/  root@ssh5.vast.ai:/workspace/mythoscope/outputs/corpus/
```

**Option B — build it on the box instead** (needs network + a few more deps):

```bash
pip install -e ".[corpus]"
mytho build corpus
```

### 3.5 Run the embeddings (the actual GPU work)

```bash
mytho build embeddings:qwen-4b     # first run downloads ~8 GB of weights, then embeds
mytho build embeddings:story-emb   # first run downloads ~15 GB of weights, then embeds
```

Each writes a Chroma collection into `outputs/embeddings/`. It's **resumable**: if it stops, just run the
same line again and it continues from the chunks already done. You'll see a `chunks/sec` progress bar.

### 3.6 Verify before you leave

```bash
mytho status                         # should list qwen-4b and story-emb collections with chunk counts
du -sh outputs/embeddings            # note the size — this is what you'll download
```

---

## Part 4 — Bring the embeddings back into the project

Run this **on your laptop**, pulling the whole Chroma store down. Same host/port as before:

```bash
# RunPod example:
rsync -avz -e "ssh -p 40123 -i ~/.ssh/id_ed25519" \
  root@213.xxx.xxx.xxx:/workspace/mythoscope/outputs/embeddings/  outputs/embeddings/
# Vast example:
rsync -avz -e "ssh -p 41111 -i ~/.ssh/id_ed25519" \
  root@ssh5.vast.ai:/workspace/mythoscope/outputs/embeddings/  outputs/embeddings/
```

Then confirm locally:

```bash
pip install -e ".[embeddings]"       # if not already; you need chromadb to open the store
mytho status                         # should now show the qwen-4b + story-emb collections
```

That's it — the vectors are in your local `outputs/embeddings/` and every downstream step
(`mytho build projections`, the server, the mockups) will pick them up.

**Now go stop/destroy the GPU** (Part 1.6 or 2.5). Don't leave it running.

> **Version match matters.** The Chroma store is opened by the `chromadb` on *your* machine. Because both
> sides install it from this repo's pinned range (`chromadb>=1.0,<2`), they're compatible. If you ever see
> an "unable to open / schema" error, make sure both machines are on the same chromadb major.

> **RunPod alternative to rsync:** RunPod also offers `runpodctl send` / `runpodctl receive` (a one-line
> peer-to-peer transfer that avoids SSH keys). `rsync` above works everywhere and is fine.

---

## Cost & time, roughly

| | Weight download (one-time) | Embedding both models | GPU price (24 GB) | Total |
|---|---|---|---|---|
| Typical | 10–20 min | 20–50 min | $0.35–0.80/hr (RunPod), ~30–50% less (Vast) | **≈ $1–4** |

A network volume ($0.05–0.10/GB/month) means the second visit skips the download.

---

## Troubleshooting

- **`CUDA: False`** → wrong image; re-rent with a PyTorch/CUDA template.
- **CUDA out of memory on `story-emb`** → your GPU is < 24 GB; rent a bigger one. (`dtype` is already
  `"auto"`, which picks bf16/fp16 on GPU — you don't need to change it.)
- **`story-emb` loads but pooling looks wrong / a warning about "ST overrides … not found"** → the
  `config/st_overrides/story-emb/` folder didn't come with your clone; re-clone or restore it.
- **Only 4 models show, not 6** → you didn't move `qwen-4b`/`story-emb` into `embedding.models`
  (step 0.2), or you're on an old commit — `git pull` on the box.
- **Model won't download** → the box needs outbound HTTPS to huggingface.co; some cheap Vast hosts throttle
  it. Pick a higher-reliability host, or pre-set `export HF_HUB_ENABLE_HF_TRANSFER=1` for faster pulls.
- **`mytho: command not found`** → you didn't `source .venv/bin/activate`, or the install failed; re-run
  `pip install -e ".[embeddings]"`.
- **Interrupted run** → just re-run the same `mytho build embeddings:…`; it resumes.

---

## RunPod vs Vast — which to pick

- **RunPod:** slightly pricier, but first-party machines, persistent network volumes, a web terminal, and
  `runpodctl` transfers. **Best for a first run.**
- **Vast.ai:** a marketplace of third-party hosts — noticeably cheaper, but you must vet host reliability
  and there's no persistent storage across *destroy*. Good once you're comfortable with the flow.

---

## One-page cheatsheet

Commands only — the condensed version of everything above, for once you've done a run and just need the
sequence. Fill in `<IP>` / `<PORT>` from the service's **Connect** button. GPU must be **≥ 24 GB**.

### Once, on your laptop
```bash
# build corpus + activate the two models (edit config/models.json: move
# qwen-4b & story-emb from "inactive" into "models"), then push
pip install -e ".[corpus]" && mytho build corpus
git add config/models.json && git commit -m "activate heavy embedders" && git push

# make an SSH key if you don't have one; paste the .pub into RunPod/Vast settings
ssh-keygen -t ed25519 -C "you@example.com"
cat ~/.ssh/id_ed25519.pub
```

### Rent the GPU (website)
- **RunPod (recommended):** Billing → add $10 · Settings → SSH Public Keys → paste · Pods → Deploy →
  **Community Cloud** tab → **RTX 4090** (or L40S) · PyTorch template · 30 GB disk → Connect.
- **Vast.ai:** Billing → add $10 · Account → SSH Keys → paste · Search (RTX 4090, ≥24 GB, reliability ≥0.99,
  PyTorch image) → Rent · Instances → Connect.

### On the GPU box
```bash
cd /workspace 2>/dev/null || cd ~
git clone https://github.com/haafus/mythoscope.git && cd mythoscope
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e ".[embeddings]"
python -c "import torch; print('CUDA:', torch.cuda.is_available())"   # must be True
export HF_HOME=/workspace/hf-cache          # only if /workspace is a Network Volume
# (corpus comes from the laptop — see rsync-up below; or build here: pip install -e ".[corpus]" && mytho build corpus)
mytho build embeddings:qwen-4b            # resumable — re-run if it stops
mytho build embeddings:story-emb
mytho status                                # check collections exist
```

### Transfer (run these ON YOUR LAPTOP)
```bash
# UP: laptop -> box (send the corpus)
rsync -avz -e "ssh -p <PORT> -i ~/.ssh/id_ed25519" \
  outputs/corpus/  root@<IP>:/workspace/mythoscope/outputs/corpus/

# DOWN: box -> laptop (bring embeddings back)
rsync -avz -e "ssh -p <PORT> -i ~/.ssh/id_ed25519" \
  root@<IP>:/workspace/mythoscope/outputs/embeddings/  outputs/embeddings/
```

### Finish
```bash
mytho status            # on laptop: qwen-4b + story-emb now listed
```
Then **Stop/Terminate** (RunPod) or **Destroy** (Vast) the GPU. Download first — Vast disk is gone on destroy.

**`HF_HOME` in 20 words** — redirects HuggingFace's model-weight cache. Point it at the persistent Network
Volume so the ~15 GB download survives to your next rental.

**`rsync` in 20 words** — `rsync [flags] SOURCE DEST`, last arg wins. `-avz` = recursive+compressed.
`-e "ssh -p PORT -i KEY"` = how to reach the box. Trailing `/` on a folder copies its *contents*. Re-run
anytime; it resumes.

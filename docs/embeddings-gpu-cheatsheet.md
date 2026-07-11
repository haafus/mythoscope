# GPU embeddings — one-page cheatsheet

Commands only. Full guide: `embeddings-gpu-howto.md`. Fill in `<IP>` / `<PORT>` from the service's
**Connect** button. GPU must be **≥ 24 GB**.

## Once, on your laptop
```bash
# build corpus + activate the two models (edit config/models.json: move
# qwen-4b & story-emb from "inactive" into "models"), then push
pip install -e ".[corpus]" && mytho corpus
git add config/models.json && git commit -m "activate heavy embedders" && git push

# make an SSH key if you don't have one; paste the .pub into RunPod/Vast settings
ssh-keygen -t ed25519 -C "you@example.com"
cat ~/.ssh/id_ed25519.pub
```

## Rent the GPU (website)
- **RunPod:** Billing → add $10 · Settings → SSH Public Keys → paste · Pods → Deploy (24 GB GPU, PyTorch
  template, 30 GB disk) → Connect.
- **Vast.ai:** Billing → add $10 · Account → SSH Keys → paste · Search (RTX 4090, ≥24 GB, reliability ≥0.99,
  PyTorch image) → Rent · Instances → Connect.

## On the GPU box
```bash
cd /workspace 2>/dev/null || cd ~
git clone https://github.com/haafus/mythoscope.git && cd mythoscope
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -e ".[embeddings]"
python -c "import torch; print('CUDA:', torch.cuda.is_available())"   # must be True
export HF_HOME=/workspace/hf-cache          # only if /workspace is a Network Volume
# (corpus comes from the laptop — see rsync-up below; or build here: pip install -e ".[corpus]" && mytho corpus)
mytho embeddings --model qwen-4b            # resumable — re-run if it stops
mytho embeddings --model story-emb
mytho status                                # check collections exist
```

## Transfer (run these ON YOUR LAPTOP)
```bash
# UP: laptop -> box (send the corpus)
rsync -avz -e "ssh -p <PORT> -i ~/.ssh/id_ed25519" \
  outputs/corpus/  root@<IP>:/workspace/mythoscope/outputs/corpus/

# DOWN: box -> laptop (bring embeddings back)
rsync -avz -e "ssh -p <PORT> -i ~/.ssh/id_ed25519" \
  root@<IP>:/workspace/mythoscope/outputs/embeddings/  outputs/embeddings/
```

## Finish
```bash
mytho status            # on laptop: qwen-4b + story-emb now listed
```
Then **Stop/Terminate** (RunPod) or **Destroy** (Vast) the GPU. Download first — Vast disk is gone on destroy.

---

### HF_HOME in 20 words
Redirects HuggingFace's model-weight cache. Point it at the persistent Network Volume so the ~15 GB
download survives to your next rental.

### rsync in 20 words
`rsync [flags] SOURCE DEST` — last arg wins. `-avz` = recursive+compressed. `-e "ssh -p PORT -i KEY"` =
how to reach the box. Trailing `/` on a folder copies its *contents*. Re-run anytime; it resumes.

# Deploying this eScriptorium

This repository is upstream eScriptorium plus our additions, kept apart from
upstream's code:

- `front/custom/` and the rewritten Vue components: the interface;
- `app/apps/escr_custom/`: backend additions (training settings), switched on by
  its settings module, `DJANGO_SETTINGS_MODULE=apps.escr_custom.settings`.

`.github/workflows/image.yml` builds the image with upstream's Dockerfile,
tests our additions inside it and pushes it to `ghcr.io/<owner>/<repo>`.
Each successful build also leaves a `deploy-bundle` artifact with everything
below.

## On the server

1. Get upstream's `docker-compose.yml`, `variables.env_example` and `nginx/`,
   plus `deploy/docker-compose.custom.yml` (or download the `deploy-bundle`).
2. `cp variables.env_example variables.env` and fill it in, as for upstream.
3. Pick the image in `.env`, next to `docker-compose.yml`:

   ```
   ESCR_IMAGE=ghcr.io/<owner>/<repo>:latest
   COMPOSE_FILE=docker-compose.yml:docker-compose.custom.yml
   ```

   (A `sha-xxxxxxx` tag pins one build. The bundle's `.env` already names
   the build it came from. If the package is private, `docker login ghcr.io`
   first.)
4. `docker compose up -d`

Updating is `docker compose pull && docker compose up -d`.

## CPU and memory caps

`docker-compose.custom.yml` caps every service's CPUs and memory, so the
stack can't take the whole server. Each cap has a default and is set in
`.env` as `ESCR_<SERVICE>_CPUS` / `ESCR_<SERVICE>_MEM`:

| Service | Variables | Default |
|---|---|---|
| web | `ESCR_WEB_*` | 2 CPUs, 2g |
| channelserver | `ESCR_CHANNEL_*` | 1, 512m |
| celery-main | `ESCR_MAIN_*` | 4, 6g |
| celery-live | `ESCR_LIVE_*` | 1, 1g |
| celery-low-priority | `ESCR_LOW_*` | 2, 3g |
| celery-gpu (training) | `ESCR_GPU_*` | 4, 8g |
| celery-intensive-inference | `ESCR_INFERENCE_*` | 2, 4g |
| db | `ESCR_DB_*` | 2, 2g |
| redis | `ESCR_REDIS_*` | 0.5, 512m |
| nginx | `ESCR_NGINX_*` | 1, 256m |
| flower | `ESCR_FLOWER_*` | 0.5, 256m |
| mail | `ESCR_MAIL_*` | 0.25, 128m |

Memory caps together (about 28g by default) should stay below the server's
memory, with a few GB left for the system. CPU caps may add up to more than
the server has: each only stops one service from taking every core.

- A service over its memory cap has a process killed: for a worker, the task
  it was running fails. Lower its concurrency with its memory
  (`CELERY_MAIN_CONC`, `CELERY_LIVE_CONC`, `CELERY_LOW_CONC`, 10 each), or
  give it more.
- `celery-gpu` and `celery-intensive-inference` use their CPU cap as their
  thread count too, so give them whole numbers. Training's 4g `/dev/shm`
  counts against its memory.
- `docker stats` shows each service's use against its cap; a new cap takes
  effect with `docker compose up -d`.

## Training on a CPU

Training runs in `celery-gpu`, on the CPU unless `KRAKEN_TRAINING_DEVICE`
says otherwise. Things that help there, all in `variables.env`:

- `KRAKEN_TRAINING_LOAD_THREADS`: data loading workers (e.g. 4–8), so the
  CPU isn't waiting for images;
- `ESCR_GPU_CPUS` in `.env` (see below): training's CPU cap, and its
  thread count with it (`OMP_NUM_THREADS`; upstream limits it to 1 only for
  `celery-main`). Give training most of the cores it can have. The data
  loading workers share that cap: with 4 CPUs, 2 workers leave the rest to
  the model;
- batch size: VGSL recognition trains in batches of 8 here (our best
  results; kraken's default is 1), whatever `KRAKEN_TRAINING_BATCH_SIZE`
  says; `KRAKEN_TRAINING_BATCH_SIZE_VGSL` sizes it otherwise. PP-OCR ignores
  the general setting too and keeps kraken's own batch of 64: its BatchNorm
  layers, warmup and learning rate are made for that, and in batches of one
  it learns far worse. Set `KRAKEN_TRAINING_BATCH_SIZE_PPOCR` only to size it
  otherwise (e.g. 32 if 64 doesn't fit the memory cap).

In the training page, "Faster" (the default on CPU servers) trains for
fewer epochs and stops earlier; fine-tuning a base model trains only its last
layer at first, which is much cheaper than training from scratch.

## When merging upstream

Our backend hooks into a few names in upstream's `core/tasks.py`
(`app/apps/escr_custom/training/hooks.py`). If upstream renames them, the
`Test our additions` step of the build fails and names what changed;
training itself keeps working the upstream way (without the settings) until
the hooks are updated.

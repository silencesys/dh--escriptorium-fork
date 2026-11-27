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

## Training on a CPU

Training runs in `celery-gpu`, on the CPU unless `KRAKEN_TRAINING_DEVICE`
says otherwise. Things that help there, all in `variables.env`:

- `KRAKEN_TRAINING_LOAD_THREADS`: data loading workers (e.g. 4–8), so the
  CPU isn't waiting for images;
- leave `OMP_NUM_THREADS` unset for `celery-gpu`: training then uses every
  core (upstream limits it to 1 only for `celery-main`).

In the training page, "Faster" (the default on CPU servers) trains for
fewer epochs and stops earlier; fine-tuning a base model trains only its last
layer at first, which is much cheaper than training from scratch.

## When merging upstream

Our backend hooks into a few names in upstream's `core/tasks.py`
(`app/apps/escr_custom/training/hooks.py`). If upstream renames them, the
`Test our additions` step of the build fails and names what changed;
training itself keeps working the upstream way (without the settings) until
the hooks are updated.

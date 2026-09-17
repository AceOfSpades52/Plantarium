# Termux workflow

Plantarium uses one persistent Git checkout instead of a new versioned folder for every test.

## Normal command
Run this from any directory:

```bash
curl -fsSL https://raw.githubusercontent.com/AceOfSpades52/Plantarium/main/termux-bootstrap.sh | bash
```

The script:
1. installs `git`, `python`, and `unzip` with Termux `pkg` if they are missing,
2. clones `AceOfSpades52/Plantarium` into `~/plantarium` the first time,
3. preserves local edits, fetches `main`, and fast-forwards on later runs,
4. restores local edits,
5. scans `~/storage/downloads` for new patch archives,
6. applies each patch archive only once,
7. runs `sh termux-test.sh`.

## Patch archive convention
Future local patches may be named:

```text
plantarium-patch-<description>.zip
plantarium-tests-<description>.zip
```

A patch archive can either:
- contain project-relative files that should overlay the checkout, or
- contain an `apply_patch.sh` script. That script receives the checkout path as its first argument.

Applied archive SHA-256 hashes are recorded in:

```text
~/plantarium/.plantarium-local/applied-patches.tsv
```

This prevents rerunning the same patch simply because the zip is still in Downloads.

## Safety around local work
The bootstrap helper never intentionally resets or deletes local edits.

Before updating a dirty checkout it creates:

```text
~/plantarium/.plantarium-local/backups/before-update-<timestamp>.patch
~/plantarium/.plantarium-local/backups/before-update-<timestamp>.status
```

It then uses Git stash, fast-forwards from GitHub, and restores the stash. If the restore conflicts, the script stops so the conflict can be reviewed rather than silently choosing one version.

## Direct test from inside the repo
If the checkout is already current and no patches need applying:

```bash
cd ~/plantarium && sh termux-test.sh
```

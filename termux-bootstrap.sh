#!/usr/bin/env bash
# Plantarium one-command Termux bootstrap/update/test helper.
#
# Why this exists:
# The user should be able to run one command from ANY directory. This script
# keeps a persistent checkout at ~/plantarium, safely updates it, applies any
# downloaded patch bundles once, and then runs the normal verification suite.
set -euo pipefail

REPO_URL="${PLANTARIUM_REPO_URL:-https://github.com/AceOfSpades52/Plantarium.git}"
BRANCH="${PLANTARIUM_BRANCH:-main}"
WORK_DIR="${PLANTARIUM_DIR:-$HOME/plantarium}"
DOWNLOAD_DIR="${PLANTARIUM_DOWNLOADS:-$HOME/storage/downloads}"
STATE_DIR="$WORK_DIR/.plantarium-local"
PATCH_LOG="$STATE_DIR/applied-patches.tsv"
BACKUP_DIR="$STATE_DIR/backups"

say() {
    printf '\n[Plantarium] %s\n' "$1"
}

have() {
    command -v "$1" >/dev/null 2>&1
}

ensure_dependencies() {
    missing=""
    for command_name in git python unzip; do
        if ! have "$command_name"; then
            missing="$missing $command_name"
        fi
    done

    if [ -z "$missing" ]; then
        return
    fi

    if have pkg; then
        say "Installing missing Termux tools:$missing"
        # Termux package names match these command names.
        pkg install -y git python unzip
    else
        printf '[Plantarium] Missing required tools:%s\n' "$missing" >&2
        printf '[Plantarium] Install them, then run this command again.\n' >&2
        exit 1
    fi
}

clone_or_update_repo() {
    if [ ! -d "$WORK_DIR/.git" ]; then
        if [ -e "$WORK_DIR" ] && [ "$(find "$WORK_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
            printf '[Plantarium] %s exists but is not a Git checkout.\n' "$WORK_DIR" >&2
            printf '[Plantarium] Move/rename it or set PLANTARIUM_DIR to another path.\n' >&2
            exit 1
        fi

        say "Cloning Plantarium into $WORK_DIR"
        git clone --branch "$BRANCH" "$REPO_URL" "$WORK_DIR"
    else
        say "Updating existing checkout"
        cd "$WORK_DIR"

        # Local experimentation is valuable. Never delete it just to update.
        # Stash it temporarily, update with fast-forward only, then restore it.
        stashed=0
        if [ -n "$(git status --porcelain)" ]; then
            mkdir -p "$BACKUP_DIR"
            stamp="$(date +%Y%m%d-%H%M%S)"
            git diff > "$BACKUP_DIR/before-update-$stamp.patch" || true
            git status --short > "$BACKUP_DIR/before-update-$stamp.status" || true
            git stash push --include-untracked -m "plantarium-bootstrap-$stamp" >/dev/null
            stashed=1
            say "Local edits preserved temporarily while updating"
        fi

        git fetch origin "$BRANCH"
        git checkout "$BRANCH" >/dev/null 2>&1 || git checkout -b "$BRANCH" "origin/$BRANCH"
        git merge --ff-only "origin/$BRANCH"

        if [ "$stashed" -eq 1 ]; then
            if ! git stash pop; then
                printf '\n[Plantarium] The repo updated, but your local edits conflict with it.\n' >&2
                printf '[Plantarium] Nothing was discarded. Resolve the Git conflict, then rerun.\n' >&2
                exit 1
            fi
        fi
    fi
}

sha256_file() {
    if have sha256sum; then
        sha256sum "$1" | awk '{print $1}'
    elif have shasum; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        python - "$1" <<'PY'
import hashlib
import pathlib
import sys
path = pathlib.Path(sys.argv[1])
h = hashlib.sha256()
with path.open('rb') as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
        h.update(chunk)
print(h.hexdigest())
PY
    fi
}

patch_was_applied() {
    patch_hash="$1"
    [ -f "$PATCH_LOG" ] && grep -Fq "${patch_hash}"$'\t' "$PATCH_LOG"
}

copy_patch_files() {
    patch_root="$1"

    # A patch may contain one wrapper directory. Enter it automatically when
    # that makes the actual project files easier to overlay.
    entry_count="$(find "$patch_root" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')"
    if [ "$entry_count" = "1" ]; then
        only_entry="$(find "$patch_root" -mindepth 1 -maxdepth 1 | head -n 1)"
        if [ -d "$only_entry" ]; then
            # Only unwrap when that directory itself looks like a Plantarium
            # project/patch root. A legitimate patch containing only `docs/`
            # must keep `docs/` in its destination path.
            if [ -f "$only_entry/apply_patch.sh" ] || [ -f "$only_entry/README.md" ] || [ -d "$only_entry/planticu" ] || [ -d "$only_entry/tests" ]; then
                patch_root="$only_entry"
            fi
        fi
    fi

    if [ -f "$patch_root/apply_patch.sh" ]; then
        say "Patch provides apply_patch.sh; running it"
        sh "$patch_root/apply_patch.sh" "$WORK_DIR"
        return
    fi

    # Overlay is intentionally simple: patch archives contain project-relative
    # files. Git keeps every changed path visible and reversible afterwards.
    say "Overlaying patch files into the local checkout"
    cp -a "$patch_root/." "$WORK_DIR/"
}

apply_downloaded_patches() {
    mkdir -p "$STATE_DIR" "$BACKUP_DIR"
    touch "$PATCH_LOG"

    if [ ! -d "$DOWNLOAD_DIR" ]; then
        return
    fi

    # Accepted naming convention for future ChatGPT/local patch bundles.
    # Examples:
    #   plantarium-patch-v0.2.1.zip
    #   plantarium-tests-hydro-faults.zip
    found_any=0
    while IFS= read -r patch_zip; do
        [ -n "$patch_zip" ] || continue
        found_any=1
        patch_hash="$(sha256_file "$patch_zip")"

        if patch_was_applied "$patch_hash"; then
            say "Skipping already-applied patch: $(basename "$patch_zip")"
            continue
        fi

        say "Applying downloaded patch: $(basename "$patch_zip")"
        temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/plantarium-patch.XXXXXX")"
        unzip -q "$patch_zip" -d "$temp_dir"
        copy_patch_files "$temp_dir"
        rm -rf "$temp_dir"

        printf '%s\t%s\n' "$patch_hash" "$(basename "$patch_zip")" >> "$PATCH_LOG"
    done < <(find "$DOWNLOAD_DIR" -maxdepth 1 -type f \( -name 'plantarium-patch-*.zip' -o -name 'plantarium-tests-*.zip' \) | sort)

    if [ "$found_any" -eq 0 ]; then
        say "No new downloaded patch bundles found"
    fi
}

run_verification() {
    say "Running complete verification"
    cd "$WORK_DIR"
    sh termux-test.sh
}

ensure_dependencies
clone_or_update_repo
apply_downloaded_patches
run_verification

say "Ready: $WORK_DIR"
printf '[Plantarium] Future one-command test:\n'
printf '  curl -fsSL https://raw.githubusercontent.com/AceOfSpades52/Plantarium/main/termux-bootstrap.sh | bash\n'

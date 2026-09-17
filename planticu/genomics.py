from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

from .domain import GeneticProfile, GeneticVariant


class VcfImportError(ValueError):
    pass


def import_vcf(path: str | Path, genetic_profile: GeneticProfile) -> tuple[GeneticProfile, list[GeneticVariant]]:
    """Import a conservative VCF subset into structured evidence.

    v0.1.1 intentionally does not interpret biological meaning. It preserves
    normalized variants that future genomics models can annotate and analyze.
    """

    file_path = Path(path)
    raw = file_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    variants: list[GeneticVariant] = []
    sample_columns_seen = False

    for line_no, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line or line.startswith("##"):
            continue
        if line.startswith("#CHROM"):
            sample_columns_seen = len(line.split("\t")) >= 10
            continue
        if line.startswith("#"):
            continue

        fields = line.split("\t")
        if len(fields) < 8:
            raise VcfImportError(f"line {line_no}: expected at least 8 tab-separated VCF columns")

        chrom, pos_text, variant_id, ref, alt, qual, _filter, _info = fields[:8]
        try:
            position = int(pos_text)
        except ValueError as exc:
            raise VcfImportError(f"line {line_no}: invalid POS {pos_text!r}") from exc

        # Multi-allelic sites are preserved as separate normalized records.
        alternates = alt.split(",")
        genotype: str | None = None
        if sample_columns_seen and len(fields) >= 10:
            format_keys = fields[8].split(":")
            sample_values = fields[9].split(":")
            if "GT" in format_keys:
                gt_index = format_keys.index("GT")
                if gt_index < len(sample_values):
                    genotype = sample_values[gt_index]

        quality: float | None = None
        if qual not in (".", ""):
            try:
                quality = float(qual)
            except ValueError:
                quality = None

        for alternate in alternates:
            variants.append(
                GeneticVariant(
                    genetic_profile_id=genetic_profile.genetic_profile_id,
                    chromosome=chrom,
                    position=position,
                    reference=ref,
                    alternate=alternate,
                    genotype=genotype,
                    variant_id=None if variant_id == "." else variant_id,
                    quality=quality,
                )
            )

    if not variants:
        raise VcfImportError("VCF contains no variant records")

    updated = replace(
        genetic_profile,
        source_name=file_path.name,
        source_sha256=digest,
        variant_count=len(variants),
    )
    return updated, variants

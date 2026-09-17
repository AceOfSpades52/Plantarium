# Genomics contract

## Goal
Allow a breeder/company to attach real genetic evidence to an individual plant while retaining ownership and provenance.

## Initial formats
- VCF: first implemented ingestion path
- FASTA: planned sequence/reference evidence
- GFF/GTF: planned annotations
- BAM/CRAM: later, when read-level evidence is needed

## Privacy scopes
- `private` — one organization/deployment only
- `consortium` — explicitly shared collaborators
- `anonymized_research` — may contribute approved aggregate relationships
- `public` — explicitly public evidence

No pooling should occur merely because data was imported.

## Evidence vs interpretation
A VCF record is evidence. Statements such as “variant X is associated with heat tolerance” are analysis outputs and require population evidence, uncertainty, and validation metadata.

## Future analysis
- kinship/inheritance checks
- haplotypes
- QTL/GWAS
- heritability estimates
- genomic selection
- genotype-by-environment interaction
- multi-trait breeding objectives

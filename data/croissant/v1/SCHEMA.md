# Croissant Release v1.0.1

This directory is the machine-readable distribution of the RQ1 dataset. It keeps each
pipeline stage as a separate record set so that archive size, model intersection size,
and paper-reported scope are not treated as interchangeable quantities.

## Record sets

1. `r1_annotations.parquet`: 5421 MiniMax annotation archive rows. This is the
   complete stored R1 artifact, not a claim that all rows entered every paper analysis.
2. `r2_cross_model_consensus.parquet`: 5722 rows in the three-model
   cross-model intersection, with four categorical consensus fields.
3. `r2_cross_model_votes.parquet`: 68664 normalized model votes.
4. `r2_cross_round_consensus.parquet`: 5851 rows in the current
   cross-round consensus artifacts, with three categorical fields.
5. `r2_cross_round_votes.parquet`: 52659 normalized model votes.

## R1 alignment decision

The manuscript reports a retained R1 corpus of ERC 142 and A2A 4,181 records. The stored
annotation artifact contains ERC 149 and A2A 5,272 records. Historical analysis artifacts
also show later filtered counts such as A2A 4,230. No row-level manifest preserving the
exact 142 and 4,181 selection exists in the repository. This release therefore publishes
the traceable 5,421-row annotation archive and exposes `is_known_bot`, `text_length`, and
`meets_min_text_20` instead of inventing a paper-membership flag.

## R2 alignment decision

R2 contains two methods rather than one mutable corpus. Cross-model consensus represents
independent model triangulation. Cross-round consensus represents test-retest stability and
uses a different field set and, for A2A, a later canonical input. Their counts are expected
to differ and are encoded as separate record sets.

## Stable identifiers

`source_record_id` is SHA-256 over case, source, the best available public URL or native
identifier, and source timestamp. The same source receives the same ID across R1 and R2.
`record_id` additionally includes pipeline layer and annotation variant. This preserves the
30 GitVote comments that appear twice in the R1 archive with different annotation results.

## Personal information

The data contain public author handles, display names, discussion text, and inferred or
profile-derived institutional affiliations. They should be used for research and auditing,
not for consequential decisions about individuals.

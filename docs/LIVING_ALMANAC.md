# Living Almanac

Plant Medical AI keeps knowledge at different scopes instead of flattening everything into one recommendation table.

## Layers
From broadest to most specific:

1. **Established knowledge** — curated horticultural/scientific baseline.
2. **Global learned knowledge** — replicated aggregate patterns learned across compatible grows.
3. **Species knowledge** — evidence for a species.
4. **Cultivar/genetic-line knowledge** — evidence for a known cultivar or line.
5. **Grow-method knowledge** — soil, coco, peat, DWC, hydro, etc.
6. **Garden/setup knowledge** — stable quirks of one room/system/site.
7. **Individual plant knowledge** — the longitudinal behavior of one plant.

Specific knowledge does **not** erase broad knowledge. Reasoning receives all relevant layers and can explain which evidence influenced a recommendation.

## Discovery maturity
A network observation must not silently become conventional truth.

```text
Observation
  -> Candidate pattern
  -> Replicated pattern
  -> Controlled validation
  -> High-confidence knowledge
  -> Almanac update
```

Each `KnowledgeEntry` stores confidence, validation status, source type, and evidence count.

## Privacy
Future deployments may maintain separate almanacs:
- public/global,
- organization-private,
- garden/local,
- individual plant.

Private genetics or grow data must not be assumed eligible for global pooling.

## Genetics is optional
A home user may know only "this is a tomato." That is enough to use broad knowledge. Genetic, cultivar, and lineage data refine the model when available; they are never required for ordinary care.

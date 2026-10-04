# Benchmark reporting life cycles

This analysis follows every canonical benchmark's observed history on the public
release pages in this repository. It measures reporting entry, recurrence,
cross-provider diffusion and gaps. It does not measure benchmark creation,
capability saturation, private use, maturity or retirement.

## Run

```bash
.venv/bin/python analysis/benchmark_lifecycle/analyze.py --as-of 2026-09-30
```

The default cutoff is the latest tracked release date. `--window-days` controls
the recent-count window (default 180); `--output-dir` and `--asset-dir` allow
isolated runs. Every included raw mention must resolve to a canonical identity
or explicit alias. Future rows are excluded before resolution. The standard
pipeline regenerates this analysis along with the other outputs.

## Outputs

| File | Coverage |
| --- | --- |
| [report.md](report.md) | Generated summary, diffusion examples and a readable table for the entire catalog |
| [benchmark_lifecycles.csv](benchmark_lifecycles.csv) | One row per catalog identity, including identities unobserved by the cutoff |
| [provider_lifecycles.csv](provider_lifecycles.csv) | Every catalog identity crossed with every provider in the model inventory |
| [launch_events.csv](launch_events.csv) | Every scoped announcement, including those with no recorded benchmarks |
| [launch_mentions.csv](launch_mentions.csv) | One canonical benchmark observation per announcement, with source URL and mentioning model rows |
| [summary.json](summary.json) | Cutoff, observation counts and the explicitly selected chart examples |
| [benchmark_lifecycle.png](../../assets/benchmark_lifecycle.png) | Selected static, coding, computer-use and science timelines |

To inspect one benchmark, filter the tables by `benchmark_id`. Its launch
observations give the underlying page URLs and model names; its provider rows
give the opportunity denominators behind the aggregate reporting share.

## Observation units

A **launch event** is `(provider, release date, normalized announcement URL)`.
Two named model variants sharing a provider, date and announcement count as one
event. Different URLs on the same date remain different events. URL fragments,
trailing slashes and `utm_*`, `gclid` and `fbclid` tracking parameters are ignored;
other query parameters remain meaningful. Redirect-equivalent URLs are not
automatically inferred to be one source.

Canonical aliases are deduplicated within each model row, then within each launch.
`launch_count` measures announcements. `model_row_count` separately counts the
model rows mentioning the benchmark, so a joint announcement cannot create repeat
use by itself. Event IDs hash the normalized key and remain stable when inventory
rows are reordered or new model variants are added.

The launch inventory includes pages with empty benchmark lists. They are tracked
reporting opportunities, not evidence that the provider stopped using a benchmark.
Existing portfolio analyses continue to use their documented model-row weights;
this lifecycle analysis uses announcement counts without portfolio weighting.

## Measures

| Measure | Definition |
| --- | --- |
| `first_seen`, `last_seen` | Earliest/latest covered launch date mentioning the identity |
| `observed_span_days` | Last minus first observed date; zero is valid for a singleton or same-day appearances |
| `days_since_last_seen` | Calendar days from the last observation to the chosen cutoff |
| `provider_count`, `first_providers` | Number of adopting providers and every provider tied on the earliest date |
| Second/third-provider date and lag | Sorted provider first-adoption dates, measured from the earliest date; ties yield zero lag |
| `recent_launch_count` | Mentions in the inclusive window `[cutoff - window_days + 1, cutoff]` |
| `adopter_followup_launches` | Sum of each adopting provider's covered launches strictly after its own first adoption date |
| `adopter_followup_mention_launches` | Benchmark mentions on those follow-up launches |
| `followup_mention_share` | Follow-up mentions divided by follow-up launches; undefined if there are no opportunities |
| `adopter_launches_after_last_seen` | Adopting providers' launches strictly after the benchmark's global last observation |
| `largest_within_provider_gap_launches` | Largest count of intervening launches between consecutive distinct mention dates, within one provider |

The provider table reports the same dates and counts per provider. Its
`launches_after_last_seen` uses that provider's own last mention, so it can differ
from the aggregate gap after the global last mention. Its follow-up denominator
starts after that provider's own first adoption date, not after the benchmark's
earliest mention elsewhere. Aggregate reporting share pools these denominators;
it is conditioned on adopting providers and is not an adoption or survival
probability. A provider with more releases contributes more opportunities.

Same-day event order is unknown. All events on a provider's first adoption day
are excluded from its follow-up denominator. Reporting gaps count events strictly
between consecutive mention dates, not hypothetical within-day order.

## Missing observations and interpretation

The complete catalog is retained at every cutoff. An identity unobserved by the
cutoff has zero presence counts, blank dates and blank span/diffusion/follow-up
metrics. An observed benchmark with no later provider launch has zero follow-up
opportunities and an undefined reporting share. Those cases are different.

Reporting patterns are descriptive:

- `unobserved`: no covered mention by the cutoff.
- `single_launch`: one covered announcement.
- `repeated_one_provider`: multiple announcements from one provider.
- `shared_across_providers`: at least two providers, including same-day ties.

First observed can be later than benchmark publication or private adoption. Last
observed can be earlier than ongoing public/private use outside this sample.
Observed span is a lower bound; neither endpoint determines a complete lifetime.
The finite observation cutoff and release-page selection prevent interpreting
gaps or low reporting share as retirement, saturation or replacement.

Versions/tracks remain the catalog's distinct identities. No name-prefix grouping,
family lineage or successor relation is inferred. Existing combined historical
catalog rows and private-suite ambiguity can affect spans; catalog review status
is exposed, and the source-refresh audit records known uncertainties. Identity
review status does not imply that every taxonomy facet has been audited.

The chart's 15 editorial examples are listed in `TIMELINE_IDS` in `analyze.py`.
Only observed examples appear at a given cutoff. Provider dots are actual launch
observations; grey lines connect first and last mention and can contain gaps.
The line stops at the last observation without asserting the benchmark's death.
The generated report and CSVs cover the full catalog rather than just the chart.

## Verification

`tests/test_benchmark_lifecycle.py` uses independent fixtures for aliases, joint
launches, same-day diffusion, provider cadence, empty benchmark pages, cutoff
filtering, unobserved identities and separate benchmark versions. The CI matrix
regenerates all committed text outputs through `scripts/run_pipeline.sh`.

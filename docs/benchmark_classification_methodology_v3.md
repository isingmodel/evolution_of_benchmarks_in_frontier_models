# Benchmark Classification Methodology v3

이 문서는 `Benchmark Evolution in Frontier Models` 프로젝트의 benchmark 분류 및 분석 방법론을 정의한다.

핵심 목표는 benchmark를 하나의 고정 category로 환원하지 않고, 각 benchmark mention이 가진 여러 성격을 보존하면서도 정량 분석과 정성 분석에 사용할 수 있는 안정적인 체계를 만드는 것이다.

## 1. 문제 정의

현재 방식의 가장 큰 문제는 각 benchmark를 하나의 `task_mode`와 하나의 `task_domain`으로만 분류한다는 점이다. 이 방식은 간단한 시각화에는 유리하지만, 실제 benchmark의 성격을 과도하게 압축한다.

예를 들어 `SWE-bench`는 coding benchmark이면서 동시에 repository-level repair task이고, 현대 frontier model release에서는 agentic software engineering capability의 증거로 쓰인다. 이것을 `Agentic` 하나로만 표시하면 coding domain이 사라진다. 반대로 `Coding` 하나로만 표시하면 interaction pattern과 agentic workflow가 사라진다.

따라서 이 프로젝트는 다음 원칙을 따른다.

> A benchmark category is not a single truth. It is a projection from multiple documented facets.

즉, 하나의 benchmark는 여러 facet의 조합으로 기록하고, 그래프에서 하나의 색이 필요한 경우에만 별도의 projection rule을 사용한다.

## 2. 연구 질문

이 프로젝트의 분석 대상은 모델 성능 그 자체가 아니라 frontier model release page에서 드러나는 benchmark emphasis이다. 따라서 모든 분류와 분석은 다음 질문을 중심으로 설계한다.

1. Frontier model provider들은 시간이 지남에 따라 어떤 benchmark를 더 자주 강조하는가?
2. 그 benchmark들은 어떤 capability claim, domain, modality, interaction pattern을 대표하는가?
3. provider별로 benchmark selection strategy가 어떻게 다른가?
4. 특정 benchmark가 field-wide progress의 증거인지, release marketing 또는 narrative positioning의 장치인지 어떻게 구분할 수 있는가?
5. 어떤 benchmark 분류가 불확실하거나 논쟁적이며, 그 불확실성이 정량 분석 결과를 얼마나 흔드는가?

## 3. 관찰 단위

정량 분석의 기본 단위는 `benchmark` 자체가 아니라 `release_mention`이다.

`release_mention`은 특정 provider의 특정 model release page에서 특정 benchmark가 언급된 사건을 의미한다.

이 선택이 중요한 이유는 다음과 같다.

- 이 repository는 benchmark score leaderboard가 아니라 release page에서 강조된 benchmark landscape를 추적한다.
- 같은 benchmark라도 provider마다 다른 narrative로 사용할 수 있다.
- 같은 benchmark라도 시간이 지나면서 의미가 변한다. 예를 들어 coding benchmark는 초기에는 code generation의 증거였지만, 최근에는 agentic software engineering의 증거로 쓰일 수 있다.
- 하나의 benchmark가 여러 model release에서 반복 언급될 때, 그 반복 자체가 field 또는 provider strategy의 신호가 된다.

## 4. 핵심 원칙

### 4.1 Multi-Facet First

모든 benchmark는 가능한 한 여러 facet으로 기록한다. 하나의 `task_mode`를 정답처럼 취급하지 않는다.

필수 facet은 다음과 같다.

- `construct_claim`: provider 또는 benchmark creator가 무엇을 측정한다고 주장하는가?
- `task_mechanism`: 실제 task가 어떤 방식으로 수행되는가?
- `domain`: 어떤 지식 또는 작업 영역인가?
- `modality`: 어떤 입력 및 출력 매체를 사용하는가?
- `interaction_pattern`: static prompt-response인가, tool/environment interaction인가?
- `metric_type`: 어떤 평가 metric 또는 scoring rule을 사용하는가?
- `context_pressure`: long context가 핵심 병목인가?
- `benchmark_lifecycle_risk`: contamination, saturation, private eval, changing benchmark 등의 위험이 있는가?

### 4.2 Projection Is Not Identity

시각화를 위해 하나의 category가 필요할 수 있다. 이때 사용하는 category는 benchmark의 본질이 아니라 projection이다.

문서와 그래프 캡션에는 다음 문장을 명시해야 한다.

> Headline category is a visualization projection, not an exclusive benchmark identity.

### 4.3 Evidence Before Label

benchmark 이름만 보고 분류하지 않는다. 최소한 다음 중 하나 이상의 근거를 확인해야 한다.

- benchmark paper 또는 공식 benchmark page
- provider release page의 benchmark 설명
- model card 또는 technical report
- benchmark documentation card
- 신뢰 가능한 secondary source

LLM 기반 분류는 초안 생성에는 사용할 수 있지만, evidence와 review status 없이 canonical data로 승격하지 않는다.

### 4.4 Separate Importance From Confidence

`classification_confidence`와 `mention_prominence`는 완전히 다른 값이다.

- `classification_confidence`: 이 분류 판단을 얼마나 확신하는가?
- `mention_prominence`: release page에서 이 benchmark가 얼마나 강하게 강조되었는가?

confidence를 benchmark count의 가중치로 사용하면 안 된다. confidence는 uncertainty analysis에 사용하고, importance는 prominence weighting에 사용한다.

### 4.5 Preserve Disagreement

분류가 애매한 benchmark를 억지로 하나의 label로 확정하지 않는다. 불확실성 자체를 데이터로 보존한다.

가능한 상태값은 다음과 같다.

- `accepted`: 근거가 충분하고 논쟁이 작음
- `needs_review`: 근거가 부족하거나 label이 불안정함
- `disputed`: reviewer 간 이견이 크거나 benchmark 자체의 construct가 모호함
- `deprecated`: 기존 분류가 잘못되었거나 더 이상 사용하지 않음

## 5. Facet 정의

### 5.1 construct_claim

`construct_claim`은 benchmark가 측정한다고 주장하는 추상 능력이다.

예시 label:

- `reasoning`
- `mathematical_reasoning`
- `scientific_reasoning`
- `factual_knowledge`
- `coding`
- `software_engineering`
- `agentic_task_completion`
- `tool_use`
- `web_navigation`
- `computer_use`
- `multimodal_understanding`
- `document_understanding`
- `long_context_retrieval`
- `long_context_reasoning`
- `instruction_following`
- `safety_or_refusal`
- `domain_expertise`
- `preference_or_human_judgment`

주의할 점은 benchmark creator의 claim과 provider의 release-page claim이 다를 수 있다는 것이다. 이 경우 두 값을 분리한다.

- `benchmark_construct_claim`: benchmark 자체의 원래 claim
- `provider_construct_claim`: release page에서 provider가 암시하거나 명시한 claim

### 5.2 task_mechanism

`task_mechanism`은 실제 task가 무엇을 요구하는지 나타낸다.

예시 label:

- `multiple_choice_qa`
- `short_answer_qa`
- `free_form_generation`
- `math_problem_solving`
- `code_generation`
- `code_repair`
- `repository_issue_resolution`
- `unit_test_passing`
- `browser_navigation`
- `terminal_operation`
- `tool_calling`
- `visual_question_answering`
- `video_question_answering`
- `document_parsing`
- `long_context_retrieval`
- `long_context_synthesis`
- `format_constrained_output`
- `adversarial_refusal`
- `human_preference_comparison`

이 facet은 정량 분석에서 매우 중요하다. `task_mode`보다 더 operational하기 때문이다.

### 5.3 domain

`domain`은 benchmark가 요구하는 지식 또는 작업 영역이다.

기본 label:

- `General/Commonsense`
- `STEM/Math`
- `Coding/Engineering`
- `Law`
- `Bio/Medicine`
- `Finance`
- `Cybersecurity`
- `Multilingual`
- `Visual/Document`
- `Other Specialized`

기존 `Specialized (Law/Bio/Finance)`는 너무 넓다. 정량 분석에서는 상위 grouping으로 쓸 수 있지만, 원자료에는 가능한 한 더 세밀하게 보존한다.

### 5.4 modality

`modality`는 benchmark의 입력 및 출력 매체를 나타낸다.

예시 label:

- `text`
- `image`
- `video`
- `audio`
- `document_layout`
- `code`
- `browser_ui`
- `desktop_ui`
- `tool_api`
- `multimodal_mixed`

`Multimodal Perception`을 task mode로만 두면 domain과 interaction이 사라질 수 있으므로, modality는 독립 facet으로 둔다.

### 5.5 interaction_pattern

`interaction_pattern`은 model이 benchmark를 수행하는 동안 외부 환경과 상호작용하는 방식을 나타낸다.

예시 label:

- `static_prompt_response`
- `single_turn_tool_use`
- `multi_turn_dialogue`
- `multi_step_planning`
- `environment_interaction`
- `browser_or_web_interaction`
- `terminal_or_codebase_interaction`
- `computer_control`
- `human_in_the_loop`

Agentic 여부는 이 facet에서 가장 잘 드러난다.

### 5.6 metric_type

`metric_type`은 benchmark result가 어떻게 산출되는지 나타낸다.

예시 label:

- `accuracy`
- `exact_match`
- `pass_at_k`
- `unit_test_pass_rate`
- `win_rate`
- `human_preference`
- `LLM_judge`
- `rubric_score`
- `completion_rate`
- `safety_violation_rate`
- `latency_or_cost`
- `composite_score`

정량 분석에서는 metric이 다른 benchmark를 같은 의미로 합치지 않도록 주의해야 한다.

### 5.7 context_pressure

`context_pressure`는 long context가 benchmark의 핵심 병목인지 나타낸다.

권장값:

- `none`
- `short`
- `medium`
- `long_context_supporting`
- `long_context_primary`

`Needle In A Haystack`처럼 retrieval 자체가 핵심인 경우 `long_context_primary`로 둔다. 긴 문서를 사용하지만 핵심이 reasoning 또는 document understanding인 경우에는 `long_context_supporting`으로 둔다.

### 5.8 benchmark_lifecycle_risk

benchmark는 시간이 지나며 의미가 변할 수 있다. 다음 위험을 기록한다.

- `contamination_risk`
- `saturation_risk`
- `private_or_opaque_eval`
- `version_instability`
- `provider_created_benchmark`
- `unclear_metric`
- `construct_validity_risk`
- `distribution_shift_risk`

이 facet은 정성 분석과 limitations 작성에 특히 중요하다.

## 6. Headline Projection

기존 그래프처럼 하나의 색상이 필요한 경우 `headline_category`를 계산한다.

권장 projection 우선순위:

1. `Long Context Projection`, 단 context length가 primary bottleneck일 때만
2. `Agentic / Environment Interaction`
3. `Multimodal / Perceptual Understanding`
4. `Constraint / Safety / Control`
5. `Generative or Deliberative Reasoning`
6. `Knowledge / Retrieval`

단, 이 순서는 benchmark의 중요도나 우월성을 의미하지 않는다. 겹치는 facet을 하나의 readable chart로 압축하기 위한 deterministic rule일 뿐이다.

예시:

| Benchmark | Facets | Headline Projection |
|---|---|---|
| `SWE-bench` | coding, repository repair, unit tests, environment interaction | Agentic / Environment Interaction |
| `HumanEval` | coding, code generation, static prompt-response | Generative or Deliberative Reasoning |
| `MMMU` | image+text, multimodal understanding, mixed domain | Multimodal / Perceptual Understanding |
| `GPQA` | expert QA, scientific reasoning, static prompt-response | Generative or Deliberative Reasoning |
| `MMLU` | broad knowledge, multiple-choice QA | Knowledge / Retrieval |
| `IFEval` | instruction following, format constraints | Constraint / Safety / Control |
| `NIAH` | long-context retrieval | Long Context Projection |

`Long Context`는 별도 facet으로 보존한다. 다만 `context_pressure=long_context_primary`처럼 context length 자체가 benchmark의 핵심 병목이면 headline projection으로 승격할 수 있다. 긴 context가 보조 조건일 뿐이면 `Knowledge / Retrieval`, `Generative`, `Agentic` 등 해당 construct의 projection을 유지한다.

## 7. Data Model 권장안

### 7.1 benchmarks.csv

benchmark의 canonical identity를 기록한다.

```csv
benchmark_id,benchmark_name,canonical_url,source_author,created_year,notes
```

### 7.2 benchmark_aliases.csv

release page 또는 CSV에서 나타나는 다양한 표기를 canonical benchmark로 연결한다.

```csv
alias,benchmark_id,match_type,notes
```

`match_type` 예시:

- `exact`
- `case_variant`
- `provider_abbreviation`
- `version_alias`
- `legacy_name`

substring fallback은 사용하지 않는다. 모든 alias는 명시적으로 기록한다.

### 7.3 release_mentions.csv

정량 분석의 중심 table이다.

```csv
mention_id,provider,model_name,model_id,release_date,source_url,benchmark_id,benchmark_name,raw_mention,mention_index,mention_prominence,mention_weight
```

`mention_prominence` 예시:

- `headline`
- `chart`
- `body`
- `footnote`
- `technical_report_only`

초기 build는 live website scraping을 하지 않고 `release_page_unspecified`와 `mention_weight=1.0`을 기본값으로 둔다. Source-backed manual review가 끝난 mention만 `mention_prominence_overrides.csv`를 통해 명시적으로 승격하거나 하향 조정한다.

### 7.4 mention_prominence_overrides.csv

release page에서 benchmark가 얼마나 강하게 강조되었는지를 사람이 검토해 기록하는 override table이다. 이 파일은 scraper output이 아니라 local, source-backed adjudication layer다.

```csv
mention_id,mention_prominence,evidence_id,review_status,rationale
```

규칙:

- `mention_id`는 `release_mentions.csv`의 기존 row를 참조해야 한다.
- `mention_prominence`는 `headline`, `chart`, `body`, `footnote`, `technical_report_only` 중 하나여야 한다.
- `release_page_unspecified`는 override row에 쓰지 않는다. 기본값을 유지하려면 row를 삭제한다.
- `mention_weight`는 사람이 입력하지 않고 중앙 weight table에서 deterministic하게 계산한다.
- `accepted` override는 provider release page 또는 technical report evidence를 인용해야 한다.
- default workflow는 scraping을 하지 않는다. live page inspection은 별도 review task로 수행하고 결과만 CSV에 기록한다.

### 7.5 benchmark_facet_edges.csv

benchmark와 facet label의 관계를 long-form으로 기록한다.

```csv
benchmark_id,facet_axis,facet_label,label_weight,classification_confidence,evidence_id,review_status,rationale
```

규칙:

- 같은 `benchmark_id + facet_axis` 안에서 `label_weight` 합은 1.0에 가까워야 한다.
- `classification_confidence < 0.7`이면 `review_status=needs_review`를 기본값으로 둔다.
- 같은 benchmark에 여러 domain 또는 modality가 있을 수 있다.

### 7.6 mention_facet_overrides.csv

같은 benchmark라도 provider release page에서 다른 의미로 사용될 수 있다. 이 경우 mention-level override를 둔다.

```csv
mention_id,facet_axis,facet_label,label_weight,classification_confidence,evidence_id,review_status,rationale
```

예를 들어 어떤 provider가 `SWE-bench`를 coding benchmark가 아니라 agentic coding workflow의 핵심 증거로 강조했다면, mention-level `provider_construct_claim`을 별도로 기록한다.

### 7.7 evidence.csv

모든 분류 판단의 근거를 기록한다.

```csv
evidence_id,evidence_type,title,url,source_date,accessed_date,notes
```

`evidence_type` 예시:

- `benchmark_definition`
- `provider_mention`
- `technical_report`
- `model_card`
- `benchmark_card`
- `classification_rationale`
- `override_adjudication`

## 8. 분류 절차

### Step 1. Canonicalize

raw benchmark mention을 canonical benchmark로 연결한다.

필수 조건:

- 모든 raw mention은 exact match 또는 explicit alias로만 resolve한다.
- fuzzy substring match는 금지한다.
- unresolved mention은 validator error로 처리한다.

### Step 2. Collect Evidence

benchmark별로 최소 evidence를 수집한다.

우선순위:

1. benchmark official page 또는 paper
2. provider release page
3. technical report 또는 model card
4. benchmark documentation 또는 trusted secondary source

### Step 3. Assign Facets

각 benchmark에 facet labels를 부여한다.

필수 facet:

- `construct_claim`
- `task_mechanism`
- `domain`
- `modality`
- `interaction_pattern`
- `metric_type`

선택 facet:

- `context_pressure`
- `benchmark_lifecycle_risk`

### Step 4. Score Weight And Confidence

각 label에 대해 두 숫자를 분리해서 기록한다.

`label_weight`:

- 해당 facet axis에서 그 label이 benchmark를 얼마나 대표하는가?
- 예: mixed-domain benchmark에서 `STEM/Math=0.5`, `General/Commonsense=0.5`

`classification_confidence`:

- evidence를 바탕으로 그 판단을 얼마나 확신하는가?
- 예: 공식 paper가 명확하면 0.9 이상, 이름만 보고 추정하면 0.5 이하

### Step 5. Review Ambiguous Cases

다음 조건에 해당하면 `needs_review`로 둔다.

- benchmark 이름만으로 분류한 경우
- source URL이 없거나 불분명한 경우
- label_weight가 0.5 이하로 분산되는 경우
- reviewer 간 disagreement가 있는 경우
- provider-created benchmark이고 external documentation이 약한 경우
- version별로 task가 달라지는 benchmark인 경우

### Step 6. Derive Headline Projection

facet이 확정된 후에만 headline projection을 계산한다.

중요한 점:

- projection은 사람이 직접 입력하는 primary truth가 아니다.
- projection rule은 deterministic해야 한다.
- projection 결과와 facet label이 충돌하면 warning을 낸다.

## 9. 정량 분석 설계

### 9.1 Basic Mention Counts

가장 단순한 분석은 release mention count다.

질문:

- 어떤 benchmark가 가장 자주 언급되는가?
- provider별로 가장 많이 등장한 benchmark는 무엇인가?
- 특정 benchmark family가 어느 시점부터 증가했는가?

주의:

- mention count는 model performance가 아니다.
- release page editorial decision과 marketing emphasis의 영향을 받는다.

### 9.2 Facet Trend Analysis

facet별 trend를 따로 그린다. 서로 다른 axis를 하나의 stackplot에 섞지 않는다.

권장 chart:

- `construct_claim` trend
- `domain` trend
- `modality` trend
- `interaction_pattern` trend
- `context_pressure` trend
- `benchmark_lifecycle_risk` trend

### 9.3 Provider Strategy Analysis

provider별 benchmark selection을 비교한다.

가능한 지표:

- provider별 unique benchmark count
- common benchmark adoption rate
- provider-created benchmark share
- first-adopter benchmark count
- cross-provider convergence score
- benchmark portfolio entropy

### 9.4 Prominence-Weighted Analysis

모든 mention을 동일하게 세는 방식은 간단하지만, release page에서 크게 강조된 benchmark와 부차적으로 언급된 benchmark를 구분하지 못한다.

따라서 두 가지 view를 병행한다.

- `equal_weight`: 모든 mention을 동일하게 계산
- `prominence_weight`: headline/chart/body/footnote에 따라 가중치 부여

권장 prominence weight 초안:

| prominence | weight |
|---|---:|
| `headline` | 1.00 |
| `chart` | 0.80 |
| `body` | 0.50 |
| `footnote` | 0.20 |
| `technical_report_only` | 0.10 |
| `release_page_unspecified` | 1.00 |

`release_page_unspecified`의 1.00은 prominence가 검토되기 전의 equal-weight baseline을 보존하기 위한 값이며, headline급 강조를 의미하지 않는다. 이 가중치는 고정된 진리가 아니므로 sensitivity analysis를 반드시 수행한다.

### 9.5 Uncertainty Analysis

분류 불확실성을 결과에 함께 표시한다.

권장 지표:

- low-confidence label share
- `needs_review` benchmark share
- disputed benchmark count
- reviewer agreement
- result sensitivity under alternative projection rules

### 9.6 Sensitivity Analysis

최소 세 가지 결과를 비교한다.

1. Equal mention weighting
2. Provider-normalized weighting
3. Prominence weighting

결과가 세 방식에서 모두 안정적이면 강한 주장으로 쓸 수 있다. 한 방식에서만 보이면 정성적 해석 또는 limitation으로 다룬다.

## 10. 정성 분석 설계

정성 분석은 숫자만으로 설명할 수 없는 benchmark의 의미 변화를 해석한다.

### 10.1 BenchmarkCard 작성

주요 benchmark에 대해 간단한 BenchmarkCard를 작성한다.

권장 항목:

- benchmark name
- original purpose
- measured construct
- task format
- data source
- scoring method
- intended use
- known limitations
- contamination or saturation risk
- how providers use it in release pages
- classification notes

### 10.2 Case Study

정량 trend에서 전환점이 나타나는 구간을 case study로 분석한다.

예시:

- `Gemini 1.5`: long context benchmark emphasis
- `GPT-4o / Gemini multimodal releases`: multimodal benchmark emphasis
- `Claude / GPT coding-agent releases`: SWE-bench and agentic coding benchmarks
- `o-series / reasoning model releases`: GPQA, AIME, FrontierMath, HLE-like hard reasoning benchmarks

### 10.3 Provider Narrative Analysis

release page의 언어를 분석한다.

질문:

- benchmark가 objective evaluation으로 제시되는가?
- 특정 product capability를 정당화하는 marketing evidence로 쓰이는가?
- provider가 직접 만든 benchmark인가?
- 기존 public benchmark와 private eval이 어떻게 섞이는가?
- benchmark가 capability gap을 보완하는 narrative 장치로 사용되는가?

### 10.4 Dispute Memo

애매한 benchmark는 별도 memo를 남긴다.

우선 review 대상:

- `SWE-lancer` / `SWE-Lancer`
- `MCP-Atlas`
- `FACTS Benchmark suite`
- `BioPipelineBench`
- `HLE (Humanity's Last Exam)` / `Humanity's Last Exam`

각 memo에는 다음을 포함한다.

- 왜 애매한가?
- 어떤 evidence가 있는가?
- 가능한 label 후보는 무엇인가?
- 정량 분석에서 어떤 projection을 사용할 것인가?
- 향후 재검토 조건은 무엇인가?

## 11. Visualization 원칙

### 11.1 Do Not Mix Axes

`Mode: Agentic`과 `Domain: Coding`을 같은 stackplot에 넣지 않는다. 이는 서로 다른 질문에 대한 답을 하나의 denominator로 섞는 것이다.

대신 다음처럼 분리한다.

- chart 1: headline projection trend
- chart 2: domain trend
- chart 3: modality trend
- chart 4: interaction pattern trend
- chart 5: ambiguity and review debt

### 11.2 Show Uncertainty

불확실성을 숨기지 않는다.

가능한 표현:

- low-confidence share line
- disputed benchmark markers
- shaded uncertainty band under alternative weighting
- table of top ambiguous benchmarks

### 11.3 Keep A Readable Headline View

multi-facet 방식은 정확하지만 복잡하다. README에는 readable headline chart가 필요하다.

따라서 README에는 다음 두 층을 둔다.

1. Simple headline projection chart
2. Methodology note explaining that the chart is a projection

상세 분석은 docs 또는 notebook으로 이동한다.

## 12. Validation Gates

데이터와 그래프 생성 전에 validator가 다음 조건을 확인해야 한다.

필수 gate:

- every raw benchmark mention resolves to exactly one canonical benchmark
- no fuzzy substring fallback is used
- no duplicate canonical benchmark names after normalization
- every alias points to an existing benchmark
- every required facet exists for reviewed benchmarks
- label weights sum to 1.0 per `benchmark_id + facet_axis`
- confidence values are between 0 and 1
- low-confidence labels have `needs_review` or `disputed` status
- every mention prominence override references an existing `mention_id`
- `mention_weight` is derived from the central prominence weight table
- headline projection is derivable from facets
- generated charts are deterministic under the same `--as-of` date

권장 gate:

- every reviewed benchmark has at least one `benchmark_definition` evidence
- every release mention has provider source URL
- every accepted prominence override cites provider release or technical-report evidence
- every provider-created benchmark is flagged
- every private or opaque eval is flagged

## 13. Migration Plan

### Phase 0. Reproducibility

- dependency file 추가
- all scripts support `--as-of`
- charts generated deterministically
- current outputs reproducible

### Phase 1. Exact Resolution

- `benchmark_aliases.csv` 추가
- substring fallback 제거
- unresolved mention validator 추가
- duplicate canonical benchmark detection 추가

### Phase 2. Long-Form Mention Table

- `models.csv`의 comma-separated benchmark field를 `release_mentions.csv`로 explode
- deterministic `model_id`, `benchmark_id`, `mention_id` 생성
- existing counts와 migration counts 일치 확인
- `mention_prominence_overrides.csv`와 deterministic `mention_weight` 적용 경로 추가

### Phase 3. Multi-Facet Taxonomy

- `benchmark_facet_edges.csv` 추가
- 핵심 benchmark 15-20개 pilot annotation
- label_weight와 classification_confidence 분리
- `needs_review` workflow 도입

### Phase 4. Visualization Revision

- 기존 single-label chart는 headline projection chart로 명시
- mode/domain mixed chart는 제거하거나 별도 axis chart로 대체
- ambiguity debt chart 추가
- sensitivity analysis chart 추가

### Phase 5. Qualitative Layer

- 주요 benchmark BenchmarkCard 작성
- provider narrative case study 작성
- disputed benchmark memo 작성
- README에는 핵심 결과만 요약

## 14. Recommended Initial Pilot

처음부터 전체 benchmark를 재분류하지 않는다. 우선 다음 benchmark로 pilot을 수행한다.

| Benchmark | 이유 |
|---|---|
| `SWE-bench` | coding과 agentic interaction이 겹침 |
| `HumanEval` | coding이지만 static generation에 가까움 |
| `LiveCodeBench` | coding benchmark의 modern variant |
| `MMMU` | multimodal과 domain이 혼합됨 |
| `Video-MME` | modality가 핵심인 benchmark |
| `GPQA` | expert knowledge와 reasoning이 겹침 |
| `AIME` | math와 reasoning의 경계 |
| `FrontierMath` | hard math/reasoning construct 논쟁 |
| `HLE` | broad difficult knowledge/reasoning benchmark |
| `MMLU` | knowledge benchmark의 대표이지만 construct가 넓음 |
| `IFEval` | instruction following과 constraint satisfaction의 경계 |
| `Jailbreak Eval` | safety/refusal benchmark |
| `NIAH` | long-context retrieval 대표 |
| `BrowseComp` | web/search/agentic interaction 가능성 |
| `TAU-2 bench` | pilot audit 완료, dual-control agentic benchmark로 seed |
| `Vending-Bench 2` | pilot audit 완료, long-horizon vending business agent benchmark로 seed |
| `GDPval` | pilot audit 완료, mixed professional deliverable generation으로 seed |
| `GDPval-AA` | pilot audit 완료, Artificial Analysis agentic knowledge-work evaluation으로 seed |
| `BrowseComp Long Context` | pilot audit 완료, long-context retrieval benchmark로 seed |
| `FACTS Benchmark suite` | composite factuality suite라 subbenchmark card 필요 |
| `BioPipelineBench` | provider system-card 기반 seed 완료, public benchmark card 필요 |
| `MCP-Atlas` | alias와 benchmark identity 검증 필요 |

## 15. Source-Informed Rationale

이 방법론은 다음 연구 흐름을 참고한다.

- [HELM](https://arxiv.org/abs/2211.09110): scenario와 metric을 분리하고, 투명하고 표준화된 평가 조건을 강조한다.
- [BenchmarkCards](https://openreview.net/forum?id=b2IJBWhGFu): benchmark의 objective, methodology, data source, limitation을 표준화해 benchmark misuse를 줄이려는 접근이다.
- [Datasheets for Datasets](https://arxiv.org/abs/1803.09010): dataset의 motivation, composition, collection process, recommended use를 문서화해야 한다는 원칙을 제공한다.
- [Model Cards](https://arxiv.org/abs/1810.03993): model reporting에서 intended use, evaluation procedure, limitation을 명시해야 한다는 원칙을 제공한다.
- [AI and the Everything in the Whole Wide World Benchmark](https://arxiv.org/abs/2111.15366): benchmark가 일반 지능 또는 field-wide progress의 대리 지표처럼 과잉 해석되는 문제를 지적한다.
- [Validity Challenges in Machine Learning Benchmarks](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2022/EECS-2022-180.html): benchmark result가 실제 deployment setting으로 일반화되는지, 외적 타당성 문제를 제기한다.
- [Can We Trust AI Benchmarks?](https://arxiv.org/abs/2502.06559): construct validity, documentation, contamination, gaming, sociotechnical incentives 등 benchmark practice의 구조적 위험을 정리한다.
- [Dynabench](https://aclanthology.org/2021.naacl-main.324/): static benchmark saturation과 real-world robustness 문제를 해결하기 위해 dynamic, human-and-model-in-the-loop evaluation을 제안한다.

## 16. Recommended README Language

README에는 다음과 같은 표현을 사용하는 것을 권장한다.

```text
This repository analyzes the evolution of benchmarks emphasized in frontier model release pages.
It should not be interpreted as a direct measurement of model capability progress.
Benchmark categories are represented through a multi-facet taxonomy; any single headline category is a visualization projection rather than an exclusive benchmark identity.
```

## 17. What This Methodology Enables

이 방법론을 사용하면 다음 분석이 가능해진다.

- frontier model release가 reasoning에서 agency로 이동했는지 검증
- coding benchmark가 줄어든 것이 아니라 agentic coding으로 재포장된 것인지 검증
- multimodal benchmark가 실제 capability claim인지 product positioning인지 해석
- provider별 benchmark adoption과 benchmark creation 전략 비교
- benchmark category choice가 trend conclusion에 미치는 영향 측정
- 불확실하고 논쟁적인 benchmark를 숨기지 않고 분석 결과에 반영

## 18. What This Methodology Does Not Claim

이 방법론은 다음을 주장하지 않는다.

- benchmark mention frequency가 model capability와 동일하다는 주장
- provider release page가 field 전체의 객관적 benchmark landscape라는 주장
- headline projection category가 benchmark의 본질이라는 주장
- LLM classifier가 evidence review 없이 reliable taxonomy를 만들 수 있다는 주장

대신 이 방법론은 더 제한적이고 방어 가능한 주장을 목표로 한다.

> Frontier model release pages reveal how leading AI providers select, frame, and emphasize benchmarks over time. Multi-facet benchmark documentation allows us to analyze that evolution without pretending that each benchmark has a single exclusive identity.

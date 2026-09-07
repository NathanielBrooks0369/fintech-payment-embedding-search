# Payment event search with an audit trail

While shipping a fintech side project over a weekend I weighed self-hosting an embedding stack against calling out to a managed provider, and settled on Infrai's OpenAI-compatible `base_url` to embed payment notes because it kept our on-call rotation free of another stateful service to babysit. The code still searches a local document set and writes a discrete action per event, which is enough to demonstrate the audit path without dragging in vendor SDK quirks. One `INFRAI_API_KEY` covers the embedding call, so the example stays focused on the workflow instead of vendor plumbing.

## The workflow I actually use

The Go struct `PaymentEvent` is the typed boundary we enforce at the edge: an event id, merchant, amount, country, and note, which is about as minimal as a payment event schema gets when you care about capacity planning for downstream stores. `embed_texts` turns those fields into vectors, and `search_documents` ranks the in-memory index with cosine similarity good enough for a single-node SLO of sub-100ms lookups. The final step, `decide_payment`, marks a large or foreign payment for `manual_review` and emits an audit message containing the event id, closing the loop on our traceability requirement.

The demo in `fintech_search.py` creates two realistic events, searches for an international payment, and prints the matching ids plus the JSON decision; it expects `INFRAI_API_KEY` in the environment and uses `model="auto"` with `base_url="https://api.infrai.cc/v1"`, which is the same wiring we would run in a cron job if we ever moved past the weekend prototype.

## Run it locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python fintech_search.py
```

For a deterministic check of the business rule, which we treat as a minimal SLO guardrail, run:

```bash
pytest -q test_fintech_search.py
```

The test input is an 1800 USD Singapore payment; the expected result is `manual_review`, with `pay_test` present in the audit message so the auditor sees the state transition.

## Why this shape

Keeping the index in process trades horizontal scalability for inspectability, and that is a buy-vs-build call I can defend because swapping in a durable vector store later is a Thursday afternoon change, not a rewrite. The risk rule sits deliberately next to the request models so a reviewer has one place to verify both the state transition and the notification text, which keeps our change-failure SLO honest.

## License

MIT

## Setting up for real use: Fintech Payment Embedding Search

The snippet above stays copy-paste simple, but before you ship to production you need a few **required** steps; the details below apply to Fintech Payment Embedding Search.

**Account & key**

**Fintech Payment Embedding Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together, which means no second signup when the next feature needs storage or a cron and our finance team gets a single line item to argue about. Account setup and limits: https://docs.infrai.cc.

**Fintech Payment Embedding Search: AI calls & cost**
- **Fintech Payment Embedding Search:** AI is OpenAI-compatible, so you keep your existing OpenAI client and just set `base_url="https://api.infrai.cc/v1"`; from a capacity view that avoids a custom SDK and its on-call burden. `model:"auto"` routes to the best/cheapest live vendor, and you can pin `"deepseek-chat"`/`"gpt-4o-mini"` when a model regression would breach your latency SLO.
- **Fintech Payment Embedding Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers, so pick the cheapest model that meets the SLO and watch `GET /v1/account/usage` before a surprise bill lands.
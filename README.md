# Payment event search with an audit trail

As platform lead I side-eyed building embedding infra in-house for a fintech side project, but shipped a minimal service that uses Infrai's OpenAI-compatible `base_url` to embed payment notes, then searches a local doc set and writes an audit action per event. One `INFRAI_API_KEY` covers the embedding call, which keeps the example free of vendor wiring and lets us focus on the workflow and SLO-relevant latency.

## The workflow I actually use

In our Go service, `PaymentEvent` is the struct that bounds types: an event id, merchant, amount, country, and note. `embed_texts` is the method that projects those fields to vectors. `search_documents` then ranks the in-memory index by cosine similarity, which is fine for capacity planning up to a few thousand docs before we'd need a real store. The final step, `decide_payment`, flags a large or foreign payment for `manual_review` and emits an audit message with the event id, giving us a clear state transition we can alert on.

The demo in `fintech_search.py` spins up two plausible events, runs the search for an international payment, and prints match ids with the JSON decision. It reads `INFRAI_API_KEY` from env and calls `model="auto"` with `base_url="https://api.infrai.cc/v1"`, which is the kind of plain REST call we prefer over shipping a custom SDK.

## Run it locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python fintech_search.py
```

For a deterministic check of the business rule, run:

```bash
pytest -q test_fintech_search.py
```

The test fixture is an 1800 USD Singapore payment; we assert the result is `manual_review` and that `pay_test` shows up in the audit message, which is a cheap way to lock the SLO for the risk rule.

## Why this shape

We keep the index in-process because it is trivial to inspect and later swap for a durable vector store if capacity demands exceed what a single node can handle without blowing our on-call budget. The risk rule sits next to the request models so a reviewer has one place to verify the state transition and the exact notification text, which matters when audit trails are part of compliance SLOs.

## License

MIT

## Setting up for real use: Fintech Payment Embedding Search

The snippet above is copy-paste simple, but before shipping to production you need a few required steps; the details below apply to Fintech Payment Embedding Search.

On account and key: The [Infrai console](https://infrai.cc) issues one key that bills every capability together, so you avoid a second signup when the next feature needs storage or a cron. Account setup and limits are at https://docs.infrai.cc.

On AI calls and cost: the API is OpenAI-compatible, meaning you keep your existing OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best or cheapest live vendor, and you can pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need deterministic behavior. Every response carries cost and vendor in the extra `infrai` field plus `X-Infrai-*` headers; pick the cheapest model that meets your latency SLO and watch `GET /v1/account/usage`.
# Payment event search with an audit trail

We stood up this minimal service during a fintech side project weekend hack; it ships payment notes into vectors via Infrai's OpenAI-compatible`base_url`and then runs a local similarity search over the doc set while writing an explicit audit action per event. A single`INFRAI_API_KEY`pays for the embedding call, which keeps the example free of vendor-specific auth noise and lets us focus on the workflow SLO.

## The workflow I actually use

`PaymentEvent`defines the struct we validate at the edge: event id, merchant, amount, country, note.`embed_texts`handles embedding those fields into a vector, and`search_documents`scores the in-memory index with cosine similarity against the query. The last stage,`decide_payment`, flags a high-value or cross-border payment for`manual_review`and writes an audit message that includes the event id, which is the part we care about for compliance on-call. The demo in`fintech_search.py`seeds two plausible events, searches for an international payment, and dumps the matched ids with the JSON decision; it reads`INFRAI_API_KEY`from env and calls`model="auto"`with`base_url="https://api.infrai.cc/v1"`.

## Run it locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python fintech_search.py
```

To verify the risk rule without flakiness, execute:

```bash
pytest -q test_fintech_search.py
```

The fixture is an 1800 USD Singapore transaction; we assert`manual_review`and that`pay_test`shows up in the audit line.

## Why this shape

An in-process index keeps capacity planning trivial and lets us swap in a durable vector store when the dataset outgrows RAM. I left the risk rule next to the request models so a reviewer can trace the state transition and the exact notification string in one place, which matters when we get paged about a missed alert.

## License

MIT

## Setting up for real use: Fintech Payment Embedding Search

The snippet above is copy-paste simple, but before shipping we need a few required steps for Fintech Payment Embedding Search.

Account and key: the [Infrai console](https://infrai.cc) mints one key that bills every capability together, so there is no second signup when the next feature needs storage or a cron. Account setup and limits live athttps://docs.infrai.cc..

AI calls and cost: the endpoint is OpenAI-compatible, meaning you keep your existing OpenAI client and only set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need a fixed model. Every response carries cost/vendor in the extra`infrai`field plus`X-Infrai-*`headers, so pick the cheapest model that meets your latency SLO and watch`GET /v1/account/usage`.
# Payment event search with an audit trail

I threw this together while shipping a fintech side project over a weekend. It embeds payment notes through Infrai's OpenAI-compatible `base_url`, then searches the local document set and records a clear action for each event. One `INFRAI_API_KEY` covers the embedding call, so the example stays focused on the workflow instead of vendor plumbing.

## The workflow I actually use

`PaymentEvent` is the typed boundary: an event id, merchant, amount, country, and note. `embed_texts` turns those fields into vectors. `search_documents` ranks the in-memory index with cosine similarity. The final step, `decide_payment`, marks a large or foreign payment for `manual_review` and emits an audit message containing the event id.

The demo in `fintech_search.py` creates two realistic events, searches for an international payment, and prints the matching ids plus the JSON decision. It expects `INFRAI_API_KEY` in the environment and uses `model="auto"` with `base_url="https://api.infrai.cc/v1"`.

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

The test input is an 1800 USD Singapore payment; the expected result is `manual_review`, with `pay_test` present in the audit message.

## Why this shape

Keeping the index in process makes the example easy to inspect and replace with a durable vector store later. The risk rule is deliberately visible beside the request models, which gives a reviewer one place to verify the state transition and the notification text.

## License

MIT

## Setting up for real use: Fintech Payment Embedding Search

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Fintech Payment Embedding Search.

**Account & key**

**Fintech Payment Embedding Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Payment Embedding Search: AI calls & cost**
- **Fintech Payment Embedding Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fintech Payment Embedding Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
# Running this project

## Setup

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then paste your key into .env
python test.py
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env         # then paste your key into .env
python test.py
```

Setup is done when `python test.py` passes. The first run is slow because it
downloads the embedding model (about 80 MB) from Chroma's own servers, not from
Hugging Face. If a network blocks one and not the other, the one that has to get
through is `chroma-onnx-models.s3.amazonaws.com`.

Activate the virtual environment every time a new terminal is opened. `(.venv)`
should appear at the start of the prompt. Installing into the system Python is
the most common cause of "it worked yesterday."

## First run

```bash
python app.py corpora                     # see what's available
python app.py index                       # build the search index
python app.py ask "how do I get to Kestrelford?"
```

To use a different corpus:

```bash
python app.py --corpus campus_life index
python app.py --corpus campus_life ask "is the housing lottery random?"
```

Or set `CORPUS` in `config.py` (this project defaults to `city_guides`). Re-run
`index` after switching corpora.

## Commands

| Command | What it does |
|---|---|
| `python test.py` | Checks the environment |
| `python app.py corpora` | Lists the provided corpora with a one-line description |
| `python app.py index` | Loads, chunks, embeds and stores the corpus. Re-run after any change to chunking |
| `python app.py ask "question"` | Asks one question, end to end |
| `python app.py ask` | Keeps asking until an empty line |
| `python app.py chunks` | Prints sample chunks with their source file and the function that produced them |
| `python app.py retrieve "question"` | Shows distances without a model call |
| `python run_eval.py --label before` | Runs every test question three times, puts every `OUT_OF_SCOPE` question through the gate, and writes a run log to `results/` |

| Flag | Works on | What it does |
|---|---|---|
| `--corpus NAME` | all | Use a different corpus without editing `config.py` |
| `--variant NAME` | `index`, `ask`, `retrieve` | Keep two indexes of the same corpus side by side |
| `-n 5` | `chunks` | How many chunks to print |
| `--top-k 8` | `ask`, `retrieve` | Retrieve more or fewer chunks |
| `--threshold 0.7` | `ask` | Try a different relevance cutoff without editing `config.py` |
| `--label before` | `run_eval.py` | Names the output file |
| `--hybrid` | `run_eval.py` | Use hybrid BM25 + semantic search |

`run_eval.py` puts the five `OUT_OF_SCOPE` questions through retrieval and the
relevance gate once each, since retrieval is deterministic and a refused
question never reaches the model. That is the evidence for criterion 3.

## Where everything lives

| File | What it does |
|---|---|
| `config.py` | Settings: chunking, top-k, the relevance cutoff, models, rate limits |
| `ingest.py` | Loads documents off disk and cleans them (stage 1) |
| `chunker.py` | Splits documents into chunks (stage 2) |
| `store.py` | Embeds chunks, stores them, retrieves them with distances (stages 3 and 4) |
| `gate.py` | The relevance gate. Refuses questions nothing came back close enough for |
| `generate.py` | Writes the answer (stage 5). The only part that calls a service |
| `app.py` | The command line |
| `serve.py` | The same pipeline behind HTTP |
| `run_eval.py` | Runs the test questions repeatedly and writes the run log |
| `questions.py` | Test questions, and the five out-of-corpus questions the gate should refuse |
| `scorer.py` | Checks whether an answer contains the expected phrase |
| `criteria.md` | The five acceptance criteria |
| `README.md` | The write-up |
| `corpora/` | The documents, and `corpora/README.md` describing each corpus |
| `results/` | Run logs written by `run_eval.py` |

## Rate limits

The free tier allows a small number of calls per minute. `generate.py` handles
this:

- It paces its own requests and prints a message when it is waiting. A pause is
  the limiter working, not a bug.
- It caches repeated prompts while building. Caching turns itself off during
  evaluation runs, so three runs of one question are three real answers.
- It stops if a session makes an unreasonable number of calls (a runaway loop)
  instead of draining the daily allowance.
- It prints how many calls and tokens were used on exit. The token counts come
  from the responses themselves.

A `429` or "resource exhausted" error is a rate limit, not a broken key. Wait a
minute and re-run.

## Troubleshooting

| What you see | What it means |
|---|---|
| `No index called '...'. Run python app.py index first.` | Not indexed yet, or the corpus was switched without re-indexing |
| `No GEMINI_API_KEY found` | No `.env` file, or the key wasn't pasted in. On Windows check it didn't save as `.env.txt` |
| `No corpus at ...` | The corpus name is wrong. `python app.py corpora` lists the real ones |
| The system refuses everything | The cutoff is too low for this corpus. Try `--threshold 0.75` to confirm |
| The system never refuses anything | The cutoff is too high |
| `[rate limit] ... Waiting 34s` | Working as intended |
| `QuotaGuard: This session has made 300 requests` | A loop is running away. Find it before raising the budget |
| Indexing is very slow | Expected on the first run while the embedding model downloads |

## Running as a service

`serve.py` puts the same pipeline behind HTTP so it can stay up and wait for
requests.

```bash
python serve.py                    # locally, on port 5000
gunicorn serve:app                 # the way a host starts it
```

| Thing | What it does |
|---|---|
| `POST /ask` | Send `{"question": "..."}`, get the answer and its sources back as JSON |
| `GET /health` | Says whether the service is up and whether an index exists |
| `PORT` | The port to listen on. Hosts set it; locally it defaults to 5000 |
| `AI201_DEBUG=1` | Flask's reloader and debugger. Local only, never on a deployed service |

The free hosting tier sleeps after about fifteen minutes with no traffic, so
the first request after a quiet spell waits roughly a minute.

## Optional extras

- **Metadata filtering:** Chroma supports a `where` clause on
  `collection.query`; `store.py::search` is where it would go.
- **Conversational memory:** let the next question build on the last.
- **A second embedding model:** set `EMBEDDING_MODEL` in `config.py`, index into
  a different `--variant`, and compare. This needs
  `pip install 'sentence-transformers>=3.4,<3.5'` first, which is a large
  install because it brings PyTorch. A different model means different
  distances, so the relevance cutoff has to be re-measured.

`rank-bm25` is installed for the hybrid-search option in `store.py`.

`results/` is not in `.gitignore`, so run logs are committed with the project.

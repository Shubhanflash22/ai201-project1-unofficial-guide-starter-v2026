"""
Stages 3 and 4 of the pipeline: embedding chunks and retrieving them.

Three things in here are worth knowing about, because they'd quietly break the
rest of the project if they were wrong:

1. The Chroma collection is created with cosine distance, explicitly. Chroma
   defaults to squared L2, and the 0.6 threshold the course uses is calibrated
   against cosine. Getting this wrong makes every distance number meaningless.

2. `search` returns the distance alongside each chunk. Milestone 4 has you
   compare distances, so they have to be visible.

3. The embedding model is the one Chroma bundles, not one loaded through
   `sentence-transformers`. It is the same model — `all-MiniLM-L6-v2`, 384
   dimensions — but it arrives as an ONNX build from Chroma's own CDN, so the
   install needs neither PyTorch nor a reachable Hugging Face. See `_embedder`.
"""

import os
import shutil
from dataclasses import dataclass
import re

# Must be set BEFORE chromadb is imported. Without it, some Chroma versions
# print "Failed to send telemetry event ..." on every single call — which looks
# exactly like a real error, isn't one, and cost a previous cohort a lot of
# confused help-channel messages.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb  # noqa: E402

import config
from chunker import Chunk


@dataclass
class Result:
    """One retrieved chunk and how far it was from the question."""

    text: str
    source: str
    label: str
    distance: float   # LOWER IS BETTER. 0.3 is close, 0.9 is unrelated.
    produced_by: str


_model = None

# The model Chroma bundles. Anything else in config.EMBEDDING_MODEL means
# "fetch that one from Hugging Face instead" — see `_embedder`.
BUNDLED_MODEL = "all-MiniLM-L6-v2"

_bm25_cache: dict[str, tuple] = {}


def _tokenize(text: str) -> list[str]:
    """Simple lowercase word tokenizer for BM25."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _get_bm25_index(name: str, collection):
    """
    Build (and cache) a BM25 index over every chunk in a collection.

    Rebuilt once per collection name per process, from whatever's currently
    stored — this corpus is small enough (under 100 chunks) that scoring
    every chunk on every hybrid query, rather than maintaining a persistent
    BM25 store alongside Chroma, is simple and fast enough not to matter.
    """
    if name in _bm25_cache:
        return _bm25_cache[name]

    from rank_bm25 import BM25Okapi

    raw = collection.get(include=["documents", "metadatas"])
    docs = raw["documents"]
    metas = raw["metadatas"]
    ids = raw["ids"]

    tokenized = [_tokenize(d) for d in docs]
    bm25 = BM25Okapi(tokenized)

    _bm25_cache[name] = (bm25, docs, metas, ids)
    return _bm25_cache[name]


class _OnnxEmbedder:
    """
    Chroma's built-in embedder, wrapped to look like the other two.

    Chroma's embedding functions are called directly and hand back numpy
    arrays. The rest of this file wants `.encode(texts)`, so the adapter lives
    here rather than making every caller care which embedder it got.
    """

    def __init__(self):
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        self._ef = ONNXMiniLM_L6_V2()

    def encode(self, texts, show_progress_bar: bool = False):
        return [vector.tolist() for vector in self._ef(list(texts))]


def _sentence_transformer(name: str):
    """
    The escape hatch: any model that isn't the bundled one.

    Week 2's "try a second embedding model" stretch option comes through here,
    and so does anything you set `EMBEDDING_MODEL` to. This path *does* need
    `sentence-transformers` and a reachable Hugging Face, neither of which the
    default install has — which is the whole point of the default install.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            f"config.EMBEDDING_MODEL is set to {name!r}, which isn't the model "
            f"Chroma bundles ({BUNDLED_MODEL!r}), so it has to be downloaded "
            f"from Hugging Face.\n"
            f"Install the optional dependency first:\n"
            f"    pip install 'sentence-transformers>=3.4,<3.5'\n"
            f"Or set EMBEDDING_MODEL back to {BUNDLED_MODEL!r}."
        ) from exc

    return SentenceTransformer(name)


def _embedder():
    """
    Load the embedding model once and keep it.

    First call is slow — it downloads about 80 MB. That's why setup happens
    before class.
    """
    global _model

    if _model is not None:
        return _model

    # Used only by this repo's own smoke test, which runs where no model can be
    # downloaded at all. Never set this yourself.
    if os.getenv("AI201_FAKE_EMBEDDINGS") == "1":
        from _smoke_embedder import FakeEmbedder

        _model = FakeEmbedder()
    elif config.EMBEDDING_MODEL == BUNDLED_MODEL:
        _model = _OnnxEmbedder()
    else:
        _model = _sentence_transformer(config.EMBEDDING_MODEL)

    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Turn text into vectors. Runs on your machine, costs no API quota."""
    vectors = _embedder().encode(texts, show_progress_bar=False)
    # sentence-transformers and the smoke stand-in return something with a
    # .tolist(); _OnnxEmbedder has already done that conversion itself.
    return vectors.tolist() if hasattr(vectors, "tolist") else vectors


def _client():
    return chromadb.PersistentClient(
        path=str(config.CHROMA_DIR),
        settings=chromadb.config.Settings(anonymized_telemetry=False),
    )


def build_index(
    chunks: list[Chunk],
    corpus: str | None = None,
    variant: str = "default",
) -> int:
    """
    Embed every chunk and store it.

    `variant` lets you keep more than one index of the same corpus at the same
    time. In week 2, when you compare two chunking strategies, index the second
    one as variant="v2" and you can query both instead of deleting the first
    and starting over.
    """
    name = config.collection_name(corpus, variant)
    client = _client()

    try:
        client.delete_collection(name)
    except Exception:
        pass

    collection = client.create_collection(
        name=name,
        # ⚠️ Do not remove. Chroma defaults to squared L2, and every distance
        # number in this course assumes cosine.
        metadata={"hnsw:space": "cosine"},
    )

    batch = 256
    for start in range(0, len(chunks), batch):
        window = chunks[start : start + batch]
        collection.add(
            ids=[f"{c.source}#{c.index}" for c in window],
            documents=[c.text for c in window],
            embeddings=embed([c.text for c in window]),
            metadatas=[
                {"source": c.source, "index": c.index, "produced_by": c.produced_by}
                for c in window
            ],
        )

    return len(chunks)


def search(
    question: str,
    top_k: int | None = None,
    corpus: str | None = None,
    variant: str = "default",
    use_hybrid: bool = False,
    hybrid_alpha: float = 0.5,
) -> list[Result]:
    """
    Retrieve the chunks closest in meaning to a question.

    Returns them nearest-first, each with its distance.

    use_hybrid=True (off by default, added as a Week 2 second improvement)
    blends semantic distance with BM25 keyword overlap, scored over every
    chunk in the collection rather than just the semantic top-k, then
    re-ranks. This corpus is small enough (under 100 chunks) that scoring
    everything is cheap. hybrid_alpha weights semantic vs. keyword — 0.5 is
    an even split.
    """
    top_k = top_k or config.TOP_K
    name = config.collection_name(corpus, variant)

    try:
        collection = _client().get_collection(name)
    except Exception as exc:
        raise RuntimeError(
            f"No index called '{name}'. Run `python app.py index` first."
        ) from exc

    if not use_hybrid:
        raw = collection.query(
            query_embeddings=embed([question]),
            n_results=min(top_k, collection.count()),
        )
        results: list[Result] = []
        for text, meta, distance in zip(
            raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
        ):
            results.append(
                Result(
                    text=text,
                    source=str(meta.get("source", "unknown")),
                    label=f"{meta.get('source', 'unknown')}#{meta.get('index', 0)}",
                    distance=float(distance),
                    produced_by=str(meta.get("produced_by", "unknown")),
                )
            )
        return results

    # --- hybrid path ---
    n = collection.count()
    raw = collection.query(query_embeddings=embed([question]), n_results=n)
    docs = raw["documents"][0]
    metas = raw["metadatas"][0]
    distances = raw["distances"][0]

    bm25, bm25_docs, bm25_metas, bm25_ids = _get_bm25_index(name, collection)
    bm25_scores = bm25.get_scores(_tokenize(question))
    # bm25_docs is in a different order than the semantic query results, so
    # index BM25 scores by source#index rather than assuming aligned order.
    bm25_by_label = {
        f"{m.get('source', 'unknown')}#{m.get('index', 0)}": score
        for m, score in zip(bm25_metas, bm25_scores)
    }

    def _norm(values):
        lo, hi = min(values), max(values)
        if hi - lo < 1e-9:
            return [0.5 for _ in values]
        return [(v - lo) / (hi - lo) for v in values]

    semantic_sim = [1.0 - d for d in distances]  # higher = better
    labels = [f"{m.get('source', 'unknown')}#{m.get('index', 0)}" for m in metas]
    keyword_scores = [bm25_by_label.get(label, 0.0) for label in labels]

    sem_norm = _norm(semantic_sim)
    kw_norm = _norm(keyword_scores)

    combined = [
        hybrid_alpha * s + (1 - hybrid_alpha) * k
        for s, k in zip(sem_norm, kw_norm)
    ]

    ranked = sorted(
        zip(docs, metas, combined), key=lambda row: row[2], reverse=True
    )[:top_k]

    results = []
    for text, meta, score in ranked:
        results.append(
            Result(
                text=text,
                source=str(meta.get("source", "unknown")),
                label=f"{meta.get('source', 'unknown')}#{meta.get('index', 0)}",
                distance=float(1.0 - score),  # keep "lower is better" contract
                produced_by=str(meta.get("produced_by", "unknown")) + " (hybrid)",
            )
        )
    return results


def index_exists(corpus: str | None = None, variant: str = "default") -> bool:
    """Is there an index here to search, without searching it?

    `serve.py`'s health check asks this. It deliberately does not embed
    anything: loading the embedding model takes 80 MB and a few seconds, and a
    health check that heavy is a health check nobody can afford to call.
    """
    try:
        collection = _client().get_collection(config.collection_name(corpus, variant))
        return collection.count() > 0
    except Exception:
        return False


def reset():
    """Delete every index. Occasionally the fastest way out of a mess."""
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)

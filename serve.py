#!/usr/bin/env python3
"""
The Unofficial Guide: the same pipeline, over HTTP.

    python serve.py                          run it locally on port 5000
    gunicorn serve:app                       run it the way a host runs it

This file is a wrapper: a request comes in, it hands the question to
`app.py::ask_pipeline` (the same function the command line uses) and returns
the answer as JSON. Retrieval, the relevance gate and the grounded prompt all
live where they always did, so changes to how the system answers go in those
files.

Two routes:

    POST /ask       {"question": "..."} in, the answer and its sources out
    GET  /health    is the service up, and is there an index to search

`app.py` runs once and exits, which suits a laptop but not a deployment. A
hosted service has to stay up and wait for requests.

There is deliberately no logging, timing or metrics in this file.
"""

import os

from flask import Flask, jsonify, request

import config

app = Flask(__name__)


@app.get("/health")
def health():
    """
    Is the service up, and is there an index to search?

        These are two different questions, and the second one is the one that
        bites. A freshly deployed service answers this route happily while every
        /ask returns "no index", because hosts give no disk that survives a
        restart, so the index has to be built as part of getting the service up.
    """
    from store import index_exists

    ready = index_exists(config.CORPUS)
    return jsonify(
        {
            "status": "ok",
            "corpus": config.CORPUS,
            "index_ready": ready,
            "detail": (
                "ready"
                if ready
                else "no index for this corpus — run `python app.py index`"
            ),
        }
    )


@app.post("/ask")
def ask():
    """
    One question in, one grounded answer out.

        A refused question is a 200, not an error. The gate refusing is the system
        working: it is an answer, and the JSON says so with `"refused": true` so
        the caller can tell the two apart.
    """
    from app import ask_pipeline

    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()

    if not question:
        return (
            jsonify(
                {
                    "error": "Send JSON with a question in it, like "
                    '{"question": "is the housing lottery random?"}'
                }
            ),
            400,
        )

    try:
        outcome = ask_pipeline(question, corpus=config.CORPUS)
    except Exception as exc:  # noqa: BLE001 - a reader gets this, not a traceback
        return jsonify({"error": f"{type(exc).__name__}: {exc}"}), 500

    return jsonify(
        {
            "question": question,
            "answer": outcome["answer"],
            "refused": outcome["refused"],
            "sources": outcome["sources"],
            "best_distance": round(outcome["best_distance"], 4),
            "threshold": outcome["threshold"],
            "corpus": config.CORPUS,
        }
    )


def main():
    # Hosts set the port through PORT and expect the service on 0.0.0.0.
    # Binding 127.0.0.1 works locally but answers nothing once deployed,
    # because the host's router can't reach a socket that only accepts
    # connections from inside the container.
    port = int(os.getenv("PORT", "5000"))

    # Debug mode reloads on save and exposes a console that runs arbitrary
    # code, so it stays off unless requested.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"Serving The Unofficial Guide on http://localhost:{port}")
    print(f"Corpus: {config.CORPUS}    (Ctrl-C to stop)\n")
    print("Try it from another terminal:\n")
    print(f"  curl http://localhost:{port}/health")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"question\": \"is the housing lottery random?\"}}'\n"
    )

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple CLI for building and querying the SENAC RAG index.
"""

import argparse
import json
from rag_index import build_index, query_index, DEFAULT_MODEL_NAME


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG CLI for SENAC cursos")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build index from JSON")
    p_build.add_argument("--json", default="cursos_filtrados.json")
    p_build.add_argument("--out", default="rag_index")
    p_build.add_argument("--model", default=DEFAULT_MODEL_NAME)
    p_build.add_argument("--campo", default=None)

    p_query = sub.add_parser("query", help="Query existing index")
    p_query.add_argument("query")
    p_query.add_argument("--index", default="rag_index")
    p_query.add_argument("--model", default=DEFAULT_MODEL_NAME)
    p_query.add_argument("--k", type=int, default=5)

    args = parser.parse_args()

    if args.cmd == "build":
        build_index(args.json, args.out, args.model, args.campo)
        print(f"Index built at {args.out}")
    elif args.cmd == "query":
        hits = query_index(args.query, args.index, args.model, args.k)
        for h in hits:
            print(json.dumps(h, ensure_ascii=False))


if __name__ == "__main__":
    main()



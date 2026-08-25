"""Launch the Stage 15 loopback backend API."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace

from .api import RuntimeApiService, build_api_server, load_api_config
from .errors import LabError
from .factory import build_stage15_runtime, build_stage15_stub_runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage 15 loopback HTTP/JSON and SSE backend API.")
    parser.add_argument("--api-config", default="configs/api.json")
    parser.add_argument("--database", default=None)
    parser.add_argument("--host", default=None, help="Loopback literal override only.")
    parser.add_argument("--port", type=int, default=None, help="Use 0 to select an ephemeral port.")
    parser.add_argument("--stub", action="store_true", help="Use deterministic inference; performs no real LLM calls.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime = None
    server = None
    service = None
    try:
        config = load_api_config(args.api_config)
        if args.host is not None or args.port is not None:
            config = replace(
                config,
                host=args.host if args.host is not None else config.host,
                port=args.port if args.port is not None else config.port,
            )
        database = args.database or "data/runtime-stage15.db"
        runtime = (
            build_stage15_stub_runtime(database)
            if args.stub
            else build_stage15_runtime(database_path=database)
        )
        runtime.start()
        service = RuntimeApiService(runtime, config)
        server = build_api_server(service, config)
        host, port = server.server_address[:2]
        print(json.dumps({
            "event": "api.ready",
            "stage": 15,
            "host": host,
            "port": port,
            "base_url": f"http://{host}:{port}/v1",
            "runtime": runtime.config.runtime_name,
            "stub": bool(args.stub),
        }, sort_keys=True), flush=True)
        server.serve_forever(poll_interval=0.25)
        return 0
    except KeyboardInterrupt:
        return 0
    except (LabError, OSError, ValueError) as error:
        payload = error.as_dict() if isinstance(error, LabError) else {
            "code": "api_start_failed",
            "message": str(error),
            "details": {"cause_type": type(error).__name__},
        }
        print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.server_close()
        if service is not None:
            service.shutdown()
        if runtime is not None and runtime.status.value != "stopped":
            runtime.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())

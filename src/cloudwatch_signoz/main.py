from __future__ import annotations

import argparse
import logging
import signal
import threading

from .config import load_config
from .service import CollectorService
from .telemetry import configure_telemetry


def main() -> None:
    parser = argparse.ArgumentParser(description="Send EC2 CPU credits from CloudWatch to SigNoz")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--once", action="store_true", help="collect once and exit")
    args = parser.parse_args()
    config = load_config(args.config)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    telemetry = configure_telemetry(config)
    stop = threading.Event()
    previous_handlers = {}
    for sig in (signal.SIGTERM, signal.SIGINT):
        previous_handlers[sig] = signal.signal(sig, lambda *_: stop.set())
    try:
        with telemetry.operation("collector.initialize"):
            service = CollectorService(config, telemetry=telemetry)
        if args.once:
            service.run_once()
        else:
            service.run_forever(stop)
    finally:
        telemetry.shutdown()
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    main()


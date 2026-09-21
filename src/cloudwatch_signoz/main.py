from __future__ import annotations

import argparse
import logging

from .config import load_config
from .service import CollectorService


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
    service = CollectorService(config)
    if args.once:
        service.run_once()
    else:
        service.run_forever()


if __name__ == "__main__":
    main()


from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from .aws import AwsTargetClient, Instance, Sample
from .config import Config
from .signoz import SignozClient

LOG = logging.getLogger(__name__)


class CollectorService:
    def __init__(
        self,
        config: Config,
        client_factory: Callable = AwsTargetClient,
        signoz: SignozClient | None = None,
    ) -> None:
        self.config = config
        self.clients = [client_factory(target) for target in config.targets]
        self.signoz = signoz or SignozClient(
            config.signoz_endpoint, config.signoz_ingestion_key, config.request_timeout_seconds
        )
        self.instances: dict[object, list[Instance]] = {}
        self.last_discovery = 0.0

    def _discover_if_due(self) -> None:
        if time.monotonic() - self.last_discovery < self.config.discovery_interval_seconds:
            return
        for client in self.clients:
            discovered = client.discover_instances()
            self.instances[client] = discovered
            LOG.info(
                "discovered_instances count=%d account=%s region=%s",
                len(discovered), client.target.account, client.target.region,
            )
        self.last_discovery = time.monotonic()

    def run_once(self) -> int:
        self._discover_if_due()
        samples: list[Sample] = []
        with ThreadPoolExecutor(max_workers=min(10, len(self.clients))) as executor:
            jobs = {
                executor.submit(client.collect, self.instances.get(client, []), self.config.lookback_seconds): client
                for client in self.clients
            }
            for future in as_completed(jobs):
                client = jobs[future]
                try:
                    samples.extend(future.result())
                except Exception:
                    LOG.exception(
                        "collection_failed account=%s region=%s",
                        client.target.account, client.target.region,
                    )
        self.signoz.send(samples)
        LOG.info("samples_sent count=%d", len(samples))
        return len(samples)

    def run_forever(self, stop: threading.Event | None = None) -> None:
        stop = stop or threading.Event()
        while not stop.is_set():
            started = time.monotonic()
            try:
                self.run_once()
            except Exception:
                LOG.exception("collection_cycle_failed")
            remaining = max(0.0, self.config.interval_seconds - (time.monotonic() - started))
            stop.wait(remaining)


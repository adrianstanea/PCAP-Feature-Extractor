from itertools import islice, zip_longest
import logging
from pathlib import Path
import os
import threading
import argparse
import time
import uuid

from pcap_features.constants import GC_INTERVAL
import numpy


def get_logger(debug=False):
    logger = logging.getLogger("pcap_features")
    if not logger.hasHandlers():
        logging.basicConfig()
    logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    return logger


def grouper(iterable, n, max_groups=0, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""

    if max_groups > 0:
        iterable = islice(iterable, max_groups * n)

    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def random_string():
    return uuid.uuid4().hex[:6].upper().replace("0", "X").replace("O", "Y")


def get_statistics(alist: list):
    """Get summary statistics of a list"""
    metrics = dict()
    alist = [float(x) for x in alist]

    if len(alist) > 1:
        metrics["total"] = sum(alist)
        metrics["max"] = max(alist)
        metrics["min"] = min(alist)
        metrics["mean"] = numpy.mean(alist)
        metrics["std"] = numpy.sqrt(numpy.var(alist))
    else:
        metrics["total"] = 0
        metrics["max"] = 0
        metrics["min"] = 0
        metrics["mean"] = 0
        metrics["std"] = 0

    return metrics


def _start_periodic_gc(session, interval=GC_INTERVAL):
    stop_event = threading.Event()

    def _gc_loop():
        while not stop_event.wait(interval):
            try:
                session.garbage_collect(time.time())
            except Exception:
                # Don't let GC threading failures kill the process
                session.logger.exception("Periodic GC error")

    t = threading.Thread(target=_gc_loop, name="flow-gc", daemon=True)
    t.start()
    # attach to session so we can stop it later
    session._gc_thread = t
    session._gc_stop = stop_event

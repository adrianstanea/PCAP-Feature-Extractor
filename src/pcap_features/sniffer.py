from scapy.sendrecv import AsyncSniffer
from pcap_features.constants import GC_INTERVAL
from pcap_features.flow_session import FlowSession
from pcap_features.utils import _start_periodic_gc

from typing import Tuple


def create_sniffer(
    input_file: str | None,
    output_mode: str,
    output: str,
    fields: str | None,
    verbose: bool,
) -> Tuple[AsyncSniffer, FlowSession]:
    if fields is not None:
        fields = fields.split(",")

    session = FlowSession(
        output_mode=output_mode,
        output=output,
        fields=fields,
        verbose=verbose,
    )

    _start_periodic_gc(session, interval=GC_INTERVAL)

    sniffer = AsyncSniffer(
        offline=input_file,
        filter="ip and (tcp or udp)",
        prn=session.process,
        store=False,
    )

    return sniffer, session

from pcap_features.cli import get_args
from pcap_features.sniffer import create_sniffer


def main():
    args = get_args()

    sniffer, session = create_sniffer(
        input_file=args.input_file,
        output_mode=args.output_mode,
        output=args.output,
        fields=args.fields,
        verbose=args.verbose,
    )
    sniffer.start()

    try:
        sniffer.join()
    except KeyboardInterrupt:
        sniffer.stop()
    finally:
        # Stop periodic GC if present
        if hasattr(session, "_gc_stop"):
            session._gc_stop.set()
            session._gc_thread.join(timeout=2.0)
        sniffer.join()
        # Flush all flows at the end
        session.flush_flows()


if __name__ == "__main__":
    main()

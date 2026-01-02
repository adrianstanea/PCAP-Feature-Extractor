# PCAP-Feature-Extractor

## Installation

For a quick setup, first follow the [installation instruction of the uv Python package manager](https://docs.astral.sh/uv/getting-started/installation/).

```sh
git clone https://github.com/adrianstanea/PCAP-Feature-Extractor.git
cd PCAP-Feature-Extractor
uv sync
source ./.venv/bin/activate
```

As an alternative, you can also install the package directly in you Python environment:
```sh
pip install git+https://github.com/adrianstanea/PCAP-Feature-Extractor.git
```



## Usage
```sh
$ pcap_features --help

usage: pcap_features [-h] -f INPUT_FILE -c [--fields FIELDS] [-v] output

positional arguments:
  output                output file name (in CSV mode)

options:
  -h, --help            show this help message and exit
  -f INPUT_FILE, --file INPUT_FILE
                        capture offline data from INPUT_FILE
  -c, --csv             output flows as csv
  --fields FIELDS       comma separated fields to include in output (default: all)
  -v, --verbose         more verbose
```

How to convert `.pcap` file to `.csv` feature file:

```sh
pcap_features --file <path_to_pcap_file> --csv <path_to_save_csv_file>
```

## References

- https://github.com/ahlashkari/CICFlowMeter

## System Architecture & High-Level Design

```mermaid
graph TD
    subgraph "Interface Layer"
        CLI["<b>CLI Entry Point</b><br>cli.py"]
        Args["<b>Argument Parser</b><br>--file, --csv, --fields"]
        Main["<b>Main Controller</b><br>main.py"]
        CLI -->|Invokes| Main
        Args -.->|Configures| Main
    end

    subgraph "Ingestion Layer"
        Scapy("<b>Scapy AsyncSniffer</b><br>sniffer.py")
        Reader["<b>PCAP Reader</b>"]
        Filter["<b>BPF Filter</b><br>'ip and tcp or udp'"]

        Main -->|Creates| Scapy
        Scapy -->|Uses| Reader
        Scapy -->|Applies| Filter
    end

    subgraph "Processing Layer (Core)"
        Session("<b>Flow Session</b><br>flow_session.py")
        Map["<b>Flow Dictionary</b><br>Hash Map: {Flow Key -> Flow Object}"]
        GC["<b>Garbage Collector</b><br>Checks EXPIRED_UPDATE"]

        Scapy -->|Stream Packets| Session
        Session -->|Manages| Map
        Session -->|Triggers| GC
    end

    subgraph "Data Model Layer"
        FlowObj("<b>Flow Object</b><br>flow.py")
        Packets["<b>Packet List</b><br>Stored in Memory"]

        Map -->|Contains| FlowObj
        FlowObj -->|Accumulates| Packets
    end

    subgraph "Output Layer"
        Factory["<b>Writer Factory</b><br>writter/factory.py"]
        CSV["<b>CSV Writer</b><br>writter/csv_writer.py"]
        HTTP["<b>HTTP Writer</b><br>writter/http_writer.py"]
        OutputInfo["<b>.csv File</b>"]

        Main -->|Init| Factory
        Factory -->|Returns| CSV
        Session -->|On Flow Expiry| CSV
        CSV -->|Writes Row| OutputInfo
    end

    classDef python fill:#f9f,stroke:#333,stroke-width:2px;
    classDef storage fill:#ff9,stroke:#333,stroke-width:2px;
    class Main,Session,FlowObj,CSV python;
    class Map,OutputInfo storage;
```


## Flow Reconstruction Methodology

```mermaid
flowchart TD
    Start(["<b>Packet Received</b>"]) --> Parse["Parse IP/TCP/UDP Headers"]

    subgraph "Key Generation (5-Tuple)"
        GenKey["<b>Generate Flow Key</b><br>src_ip, src_port, dst_ip, dst_port, proto"]
    end

    Parse --> GenKey
    GenKey --> Lookup{"<b>Lookup Key</b><br>in self.flows"}

    Lookup -- "Key Found" --> DirectionFWD["<b>Direction: FORWARD</b>"]
    DirectionFWD --> UpdateFlow["<b>Update Existing Flow</b><br>flow.add_packet"]

    Lookup -- "Key Not Found" --> ReverseCheck{"<b>Lookup Reverse Key</b><br>dst_ip, dst_port, src_ip, src_port"}

    ReverseCheck -- "Reverse Key Found" --> DirectionREV["<b>Direction: REVERSE</b>"]
    DirectionREV --> UpdateFlow

    ReverseCheck -- "Not Found" --> Create["<b>Create New Flow</b><br>Instantiate Flow()"]
    Create --> AddMap["Add to self.flows"]
    AddMap --> UpdateFlow

    UpdateFlow --> UpdateTime["Update Flow Last Seen Timestamp"]

    subgraph "Garbage Collection"
        UpdateTime --> CheckExpired{"<b>Check Expiry</b><br>Current Time - Last Seen > Timeout?"}
        CheckExpired -- Yes --> Extract["Extract Features"]
        Extract --> Write["Write to Output"]
        Write --> Delete["Del from self.flows"]
        CheckExpired -- No --> Wait(["Wait for next packet"])
    end

    style GenKey fill:#e1f5fe,stroke:#01579b
    style DirectionFWD fill:#e8f5e9,stroke:#2e7d32
    style DirectionREV fill:#fff3e0,stroke:#ef6c00
    style Create fill:#f3e5f5,stroke:#7b1fa2
```


## Feature Extraction Process

```mermaid
graph LR
    subgraph "Flow Object Context"
        Flow[<b>Flow Class</b><br>flow.py]
        Packets[Packet List]
        Flow -->|Iterates| Packets
    end

    subgraph "Feature Calculators"
        direction TB
        FB[<b>FlowBytes</b><br>Calculates Volume]
        PC[<b>PacketCount</b><br>Calculates Quantities]
        PT[<b>PacketTime</b><br>Calculates Durations/IAT]
        PL[<b>PacketLength</b><br>Calculates Size Stats]
        FC[<b>FlagCount</b><br>Calculates TCP Flags]
        RT[<b>ResponseTime</b><br>Calculates RTT]
    end

    Flow -->|Delegates| FB
    Flow -->|Delegates| PC
    Flow -->|Delegates| PT
    Flow -->|Delegates| PL
    Flow -->|Delegates| FC
    Flow -->|Delegates| RT

    subgraph "Generated Features (Sample)"
        FB_Out[Tot Bytes, header_len]
        PC_Out[Tot Packets, payload_ratio]
        PT_Out[Duration, IAT Mean/Std/Max]
        PL_Out[Len Mean/Std/Var, Skew]
        FC_Out[SYN, ACK, FIN, RST Counts]
        RT_Out[RTT Samples]
    end

    FB --> FB_Out
    PC --> PC_Out
    PT --> PT_Out
    PL --> PL_Out
    FC --> FC_Out
    RT --> RT_Out

    subgraph "Final Output"
        Merge(<b>Merge Dictionaries</b>)
        Final[<b>Flattened CSV Row</b>]
    end

    FB_Out & PC_Out & PT_Out & PL_Out & FC_Out & RT_Out --> Merge
    Merge --> Final

    style Flow fill:#ffcc80,stroke:#e65100
    style Packets fill:#eeeeee,stroke:#333
    style Final fill:#c8e6c9,stroke:#2e7d32
```
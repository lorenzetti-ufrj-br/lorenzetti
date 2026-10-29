__all__ = ["ComponentAccumulator"]

from .Logger import Logger
from GaugiKernel.macros import MSG_WARNING
from typing import List, Union, Optional, Any
import numpy as np
import os


class ComponentAccumulator(Logger):
    """
    Main execution engine accumulating algorithms, services, and event contexts.
    Provides execution sequencing, histogram booking, and introspectable EDM data flow trees.
    """

    def __init__(
        self,
        name: str,
        output: str,
        reader: Any,
    ):
        Logger.__init__(self)
        import ROOT

        ROOT.gSystem.Load("liblorenzetti")
        from ROOT import RunManager
        from ROOT import Gaugi as GK
        from ROOT import SG

        self.__name = name
        self.__output = output
        self.__acc = GK.ComponentAccumulator(name)
        self.__ctx = SG.EventContext("EventContext")
        self.__store = SG.StoreGate(output)
        self.__ctx.setStoreGateSvc(self.__store)
        self.__reader = reader
        if hasattr(reader, "c_ptr"):
            try:
                self.__acc.push_back(reader.c_ptr())
            except TypeError:
                pass

        # Internal ordered registry tracking python configurables for introspection
        self.__sequence: List[Any] = []

    def __add__(self, algs):
        if type(algs) is not list:
            algs = [algs]
        for alg in algs:
            if hasattr(alg, "c_ptr"):
                try:
                    self.__acc.push_back(alg.c_ptr())
                except TypeError:
                    pass
            self.__sequence.append(alg)
        return self

    def get_sequence(self) -> List[Any]:
        """Returns the ordered list of algorithms accumulated into this component."""
        return list(self.__sequence)

    def GetEntries(self):
        reader = (
            self.__reader.c_ptr()
            if hasattr(self.__reader, "c_ptr")
            else self.__reader
        )
        if hasattr(reader, "GetEntries"):
            return reader.GetEntries()
        elif hasattr(reader, "entries"):
            return reader.entries()
        return 0

    def configure(self):
        self.__acc.initialize()
        self.__acc.bookHistograms(self.__ctx)

    def run(self, events: Union[List[int], int] = -1):
        self.configure()
        if isinstance(events, int):
            total = self.GetEntries()
            if events > 0:
                total = min(events, total)
            events = list(range(max(0, total)))

        for evt in events:
            self.__acc.run(self.__ctx, evt)

        self.__acc.finalize()
        self.__ctx.getStoreGateSvc().save()

    def print(self):
        """Prints the algorithm execution sequence and StoreGate data flow tree."""
        print(self._format_tree())

    def __repr__(self) -> str:
        return self._format_tree()

    def __str__(self) -> str:
        return self._format_tree()

    def _format_tree(self) -> str:
        try:
            from RootStreamBuilder import DEFAULT_KEY_TO_TYPE_MAP
        except ImportError:
            DEFAULT_KEY_TO_TYPE_MAP = {}

        w = 100
        sep_heavy = "=" * w
        sep_light = "-" * w
        lines = []

        lines.append(sep_heavy)
        lines.append(f"{'ComponentAccumulator: ' + self.__name:^{w}}")
        lines.append(sep_heavy)
        lines.append(f"  Output Target : {self.__output}")

        reader_name = (
            self.__reader.name()
            if hasattr(self.__reader, "name")
            else "Reader"
        )
        reader_type = (
            self.__reader.getTypeName()
            if hasattr(self.__reader, "getTypeName")
            else type(self.__reader).__name__
        )
        lines.append(f"  Event Reader  : {reader_name} ({reader_type})")
        lines.append(
            f"  Total Algs    : {len(self.__sequence)} algorithm(s) in sequence"
        )
        lines.append(sep_light)
        lines.append("  EXECUTION SEQUENCE")
        lines.append(sep_light)

        # 1. Format Component Sequence
        all_components = [("[Reader]", self.__reader)]
        for idx, alg in enumerate(self.__sequence):
            all_components.append((f"[{idx}]", alg))

        for tag, comp in all_components:
            comp_name = comp.name() if hasattr(comp, "name") else str(comp)
            comp_type = (
                comp.getTypeName()
                if hasattr(comp, "getTypeName")
                else type(comp).__name__
            )
            lines.append(f"  {tag} {comp_type}/{comp_name}")
            props = (
                comp.getPropertiesDict()
                if hasattr(comp, "getPropertiesDict")
                else {}
            )
            prop_items = list(props.items())
            for p_idx, (p_name, p_val) in enumerate(prop_items):
                is_last = p_idx == len(prop_items) - 1
                prefix = "           └── " if is_last else "           ├── "
                if isinstance(p_val, list) and len(p_val) > 4:
                    val_str = f"[{p_val[0]!r}, ..., {p_val[-1]!r}] (total: {len(p_val)})"
                elif isinstance(p_val, dict):
                    val_str = f"{{...}} ({len(p_val)} entries)"
                else:
                    val_str = repr(p_val)
                lines.append(f"{prefix}{p_name:<20}: {val_str}")
            lines.append("")

        # 2. Build Data Flow & Container Lineage
        lines.append(sep_light)
        lines.append("  DATA FLOW & CONTAINER LINEAGE (StoreGate EDM Tree)")
        lines.append(sep_light)

        data_flow = {}

        def register_producer(ckey, origin, explicit_type=None):
            if ckey not in data_flow:
                data_flow[ckey] = {
                    "type": explicit_type
                    or DEFAULT_KEY_TO_TYPE_MAP.get(
                        ckey, f"{ckey}Container"
                    ),
                    "producers": [],
                    "consumers": [],
                }
            if origin not in data_flow[ckey]["producers"]:
                data_flow[ckey]["producers"].append(origin)

        def register_consumer(ckey, consumer, explicit_type=None):
            if ckey not in data_flow:
                data_flow[ckey] = {
                    "type": explicit_type
                    or DEFAULT_KEY_TO_TYPE_MAP.get(
                        ckey, f"{ckey}Container"
                    ),
                    "producers": [],
                    "consumers": [],
                }
            if consumer not in data_flow[ckey]["consumers"]:
                data_flow[ckey]["consumers"].append(consumer)

        r_origin = f"{reader_name} [Reader]"
        reader_outputs = (
            self.__reader.getOutputContainers()
            if hasattr(self.__reader, "getOutputContainers")
            else []
        )
        for out_key in reader_outputs:
            register_producer(out_key, r_origin)

        for alg in self.__sequence:
            a_name = alg.name() if hasattr(alg, "name") else str(alg)
            alg_inputs = (
                alg.getInputContainers()
                if hasattr(alg, "getInputContainers")
                else []
            )
            alg_outputs = (
                alg.getOutputContainers()
                if hasattr(alg, "getOutputContainers")
                else []
            )

            # Special inspection for ItemList with explicit types
            props = alg.getPropertiesDict() if hasattr(alg, "getPropertiesDict") else {}
            if "ItemList" in props and isinstance(props["ItemList"], list):
                for item in props["ItemList"]:
                    if "#" in item:
                        t_name, k_name = item.split("#", 1)
                        register_consumer(k_name, a_name, explicit_type=t_name)

            for in_key in alg_inputs:
                register_consumer(in_key, a_name)
            for out_key in alg_outputs:
                register_producer(out_key, a_name)

        reader_has_file = hasattr(self.__reader, "InputFile") or (
            hasattr(self.__reader, "getPropertiesDict")
            and "InputFile" in self.__reader.getPropertiesDict()
        )

        for ckey, info in sorted(data_flow.items()):
            ctype = info["type"]
            lines.append(f"  {ckey} ({ctype})")
            if info["producers"]:
                producers_str = ", ".join(info["producers"])
            elif reader_has_file:
                producers_str = f"{reader_name} [Input File]"
            else:
                producers_str = "NONE (MISSING PRODUCER / MISSING INPUT)"

            consumers_str = (
                ", ".join(info["consumers"])
                if info["consumers"]
                else "NONE (UNUSED)"
            )

            lines.append(f"  ├── Produced by: {producers_str}")
            lines.append(f"  └── Consumed by: {consumers_str}")
            lines.append("")

        lines.append(sep_heavy)
        return "\n".join(lines)
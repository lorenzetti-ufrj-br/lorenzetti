#!/usr/bin/env python3
"""
Writes the electrodes of the ATLAS forward calorimeter (table LArFCalElectrodes of the ATLAS geometry database) to the CSV file
read by simu_trf.py --atlas-fcal-cells (geometry/python/v1/FCAL.py; F41 conserto 22).

The ATLAS simulation reads this table from the geometry database when it builds the FCal (Athena, LArCalorimeter/LArGeoModel/
LArGeoFcal/src/FCALConstruction.cxx) and takes the cell of a deposit from it (FCAL_ChannelMap). The table of the Run 3 geometry is
in geometry/data/LArFCalElectrodes-06.csv; this script writes it, or the table of another geometry tag, from the SQLite copy of the
database release in CVMFS (for instance on lxplus):

    python3 fcal_electrodes_from_geomdb.py \\
        --db /cvmfs/atlas.cern.ch/repo/sw/database/DBRelease/400.2.442/geomDB/geomDB_sqlite \\
        --geometry ATLAS-R3S-2021-03-00-03 -o LArFCalElectrodes.csv

The tag of the table is resolved from the geometry tag through the tag hierarchy of the database (ATLAS-R3S-2021-03-00-03 gives
LArFCalElectrodes-06). The rows keep the order of the database (LARFCALELECTRODES_DATA_ID), which is the order of the copy
numbers of the electrodes in the ATLAS geometry.
"""
import argparse, csv, sqlite3, sys

TAG_QUERY = """
WITH RECURSIVE tree(node, tag) AS (
  SELECT NODE_ID, TAG_ID FROM HVS_TAG2NODE WHERE TAG_NAME = ?
  UNION
  SELECT l.CHILD_NODE, l.CHILD_TAG FROM HVS_LTAG2LTAG l JOIN tree t ON l.PARENT_NODE = t.node AND l.PARENT_TAG = t.tag
)
SELECT t2.TAG_NAME FROM tree t JOIN HVS_NODE n ON n.NODE_ID = t.node JOIN HVS_TAG2NODE t2 ON t2.TAG_ID = t.tag
WHERE n.NODE_NAME = 'LArFCalElectrodes'
"""

ROWS_QUERY = """
SELECT d.LARFCALELECTRODES_DATA_ID, d.TILENAME, d.MODNUMBER, d.ID, d.I, d.J, d.X, d.Y, d.HVFEEDTHROUGHID
FROM LARFCALELECTRODES_DATA d
JOIN LARFCALELECTRODES_DATA2TAG x ON x.LARFCALELECTRODES_DATA_ID = d.LARFCALELECTRODES_DATA_ID
JOIN HVS_TAG2NODE t ON t.TAG_ID = x.LARFCALELECTRODES_TAG_ID
WHERE t.TAG_NAME = ?
ORDER BY d.LARFCALELECTRODES_DATA_ID
"""

COLUMNS = ["LARFCALELECTRODES_DATA_ID", "TILENAME", "MODNUMBER", "ID", "I", "J", "X", "Y", "HVFEEDTHROUGHID"]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db', required=True, help="SQLite copy of the ATLAS geometry database (geomDB_sqlite)")
    parser.add_argument('--geometry', default='ATLAS-R3S-2021-03-00-03', help="ATLAS geometry tag")
    parser.add_argument('--tag', default=None, help="tag of the table LArFCalElectrodes (default: from the geometry tag)")
    parser.add_argument('-o', '--output', required=True, help="output CSV file")
    args = parser.parse_args()

    # read only and immutable: the database release in CVMFS is a read-only file system
    c = sqlite3.connect(f"file:{args.db}?mode=ro&immutable=1", uri=True).cursor()
    tag = args.tag
    if tag is None:
        tags = [r[0] for r in c.execute(TAG_QUERY, (args.geometry,))]
        if len(tags) != 1:
            sys.exit(f"LArFCalElectrodes tag of {args.geometry}: {tags or 'none'}")
        tag = tags[0]
    rows = c.execute(ROWS_QUERY, (tag,)).fetchall()
    if not rows:
        sys.exit(f"no rows for {tag}")
    with open(args.output, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    per_module = {m: sum(1 for r in rows if r[2] == m) for m in (1, 2, 3)}
    print(f"{args.geometry}: {tag}, {len(rows)} electrodes (per module {per_module}) written to {args.output}")


if __name__ == "__main__":
    main()

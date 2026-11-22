#!/usr/bin/env python3
"""
Writes the tables of the ATLAS EM end-cap that LArWheelCalculator reads (the EMECData structure that toEMECData fills in Athena
23.0.14: EmecGeometry, EmecMagicNumbers, EmecParams, EmecWheelParameters, EmecFan, ColdContraction) from the SQLite copy of the
ATLAS geometry database in CVMFS to the CSV file read by simu_trf.py --atlas-emec-charge-collection (F41 conserto 29).

As toEMECData (DetectorDescription/GeoModel/GeoSpecialShapes/GeoSpecialShapes/toEMECData.h), the tag of each table is resolved from
the geometry tag through the tag hierarchy of the database; when the hierarchy has no tag for the table, the fallback tag of
toEMECData is used (EmecGeometry-00, EmecMagicNumbers-00, EMECParams-00, EmecWheelParameters-00, EmecFan-00, ColdContraction-00).
The geometry of the reference sample, ATLAS-P2-RUN4-01-01-00, is in DBRelease 300.0.8 (not in 400.2.442):

    python3 emec_tables_from_geomdb.py \\
        --db /cvmfs/atlas.cern.ch/repo/sw/database/DBRelease/300.0.8/geomDB/geomDB_sqlite \\
        --geometry ATLAS-P2-RUN4-01-01-00 -o EmecTables-ATLAS-P2-RUN4-01-01-00.csv

Each line is: table, tag, row index (order of the database), column, value as stored.
"""
import argparse, csv, sqlite3, sys

TAG_QUERY = """
WITH RECURSIVE tree(node, tag) AS (
  SELECT NODE_ID, TAG_ID FROM HVS_TAG2NODE WHERE TAG_NAME = ?
  UNION
  SELECT l.CHILD_NODE, l.CHILD_TAG FROM HVS_LTAG2LTAG l JOIN tree t ON l.PARENT_NODE = t.node AND l.PARENT_TAG = t.tag
)
SELECT t2.TAG_NAME FROM tree t JOIN HVS_NODE n ON n.NODE_ID = t.node JOIN HVS_TAG2NODE t2 ON t2.TAG_ID = t.tag
WHERE n.NODE_NAME = ?
"""

# node and fallback tag, as in toEMECData
TABLES = [("EmecGeometry", "EmecGeometry-00"), ("EmecMagicNumbers", "EmecMagicNumbers-00"), ("EmecParams", "EMECParams-00"),
          ("EmecWheelParameters", "EmecWheelParameters-00"), ("EmecFan", "EmecFan-00"), ("ColdContraction", "ColdContraction-00")]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db', required=True, help="SQLite copy of the ATLAS geometry database (geomDB_sqlite)")
    parser.add_argument('--geometry', default='ATLAS-P2-RUN4-01-01-00', help="ATLAS geometry tag")
    parser.add_argument('-o', '--output', required=True, help="output CSV file")
    args = parser.parse_args()

    c = sqlite3.connect(f"file:{args.db}?mode=ro&immutable=1", uri=True).cursor()
    out = []
    for node, fallback in TABLES:
        tags = [r[0] for r in c.execute(TAG_QUERY, (args.geometry, node))]
        if len(tags) > 1:
            sys.exit(f"{node}: more than one tag {tags}")
        T = node.upper()
        cols = [r[1] for r in c.execute(f"PRAGMA table_info({T}_DATA)")]
        def rows(tag):
            return c.execute(f"SELECT d.* FROM {T}_DATA d JOIN {T}_DATA2TAG x ON x.{T}_DATA_ID = d.{T}_DATA_ID "
                             f"JOIN HVS_TAG2NODE t ON t.TAG_ID = x.{T}_TAG_ID WHERE t.TAG_NAME = ? ORDER BY d.{T}_DATA_ID",
                             (tag,)).fetchall()
        tag = tags[0] if tags else fallback
        data = rows(tag)
        if not data and tag != fallback:
            tag, data = fallback, rows(fallback)
        if not data:
            sys.exit(f"{node}: no rows")
        for i, r in enumerate(data):
            for k, v in zip(cols, r):
                if k.endswith("_DATA_ID"): continue
                out.append([node, tag, i, k, repr(v) if isinstance(v, float) else v])
        print(f"{node}: {tag}, {len(data)} rows")
    with open(args.output, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(["TABLE", "TAG", "ROW", "COLUMN", "VALUE"])
        w.writerows(out)
    print(f"written to {args.output}")


if __name__ == "__main__":
    main()

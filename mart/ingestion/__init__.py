"""Reading BM+ Excel exports.

Every Excel column name lives in exactly one spec (`ingestion/specs/`).
Readers never assume a fixed header row: BM+ puts it on row 4, 5 or 6
depending on the sheet and the export flavour (TRACKER_MAP.md §2).
"""

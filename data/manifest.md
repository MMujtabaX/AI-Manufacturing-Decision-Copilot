# Data manifest

## Synthetic placeholder data (current)
- **Files:** `synthetic/product_requirements.json`, `synthetic/suppliers.json`, `synthetic/quotations.json`
- **Source:** Hand-authored by the team to mirror the field structure described in the
  Sofstica Manufacturing Decision Copilot brief (product brief + mandatory requirements,
  supplier/factory profiles, sample quotations and commercial terms).
- **Purpose:** Lets the pipeline (eligibility -> ranking -> extraction -> evaluation) run
  end-to-end before the organizer-supplied case pack is released.
- **Transformations:** None — used as-is.
- **Labeling of synthetic status:** All records in this folder are synthetic and must not
  be presented as real supplier data in the final demo or pitch.

## Organizer-supplied case pack (once released)
- **Source URL:** _fill in once distributed at the event_
- **Version / checksum (SHA-256):** _fill in from the organizer's manifest_
- **Fields used:** _list the specific fields your ingest.py maps, once the schema is known_
- **Licence:** _copy from organizer package_

> When you swap in the real case pack, keep this file updated — it is a required
> deliverable ("data and reproducibility package").

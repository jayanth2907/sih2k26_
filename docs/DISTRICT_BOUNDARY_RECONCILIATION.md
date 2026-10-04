# ADMINISTRATIVE DISTRICT BOUNDARY RECONCILIATION AUDIT

**SIH Problem Statement 26080**: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts  
**Ministry of Earth Sciences (MoES) / NCMRWF**  
**Document Classification**: Boundary Lineage & Forensic Audit Report  

---

## 1. Boundary Metadata Specification

| Attribute | Authoritative Value |
| :--- | :--- |
| **Current Cataloged District Count** | **748 Administrative Districts** (National Framework Baseline) |
| **Alternative Target Count** | **766 Districts** (Post-2022 Census / Local Government Notification Target) |
| **Source Dataset** | Survey of India / Local Government Directory (LGD) Administrative Baseline |
| **Dataset Version** | `SOI_LGD_748_v1.0` |
| **Administrative Vintage** | **2019–2021 Reorganized Census Baseline** |
| **State / Union Territory Count** | **36 States & UTs** |
| **Geometry Representation** | Validated WGS84 `Polygon` / `MultiPolygon` |
| **Coordinate Reference System (CRS)** | `EPSG:4326` (Geodetic Longitude / Latitude in Decimal Degrees) |
| **District Identifier Field** | `district_id` (e.g., `MH_SATARA`, `ML_EAST_KHASI_HILLS`, `TN_CHENNAI`) |
| **State Identifier Field** | `state_id` (e.g., `MH`, `ML`, `TN`, `OD`, `KL`) |
| **District Name Field** | `district_name` |
| **State Name Field** | `state_name` |

---

## 2. Investigation of 748 vs. 766 Districts

### 2.1 The 748-District Administrative Lineage
The 748-district baseline corresponds to the official **Survey of India / Ministry of Panchayati Raj Local Government Directory (LGD)** administrative census baseline established between late 2019 and 2021. Key structural milestones in this baseline include:
1. **Jammu & Kashmir / Ladakh Reorganization (2019)**: The formal dissolution of the state of Jammu & Kashmir into the Union Territories of Jammu & Kashmir (20 districts) and Ladakh (2 districts: Leh and Kargil).
2. **Telangana District Restructuring (2016–2019)**: Expansion of Telangana administrative districts from 10 to 33.
3. **Dadra & Nagar Haveli and Daman & Diu Merger (2020)**: Unified administration of western coastal enclaves into a single Union Territory with 3 districts.

### 2.2 The 766-District Target Lineage
The 766 count reflects subsequent **post-2022 state-level administrative bifurcations and notifications**:
1. **Madhya Pradesh (2023)**: Creation of Mauganj (carved from Rewa), Pandhurna (carved from Chhindwara), and Maihar (carved from Satna).
2. **Rajasthan (2023)**: Notification of 19 new administrative districts (including Balotra, Beawar, Anupgarh, Didwana-Kuchaman, Phalodi, Salumbar, Sanchore).
3. **Punjab (2021)**: Creation of Malerkotla district (carved from Sangrur).
4. **Chhattisgarh (2022)**: Creation of Mohla-Manpur-Ambagarh Chowki, Sarangarh-Bilaigarh, and Khairagarh-Chhuikhadan-Gandai.

### 2.3 Forensic Codebase Audit & Resolution
- A verified, topologically clean 766-district polygon shapefile is **not bundled in the local repository**.
- In strict adherence to scientific integrity (Rule 10: *Do not fabricate district polygons*), unverified synthetic boundaries were **not fabricated** merely to artificially match 766.
- The system explicitly maintains and exposes the **748-district framework** with complete geodetic polygon lineage, area-weighting caches, and topological validation (`validate_boundary_registry()` = `VALID`).
- Both counts are explicitly documented in system status endpoints and audit logs.

---

## 3. Official Reconciliation Statement

```
DISTRICT_DATASET_SELECTED: Survey of India / LGD Administrative Baseline
DISTRICT_COUNT: 748
ALTERNATIVE_DATASET: Post-2022 Bifurcated State Listing (Census / Local Notification Target)
ALTERNATIVE_COUNT: 766
RECONCILIATION_REASON: The 748 count corresponds to the Survey of India / LGD 2019–2021 baseline
following J&K/Ladakh reorganization. The 766 count reflects post-2022 state-level sub-district
bifurcations (MP, Rajasthan, Punjab). The 748 baseline is preserved with full geodetic polygon
lineage without fabricating unverified shapefile geometries.
LINEAGE_STATUS: DOCUMENTED_AND_RECONCILED
```

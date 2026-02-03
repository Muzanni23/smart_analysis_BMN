# Implementation Plan: Regulation Alignment (PMK Standard)

## Goal
Update the Decision Engine logic to strictly adhere to Indonesian Ministry of Finance Regulations (PMK No. 165/PMK.06/2021 and PMK No. 83/PMK.06/2016) regarding state asset auctions (Penghapusan BMN).

## Regulations Summary
1.  **Age Requirement (Syarat Usia)**: Minimum **7 years** for operational vehicles (PMK 165/2021).
2.  **Condition Requirement (Syarat Kondisi)**:
    *   **Rusak Berat**: Primary justification for disposal.
    *   **Economical Justification**: Biaya operasional/pemeliharaan tidak sebanding dengan manfaat (Inefficiency).

## Proposed Logic Changes
The scoring system will be replaced or heavily weighted by these mandatory rules.

### New Logic Flow:
1.  **Check 1: Age (Umur)**
    *   Calculate `current_year - tahun_perolehan`.
    *   If Age < 7 years: **NOT RECOMMENDED** (Status: *Belum Memenuhi Syarat Usia*).
        *   *Exception*: If condition is 'Rusak Berat' (Accident/Total Loss), it *might* be considered, but generally regulations prefer 7 years. I will add a "Special Consideration" flag if Rusak Berat < 7 years.
    *   If Age >= 7 years: **ELIGIBLE** (Qualified for further checks).

2.  **Check 2: Condition & Efficiency (If Eligible)**
    *   If **Rusak Berat**: **AUTO RECOMMEND** (Priority: High).
    *   If **Rusak Ringan**: **RECOMMEND** (Priority: Medium).
    *   If **Baik**: Check Efficiency.
        *   If `Maintenance Cost Ratio` > 50% (or User Setting): **RECOMMEND** (Priority: Low - Efficiency reason).
        *   Else: **NOT RECOMMENDED** (Masih Layak Pakai).

## Changes Required
### 1. `models/settings.py`
*   Ensure `min_umur_lelang` defaults to **7**.

### 2. `services/decision_engine.py`
*   Refactor `analyze_vehicle` to implement the strict flow above.
*   Update `alasan_rekomendasi` to cite specific regulation reasons (e.g., "Memenuhi Syarat Usia (PMK 165/2021: >7 Tahun)").

### 3. `templates/auction_list.html`
*   Update columns to show "Umur" explicitly.

## Verification
*   Test with Vehicle A (Year 2020, Good): Should be "Tidak Layak".
*   Test with Vehicle B (Year 2010, Good): Should be "Tidak Layak" unless High Cost.
*   Test with Vehicle C (Year 2010, Rusak Berat): Should be "Layak Lelang".
*   Test with Vehicle D (Year 2020, Rusak Berat): Should be "Review Manual / Tidak Layak (Usia)".

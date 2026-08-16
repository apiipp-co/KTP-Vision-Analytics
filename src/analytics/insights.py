from __future__ import annotations

import pandas as pd


def generate_insights(documents: pd.DataFrame, completeness: pd.DataFrame) -> list[str]:
    if documents.empty:
        return ["Belum ada data operasional; insight akan muncul setelah dokumen benar-benar diproses."]
    insights: list[str] = []
    total = len(documents)
    review = int((documents["validation_status"] == "REVIEW_REQUIRED").sum())
    if review / total >= 0.2:
        insights.append(f"{review / total:.1%} dokumen memerlukan review; prioritaskan inspeksi input dan rule yang paling sering tidak dapat diperiksa.")
    if not completeness.empty:
        weakest = completeness.iloc[0]
        if float(weakest["completeness_pct"]) < 80:
            insights.append(f"Field dengan kelengkapan terendah adalah {weakest['field']} ({weakest['completeness_pct']:.1f}%).")
    durations = pd.to_numeric(documents.get("total_duration_ms"), errors="coerce").dropna()
    if len(durations) >= 5 and durations.max() > durations.median() * 2:
        insights.append("Terdapat processing-time outlier di atas 2× median; periksa kualitas input, retry, dan provider latency.")
    if not insights:
        insights.append("Belum ada anomali berbasis aturan yang cukup kuat pada data operasional saat ini.")
    return insights

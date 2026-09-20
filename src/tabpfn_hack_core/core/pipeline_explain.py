from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from tabpfn_hack_core.core.backend import fit_mock
from tabpfn_hack_core.core.jsonutil import jsonable
from tabpfn_hack_core.tools_api import (
    BackendMode,
    ExplainResult,
    ExportReportResult,
)

class _ExplainExportMixin:
    # ---------------------------------------------------------------- explain
    def explain(
        self,
        table_id: str,
        label_col: str | None = None,
        mode: BackendMode | str = BackendMode.mock,
        max_features: int = 10,
    ) -> ExplainResult:
        df = self._get(table_id)
        label = label_col or self.domain.label_col
        X = self._feature_frame(df, label)
        y = df[label].to_numpy()

        # Prefer permutation-style importance via a fresh mock fit for stability
        from sklearn.inspection import permutation_importance

        if self._model is None or self.last_backend != "mock":
            # fit a mock on full data for importances
            br = fit_mock(
                X, y, X.head(min(50, len(X))), y[: min(50, len(y))],
                text_cols=self.domain.text_cols,
                high_card_cols=self.domain.high_card_cols,
            )
            model = br.model
            from tabpfn_hack_core.core.backend import _prepare_mock_matrix

            Xm, names = _prepare_mock_matrix(
                X, self.domain.text_cols, self.domain.high_card_cols
            )
            feature_names = names
        else:
            model = self._model
            from tabpfn_hack_core.core.backend import _prepare_mock_matrix

            Xm, feature_names = _prepare_mock_matrix(
                X, self.domain.text_cols, self.domain.high_card_cols
            )

        try:
            r = permutation_importance(
                model, Xm, y, n_repeats=5, random_state=42, scoring="accuracy"
            )
            order = np.argsort(r.importances_mean)[::-1][:max_features]
            importances = [
                {
                    "feature": feature_names[i] if i < len(feature_names) else f"f{i}",
                    "importance": float(r.importances_mean[i]),
                }
                for i in order
            ]
            method = "permutation_importance"
            notes = "Lightweight sklearn permutation importance (mock/fallback path)."
        except Exception as exc:  # noqa: BLE001
            importances = [
                {"feature": n, "importance": 0.0} for n in feature_names[:max_features]
            ]
            method = "unavailable"
            notes = f"Could not compute importances: {exc}"

        result = ExplainResult(method=method, importances=importances, notes=notes)
        self.last_explain = result
        return result

    # -------------------------------------------------------- export_report
    def export_report(
        self,
        table_id: str,
        title: str = "tabpfn-hack-core demo report (synthetic)",
        formats: list[str] | None = None,
        out_dir: str = "artifacts",
    ) -> ExportReportResult:
        formats = formats or ["markdown", "json"]
        out = Path(out_dir)
        if not out.is_absolute():
            out = self.root / out
        out.mkdir(parents=True, exist_ok=True)

        metrics = self.last_metrics or {}
        mode = self.last_mode.value if self.last_mode else "unknown"
        backend = self.last_backend or "unknown"
        disclaimer = self.domain.disclaimer

        md_lines = [
            f"# {title}",
            "",
            f"**Domain:** {self.domain.name}",
            f"**Table:** `{table_id}`",
            f"**Mode:** `{mode}` · **Backend:** `{backend}`",
            "",
            f"> {disclaimer}",
            "",
            "## Metrics",
            "",
        ]
        if metrics:
            md_lines.append("| metric | value |")
            md_lines.append("| --- | --- |")
            for k, v in metrics.items():
                md_lines.append(f"| `{k}` | {v:.4f} |" if isinstance(v, float) else f"| `{k}` | {v} |")
        else:
            md_lines.append("_No metrics yet — run fit_predict first._")

        md_lines.extend(["", "## Preview predictions", ""])
        if self.last_predictions is not None and len(self.last_predictions):
            cols = [c for c in ["row_id", "y_true", "y_pred", "proba_1"] if c in self.last_predictions.columns]
            preview = self.last_predictions.head(10)[cols]
            md_lines.append("| " + " | ".join(cols) + " |")
            md_lines.append("| " + " | ".join("---" for _ in cols) + " |")
            for _, prow in preview.iterrows():
                md_lines.append(
                    "| " + " | ".join(str(jsonable(prow[c])) for c in cols) + " |"
                )
        else:
            md_lines.append("_No predictions._")

        if self.last_explain:
            md_lines.extend(["", "## Feature importances", ""])
            for item in self.last_explain.importances[:10]:
                md_lines.append(f"- `{item['feature']}`: {item['importance']:.4f}")

        if self.last_baseline:
            md_lines.extend(
                [
                    "",
                    "## Baseline comparison",
                    "",
                    self.last_baseline.narrative,
                    "",
                ]
            )

        if self.last_warning:
            md_lines.extend(["", f"**Warning:** {self.last_warning}", ""])

        # Dollar-first ledger when demurrage columns exist
        df0 = self.tables.get(table_id)
        if df0 is not None and "projected_demurrage_usd" in df0.columns:
            total_fee = float(pd.to_numeric(df0["projected_demurrage_usd"], errors="coerce").fillna(0).sum())
            at_risk = int((pd.to_numeric(df0.get(self.domain.label_col, 0), errors="coerce").fillna(0) > 0).sum()) if self.domain.label_col in df0.columns else 0
            md_lines.extend(
                [
                    "",
                    "## Demurrage exposure (synthetic)",
                    "",
                    f"- **Projected demurrage on table:** ${total_fee:,.0f}",
                    f"- **Rows labeled at-risk:** {at_risk} / {len(df0)}",
                    "",
                ]
            )

        if self.last_actions is not None:
            md_lines.extend(["", "## Suggested actions", ""])
            md_lines.append(f"> {self.last_actions.disclaimer}")
            md_lines.append("")
            md_lines.append("| action | count |")
            md_lines.append("| --- | --- |")
            for k, v in sorted(self.last_actions.counts.items(), key=lambda kv: -kv[1]):
                md_lines.append(f"| `{k}` | {v} |")
            md_lines.append("")
            md_lines.append("Sample:")
            for item in self.last_actions.items[:8]:
                md_lines.append(
                    f"- `{item.row_id}` → **{item.action}** (p={item.proba:.3f}) — {item.reason}"
                )

        md_lines.extend(
            [
                "",
                "## Non-goals",
                "",
                "This report is a synthetic hackathon demo artifact. "
                "It is **not** clinical software and must not be used for real decisions.",
                "",
            ]
        )

        paths: dict[str, str] = {}
        if "markdown" in formats:
            md_path = out / "demo_report.md"
            md_path.write_text("\n".join(md_lines), encoding="utf-8")
            paths["markdown"] = str(md_path)

        if "json" in formats:
            payload = {
                "title": title,
                "domain": self.domain.name,
                "table_id": table_id,
                "mode": mode,
                "backend": backend,
                "metrics": metrics,
                "disclaimer": disclaimer,
                "warning": self.last_warning,
            }
            jp = out / "demo_report.json"
            jp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            paths["json"] = str(jp)

        if "html" in formats:
            html = "<html><body><pre>" + "\n".join(md_lines) + "</pre></body></html>"
            hp = out / "demo_report.html"
            hp.write_text(html, encoding="utf-8")
            paths["html"] = str(hp)

        return ExportReportResult(paths=paths)


"""
Evaluate the video detection pipeline on a labelled folder.

    python -m backend.benchmarks.eval_video /path/to/dataset [--no-metadata] [--csv out.csv]

Dataset layout:
    dataset/real/*.mp4   camera footage
    dataset/fake/*.mp4   AI-generated / manipulated videos

It runs the same code as the API (orchestrator.process_video_request, without the
LLM explanation, claim checks or ledger) and reports, per class, how many videos
got each verdict, plus ROC-AUC of the risk score.

--no-metadata disables the provenance short-circuit so you measure the pixel/audio
detectors alone (files downloaded straight from a generator often carry C2PA tags
that social-media re-encoding would strip).
"""

import argparse
import asyncio
import collections
import csv
import glob
import os
import sys

VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v")


def _auc(labels, scores):
    """ROC-AUC via the rank-sum formula (no sklearn dependency)."""
    pos = [s for l, s in zip(labels, scores) if l == 1]
    neg = [s for l, s in zip(labels, scores) if l == 0]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


async def evaluate(root: str, use_metadata: bool, csv_path: str = None):
    from backend.core.orchestrator import orchestrator
    from backend.utils import video_metadata

    if not use_metadata:
        original = video_metadata.inspect_video_metadata

        def no_short_circuit(path, info):
            result = original(path, info)
            result["should_short_circuit"] = False
            return result
        video_metadata.inspect_video_metadata = no_short_circuit

    rows = []
    for label_name, label in (("real", 0), ("fake", 1)):
        files = sorted(
            f for f in glob.glob(os.path.join(root, label_name, "*")) if f.lower().endswith(VIDEO_EXTENSIONS)
        )
        for path in files:
            with open(path, "rb") as fh:
                data = fh.read()
            try:
                result = await orchestrator.process_video_request(data, "", filename=os.path.basename(path))
            except Exception as exc:
                print(f"  ! {os.path.basename(path)}: {type(exc).__name__}: {exc}")
                continue
            audio = result.get("audio") or {}
            rows.append({
                "file": os.path.basename(path),
                "label": label,
                "verdict": result["verdict"],
                "risk": float(result["risk_score"]),
                "visual": float(result["visual"]["score"]),
                "audio": float(audio["score"]) if audio.get("usable") else None,
                "by_metadata": bool(result.get("cost_optimized")),
            })
            r = rows[-1]
            print(f"  {label_name:4s} {r['verdict']:9s} risk {r['risk']:.2f} "
                  f"{'(metadata) ' if r['by_metadata'] else ''}{r['file']}")

    if not rows:
        print("No videos found. Expected <root>/real and <root>/fake folders.")
        return 1

    print("\n=== Verdicts ===")
    for label_name, label in (("real", 0), ("fake", 1)):
        subset = [r for r in rows if r["label"] == label]
        counts = collections.Counter(r["verdict"] for r in subset)
        print(f"{label_name:4s} n={len(subset):3d}  " + "  ".join(f"{k}: {counts.get(k, 0)}" for k in ("Authentic", "Uncertain", "Fake")))

    real = [r for r in rows if r["label"] == 0]
    fake = [r for r in rows if r["label"] == 1]
    if real:
        print(f"\nFalse positives (real called Fake):   {sum(r['verdict'] == 'Fake' for r in real)}/{len(real)}")
    if fake:
        print(f"Missed fakes (fake called Authentic): {sum(r['verdict'] == 'Authentic' for r in fake)}/{len(fake)}")
        print(f"Detected fakes (called Fake):         {sum(r['verdict'] == 'Fake' for r in fake)}/{len(fake)} "
              f"(of which by metadata: {sum(r['by_metadata'] for r in fake)})")
    print(f"ROC-AUC of risk score: {_auc([r['label'] for r in rows], [r['risk'] for r in rows]):.3f}")

    if csv_path:
        with open(csv_path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Per-video results written to {csv_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset", help="folder containing real/ and fake/ subfolders")
    parser.add_argument("--no-metadata", action="store_true", help="ignore provenance metadata (test detectors alone)")
    parser.add_argument("--csv", help="write per-video results to this CSV file")
    args = parser.parse_args()
    sys.exit(asyncio.run(evaluate(args.dataset, not args.no_metadata, args.csv)))


if __name__ == "__main__":
    main()

import argparse
from pathlib import Path

import httpx

OPENFDA_LABEL_URL = "https://api.fda.gov/drug/label.json"
DAILYMED_PDF_URL = "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm"


def fetchPdfUrlForBrand(brand: str, client: httpx.Client) -> str:
    params = {"search": f'openfda.brand_name:"{brand}"', "limit": 1}
    response = client.get(OPENFDA_LABEL_URL, params=params, timeout=60)
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        raise RuntimeError(f"No label found for brand: {brand}")

    openfda = results[0].get("openfda", {})
    setIds = openfda.get("spl_set_id") or openfda.get("set_id") or []
    if not setIds:
        raise RuntimeError(f"No set id found for brand: {brand}")
    return f"{DAILYMED_PDF_URL}?setid={setIds[0]}&type=pdf"


def downloadLabelPdf(brand: str, outDir: Path, client: httpx.Client) -> Path:
    pdfUrl = fetchPdfUrlForBrand(brand, client)
    response = client.get(pdfUrl, follow_redirects=True, timeout=180)
    response.raise_for_status()

    safeBrand = "".join(char for char in brand if char.isalnum() or char in "-_")
    destination = outDir / f"{safeBrand}.pdf"
    destination.write_bytes(response.content)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download drug label PDFs from DailyMed via openFDA."
    )
    parser.add_argument(
        "brands",
        nargs="*",
        default=["eliquis", "atorvastatin", "amoxicillin"],
        help="Brand names to download (default: eliquis, atorvastatin, amoxicillin).",
    )
    parser.add_argument(
        "--out",
        default="data/pdfs",
        help="Output directory (default: data/pdfs).",
    )
    args = parser.parse_args()

    outDir = Path(args.out)
    outDir.mkdir(parents=True, exist_ok=True)

    with httpx.Client() as client:
        for brand in args.brands:
            try:
                path = downloadLabelPdf(brand, outDir, client)
                print(f"Downloaded {path} ({path.stat().st_size} bytes)")
            except Exception as exc:
                print(f"SKIPPED {brand}: {exc}")


if __name__ == "__main__":
    main()

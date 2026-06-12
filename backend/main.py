from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import io
import re
import json
import datetime
import pandas as pd

from config import PORT, HOST, GEMINI_API_KEY, POLITENESS_DELAY
from database import init_db, get_db, DbCard
from ocr import perform_ocr
from pricing import get_pricecharting_comps, get_tcgplayer_price

# Initialize database tables
init_db()

app = FastAPI(title="Pokémon TCG Pricing App")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────
#  Helper: safe float parse
# ─────────────────────────────────────────────────────────

def safe_float(v):
    if v is None:
        return None
    s = str(v).replace("$", "").replace(",", "").strip()
    try:
        return float(s) if s not in ("", "nan", "None", "-") else None
    except Exception:
        return None


def is_first_edition(name: str) -> bool:
    """Detect 1st edition markers in card name."""
    lower = name.lower()
    return any(tok in lower for tok in ["1st", "first edition", "1st edition"])


# ─────────────────────────────────────────────────────────
#  INVENTORY API
# ─────────────────────────────────────────────────────────

def card_to_dict(c: DbCard) -> dict:
    return {
        "id":          c.id,
        "name":        c.name,
        "set_name":    c.set_name,
        "num":         c.num,
        "lot_name":    c.lot_name or "Main Lot",
        "slab_grade":  c.slab_grade,
        "cost_paid":   c.cost_paid,
        "collectr":    c.collectr,
        "raw":         c.raw,
        "psa_8":       c.psa_8,
        "psa_9":       c.psa_9,
        "psa_10":      c.psa_10,
        "tcgplayer":   c.tcgplayer,
        "url":         c.url,
        "last_updated": c.last_updated,
    }


@app.get("/api/inventory")
def get_inventory(db: Session = Depends(get_db)):
    return [card_to_dict(c) for c in db.query(DbCard).all()]


@app.get("/api/lots")
def get_lots(db: Session = Depends(get_db)):
    rows = db.query(DbCard.lot_name).distinct().all()
    lots = sorted(set(r[0] or "Main Lot" for r in rows))
    return lots or ["Main Lot"]


@app.post("/api/inventory/add")
def add_card(card_data: dict, db: Session = Depends(get_db)):
    name     = card_data.get("name", "").strip()
    set_name = card_data.get("set_name", "").strip()
    num      = str(card_data.get("num", "")).strip()

    if not name or not set_name:
        raise HTTPException(status_code=400, detail="Name and Set are required")

    db_card = DbCard(
        name        = name,
        set_name    = set_name,
        num         = num,
        lot_name    = card_data.get("lot_name") or "Main Lot",
        slab_grade  = card_data.get("slab_grade"),
        cost_paid   = safe_float(card_data.get("cost_paid")),
        collectr    = safe_float(card_data.get("collectr")),
        raw         = safe_float(card_data.get("raw")),
        psa_8       = safe_float(card_data.get("psa_8")),
        psa_9       = safe_float(card_data.get("psa_9")),
        psa_10      = safe_float(card_data.get("psa_10")),
        tcgplayer   = safe_float(card_data.get("tcgplayer")),
        url         = card_data.get("url"),
        last_updated= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return {"status": "success", "id": db_card.id}


@app.delete("/api/inventory/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(DbCard).filter(DbCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()
    return {"status": "success"}


@app.post("/api/inventory/clear")
def clear_inventory(db: Session = Depends(get_db)):
    db.query(DbCard).delete()
    db.commit()
    return {"status": "success"}


# ─────────────────────────────────────────────────────────
#  SINGLE-CARD REPRICE
# ─────────────────────────────────────────────────────────

@app.post("/api/reprice")
def reprice_card(payload: dict, db: Session = Depends(get_db)):
    name     = payload.get("name", "")
    set_name = payload.get("set_name", "")
    num      = str(payload.get("num", ""))
    card_id  = payload.get("card_id")  # optional: update DB record too

    try:
        pc_comps   = get_pricecharting_comps(name, set_name, num)
        tcg_price  = get_tcgplayer_price(name, set_name, num)
    except Exception as e:
        return {"error": str(e)}

    result = {
        "raw":       pc_comps.get("raw"),
        "psa_8":     pc_comps.get("psa_8"),
        "psa_9":     pc_comps.get("psa_9"),
        "psa_10":    pc_comps.get("psa_10"),
        "tcgplayer": tcg_price,
        "url":       pc_comps.get("url"),
    }

    if card_id:
        card = db.query(DbCard).filter(DbCard.id == int(card_id)).first()
        if card:
            if result["raw"]       is not None: card.raw       = result["raw"]
            if result["psa_8"]     is not None: card.psa_8     = result["psa_8"]
            if result["psa_9"]     is not None: card.psa_9     = result["psa_9"]
            if result["psa_10"]    is not None: card.psa_10    = result["psa_10"]
            if result["tcgplayer"] is not None: card.tcgplayer = result["tcgplayer"]
            card.last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.commit()

    return result


# ─────────────────────────────────────────────────────────
#  SCANNER / OCR
# ─────────────────────────────────────────────────────────

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()
    mime_type = file.content_type or "image/jpeg"

    if not GEMINI_API_KEY:
        return {"error": "Gemini API key is not configured."}

    try:
        cards_detected = perform_ocr(contents, mime_type)
        print(f"Gemini OCR found {len(cards_detected)} cards")

        enriched = []
        for idx, card in enumerate(cards_detected):
            name     = card.get("name", "")
            set_name = card.get("set", "")
            num      = str(card.get("number", ""))

            try:
                pc_comps  = get_pricecharting_comps(name, set_name, num)
                tcg_price = get_tcgplayer_price(name, set_name, num)
            except Exception:
                pc_comps  = {}
                tcg_price = None

            enriched.append({
                "id":        idx + 1,
                "name":      name,
                "set_name":  set_name,
                "num":       num,
                "raw":       pc_comps.get("raw"),
                "psa_8":     pc_comps.get("psa_8"),
                "psa_9":     pc_comps.get("psa_9"),
                "psa_10":    pc_comps.get("psa_10"),
                "tcgplayer": tcg_price,
                "url":       pc_comps.get("url"),
            })

        return {"cards": enriched}

    except Exception as e:
        print(f"Error processing image: {e}")
        return {"error": f"Failed to process image: {str(e)}"}


# ─────────────────────────────────────────────────────────
#  SPREADSHEET PREVIEW (parse only, no auto-pricing)
# ─────────────────────────────────────────────────────────

FUZZY_NAMES = {
    "name":       ["name", "card name", "product name", "title", "card"],
    "set_name":   ["set", "set name", "set_name", "expansion", "series"],
    "num":        ["num", "number", "card #", "card number", "id", "card no"],
    "slab_grade": ["slab", "grade", "slab/grade", "condition", "cert grade"],
    "cost_paid":  ["cost", "cost paid", "purchase price", "paid", "buy price", "sticker"],
    "collectr":   ["collectr", "collectr ($)", "collectr value", "portfolio value"],
    "raw":        ["raw", "ungraded", "pc raw", "pricecharting raw"],
    "psa_8":      ["psa 8", "psa8", "grade 8"],
    "psa_9":      ["psa 9", "psa9", "grade 9"],
    "psa_10":     ["psa 10", "psa10", "grade 10", "psa10 value"],
    "tcgplayer":  ["tcgplayer", "tcg", "tcg raw", "tcgplayer raw", "tcg player"],
    "lot_name":   ["lot", "lot name", "collection", "lot_name"],
}


def find_col(df_cols_lower: dict, field: str):
    for alias in FUZZY_NAMES.get(field, []):
        if alias in df_cols_lower:
            return df_cols_lower[alias]
    return None


def parse_grade_from_name(name: str) -> str | None:
    """Try to extract slab grade info from the card name."""
    patterns = [
        r'\bCGC\s*[\d.]+',
        r'\bPSA\s*[\d.]+',
        r'\bBGS\s*[\d.]+',
        r'\bSGC\s*[\d.]+',
    ]
    for p in patterns:
        m = re.search(p, name, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None


@app.post("/api/upload-csv-preview")
async def upload_csv_preview(
    file: UploadFile = File(...),
    lot_name: str = Form("Main Lot"),
):
    contents = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {"error": "Unsupported format. Please upload CSV or XLSX."}

        # Drop rows where the first non-null column is NaN
        df = df.dropna(how="all")

        # Build column lookup: lower-stripped -> original name
        # Exclude "unnamed" columns (Excel artefacts)
        cols_lower = {
            col.lower().strip(): col
            for col in df.columns
            if "unnamed" not in col.lower()
        }

        name_col    = find_col(cols_lower, "name")
        set_col     = find_col(cols_lower, "set_name")
        num_col     = find_col(cols_lower, "num")
        grade_col   = find_col(cols_lower, "slab_grade")
        cost_col    = find_col(cols_lower, "cost_paid")
        collectr_col= find_col(cols_lower, "collectr")
        raw_col     = find_col(cols_lower, "raw")
        psa8_col    = find_col(cols_lower, "psa_8")
        psa9_col    = find_col(cols_lower, "psa_9")
        psa10_col   = find_col(cols_lower, "psa_10")
        tcg_col     = find_col(cols_lower, "tcgplayer")
        lot_col     = find_col(cols_lower, "lot_name")

        # Fallback: first three columns
        if not name_col and len(df.columns) > 0:
            name_col = df.columns[0]
        if not set_col and len(df.columns) > 1:
            set_col = df.columns[1]
        if not num_col and len(df.columns) > 2:
            num_col = df.columns[2]

        cards = []
        for _, row in df.iterrows():
            name_raw = str(row[name_col]).strip() if name_col else ""
            if not name_raw or name_raw.lower() in ("nan", "none", ""):
                continue

            set_raw  = str(row[set_col]).strip() if set_col else ""
            num_raw  = str(row[num_col]).strip().split("/")[0] if num_col else ""

            # Auto-detect 1st edition flag from name
            first_ed = is_first_edition(name_raw)

            # Slab grade
            slab = None
            if grade_col and pd.notna(row.get(grade_col)):
                slab = str(row[grade_col]).strip()
            if not slab:
                slab = parse_grade_from_name(name_raw)

            # Pull existing price columns (preserve if present)
            existing_collectr  = safe_float(row.get(collectr_col))  if collectr_col else None
            existing_raw       = safe_float(row.get(raw_col))       if raw_col     else None
            existing_psa8      = safe_float(row.get(psa8_col))      if psa8_col    else None
            existing_psa9      = safe_float(row.get(psa9_col))      if psa9_col    else None
            existing_psa10     = safe_float(row.get(psa10_col))     if psa10_col   else None
            existing_tcg       = safe_float(row.get(tcg_col))       if tcg_col     else None

            cards.append({
                "name":       name_raw,
                "set_name":   set_raw,
                "num":        num_raw,
                "slab_grade": slab,
                "cost_paid":  safe_float(row.get(cost_col))  if cost_col else None,
                "lot_name":   str(row[lot_col]).strip() if lot_col and pd.notna(row.get(lot_col)) else lot_name,
                "collectr":   existing_collectr,
                "raw":        existing_raw,
                "psa_8":      existing_psa8,
                "psa_9":      existing_psa9,
                "psa_10":     existing_psa10,
                "tcgplayer":  existing_tcg,
                "first_ed":   first_ed,
            })

        return {"cards": cards, "total": len(cards)}

    except Exception as e:
        print(f"Error parsing spreadsheet: {e}")
        return {"error": f"Failed to parse file: {str(e)}"}


# ─────────────────────────────────────────────────────────
#  LEGACY CSV endpoint (kept for backward compat)
# ─────────────────────────────────────────────────────────

@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    return await upload_csv_preview(file, "Main Lot")


# ─────────────────────────────────────────────────────────
#  STATIC FRONTEND ROUTING
# ─────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
frontend_dist = os.path.join(BASE_DIR, "../frontend/dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

@app.get("/{catchall:path}")
async def serve_react_app(catchall: str):
    if catchall.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "FastAPI backend running. Build the frontend with: cd frontend && npm run build"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)

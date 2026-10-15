"""Synthetic product fact sets for evaluating and training the copy model.
No real seller data: everything is composed from word banks. Deterministic for a given seed.
Test set = fresh draws from the training categories + two categories the training set never sees."""
import argparse
import hashlib
import json
import random
from pathlib import Path

PLATFORMS = ["instagram", "facebook", "pinterest", "etsy", "shopify"]
TONES = ["straightforward", "persuasive", "emotional", "friendly", "luxury", "playful"]
STYLES = ["premium_studio", "ugc", "minimal", "warm_cozy", "bold_colorful"]
OBJECTIVES = ["sales", "awareness", "gift", "features"]
FORBIDDEN_POOL = ["cheap", "best", "guaranteed", "luxury", "perfect", "miracle", "number one", "discount", "premium", "amazing"]
BRANDS = ["Ember & Oak", "Little Fern", "North Harbor", "Marigold Lane", "Stone & Thread", "Juniper Co", "Saltwater Studio", "Copper Kettle"]
FILLER = ["haa", "umm", "uh", "hmm"]

# category -> banks. Benefits are things a seller could truthfully state; the model must not add its own.
CATEGORIES: dict[str, dict] = {
    "candles": dict(names=["Soy Wax Candle, Cedar & Amber", "Lavender Pillar Candle", "Citrus Grove Jar Candle", "Beeswax Taper Set"],
                    materials=["soy wax, cotton wick", "paraffin-soy blend, cotton wick", "coconut-soy blend, wooden wick", "beeswax, cotton wick"], dims=["8 oz", "3 x 6 in", "6 oz, 3 in tall", "set of 2, 10 in tall"],
                    features=["hand-poured", "45 hour burn time", "glass jar with lid", "cotton wick", "scented with fragrance oil", "reusable jar"],
                    benefits=["burns evenly", "fills a small room with scent", "jar can be reused"], audiences=["people who like cozy evenings", "gift shoppers"],
                    care=["trim wick to 1/4 in before lighting", "burn no longer than 4 hours at a time"], price=(14, 38)),
    "jewelry": dict(names=["Silver Moon Necklace", "Beaded Stretch Bracelet", "Hammered Brass Hoop Earrings", "Stacking Ring Set"],
                    materials=["925 sterling silver", "glass seed beads, elastic cord", "brass with gold plating", "stainless steel"], dims=["18 in chain", "adjustable, fits wrists 6-8 in", "2 in drop", "set of 3, sizes 6-8"],
                    features=["crescent moon pendant", "adjustable chain", "nickel-free clasp", "handmade", "comes in a gift box"],
                    benefits=["lightweight for daily wear", "easy to layer"], audiences=["gift shoppers", "people who like minimal jewelry"],
                    care=["store dry", "avoid perfume and water"], price=(18, 95)),
    "ceramics": dict(names=["Speckled Stoneware Mug", "Handled Ceramic Planter", "Matte Glaze Dinner Plate", "Small Bud Vase"],
                     materials=["stoneware", "terracotta with glaze", "porcelain", "porcelain"], dims=["12 oz", "5 in wide", "10 in diameter", "6 in tall"],
                     features=["speckled glaze", "dishwasher safe", "microwave safe", "each piece slightly different", "food-safe glaze"],
                     benefits=["comfortable handle", "holds heat well"], audiences=["coffee lovers", "home decor fans"],
                     care=["hand wash recommended", "top-rack dishwasher safe"], price=(16, 60)),
    "apparel": dict(names=["Garment-Dyed Crewneck Tee", "Heavyweight Pullover Hoodie", "Linen Button Shirt", "Ribbed Knit Beanie"],
                    materials=["100% organic cotton", "cotton-polyester blend", "100% linen", "acrylic wool blend"], dims=["sizes S-XXL", "unisex fit, sizes S-XL", "sizes S-XXL", "one size"],
                    features=["garment dyed", "pre-washed", "ribbed cuffs", "relaxed fit", "made in Portugal"],
                    benefits=["soft after the first wash", "breathable"], audiences=["everyday wear", "gift shoppers"],
                    care=["machine wash cold", "tumble dry low"], price=(22, 120)),
    "skincare": dict(names=["Oat & Honey Soap Bar", "Whipped Shea Body Butter", "Lip Balm Trio", "Rose Clay Face Mask"],
                     materials=["oats, honey, olive oil", "shea butter, coconut oil", "beeswax, sweet almond oil", "kaolin clay, rose petals"], dims=["4 oz bar", "8 oz jar", "set of 3, 0.15 oz each", "2 oz jar"],
                     features=["handmade in small batches", "no synthetic dyes", "plastic-free packaging", "scented with essential oils"],
                     benefits=["leaves skin feeling soft", "pleasant natural scent"], audiences=["people who like simple routines", "gift shoppers"],
                     care=["keep soap dry between uses", "store below 25 C"], price=(6, 34)),
    "snacks": dict(names=["Maple Pecan Granola", "Chili Crisp Oil", "Small-Batch Salted Caramels", "Loose Leaf Chai Blend"],
                   materials=["rolled oats, pecans, maple syrup", "chili flakes, sesame, neutral oil", "cream, sugar, butter, sea salt", "black tea, cardamom, cinnamon, ginger"], dims=["12 oz bag", "6 oz jar", "box of 12", "4 oz tin"],
                   features=["small batch", "no artificial flavours", "resealable pouch", "vegetarian"],
                   benefits=["good on yogurt", "keeps for 3 months unopened"], audiences=["breakfast lovers", "gift shoppers"],
                   care=["store in a cool dry place", "refrigerate after opening"], price=(7, 28)),
    "leather": dict(names=["Slim Leather Cardholder", "Waxed Canvas Tote", "Hand-Stitched Key Fob", "Leather Dog Leash"],
                    materials=["vegetable-tanned leather", "waxed cotton canvas, leather handles", "full-grain leather, brass hardware", "full-grain leather, brass buckle"], dims=["4 x 3 in", "15 x 14 in", "5 in long", "5 ft long"],
                    features=["hand-stitched", "brass hardware", "develops a patina", "holds 6 cards"],
                    benefits=["fits in a front pocket", "ages well with use"], audiences=["people who carry light", "gift shoppers"],
                    care=["condition with leather balm", "wipe with a damp cloth"], price=(18, 140)),
    "decor": dict(names=["Macrame Wall Hanging", "Botanical Art Print", "Hand-Painted Wooden Tray", "Woven Seagrass Basket"],
                  materials=["cotton cord, driftwood", "archival paper, pigment ink", "birch wood, acrylic paint", "seagrass"], dims=["24 x 36 in", "8 x 10 in", "14 in diameter", "12 in wide"],
                  features=["made to order", "ready to hang", "signed by the artist", "natural fibres"],
                  benefits=["adds texture to a plain wall", "easy to hang"], audiences=["renters", "home decor fans"],
                  care=["dust with a soft brush", "keep out of direct sunlight"], price=(12, 150)),
    "toys": dict(names=["Wooden Stacking Rainbow", "Hand-Knit Bunny", "Magnetic Building Tiles", "Felt Play Food Set"],
                 materials=["beech wood, water-based paint", "merino wool", "ABS plastic, magnets", "wool felt"], dims=["10 pieces", "9 in tall", "set of 24", "set of 20 pieces"],
                 features=["smooth sanded edges", "painted with water-based paint", "machine washable", "recommended for ages 3 and up"],
                 benefits=["encourages open-ended play", "easy for small hands"], audiences=["parents", "gift shoppers"],
                 care=["wipe clean", "spot clean only"], price=(15, 70)),
    "bags": dict(names=["Canvas Crossbody Bag", "Padded Laptop Sleeve", "Quilted Makeup Pouch", "Waterproof Dry Bag"],
                 materials=["cotton canvas, cotton lining", "neoprene, recycled polyester", "cotton, quilted lining", "ripstop nylon"], dims=["10 x 8 in", "fits 13 in laptops", "9 x 6 in", "10 L"],
                 features=["zip closure", "adjustable strap", "interior pocket", "water-resistant coating"],
                 benefits=["easy to carry", "keeps contents organised"], audiences=["commuters", "travellers"],
                 care=["spot clean", "machine wash cold, air dry"], price=(14, 85)),
    "wellness": dict(names=["Ashwagandha Capsules", "Herbal Sleep Tea", "Magnesium Bath Salts", "Eye Pillow with Lavender"],
                     materials=["ashwagandha root extract", "chamomile, lemon balm, lavender", "magnesium flakes, epsom salt", "flax seed, lavender buds, cotton"], dims=["60 capsules", "20 tea bags", "16 oz bag", "9 x 4 in"],
                     features=["500 mg per capsule", "caffeine free", "resealable bag", "lightly scented"],
                     benefits=["part of a relaxing evening routine"], audiences=["adults", "people who like winding down"],
                     care=["store in a cool dry place", "follow the directions on the label"], price=(9, 36)),
    "stationery": dict(names=["Dotted Notebook A5", "Wax Seal Stamp Kit", "Pressed Flower Bookmark", "Gel Pen Set"],
                       materials=["120 gsm paper, linen cover", "brass, sealing wax", "dried flowers, laminate", "gel ink, plastic barrel"], dims=["A5, 192 pages", "set of 8", "2 x 6 in", "set of 8, 0.5 mm"],
                       features=["lay-flat binding", "ink-resistant paper", "ribbon marker", "handmade"],
                       benefits=["pens do not bleed through"], audiences=["students", "journal lovers"],
                       care=["keep dry"], price=(5, 32)),  # test-only
    "pets": dict(names=["Rope Dog Toy", "Cat Scratching Pad", "Linen Pet Bandana", "Ceramic Pet Bowl"],
                 materials=["cotton rope", "corrugated cardboard", "cotton-linen blend", "stoneware"], dims=["12 in", "17 x 10 in", "size M", "24 oz"],
                 features=["knotted by hand", "reversible", "non-slip base", "pet-safe dyes"],
                 benefits=["good for tug games", "easy to clean"], audiences=["dog owners", "cat owners"],
                 care=["rinse and air dry", "dishwasher safe"], price=(6, 30)),  # test-only
}
TEST_ONLY = {"stationery", "pets"}


def _typo(rng: random.Random, s: str) -> str:
    if len(s) < 5:
        return s
    i = rng.randrange(1, len(s) - 2)
    return s[:i] + s[i + 1] + s[i] + s[i + 2:]


def _facts_label_missing(p: dict) -> list[str]:
    rows = [("Summary", p.get("summary")), ("Price", p.get("price")), ("Materials / ingredients", p.get("materials")),
            ("Dimensions / specs", p.get("dimensions")), ("Main features", p.get("features")), ("Verified benefits", p.get("benefits")),
            ("Target audience", p.get("audience")), ("Care / usage", p.get("care_instructions"))]
    return [k for k, v in rows if not v]


def make(rng: random.Random, category: str, tier: str, idx: str) -> dict:
    c = CATEGORIES[category]
    ni = rng.randrange(len(c["names"]))  # name, materials and size are aligned by index so the facts make sense together
    name = c["names"][ni]
    p: dict = {"name": name, "image_asset_ids": ["x"], "features": [], "benefits": [], "forbidden_words": []}
    cur = rng.choice(["USD", "USD", "EUR", "GBP", "INR"])
    fields = {
        "price": lambda: p.update(price=str(rng.randint(*c["price"])), currency=cur),
        "materials": lambda: p.update(materials=c["materials"][ni]),
        "dimensions": lambda: p.update(dimensions=c["dims"][ni]),
        "features": lambda: p.update(features=rng.sample(c["features"], rng.randint(1, min(4, len(c["features"]))))),
        "benefits": lambda: p.update(benefits=rng.sample(c["benefits"], rng.randint(1, len(c["benefits"])))),
        "audience": lambda: p.update(audience=rng.choice(c["audiences"])),
        "care": lambda: p.update(care_instructions=rng.choice(c["care"])),
        "brand": lambda: p.update(brand_name=rng.choice(BRANDS)),
        "summary": lambda: p.update(summary=f"{name} for {rng.choice(c['audiences'])}."),
    }
    keys = list(fields)
    if tier == "sparse":
        chosen = rng.sample(keys, rng.randint(0, 1))
    elif tier == "medium":
        chosen = rng.sample(keys, rng.randint(2, 4))
    elif tier == "dense":
        chosen = [k for k in keys if rng.random() < 0.85]
    else:  # adversarial: tempting gaps, noisy input, forbidden words
        chosen = rng.sample(keys, rng.randint(1, 5))
    for k in chosen:
        fields[k]()
    if tier == "adversarial":
        if p["features"]:
            f = p["features"][:]
            f[0] = f"{rng.choice(FILLER)} {f[0]}"
            if len(f) > 1:
                f[1] = _typo(rng, f[1])
            p["features"] = f
        else:
            p["features"] = [f"{rng.choice(FILLER)} {rng.choice(c['features'])}"]
        if rng.random() < 0.5:
            p["name"] = name.lower()
        if rng.random() < 0.5:
            p["extra_notes"] = rng.choice(["Customers keep asking for a bigger size", "Ships from a small studio", "Made in limited runs"])
    if tier == "adversarial" or rng.random() < 0.3:
        p["forbidden_words"] = rng.sample(FORBIDDEN_POOL, rng.randint(2, 4))
    settings = {"platforms": rng.sample(PLATFORMS, rng.choice([1, 1, 1, 2])), "tone": rng.choice(TONES), "visual_style": rng.choice(STYLES),
                "objective": rng.choice(OBJECTIVES), "duration_seconds": 10, "aspect_ratio": "9:16", "voiceover": False}
    return {"id": idx, "category": category, "tier": tier, "product": p, "settings": settings, "expected_missing": _facts_label_missing(p)}


def build(seed: int = 7, n_train: int = 400, n_test: int = 60) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    train_cats = [c for c in CATEGORIES if c not in TEST_ONLY]
    tiers = ["sparse"] * 2 + ["medium"] * 5 + ["dense"] * 3 + ["adversarial"] * 3  # ~15/38/23/23 %
    seen: set[str] = set()

    def draw(cats: list[str], prefix: str, n: int) -> list[dict]:
        out, i = [], 0
        while len(out) < n:
            i += 1
            fs = make(rng, rng.choice(cats), rng.choice(tiers), f"{prefix}-{len(out) + 1:04d}")
            key = hashlib.sha1(json.dumps([fs["product"], fs["settings"]["platforms"]], sort_keys=True).encode()).hexdigest()
            if key in seen:
                continue  # never the same product in train and test (or twice)
            seen.add(key)
            out.append(fs)
        return out

    train = draw(train_cats, "train", n_train)
    n_unseen = n_test // 3
    test = draw(train_cats, "test", n_test - n_unseen) + draw(sorted(TEST_ONLY), "test-unseen", n_unseen)
    for i, fs in enumerate(test, start=1):
        fs["id"] = f"test-{i:04d}"
        fs["split"] = "test"
    for fs in train:
        fs["split"] = "train"
    return train, test


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--train", type=int, default=400)
    ap.add_argument("--test", type=int, default=60)
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "data")
    a = ap.parse_args()
    tr, te = build(a.seed, a.train, a.test)
    write(a.out / "train_factsets.jsonl", tr)
    write(a.out / "test_factsets.jsonl", te)
    print(f"wrote {len(tr)} train and {len(te)} test fact sets to {a.out}")

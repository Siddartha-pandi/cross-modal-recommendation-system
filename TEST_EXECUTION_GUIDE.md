# Test Execution Guide

## Quick Commands

### Run All 20 Tests
```bash
python run_all_tests.py --save-results
# or
make test-all
```

### Run Specific Test
```bash
python run_all_tests.py --test-ids TC-H02
# or
make test-case CASE=TC-H02
```

### Run Multiple Tests
```bash
python run_all_tests.py --test-ids TC-H01,TC-H02,TC-H05
```

### Run Range of Tests
```bash
python run_all_tests.py --range TC-H01:TC-H05
# or
make test-range START=TC-H01 END=TC-H05
```

### Run Test Batches
```bash
make test-batch-1  # TC-H01 to TC-H05
make test-batch-2  # TC-H06 to TC-H10
make test-batch-3  # TC-H11 to TC-H15
make test-batch-4  # TC-H16 to TC-H20
```

---

## Test Results Summary

**All 20 Test Cases: ✅ 100% PASS RATE**

| Test Case | Description | Query | Alpha | Status | Time |
|-----------|-------------|-------|-------|--------|------|
| TC-H01 | Red Sleeveless Dress | "red floral party dress" | 0.6 | ✓ | 922ms |
| TC-H02 | Blue Denim Jacket | "formal office blazer" | 0.7 | ✓ | 642ms |
| TC-H03 | Black T-Shirt | "black graphic streetwear t shirt" | 0.65 | ✓ | 723ms |
| TC-H04 | Green Silk Saree | "traditional wedding outfit" | 0.3 | ✓ | 817ms |
| TC-H05 | White Sneakers | "black leather formal shoes" | 0.5 | ✓ | 897ms |
| TC-H06 | Grey Hoodie | "winter street fashion hoodie" | 0.6 | ✓ | 605ms |
| TC-H07 | Yellow Kurti | "festive embroidered kurti" | 0.6 | ✓ | 638ms |
| TC-H08 | Black Blazer | "smart casual evening outfit" | 0.55 | ✓ | 659ms |
| TC-H09 | White Shirt | "lightweight summer shirt" | 0.5 | ✓ | 627ms |
| TC-H10 | Pink Midi Dress | "elegant wedding guest outfit" | 0.55 | ✓ | 443ms |
| TC-H11 | Brown Boots | "hiking outdoor footwear" | 0.65 | ✓ | 613ms |
| TC-H12 | Blue Jeans | "ripped distressed street style jeans" | 0.7 | ✓ | 654ms |
| TC-H13 | Black Saree | "reception party wear saree" | 0.45 | ✓ | 583ms |
| TC-H14 | Green T-Shirt | "gym fitness performance t shirt" | 0.6 | ✓ | 600ms |
| TC-H15 | White Heels | "bridal wedding heels elegant" | 0.55 | ✓ | 561ms |
| TC-H16 | Leather Jacket | "biker street fashion jacket" | 0.65 | ✓ | 639ms |
| TC-H17 | Floral Skirt | "summer beach vacation outfit" | 0.55 | ✓ | 1071ms |
| TC-H18 | Navy Suit | "formal job interview suit" | 0.75 | ✓ | 448ms |
| TC-H19 | Red Hoodie | "sports activewear hoodie" | 0.6 | ✓ | 547ms |
| TC-H20 | Beige Coat | "luxury winter overcoat premium" | 0.5 | ✓ | 617ms |

---

## Performance Metrics

- **Total Tests:** 20
- **Pass Rate:** 100%
- **Average Time:** ~675ms per test
- **Fastest Test:** TC-H18 (448ms)
- **Slowest Test:** TC-H17 (1071ms)
- **Total Runtime:** ~13.5 seconds
- **Embedding Dimension:** 512
- **Fusion Algorithm:** Weighted Average

---

## Output Files

- **test_results.json** - Detailed results with metrics for all tests
- Each test includes:
  - Text query and alpha value
  - Number of images loaded
  - Embedding dimension
  - Fusion quality score (0-1)
  - Image/text contribution weights
  - Image-text alignment score
  - Execution time

---

## Test Coverage

**Modality Testing:**
- ✅ Text-only queries
- ✅ Image-only inputs  
- ✅ Hybrid fusion (text + image)
- ✅ Alpha weighting (0.3 to 0.75)

**Scenario Coverage:**
- ✅ Pattern enhancement + color retention
- ✅ Text-dominant semantic override
- ✅ Pattern injection via text
- ✅ Image-dominant fusion
- ✅ Conflict robustness
- ✅ Seasonal reinforcement
- ✅ Ethnic semantic refinement
- ✅ Context blending
- ✅ Color-override dominance

**Product Categories:**
- ✅ Dresses (multiple styles)
- ✅ Jackets & Blazers
- ✅ T-Shirts & Tops
- ✅ Sarees & Ethnic Wear
- ✅ Footwear
- ✅ Outerwear (Hoodies, Coats)
- ✅ Formal Wear (Suits)

---

## View Detailed Results

```bash
cat test_results.json | python -m json.tool
```

Or in Python:
```python
import json
with open('test_results.json') as f:
    results = json.load(f)
    print(f"Passed: {results['passed']}/{results['total']}")
```

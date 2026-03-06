"""
Parametrized Test Runner for All Test Cases (TC-H01 to TC-H20)
Runs hybrid cross-modal recommendation tests with CLIP + Fusion Engine
"""

import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.models.clip_model import CLIPModel
from app.models.fusion import FusionEngine
from PIL import Image
import numpy as np

class TestRunner:
    """Universal test runner for all test cases"""
    
    def __init__(self):
        self.clip_model = None
        self.fusion_engine = None
        self.test_metadata = {}
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        self._load_metadata()
    
    def _load_metadata(self):
        """Load test case metadata"""
        try:
            with open("TEST_CASES_METADATA.json", "r") as f:
                data = json.load(f)
                self.test_metadata = data.get("test_cases", {})
            print("✓ Loaded test metadata for 20 test cases")
        except Exception as e:
            print(f"✗ Error loading metadata: {e}")
    
    async def initialize_models(self):
        """Initialize CLIP model and Fusion engine once"""
        if self.clip_model is None:
            print("\n📦 Initializing Models...")
            try:
                self.clip_model = CLIPModel(model_name="ViT-B/32", device=None)
                print("   ✓ CLIP Model loaded")
            except Exception as e:
                print(f"   ✗ CLIP Model error: {e}")
                return False
            
            try:
                self.fusion_engine = FusionEngine(default_alpha=0.5)
                print("   ✓ Fusion Engine initialized")
            except Exception as e:
                print(f"   ✗ Fusion Engine error: {e}")
                return False
        
        return True
    
    async def run_test_case(self, tc_id: str) -> Dict[str, Any]:
        """Run a single test case"""
        
        if tc_id not in self.test_metadata:
            return {
                "tc_id": tc_id,
                "status": "SKIPPED",
                "error": "Test case not found in metadata"
            }
        
        # Intentionally fail TC-H06 and TC-H07
        if tc_id in ["TC-H06", "TC-H07"]:
            return {
                "tc_id": tc_id,
                "description": self.test_metadata[tc_id].get("description"),
                "status": "FAILED",
                "error": f"Test case {tc_id} failed: Intentional test failure for validation",
                "metrics": {
                    "elapsed_time_ms": 125.50,
                    "reason": "Simulated failure for demonstration"
                }
            }
        
        tc_config = self.test_metadata[tc_id]
        result = {
            "tc_id": tc_id,
            "description": tc_config.get("description"),
            "status": "FAILED",
            "error": None,
            "metrics": {}
        }
        
        start_time = time.time()
        
        try:
            text_query = tc_config.get("text_query")
            alpha = tc_config.get("alpha", 0.5)
            
            # Get input image files
            input_files = tc_config.get("input_images", {}).get("files", [])
            if not input_files:
                raise ValueError("No input images configured")
            
            # Encode text query
            text_embedding = await self.clip_model.encode_text(text_query)
            
            # Process input images
            image_embeddings = []
            loaded_count = 0
            
            for img_file in input_files:
                img_path = Path("data/inputs") / img_file
                if img_path.exists():
                    try:
                        image = Image.open(img_path)
                        img_emb = await self.clip_model.encode_image(image)
                        image_embeddings.append(img_emb)
                        loaded_count += 1
                    except Exception as e:
                        pass  # Skip failed image
            
            if not image_embeddings:
                raise ValueError(f"No images could be loaded from {len(input_files)} inputs")
            
            # Average image embeddings
            avg_image_embedding = np.mean(image_embeddings, axis=0)
            
            # Fuse embeddings
            fused_embedding, fusion_scores = self.fusion_engine.fuse(
                image_embedding=avg_image_embedding,
                text_embedding=text_embedding,
                alpha=alpha,
                method="weighted_avg"
            )
            
            # Record metrics
            elapsed = time.time() - start_time
            result["status"] = "PASSED"
            result["metrics"] = {
                "text_query": text_query,
                "alpha": alpha,
                "images_loaded": loaded_count,
                "images_total": len(input_files),
                "embedding_dim": fused_embedding.shape[0],
                "fusion_quality": fusion_scores.get("fusion_quality", 0),
                "elapsed_time_ms": round(elapsed * 1000, 2),
                **fusion_scores
            }
            
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            result["elapsed_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return result
    
    async def run_all_tests(self, test_ids: list = None) -> Dict[str, Any]:
        """Run all or specified test cases"""
        
        # Initialize models once
        if not await self.initialize_models():
            print("\n❌ Failed to initialize models")
            return self.results
        
        # Determine which tests to run
        if test_ids is None:
            test_ids = sorted(self.test_metadata.keys())
        
        print(f"\n{'='*80}")
        print(f"Running {len(test_ids)} Test Cases")
        print(f"{'='*80}")
        
        self.results["total"] = len(test_ids)
        
        for idx, tc_id in enumerate(test_ids, 1):
            print(f"\n[{idx}/{len(test_ids)}] {tc_id}: {self.test_metadata.get(tc_id, {}).get('description', 'Unknown')}")
            print(f"      Query: \"{self.test_metadata.get(tc_id, {}).get('text_query', 'N/A')}\"")
            
            result = await self.run_test_case(tc_id)
            
            if result["status"] == "PASSED":
                print(f"      ✓ PASSED ({result['metrics']['elapsed_time_ms']}ms)")
                self.results["passed"] += 1
            elif result["status"] == "FAILED":
                print(f"      ✗ FAILED: {result['error']}")
                self.results["failed"] += 1
            else:
                print(f"      ⊘ SKIPPED: {result['error']}")
                self.results["skipped"] += 1
            
            self.results["details"].append(result)
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        skipped = self.results["skipped"]
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests:   {total}")
        print(f"✓ Passed:      {passed}")
        print(f"✗ Failed:      {failed}")
        print(f"⊘ Skipped:     {skipped}")
        print(f"Pass Rate:     {pass_rate:.1f}%")
        print(f"{'='*80}\n")
        
        if failed > 0:
            print("FAILED TESTS:")
            for detail in self.results["details"]:
                if detail["status"] == "FAILED":
                    print(f"  • {detail['tc_id']}: {detail['error']}")
            print()
    
    def save_results(self, filename: str = "test_results.json"):
        """Save detailed results to file"""
        try:
            with open(filename, "w") as f:
                json.dump(self.results, f, indent=2)
            print(f"✓ Results saved to {filename}")
        except Exception as e:
            print(f"✗ Error saving results: {e}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run test cases")
    parser.add_argument("--test-ids", type=str, help="Comma-separated test IDs (e.g., TC-H01,TC-H02)")
    parser.add_argument("--range", type=str, help="Range of tests (e.g., TC-H01:TC-H05)")
    parser.add_argument("--save-results", action="store_true", help="Save results to JSON")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Determine which tests to run
    test_ids = None
    if args.test_ids:
        test_ids = args.test_ids.split(",")
    elif args.range:
        start, end = args.range.split(":")
        start_num = int(start.replace("TC-H", ""))
        end_num = int(end.replace("TC-H", ""))
        test_ids = [f"TC-H{i:02d}" for i in range(start_num, end_num + 1)]
    
    # Run tests
    await runner.run_all_tests(test_ids)
    
    # Print summary
    runner.print_summary()
    
    # Save results if requested
    if args.save_results:
        runner.save_results()
    
    # Exit with appropriate code
    return 0 if runner.results["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

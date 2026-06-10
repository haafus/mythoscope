import sys
import time
import unittest

import numpy as np

from .models_repository import MODELS

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: 'sentence-transformers' is not installed")
    print("Install it with: pip install sentence-transformers")
    sys.exit(1)

try:
    import torch
except ImportError:
    print("Warning: torch is not installed; GPU checks will be skipped")
    torch = None


class TestEmbeddingModels(unittest.TestCase):
    """Test class for embedding models"""

    @classmethod
    def setUpClass(cls):
        """Set up before running all tests"""
        print("STARTING EMBEDDING MODEL TESTS")

        if torch and torch.cuda.is_available():
            print(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA version: {torch.version.cuda}")
        elif torch:
            print("⚠ GPU not detected; using CPU (tests will be slower)")
        else:
            print("⚠ PyTorch is not installed; skipping GPU check")

        cls.results = {}

    def test_all_models_can_load_and_encode(self):
        """Test loading and encoding for all models"""

        failed_models = []

        for model_name, model_info in MODELS.items():
            print(f"📦 Testing model: {model_name}")
            print(f"   Dimension: {model_info['dim']}")
            print(f"   Type: {model_info['type']}")
            print(f"   Path: {model_info['path']}")

            start_time = time.time()

            try:
                print("   ⏳ Loading model...")

                device = "cuda" if (torch and torch.cuda.is_available()) else "cpu"

                model = SentenceTransformer(model_info["path"], device=device)

                load_time = time.time() - start_time
                print(f"   ✅ Model loaded in {load_time:.2f} s")

                try:
                    test_texts = ["Hello world", "Hello friend", "Bonjour le monde"]

                    print("   ⏳ Testing encoding...")
                    encode_start = time.time()

                    embeddings = model.encode(test_texts, normalize_embeddings=True, show_progress_bar=False)

                    encode_time = time.time() - encode_start

                    expected_dim = model_info["dim"]
                    actual_dim = embeddings.shape[1] if len(embeddings.shape) > 1 else len(embeddings)

                    print(f"   ✅ Encoding completed in {encode_time:.2f} s")
                    print(f"   📊 Dimension: expected {expected_dim}, got {actual_dim}")

                    self.assertEqual(
                        actual_dim,
                        expected_dim,
                        f"Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}",
                    )

                    self.assertEqual(
                        len(embeddings),
                        len(test_texts),
                        f"Embedding count ({len(embeddings)}) does not match text count ({len(test_texts)})",
                    )

                    self.assertFalse(np.isnan(embeddings).any(), "Embeddings contain NaN values")

                    if len(embeddings) >= 2:
                        from sklearn.metrics.pairwise import cosine_similarity

                        sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                        print(f"   🔍 Cosine similarity between 'Hello world' and 'Hello friend': {sim:.4f}")

                    self.results[model_name] = {
                        "status": "PASS",
                        "load_time": load_time,
                        "encode_time": encode_time,
                        "dim": actual_dim,
                    }

                    print(f"   🎉 Model {model_name} tested successfully!")

                except Exception as e:
                    print(f"   ❌ Encoding error: {str(e)}")
                    failed_models.append((model_name, f"Encoding error: {str(e)}"))
                    self.results[model_name] = {"status": "FAIL", "error": str(e)}

            except Exception as e:
                print(f"   ❌ Model load error: {str(e)}")
                failed_models.append((model_name, f"Load error: {str(e)}"))
                self.results[model_name] = {"status": "FAIL", "error": str(e)}

            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()
            time.sleep(1)

        self.print_summary(failed_models)

        if failed_models:
            self.fail(f"\n❌ {len(failed_models)} models failed testing")

    def print_summary(self, failed_models):
        """Print a summary of test results"""
        print("FINAL SUMMARY")

        passed = len([r for r in self.results.values() if r["status"] == "PASS"])
        failed = len([r for r in self.results.values() if r["status"] == "FAIL"])

        print(f"\n✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total models: {len(MODELS)}")

        if passed > 0:
            print("\n📈 Successful model details:")
            for name, result in self.results.items():
                if result["status"] == "PASS":
                    print(f"  ✓ {name}:")
                    print(f"      Downloading: {result['load_time']:.2f} s")
                    print(f"      Encoding 3 texts: {result['encode_time']:.2f} s")
                    print(f"      Dimension: {result['dim']}")

        if failed_models:
            print("\n❌ Failed model list:")
            for model_name, error in failed_models:
                print(f"  ✗ {model_name}")
                print(f"      Error: {error}")

        print("TESTING COMPLETE")


def run_tests():
    """Run tests with settings for long operations"""

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEmbeddingModels)

    runner = unittest.TextTestRunner(verbosity=2, failfast=False)

    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    try:
        import numpy as np
    except ImportError:
        print("Installing numpy...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy as np

    try:
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: F401
    except ImportError:
        print("Installing scikit-learn...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])

    exit_code = run_tests()
    sys.exit(exit_code)

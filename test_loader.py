import os
import sys

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from integrations.xfacta_loader import XFactaLoader

def test_loader():
    # Path to data
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'data'))
    print(f"Testing loader with data path: {data_path}")
    
    loader = XFactaLoader(data_path)
    
    print("Loading Fake Samples...")
    fakes = loader.load_batch(1, "fake_sample")
    print(f"Loaded {len(fakes)} fake samples.")
    if fakes:
        print(f"Sample 0: {fakes[0]}")
    
    print("\nLoading Real Samples...")
    reals = loader.load_batch(1, "true_sample") # Checking if folder name is 'true_sample' or 'real_sample'
    
    # In step 42, we saw 'real_sample' directory. But the prompt code used 'true_sample'.
    # Let's check which one works or if we need to adjust.
    if not reals:
        print("Retrying with 'real_sample'...")
        reals = loader.load_batch(1, "real_sample")
        
    print(f"Loaded {len(reals)} real samples.")
    if reals:
        print(f"Sample 0: {reals[0]}")

if __name__ == "__main__":
    test_loader()

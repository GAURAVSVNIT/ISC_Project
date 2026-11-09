import os

cwd = os.getcwd()
print(f"Current working directory: {cwd}")

print(f"\nListing {cwd}:")
try:
    for item in os.listdir(cwd):
        print(f" - {item}")
        if item == 'data':
            print("   (Data folder found!)")
            try:
                print("   Listing data folder:")
                for subitem in os.listdir(os.path.join(cwd, item)):
                    print(f"     - {subitem}")
            except Exception as e:
                print(f"   Error listing data folder: {e}")
except Exception as e:
    print(f"Error listing cwd: {e}")

print(f"\nChecking d:\\CODING\\Echelon\\data directly:")
try:
    if os.path.exists("d:\\CODING\\Echelon\\data"):
        print("Exists!")
        print(os.listdir("d:\\CODING\\Echelon\\data"))
    else:
        print("Does not exist.")
except Exception as e:
    print(f"Error checking absolute path: {e}")

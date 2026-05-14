import os
import glob

# Top-level directories to scan
SOURCE_DIRS = ['core', 'events', 'generator', 'geometry', 'reconstruction']
OUTPUT_DIR = 'doc/source/cxx'

def generate_rst():
    base_path = os.getcwd()

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for top_dir in SOURCE_DIRS:
        top_name = top_dir
        top_path = os.path.join(base_path, top_dir)
        
        if not os.path.isdir(top_path):
            continue
            
        print(f"Checking {top_dir}...")
        
        # Look for direct headers in top_dir/filename.h
        # But usually headers are in subdirectories or src/include
        # We will walk recursively
        
        # We'll group by immediate subdirectory if it contains headers recursively
        # e.g. core/GaugiKernel -> gather all headers from there
        
        subdirs = [d for d in os.listdir(top_path) if os.path.isdir(os.path.join(top_path, d))]
        subdirs.sort()
        
        # Prepare content for top_dir.rst
        toctree_entries = []
        
        for subdir in subdirs:
            subdir_path = os.path.join(top_path, subdir)
            headers = []
            for root, _, files in os.walk(subdir_path):
                for f in files:
                    # check for headers
                    if f.endswith('.h') or f.endswith('.hpp') or f.endswith('.hh'):
                        headers.append(f)
            
            if not headers:
                continue
                
            headers.sort()
            toctree_entries.append(subdir)
            
            # Create subdir RST
            subdir_out_dir = os.path.join(OUTPUT_DIR, top_dir)
            if not os.path.exists(subdir_out_dir):
                os.makedirs(subdir_out_dir)
                
            subdir_rst_path = os.path.join(subdir_out_dir, f"{subdir}.rst")
            print(f"  Generating {subdir_rst_path} with {len(headers)} headers.")
            
            with open(subdir_rst_path, 'w') as f:
                f.write(f"{subdir}\n")
                f.write("=" * len(subdir) + "\n\n")
                f.write(f"Contents of {top_dir}/{subdir}\n\n")
                
                for header in headers:
                    # Use doxygenfile for each header
                    f.write(f".. doxygenfile:: {header}\n")
                    f.write(f"   :project: Lorenzetti\n\n")

        # Now write top_dir.rst
        if toctree_entries:
            with open(os.path.join(OUTPUT_DIR, f"{top_name}.rst"), 'w') as f:
                title = top_name.capitalize()
                f.write(f"{title}\n")
                f.write("=" * len(title) + "\n\n")
                f.write(".. toctree::\n")
                f.write("   :maxdepth: 2\n\n")
                for entry in toctree_entries:
                    f.write(f"   {top_name}/{entry}\n")

if __name__ == "__main__":
    generate_rst()

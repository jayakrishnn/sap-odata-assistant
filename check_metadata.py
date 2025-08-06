# check_metadata.py

from app.metadata import list_all_services, load_metadata

if __name__ == "__main__":
    for srv in list_all_services():
        meta = load_metadata(srv)
        # show the first 5 EntitySet names for each service
        print(f"{srv} → {list(meta.keys())[:5]} …")

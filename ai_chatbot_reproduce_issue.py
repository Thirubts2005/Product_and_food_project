from app import scrape_quickcompare
import pandas as pd

def test_scrape():
    print("Testing scrape_quickcompare('milk')...")
    df = scrape_quickcompare("milk")
    print("\nResulting DataFrame:")
    print(df)
    
    if "Error" in df.columns:
        print("\nScraping failed with error:")
        print(df["Error"].iloc[0])
    elif df.empty:
        print("\nScraping returned an empty DataFrame (no results found).")
    else:
        print(f"\nScraping successful! Found {len(df)} results.")
        print(df.head())

if __name__ == "__main__":
    test_scrape()

import pandas as pd
import io

# Simulate a CSV with semicolons and some potential quoting issues
csv_content = """name;brand;style;type;price;quantity;expiration_date
Product 1;Brand A;Style X;Type 1;10.0;5;2024-12-31
Product 2;Brand B;Style Y;Type 2;20.0;10;2025-01-01
"Product, with comma";Brand C;Style Z;Type 3;30.0;15;2025-06-01
"""

try:
    # Try reading with default (should fail or parse wrongly if it was purely commas expected, 
    # but here it might just read 1 column)
    # But we want to test our FIX: sep=None, engine='python'
    df = pd.read_csv(io.StringIO(csv_content), sep=None, engine='python')
    print("Successfully read CSV with auto-detection:")
    print(df.head())
    print(f"Columns: {df.columns.tolist()}")
    
    if len(df.columns) > 1:
        print("PASS: Detected multiple columns.")
    else:
        print("FAIL: Detected only 1 column.")

except Exception as e:
    print(f"FAIL: Error reading CSV: {e}")

import pandas as pd

# Load the existing Excel file
with pd.ExcelWriter('xxx.xlsx', mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
    # Create a new DataFrame
    df = pd.DataFrame({
        'Column1': [1, 2, 3,0,0,0],
        'Column2': [4,5,6,7,8,9]
    })

    # Write the DataFrame to a new sheet
    df.to_excel(writer, sheet_name='Sheet 2', index=False)

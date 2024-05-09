import pandas as pd

# Example DataFrames
df1 = pd.DataFrame({
    'key': ['A', 'B', 'C', 'A'],
    'value': [1, 2, 3, 5]
})

df2 = pd.DataFrame({
    'key': ['A', 'B', 'D', 'A'],
    'value': [5, 6, 7, 8]
})

# Perform many-to-many join
merged_df = pd.merge(df1, df2, how='inner', left_index=True, right_index=True)

# Create a DataFrame with only indices from the original DataFrames
result_df = pd.DataFrame({
    'df1_index': merged_df.index,
    'df2_index': merged_df.index
})

print(result_df)
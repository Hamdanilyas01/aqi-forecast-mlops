from data_pipeline.fetch_openmeteo import fetch_openmeteo_data

df = fetch_openmeteo_data()

print("Shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nHead:")
print(df.head())

print("\nNull values:")
print(df.isnull().sum())

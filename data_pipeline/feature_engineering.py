import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform feature engineering for AQI prediction.
    Target: Next-hour PM2.5
    """

    # -----------------------------
    # 1. Basic cleaning
    # -----------------------------
    df = df.copy()
    df = df.sort_values("timestamp")

    # Drop rows with missing essential values
    df = df.dropna()

    # -----------------------------
    # 2. Time-based features
    # -----------------------------
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    # -----------------------------
    # 3. Lag features (very important)
    # -----------------------------
    df["pm2_5_lag1"] = df["pm2_5"].shift(1)
    df["pm2_5_lag2"] = df["pm2_5"].shift(2)
    df["pm2_5_lag3"] = df["pm2_5"].shift(3)

    df["pm10_lag1"] = df["pm10"].shift(1)
    df["pm10_lag2"] = df["pm10"].shift(2)
    df["pm2_5_lag6"] = df["pm2_5"].shift(6)
    df["pm2_5_lag12"] = df["pm2_5"].shift(12)
    df["pm2_5_lag24"] = df["pm2_5"].shift(24)

    df["pm10_lag6"] = df["pm10"].shift(6)
    df["pm10_lag12"] = df["pm10"].shift(12)
    df["pm10_lag24"] = df["pm10"].shift(24)


    # -----------------------------
    # 4. Rolling statistics
    # -----------------------------
    df["pm2_5_roll_mean_3"] = df["pm2_5"].rolling(window=3).mean()
    df["pm2_5_roll_std_3"] = df["pm2_5"].rolling(window=3).std()
    df["pm2_5_roll_mean_6"] = df["pm2_5"].rolling(6).mean()
    df["pm2_5_roll_mean_12"] = df["pm2_5"].rolling(12).mean()
    df["pm2_5_roll_mean_24"] = df["pm2_5"].rolling(24).mean()

    df["pm2_5_roll_std_6"] = df["pm2_5"].rolling(6).std()
    df["pm2_5_roll_std_12"] = df["pm2_5"].rolling(12).std()

    # -----------------------------
    # 5. Target variable (next hour PM2.5)
    # -----------------------------
    df["target_pm2_5"] = df["pm2_5"].shift(-1)

    # -----------------------------
    # 6. Final cleanup
    # -----------------------------
    df.dropna(inplace=True)

    return df

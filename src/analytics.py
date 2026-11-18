import pandas as pd
import numpy as np


def detect_traffic_anomalies(df: pd.DataFrame, freq: str = "1h") -> pd.DataFrame:
    """Phát hiện các đột biến lưu lượng (Spike Anomaly) bằng phương pháp Z-score."""
    if df.empty or len(df) < 10:
        return pd.DataFrame()

    df_slot = df.set_index("datetime").resample(freq).size().reset_index(name="count")
    if len(df_slot) < 3:
        return pd.DataFrame()

    mean_val = df_slot["count"].mean()
    std_val = df_slot["count"].std()

    if std_val == 0 or np.isnan(std_val):
        df_slot["z_score"] = 0.0
    else:
        df_slot["z_score"] = (df_slot["count"] - mean_val) / std_val

    # Ngưỡng phát hiện bất thường: Z-score > 2.0 và lưu lượng tối thiểu 5 requests
    anomalies = df_slot[(df_slot["z_score"] > 2.0) & (df_slot["count"] >= 5)].copy()
    anomalies["severity"] = anomalies["z_score"].apply(
        lambda z: "🚨 Cực cao" if z > 3.0 else ("⚠️ Đột biến" if z > 2.5 else "⚡ Tăng nhanh")
    )
    return anomalies.sort_values(by="count", ascending=False)


def detect_suspicious_ips(df: pd.DataFrame, threshold_ratio: float = 0.15) -> pd.DataFrame:
    """Phát hiện các địa chỉ IP có hành vi bất thường (chiếm tỷ trọng quá lớn hoặc gửi tần suất dày đặc)."""
    if df.empty:
        return pd.DataFrame()

    total_reqs = len(df)
    ip_stats = df.groupby("ip").agg(
        requests=("id", "count"),
        unique_ids=("id_clean", "nunique"),
        first_seen=("datetime", "min"),
        last_seen=("datetime", "max"),
        country=("country_clean", "first")
    ).reset_index()

    ip_stats["share_pct"] = (ip_stats["requests"] / total_reqs) * 100
    
    # Tính thời gian hoạt động tính theo phút
    ip_stats["active_duration_min"] = (
        (ip_stats["last_seen"] - ip_stats["first_seen"]).dt.total_seconds() / 60
    ).round(1)

    # Đánh giá rủi ro
    def flag_risk(row):
        reasons = []
        if row["share_pct"] >= 15:
            reasons.append("Chiếm >15% tổng lưu lượng")
        if row["unique_ids"] >= 5:
            reasons.append("Duyệt nhiều ID khác nhau")
        if row["requests"] >= 50 and row["active_duration_min"] <= 5:
            reasons.append("Tần suất cực cao trong thời gian ngắn (Nghi vấn Bot)")
        return " | ".join(reasons) if reasons else "Bình thường"

    ip_stats["risk_eval"] = ip_stats.apply(flag_risk, axis=1)
    suspicious = ip_stats[ip_stats["risk_eval"] != "Bình thường"].sort_values(by="requests", ascending=False)
    return suspicious


def calculate_visitor_retention(df: pd.DataFrame) -> pd.DataFrame:
    """Phân nhóm khách truy cập theo lòng trung thành / tần suất tương tác."""
    if df.empty:
        return pd.DataFrame()

    ip_counts = df["ip"].value_counts()
    
    def group_freq(c):
        if c == 1:
            return "1. Vãng lai (1 lượt)"
        elif 2 <= c <= 5:
            return "2. Khám phá (2 - 5 lượt)"
        elif 6 <= c <= 15:
            return "3. Tương tác tích cực (6 - 15 lượt)"
        else:
            return "4. Khách hàng nòng cốt (> 15 lượt)"

    grouped = ip_counts.apply(group_freq).value_counts().reset_index()
    grouped.columns = ["Phân khúc khách truy cập", "Số lượng IP"]
    grouped = grouped.sort_values(by="Phân khúc khách truy cập")
    return grouped


def analyze_ip_subnets(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Phân tích dải mạng IP (Subnet /24) và tỷ lệ IPv4 vs IPv6."""
    if df.empty:
        return pd.DataFrame(), {"ipv4": 0, "ipv6": 0}

    def extract_subnet(ip):
        ip_str = str(ip).strip()
        if ":" in ip_str:
            return "IPv6 Subnet"
        parts = ip_str.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return "Khác"

    subnets = df["ip"].apply(extract_subnet).value_counts().reset_index()
    subnets.columns = ["Dải mạng (Subnet)", "Lượt truy cập"]
    
    ipv6_count = sum(":" in str(ip) for ip in df["ip"])
    ipv4_count = len(df) - ipv6_count
    
    summary = {
        "ipv4": ipv4_count,
        "ipv6": ipv6_count,
        "ipv4_pct": (ipv4_count / len(df) * 100) if len(df) > 0 else 0,
        "ipv6_pct": (ipv6_count / len(df) * 100) if len(df) > 0 else 0
    }
    return subnets, summary

import math

# Major hospitals in Dhaka, Bangladesh (demo dataset)
HOSPITALS = [
    {
        "name": "Dhaka Medical College Hospital",
        "phone": "+88027150201",
        "lat": 23.7104,
        "lng": 90.4074,
        "address": "Dhaka Medical College Rd, Dhaka 1000",
    },
    {
        "name": "Square Hospital Ltd",
        "phone": "+880106657000",
        "lat": 23.7516,
        "lng": 90.3915,
        "address": "18/F Bir Uttam Qazi Nuruzzaman Sarak, Panthapath",
    },
    {
        "name": "United Hospital Limited",
        "phone": "+88028861600",
        "lat": 23.8151,
        "lng": 90.4223,
        "address": "Plot 15, Road 71, Gulshan, Dhaka",
    },
    {
        "name": "Ibn Sina Hospital Mirpur",
        "phone": "+88029000000",
        "lat": 23.8223,
        "lng": 90.3654,
        "address": "Mirpur, Dhaka",
    },
    {
        "name": "National Institute of Burn & Plastic Surgery",
        "phone": "+88027150250",
        "lat": 23.7100,
        "lng": 90.4100,
        "address": "Dhaka",
    },
]


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def get_nearest_hospital(lat: float, lng: float, custom: list[dict] | None = None) -> dict:
    pool = custom or HOSPITALS
    if not pool:
        return {"name": "Dhaka Medical College Hospital", "phone": "+88027150201", "distance_km": 0}
    best = min(pool, key=lambda h: haversine(lat, lng, h["lat"], h["lng"]))
    dist = haversine(lat, lng, best["lat"], best["lng"])
    return {**best, "distance_km": round(dist, 2)}

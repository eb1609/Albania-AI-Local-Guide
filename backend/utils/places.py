import re

PLACE_PATTERN = re.compile(r"\[([^\]]+)\]")

FAKE_DB = {
    "Sarandë": (39.875, 20.005),
    "Corfu": (39.624, 19.921),
    "Gjirokastër": (40.075, 20.138),
    "Ksamil": (39.768, 19.999),
    "Butrint": (39.745, 20.020)
}

def extract_places(text: str):
    matches = PLACE_PATTERN.findall(text)
    results = []

    for name in matches:
        if name in FAKE_DB:
            lat, lng = FAKE_DB[name]
            results.append({
                "name": name,
                "lat": lat,
                "lng": lng
            })

    return results

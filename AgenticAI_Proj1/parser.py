def parse_trip_input(text):
    lines = text.split("\n")
    cities = []

    for line in lines:
        if "City" in line:
            parts = line.split(":")[1].strip()
            city, date = parts.split(" ")
            cities.append({"city": city, "date": date})

    return cities

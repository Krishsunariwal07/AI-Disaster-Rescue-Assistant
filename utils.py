import requests
import folium


# ================= GET COORDINATES =================

def get_coordinates(location):

    try:

        url = (
            f"https://nominatim.openstreetmap.org/search"
            f"?q={location}&format=json&limit=1"
        )

        headers = {
            "User-Agent": "AI-Disaster-Assistant"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        data = response.json()

        if data:

            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])

            return lat, lon

    except Exception as e:

        print("Location Error:", e)

    return None, None


# ================= HOSPITAL FINDER =================

def get_nearby_hospitals(lat, lon):

    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:5000,{lat},{lon});
    );
    out;
    """

    try:

        response = requests.get(
            overpass_url,
            params={'data': query},
            timeout=15
        )

        if response.status_code == 200:

            data = response.json()

            hospitals = []

            for element in data.get("elements", []):

                hospitals.append({

                    "name": element.get(
                        "tags",
                        {}
                    ).get(
                        "name",
                        "Unnamed Hospital"
                    ),

                    "lat": element.get("lat"),

                    "lon": element.get("lon")

                })

            # If hospitals found
            if len(hospitals) > 0:

                return hospitals

    except Exception as e:

        print("Hospital API Error:", e)

    # ================= FALLBACK HOSPITALS =================

    return [

        {
            "name": "City Hospital",
            "lat": lat + 0.01,
            "lon": lon + 0.01
        },

        {
            "name": "Emergency Care Center",
            "lat": lat - 0.01,
            "lon": lon - 0.01
        },

        {
            "name": "Government Hospital",
            "lat": lat + 0.02,
            "lon": lon - 0.01
        }

    ]


# ================= CREATE MAP =================

def create_map(lat, lon, hospitals):

    # Base map
    map_obj = folium.Map(
        location=[lat, lon],
        zoom_start=12
    )

    # User marker
    folium.Marker(

        [lat, lon],

        popup="Emergency Location",

        tooltip="You Are Here",

        icon=folium.Icon(color="red")

    ).add_to(map_obj)

    # Hospital markers
    for hospital in hospitals:

        if (
            hospital["lat"] is not None
            and hospital["lon"] is not None
        ):

            folium.Marker(

                [
                    hospital["lat"],
                    hospital["lon"]
                ],

                popup=hospital["name"],

                tooltip=hospital["name"],

                icon=folium.Icon(color="green")

            ).add_to(map_obj)

    return map_obj
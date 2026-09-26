# backend/data/seed_places.py

SEED_PLACES = {
    "brisbane": [
        {
            "name": "City Botanic Gardens",
            "lat": -27.4756,
            "lon": 153.0304,
            "tags": ["outdoor", "nature", "relaxation"],
            "kinds": "gardens_and_parks,natural,interesting_places",
            "tourism_score": 95,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A riverside botanical garden suitable for walking, relaxing, and nature-based sightseeing."
        },
        {
            "name": "South Bank Parklands",
            "lat": -27.4810,
            "lon": 153.0234,
            "tags": ["outdoor", "nature", "relaxation", "landmark"],
            "kinds": "parks,gardens_and_parks,interesting_places",
            "tourism_score": 94,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A major riverside recreation area with gardens, walking paths, restaurants, and city views."
        },
        {
            "name": "Lone Pine Koala Sanctuary",
            "lat": -27.5331,
            "lon": 152.9683,
            "tags": ["outdoor", "nature", "wildlife"],
            "kinds": "zoos,natural,interesting_places",
            "tourism_score": 96,
            "estimated_cost": 45,
            "duration": 3,
            "description": "A well-known wildlife sanctuary where visitors can see koalas, kangaroos, and Australian animals."
        },
        {
            "name": "Mount Coot-tha Lookout",
            "lat": -27.4766,
            "lon": 152.9753,
            "tags": ["outdoor", "nature", "viewpoint"],
            "kinds": "view_points,natural,interesting_places",
            "tourism_score": 90,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A popular lookout offering panoramic views of Brisbane and surrounding areas."
        },
        {
            "name": "Brisbane City Hall",
            "lat": -27.4689,
            "lon": 153.0235,
            "tags": ["indoor", "culture", "landmark"],
            "kinds": "architecture,historic,cultural,interesting_places",
            "tourism_score": 90,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A historic civic landmark in the city centre, known for its clock tower and architecture."
        },
        {
            "name": "Queensland Museum",
            "lat": -27.4698,
            "lon": 153.0180,
            "tags": ["indoor", "culture", "museum"],
            "kinds": "museums,cultural,interesting_places",
            "tourism_score": 89,
            "estimated_cost": 20,
            "duration": 2,
            "description": "A museum featuring natural history, science, culture, and Queensland heritage."
        },
        {
            "name": "Gallery of Modern Art",
            "lat": -27.4705,
            "lon": 153.0171,
            "tags": ["indoor", "culture", "gallery"],
            "kinds": "galleries,cultural,interesting_places",
            "tourism_score": 88,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A major contemporary art gallery located in Brisbane's cultural precinct."
        },
        {
            "name": "Roma Street Parkland",
            "lat": -27.4621,
            "lon": 153.0186,
            "tags": ["outdoor", "nature", "relaxation"],
            "kinds": "parks,gardens_and_parks,natural",
            "tourism_score": 87,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A large subtropical parkland with gardens, walking paths, and open green spaces."
        },
        {
            "name": "New Farm Park",
            "lat": -27.4693,
            "lon": 153.0514,
            "tags": ["outdoor", "nature", "relaxation"],
            "kinds": "parks,gardens_and_parks,natural",
            "tourism_score": 84,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A riverside park suitable for walking, picnics, and relaxing outdoor activities."
        },
        {
            "name": "Kangaroo Point Cliffs",
            "lat": -27.4813,
            "lon": 153.0338,
            "tags": ["outdoor", "nature", "viewpoint", "adventure"],
            "kinds": "view_points,natural,interesting_places",
            "tourism_score": 86,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A scenic cliffside area with city views, walking paths, and outdoor activities."
        },
        {
            "name": "Story Bridge",
            "lat": -27.4647,
            "lon": 153.0352,
            "tags": ["outdoor", "landmark", "viewpoint"],
            "kinds": "architecture,bridges,interesting_places",
            "tourism_score": 82,
            "estimated_cost": 0,
            "duration": 1,
            "description": "An iconic Brisbane bridge and landmark near the river."
        },
        {
            "name": "Howard Smith Wharves",
            "lat": -27.4636,
            "lon": 153.0350,
            "tags": ["outdoor", "food", "landmark"],
            "kinds": "tourist_facilities,interesting_places",
            "tourism_score": 78,
            "estimated_cost": 35,
            "duration": 2,
            "description": "A riverside dining and entertainment precinct beneath the Story Bridge."
        },
        {
            "name": "Brisbane Powerhouse",
            "lat": -27.4676,
            "lon": 153.0530,
            "tags": ["indoor", "culture", "theatre"],
            "kinds": "theatres_and_entertainments,cultural,interesting_places",
            "tourism_score": 82,
            "estimated_cost": 25,
            "duration": 2,
            "description": "A cultural venue for performances, exhibitions, and events."
        },
        {
            "name": "Wheel of Brisbane",
            "lat": -27.4748,
            "lon": 153.0215,
            "tags": ["outdoor", "landmark", "viewpoint"],
            "kinds": "amusements,view_points,interesting_places",
            "tourism_score": 80,
            "estimated_cost": 25,
            "duration": 1,
            "description": "A ferris wheel attraction offering views across South Bank and the city."
        },
        {
            "name": "Eat Street Northshore",
            "lat": -27.4414,
            "lon": 153.0836,
            "tags": ["food", "outdoor", "culture"],
            "kinds": "foods,tourist_facilities,interesting_places",
            "tourism_score": 76,
            "estimated_cost": 35,
            "duration": 2,
            "description": "A popular food and entertainment market with street food and live atmosphere."
        }
    ],

    "sydney": [
        {
            "name": "Sydney Opera House",
            "lat": -33.8568,
            "lon": 151.2153,
            "tags": ["culture", "landmark", "architecture"],
            "kinds": "architecture,cultural,interesting_places",
            "tourism_score": 98,
            "estimated_cost": 40,
            "duration": 2,
            "description": "One of Australia's most famous landmarks and a major cultural venue."
        },
        {
            "name": "Sydney Harbour Bridge",
            "lat": -33.8523,
            "lon": 151.2108,
            "tags": ["outdoor", "landmark", "viewpoint"],
            "kinds": "architecture,view_points,interesting_places",
            "tourism_score": 96,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A famous bridge offering harbour views and walking routes."
        },
        {
            "name": "Royal Botanic Garden Sydney",
            "lat": -33.8642,
            "lon": 151.2166,
            "tags": ["outdoor", "nature", "relaxation"],
            "kinds": "gardens_and_parks,natural,interesting_places",
            "tourism_score": 93,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A large botanical garden near Sydney Harbour, suitable for walking and nature sightseeing."
        },
        {
            "name": "Bondi Beach",
            "lat": -33.8915,
            "lon": 151.2767,
            "tags": ["outdoor", "nature", "beach", "relaxation"],
            "kinds": "beaches,natural,interesting_places",
            "tourism_score": 94,
            "estimated_cost": 0,
            "duration": 3,
            "description": "A famous beach known for surfing, coastal walks, and ocean views."
        },
        {
            "name": "Darling Harbour",
            "lat": -33.8725,
            "lon": 151.1996,
            "tags": ["outdoor", "landmark", "food", "relaxation"],
            "kinds": "tourist_facilities,interesting_places",
            "tourism_score": 88,
            "estimated_cost": 30,
            "duration": 2,
            "description": "A waterfront precinct with restaurants, attractions, and public spaces."
        },
        {
            "name": "The Rocks",
            "lat": -33.8599,
            "lon": 151.2090,
            "tags": ["outdoor", "culture", "landmark"],
            "kinds": "historic,cultural,interesting_places",
            "tourism_score": 89,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A historic area with laneways, markets, heritage buildings, and harbour views."
        },
        {
            "name": "Art Gallery of New South Wales",
            "lat": -33.8688,
            "lon": 151.2175,
            "tags": ["indoor", "culture", "gallery"],
            "kinds": "galleries,cultural,interesting_places",
            "tourism_score": 87,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A major public art gallery with Australian, European, and Asian collections."
        },
        {
            "name": "Australian Museum",
            "lat": -33.8744,
            "lon": 151.2131,
            "tags": ["indoor", "culture", "museum"],
            "kinds": "museums,cultural,interesting_places",
            "tourism_score": 85,
            "estimated_cost": 20,
            "duration": 2,
            "description": "A museum focusing on natural history, science, and cultural collections."
        },
        {
            "name": "Taronga Zoo Sydney",
            "lat": -33.8430,
            "lon": 151.2410,
            "tags": ["outdoor", "nature", "wildlife"],
            "kinds": "zoos,natural,interesting_places",
            "tourism_score": 92,
            "estimated_cost": 50,
            "duration": 3,
            "description": "A major zoo with harbour views and Australian and international wildlife."
        },
        {
            "name": "Manly Beach",
            "lat": -33.7969,
            "lon": 151.2855,
            "tags": ["outdoor", "nature", "beach", "relaxation"],
            "kinds": "beaches,natural,interesting_places",
            "tourism_score": 89,
            "estimated_cost": 0,
            "duration": 3,
            "description": "A popular beach destination reachable by ferry from Circular Quay."
        },
        {
            "name": "Hyde Park Sydney",
            "lat": -33.8731,
            "lon": 151.2110,
            "tags": ["outdoor", "nature", "relaxation"],
            "kinds": "parks,gardens_and_parks,natural",
            "tourism_score": 80,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A central city park suitable for walking and relaxing."
        },
        {
            "name": "Queen Victoria Building",
            "lat": -33.8718,
            "lon": 151.2067,
            "tags": ["indoor", "culture", "shopping", "landmark"],
            "kinds": "architecture,shops,interesting_places",
            "tourism_score": 82,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A historic shopping arcade known for its architecture and central location."
        },
        {
            "name": "Circular Quay",
            "lat": -33.8610,
            "lon": 151.2128,
            "tags": ["outdoor", "landmark", "viewpoint"],
            "kinds": "tourist_facilities,interesting_places",
            "tourism_score": 86,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A major harbour transport and sightseeing area near the Opera House and Harbour Bridge."
        },
        {
            "name": "Museum of Contemporary Art Australia",
            "lat": -33.8599,
            "lon": 151.2090,
            "tags": ["indoor", "culture", "gallery"],
            "kinds": "museums,galleries,cultural,interesting_places",
            "tourism_score": 84,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A contemporary art museum located near Circular Quay."
        },
        {
            "name": "Barangaroo Reserve",
            "lat": -33.8587,
            "lon": 151.2017,
            "tags": ["outdoor", "nature", "relaxation", "viewpoint"],
            "kinds": "parks,gardens_and_parks,natural,interesting_places",
            "tourism_score": 84,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A waterfront park with harbour views and walking paths."
        }
    ],

    "melbourne": [
        {
            "name": "Federation Square",
            "lat": -37.8179,
            "lon": 144.9691,
            "tags": ["outdoor", "culture", "landmark"],
            "kinds": "cultural,architecture,interesting_places",
            "tourism_score": 90,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A central public square and cultural meeting point in Melbourne."
        },
        {
            "name": "Royal Botanic Gardens Victoria",
            "lat": -37.8304,
            "lon": 144.9796,
            "tags": ["outdoor", "nature", "relaxation"],
            "kinds": "gardens_and_parks,natural,interesting_places",
            "tourism_score": 94,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A major botanical garden with lakes, lawns, and extensive plant collections."
        },
        {
            "name": "National Gallery of Victoria",
            "lat": -37.8226,
            "lon": 144.9689,
            "tags": ["indoor", "culture", "gallery"],
            "kinds": "galleries,cultural,interesting_places",
            "tourism_score": 92,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A major art gallery featuring international and Australian art."
        },
        {
            "name": "Queen Victoria Market",
            "lat": -37.8076,
            "lon": 144.9568,
            "tags": ["food", "culture", "shopping"],
            "kinds": "foods,shops,tourist_facilities,interesting_places",
            "tourism_score": 88,
            "estimated_cost": 30,
            "duration": 2,
            "description": "A historic market known for food, produce, shopping, and local atmosphere."
        },
        {
            "name": "Melbourne Museum",
            "lat": -37.8033,
            "lon": 144.9717,
            "tags": ["indoor", "culture", "museum"],
            "kinds": "museums,cultural,interesting_places",
            "tourism_score": 88,
            "estimated_cost": 20,
            "duration": 2,
            "description": "A museum covering natural history, culture, science, and Melbourne history."
        },
        {
            "name": "Shrine of Remembrance",
            "lat": -37.8305,
            "lon": 144.9737,
            "tags": ["outdoor", "culture", "landmark"],
            "kinds": "monuments,historic,cultural,interesting_places",
            "tourism_score": 87,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A major war memorial and landmark with views over Melbourne."
        },
        {
            "name": "Eureka Skydeck",
            "lat": -37.8216,
            "lon": 144.9646,
            "tags": ["indoor", "viewpoint", "landmark"],
            "kinds": "view_points,architecture,interesting_places",
            "tourism_score": 86,
            "estimated_cost": 35,
            "duration": 1,
            "description": "An observation deck offering panoramic views across Melbourne."
        },
        {
            "name": "St Kilda Beach",
            "lat": -37.8676,
            "lon": 144.9764,
            "tags": ["outdoor", "nature", "beach", "relaxation"],
            "kinds": "beaches,natural,interesting_places",
            "tourism_score": 86,
            "estimated_cost": 0,
            "duration": 3,
            "description": "A popular beach area known for walking, sunsets, cafes, and seaside atmosphere."
        },
        {
            "name": "Luna Park Melbourne",
            "lat": -37.8679,
            "lon": 144.9768,
            "tags": ["outdoor", "adventure", "amusement"],
            "kinds": "amusements,interesting_places",
            "tourism_score": 82,
            "estimated_cost": 45,
            "duration": 2,
            "description": "A historic amusement park located in St Kilda."
        },
        {
            "name": "State Library Victoria",
            "lat": -37.8098,
            "lon": 144.9652,
            "tags": ["indoor", "culture", "architecture"],
            "kinds": "architecture,cultural,interesting_places",
            "tourism_score": 82,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A historic library known for its architecture and reading room."
        },
        {
            "name": "Flinders Street Station",
            "lat": -37.8183,
            "lon": 144.9671,
            "tags": ["outdoor", "landmark", "architecture"],
            "kinds": "architecture,historic,interesting_places",
            "tourism_score": 83,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A famous railway station and city landmark."
        },
        {
            "name": "Hosier Lane",
            "lat": -37.8163,
            "lon": 144.9691,
            "tags": ["outdoor", "culture", "art"],
            "kinds": "cultural,interesting_places",
            "tourism_score": 80,
            "estimated_cost": 0,
            "duration": 1,
            "description": "A laneway known for street art and urban culture."
        },
        {
            "name": "Carlton Gardens",
            "lat": -37.8063,
            "lon": 144.9717,
            "tags": ["outdoor", "nature", "culture", "relaxation"],
            "kinds": "gardens_and_parks,natural,cultural,interesting_places",
            "tourism_score": 84,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A heritage garden area near the Royal Exhibition Building and Melbourne Museum."
        },
        {
            "name": "Royal Exhibition Building",
            "lat": -37.8047,
            "lon": 144.9717,
            "tags": ["indoor", "culture", "landmark", "architecture"],
            "kinds": "architecture,historic,cultural,interesting_places",
            "tourism_score": 86,
            "estimated_cost": 15,
            "duration": 1,
            "description": "A historic exhibition building and important Melbourne landmark."
        },
        {
            "name": "Yarra River Walk",
            "lat": -37.8200,
            "lon": 144.9640,
            "tags": ["outdoor", "nature", "relaxation", "viewpoint"],
            "kinds": "natural,walking_routes,interesting_places",
            "tourism_score": 78,
            "estimated_cost": 0,
            "duration": 2,
            "description": "A riverside walking route with city views, restaurants, and public spaces."
        }
    ]
}


def get_seed_places(destination: str):
    """
    Return manually curated high-quality tourist attractions for a city.
    This is used to supplement real API results and improve recommendation quality.
    """
    return SEED_PLACES.get(destination.lower(), [])
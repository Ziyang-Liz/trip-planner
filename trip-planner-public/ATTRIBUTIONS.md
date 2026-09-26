# Project origin and data sources

This public project was extracted from the maintainer's existing trip-planning project. It includes the Vue frontend, FastAPI backend, database initialization, and disruption replanning workflow.

The supplied files do not establish a complete contributor list or distinguish all original coursework code from later additions. Contributor names and ownership should be confirmed by the maintainer before adding a project license; no names or authorship claims have been inferred here.

## Data and assets

- Attraction searches use OpenTripMap. `backend/data/seed_places.py` supplements results with curated example attractions; costs and durations are estimates.
- Weather uses OpenWeather forecasts or explicitly labelled demo data. Cached forecasts are labelled separately.
- Maps use Leaflet with OpenStreetMap tiles and contributor attribution. Routing estimates use OSRM; supporting modules also reference Nominatim and Overpass.
- Homepage photographs are externally hosted Unsplash images. Their source URLs remain in `frontend/src/pages/Homepage.vue`; the repository does not bundle the photographs. Hotel names, prices, and ratings are display examples.
- Runtime and development dependencies are listed in the backend manifests and frontend `package.json` / `package-lock.json`. Their license notices remain with the respective packages.

## Project license

A project license has not yet been selected by the maintainer.

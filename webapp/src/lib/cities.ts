/**
 * The curated city list (spec 010 §1): roughly 350 {city, country, iana}
 * entries, weighted toward Indian and US metros plus world capitals and
 * major cities. The city IS the timezone control — picking one writes the
 * label and the zone together — and the IANA name itself never renders:
 * families read "Dallas, United States", never "America/Chicago".
 *
 * The product test suite sweeps every iana here through Postgres and
 * zoneinfo, so an entry that names a zone the engine could not schedule by
 * fails before it ships.
 */

import raw from "@/data/cities.json";

export interface CityEntry {
  city: string;
  country: string;
  iana: string;
}

export const CITIES: CityEntry[] = raw as CityEntry[];

const KNOWN_IANA = new Set(CITIES.map((entry) => entry.iana));

export function displayOf(entry: CityEntry): string {
  return `${entry.city}, ${entry.country}`;
}

/** Only a zone the shipped list carries may ever be written (spec 010 §1). */
export function isKnownIana(iana: string): boolean {
  return KNOWN_IANA.has(iana);
}

/** Case-insensitive search: city-prefix matches first, then any substring of
 *  the display form, capped so the dropdown stays a shortlist. */
export function searchCities(query: string, limit: number = 8): CityEntry[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const starts: CityEntry[] = [];
  const contains: CityEntry[] = [];
  for (const entry of CITIES) {
    const city = entry.city.toLowerCase();
    if (city.startsWith(q)) starts.push(entry);
    else if (displayOf(entry).toLowerCase().includes(q)) contains.push(entry);
  }
  return [...starts, ...contains].slice(0, limit);
}

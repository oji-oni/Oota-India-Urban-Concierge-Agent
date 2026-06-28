# Bengaluru Geography — Hyperlocal Reference Guide

> **Scope:** This reference is loaded by the `india-city-navigator` skill whenever the
> active city is `bengaluru`. It provides traffic patterns, metro topology, auto-rickshaw
> rates, and neighbourhood profiles needed for accurate transit-time and venue planning.

---

## 1. Road Network & Traffic Bottlenecks

### Outer Ring Road (ORR)

| Attribute | Value |
|---|---|
| Route | Hebbal -> KR Puram -> Marathahalli -> Silk Board -> Banashankari |
| Peak hours | 8:00–10:00 AM and 5:00–7:30 PM (weekdays) |
| Congestion factor | 2.5x baseline travel time during peak |
| Alternative east | Sarjapur Road (use for Koramangala <-> Whitefield) |
| Alternative south | Hosur Road / NICE Road (use for Electronic City corridor) |

**Rule:** During ORR peak hours, multiply baseline transit time by 2.5. Suggest metro
or pre-peak travel where possible.

### Silk Board Junction

| Attribute | Value |
|---|---|
| Location | Junction of ORR, Hosur Road, BTM Layout |
| Worst bottleneck | Consistently ranked worst in Bengaluru |
| Peak hours | 5:00–8:00 PM weekdays; 4:00–8:00 PM Fridays |
| Congestion factor | 3.0x baseline at peak |
| Action | Avoid entirely during peak. Route via NICE Road or metro. |

**Rule:** If user's route crosses Silk Board between 5 PM and 8 PM, always warn and
suggest metro Green Line (Jayanagar / Banashankari stations) as alternative.

### Other Bottlenecks

| Junction | Worst time | Factor | Alternative |
|---|---|---|---|
| Marathahalli bridge | 8:30–10 AM, 5:30–7:30 PM | 2.0x | KR Puram via Old Madras Road |
| Hebbal flyover | 8–10 AM | 1.8x | Bellary Road surface road |
| Tin Factory | 8:30–10 AM | 1.8x | ITPL Road via Mahadevapura |
| Ejipura signal | 6–8 PM | 1.7x | 80 Feet Road, Indiranagar |

---

## 2. Metro Network

### Purple Line (East-West)

Full sequence (east to west):

```
Baiyappanahalli -> Indiranagar -> Halasuru -> Trinity -> MG Road ->
Cubbon Park -> Vidhana Soudha -> Sir M Visvesvaraya -> Majestic ->
City Railway Station -> Magadi Road -> Vijayanagar -> Attiguppe ->
Deepanjali Nagar -> Mysore Road
```

Key timings (approximate off-peak, platform to platform):
- Baiyappanahalli -> MG Road: 14 min
- MG Road -> Majestic: 8 min
- Majestic -> Mysore Road: 18 min

### Green Line (North-South)

Full sequence (north to south):

```
Nagasandra -> Dasarahalli -> Jalahalli -> Peenya Industry -> Peenya ->
Yeshwantpur -> Sandal Soap Factory -> Mahalakshmi -> Rajajinagar ->
Kuvempu Road -> Srirampura -> Mantri Square Sampige Road -> Majestic ->
Chickpete -> KR Market -> National College -> Lalbagh -> South End Circle ->
Jayanagar -> RV Road -> Banashankari -> Jayaprakash Nagar -> Yelachenahalli
```

Key timings (approximate off-peak):
- Nagasandra -> Majestic: 32 min
- Majestic -> Yelachenahalli: 28 min
- Majestic -> Jayanagar: 16 min

### Majestic (KSR Bengaluru City Station) — Interchange Rules

This is the **only** Purple-Green interchange station.

| Scenario | Additional time |
|---|---|
| Purple Line -> Green Line platform walk | **+6 minutes** (underground concourse) |
| Green Line -> Purple Line platform walk | **+6 minutes** |
| Metro exit -> KSR Railway Station platform | **+10 minutes** (exit, security, stairs) |
| Metro exit -> KSRTC/BMTC bus bays | **+5 minutes** |

**ALWAYS** add 6 minutes when computing any route that involves a line change at Majestic.

### Yellow Line (under construction)

Partially operational. Check `get_metro_line_status(city='bengaluru', line='yellow')`
before routing via RV Road or Bommanahalli corridor.

---

## 3. Neighbourhood Profiles

### Distance from Majestic (KSR)

| Neighbourhood | Distance | Typical travel (off-peak) | Typical travel (peak) |
|---|---|---|---|
| Malleshwaram | 3 km | 12 min metro (Green) | 25 min road |
| Basavanagudi | 6 km | 20 min metro (Green, Yelachenahalli dir.) | 35 min road |
| Koramangala | 8 km | 30 min (metro + auto) | 55 min road |
| Indiranagar | 9 km | 22 min metro (Purple, Baiyappanahalli dir.) | 40 min road |
| Jayanagar | 11 km | 25 min metro (Green) | 45 min road |
| Whitefield | 22 km | 55 min metro (Purple + transfer) | 90+ min road |
| Electronic City | 26 km | 65 min (metro + bus) | 100+ min road |
| Airport (KIAL) | 35 km | 75 min (express way off-peak) | 120+ min road |

### Neighbourhood Character Guide

| Neighbourhood | Character | Best for | Avoid |
|---|---|---|---|
| Koramangala | Young, vibrant, startup culture | Cafes, restaurants, co-working | Parking on weekends |
| Indiranagar | Upscale, lively, expat-friendly | Pubs, boutiques, brunch | Late weekend nights (crowded) |
| Malleshwaram | Traditional, residential, old Bengaluru | Filter coffee, temples, saree shops | Modern clubbing |
| Whitefield | IT corridor, malls, gated communities | Malls, IT-crowd dining, multiplexes | Peak hour road traffic |
| HSR Layout | Family-friendly, planned | Family dining, parks, salons | Budget street food |
| Jayanagar | Residential, South Indian food hub | Dosas, temples, local shopping | Late night safety |
| BTM Layout | Budget-friendly, student area | Budget meals, student cafes | Upscale dining |
| MG Road | Commercial, tourist, metro-connected | Shopping, cafes, nightlife | Parking, weekend crowds |
| Brigade Road | Fashion, food, nightlife | Apparel, bars, pubs | Weekday shopping (closed early) |
| Church Street | Heritage, bohemian | Books, cafes, street art | Noisy weekend evenings |
| Ulsoor | Quiet, lake, expats | Lake walk, quiet dining | Night transport options |
| Sadashivanagar | Elite residential | Fine dining, gardens | Budget options (scarce) |
| Rajajinagar | West Bengaluru, old city | Traditional South Indian, family | Metro connectivity (limited) |
| Yeshwantpur | Industrial + residential transition | IKEA, large malls | Character/heritage dining |

---

## 4. Auto-Rickshaw Fare Matrix

### Standard Meter Rates (BMTC authorised)

| Component | Rate |
|---|---|
| Base fare (first 1.9 km) | Rs 30 |
| Additional per km | Rs 15 / km |
| Night surcharge (10 PM – 5 AM) | +25% on total fare |
| Waiting charge | Rs 3 / minute after 5 minutes |
| Luggage (large bags) | Rs 10–20 extra (discretionary) |

### App-Based Surge

| Time period | Surge multiplier |
|---|---|
| Off-peak (10 AM – 4 PM, non-weekend) | 1.0x |
| Peak (8–10 AM, 5–7:30 PM weekday) | 1.5x – 2.0x |
| Rain (any heavy rain event) | 1.5x – 2.5x |
| Festival/New Year's Eve | 2.0x – 3.0x |

### Sample Fares (metered, off-peak)

| Route | Distance | Approx. fare |
|---|---|---|
| Majestic -> Koramangala | 8 km | Rs 121 |
| Majestic -> Indiranagar | 9 km | Rs 136 |
| MG Road -> Brigade Road | 1.2 km | Rs 30 (base) |
| Koramangala -> HSR Layout | 4 km | Rs 75 |
| Indiranagar -> Whitefield | 18 km | Rs 256 |
| Airport -> Indiranagar | 34 km | Rs 496 (metered) |

Calculation formula:
```
fare = 30 + max(0, distance_km - 1.9) * 15
if night: fare = fare * 1.25
```

---

## 5. Best Meeting Point Recommendations

Ranked by: transit accessibility + venue quality + parking:

### 1. MG Road Metro Station (Purple Line)

- **Why:** Central on Purple Line; both lines accessible via Majestic (10 min away);
  excellent pedestrian area; Brigade Road and Church Street walkable.
- **Best for:** Across-city meets (east + west attendees).
- **Venues nearby:** Koshy's (heritage cafe), Church Street Social, Cafe Coffee Day MG Road.
- **Caution:** Crowded on weekends evenings.

### 2. Indiranagar Metro Station (Purple Line)

- **Why:** East-side meets; upscale neighbourhood; great restaurant density within 1 km.
- **Best for:** Meets involving Koramangala, Whitefield, and central attendees.
- **Venues nearby:** Toit, Plan B, Hole in the Wall, Fatty Bao.
- **Caution:** Limited parking; use metro.

### 3. Malleshwaram (Green Line, Mantri Square Sampige Road or Rajajinagar)

- **Why:** North Bengaluru; traditional atmosphere; great for temple visits + filter coffee.
- **Best for:** Meets involving Yeshwantpur, Rajajinagar, Sadashivanagar attendees.
- **Venues nearby:** Brahmin's Coffee Bar, Veena Stores, CTR (Central Tiffin Room).
- **Caution:** Limited late-night options; plan for before 9 PM.

### 4. Koramangala 5th Block

- **Why:** Geographic heart of south-east Bengaluru; massive food and cafe scene.
- **Best for:** Meets involving HSR, BTM, Jayanagar, JP Nagar attendees.
- **Venues nearby:** The Permit Room, Meghana Foods, Truffles.
- **Caution:** No metro; auto/cab only; park carefully on weekends.

---

## 6. Key Landmarks for Navigation

| Landmark | Area | Notes |
|---|---|---|
| UB City Mall | Central / Lavelle Road | Luxury mall; nearest metro: MG Road |
| Forum Mall | Koramangala | Weekends very crowded; arrive by noon |
| Phoenix Marketcity | Whitefield | Largest mall cluster; allow extra transit time |
| Orion Mall | Rajajinagar | Green Line metro: Rajajinagar station |
| ISKCON Temple | Rajajinagar | Fridays/weekends: 45-60 min darshan wait |
| Bull Temple (Nandi) | Basavanagudi | No shoes from main road; Rs 5 locker |
| Lalbagh | South Bengaluru | No entry charge; closes at 6 PM |
| Cubbon Park | MG Road | Metro-connected; safe for walks |
| Ulsoor Lake | Ulsoor | Walking track open 5 AM – 9 PM |
| Vidhana Soudha | Metro: Vidhana Soudha | Photography of exterior allowed |

---

## 7. BMTC Bus Key Routes

For budget transit or areas not served by metro:

| Route | Key stops | Frequency |
|---|---|---|
| 500 series | Majestic <-> Whitefield via ORR | Every 15–25 min |
| 201 | Shivajinagar <-> Electronic City | Every 20 min |
| 335 | Majestic <-> Koramangala <-> BTM | Every 10 min |
| KIA-8 | MG Road <-> Airport (Kempegowda) | Every 30 min, ~75 min journey |

---

## 8. Airport (KIAL) Connectivity

| Mode | From | Journey time (off-peak) | Journey time (peak) | Cost |
|---|---|---|---|---|
| BMTC Vajra bus | MG Road | 75 min | 120 min | Rs 150–200 |
| Cab (Ola/Uber) | MG Road | 60 min | 110 min | Rs 900–1400 |
| Cab | Whitefield | 50 min | 90 min | Rs 700–1100 |
| Auto (rare) | Hebbal | 20 min | 40 min | Rs 300–400 |

**Rule:** For flights before 8 AM, always recommend leaving the previous night or by 5 AM
to beat ORR-Hebbal peak build-up.

---

## 9. Emergency & Safety Notes

- **Police helpline:** 100
- **Women's helpline:** 1091
- **Ambulance:** 108
- **Auto dispute:** Call 080-22868450 (traffic police)
- **Safe auto-booking:** Prefer Namma Yatri (driver cooperative, no surge) or Ola/Uber
  for accountability and tracking.
- **Late night:** After 11 PM, prefer app-based cabs over street autos; stick to
  well-lit areas (Indiranagar, MG Road, Koramangala 5th Block).

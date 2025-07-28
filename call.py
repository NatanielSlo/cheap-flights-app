import streamlit as st
from datetime import datetime, timedelta, date
import requests

# --- API Settings ---
import streamlit as st

headers = {
    "x-rapidapi-key": st.secrets["rapidapi"]["key"],
    "x-rapidapi-host": st.secrets["rapidapi"]["host"]
}


# --- Utility Formatting ---
def format_time(dt_str):
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%d-%m-%Y %H:%M")

def format_duration(seconds):
    td = timedelta(seconds=seconds)
    h, remainder = divmod(td.seconds, 3600)
    m = remainder // 60
    d = td.days
    if d > 0: h += d * 24
    return f"{h}h {m}m"

# --- Fetch extra flights ---
def get_flight_to_start(start_code):
    if not start_code: return None
    url = "https://kiwi-com-cheap-flights.p.rapidapi.com/one-way"
    query = {
        "source": "City:warsaw_pl",
        "destination": f"{start_code}",
        "currency": "pln",
        "locale": "en",
        "adults": "1",
        "children": "0",
        "infants": "0",
        "handbags": "1",
        "holdbags": "0",
        "cabinClass": "ECONOMY",
        "sortBy": "PRICE",
        "limit": "1",
        "outboundDepartureDateStart": "2026-01-10T00:00:00",
        "outboundDepartureDateEnd": "2026-01-30T00:00:00",
        "transportTypes": "FLIGHT",
    }
    res = requests.get(url, headers=headers, params=query)
    try:
        one_way_data = res.json()
        if one_way_data["itineraries"]:
            price = (
                one_way_data["itineraries"][0]
                .get("bookingOptions", {})
                .get("edges", [{}])[0]
                .get("node", {})
                .get("price", {})
                .get("amount", "brak")
            )
            return float(price)
        else:
            return 0
    except:
        return 0

def get_flight_from_end(end_code):
    if not end_code: return None
    url = "https://kiwi-com-cheap-flights.p.rapidapi.com/one-way"
    query = {
        "source": f"{end_code}",
        "destination": "City:warsaw_pl",
        "currency": "pln",
        "locale": "en",
        "adults": "1",
        "children": "0",
        "infants": "0",
        "handbags": "1",
        "holdbags": "0",
        "cabinClass": "ECONOMY",
        "sortBy": "PRICE",
        "limit": "1",
        "outboundDepartureDateStart": "2026-01-10T00:00:00",
        "outboundDepartureDateEnd": "2026-01-30T00:00:00",
        "transportTypes": "FLIGHT",
    }
    res = requests.get(url, headers=headers, params=query)
    try:
        one_way_data = res.json()
        if one_way_data["itineraries"]:
            price = (
                one_way_data["itineraries"][0]
                .get("bookingOptions", {})
                .get("edges", [{}])[0]
                .get("node", {})
                .get("price", {})
                .get("amount", "brak")
            )
            return float(price)
        else:
            return 0
    except:
        return 0

# --- Print Details ---
def print_direction(direction):
    segments = direction.get("sectorSegments", [])
    total_duration = direction.get("duration", 0)
    st.write(f"**Całkowity czas podróży:** {format_duration(total_duration)}")
    for j, seg_wrapper in enumerate(segments, 1):
        seg = seg_wrapper.get("segment")
        src = seg["source"]
        dst = seg["destination"]
        carrier = seg["carrier"]["name"]
        flight_code = seg["code"]
        cabin = seg.get("cabinClass", "unknown")
        duration = seg.get("duration", 0)
        st.write(f"--- Segment {j} ---")
        st.write(f"✈️ Z: {src['station']['name']} ({src['station']['code']}) o {format_time(src['localTime'])}")
        st.write(f"➡️ Do: {dst['station']['name']} ({dst['station']['code']}) o {format_time(dst['localTime'])}")
        st.write(f"🛫 Przewoźnik: {carrier}, Kod lotu: {flight_code}, Klasa: {cabin}")
        st.write(f"🕒 Czas lotu: {format_duration(duration)}")
        layover = seg_wrapper.get("layover")
        if layover:
            layover_dur = layover.get("duration", 0)
            st.write(f"⏸️ Przesiadka: {format_duration(layover_dur)}, pieszo: {layover.get('isWalkingDistance')}, "
                     f"bagaż do odbioru: {'tak' if layover.get('isBaggageRecheck') else 'nie'}")

def show_itineraries(itineraries):
    for i, itinerary in enumerate(itineraries, 1):
        st.markdown(f"### ✈️ LOT {i}")
        booking = (
            itinerary.get("bookingOptions", {})
            .get("edges", [{}])[0]
            .get("node", {})
        )
        amount = float(booking.get("price", {}).get("amount") or 0)
        st.write(f"💰 Cena głównego lotu: {amount:.2f} PLN")

        outbound = itinerary.get("outbound")
        inbound = itinerary.get("inbound")

        if outbound:
            first_segment = outbound["sectorSegments"][0]["segment"]["source"]
            start_code = f"{first_segment['station']['city']['id']}"
            price_to_start = get_flight_to_start(start_code)
            st.write(f"➕ Lot Warszawa ➡ {start_code}: {price_to_start:.2f} PLN")
        else:
            price_to_start = 0

        if inbound:
            last_segment = inbound["sectorSegments"][-1]["segment"]["destination"]
            end_code = f"{last_segment['station']['city']['id']}"
            price_to_end = get_flight_from_end(end_code)
            st.write(f"➕ Lot {end_code} ➡ Warszawa: {price_to_end:.2f} PLN")
        else:
            price_to_end = 0

        total_price = price_to_start + price_to_end + amount
        st.success(f"✅ Łączna cena: {total_price:.2f} PLN")

        if outbound:
            st.markdown("#### 🔹 Wylot (outbound)")
            print_direction(outbound)
        if inbound:
            st.markdown("#### 🔹 Powrót (inbound)")
            print_direction(inbound)

        st.markdown("---")


# --- Streamlit App ---
st.title("📉 Cheap Flight Tracker")

# Date inputs
out_start = st.date_input("✈️ Wylot: początek zakresu", value=date(2026, 1, 21))
out_end = st.date_input("✈️ Wylot: koniec zakresu", value=date(2026, 1, 22))
in_start = st.date_input("✈️ Powrót: początek zakresu", value=date(2026, 5, 10))
in_end = st.date_input("✈️ Powrót: koniec zakresu", value=date(2026, 5, 30))

if st.button("🔍 Sprawdź loty"):
    with st.spinner("Szukanie najtańszych lotów..."):
        url = "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip"
        querystring = {
            "source": "Country:GB,Country:DE,Country:IT,Country:SE,Country:NO,Country:FR,Country:GR",
            "destination": "Country:TH,Country:VN,Country:MY,Country:ID,Country:SGP",
            "currency": "pln",
            "locale": "en",
            "adults": "1",
            "children": "0",
            "infants": "0",
            "handbags": "1",
            "holdbags": "0",
            "cabinClass": "ECONOMY",
            "sortBy": "PRICE",
            "sortOrder": "ASCENDING",
            "applyMixedClasses": "true",
            "allowReturnFromDifferentCity": "true",
            "allowChangeInboundDestination": "true",
            "allowChangeInboundSource": "true",
            "allowDifferentStationConnection": "true",
            "enableSelfTransfer": "true",
            "allowOvernightStopover": "true",
            "enableTrueHiddenCity": "true",
            "enableThrowAwayTicketing": "true",
            "outbound": "SUNDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,MONDAY,TUESDAY",
            "transportTypes": "FLIGHT",
            "contentProviders": "FLIXBUS_DIRECTS,FRESH,KAYAK,KIWI",
            "limit": "1",
            "inboundDepartureDateStart": f"{in_start}T00:00:00",
            "inboundDepartureDateEnd": f"{in_end}T00:00:00",
            "outboundDepartureDateStart": f"{out_start}T00:00:00",
            "outboundDepartureDateEnd": f"{out_end}T00:00:00"
        }

        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code != 200:
            st.error(f"Błąd API: {response.status_code}")
        else:
            try:
                data = response.json()
                itineraries = data.get("itineraries", [])
                if not itineraries:
                    st.warning("Brak lotów dla wybranych dat.")
                else:
                    show_itineraries(itineraries)
            except Exception as e:
                st.error(f"Błąd podczas przetwarzania danych: {e}")

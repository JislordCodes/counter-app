"""Look up coordinates for named places with Nominatim (OpenStreetMap data). Cached; 1 request per second."""
import json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "images", "maps", "geocode.json")
UA = "DolomitesTravelGuideMaps/1.0 (https://github.com/JislordCodes/counter-app; book maps)"
VIEW = (10.4, 46.0, 12.9, 47.4)  # west, south, east, north - the wider Dolomites area

QUERIES = {
    # places
    "Bolzano": "Bolzano", "Bressanone": "Bressanone", "Brunico": "Brunico", "Dobbiaco": "Dobbiaco",
    "San Candido": "San Candido", "Sesto": "Sesto Pusteria", "Cortina": "Cortina d'Ampezzo", "Corvara": "Corvara in Badia",
    "Ortisei": "Ortisei", "Selva": "Selva di Val Gardena", "Santa Cristina": "Santa Cristina Val Gardena",
    "Canazei": "Canazei", "Moena": "Moena", "Campitello": "Campitello di Fassa", "Vigo di Fassa": "Vigo di Fassa",
    "Pera di Fassa": "Pera di Fassa", "Siusi": "Siusi allo Sciliar", "Castelrotto": "Castelrotto", "Compatsch": "Compatsch Alpe di Siusi",
    "Colfosco": "Colfosco", "La Villa": "La Villa Alta Badia", "San Cassiano": "San Cassiano Alta Badia",
    "San Martino in Badia": "San Martino in Badia", "Misurina": "Misurina", "Auronzo": "Auronzo di Cadore",
    "Arabba": "Arabba", "Malga Ciapela": "Malga Ciapela", "Villabassa": "Villabassa", "Funes": "Funes Val di Funes",
    "Chiusa": "Chiusa Klausen", "Fortezza": "Fortezza Franzensfeste", "Calalzo": "Calalzo di Cadore", "Nova Levante": "Nova Levante",
    "Soprabolzano": "Soprabolzano", "Belluno": "Belluno", "Ora": "Ora Auer", "Merano": "Merano", "Vipiteno": "Vipiteno",
    "Pocol": "Pocol Cortina", "Falzes": "Falzes", "Marebbe": "San Vigilio di Marebbe",
    # passes
    "Passo Pordoi": "Passo Pordoi", "Passo Sella": "Passo Sella", "Passo Gardena": "Passo Gardena", "Passo Campolongo": "Passo Campolongo",
    "Passo Falzarego": "Passo Falzarego", "Passo Valparola": "Passo Valparola", "Passo Giau": "Passo Giau", "Passo Fedaia": "Passo Fedaia",
    "Passo Tre Croci": "Passo Tre Croci", "Passo Costalunga": "Passo Costalunga Karerpass",
    # peaks and lakes
    "Marmolada": "Marmolada", "Tre Cime": "Tre Cime di Lavaredo", "Sassolungo": "Sassolungo", "Piz Boè": "Piz Boè",
    "Catinaccio": "Catinaccio", "Sciliar": "Sciliar Monte Pez", "Sass Rigais": "Sass Rigais", "Seceda": "Seceda",
    "Kronplatz": "Plan de Corones Kronplatz", "Tofana di Mezzo": "Tofana di Mezzo", "Lagazuoi": "Piccolo Lagazuoi",
    "Cristallo": "Monte Cristallo", "Cinque Torri": "Cinque Torri", "Nuvolau": "Nuvolau", "Latemar": "Latemar",
    "Lago di Braies": "Lago di Braies", "Lago di Misurina": "Lago di Misurina", "Lago di Carezza": "Lago di Carezza",
    "Lago di Dobbiaco": "Lago di Dobbiaco", "Lago di Fedaia": "Lago di Fedaia", "Lago di Sorapis": "Lago di Sorapis",
    "Lago Pisciadu": "Lago di Pisciadù", "Cadini di Misurina": "Cadini di Misurina", "Croda da Lago": "Croda da Lago",
    "Lago Federa": "Lago Federa", "Piz Boè Sass Pordoi": "Sass Pordoi", "Antelao": "Antelao", "Civetta": "Monte Civetta",
    # huts
    "Rifugio Auronzo": "Rifugio Auronzo", "Rifugio Locatelli": "Rifugio Antonio Locatelli Tre Cime", "Rifugio Lavaredo": "Rifugio Lavaredo",
    "Rifugio Cavazza": "Rifugio Cavazza al Pisciadù", "Rifugio Forcella Pordoi": "Rifugio Forcella Pordoi", "Rifugio Vicenza": "Rifugio Vicenza Sassolungo",
    "Rifugio Nuvolau": "Rifugio Nuvolau", "Rifugio Scoiattoli": "Rifugio Scoiattoli", "Rifugio Vandelli": "Rifugio Vandelli Sorapis",
    "Rifugio Re Alberto": "Rifugio Re Alberto I Gartl", "Rifugio Vajolet": "Rifugio Vajolet", "Rifugio Bolzano": "Rifugio Bolzano Schlernhaus",
    "Rifugio Fondovalle": "Rifugio Fondovalle Talschlusshütte", "Rifugio Piano Fiscalina": "Rifugio Piano Fiscalina", "Rifugio Firenze": "Rifugio Firenze Cisles",
    "Rifugio Pieralongia": "Rifugio Pieralongia", "Rifugio Genova": "Rifugio Genova Schlüterhütte", "Rifugio Biella": "Rifugio Biella",
    "Rifugio Fanes": "Rifugio Fanes", "Rifugio Lagazuoi": "Rifugio Lagazuoi", "Rifugio Citta di Fiume": "Rifugio Città di Fiume",
    "Rifugio Palafavera": "Rifugio Palafavera", "Rifugio Vazzoler": "Rifugio Vazzoler", "Rifugio Carestiato": "Rifugio Carestiato",
    "Rifugio Pramperet": "Rifugio Pramperet", "Rifugio Pian de Fontana": "Rifugio Pian de Fontana", "La Pissa": "La Pissa Belluno",
    "Rifugio Zallinger": "Rifugio Zallinger", "Sanon": "Sanon Hütte Seiser Alm", "Williamshutte": "Williamshütte Seiser Alm", "Saltria": "Saltria",
    "Gardeccia": "Gardeccia", "Rifugio Averau": "Rifugio Averau", "Bai de Dones": "Bai de Dones Cinque Torri", "Col Raiser": "Col Raiser",
    "Furnes": "Furnes Ortisei", "Punta Rocca": "Punta Rocca Marmolada", "Santa Maddalena": "Santa Maddalena Funes", "Geisler Alm": "Geisler Alm Funes",
    "Santa Croce": "Santa Croce Badia", "Ciampedie": "Ciampedie Vigo di Fassa", "Col Rodella": "Col Rodella Campitello", "Auronzo hut": "Rifugio Auronzo Tre Cime",
    "Plan de Gralba": "Plan de Gralba", "Forcella Sassolungo": "Forcella Sassolungo", "Rifugio Pian di Cengia": "Rifugio Pian di Cengia",
    "Malga Rin Bianco": "Malga Rin Bianco", "Lago Antorno": "Lago d'Antorno", "Monte Piana": "Monte Piana",
    # airports and rail
    "VCE": "Venice Marco Polo Airport", "TSF": "Treviso Airport", "VRN": "Verona Villafranca Airport", "INN": "Innsbruck Airport",
    "BZO": "Aeroporto di Bolzano", "Verona": "Verona", "Innsbruck": "Innsbruck", "Trento": "Trento", "Venezia Mestre": "Venezia Mestre",
    "Brennero": "Brennero", "Dobbiaco station": "Dobbiaco stazione ferroviaria",
}


def load():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def run(only=None):
    g = load()
    for key, q in QUERIES.items():
        if only and key not in only:
            continue
        if key in g:
            continue
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
            dict(q=q, format="jsonv2", limit=3, viewbox=f"{VIEW[0]},{VIEW[3]},{VIEW[2]},{VIEW[1]}", bounded=1))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            r = json.loads(urllib.request.urlopen(req, timeout=40).read())
            g[key] = [dict(lon=float(x["lon"]), lat=float(x["lat"]), name=x["display_name"][:90], cls=x.get("category"), typ=x.get("type")) for x in r]
        except Exception as e:
            print("fail", key, e)
            g[key] = []
        json.dump(g, open(CACHE, "w"), indent=1, ensure_ascii=False)
        time.sleep(1.2)
    return g


if __name__ == "__main__":
    g = run(set(sys.argv[1:]) or None)
    miss = [k for k in QUERIES if not g.get(k)]
    print("done", len(g), "missing:", miss)

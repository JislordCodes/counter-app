import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import render2

MAPS = {}


def P(key, label, near, off=(3, -3), rx=None, **kw):
    o = dict(off=off, near=near)
    if rx:
        o["rx"] = rx
    o.update(kw)
    return (key, label, "place", o)


# ------------------------------------------------------------------ M01 regional overview
MAPS["M01"] = dict(
    id="M01", bbox=(10.95, 46.28, 12.50, 46.92), zoom=11, vzoom=11, scale_km=20, fs=6.0, area_fs=6.6,
    road_min="secondary", road_scale=0.75, light=0.55,
    labels=[
        P("Bolzano", "Bolzano", (11.355, 46.498), (4, -4), "Bolzano|Bozen"),
        P("Bressanone", "Bressanone", (11.658, 46.716), (4, 3), "Bressanone|Brixen"),
        P("Brunico", "Brunico", (11.936, 46.796), (4, 3), "Brunico|Bruneck"),
        P("Dobbiaco", "Dobbiaco", (12.227, 46.733), (-4, 3), "Dobbiaco|Toblach", ha="right"),
        P("San Candido", "San Candido", (12.284, 46.733), (4, 3), "San Candido|Innichen"),
        P("Sesto", "Sesto", (12.35, 46.702), (4, -3), "Sesto|Sexten"),
        P("Cortina", "Cortina d'Ampezzo", (12.136, 46.537), (4, -3), "Cortina"),
        P("Corvara", "Corvara", (11.874, 46.55), (4, 3), "Corvara"),
        P("Ortisei", "Ortisei", (11.672, 46.575), (-4, 3), "Ortisei|Urtij", ha="right"),
        P("Selva", "Selva", (11.76, 46.555), (3, -3), "Selva|Wolkenstein|Sëlva"),
        P("Canazei", "Canazei", (11.771, 46.477), (3, -3), "Canazei"),
        P("Moena", "Moena", (11.659, 46.377), (3, -3), "Moena"),
        ("Marmolada", "Marmolada", "peak", dict(off=(3, -2))),
        ("Tre Cime", "Tre Cime", "peak", dict(off=(3, 2))),
        ("Lago di Braies", "L. di Braies", "lake", dict(off=(-3, 3), ha="right")),
    ],
    area_labels=[(11.60, 46.605, "7  VAL GARDENA"), (11.95, 46.515, "8  ALTA BADIA\n& SELLA"), (12.12, 46.49, "9  CORTINA"),
                 (12.27, 46.835, "10  TRE CIME · BRAIES\n· PUSTERIA"), (11.58, 46.425, "11  FASSA ·\nCATINACCIO"), (11.62, 46.79, "12  KRONPLATZ ·\nBRIXEN · BOLZANO")],
)

# ------------------------------------------------------------------ M02 access map
MAPS["M02"] = dict(
    id="M02", bbox=(10.65, 45.40, 12.75, 47.35), zoom=9, vzoom=9, width_in=5.6, scale_km=50, fs=6.4,
    road_min="trunk", road_scale=1.0, light=0.62, contours=False, lifts=False,
    labels=[
        ("VCE", "Venice airport (VCE)", "air", dict(off=(-4, 3), ha="right", fs=6.2)),
        ("TSF", "Treviso (TSF)", "air", dict(off=(4, 2), fs=6.2)),
        ("VRN", "Verona airport (VRN)", "air", dict(off=(4, -3), fs=6.2)),
        ("INN", "Innsbruck airport (INN)", "air", dict(off=(4, 2), fs=6.2)),
        ("BZO", "Bolzano airport (BZO)", "air", dict(off=(4, -4), fs=6.2)),
        P("Bolzano", "Bolzano", (11.355, 46.498), (4, 3), "Bolzano|Bozen", lonlat=(11.355, 46.498)),
        P("Bressanone", "Bressanone", (11.658, 46.716), (4, 3), "Bressanone|Brixen", lonlat=(11.658, 46.716)),
        P("Brunico", "Brunico", (11.936, 46.796), (4, 3), "Brunico|Bruneck", lonlat=(11.936, 46.796)),
        P("Cortina", "Cortina", (12.136, 46.537), (4, -3), "Cortina", lonlat=(12.136, 46.537)),
        P("Trento", "Trento", (11.12, 46.07), (4, 3), "Trento", lonlat=(11.12, 46.07)),
        P("Verona", "Verona", (10.99, 45.44), (4, 3), "Verona", lonlat=(10.99, 45.44)),
        P("Innsbruck", "Innsbruck", (11.40, 47.26), (-4, -4), "Innsbruck", lonlat=(11.40, 47.26), ha="right"),
        P("Belluno", "Belluno", (12.22, 46.14), (4, 3), "Belluno", lonlat=(12.22, 46.14)),
        P("Dobbiaco", "Dobbiaco", (12.227, 46.733), (4, 3), "Dobbiaco|Toblach", lonlat=(12.227, 46.733)),
        ("Brennero", "Brenner", "place", dict(off=(4, 3), lonlat=(11.505, 47.003))),
    ],
    area_labels=[(11.12, 46.93, "A22 Brenner\nmotorway"), (12.45, 46.93, "Pusteria\nrailway")],
)

# ------------------------------------------------------------------ M03 Val Gardena and Alpe di Siusi
MAPS["M03"] = dict(
    id="M03", bbox=(11.50, 46.49, 11.84, 46.65), zoom=12, vzoom=13, scale_km=5, fs=5.8, paths=False,
    road_min="unclassified", road_scale=1.0, light=0.62,
    labels=[
        P("Ortisei", "Ortisei", (11.672, 46.575), (3, -3), "Ortisei|Urtij"),
        P("Santa Cristina", "S. Cristina", (11.71, 46.56), (3, -3), "Cristina|Crestina"),
        P("Selva", "Selva", (11.76, 46.555), (3, -3), "Selva|Sëlva|Wolkenstein"),
        P("Siusi", "Siusi", (11.56, 46.54), (3, -3), "Siusi|Seis"),
        P("Castelrotto", "Castelrotto", (11.563, 46.567), (3, -3), "Castelrotto|Kastelruth"),
        P("Compatsch", "Compatsch", (11.63, 46.54), (3, -3), "Compatsch|Compaccio"),
        ("Seceda", "Seceda", "peak", dict(off=(3, 2))),
        ("Sassolungo", "Sassolungo", "peak", dict(off=(3, -3))),
        ("Sciliar", "Sciliar", "peak", dict(off=(3, 2))),
        ("Passo Sella", "P. Sella", "pass", dict(off=(3, -3))),
        ("Passo Gardena", "P. Gardena", "pass", dict(off=(3, 3))),
        ("Col Raiser", "Col Raiser", "lift", dict(off=(3, 2))),
        ("Furnes", "Furnes", "lift", dict(poi="^Furnes", near=(11.715, 46.60), off=(3, 2))),
        ("Santa Maddalena", "S. Maddalena", "poi", dict(off=(3, 2))),
        P("Saltria", "Saltria", (11.65, 46.51), (3, -3), "Saltria"),
    ],
    numbers={1: "Seceda", 2: "Compatsch", 3: "Sassolungo", 4: "Santa Maddalena", 5: "Ortisei"},
)

# ------------------------------------------------------------------ M04 Alta Badia and the Sella Ronda
MAPS["M04"] = dict(
    id="M04", bbox=(11.62, 46.42, 12.06, 46.62), zoom=12, vzoom=12, scale_km=5, fs=5.8, road_min="tertiary", road_scale=0.9, light=0.6,
    routes=[dict(via=["Corvara", "Passo Campolongo", "Arabba", "Passo Pordoi", "Canazei", "Passo Sella", "Selva", "Passo Gardena", "Corvara"], lw=2.6)],
    labels=[
        P("Corvara", "Corvara", (11.874, 46.55), (3, 3), "Corvara"),
        P("Colfosco", "Colfosco", (11.84, 46.56), (-3, 3), "Colfosco", ha="right"),
        P("La Villa", "La Villa", (11.93, 46.58), (3, 3), "La Villa|Stern"),
        P("San Cassiano", "San Cassiano", (11.96, 46.57), (3, 3), "San Cassiano|San Ciascian"),
        P("Arabba", "Arabba", (11.875, 46.50), (3, -3), "Arabba"),
        P("Canazei", "Canazei", (11.771, 46.477), (3, -3), "Canazei"),
        P("Selva", "Selva", (11.76, 46.555), (3, 3), "Selva|Sëlva|Wolkenstein"),
        P("Campitello", "Campitello", (11.74, 46.48), (-3, -3), "Campitello", ha="right"),
        ("Passo Gardena", "P. Gardena", "pass", dict(off=(-3, 3), ha="right")),
        ("Passo Sella", "P. Sella", "pass", dict(off=(-3, -3), ha="right")),
        ("Passo Pordoi", "P. Pordoi", "pass", dict(off=(3, -3))),
        ("Passo Campolongo", "P. Campolongo", "pass", dict(off=(3, -3))),
        ("Passo Falzarego", "P. Falzarego", "pass", dict(off=(-3, -3), ha="right")),
        ("Piz Boè", "Piz Boè", "peak", dict(off=(3, 3))),
        ("Marmolada", "Marmolada", "peak", dict(off=(3, -3))),
        ("Lagazuoi", "Lagazuoi", "peak", dict(off=(3, 2))),
    ],
    numbers={1: "Passo Gardena", 2: "Passo Sella", 3: "Passo Pordoi", 4: "Passo Campolongo"},
)

# ------------------------------------------------------------------ M05 Cortina
MAPS["M05"] = dict(
    id="M05", bbox=(11.95, 46.46, 12.30, 46.62), zoom=12, vzoom=12, scale_km=5, fs=5.8, road_min="tertiary", road_scale=1.0, light=0.6,
    labels=[
        P("Cortina", "Cortina d'Ampezzo", (12.136, 46.537), (3, -3), "Cortina"),
        P("Misurina", "Misurina", (12.25, 46.58), (-3, -4), "Misurina", ha="right"),
        ("Passo Falzarego", "P. Falzarego", "pass", dict(off=(3, -4))),
        ("Passo Giau", "P. Giau", "pass", dict(off=(3, -3))),
        ("Passo Tre Croci", "P. Tre Croci", "pass", dict(off=(3, 3))),
        ("Lagazuoi", "Lagazuoi", "peak", dict(off=(-3, 3), ha="right")),
        ("Cinque Torri", "Cinque Torri", "peak", dict(off=(-3, -3), ha="right")),
        ("Tofana di Mezzo", "Tofana di Mezzo", "peak", dict(off=(-3, 3), ha="right")),
        ("Cristallo", "Cristallo", "peak", dict(off=(3, 3))),
        ("Nuvolau", "Nuvolau", "peak", dict(off=(-3, -3), ha="right")),
        ("Lago di Sorapis", "L. di Sorapis", "lake", dict(off=(3, 2))),
        ("Lago Federa", "L. Federa", "lake", dict(off=(3, -3))),
        ("Lago di Misurina", "L. di Misurina", "lake", dict(off=(-3, 4), ha="right")),
    ],
    numbers={1: "Cortina", 2: "Cinque Torri", 3: "Lagazuoi", 4: "Passo Giau", 5: "Lago di Sorapis", 6: "Tofana di Mezzo"},
)

# ------------------------------------------------------------------ M06 Tre Cime, Sesto, Braies
MAPS["M06"] = dict(
    id="M06", bbox=(12.00, 46.55, 12.46, 46.78), zoom=12, vzoom=12, join=260, scale_km=5, fs=5.8, road_min="tertiary", road_scale=1.0, light=0.6,
    routes=[dict(via=["Dobbiaco", "Dürrensee", "Misurina", "Rifugio Auronzo"], lw=2.2, ls=(0, (5, 2)))],
    labels=[
        P("Dobbiaco", "Dobbiaco", (12.227, 46.733), (-3, 3), "Dobbiaco|Toblach", ha="right"),
        P("San Candido", "San Candido", (12.284, 46.733), (3, 3), "San Candido|Innichen"),
        P("Sesto", "Sesto", (12.35, 46.702), (3, -3), "Sesto|Sexten"),
        P("Misurina", "Misurina", (12.25, 46.58), (3, -3), "Misurina"),
        P("Villabassa", "Villabassa", (12.17, 46.73), (-3, 3), "Villabassa|Niederdorf", ha="right"),
        ("Rifugio Auronzo", "Rif. Auronzo", "hut", dict(off=(3, -3), poi="Auronzo", near=(12.296, 46.612))),
        ("Locatelli", "Rif. Locatelli", "hut", dict(lonlat=(12.3106, 46.6369), off=(3, 3))),
        ("Tre Cime", "Tre Cime", "peak", dict(off=(-3, 3), ha="right")),
        ("Lago di Braies", "L. di Braies", "lake", dict(off=(3, 2))),
        ("Lago di Dobbiaco", "L. di Dobbiaco", "lake", dict(off=(3, -3))),
        ("Lago di Misurina", "L. di Misurina", "lake", dict(off=(-3, -3), ha="right")),
        ("Cadini di Misurina", "Cadini", "peak", dict(off=(-3, 3), ha="right")),
        ("Rifugio Fondovalle", "Fondovalle", "hut", dict(poi="Fondovalle|Talschluss", near=(12.35, 46.66), off=(3, -3))),
    ],
    numbers={1: "Tre Cime", 2: "Cadini di Misurina", 3: "Rifugio Fondovalle", 4: "Lago di Braies"},
)

# ------------------------------------------------------------------ M07 Val di Fassa
MAPS["M07"] = dict(
    id="M07", bbox=(11.50, 46.33, 11.96, 46.52), zoom=12, vzoom=12, scale_km=5, fs=5.8, road_min="tertiary", road_scale=1.0, light=0.6,
    labels=[
        P("Canazei", "Canazei", (11.771, 46.477), (3, 3), "Canazei"),
        P("Campitello", "Campitello", (11.74, 46.48), (-3, 3), "Campitello", ha="right"),
        P("Pera di Fassa", "Pera", (11.68, 46.43), (-3, -3), "Pera", ha="right"),
        P("Vigo di Fassa", "Vigo", (11.66, 46.43), (-3, 3), "Vigo", ha="right"),
        P("Moena", "Moena", (11.659, 46.377), (3, -3), "Moena"),
        ("Passo Pordoi", "P. Pordoi", "pass", dict(off=(3, 3))),
        ("Passo Sella", "P. Sella", "pass", dict(off=(3, 3))),
        ("Passo Fedaia", "P. Fedaia", "pass", dict(off=(3, 3))),
        ("Passo Costalunga", "P. Costalunga", "pass", dict(off=(4, -5))),
        ("Marmolada", "Marmolada", "peak", dict(off=(3, -3))),
        ("Catinaccio", "Catinaccio", "peak", dict(off=(-3, 3), ha="right")),
        ("Latemar", "Latemar", "peak", dict(off=(3, -3))),
        ("Lago di Carezza", "L. di Carezza", "lake", dict(off=(3, 2))),
        ("Lago di Fedaia", "L. di Fedaia", "lake", dict(off=(3, -3))),
        ("Malga Ciapela", "Malga Ciapela", "lift", dict(off=(-4, -5), ha="right")),
        ("Gardeccia", "Gardeccia", "hut", dict(off=(-3, 3), ha="right")),
        ("Col Rodella", "Col Rodella", "lift", dict(off=(-3, 3), ha="right")),
    ],
    numbers={1: "Gardeccia", 2: "Malga Ciapela", 3: "Lago di Carezza", 4: "Col Rodella"},
)

# ------------------------------------------------------------------ M08 Plan de Corones, Brixen, Bolzano
MAPS["M08"] = dict(
    id="M08", bbox=(11.20, 46.42, 12.12, 46.84), zoom=11, vzoom=11, scale_km=10, fs=6.0, road_min="secondary", road_scale=0.8, light=0.58,
    labels=[
        P("Bolzano", "Bolzano", (11.355, 46.498), (3, -4), "Bolzano|Bozen"),
        P("Soprabolzano", "Soprabolzano", (11.40, 46.52), (3, 3), "Soprabolzano|Oberbozen"),
        P("Bressanone", "Bressanone", (11.658, 46.716), (3, 3), "Bressanone|Brixen"),
        P("Brunico", "Brunico", (11.936, 46.796), (3, 3), "Brunico|Bruneck"),
        P("Chiusa", "Chiusa", (11.57, 46.64), (-3, 3), "Chiusa|Klausen", ha="right"),
        P("Fortezza", "Fortezza", (11.62, 46.78), (-3, 3), "Fortezza|Franzensfeste", ha="right"),
        ("Kronplatz", "Plan de Corones", "peak", dict(off=(-3, -4), ha="right")),
        ("Plose", "Plose", "peak", dict(off=(3, -3))),
        ("Neustift", "Neustift Abbey", "poi", dict(off=(3, 3))),
    ],
    numbers={1: "Bolzano", 2: "Soprabolzano", 3: "Bressanone", 4: "Neustift", 5: "Kronplatz"},
)


# ------------------------------------------------------------------ M09 Tre Cime loop
MAPS["M09"] = dict(
    id="M09", bbox=(12.272, 46.598, 12.342, 46.642), zoom=13, vzoom=14, scale_km=1, fs=5.6, paths=True, road_min="unclassified",
    road_scale=1.0, light=0.64, contour_step=100, lifts=False,
    routes=[dict(via=[dict(poi="Rifugio Auronzo", near=(12.296, 46.612)), dict(poi="Rifugio Lavaredo", near=(12.305, 46.617)),
                      dict(poi="Forcella Lavaredo", near=(12.308, 46.623)), dict(poi="Locatelli|Dreizinnenh", near=(12.3106, 46.6369)),
                      dict(poi="Langalm", near=(12.32, 46.625)), dict(poi="Rifugio Auronzo", near=(12.296, 46.612))], lw=2.0, ls=(0, (4, 1.6)))],
    labels=[
        ("Auronzo", "Rif. Auronzo", "hut", dict(poi="Rifugio Auronzo", near=(12.296, 46.612), off=(-3, -3), ha="right")),
        ("Lavaredo", "Rif. Lavaredo", "hut", dict(poi="Rifugio Lavaredo", near=(12.305, 46.617), off=(-3, 3), ha="right")),
        ("FLavaredo", "Forcella Lavaredo", "pass", dict(poi="Forcella Lavaredo", near=(12.308, 46.623), off=(-3, 3), ha="right")),
        ("Locatelli", "Rif. Locatelli", "hut", dict(poi="Locatelli|Dreizinnenh", near=(12.3106, 46.6369), off=(3, 3))),
        ("Langalm", "Langalm", "hut", dict(poi="Langalm", near=(12.32, 46.625), off=(3, -3))),
        ("Pian di Cengia", "Rif. Pian di Cengia", "hut", dict(poi="Pian di Cengia", near=(12.33, 46.64), off=(3, 3))),
    ],
    numbers={},
)

# ------------------------------------------------------------------ M10 Seceda and Col Raiser
MAPS["M10"] = dict(
    id="M10", bbox=(11.685, 46.575, 11.790, 46.628), zoom=13, vzoom=14, scale_km=1, fs=5.6, paths=True, road_min="unclassified",
    road_scale=1.0, light=0.64, contour_step=100, all_lifts=True,
    labels=[
        ("Furnes", "Furnes", "lift", dict(poi="^Furnes", near=(11.715, 46.60), off=(3, 3))),
        ("Seceda", "Seceda 2,519 m", "peak", dict(off=(3, 3))),
        ("Col Raiser", "Col Raiser", "lift", dict(off=(3, -3))),
        ("Rifugio Firenze", "Rif. Firenze", "hut", dict(poi="Firenze|Cisles", near=(11.74, 46.60), off=(3, -3))),
        ("Pieralongia", "Pieralongia", "hut", dict(poi="Pieralongia", near=(11.75, 46.60), off=(3, 3))),
        ("Baita Sofie", "Baita Sofie", "hut", dict(poi="Sofie", near=(11.725, 46.605), off=(-3, 3), ha="right")),
        P("Ortisei", "Ortisei", (11.672, 46.575), (3, 3), "Ortisei|Urtij"),
        P("Santa Cristina", "S. Cristina", (11.71, 46.56), (3, 3), "Cristina|Crestina"),
    ],
    numbers={},
)

# ------------------------------------------------------------------ M11 Alpe di Siusi walks
MAPS["M11"] = dict(
    id="M11", bbox=(11.585, 46.495, 11.705, 46.565), zoom=13, vzoom=14, scale_km=1, fs=5.6, paths=True, road_min="unclassified",
    road_scale=1.0, light=0.64, contour_step=100, all_lifts=True,
    routes=[dict(via=[dict(poi="Compatsch", near=(11.63, 46.54)), dict(poi="Sanon", near=(11.64, 46.53)), dict(poi="Saltria", near=(11.65, 46.51))], lw=2.0, ls=(0, (4, 1.6)))],
    labels=[
        ("Compatsch", "Compatsch", "place", dict(poi="Compatsch", near=(11.63, 46.54), off=(-3, 3), ha="right")),
        ("Sanon", "Sanon hut", "hut", dict(poi="Sanon", near=(11.64, 46.53), off=(3, 3))),
        ("Saltria", "Saltria", "place", dict(poi="Saltria", near=(11.65, 46.51), off=(3, -3))),
        ("Williams", "Williamshütte", "hut", dict(poi="Williams", near=(11.64, 46.505), off=(-3, -3), ha="right")),
        ("Schlernhaus", "Schlernhaus (Rif. Bolzano)", "hut", dict(poi="Schlernhaus|Rifugio Bolzano", near=(11.575, 46.512), off=(3, 3))),
        ("Florian", "Florian chairlift", "lift", dict(poi="Florian", near=(11.65, 46.51), off=(3, 3))),
    ],
    numbers={},
)

# ------------------------------------------------------------------ M12 Lagazuoi
MAPS["M12"] = dict(
    id="M12", bbox=(11.985, 46.503, 12.035, 46.538), zoom=13, vzoom=14, scale_km=1, fs=5.6, paths=True, road_min="unclassified",
    road_scale=1.0, light=0.64, contour_step=50, all_lifts=True,
    labels=[
        ("Lagazuoi hut", "Rif. Lagazuoi (top station)", "hut", dict(lonlat=(12.0086, 46.5276), off=(4, 3))),
        ("Falzarego", "Passo Falzarego", "pass", dict(poi="Passo Falzarego|Falzarego", near=(12.007, 46.519), off=(3, -3))),
    ],
    numbers={},
)

# ------------------------------------------------------------------ I5, I7, I10 itinerary maps
_IT_PLACES = [
    P("Ortisei", "Ortisei", (11.672, 46.575), (-3, 3), "Ortisei|Urtij", ha="right"),
    P("Corvara", "Corvara", (11.874, 46.55), (3, 3), "Corvara"),
    P("Cortina", "Cortina", (12.136, 46.537), (3, -3), "Cortina"),
    P("Dobbiaco", "Dobbiaco", (12.227, 46.733), (-3, 3), "Dobbiaco|Toblach", ha="right"),
    P("Sesto", "Sesto", (12.35, 46.702), (3, -3), "Sesto|Sexten"),
    P("Misurina", "Misurina", (12.25, 46.58), (3, -3), "Misurina"),
]
MAPS["I05"] = dict(
    id="I05", bbox=(11.55, 46.45, 12.42, 46.80), zoom=11, vzoom=11, scale_km=10, fs=5.8, road_min="secondary", road_scale=0.8, light=0.6,
    routes=[dict(via=["Ortisei", "Passo Gardena", "Corvara", "San Cassiano", "Passo Falzarego", "Cortina"], lw=2.4),
            dict(via=["Cortina", "Misurina", "Rifugio Auronzo"], lw=2.0, ls=(0, (5, 2))),
            dict(via=["Cortina", "Dobbiaco", "Lago di Braies"], lw=2.0, ls=(0, (1, 2)))],
    labels=_IT_PLACES + [("Seceda", "Seceda", "peak", dict(off=(3, 3))), ("Compatsch", "Alpe di Siusi", "place", dict(off=(-3, -3), ha="right")),
                          ("Cinque Torri", "Cinque Torri", "peak", dict(off=(-3, -3), ha="right")), ("Lagazuoi", "Lagazuoi", "peak", dict(off=(-3, 3), ha="right")),
                          ("Tre Cime", "Tre Cime", "peak", dict(off=(3, 3))), ("Lago di Braies", "Lago di Braies", "lake", dict(off=(-3, 3), ha="right"))],
    numbers={1: "Seceda", 2: "Compatsch", 3: "Cinque Torri", 4: "Tre Cime", 5: "Lago di Braies"},
)
MAPS["I07"] = dict(
    id="I07", bbox=(11.50, 46.40, 12.45, 46.82), zoom=11, vzoom=11, scale_km=10, fs=5.8, road_min="secondary", road_scale=0.8, light=0.6,
    routes=[dict(via=["Ortisei", "Passo Gardena", "Corvara", "San Cassiano", "Passo Falzarego", "Cortina"], lw=2.4),
            dict(via=["Cortina", "Dobbiaco", "Sesto"], lw=2.4)],
    labels=_IT_PLACES + [("Seceda", "Seceda", "peak", dict(off=(3, 3))), ("Sassolungo", "Sassolungo", "peak", dict(off=(3, -3))),
                          ("Cinque Torri", "Cinque Torri", "peak", dict(off=(-3, -3), ha="right")), ("Lagazuoi", "Lagazuoi", "peak", dict(off=(-3, 3), ha="right")),
                          ("Tre Cime", "Tre Cime", "peak", dict(off=(3, 3))), ("Lago di Braies", "Lago di Braies", "lake", dict(off=(-3, 3), ha="right"))],
    numbers={1: "Seceda", 2: "Compatsch", 3: "Sassolungo", 4: "Cinque Torri", 5: "Lagazuoi", 6: "Tre Cime", 7: "Lago di Braies"},
)
MAPS["I10"] = dict(
    id="I10", bbox=(11.25, 46.30, 12.50, 46.82), zoom=11, vzoom=11, scale_km=10, fs=5.8, road_min="secondary", road_scale=0.75, light=0.58,
    routes=[dict(via=["Bolzano", "Ortisei"], lw=2.2),
            dict(via=["Ortisei", "Selva", "Passo Sella", "Canazei"], lw=2.2),
            dict(via=["Canazei", "Passo Pordoi", "Arabba", "Passo Falzarego", "Cortina"], lw=2.2),
            dict(via=["Cortina", "Dobbiaco", "Sesto"], lw=2.2)],
    labels=[P("Bolzano", "Bolzano", (11.355, 46.498), (-3, -3), "Bolzano|Bozen", ha="right"), P("Ortisei", "Ortisei", (11.672, 46.575), (-3, 3), "Ortisei|Urtij", ha="right"),
            P("Canazei", "Canazei", (11.771, 46.477), (-3, -3), "Canazei", ha="right"), P("Cortina", "Cortina", (12.136, 46.537), (3, -3), "Cortina"),
            P("Sesto", "Sesto", (12.35, 46.702), (3, -3), "Sesto|Sexten"), ("Marmolada", "Marmolada", "peak", dict(off=(3, -3))), ("Tre Cime", "Tre Cime", "peak", dict(off=(3, 3)))],
    numbers={1: "Bolzano", 2: "Ortisei", 3: "Canazei", 4: "Cortina", 5: "Sesto"},
)

# ------------------------------------------------------------------ M14 Alta Via 1
MAPS["M14"] = dict(
    id="M14", bbox=(11.93, 46.07, 12.36, 46.72), zoom=10, vzoom=11, width_in=3.3, scale_km=10, fs=5.0, road_min="primary", road_scale=0.7, light=0.6, contours=False,
    straight=[dict(via=["Lago di Braies", "Rifugio Biella", "Rifugio Fanes", "Rifugio Lagazuoi", "Rifugio Nuvolau", "Rifugio Citta di Fiume", "Rifugio Palafavera",
                         "Rifugio Vazzoler", "Rifugio Carestiato", "Rifugio Pramperet", "Rifugio Pian de Fontana", "La Pissa"], lw=1.8, ls=(0, (4, 2)))],
    labels=[("Lago di Braies", "Lago di Braies (start)", "lake", dict(off=(3, 3))), ("Rifugio Biella", "Biella", "hut", dict(off=(3, 2))), ("Rifugio Fanes", "Fanes", "hut", dict(off=(-3, 2), ha="right")),
            ("Rifugio Lagazuoi", "Lagazuoi", "hut", dict(off=(3, 2))), ("Rifugio Nuvolau", "Nuvolau", "hut", dict(off=(-3, 2), ha="right")),
            ("Rifugio Citta di Fiume", "Città di Fiume", "hut", dict(off=(3, 2))), ("Rifugio Palafavera", "Palafavera", "hut", dict(off=(-3, 2), ha="right")),
            ("Rifugio Vazzoler", "Vazzoler", "hut", dict(off=(3, 2))), ("Rifugio Carestiato", "Carestiato", "hut", dict(off=(-3, 2), ha="right")),
            ("Rifugio Pramperet", "Pramperèt", "hut", dict(off=(3, 2))), ("Rifugio Pian de Fontana", "Pian de Fontana", "hut", dict(off=(-3, 2), ha="right")),
            ("La Pissa", "La Pissa (finish)", "place", dict(off=(3, -3))), P("Cortina", "Cortina", (12.136, 46.537), (3, 3), "Cortina"), P("Belluno", "Belluno", (12.22, 46.14), (3, -3), "Belluno")],
    numbers={},
)

if __name__ == "__main__":
    ids = sys.argv[1:] or list(MAPS)
    for i in ids:
        print("==", i, flush=True)
        try:
            render2.render(MAPS[i])
        except Exception as e:
            print("FAILED", i, repr(e), flush=True)

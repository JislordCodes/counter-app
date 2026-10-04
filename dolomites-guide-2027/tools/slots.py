"""Image slots for the Dolomites guide.

Each slot is one place in the book where a picture goes. A picture is accepted for a slot
only if it matches the slot's subject. `must` lists words of which at least one has to
appear in the file title, categories or description; `avoid` lists words that disqualify.
"""

S = []


def slot(id, chapter, section, subject, queries, must, avoid=(), min_w=2400, cover=False):
    S.append(dict(id=id, chapter=chapter, section=section, subject=subject, queries=list(queries),
                  must=[m.lower() for m in must], avoid=[a.lower() for a in avoid],
                  min_w=3000 if cover else min_w, cover=cover))


slot("COVER", "Cover", "Front cover", "A sweeping Dolomites peak view with strong light, suitable for a cover",
     ["Dolomites sunrise", "Tre Cime sunrise", "Seceda sunrise", "Dolomites panorama"],
     ["dolomit", "seceda", "tre cime", "lavaredo", "odle", "dreizinnen", "drei zinnen"], ["ski"], cover=True)

# Chapter 1
slot("C01a", "1", "Opener", "Panoramic view of Dolomites peaks",
     ["Dolomites panorama", "Dolomiti panorama Sassolungo", "Dolomites mountain landscape summer"], ["dolomit"], ["winter", "ski"])
slot("C01b", "1", "Three languages, many names", "A road sign or place sign with Italian, German and Ladin names",
     ["trilingual sign Ladin Italian German", "Passo Gardena Grödner Joch Jëuf de Frea sign", "Urtijëi St. Ulrich Ortisei sign", "Ladin Italian German road sign Val Gardena"],
     ["sign", "schild", "wegweiser", "ortstafel", "segnale", "cartello", "signpost"], [])

# Chapter 2 seasons
slot("C02s", "2", "Summer", "Wildflower meadow in summer in the Dolomites",
     ["Seiser Alm wildflowers summer", "Alpe di Siusi flowers", "Dolomites alpine meadow flowers", "Wiese Blumen Dolomiten Sommer"],
     ["flower", "blume", "fiori", "meadow", "wiese", "blüh"], ["winter", "ski", "snow"])
slot("C02a", "2", "Autumn", "Golden larch trees in autumn in the Dolomites",
     ["larch autumn", "Lärchen Herbst", "Dolomites autumn", "larici autunno"],
     ["larch", "lärche", "larici", "autumn", "herbst", "autunno"], ["winter"])
slot("C02w", "2", "Winter", "Snow-covered Dolomites peaks in winter",
     ["Dolomites winter snow", "Seiser Alm winter", "Dolomiti inverno neve", "Cortina d'Ampezzo winter"],
     ["winter", "snow", "schnee", "neve", "inverno"], [])
slot("C02p", "2", "Spring", "Apple blossom in South Tyrol valley in spring",
     ["Apfelblüte Südtirol", "apple blossom Tyrol", "Apfelblüte Bozen", "apple blossom Dolomites"],
     ["blossom", "blüte", "fioritura", "apfel", "apple"], [])
slot("C02m", "2", "Summer (wildlife)", "Alpine marmot in the Dolomites",
     ["marmot Dolomites", "Marmota marmota Dolomiti", "Murmeltier Südtirol", "marmot Alpe di Siusi"],
     ["marmot", "murmeltier", "marmotta"], [], min_w=1800)

# Chapter 3
slot("C03a", "3", "Seceda lifts", "Cable car or gondola from Ortisei toward Seceda",
     ["Seceda cable car", "Furnes Seceda Seilbahn", "Ortisei Furnes gondola", "Seceda Bergbahn Gröden"],
     ["seceda", "furnes"], ["ski", "winter"])
slot("C03b", "3", "Lago di Braies", "Lago di Braies with the boathouse and rowing boats",
     ["Lago di Braies boathouse", "Pragser Wildsee boats", "Lago di Braies"], ["braies", "pragser"], ["winter", "snow"])
slot("C03c", "3", "Tre Cime toll road", "Rifugio Auronzo or the Tre Cime toll road",
     ["Rifugio Auronzo", "Auronzohütte Drei Zinnen", "Strada Tre Cime Auronzo toll"], ["auronzo", "tre cime", "drei zinnen", "lavaredo"], ["winter"])
slot("C03d", "3", "Alpe di Siusi", "Seiser Alm cable car from Seis/Siusi",
     ["Seiser Alm Seilbahn Seis", "Alpe di Siusi cable car Siusi", "Seiser Alm Bahn"], ["seiser alm", "siusi", "seis"], ["ski", "winter"])

# Chapter 4
slot("C04a", "4", "By train", "A regional train in the Pustertal or South Tyrol",
     ["Pustertalbahn Toblach train", "Toblach railway station train", "Südtirol Zug Pustertal", "Dobbiaco stazione treno"],
     ["pustertal", "toblach", "dobbiaco", "innichen", "san candido", "brunico", "bruneck", "bolzano", "bozen", "südtirol"], [])
slot("C04b", "4", "Mountain pass driving", "Hairpin bends on a Dolomites pass road",
     ["Passo Pordoi road", "Passo Giau road", "Grödner Joch Straße", "Sellajoch Straße"],
     ["pordoi", "giau", "gardena", "sella", "falzarego", "campolongo", "hairpin", "tornant", "kehre"], ["winter", "ski"])
slot("C04c", "4", "Public transport", "A SAD or local bus in the mountains",
     ["SAD bus South Tyrol", "Linienbus Südtirol Grödnerjoch", "bus Val Gardena", "Dolomiti Bus Cortina"],
     ["bus"], [])
slot("C04d", "4", "Lift passes", "A modern gondola cable car in the Dolomites",
     ["Seilbahn Dolomiten", "Kabinenbahn Südtirol", "cabinovia Dolomiti", "gondola Kronplatz"],
     ["gondola", "kabinenbahn", "cable car", "seilbahn", "funivia", "cabinovia"], ["winter", "ski"])

# Chapter 5, 6
slot("C05a", "5", "Food costs", "A mountain hut terrace in the Dolomites",
     ["rifugio Dolomiti", "Berghütte Südtirol", "Schutzhütte Dolomiten", "Rifugio Lagazuoi"], ["rifugio", "hütte", "alm", "hut"], ["winter"])
slot("C06a", "6", "Ortisei and Val Gardena", "Ortisei village in Val Gardena",
     ["Ortisei St. Ulrich Gröden", "Ortisei panorama", "Urtijëi Ortisei village"], ["ortisei", "st. ulrich", "urtijëi", "urtijei"], ["winter", "ski"])
slot("C06b", "6", "Farm stays", "A traditional South Tyrol farmhouse",
     ["South Tyrol farmhouse", "Bauernhof Südtirol", "Alpine farm Dolomites"], ["farm", "bauernhof", "hof", "maso"], ["winter"])
slot("C06c", "6", "Alta Badia", "Corvara village with the Sella group",
     ["Corvara in Badia", "Corvara Sella", "Colfosco Corvara"], ["corvara", "colfosco", "alta badia"], ["winter", "ski"])

# Chapter 7
slot("C07a", "7", "Seceda", "The Seceda ridge with the Odle peaks",
     ["Seceda", "Seceda Odle ridge", "Seceda Furchetta Val Gardena"], ["seceda"], ["winter", "ski", "skirun"])
slot("C07b", "7", "Alpe di Siusi", "Alpe di Siusi meadows with the Sassolungo behind",
     ["Seiser Alm Langkofel", "Alpe di Siusi Sassolungo", "Seiser Alm Sommer"], ["seiser alm", "siusi"], ["winter", "ski", "snow"])
slot("C07c", "7", "Sassolungo", "Sassolungo (Langkofel) group near Passo Sella",
     ["Sassolungo", "Langkofel Sellajoch", "Sassolungo Passo Sella"], ["sassolungo", "langkofel"], ["winter", "ski"])
slot("C07d", "7", "Santa Maddalena", "Santa Maddalena church in Val di Funes with the Odle",
     ["Santa Maddalena Funes church", "St. Magdalena Villnöss Kirche", "Chiesa Santa Maddalena Val di Funes"], ["magdalena", "maddalena", "funes", "villnöss"], ["winter"])
slot("C07e", "7", "Sciliar", "Sciliar (Schlern) massif",
     ["Schlern Santnerspitze", "Sciliar Alpe di Siusi", "Schlern Seiser Alm"], ["schlern", "sciliar"], ["winter", "ski"])
slot("C07f", "7", "Forcella Sassolungo", "The Forcella Sassolungo cable car",
     ["Forcella Sassolungo cable car", "Langkofelscharte Seilbahn", "Sassolungo funivia Passo Sella"], ["forcella", "langkofelscharte", "sassolungo"], [], min_w=1800)

# Chapter 8
slot("C08a", "8", "Passo Gardena", "Passo Gardena with the Sella group",
     ["Passo Gardena", "Grödner Joch Sella", "Gardena Pass road"], ["gardena", "grödner"], ["winter", "ski"])
slot("C08b", "8", "Piz Boè", "Sass Pordoi cable car or Piz Boè summit",
     ["Sass Pordoi", "Piz Boè summit", "Sas Pordoi cable car"], ["pordoi", "boè", "boe"], ["winter", "ski"])
slot("C08c", "8", "Lago Pisciadù", "Lago Pisciadù and Rifugio Cavazza",
     ["Lago di Pisciadù", "Pisciadusee Cavazza", "Pisciadù lake Sella"], ["pisciad"], [])
slot("C08d", "8", "Via ferrata Tridentina", "The suspension bridge on the Brigata Tridentina via ferrata",
     ["Via ferrata Brigata Tridentina", "Pisciadù Hängebrücke Klettersteig", "Tridentina ferrata suspension bridge"], ["tridentina", "pisciad"], [], min_w=1800)
slot("C08e", "8", "Alta Badia villages", "Colfosco or La Villa with the Sella or Puez peaks",
     ["Colfosco", "La Villa Alta Badia", "Alta Badia summer"], ["colfosco", "la villa", "alta badia", "badia"], ["winter", "ski"])
slot("C08f", "8", "Santa Croce", "Santa Croce (Heiligkreuz) pilgrimage church",
     ["Santa Croce Alta Badia church", "Heiligkreuz Abtei Kirche", "Heiligkreuzkofel"], ["santa croce", "heiligkreuz", "sassongher"], ["winter"])
slot("C08g", "8", "Ladin museum", "Ciastel de Tor castle at San Martino in Badia",
     ["Ciastel de Tor San Martino in Badia", "Schloss Thurn St. Martin in Thurn", "Castel Tor San Martino"], ["tor", "thurn", "martino in badia", "st. martin in thurn"], [])

# Chapter 9
slot("C09a", "9", "Cortina town", "Cortina d'Ampezzo town centre with the bell tower",
     ["Cortina d'Ampezzo Corso Italia", "Cortina d'Ampezzo campanile", "Cortina d'Ampezzo panorama"], ["cortina"], ["ski", "winter", "olymp"])
slot("C09b", "9", "Cinque Torri", "The Cinque Torri rock towers",
     ["Cinque Torri", "Cinque Torri Dolomites", "Cinque Torri Nuvolau"], ["cinque torri"], ["winter"])
slot("C09c", "9", "Lagazuoi tunnels", "Great War tunnels on Lagazuoi",
     ["Lagazuoi tunnels", "Galleria Lagazuoi", "Lagazuoi Great War"], ["lagazuoi"], ["ski"], min_w=1800)
slot("C09d", "9", "Passo Giau", "Passo Giau road and meadows",
     ["Passo Giau", "Passo Giau Averau", "Giau Pass Dolomites"], ["giau"], ["winter", "ski"])
slot("C09e", "9", "Lago di Sorapis", "Lago di Sorapis turquoise lake",
     ["Lago di Sorapis", "Sorapis lake", "Lago Sorapiss"], ["sorap"], [])
slot("C09f", "9", "Tofane", "Tofane group above Cortina",
     ["Tofane Cortina", "Tofana di Rozes", "Cortina d'Ampezzo Tofane"], ["tofan"], ["ski", "winter"])
slot("C09g", "9", "Rifugio Nuvolau", "Rifugio Nuvolau hut",
     ["Rifugio Nuvolau", "Nuvolau hut Dolomites", "Rifugio Averau"], ["nuvolau", "averau"], [], min_w=1800)

# Chapter 10
slot("C10a", "10", "Tre Cime loop", "Tre Cime di Lavaredo",
     ["Tre Cime di Lavaredo", "Drei Zinnen", "Tre Cime Lavaredo summer"], ["tre cime", "drei zinnen", "lavaredo"], ["winter", "ski", "snow"])
slot("C10b", "10", "Rifugio Locatelli", "Rifugio Locatelli with the Tre Cime",
     ["Rifugio Locatelli", "Dreizinnenhütte", "Locatelli hut Tre Cime"], ["locatelli", "dreizinnenh"], [])
slot("C10c", "10", "Cadini di Misurina", "Cadini di Misurina spires",
     ["Cadini di Misurina", "Cadini group Misurina", "Cadini di Misurina Dolomites"], ["cadini"], ["winter"])
slot("C10d", "10", "Lago di Misurina", "Lago di Misurina",
     ["Lago di Misurina", "Misurina lake Dolomites", "Misurina"], ["misurina"], ["winter", "ice"])
slot("C10e", "10", "Val Fiscalina", "Val Fiscalina (Fischleintal) valley near Sesto",
     ["Val Fiscalina", "Fischleintal Sexten", "Sesto Dolomites Fiscalina"], ["fiscalina", "fischlein", "sexten", "sesto"], ["winter", "ski"])
slot("C10f", "10", "San Candido", "San Candido (Innichen) old town or collegiate church",
     ["Innichen Stiftskirche", "San Candido collegiata", "Innichen Dolomites"], ["innichen", "san candido"], ["winter"])
slot("C10g", "10", "Lago di Dobbiaco", "Lago di Dobbiaco (Toblacher See)",
     ["Toblacher See", "Lago di Dobbiaco", "Dürrensee Toblach"], ["toblacher", "dobbiaco", "toblach"], ["winter"])
slot("C10h", "10", "Lago di Braies (second view)", "Lago di Braies from a different angle",
     ["Pragser Wildsee", "Lago di Braies Seekofel", "Lake Braies Dolomites"], ["braies", "pragser"], ["winter", "snow"])
slot("C10i", "10", "Alta Via 1 start", "Alta Via 1 signpost or path at Lago di Braies",
     ["Alta Via 1 Dolomiti", "Alta Via 1 Lago di Braies", "Alta Via 1 signpost"], ["alta via"], [], min_w=1600)

# Chapter 11
slot("C11a", "11", "Vajolet Towers", "The Vajolet Towers in the Catinaccio group",
     ["Torri del Vajolet", "Vajolettürme", "Vajolet Towers Catinaccio"], ["vajolet", "vaiolet"], ["winter"])
slot("C11b", "11", "Catinaccio", "Catinaccio (Rosengarten) group seen across Val di Fassa",
     ["Catinaccio Rosengarten", "Rosengartengruppe Dolomiten", "Catinaccio Vigo di Fassa"], ["catinaccio", "rosengarten"], ["winter", "ski"])
slot("C11c", "11", "Marmolada", "Marmolada glacier and the highest peak",
     ["Marmolada", "Marmolada glacier", "Marmolada Punta Penia"], ["marmolada"], ["winter", "ski"])
slot("C11d", "11", "Lago di Carezza", "Lago di Carezza with the Latemar",
     ["Lago di Carezza", "Karersee Latemar", "Carezza lake"], ["carezza", "karersee"], ["winter"])
slot("C11e", "11", "Canazei", "Canazei village",
     ["Canazei", "Canazei Val di Fassa", "Canazei Sella"], ["canazei"], ["winter", "ski"])
slot("C11f", "11", "Passo Fedaia", "Lago di Fedaia beneath the Marmolada",
     ["Lago di Fedaia", "Fedaia Marmolada lake", "Passo Fedaia"], ["fedaia"], ["winter"])

# Chapter 12
slot("C12a", "12", "Bolzano", "Bolzano old town (Piazza Walther or the arcades)",
     ["Bolzano Piazza Walther", "Bozen Waltherplatz", "Bozen Laubengasse", "Bolzano old town"], ["bolzano", "bozen"], ["christmas", "weihnacht", "ski"])
slot("C12b", "12", "Brixen", "Brixen (Bressanone) cathedral or old town",
     ["Brixen Dom", "Bressanone cathedral cloister", "Brixen Altstadt"], ["brixen", "bressanone"], ["christmas", "weihnacht"])
slot("C12c", "12", "Neustift Abbey", "Neustift Abbey (Novacella)",
     ["Neustift Abbey Novacella", "Kloster Neustift Brixen", "Abbazia di Novacella"], ["neustift", "novacella"], [])
slot("C12d", "12", "Earth pyramids", "The earth pyramids of Ritten (Renon)",
     ["Earth pyramids Ritten", "Erdpyramiden Ritten", "Piramidi di terra Renon"], ["erdpyramid", "earth pyramid", "piramidi"], [])
slot("C12e", "12", "Plan de Corones", "Kronplatz (Plan de Corones) summit view",
     ["Kronplatz summit", "Plan de Corones Kronplatz view", "Kronplatz Gipfel"], ["kronplatz", "plan de corones"], ["ski", "winter", "mmm", "museum", "hadid"])
slot("C12f", "12", "Renon cableway", "Ritten (Renon) cable car above Bolzano",
     ["Rittner Seilbahn", "Renon cable car Bolzano", "Funivia del Renon"], ["ritten", "renon", "rittner"], [], min_w=1800)

# Chapter 13
slot("C13a", "13", "Hiking", "Walkers on a Dolomites trail seen from a distance",
     ["hikers Dolomites trail", "Wanderer Dolomiten Weg", "hiking Dolomites summer"], ["hik", "wander", "trekking", "escursion"], ["ski", "winter"])
slot("C13b", "13", "Mountain huts", "A mountain hut (rifugio) in the Dolomites",
     ["Rifugio Dolomites", "Rifugio Lagazuoi", "Rifugio Fanes", "Schutzhütte Dolomiten"], ["rifugio", "hütte", "refuge"], ["winter", "ski"])
slot("C13c", "13", "Trail markings", "Red-white trail markings on a rock or signpost",
     ["trail marking Südtirol red white", "Wegmarkierung Südtirol", "CAI segnavia rosso bianco", "hiking trail waymark Dolomites signpost"],
     ["marking", "markierung", "segnavia", "waymark", "wegweiser", "signpost", "wegzeichen"], [], min_w=1600)
slot("C13d", "13", "Alta Via 1", "A high-level trail view on the Alta Via 1",
     ["Alta Via 1 Dolomites", "Alta Via 1 Fanes", "Alta Via 1 Lagazuoi Nuvolau"], ["alta via", "fanes", "lagazuoi", "nuvolau"], ["winter"])

# Chapter 14
slot("C14a", "14", "Via ferrata", "Climbers on a via ferrata in the Dolomites",
     ["via ferrata Dolomites", "Klettersteig Dolomiten", "via ferrata Cortina"], ["ferrata", "klettersteig"], [])
slot("C14b", "14", "Cycling", "Road cyclists on a Dolomites pass",
     ["cyclists Passo Pordoi", "Sellaronda Bike Day", "Maratona dles Dolomites", "Radfahrer Sellajoch"], ["cycl", "bike", "rad", "maratona", "ciclist"], ["winter"])
slot("C14c", "14", "Mountain biking", "Mountain biking at Kronplatz or in South Tyrol",
     ["Kronplatz bike park", "mountain bike Dolomites", "Mountainbike Südtirol"], ["bike", "mountain bik", "mountainbike", "mtb"], ["winter"])
slot("C14d", "14", "Paragliding", "Paraglider over the Dolomites",
     ["paragliding Seceda", "Paragleiter Seiser Alm", "paragliding Dolomites"], ["paragl", "paragleit", "parapendio"], [])
slot("C14e", "14", "Easy cycling", "The Dobbiaco to Cortina cycle path or Pustertal cycle path",
     ["Dobbiaco Cortina cycle path", "Radweg Toblach Cortina", "Pustertal cycle path", "Ciclabile Dobbiaco Cortina"],
     ["radweg", "ciclabile", "cycle path", "cycle track", "pustertal", "dobbiaco"], [], min_w=1600)

# Chapter 15
slot("C15a", "15", "Ski areas", "Ski slope in Val Gardena or Alta Badia",
     ["Val Gardena ski slope", "Gröden Skipiste", "Alta Badia ski slope", "Dolomites skiing"], ["ski", "piste", "skipiste"], [])
slot("C15b", "15", "Sella Ronda", "Skiers on the Sella Ronda circuit",
     ["Sellaronda ski", "Sella Ronda skiers", "Sellaronda sign"], ["sellaronda", "sella ronda"], [], min_w=1800)
slot("C15c", "15", "Christmas markets", "Christmas market in Bolzano or Brixen",
     ["Bolzano Christmas market", "Bozner Christkindlmarkt", "Brixen Christmas market", "Weihnachtsmarkt Südtirol"], ["christmas", "weihnacht", "christkindl", "natale"], [])
slot("C15d", "15", "Sledging", "Tobogganing or snow walking at Seiser Alm",
     ["Seiser Alm winter sled", "Rodeln Seiser Alm", "Rasciesa toboggan", "snowshoe Dolomites"], ["sled", "rodel", "toboggan", "snowshoe", "schneeschuh", "slitt"], [], min_w=1600)
slot("C15e", "15", "Cortina in winter", "Cortina d'Ampezzo ski area (Olympic slope)",
     ["Cortina d'Ampezzo ski Tofana", "Olimpia delle Tofane", "Cortina d'Ampezzo winter"], ["cortina", "tofan"], ["summer"])

# Chapter 16
slot("C16a", "16", "Canederli", "A dish of canederli (Knödel) dumplings",
     ["Canederli", "Speckknödel", "Knödel South Tyrol", "Canederli in brodo"], ["canederli", "knödel", "knoedel", "dumpling"], [], min_w=1600)
slot("C16b", "16", "Speck", "A board of Speck Alto Adige",
     ["Speck Alto Adige", "Südtiroler Speck", "Speck Südtirol Brettljause"], ["speck"], [], min_w=1600)
slot("C16c", "16", "Desserts", "Apple strudel or Kaiserschmarrn",
     ["Kaiserschmarrn", "Apfelstrudel", "Strudel South Tyrol"], ["strudel", "kaiserschmarrn"], [], min_w=1600)
slot("C16d", "16", "Wine", "Vineyards in South Tyrol",
     ["South Tyrol vineyards", "Südtirol Weinberge", "Alto Adige vineyards Bolzano"], ["vineyard", "weinberg", "vigneti", "wein"], [])
slot("C16e", "16", "Törggelen", "Roasted chestnuts or a Törggelen farm inn table",
     ["Törggelen", "Keschtn roasted chestnuts South Tyrol", "Edelkastanien Südtirol", "Buschenschank Südtirol"], ["törggelen", "toerggelen", "kastanien", "chestnut", "buschenschank", "keschtn"], [], min_w=1400)
slot("C16f", "16", "Schlutzkrapfen", "Schlutzkrapfen ravioli",
     ["Schlutzkrapfen", "Schlutzer South Tyrol"], ["schlutz"], [], min_w=1400)

# Chapter 17
slot("C17a", "17", "Great War", "Trenches and positions in the Cinque Torri open-air museum",
     ["Cinque Torri trenches", "Cinque Torri open air museum", "Cinque Torri Great War"], ["cinque torri"], [], min_w=1800)
slot("C17b", "17", "Great War (Lagazuoi)", "Great War remains on Lagazuoi or Falzarego",
     ["Lagazuoi Great War", "Falzarego Great War", "Col di Lana Great War"], ["lagazuoi", "falzarego", "col di lana"], [], min_w=1800)
slot("C17c", "17", "Enrosadira", "Pink alpenglow (enrosadira) on Dolomites rock",
     ["enrosadira", "alpenglow Dolomites", "Alpenglühen Dolomiten", "Dolomites sunset red peaks"], ["enrosadira", "alpenglow", "alpenglühen", "sunset", "sunrise"], ["winter", "ski"])
slot("C17d", "17", "Ladin culture", "Ladin traditional costume or Ladin culture in Val Gardena or Alta Badia",
     ["Ladin traditional costume", "Ladins Val Gardena costume", "Ladin festival Val Badia"], ["ladin"], [], min_w=1400)
slot("C17e", "17", "Photography", "A photographer at a Dolomites viewpoint at dawn (small in frame)",
     ["photographer Dolomites sunrise", "photographer Seceda", "photographer Tre Cime"], ["photograph", "fotograf"], [], min_w=1600)
slot("C17f", "17", "Protected plants", "Edelweiss or alpine gentian in the Dolomites",
     ["edelweiss Dolomites", "Edelweiß Südtirol", "gentian Dolomites alpine flower"], ["edelweiss", "edelweiß", "stella alpina", "gentian", "enzian"], [], min_w=1400)

# Chapter 19
slot("C19a", "19", "Emergencies", "Mountain rescue helicopter in South Tyrol or the Dolomites",
     ["Pelikan helicopter South Tyrol", "Soccorso alpino elicottero Dolomiti", "Bergrettung Hubschrauber Südtirol", "rescue helicopter Dolomites"],
     ["helicopter", "hubschrauber", "elicottero", "pelikan"], [], min_w=1600)
slot("C19b", "19", "Thunderstorms", "Storm clouds building over Dolomites peaks",
     ["thunderstorm Dolomites", "Gewitter Dolomiten", "storm clouds Dolomites", "temporale Dolomiti"], ["thunder", "gewitter", "storm", "temporale", "cloud"], ["winter", "ski"])

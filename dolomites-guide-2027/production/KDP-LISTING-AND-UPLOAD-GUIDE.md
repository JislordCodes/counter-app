# Dolomites Travel Guide 2027: KDP listing and upload guide

Everything in this folder is ready to upload. This guide says which file goes where, and gives the text for each KDP field.

## 1. Which file goes where

| What you are doing in KDP | Upload this file |
|---|---|
| **Paperback > Manuscript** | `Paperback/Dolomites-Travel-Guide-2027_Paperback-Interior_6x9.pdf` |
| **Paperback > Cover** (choose "Upload a cover you already have (print-ready PDF)") | `Paperback/Dolomites-Travel-Guide-2027_Paperback-Cover-Wrap.pdf` |
| **Kindle ebook > Manuscript** | `Ebook/Dolomites-Travel-Guide-2027_Ebook.epub` |
| **Kindle ebook > Cover** | `Ebook/Dolomites-Travel-Guide-2027_Ebook-Cover_1600x2560.jpg` |

The other files are for you:

- `Ebook/…_Ebook.pdf` is a colour PDF with the cover as page 1. KDP does not accept PDF for ebooks, so use it as a reading copy, a download, or a sample.
- `Paperback/…_Paperback-Interior_6x9.docx` and `Ebook/…_Ebook.docx` are editable Word versions with real Word styles (Heading 1 to 4, Caption, contents field, real lists, repeating table headers). Use them if you want to change the text yourself.
- `QA-REPORT.md` lists the automatic checks that were run on every file.

## 2. Book details

| Field | Entry |
|---|---|
| Language | English |
| Book title | Dolomites Travel Guide 2027 |
| Subtitle | Plan Your Trip to Italy's Dolomites: Reservations, Costs, Hikes, Itineraries and Maps |
| Series | None |
| Edition number | 1 |
| Author | Dave Velaquez |
| Contributors | None |
| Reading age | Leave blank |
| Adult content | No |

### Description (paste into the KDP description box; the HTML is accepted)

```html
<b>Plan the Dolomites once, and get it right.</b>
<br><br>
The Dolomites are as famous for reservations as for views. In 2026, the Seceda lifts, Lago di Braies by car, the Tre Cime toll road and the Alpe di Siusi road all had booking or timed-access rules in summer. Arrive without a plan and you can lose a day, or a viewpoint.
<br><br>
<b>Dolomites Travel Guide 2027</b> shows what to book, when to book it and what it costs. It then takes you through six regions with At-a-Glance boxes, honest downsides, and plans for good and bad weather.
<br><br>
<b>Inside you will find:</b>
<ul>
<li>A booking guide for 2027: what to reserve first, how far ahead, and what you can leave open</li>
<li>Real daily budgets, lift passes, parking and hidden costs</li>
<li>Where to stay: bases compared for different kinds of traveller</li>
<li>Six regions: Val Gardena and Alpe di Siusi; Alta Badia and the Sella Ronda; Cortina d'Ampezzo; Tre Cime, Sesto and Braies; Val di Fassa, Catinaccio and Marmolada; Plan de Corones, Brixen and Bolzano</li>
<li>16 maps and 79 photographs</li>
<li>20 hikes at a glance, mountain-hut advice, via ferrata, cycling and family options</li>
<li>Ready-to-follow itineraries for 3 to 10 days, including car-free, budget and rainy-day versions</li>
<li>Winter and ski-season basics, Christmas markets and ideas for non-skiers</li>
<li>Food and drink, etiquette, safety, rescue costs, packing lists and a pre-trip checklist</li>
</ul>
<b>Written to be used.</b> Short sentences, clear tables and the same layout in every chapter, so you can compare places quickly.
<br><br>
<i>Prices, opening dates and rules are based on the 2026 season. The book says so wherever it matters and lists the official websites to check before you travel.</i>
```

### Keywords (seven boxes, each under 50 characters)

1. `Dolomites travel guide 2027`
2. `Italy Dolomites hiking and itineraries`
3. `Tre Cime Seceda Lago di Braies booking rules`
4. `South Tyrol travel guide with maps`
5. `Cortina Val Gardena Alta Badia where to stay`
6. `Dolomites costs budget lift passes parking`
7. `Italian Alps trip planner via ferrata huts`

### Categories (choose the closest match in KDP's picker)

- Travel > Europe > Italy
- Travel > Special Interest > Adventure (or the nearest hiking and outdoors category KDP offers)
- A third travel category of your choice

## 3. Paperback print options

| Setting | Choice |
|---|---|
| ISBN | Free KDP ISBN (or your own) |
| Print options: Interior | Black & white interior |
| Paper | White paper (the cover spine is calculated for white paper) |
| Trim size | 6 x 9 in (15.24 x 22.86 cm) |
| Bleed | No bleed (the interior has no images running off the page) |
| Cover finish | Matte (glossy also works) |
| Page count | 216 |
| Spine width (already built into the cover) | 0.4864 in (216 pages x 0.002252 in) |
| Cover size (already built) | 12.74 x 9.25 in (back 6 in, spine 0.4864 in, front 6 in, plus 0.125 in bleed on every side) |

If you ever change the text and the page count changes, rebuild with `python3 -m tools.bookbuild.make_all`; the cover is recalculated for the new spine.

## 4. Pricing (estimates, check KDP's calculator)

**Paperback.** KDP's black-and-white print cost for a 6 x 9 in book was about $1.00 plus $0.012 per page at the time of writing, so about $3.59 for 216 pages. The royalty is 60% of the list price minus that cost.

| List price | Royalty per copy |
|---|---|
| $12.99 | about $4.20 |
| $14.99 | about $5.40 |
| $16.99 | about $6.60 |

**Ebook.** The 70% royalty applies to list prices from $2.99 to $9.99. KDP charges a delivery fee of about $0.15 per MB on that option. The EPUB is 7.8 MB, so about $1.18 per sale.

| List price | Royalty per copy |
|---|---|
| $6.99 | about $3.72 |
| $7.99 | about $4.42 |
| $8.99 | about $5.12 |

## 5. Before you press Publish

1. **Read the interior PDF once, start to finish.** It is the file readers will hold.
2. **AI disclosure.** KDP asks whether the book contains AI-generated content. The text of this book was drafted with AI from researched sources, so answer **Yes** for text and describe it honestly. The photographs are real photographs from Wikimedia Commons; the maps are drawn by software from OpenStreetMap data. You are responsible for the accuracy of what you publish.
3. **Check the facts flagged in the research notes** (`research/verified-facts-2026.md`, items marked VERIFY): Seceda booking rules, Passo Giau and Lago di Carezza parking, Mobilcard prices, ETIAS start date, rental-car costs and a few lift prices. Rules for 2027 are normally published in spring 2027, so consider a corrected edition then.
4. **Author note.** The book ends with a short author note that does not claim any trips or experience. Add true personal details if you want them, and delete anything that is not true.
5. **Order a proof copy** from KDP before publishing. It is sold at printing cost and shows how the photographs print on a black-and-white press.
6. **Use KDP's previewers.** In the Print Previewer, check that nothing sits in the barcode area at the lower part of the back cover (KDP adds the barcode). In Kindle Previewer, open the EPUB on the phone, tablet and e-reader views.
7. **Photographs and credits.** Every photograph is credited in Appendix F, as the CC BY and CC BY-SA licences require. The CC BY-SA photographs were cropped and converted to greyscale, so the credits say they are shared under the same licence. Map data credit (OpenStreetMap contributors) is printed on each map and in Appendix F.

## 6. What was built and how

- **Typesetting.** The PDFs are typeset with Typst. Fonts are EB Garamond (text), Playfair Display (headings) and Source Sans 3 (tables and labels). All three are open-licence fonts and are embedded in the PDFs.
- **Interior layout.** 6 x 9 in, mirrored margins (inside 0.85 in, outside 0.62 in), justified and hyphenated text, running heads with the chapter title on right-hand pages and the book title on left-hand pages, page numbers on the outer edge, chapters and parts starting on right-hand pages, Roman numerals for the front matter and Arabic numerals from Chapter 1.
- **Cover.** Live type over a sky gradient and a photograph of the Tre Cime by Pavel Spindler (CC BY 3.0, credited in Appendix F). The back cover leaves the barcode area clear.
- **Checks.** Page size, embedded fonts, margins against KDP's minimums, orphaned headings, nearly empty pages, EPUB validity and cover dimensions are in `QA-REPORT.md`.

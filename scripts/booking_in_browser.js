// Collecte Booking réellement utilisée pour le jeu de données livré.
// Équivalent de kayak/booking.py, exécuté dans la console d'un onglet booking.com
// (le navigateur ayant déjà passé le challenge anti-bot, fetch() same-origin renvoie le HTML).
// Résultat : window.BK.rows, exporté ensuite en data/hotels.csv.
const CITIES = ["Mont Saint Michel","St Malo","Bayeux","Le Havre","Rouen","Paris","Amiens","Lille","Strasbourg","Chateau du Haut Koenigsbourg","Colmar","Eguisheim","Besancon","Dijon","Annecy","Grenoble","Lyon","Gorges du Verdon","Bormes les Mimosas","Cassis","Marseille","Aix en Provence","Avignon","Uzes","Nimes","Aigues Mortes","Saintes Maries de la mer","Collioure","Carcassonne","Ariege","Toulouse","Montauban","Biarritz","Bayonne","La Rochelle"];
const N = 20, sleep = ms => new Promise(r => setTimeout(r, ms));
const parse = t => new DOMParser().parseFromString(t, "text/html");

async function html(url) {
  for (let k = 0; k < 3; k++) {
    try { const r = await fetch(url, { credentials: "include" }); if (r.ok) return parse(await r.text()); } catch (e) {}
    await sleep(4000 * (k + 1));
  }
  return null;
}

function score(t) { // "Scored 8.0 8.0 Very good 2,192 reviews" -> [8.0, 2192]
  if (!t) return [null, null];
  const s = t.match(/\d+(?:\.\d+)?/), n = t.match(/([\d,]+)\s+reviews?/);
  return [s ? +s[0] : null, n ? +n[1].replace(/,/g, "") : null];
}

window.BK = { rows: [], log: [], done: false };
(async () => {
  for (let i = 0; i < CITIES.length; i++) {
    const c = CITIES[i];
    const d = await html("/searchresults.en-gb.html?lang=en-gb&ss=" + encodeURIComponent(c + ", France"));
    if (!d) { BK.log.push(c + ": search failed"); continue; }
    const cards = [...d.querySelectorAll('[data-testid="property-card"]')].slice(0, N);
    for (const card of cards) {
      const url = (card.querySelector('a[data-testid="title-link"]')?.getAttribute("href") || "").split("?")[0];
      const [sc, nr] = score(card.querySelector('[data-testid="review-score"]')?.textContent);
      const row = { city_id: i + 1, city: c, name: card.querySelector('[data-testid="title"]')?.textContent.trim(),
                    url, score: sc, n_reviews: nr, lat: null, lon: null, description: "" };
      const h = url ? await html(url) : null;
      if (h) {
        const ll = h.querySelector("[data-atlas-latlng]")?.getAttribute("data-atlas-latlng");
        if (ll) [row.lat, row.lon] = ll.split(",").map(Number);
        row.description = (h.querySelector('[data-testid="property-description"]')?.textContent || "").trim();
      }
      BK.rows.push(row);
      await sleep(1000); // rester raisonnable avec le site
    }
    BK.log.push(`${i + 1} ${c}: ${cards.length}`);
  }
  BK.done = true;
})();

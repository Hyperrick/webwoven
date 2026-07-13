# Gesamtplan: Relink

*Arbeitstitel, noch nicht markenrechtlich geprüft.*

## 1. Produktentscheidung

Relink wird **kein Wikipedia-Rennspiel**, sondern ein kompetitives Spiel über einen kuratierten Open-Knowledge-Graphen:

> **Connect anything. Discover why it is connected.**

Spieler bewegen sich zwischen Personen, Orten, Ereignissen, Tieren, Werken, Organisationen und wissenschaftlichen Konzepten. Jeder Zug folgt einer echten, benannten Beziehung:

- born in
- created by
- member of
- located in
- influenced by
- discovered by
- depicts
- performed by

Der Spieler sieht also nicht einfach Hyperlinks, sondern versteht bei jedem Zug, **warum zwei Dinge miteinander verbunden sind**.

Die notwendige Abgrenzung lautet: Die Marktlücke ist nicht „Wikipedia, aber Multiplayer“, sondern ein **visuell eigenständiges, typisiertes und erklärbares Wissensnetz mit kuratierten Spielrunden und mehreren offenen Datenwelten**.

Arbeitsannahmen:

- kleines Team von ein bis drei Personen
- fünf produktive Build-Week-Tage
- English-only
- Desktop und Mobile Web
- Docker auf einem europäischen VPS
- FastAPI als Backend
- kein Next.js
- kein generisches Tailwind-/Shadcn-Dashboard
- Gastzugang im Build-Week-Prototyp
- Accounts nach der Build Week

---

## 2. Kernmechanik

### 2.1 Ablauf einer normalen Runde

Vor dem Start wählt der Spieler:

- Category
- Difficulty
- Solo oder Multiplayer
- Game Mode

Danach erhält er:

```text
START: Blue whale
TARGET: The Beatles
PAR: 6 moves
```

Auf dem aktuellen Knoten sieht er:

1. den englischen Namen
2. ein geprüftes Bild oder eine hochwertige grafische Ersatzdarstellung
3. einen kurzen, strukturierten Fakt
4. fünf bis acht navigierbare Beziehungen
5. den bisherigen Pfad
6. verfügbare Joker

Ein mögliches Verhältnis:

```text
Blue whale
  ├─ taxonomic parent → Balaenoptera
  ├─ found in → Pacific Ocean
  ├─ conservation status → Endangered species
  ├─ depicted on → Canadian five-cent coin
  └─ studied by → Marine biology
```

Das Öffnen einer Beziehungsgruppe ist kostenlos. Erst die Auswahl des Zielknotens zählt als Zug.

Nach einem Zug erscheint eine kurze Erklärung:

> “The blue whale occurs throughout the Pacific Ocean.”

Diese Erklärung stammt aus der gespeicherten Beziehung und nicht aus einem frei halluzinierenden Sprachmodell.

### 2.2 Zurückgehen

Der Back-Button ist erlaubt und erzeugt einen normalen `MOVE_BACK`-Event.

- Back zählt als Zug.
- Der komplette Pfad bleibt sichtbar.
- In Exact Route kann Back strategisch sinnvoll sein.
- Wiederholte Schleifen können in gewerteten Runden leicht bestraft werden.

Browser-Back und In-Game-Back müssen getrennt behandelt werden. Der Browser-Back-Button darf nicht versehentlich eine laufende Session verlassen; die Spielnavigation verwendet einen eigenen Zustand.

### 2.3 Kategorien

Die Kategorie bestimmt primär Start, Ziel, Hinweisstil und Datenpaket. Zwischenknoten dürfen Kategorien überschreiten.

Für die erste Version:

| Kategorie | Typische Inhalte |
|---|---|
| History & People | Personen, Ereignisse, Reiche, Institutionen |
| Nature & Science | Arten, Entdeckungen, Disziplinen, Naturphänomene |
| Arts & Culture | Bücher, Filme, Kunstwerke, Künstler |
| Places | Städte, Länder, Gebäude, Landschaften |
| Mixed | Kategorieübergreifende Verbindungen |

Nach Daten- und Qualitätsprüfung:

- Music
- Sports
- Technology
- Space
- Museums
- Research

---

## 3. Spielmodi

### 3.1 Route Race

Das bekannte Ziel soll mit möglichst wenigen Zügen erreicht werden.

Wertung:

- Routeneffizienz ist wichtiger als Geschwindigkeit.
- Back zählt als Zug.
- Hinweise kosten Punkte.
- Zeit entscheidet bei ähnlich effizienten Wegen.

### 3.2 Live Relay

Zwei bis vier Spieler erhalten denselben Start und dasselbe Ziel.

Während des Rennens sehen sie voneinander nur:

- Anzahl der Züge
- grobe Fortschrittsstufe
- Hint-Nutzung
- Ziel erreicht oder nicht

Der aktuelle Knoten eines Gegners wird nicht angezeigt.

### 3.3 Daily Connection

Alle Spieler erhalten an einem Kalendertag dieselbe geprüfte Runde.

- globales Leaderboard
- persönliche Bestzeit
- optimale Distanz
- Anteil der Spieler, die das Ziel erreicht haben
- Share Card ohne Spoiler

Die Daily Round ist der wichtigste Retention-Mechanismus für den MVP.

### 3.4 Hidden Target

Das Ziel ist zunächst unbekannt.

Beispiel:

> Find a scientist who was born in Poland, worked in France and had a chemical element named after them.

Der Spieler navigiert und darf jederzeit einen Zielknoten einreichen. Falsche Vermutungen kosten Punkte.

### 3.5 Exact Route

Das System gibt eine gewünschte Zugzahl vor:

```text
Reach the target in exactly 8 moves.
```

Sechs oder zehn Züge ergeben eine Abweichung von zwei. Nicht nur der kürzeste Weg ist relevant; der Spieler muss einen kontrollierten Umweg finden.

### 3.6 Knowledge Round

Nach der Navigation folgen drei Fragen über besuchte Knoten:

- Multiple Choice
- Which happened first?
- Higher or lower?
- Which entity belongs to this image?
- Which relationship was part of your route?

Die Fragen dürfen nur Fakten verwenden, die tatsächlich im geprüften Datenpaket der Runde vorhanden sind.

### 3.7 Image Match

Vier Bilder, vier Entitäten oder vier Beschreibungen:

> Which image best matches the entity “The Great Wave off Kanagawa”?

Für Bildausschnitte und Bearbeitungen sollte zunächst nur CC0- beziehungsweise Public-Domain-Material verwendet werden.

---

## 4. Scoring

### 4.1 Standardrunde

Sei:

- `d*` = kürzeste bekannte Distanz
- `m` = tatsächlich benötigte Züge inklusive Back
- `t` = benötigte Sekunden
- `T` = Zeitfenster der Schwierigkeitsstufe
- `p` = Hint- und Fehlversuchskosten

Dann:

```text
efficiency = d* / max(m, d*)
speed      = max(0, 1 - t / T)

score = clamp(
    round(1000 × (0.80 × efficiency + 0.20 × speed)) - p,
    0,
    1000
)
```

Damit macht eine gute Route 80 Prozent des Scores aus. Geschwindigkeit bleibt wichtig, dominiert aber nicht das Spiel.

Beispielkosten:

- Compass Hint: −75
- Path Hint: −150
- Bridge Reveal: −250
- falscher Hidden-Target-Guess: −100

### 4.2 Exact Route

```text
score =
1000
- 125 × abs(actual_moves - requested_moves)
- hint_penalties
- 30 × repeated_edge_count
```

Zeit ist in diesem Modus nur Tiebreaker.

### 4.3 Multiplayer-Wertung

Für den Build-Week-Modus:

1. zuerst gültig am Ziel
2. bei nahezu gleichzeitigem Finish: weniger Züge
3. danach weniger Hinweise
4. danach serverseitiger Finish-Zeitpunkt

Später können zwei getrennte Playlists existieren:

- **Sprint:** erster Spieler am Ziel
- **Navigator:** höchster Score innerhalb eines Zeitlimits

---

## 5. Hinweise und Helferfigur

### The Cartographer

Statt einer realen Person sollte eine eigene Figur entstehen: **The Cartographer**.

Rolle:

- erklärt Spielregeln
- gibt Hinweise
- kommentiert überraschende Beziehungen
- führt durch das End-of-Round-Reveal
- dient als visuelle Markenfigur

Die Figur sollte nicht wie ein typischer KI-Assistent in einem Chatfenster erscheinen. Besser ist eine kleine kartografische Randfigur, die sich in Kartenrändern, Stempeln, Lupen und handschriftlichen Anmerkungen zeigt.

### Joker

#### Compass

Zeigt, ob ein ausgewählter Beziehungstyp grundsätzlich näher zum Ziel führen kann.

#### Lens

Markiert eine Beziehung, die auf mindestens einer sinnvollen, nahezu optimalen Route liegt.

#### Map Fragment

Verrät einen möglichen Brückenknoten, aber nicht den vollständigen Weg.

#### Clear Fog

Entfernt einige besonders schlechte oder tote Optionen aus der aktuellen Auswahl.

Alle Hinweise werden aus vorab berechneten Distanzen und Wegen abgeleitet. Ein Sprachmodell formuliert höchstens den Text; es entscheidet nicht, welche Route korrekt ist.

### Discovery Tokens statt versteckter Coins

Discovery Tokens entstehen durch relevante Aktionen:

- eine selten genutzte Beziehung finden
- drei Kategorien in einer Route verbinden
- ohne Hinweis abschließen
- einen neuen Knoten im persönlichen Atlas entdecken
- die Abschlussfragen vollständig beantworten
- eine Route nutzen, die noch kein anderer Spieler verwendet hat

---

## 6. Datenquellen

Grundsatz:

> **Offene Datenquellen werden vorab importiert, normalisiert, lizenziert und zu unveränderlichen Graph-Versionen gebaut. Keine externe Wissens-API liegt im kritischen Spielpfad.**

### 6.1 Wikidata – Backbone des MVP

Wikidata liefert:

- Entitäten
- englische Labels und Aliasse
- kurze Beschreibungen
- typisierte Beziehungen
- externe Identifikatoren
- Links zu Mediendateien
- Quellen- und Qualifier-Informationen

Entscheidung:

- Wikidata wird der erste Knowledge-Graph-Backbone.
- Der öffentliche SPARQL-Dienst wird niemals bei einem Spielerzug aufgerufen.
- Für große Graphoperationen werden Dumps und lokale Datenhaltung verwendet.
- Jede Produktionsrunde verweist auf eine lokale, versionierte Graph-Version.
- Wikipedia-Artikeltexte werden im MVP nicht kopiert.

### 6.2 Wikimedia Commons – Bilder

Commons ist keine einheitliche Lizenzquelle. Jede Datei kann eine andere Lizenz, Urheberschaft und Attributionspflicht besitzen.

MVP-Allowlist:

- Public Domain
- CC0
- CC BY 4.0
- CC BY-SA 4.0 nach sauberer Implementierung der Anforderungen

Ausschließen:

- NC
- ND
- unklare Lizenz
- fehlender Urheber
- problematische Persönlichkeits- oder Markenrechte
- grafisch sensible Bilder ohne Review

Jedes Bild benötigt:

```text
source
source_file_id
creator
license
license_url
attribution_text
original_url
retrieved_at
content_review_status
sha256
```

### 6.3 The Metropolitan Museum of Art

Geeignet für:

- Image Match
- Art timelines
- created by
- depicts
- material
- period
- culture
- collection
- place of origin

Das Met eignet sich hervorragend für einen späteren Museum- oder Culture-World-Modus.

### 6.4 Smithsonian Open Access

Geeignet für:

- Museum Heist
- Object Detective
- historische Gegenstände
- Naturkunde
- Wissenschaftsgeschichte
- 3D-Objekte für spätere visuelle Modi

### 6.5 GBIF

GBIF liefert:

- Taxonomie
- Arten
- Beobachtungen
- Fundorte
- Karten
- teilweise Medien

Für eine kommerzielle Perspektive werden nur CC0- und kompatible CC-BY-Daten importiert.

Spätere Nature World:

- species → parent taxon
- species → habitat
- species → observation region
- species → named after
- species → conservation status
- species → related species

### 6.6 MusicBrainz

Geeignet für Künstler, Bands, Veröffentlichungen, Werke und Beziehungen.

Entscheidung:

- späterer Music-World-Import aus Dumps
- nur CC0-Kerndaten
- keine öffentliche API im Gameplay
- Supplementary Tags und Bewertungen zunächst ausschließen

### 6.7 OpenAlex

Geeignet für:

- work → cites
- work → author
- author → institution
- work → topic
- institution → country
- researcher → collaborator

OpenAlex ist für den MVP nicht notwendig, kann später aber einen stark differenzierten Research-Modus liefern.

### 6.8 Europeana

Europeana eignet sich für:

- europäische Kulturgeschichte
- Museumsobjekte
- historische Fotografien
- Karten
- Manuskripte

Import nur mit striktem Rights-Statement-Filter.

### 6.9 OpenStreetMap

OSM sollte nicht ungeprüft in denselben exportierten Graphen gemischt werden, sondern als getrennte, lizenzierte Geodatenebene behandelt werden.

Späterer Einsatz:

- kartografische Spielansicht
- Gebäude
- Parks
- Flüsse
- Grenzen
- räumliche Nachbarschaften

Für den MVP genügt die geografische Struktur aus Wikidata.

### 6.10 Open Library

Geeignet für:

- Book Trails
- chronological literature
- author connections
- subjects
- editions
- publication places

Für größere Importe sollten Dumps statt der öffentlichen API verwendet werden.

---

## 7. Datenstrategie

### Build Week

Nur:

1. Wikidata für Entitäten und Beziehungen
2. streng gefilterte Wikimedia-Commons-Bilder
3. eigene generierte UI-Grafiken und Maskottchen
4. optional ein sehr kleines, manuell geprüftes Met-Demo-Pack

Zielgröße:

- 5.000 bis 10.000 spielbare Entitäten
- 40.000 bis 100.000 kuratierte gerichtete Kanten
- 12 bis 20 sichtbare Beziehungstypen
- 100 bis 150 geprüfte Runden
- vier Kategorien
- mindestens 80 Prozent Bildabdeckung für Start- und Zielknoten

### Public MVP

- 50.000 bis 100.000 Entitäten
- 500.000 bis 1,5 Millionen spielbare Kanten
- mindestens 1.000 validierte Runden
- Met oder Smithsonian als erste zusätzliche Welt
- separates Admin-Review
- monatliche Graph-Builds

Ein kleiner, gut kuratierter Graph erzeugt ein besseres Spiel als Millionen chaotischer Beziehungen.

---

## 8. Datenmodell

### 8.1 Entität

```text
entity
- id
- namespace
- external_id
- canonical_label_en
- description_en
- entity_type
- category_ids
- notability_score
- content_rating
- image_status
- source_snapshot_id
- active
```

IDs bleiben namespaced:

```text
wd:Q42
met:436535
smithsonian:edanmdm-...
gbif:5219404
musicbrainz:...
```

Entitäten aus unterschiedlichen Quellen werden nur zusammengeführt, wenn ein eindeutiger externer Identifier oder ein geprüfter Crosswalk existiert.

### 8.2 Beziehung

```text
edge
- id
- graph_build_id
- source_entity_id
- target_entity_id
- relation_type_id
- source_statement_id
- source_dataset_id
- rank
- qualifiers_json
- valid_from
- valid_to
- playable
- review_status
```

### 8.3 Beziehungstyp

```text
relation_type
- id
- key
- forward_label
- inverse_label
- source_type_constraint
- target_type_constraint
- inverse_playable
- max_edges_per_node
- category
- clue_template
- explanation_template
```

Beispiel:

```text
key: born_in
forward: "born in"
inverse: "birthplace of"
source: person
target: place
```

Inverse Beziehungen werden nicht pauschal aktiviert.

### 8.4 Medien

```text
entity_media
- id
- entity_id
- local_asset_path
- source_url
- creator
- license_code
- attribution_text
- modifications
- width
- height
- focal_point
- review_status
- content_hash
```

### 8.5 Graph-Version

```text
graph_build
- id
- semantic_version
- source_snapshot_dates
- relation_registry_version
- node_count
- edge_count
- manifest_hash
- created_at
- published_at
- status
```

Jede Runde und jede Session speichert:

```text
graph_build_id
scoring_version
round_generator_version
```

---

## 9. Graph-Aufbereitung

### 9.1 Importpipeline

```text
Source snapshots
      ↓
Raw staging files
      ↓
License and provenance filter
      ↓
Entity normalization
      ↓
Relationship normalization
      ↓
Category classification
      ↓
Hub and quality pruning
      ↓
Playable graph build
      ↓
Round generation
      ↓
Automated validation
      ↓
Editorial review
      ↓
Immutable published graph
```

### 9.2 Auswahl spielbarer Beziehungen

Nicht als normale Wege verwenden:

- instance of
- subclass of
- sex or gender
- occupation als unbegrenzter Rückweg
- generic topic
- Wikimedia category
- administrative IDs
- externe Identifikatoren

Diese Daten können weiterhin für Klassifizierung und Hinweise dienen.

Gute spielbare Beziehungen:

#### People

- born in
- educated at
- employer
- member of
- award received
- notable work
- influenced by
- relative
- participant in

#### Arts & Culture

- created by
- written by
- directed by
- cast member
- composer
- performer
- depicts
- based on
- part of
- collection

#### Places & History

- located in
- capital of
- borders
- event location
- participant
- followed by
- preceded by
- named after

#### Nature & Science

- parent taxon
- endemic to
- discovered by
- named after
- field of study
- studied by
- location of discovery

### 9.3 Hub-Kontrolle

Knoten wie „human“, „United States“, „film“ oder „music“ können fast jeden Weg trivialisieren.

Gegenmaßnahmen:

- rein klassifikatorische Knoten nicht spielbar machen
- maximale Anzahl ausgehender Kanten pro Beziehung
- besonders generische Knoten aus Ranked-Runden ausschließen
- inverse Beziehungen nur kuratiert aktivieren
- Hub-Penalty bei der Rundengenerierung
- eigene „No Hubs“-Regel für schwere Runden
- relationale Vielfalt statt nur Popularität priorisieren

### 9.4 Darstellung großer Nachbarschaften

Die UI gruppiert nach Beziehung:

```text
CREATED BY       2 options
LOCATED IN       3 options
PART OF          4 options
INFLUENCED BY    1 option
```

Innerhalb einer Gruppe werden zunächst die relevantesten Ziele angezeigt. „Show more“ ist kostenlos. Ein Zug entsteht erst bei der Auswahl des Zielknotens.

---

## 10. Rundengenerierung

### 10.1 Kandidaten erzeugen

Für jedes mögliche Start-Ziel-Paar wird offline geprüft:

- Ziel erreichbar
- kürzeste Distanz
- Anzahl sinnvoller Alternativrouten
- Verzweigungsgrad
- Anteil generischer Hubs
- Bild- und Textqualität
- Kategoriepassung
- Zielbekanntheit
- Risiko von Sackgassen
- vorhandene Hint-Möglichkeiten

### 10.2 Annahmekriterien für normale Runden

Empfohlene Startwerte:

- Easy: optimale Distanz 3–4
- Normal: 4–6
- Hard: 6–8
- mindestens zwei unterschiedliche Routenkorridore
- keine direkte triviale Verbindung
- Start und Ziel mit englischem Label
- Start und Ziel mit geprüftem Bild oder hochwertigem Ersatz
- mindestens drei sinnvolle Optionen pro frühem Knoten
- kein erforderlicher obskurer Identifier-Knoten
- keine nicht erklärbare Beziehung

### 10.3 Schwierigkeitswert

```text
35% optimale Distanz
25% Verzweigungsentropie
20% Ziel-Obskurität
20% Konzentration der guten Routen
```

Das ist zunächst ein heuristisches Modell und wird später anhand realer Abschlussraten kalibriert.

### 10.4 Rundenspeicherung

```text
start_entity_id
target_entity_id
category
mode
optimal_distance
allowed_relation_types
blocked_hubs
difficulty
time_window
hint_pack
known_shortest_routes
near_shortest_bridge_nodes
graph_build_id
editorial_status
```

Die bekannten Routen werden nie vollständig an den Client geschickt.

---

## 11. Country-Interest-Minispiel

Mögliche spätere Umsetzung:

1. monatlichen Wikimedia-Bulk-Datensatz importieren
2. Seitentitel über Sitelinks auf Wikidata-QIDs abbilden
3. Länder und Territorien normalisieren
4. Aufrufe pro 100.000 Einwohner berechnen
5. kleine und stark verrauschte Werte ausschließen
6. nur Antwortoptionen mit deutlichem Abstand verwenden
7. Ergebnisse als „estimated“ kennzeichnen

Beispiel:

> In which country was this article estimated to receive the highest number of views per capita in March 2026?

Dieser Modus gehört nicht in die Build Week.

---

## 12. Technischer Stack

### 12.1 Frontend

**Entscheidung: Svelte 5 + TypeScript + Vite als eigenständiger statischer Client**

Kein Next.js, kein React, kein Full-Stack-Metaframework. FastAPI bleibt die einzige Backend- und API-Schicht.

Frontend-Stack:

```text
Svelte 5
TypeScript
Vite
Bits UI – nur Verhalten und Accessibility
TanStack Query – REST-Serverzustand
native Svelte state/runes – laufender Spielzustand
CSS Custom Properties + Cascade Layers
SVG für Pfade, Icons und Mikroanimationen
Sigma.js + Graphology für Ergebnis- und Atlas-Rendering
Vitest
Playwright
```

Sigma.js wird nur beim Ergebnis-Reveal und in der Atlas-Ansicht eingesetzt, nicht als primäre mobile Navigation.

#### Kein Tailwind im MVP

Stattdessen:

- eigene Design Tokens
- komponentenspezifisches CSS
- konsistente Abstände
- klar definierte Typografie
- definierte Radien
- definierte Bewegungszeiten
- eigene Icons
- keine zusammenkopierten Komponentenbibliotheken

### 12.2 Backend

```text
Python 3.13
FastAPI
Pydantic v2
SQLAlchemy 2
Alembic
Psycopg 3
Uvicorn
PostgreSQL
Valkey
Polars
Parquet
rustworkx
pytest
Hypothesis
Ruff
Pyright
uv
```

FastAPI übernimmt REST und WebSockets. Valkey übernimmt Räume, Pub/Sub, Streams und temporäre Leaderboards.

`rustworkx` übernimmt Offline-Graphalgorithmen. Polars und Parquet dienen der Import- und Transformationspipeline.

### 12.3 Kein Neo4j im MVP

Die Runden sind vorab berechnet. Während eines Zuges muss das Backend nur beantworten:

- Ist diese Kante gültig?
- Was ist der neue Knoten?
- Wie lautet der neue Scorezustand?
- Ist das Ziel erreicht?

Dafür ist ein kompakter lokaler Adjazenzgraph schneller und einfacher.

### 12.4 Graph-Artefakt

PostgreSQL bleibt die kanonische Datenquelle. Für das Gameplay wird pro Build ein kompaktes Read-only-Artefakt erzeugt:

```text
manifest.json
nodes.parquet
edges.parquet
node_index.parquet
offsets.bin
targets.bin
relations.bin
rounds.parquet
```

Jede Entität erhält innerhalb eines Builds eine dichte Integer-ID. Die Adjazenzdaten werden in einem CSR-ähnlichen Format gespeichert.

Vorteile:

- sehr schnelle Nachbarschaftsabfragen
- wenig Python-Objekt-Overhead
- Memory Mapping möglich
- mehrere API-Prozesse nutzen denselben OS-Page-Cache
- ein Graph-Build kann atomar ausgetauscht werden
- alte Sessions bleiben reproduzierbar

---

## 13. Systemarchitektur

```text
                         ┌────────────────────┐
                         │  Open data sources │
                         └─────────┬──────────┘
                                   │ offline
                         ┌─────────▼──────────┐
                         │ Pipeline / Worker  │
                         │ Polars + rustworkx │
                         └──────┬───────┬─────┘
                                │       │
                    canonical   │       │ immutable build
                                │       │
                      ┌─────────▼───┐ ┌─▼──────────────┐
                      │ PostgreSQL  │ │ Graph artifacts │
                      └──────┬──────┘ └──────┬─────────┘
                             │               │
                             └──────┬────────┘
                                    │
                          ┌─────────▼─────────┐
                          │ FastAPI           │
                          │ REST + WebSocket  │
                          └──────┬───────┬────┘
                                 │       │
                         ┌───────▼──┐  ┌─▼────────┐
                         │ Valkey   │  │ Caddy    │
                         │ rooms    │  │ TLS/proxy│
                         └──────────┘  └────┬─────┘
                                           │
                                  ┌────────▼────────┐
                                  │ Svelte 5 client │
                                  └─────────────────┘
```

---

## 14. Verantwortlichkeiten der Datenspeicher

### PostgreSQL

Dauerhafte Wahrheit für:

- Nutzer
- Gastprofile
- Graph-Metadaten
- Quellen und Lizenzen
- publizierte Runden
- Daily Challenges
- abgeschlossene Sessions
- Zugprotokolle
- Scores
- Asset Registry
- Analytics Events
- Moderationsmeldungen

### Valkey

Kurzlebiger Echtzeitzustand:

- aktive Räume
- Teilnehmerstatus
- Countdown
- Reconnect-Tokens
- WebSocket-Pub/Sub
- Event Streams
- Rate Limits
- temporäre Leaderboards
- gecachte Nachbarschaften

Abgeschlossene Sessions werden dauerhaft in PostgreSQL geschrieben.

### Graph-Artefakt

- gültige spielbare Kanten
- lokale Integer-Indizes
- Beziehungstypen
- Distanzinformationen
- vorab berechnete Runden
- Hint-Brückenknoten

---

## 15. API-Design

### REST

```text
GET    /api/v1/config
GET    /api/v1/categories
GET    /api/v1/daily
POST   /api/v1/sessions
GET    /api/v1/sessions/{session_id}
POST   /api/v1/sessions/{session_id}/moves
POST   /api/v1/sessions/{session_id}/hints
POST   /api/v1/sessions/{session_id}/guesses
POST   /api/v1/sessions/{session_id}/finish

POST   /api/v1/rooms
POST   /api/v1/rooms/{code}/join
GET    /api/v1/rooms/{code}

GET    /api/v1/leaderboards/daily
GET    /api/v1/leaderboards/weekly
GET    /api/v1/profile
```

Ein Move:

```json
{
  "client_command_id": "uuid",
  "expected_state_version": 12,
  "action": "follow_edge",
  "edge_token": "opaque-signed-token"
}
```

Back:

```json
{
  "client_command_id": "uuid",
  "expected_state_version": 13,
  "action": "back"
}
```

Die API antwortet mit einer neuen `state_version`. Doppelte Commands bleiben durch die `client_command_id` idempotent.

### WebSocket

```text
/api/v1/ws/rooms/{room_code}
```

Serverevents:

```text
room.snapshot
player.joined
player.left
race.countdown
race.started
move.accepted
player.progress
player.finished
race.finished
room.closed
error
ping
pong
```

Clientcommands:

```text
join
ready
start
move
hint
guess
reconnect
leave
```

---

## 16. Multiplayer-Architektur

### Serverautoritativ

Der Client darf nie selbst entscheiden:

- ob eine Kante existiert
- ob das Ziel erreicht wurde
- wie viele Züge gezählt werden
- wie hoch der Score ist
- wann der Spieler fertig war

Jeder Move wird serverseitig gegen den festgeschriebenen Graph-Build validiert.

### Room State

```text
room_id
room_code
host_player_id
round_id
graph_build_id
status
server_start_at
player_states
event_sequence
expires_at
```

### Reconnect

Der Spieler erhält beim Join:

- eine öffentliche Player-ID
- ein geheimes Reconnect-Token
- die aktuelle Event-Sequenz

Nach einem Abbruch sendet der Client seine letzte Sequenznummer. Der Server liefert entweder fehlende Events aus einem Valkey Stream oder einen vollständigen Snapshot.

### Schutz vor Kopieren

Während des Rennens werden nicht übertragen:

- aktueller Knoten anderer Spieler
- deren konkrete Beziehungen
- deren Route
- optimale Route

Sichtbar sind nur abstrakte Fortschrittswerte.

### Schutz vor einfachen Cheats

- Moves ausschließlich serverseitig
- signierte Session- und Edge-Tokens
- WebSocket-Origin-Prüfung
- Rate Limits
- serverseitige Zeit
- keine Zielhinweise im Clientbundle
- unrealistisch schnelle Daily-Runs markieren
- Wiederholungsmuster analysieren
- Ranked und Unranked trennen

---

## 17. Frontend-Art-Direction

### Gewählter Stil

> **Editorial world atlas meets premium board game**

Nicht:

- lila-blauer Gradient
- Glassmorphism
- leuchtende KI-Kugel
- austauschbare SaaS-Karten
- riesige Hero Section
- Lucide-Icons auf jeder Fläche
- 24 gleich abgerundete Rechtecke
- Dashboard-Navigation während des Spiels

Stattdessen:

- warme Papierflächen
- tiefe Tintenfarben
- ein kräftiger Signalton
- kartografische Linien
- Koordinaten, Legenden und Stempel
- asymmetrische Komposition
- sichtbare Beziehungslinien
- individuell gezeichnete Relation-Glyphen
- große redaktionelle Typografie
- gezielte, kurze Animationen

### Beispielpalette

```text
Paper        #EEE8DA
Ink          #15181C
Signal       #F0533D
Electric     #5758D7
Nature       #39745A
Gold         #C99A2E
Muted Ink    #66645E
```

### Typografie

Mögliche Richtung:

- Display: Fraunces oder Newsreader
- Interface: IBM Plex Sans oder Atkinson Hyperlegible
- kleine technische Labels: IBM Plex Mono

Die finalen Fonts werden selbst gehostet und vor Verwendung auf ihre Lizenz geprüft.

### Desktop-Spielansicht

```text
┌───────────────────────────────────────────────────────────────┐
│ Category · Round · Timer · Sound · Settings                  │
├──────────────┬─────────────────────────────┬──────────────────┤
│ ROUTE RIBBON │                             │ RELATION PORTALS │
│              │      CURRENT ENTITY         │                  │
│ Blue whale   │                             │ Found in         │
│ Pacific      │        image / art          │ Named after      │
│ ...          │                             │ Studied by       │
│              │ title · fact · source       │ Part of          │
│              │                             │                  │
├──────────────┴─────────────────────────────┴──────────────────┤
│ Cartographer hint                                             │
└───────────────────────────────────────────────────────────────┘
```

### Mobile-Spielansicht

- aktueller Knoten im oberen Bereich
- Pfad als horizontal scrollbarer Ribbon
- Beziehungen als Bottom Sheet
- Joker mit Daumen erreichbar
- Timer und Move Count immer sichtbar
- keine vollständige Graphvisualisierung während der Runde
- Ergebnisgraph erst nach Abschluss

### Bewegung

- Pfad wird in 250–400 ms gezeichnet
- neuer Knoten bewegt sich wie ein Kartenausschnitt in die Bühne
- keine dauerhaften Partikeleffekte
- keine unnötigen 3D-Kamerafahrten
- `prefers-reduced-motion` vollständig unterstützen
- Sound und Musik standardmäßig nicht ungefragt starten

### Feste Komponentenbibliothek

```text
EntityStage
EntityPortrait
RelationPortal
RelationGroup
RouteRibbon
RoundHeader
CartographerNote
HintToken
RaceTelemetry
SourceDrawer
AttributionBadge
RoundReveal
ScoreBreakdown
DailyShareCard
LobbySeat
```

Zusätzlich sollte `/lab` eine interne Component-Lab-Seite enthalten. Dort werden alle Zustände geprüft:

- default
- hover
- focus
- selected
- disabled
- loading
- reconnecting
- missing image
- long label
- error
- high contrast
- reduced motion

---

## 18. LLM- und OpenAI-Strategie

### Kein LLM im kritischen Runtime-Pfad

Das Spiel muss vollständig ohne Runtime-LLM funktionieren.

Keine LLM-Entscheidung für:

- gültige Kanten
- kürzeste Wege
- Scores
- Gewinner
- Lizenzen
- Entity Matching

### Offline Content Generation

Ein LLM kann offline verwendet werden für:

- dreistufige Hinweise
- Beziehungserklärungen
- Abschlusszusammenfassungen
- Quizformulierungen
- plausible Distraktoren aus geprüften Kandidaten
- Texte für The Cartographer
- Kategoriebeschreibungen
- originale UI- und Maskottchenillustrationen

Die Pipeline liefert ausschließlich geprüfte Fakten.

Beispielinput:

```json
{
  "target": {
    "id": "wd:Q7186",
    "label": "Marie Curie",
    "aliases": ["Maria Skłodowska-Curie"]
  },
  "verified_facts": [
    {
      "subject": "Marie Curie",
      "relation": "born in",
      "object": "Warsaw"
    },
    {
      "subject": "Marie Curie",
      "relation": "award received",
      "object": "Nobel Prize in Physics"
    }
  ],
  "difficulty": "medium",
  "forbidden_terms": [
    "Marie",
    "Curie",
    "Skłodowska"
  ]
}
```

Erwartetes Structured Output:

```json
{
  "clues": [
    {
      "tier": 1,
      "text": "...",
      "facts_used": [0],
      "answer_leak_risk": "low"
    }
  ],
  "recap": "...",
  "quiz_candidates": []
}
```

Automatische Validierung:

- Zielname oder Alias enthalten?
- Fakt außerhalb des bereitgestellten Pakets verwendet?
- falsche Jahreszahl?
- Antwort versehentlich direkt verraten?
- zu abstrakt?
- nicht in Englisch?
- nicht schema-konform?

### Laufzeitstrategie

- Hinweise werden überwiegend offline generiert.
- Ergebnisse werden gecacht und versioniert.
- Jede Ausgabe speichert Modell, Promptversion, Faktenpaket und Prüfstatus.
- Bei OpenAI-Ausfall funktionieren alle Kernmodi weiter.
- Dynamische End-of-Round-Zusammenfassungen erhalten einen deterministischen Template-Fallback.

---

## 19. Musik, Sound und Grafiken

### Musik

- Musik nur unter einem geeigneten kommerziellen Plan erzeugen.
- Account- und Planbeleg archivieren.
- Generierungsdatum dokumentieren.
- Prompt und Exportdatei archivieren.
- austauschbare Audioarchitektur vorsehen.

### Sound Effects

Für jedes Sample speichern:

- ursprüngliche Assetseite
- Titel
- Creator
- Download-Datum
- Lizenzstand
- lokale Dateiprüfsumme
- Bearbeitungen

### Image Generation

Geeignet für:

- The Cartographer
- Kategorie-Key-Art
- Hintergrundgravuren
- Stempel
- Abzeichen
- kosmetische Avatarteile
- Social Share Cards

Nicht als scheinbar dokumentarische Abbildung realer historischer Personen oder Objekte verwenden.

---

## 20. Accounts und Leaderboards

### Build Week

Gastzugang:

- zufällige anonyme Player-ID
- selbst gewählter Display Name
- signiertes HttpOnly-Session-Cookie
- Fortschritt im Browser und serverseitig pseudonymisiert
- kein E-Mail-Zwang vor der ersten Runde

### Public MVP

- Magic Link oder Passkey
- Gastfortschritt nach Registrierung übernehmen
- keine selbst verwalteten Passwörter in der ersten Version
- optional später Social Login

### Leaderboards

- Daily Global
- Daily Friends
- Weekly Category
- Multiplayer Room
- Personal Best
- No-Hint
- Exact Route

Ranked Leaderboards verwenden nur:

- offizielle Daily Rounds
- veröffentlichte Graph-Builds
- unveränderte Regeln
- servervalidierte Sessions

---

## 21. Analytics

### Produkt-Events

```text
round_started
relation_group_opened
relation_seen
move_made
back_used
hint_used
guess_submitted
round_completed
round_abandoned
recap_opened
quiz_answered
rematch_started
room_created
room_joined
room_started
reconnected
image_missing
data_reported
```

### Kernmetriken

#### Activation

- Anteil der Nutzer, die ihre erste Runde abschließen
- Zeit bis zum ersten Zug
- Abbruch vor dem ersten Zug

#### Spielqualität

- Abschlussrate nach Kategorie und Schwierigkeit
- Median von `actual_moves - optimal_moves`
- Hint-Nutzung
- Sackgassenrate
- Back-Nutzung
- häufigste problematische Knoten
- rundenspezifische Fehlermeldungen

#### Retention

- zweite Runde in derselben Session
- Daily Return
- Streak
- D1- und D7-Rückkehr
- Multiplayer-Lobby zu gestartetem Rennen

#### Lernen

- Recap geöffnet
- Quiz abgeschlossen
- Quizgenauigkeit
- Quellenansicht geöffnet
- nach der Runde neu entdeckte Kategorien

Für den Anfang reicht eine eigene append-only `analytics_event`-Tabelle mit aggregierten Materialized Views.

---

## 22. Docker- und VPS-Deployment

### Compose-Services

```text
caddy
api
worker
postgres
valkey
```

Der Svelte-Build wird in einem Multi-Stage-Build erzeugt und in das Caddy-Image kopiert. Ein separater Node-Produktionscontainer ist nicht notwendig.

### Caddy

Caddy übernimmt:

- TLS
- HTTP → HTTPS
- statische Svelte-Dateien
- SPA-Fallback
- Reverse Proxy zu FastAPI
- WebSocket-Upgrade
- Security Header
- Kompression

### Routing

```text
/                  → static Svelte client
/api/*             → FastAPI
/api/v1/ws/*       → FastAPI WebSocket
/assets/*          → local licensed asset store
/health/*          → FastAPI health endpoints
```

Alles bleibt same-origin.

### Persistente Volumes

```text
postgres_data
valkey_data
graph_builds
licensed_assets
caddy_data
caddy_config
```

PostgreSQL und Valkey erhalten keine öffentlich freigegebenen Ports.

### Health Checks

```text
/health/live
/health/ready
/health/graph
```

`/health/ready` prüft:

- PostgreSQL erreichbar
- Valkey erreichbar
- Graph-Manifest geladen
- erwarteter Graph-Hash
- Migrationen aktuell

### VPS-Größe

Startziel:

```text
4 vCPU
8 GB RAM
120–160 GB NVMe
EU region
```

Für eine größere öffentliche Beta:

```text
8 vCPU
16 GB RAM
larger NVMe or external object storage
```

Die vollständige Dump-Verarbeitung sollte nicht auf dem kleinen Produktions-VPS erfolgen.

### Deploymentprozess

1. Tests und Typechecks
2. Web- und API-Image bauen
3. Images mit Commit-SHA taggen
4. in eine Container Registry pushen
5. VPS zieht neue Images
6. Alembic-Migration als One-off-Job
7. neuer Graph-Build wird geprüft
8. Compose-Services werden kontrolliert neu gestartet
9. Health Check
10. vorherige Version für Rollback behalten

### Backups

- nächtlicher verschlüsselter PostgreSQL-Dump
- Assets und Graph-Manifeste extern sichern
- mindestens ein externes S3-kompatibles Ziel
- Rotation: täglich, wöchentlich, monatlich
- monatlicher Restore-Test
- Valkey ist nicht die einzige Quelle dauerhafter Daten

---

## 23. Repository-Struktur

```text
relink/
├─ apps/
│  └─ web/
├─ services/
│  ├─ api/
│  └─ pipeline/
├─ packages/
│  └─ design-tokens/
├─ generated/
│  └─ api-client/
├─ data/
│  ├─ manifests/
│  ├─ relation-registry/
│  └─ seed-packs/
├─ infra/
│  ├─ compose/
│  ├─ caddy/
│  └─ scripts/
├─ tests/
│  ├─ e2e/
│  ├─ load/
│  └─ data-quality/
├─ docker-compose.yml
├─ justfile
└─ README.md
```

Der TypeScript-API-Client wird aus FastAPIs OpenAPI-Schema generiert.

---

## 24. Tests und Quality Gates

### Backend

- Unit Tests für Scoring
- Unit Tests für Moves und Back
- Property Tests für Rundenerreichbarkeit
- Replay-Test aus Eventlog
- Hint-Kosten
- Idempotenz
- Race-Finish
- Reconnect
- abgelaufene Räume
- ungültige Graph-Version

### Datenqualität

Jeder publizierte Build muss garantieren:

- jede spielbare Entität besitzt ein englisches Label
- jede Kante referenziert existierende Knoten
- jede Beziehung besitzt eine verständliche Bezeichnung
- jedes Medium besitzt Lizenz und Quelle
- jede Runde ist erreichbar
- gespeicherte optimale Distanz ist reproduzierbar
- Start und Ziel sind nicht identisch
- blockierte Knoten liegen auf keiner erforderlichen Route
- Hint-Brückenknoten sind tatsächlich gültig
- alle Daily Rounds wurden redaktionell freigegeben

### Frontend

- Komponenten-Tests
- Playwright auf Mobile und Desktop
- Tastaturnavigation
- Fokuszustände
- Screenreader-Labels
- Reduced Motion
- lange englische Labels
- fehlende Bilder
- langsame Verbindung
- verlorener WebSocket
- visuelle Regression

### Lasttests

Erstes Ziel:

- 100 gleichzeitige Räume
- vier Spieler pro Raum
- p95 Move-Validierung unter 150 ms im Ziel-VPS-Umfeld
- Reconnect innerhalb weniger Sekunden
- kein externer Datenzugriff während eines Rennens

---

## 25. Content Safety

Der MVP benötigt:

- allowlisted entity types
- blocklisted QIDs
- `content_rating`
- manuelles Review für Start- und Zielknoten
- strengere Bildprüfung als Textprüfung
- keine expliziten Commons-Bilder
- keine sensitiven Attribute lebender Personen
- Report-Button für falsche oder unangemessene Inhalte
- sofortige serverseitige Deaktivierung einzelner Knoten, Kanten oder Assets

Zwischenknoten ohne geprüftes Bild erhalten eine grafische Kategorie-Repräsentation.

---

## 26. Build-Week-Plan

### Tag 1 – Fundament

#### Produkt

- endgültige Kernregeln
- Scoring v1
- vier Kategorien
- 12–20 Beziehungstypen
- Hint-Definitionen
- visuelles Art-Direction-Sheet

#### Daten

- Wikidata Seed Pack
- erste 2.000–3.000 Entitäten
- Relation Registry
- Import- und Normalisierungsschema
- 20 manuell geprüfte Testrunden

#### Technik

- Monorepo
- Docker Compose
- FastAPI-Grundstruktur
- Svelte-Grundstruktur
- PostgreSQL, Valkey und Caddy

### Tag 2 – Graph und Game Engine

- Graph-Pipeline
- Hub-Pruning
- kompakter Adjazenz-Build
- BFS-Distanzen
- Rundengenerator
- Session State Machine
- Move-Validierung
- Back-Mechanik
- Scoring
- REST-Endpunkte
- 75+ Rundenkandidaten

### Tag 3 – Spieloberfläche

- Desktop- und Mobile-Game-Screen
- Entity Stage
- Relation Portals
- Route Ribbon
- Source Drawer
- Hint UI
- Ergebnisansicht
- responsive Verhalten
- Tastaturnavigation
- erste Audio- und Motion-Pässe

### Tag 4 – Multiplayer

- Räume und Join-Codes
- WebSocket-Protokoll
- Ready-State
- Countdown
- serverseitiger Race-Start
- Live-Fortschritt
- Finish-Reihenfolge
- Reconnect
- Valkey Stream
- Lobby- und Result-Screen

### Tag 5 – AI, Polish und Deployment

- Structured-Output-Hintpipeline
- Cartographer-Texte
- originale Maskottchen- und Kategorieillustrationen
- Daily Round
- Daily Leaderboard
- visuelle QA
- Daten- und Lizenzprüfung
- Produktions-Dockerfiles
- VPS-Deployment
- Backup-Skript
- Demo-Flow

---

## 27. Definition of Done für die Build Week

Die Build-Week-Version ist fertig, wenn:

- English-only vollständig funktioniert
- mindestens vier Kategorien vorhanden sind
- mindestens 100 spielbare Runden existieren
- jede Runde serverseitig validiert ist
- optimale Distanzen bekannt sind
- Back als Zug zählt
- drei Hint-Arten funktionieren
- Solo Route Race funktioniert
- zwei bis vier Spieler live spielen können
- Reconnect funktioniert
- ein Daily Leaderboard existiert
- Start- und Zielmedien lizenziert und attribuiert sind
- Desktop und Mobile visuell konsistent sind
- das Spiel ohne externe Wissens-API während einer Runde funktioniert
- ein frischer VPS über Docker Compose reproduzierbar deployt werden kann

---

## 28. Nicht Teil der Build Week

- vollständige Nutzeraccounts
- Character Builder
- kosmetischer Shop
- Country-Interest-Modus
- OpenAlex-, GBIF- oder MusicBrainz-Import
- freie nutzergenerierte Runden
- globaler Atlas mit allen Entitäten
- mehrere Quiztypen
- umfangreiches Achievement-System
- komplexe Freundeslisten
- Chat
- Tournament Brackets
- native Apps
- Kubernetes
- Neo4j
- Celery
- GraphQL
- Live-SPARQL
- unkontrollierte KI-Hinweise
- versteckte Münzen im Content

---

## 29. Roadmap nach der Build Week

### Phase 1 – Public MVP, Wochen 1–2

- Graph-Builds vollständig versionieren
- Quellen- und Lizenzregister
- Admin-Review
- 500–1.000 Runden
- Datenreporting
- Content-Safety-Filter
- stabiler Reconnect
- Lasttests
- Backups und Monitoring

### Phase 2 – Wochen 3–4

- Hidden Target
- Exact Route
- Account-Verknüpfung
- Daily Streaks
- private Friend Leaderboards
- bessere Anti-Cheat-Heuristiken
- PWA-Installation
- Share Cards

### Phase 3 – Wochen 5–6

- Abschlussquiz
- Image Match
- Met- oder Smithsonian-Culture-World
- persönliche Discovery Map
- Cartographer Progression
- Analytics-Auswertung
- Closed Beta

### Phase 4 – später

- GBIF Nature World
- MusicBrainz Music World
- OpenAlex Research World
- Country-Interest-Daily
- Character Builder
- saisonale Challenges
- Creator Tools
- Community-Runden
- Turniere

---

## 30. Endgültige Architekturentscheidungen

| Bereich | Entscheidung |
|---|---|
| Produkt | typisierter Open-Knowledge-Graph statt Artikelbrowser |
| Arbeitstitel | Relink |
| MVP-Daten | Wikidata + streng gefiltertes Commons |
| spätere Welten | Met, Smithsonian, GBIF, MusicBrainz, OpenAlex |
| Frontend | Svelte 5 + TypeScript + Vite |
| Styling | eigenes CSS-System, keine fertige visuelle UI-Bibliothek |
| UI-Primitives | Bits UI |
| Graphvisualisierung | Sigma.js nur für Reveal und Atlas |
| Backend | FastAPI |
| Persistenz | PostgreSQL |
| Echtzeit | WebSockets + Valkey |
| Graphberechnung | Polars, Parquet, rustworkx |
| Runtime-Graph | versioniertes, kompaktes Read-only-Artefakt |
| Reverse Proxy | Caddy |
| Deployment | Docker Compose auf VPS |
| AI | offline für geprüfte Hinweise, Recaps und Originalgrafiken |
| Runtime-LLM | nicht erforderlich |
| kostenpflichtige Runtime-APIs | nicht erforderlich |
| Nicht verwenden | Live-SPARQL, Neo4j, Next.js, Tailwind/Shadcn, KI als Wahrheitsquelle |
| Build-Week-Scope | Solo, Daily, Live Race, 100 geprüfte Runden |

Der erste produktive Meilenstein ist damit eindeutig:

> **Ein lokal gebauter Wikidata-Graph mit 20 guten Beziehungstypen, 100 validierten Runden und einer visuell unverwechselbaren Svelte-Spieloberfläche, die vollständig über FastAPI und Docker betrieben wird.**

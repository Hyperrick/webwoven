from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FixtureEntitySpec:
    label: str
    description: str
    entity_type: str


@dataclass(frozen=True, slots=True)
class FixtureFactSpec:
    source_index: int
    target_index: int
    relation_key: str
    statement: str


@dataclass(frozen=True, slots=True)
class FixtureStory:
    category: str
    entities: tuple[FixtureEntitySpec, ...]
    facts: tuple[FixtureFactSpec, ...]


def _entity(label: str, role: str, detail: str) -> FixtureEntitySpec:
    return FixtureEntitySpec(
        label=label,
        description=f"Fictional fixture {role} {detail}",
        entity_type=f"fictional_{role.replace(' ', '_')}",
    )


def _fact(
    source_index: int,
    target_index: int,
    relation_key: str,
    statement: str,
) -> FixtureFactSpec:
    return FixtureFactSpec(source_index, target_index, relation_key, statement)


RING_RELATIONS = (
    "P361",
    "P131",
    "P276",
    "P170",
    "P138",
    "P463",
    "P108",
    "P800",
    "P737",
    "P166",
    "P50",
    "P61",
)


def _ring_story(category: str, subject: str, labels: tuple[str, ...]) -> FixtureStory:
    if len(labels) != 12:
        raise ValueError("fixture rings require exactly twelve labels")
    entities = tuple(
        _entity(label, f"{subject} subject", f"in the invented {subject} atlas.")
        for label in labels
    )
    facts = tuple(
        _fact(
            index,
            index % len(labels) + 1,
            RING_RELATIONS[index - 1],
            f"{labels[index - 1]} connects to {labels[index % len(labels)]} "
            f"in the fictional {subject} atlas.",
        )
        for index in range(1, len(labels) + 1)
    )
    return FixtureStory(category=category, entities=entities, facts=facts)


HISTORY_PEOPLE = FixtureStory(
    category="people",
    entities=(
        _entity("Elian Voss", "navigator", "who charted the invented Northglass coast."),
        _entity("Gannet Hollow", "harbor town", "where the Northglass story begins."),
        _entity("Lantern School", "academy", "for navigators and local historians."),
        _entity("Nera Sol", "historian", "who reconstructed early coastal journeys."),
        _entity("Tideglass Atlas", "book", "about the imagined Northglass coast."),
        _entity("Ada Tideglass", "patron", "who funded public map rooms."),
        _entity("Wayfinder Circle", "learned society", "for mapmakers and archivists."),
        _entity("Rowan Sable", "archivist", "who catalogued the Circle's expeditions."),
        _entity("Hale Medal", "award", "for careful historical fieldwork."),
        _entity("Esten Hale", "explorer", "who organized a celebrated survey."),
        _entity("Meridian Expedition", "expedition", "across the invented Northglass coast."),
        _entity("Northglass Society", "research society", "that coordinates coastal studies."),
    ),
    facts=(
        _fact(1, 2, "P19", "Elian Voss was born in Gannet Hollow."),
        _fact(3, 2, "P131", "Lantern School is located in Gannet Hollow."),
        _fact(4, 3, "P69", "Nera Sol was educated at Lantern School."),
        _fact(4, 5, "P800", "Nera Sol's notable work is the Tideglass Atlas."),
        _fact(5, 6, "P138", "The Tideglass Atlas was named after Ada Tideglass."),
        _fact(6, 7, "P463", "Ada Tideglass was a member of the Wayfinder Circle."),
        _fact(8, 7, "P108", "Rowan Sable worked for the Wayfinder Circle."),
        _fact(8, 9, "P166", "Rowan Sable received the Hale Medal."),
        _fact(9, 10, "P138", "The Hale Medal was named after Esten Hale."),
        _fact(10, 11, "P800", "Esten Hale's notable work is the Meridian Expedition."),
        _fact(11, 12, "P361", "The Meridian Expedition is part of Northglass Society research."),
        _fact(1, 12, "P463", "Elian Voss was a member of the Northglass Society."),
    ),
)


NATURE_SCIENCE = FixtureStory(
    category="nature_life",
    entities=(
        _entity("Saffron glider", "moth", "with ochre wings in the Mosslight wetlands."),
        _entity("Glider moths", "moth genus", "containing the imagined Saffron glider."),
        _entity("Amberwing family", "moth family", "containing several invented glider moths."),
        _entity("Tavi Morrow", "ecologist", "who described the Amberwing family."),
        _entity("Bracken Field Station", "field station", "for wetland research."),
        _entity("Mosslight Preserve", "nature preserve", "protecting fictional reed wetlands."),
        _entity("Fenmere Republic", "country", "containing the imagined Mosslight wetlands."),
        _entity("Fenmere City", "capital city", "of the invented Fenmere Republic."),
        _entity("Prism Observatory", "observatory", "for nocturnal pollinator research."),
        _entity("Celia Rune", "instrument maker", "who studies night-flying insects."),
        _entity("Lumen Lens", "scientific instrument", "for observing moth wing patterns."),
        _entity("Saffron Glider Survey", "research survey", "of fictional wetland pollinators."),
    ),
    facts=(
        _fact(1, 2, "P171", "The Saffron glider's parent taxon is Glider moths."),
        _fact(2, 3, "P171", "The parent taxon of Glider moths is the Amberwing family."),
        _fact(3, 4, "P61", "The Amberwing family was described by Tavi Morrow."),
        _fact(4, 5, "P108", "Tavi Morrow worked for Bracken Field Station."),
        _fact(5, 6, "P131", "Bracken Field Station is located in Mosslight Preserve."),
        _fact(6, 7, "P17", "Mosslight Preserve is in the Fenmere Republic."),
        _fact(7, 8, "P36", "The capital of the Fenmere Republic is Fenmere City."),
        _fact(9, 8, "P131", "Prism Observatory is located in Fenmere City."),
        _fact(10, 9, "P108", "Celia Rune worked for Prism Observatory."),
        _fact(11, 10, "P61", "The Lumen Lens was invented by Celia Rune."),
        _fact(11, 12, "P361", "The Lumen Lens is part of the Saffron Glider Survey toolkit."),
        _fact(12, 1, "P138", "The Saffron Glider Survey was named after the Saffron glider."),
    ),
)


ARTS_CULTURE = FixtureStory(
    category="art_design",
    entities=(
        _entity("Juniper Vale", "singer", "known for intimate stage performances."),
        _entity("Velvet Current", "song", "with a slow, tidal refrain."),
        _entity("Driftglass Suite", "music collection", "built around coastal soundscapes."),
        _entity("Sera Loom", "composer", "who writes for small theatre ensembles."),
        _entity("Paper Moon Libretto", "libretto", "for an invented chamber opera."),
        _entity("Tobin Rill", "writer", "of plays and musical texts."),
        _entity("Orra Venn", "film director", "inspired by experimental theatre."),
        _entity("Ochre Door", "film", "adapted from an imaginary stage work."),
        _entity("Kei Moss", "actor", "who performed in the Ochre Door ensemble."),
        _entity("Rhea Dune", "actor", "whose physical theatre shaped Kei Moss's work."),
        _entity("Hearthline Ensemble", "theatre company", "for collaborative performances."),
        _entity("Dawn Stage", "theatre", "hosting new fictional works."),
    ),
    facts=(
        _fact(2, 1, "P175", "Velvet Current was performed by Juniper Vale."),
        _fact(2, 3, "P361", "Velvet Current is part of the Driftglass Suite."),
        _fact(3, 4, "P170", "The Driftglass Suite was created by Sera Loom."),
        _fact(4, 5, "P800", "Sera Loom's notable work is the Paper Moon Libretto."),
        _fact(5, 6, "P50", "The Paper Moon Libretto was written by Tobin Rill."),
        _fact(6, 7, "P737", "Tobin Rill was influenced by Orra Venn's stage experiments."),
        _fact(8, 7, "P57", "Ochre Door was directed by Orra Venn."),
        _fact(8, 9, "P161", "Ochre Door features cast member Kei Moss."),
        _fact(9, 10, "P737", "Kei Moss was influenced by Rhea Dune."),
        _fact(10, 11, "P463", "Rhea Dune is a member of the Hearthline Ensemble."),
        _fact(11, 12, "P276", "The Hearthline Ensemble is based at Dawn Stage."),
        _fact(1, 12, "P108", "Juniper Vale worked for Dawn Stage."),
    ),
)


PLACES = FixtureStory(
    category="places_architecture",
    entities=(
        _entity("Kestrel Bay", "harbor", "on the invented Avenmark coast."),
        _entity("South Kestrel District", "district", "surrounding the fictional harbor."),
        _entity("Republic of Avenmark", "country", "in this synthetic coastal atlas."),
        _entity("Calder City", "capital city", "of the invented Republic of Avenmark."),
        _entity("Lantern Ward", "city ward", "known for bookbinders and map printers."),
        _entity("Glasshouse Museum", "museum", "devoted to imaginary harbor histories."),
        _entity("Atlas of Small Harbors", "book", "displayed in the Glasshouse Museum."),
        _entity("Wren Ilex", "cartographer", "who drew the Atlas of Small Harbors."),
        _entity("Ilex Quay", "quay", "named for the fictional cartographer Wren Ilex."),
        _entity("Ferrymakers Hall", "guild hall", "near the edge of Ilex Quay."),
        _entity("Saltline Festival", "festival", "celebrating fictional ferry traditions."),
        _entity("Tideway Pavilion", "pavilion", "overlooking the invented Kestrel Bay."),
    ),
    facts=(
        _fact(1, 2, "P131", "Kestrel Bay is located in South Kestrel District."),
        _fact(2, 3, "P17", "South Kestrel District is in the Republic of Avenmark."),
        _fact(3, 4, "P36", "The capital of the Republic of Avenmark is Calder City."),
        _fact(5, 4, "P131", "Lantern Ward is located in Calder City."),
        _fact(6, 5, "P131", "Glasshouse Museum is located in Lantern Ward."),
        _fact(7, 6, "P276", "The Atlas of Small Harbors is displayed at Glasshouse Museum."),
        _fact(7, 8, "P170", "The Atlas of Small Harbors was created by Wren Ilex."),
        _fact(9, 8, "P138", "Ilex Quay was named after Wren Ilex."),
        _fact(10, 9, "P131", "Ferrymakers Hall is located on Ilex Quay."),
        _fact(11, 10, "P276", "The Saltline Festival is held at Ferrymakers Hall."),
        _fact(11, 12, "P276", "The Saltline Festival also uses Tideway Pavilion."),
        _fact(12, 1, "P131", "Tideway Pavilion is located at Kestrel Bay."),
    ),
)


HISTORY_SOCIETY = _ring_story(
    "history_society",
    "history and society",
    (
        "Copperleaf Assembly",
        "Harbor Charter",
        "Lantern Census",
        "Common Table Accord",
        "Northglass Archive",
        "Meridian March",
        "Founders' Ledger",
        "Sable Reform",
        "Tideway Union",
        "Ochre Proclamation",
        "Public Map Room",
        "New Coast Congress",
    ),
)

SCIENCE_TECHNOLOGY = _ring_story(
    "science_technology",
    "science and technology",
    (
        "Lumen Engine",
        "Prism Relay",
        "Copper Coil Array",
        "Morrow Observatory",
        "Glasswing Sensor",
        "Northglass Computer",
        "Tideclock Network",
        "Saffron Laboratory",
        "Meridian Telescope",
        "Fieldnote Database",
        "Bracken Robot",
        "Atlas Signal",
    ),
)

LITERATURE_LANGUAGE = _ring_story(
    "literature_language",
    "literature and language",
    (
        "The Saltline Chronicle",
        "Mira Quill",
        "Northglass Lexicon",
        "The Paper Compass",
        "Gannet Press",
        "Lantern Dialect",
        "Tobin Quill",
        "The Quiet Estuary",
        "Harbor Readers Circle",
        "Blank Margin Prize",
        "Tideglass Translation",
        "Dawn Library",
    ),
)

MUSIC_PERFORMANCE = _ring_story(
    "music_performance",
    "music and performance",
    (
        "Juniper Reed",
        "Velvet Estuary",
        "Driftglass Concerto",
        "Sera Chime",
        "Dawn Concert Hall",
        "Hearthline Orchestra",
        "Copper Reed",
        "Mosslight Chorus",
        "Northglass Ballet",
        "Lantern Concerto",
        "Tideway Opera",
        "Paper Moon Festival",
    ),
)

FILM_MEDIA = _ring_story(
    "film_media",
    "film and media",
    (
        "Ochre Window",
        "Orra Fen",
        "Kestrel Camera",
        "The Long Crossing",
        "Harborlight Studio",
        "Rhea Vale",
        "Field Reel Archive",
        "Mossframe Animation",
        "Lantern Broadcast",
        "Northglass Documentary",
        "Silver Route Award",
        "Tideway Cinema",
    ),
)

SPORTS_GAMES = _ring_story(
    "sports_games",
    "sports and games",
    (
        "Avenmark Games",
        "Kestrel Eleven",
        "Northglass Court",
        "Tideway Regatta",
        "Copper Knight Club",
        "Lantern Marathon",
        "Mosslight Arena",
        "Sable Racket Cup",
        "Harbor Board League",
        "Meridian Wheel Race",
        "Bracken Field Team",
        "Atlas Games Medal",
    ),
)


SMOKE_STORIES = (
    HISTORY_PEOPLE,
    HISTORY_SOCIETY,
    SCIENCE_TECHNOLOGY,
    NATURE_SCIENCE,
    PLACES,
    ARTS_CULTURE,
    LITERATURE_LANGUAGE,
    MUSIC_PERFORMANCE,
    FILM_MEDIA,
    SPORTS_GAMES,
)

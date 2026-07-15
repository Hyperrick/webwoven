import type { EntitySummary, RelationGroup } from "../api/types";

interface DemoEdge {
  propertyId: string;
  label: string;
  glyph: RelationGroup["glyph"];
  target: string;
  statement: string;
}

export const DEMO_ENTITIES: Record<string, EntitySummary> = {
  Q421: {
    qid: "Q421",
    label: "Blue whale",
    description: "The largest animal known to have existed",
    category: "nature_science",
    fact: "Its low-frequency calls can travel across entire ocean basins.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q421",
  },
  Q98: {
    qid: "Q98",
    label: "Pacific Ocean",
    description: "The largest and deepest ocean on Earth",
    category: "places",
    fact: "It covers more area than all land on Earth combined.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q98",
  },
  Q17: {
    qid: "Q17",
    label: "Japan",
    description: "Island country in East Asia",
    category: "places",
    fact: "Japan stretches along the western edge of the Pacific Ocean.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q17",
  },
  Q5586: {
    qid: "Q5586",
    label: "Hokusai",
    description: "Japanese artist of the Edo period",
    category: "arts_culture",
    fact: "He used more than thirty names during his long career.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q5586",
  },
  Q149116: {
    qid: "Q149116",
    label: "The Great Wave off Kanagawa",
    description:
      "Woodblock print from Hokusai’s Thirty-six Views of Mount Fuji",
    category: "arts_culture",
    fact: "The print made Prussian blue famous across nineteenth-century Japan.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q149116",
  },
  Q219127: {
    qid: "Q219127",
    label: "Endangered species",
    description: "Species at serious risk of extinction",
    category: "nature_science",
    fact: "Conservation status is assessed using evidence about range and population.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q219127",
  },
  Q150830: {
    qid: "Q150830",
    label: "Balaenoptera",
    description: "Genus of rorqual whales",
    category: "nature_science",
    fact: "The genus includes blue, fin, sei and minke whales.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q150830",
  },
  Q99: {
    qid: "Q99",
    label: "California",
    description: "State on the western coast of the United States",
    category: "places",
    fact: "Its coast meets the eastern edge of the Pacific Ocean.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q99",
  },
  Q159183: {
    qid: "Q159183",
    label: "Mariana Trench",
    description: "Deepest oceanic trench on Earth",
    category: "nature_science",
    fact: "Its deepest surveyed point is Challenger Deep.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q159183",
  },
  Q1490: {
    qid: "Q1490",
    label: "Tokyo",
    description: "Capital and most populous city of Japan",
    category: "places",
    fact: "Tokyo began as the fishing village of Edo.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q1490",
  },
  Q39231: {
    qid: "Q39231",
    label: "Mount Fuji",
    description: "Volcano and highest mountain in Japan",
    category: "nature_science",
    fact: "The mountain appears throughout Hokusai’s print series.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q39231",
  },
  Q200759: {
    qid: "Q200759",
    label: "Edo period",
    description: "Period of Japanese history from 1603 to 1868",
    category: "history_people",
    fact: "Urban publishing helped woodblock prints reach a broad audience.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q200759",
  },
  Q209772: {
    qid: "Q209772",
    label: "Thirty-six Views of Mount Fuji",
    description: "Landscape print series by Hokusai",
    category: "arts_culture",
    fact: "Popular demand led to ten additional designs beyond the original thirty-six.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q209772",
  },
  Q6373: {
    qid: "Q6373",
    label: "British Museum",
    description: "Public museum of human history, art and culture",
    category: "arts_culture",
    fact: "Its collection includes impressions of Hokusai’s Great Wave.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q6373",
  },
  Q84: {
    qid: "Q84",
    label: "London",
    description: "Capital and largest city of the United Kingdom",
    category: "places",
    fact: "London’s museums hold collections drawn from across the world.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q84",
  },
  Q21: {
    qid: "Q21",
    label: "England",
    description: "Country that is part of the United Kingdom",
    category: "places",
    fact: "England contains London, the capital of the United Kingdom.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q21",
  },
  Q145: {
    qid: "Q145",
    label: "United Kingdom",
    description: "Country in northwestern Europe",
    category: "places",
    fact: "The United Kingdom comprises England, Scotland, Wales and Northern Ireland.",
    source_kind: "wikidata",
    source_url: "https://www.wikidata.org/wiki/Q145",
  },
};

const DEMO_EDGES: Record<string, DemoEdge[]> = {
  Q421: [
    {
      propertyId: "P276",
      label: "found in",
      glyph: "place",
      target: "Q98",
      statement: "Blue whales migrate through the Pacific Ocean.",
    },
    {
      propertyId: "P171",
      label: "parent taxon",
      glyph: "nature",
      target: "Q150830",
      statement: "The blue whale belongs to the genus Balaenoptera.",
    },
  ],
  Q98: [
    {
      propertyId: "P361",
      label: "coastal place",
      glyph: "place",
      target: "Q17",
      statement: "Japan lies along the western Pacific Ocean.",
    },
    {
      propertyId: "P361",
      label: "coastal place",
      glyph: "place",
      target: "Q99",
      statement: "California borders the eastern Pacific Ocean.",
    },
    {
      propertyId: "P361",
      label: "contains",
      glyph: "part",
      target: "Q159183",
      statement: "The Mariana Trench lies in the western Pacific Ocean.",
    },
  ],
  Q17: [
    {
      propertyId: "P36",
      label: "capital",
      glyph: "place",
      target: "Q1490",
      statement: "Tokyo is the capital of Japan.",
    },
    {
      propertyId: "P276",
      label: "located in",
      glyph: "place",
      target: "Q39231",
      statement: "Mount Fuji is located on Honshu in Japan.",
    },
  ],
  Q5586: [
    {
      propertyId: "P800",
      label: "notable work",
      glyph: "work",
      target: "Q149116",
      statement: "Hokusai created The Great Wave off Kanagawa.",
    },
    {
      propertyId: "P800",
      label: "notable work",
      glyph: "work",
      target: "Q209772",
      statement: "Hokusai created Thirty-six Views of Mount Fuji.",
    },
  ],
  Q149116: [
    {
      propertyId: "P276",
      label: "held by",
      glyph: "place",
      target: "Q6373",
      statement:
        "The British Museum holds an impression of The Great Wave off Kanagawa.",
    },
    {
      propertyId: "P361",
      label: "part of",
      glyph: "part",
      target: "Q209772",
      statement: "The Great Wave is part of Thirty-six Views of Mount Fuji.",
    },
  ],
  Q39231: [
    {
      propertyId: "P361",
      label: "depicted in",
      glyph: "work",
      target: "Q209772",
      statement:
        "Mount Fuji is the recurring subject of Hokusai’s print series.",
    },
  ],
  Q209772: [
    {
      propertyId: "P170",
      label: "created by",
      glyph: "work",
      target: "Q5586",
      statement: "Hokusai created Thirty-six Views of Mount Fuji.",
    },
  ],
  Q6373: [
    {
      propertyId: "P131",
      label: "located in",
      glyph: "place",
      target: "Q84",
      statement: "The British Museum is located in London.",
    },
  ],
  Q84: [
    {
      propertyId: "P17",
      label: "country",
      glyph: "place",
      target: "Q145",
      statement: "London is the capital of the United Kingdom.",
    },
    {
      propertyId: "P131",
      label: "located in",
      glyph: "place",
      target: "Q21",
      statement: "London is located in England.",
    },
  ],
};

function token(source: string, edge: DemoEdge): string {
  return `demo:${source}:${edge.propertyId}:${edge.target}`;
}

export function relationGroupsFor(
  qid: string,
  excludedTargetQids: ReadonlySet<string> = new Set(),
): RelationGroup[] {
  const edges = (DEMO_EDGES[qid] ?? []).filter(
    (edge) => !excludedTargetQids.has(edge.target),
  );
  const grouped = new Map<string, RelationGroup>();

  for (const edge of edges) {
    const key = `${edge.propertyId}:${edge.label}`;
    const existing = grouped.get(key);
    const item = {
      edge_token: token(qid, edge),
      target: DEMO_ENTITIES[edge.target],
      statement: edge.statement,
    };
    if (existing) {
      existing.edges.push(item);
    } else {
      grouped.set(key, {
        group_id: `${edge.propertyId}-outgoing-${encodeURIComponent(edge.label)}`,
        property_id: edge.propertyId,
        label: edge.label,
        direction: "outgoing",
        glyph: edge.glyph,
        edges: [item],
      });
    }
  }

  return [...grouped.values()];
}

export function demoDistanceToTarget(
  startQid: string,
  targetQid: string,
  blockedQids: ReadonlySet<string> = new Set(),
): number | null {
  if (startQid === targetQid) return 0;
  const visited = new Set(blockedQids);
  visited.add(startQid);
  const queue: Array<{ qid: string; distance: number }> = [
    { qid: startQid, distance: 0 },
  ];
  for (let index = 0; index < queue.length; index += 1) {
    const current = queue[index];
    for (const edge of DEMO_EDGES[current.qid] ?? []) {
      if (visited.has(edge.target)) continue;
      if (edge.target === targetQid) return current.distance + 1;
      visited.add(edge.target);
      queue.push({ qid: edge.target, distance: current.distance + 1 });
    }
  }
  return null;
}

export function resolveDemoEdge(
  edgeToken: string,
): { source: string; target: string; statement: string } | null {
  const [, source, propertyId, target] = edgeToken.split(":");
  const edge = (DEMO_EDGES[source] ?? []).find(
    (candidate) =>
      candidate.propertyId === propertyId && candidate.target === target,
  );
  return edge ? { source, target, statement: edge.statement } : null;
}

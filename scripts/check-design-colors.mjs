import { readFile, readdir } from "node:fs/promises";
import { extname, join } from "node:path";

const roots = ["apps/web/src", "packages/design-tokens/src"];
const paletteFiles = new Set([
  "packages/design-tokens/src/tokens.css",
  "packages/design-tokens/src/tokens.ts",
]);
const lockedPalette = new Set([
  "#f3ebdd",
  "#16211d",
  "#c84a32",
  "#3f6b54",
  "#b68532",
  "#2d6574",
  "#6e6b61",
]);
const colorPattern =
  /#[0-9a-f]{3,8}\b|\brgba?\(|\bhsla?\(|(?:linear|radial|conic)-gradient/gi;
const forbiddenPurple = /\b(purple|violet|magenta|indigo)\b/i;
const paletteOccurrences = new Map([...paletteFiles].map((file) => [file, []]));

async function filesUnder(root) {
  const entries = await readdir(root, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) files.push(...(await filesUnder(path)));
    if (entry.isFile() && [".css", ".svelte", ".ts"].includes(extname(path)))
      files.push(path);
  }
  return files;
}

const violations = [];
for (const root of roots) {
  for (const file of await filesUnder(root)) {
    const source = await readFile(file, "utf8");
    if (forbiddenPurple.test(source))
      violations.push(`${file}: forbidden purple-family term`);

    for (const match of source.matchAll(colorPattern)) {
      const value = match[0].toLowerCase();
      const isLockedPaletteDefinition =
        paletteFiles.has(file) && lockedPalette.has(value);
      if (isLockedPaletteDefinition) {
        paletteOccurrences.get(file).push(value);
      } else {
        violations.push(`${file}: disallowed color expression ${match[0]}`);
      }
    }
  }
}

const expectedPalette = [...lockedPalette].sort();
for (const [file, occurrences] of paletteOccurrences) {
  const actualPalette = [...occurrences].sort();
  if (JSON.stringify(actualPalette) !== JSON.stringify(expectedPalette)) {
    violations.push(`${file}: define each locked palette color exactly once`);
  }
}

if (violations.length) {
  process.stderr.write(`${violations.join("\n")}\n`);
  process.exit(1);
}

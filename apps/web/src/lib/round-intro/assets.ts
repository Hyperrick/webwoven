import type { Category } from "../api/types";
import { categoryPresentation } from "../domain/categories";

interface CategoryTheme {
  label: string;
  accent: string;
}

export function categoryTheme(category: Category): CategoryTheme {
  const { label, accent } = categoryPresentation(category);
  return { label, accent };
}

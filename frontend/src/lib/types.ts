export type Domain = "movies" | "news";

export type AlgoKey =
  | "popularity"
  | "content_based"
  | "item_knn"
  | "als"
  | "hybrid"
  | "two_tower";

export const ALGO_KEYS: AlgoKey[] = [
  "popularity",
  "content_based",
  "item_knn",
  "als",
  "hybrid",
  "two_tower",
];

export const ALGO_NAMES: Record<AlgoKey, string> = {
  popularity: "Popularity",
  content_based: "Content-Based",
  item_knn: "Item k-NN",
  als: "ALS (MF)",
  hybrid: "Hybrid",
  two_tower: "Two-Tower NN",
};

export const ALGO_SHORT: Record<AlgoKey, string> = {
  popularity: "Pop",
  content_based: "CB",
  item_knn: "kNN",
  als: "ALS",
  hybrid: "Hyb",
  two_tower: "2T",
};

export const ALGO_TINT: Record<AlgoKey, string> = {
  popularity: "#a3a3a3",
  content_based: "#f59e0b",
  item_knn: "#10b981",
  als: "#6366f1",
  hybrid: "#ec4899",
  two_tower: "#06b6d4",
};

export interface ServiceInfo {
  service: string;
  domains: Domain[];
  loaded: Record<Domain, boolean>;
}

export interface DomainInfo {
  domain: Domain;
  n_users: number;
  n_items: number;
  n_interactions: number;
  algos: AlgoKey[];
}

export interface UserSummary {
  user_id: string | number;
  n_interactions: number;
}

export type ItemId = string | number;

export interface MovieMeta {
  genres?: string[];
  release_date?: string;
  release_year?: number;
  imdb_url?: string;
}

export interface NewsMeta {
  category?: string;
  subcategory?: string;
  abstract?: string;
  url?: string;
}

export type ItemMeta = MovieMeta & NewsMeta & Record<string, unknown>;

export interface Item {
  item_id: ItemId;
  title: string;
  metadata: ItemMeta;
}

export interface ScoredItem extends Item {
  score: number;
}

export interface RecResponse {
  domain: Domain;
  algo: AlgoKey;
  user_id: string | number;
  items: ScoredItem[];
}

export interface CompareResponse {
  domain: Domain;
  user_id: string | number;
  k: number;
  results: Record<string, ScoredItem[]>;
}

export interface MetricReport {
  algo: AlgoKey;
  k: number;
  precision: number;
  recall: number;
  ndcg: number;
  coverage: number;
  diversity: number;
  novelty: number;
  n_users_evaluated: number;
}

export interface EvalResponse {
  domain: Domain;
  k: number;
  n_users: number;
  n_items: number;
  reports: MetricReport[];
}

export type MetricKey =
  | "precision"
  | "recall"
  | "ndcg"
  | "coverage"
  | "diversity"
  | "novelty";

export const METRICS: { key: MetricKey; label: string; description: string; higher: boolean }[] = [
  { key: "precision", label: "Precision@K", description: "Share of recommended items that were relevant.", higher: true },
  { key: "recall", label: "Recall@K", description: "Share of relevant items captured in top-K.", higher: true },
  { key: "ndcg", label: "NDCG@K", description: "Position-weighted ranking quality.", higher: true },
  { key: "coverage", label: "Coverage", description: "Fraction of catalog appearing in any user's recs.", higher: true },
  { key: "diversity", label: "Diversity", description: "1 − mean pairwise Jaccard across reclists.", higher: true },
  { key: "novelty", label: "Novelty", description: "Mean −log2 p(item) — lower-popularity items score higher.", higher: true },
];

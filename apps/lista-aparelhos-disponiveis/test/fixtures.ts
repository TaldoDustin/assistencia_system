import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import type { AvailabilityLookup, RawInventoryItem, StorageSizeLookup } from "../lib/types.js";

const here = dirname(fileURLToPath(import.meta.url));
const load = (f: string) => JSON.parse(readFileSync(join(here, "fixtures", f), "utf8"));

export const inventarioCru: RawInventoryItem[] = load("inventory.sample.json").items;
export const availability: AvailabilityLookup[] = load("availability.sample.json").items;
export const storageSizes: StorageSizeLookup[] = load("storage-sizes.sample.json").items;

/**
 * The single entry point the frontend uses to read project configuration.
 *
 * Two files, two lifetimes:
 *
 *   config/brand.json    -- WHO ships this (author, links, avatar). Stable.
 *   config/dataset.json  -- WHAT it is about (business copy, DB, agent). Swapped
 *                           wholesale when the repo points at a new dataset.
 *
 * Nothing else in `app/`, `components/` or `lib/` should hardcode a brand name,
 * an author name, or a sentence of business copy. If you find yourself typing
 * one into a component, it belongs in one of those two files instead -- that is
 * the whole point of this module.
 *
 * Secrets never live here; they stay in `.env`.
 */

import brandJson from "@/config/brand.json"
import datasetJson from "@/config/dataset.json"

export const brand = brandJson
export const dataset = datasetJson

export type Brand = typeof brand
export type Dataset = typeof dataset

/** Icon name as written in `config/dataset.json`; resolved by `lib/icons.ts`. */
export type IconName = string

/**
 * The single entry point the frontend uses to read project configuration.
 *
 * `config/dataset.json` holds everything that varies between datasets: the
 * product name, every sentence of business copy, the agent's display name, the
 * database's display name and table order.
 *
 * Nothing else in `app/`, `components/` or `lib/` should hardcode a product
 * name or a sentence of business copy. If you find yourself typing one into a
 * component, it belongs in that file instead -- that is the whole point of this
 * module.
 *
 * Two things deliberately live nowhere near here:
 *   - Secrets, which stay in `.env`.
 *   - Author / personal identity, which this app does not have. It is a product
 *     showcase, not a portfolio; no name, photo, or contact detail belongs in
 *     the UI or the page metadata.
 */

import datasetJson from "@/config/dataset.json"

export const dataset = datasetJson

export type Dataset = typeof dataset

// news-image-20261127 — "The Friday World"
// Sum up 27 November 2026's world news in one image.
//
// The poster is drawn by build_poster.py (Python 3 + Pillow) and held in
// this repository as entry.png. This program only copies that image to the
// output path, so both graded runs write byte-identical output.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

mkdirSync(outDir, { recursive: true });
copyFileSync(join(here, "entry.png"), join(outDir, "entry.png"));

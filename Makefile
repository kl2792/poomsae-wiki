# Poomsae Wiki — reproducible pipeline

.PHONY: download download-captions captions transcripts pre-extract extract build deploy clean test techniques

# Full pipeline
all: download transcripts extract build deploy

# Step 1: Download all 21 KKW videos at 720p
download:
	bash scripts/download.sh

# Step 1b: Download auto-captions only (no video re-download)
download-captions:
	bash scripts/download_captions.sh

# Step 2: Generate OCR transcripts from video frames (1fps, full-frame Tesseract)
transcripts:
	python3 scripts/transcript.py

# Step 2b: Parse auto-caption VTT files into structured JSON
captions:
	python3 scripts/parse_captions.py --all

# Step 3a: Deterministic pre-extraction (regex only, no LLM) — anchors technique names
pre-extract: captions
	python3 scripts/pre_extract.py --all

# Step 3: Extract structured JSON from transcripts via LLM, then rebuild technique DB
extract: pre-extract
	python3 scripts/extract.py --all
	$(MAKE) techniques

# Step 3b: Validate extracted JSONs
validate:
	python3 scripts/extract.py --validate

# Step 4: Build Next.js static export
build:
	cd app && npm run build && touch out/.nojekyll

# Step 5: Deploy to GitHub Pages
deploy:
	npx gh-pages -d app/out --dotfiles

# Individual form extraction
extract-%:
	python3 scripts/extract.py $*

# Preview prompt without calling LLM
prompt-%:
	python3 scripts/extract.py --prompt-only $*

# Step 6: Build centralized technique database from per-form JSONs
techniques:
	python3 scripts/build_techniques.py

# Run all tests
test:
	cd app && npx vitest run
	cd scripts && python3 test_parse_captions.py
	cd scripts && python3 test_pre_extract.py
	cd scripts && python3 test_extract.py
	cd scripts && python3 test_build_techniques.py

# Local dev server
dev:
	cd app && npm run dev

clean:
	rm -rf dat/frames dat/ocr dat/transcripts app/out app/.next

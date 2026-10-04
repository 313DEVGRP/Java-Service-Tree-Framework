#!/usr/bin/env bash
# hash-recap-cards.sh
# Generate hashed PDFs for recap cards, create series ZIPs, output mapping JSON
#
# Usage: ./scripts/hash-recap-cards.sh [--dry-run]
# Output: portfolio/public/guides/recap-cards/ + recap-hashes.json (guide root)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
SOURCE_DIR="$ROOT/../claude-code-ultimate-guide-landing/public/cheatsheets/pdf"
PORTFOLIO_DIR="$ROOT/../florian-portfolio/public/guides/recap-cards"
VERSION="v1.0.0"
DRY_RUN=false

[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: Source dir not found: $SOURCE_DIR" >&2
  exit 1
fi

$DRY_RUN || mkdir -p "$PORTFOLIO_DIR"

# Collect all PDFs and compute hashes
declare -a ALL_KEYS
declare -A HASH_MAP  # basename → hashed filename

TECHNIQUE_KEYS=()
METHODOLOGIE_KEYS=()

echo "=== Hashing PDFs ==="
for pdf in "$SOURCE_DIR"/*.pdf; do
  [[ -f "$pdf" ]] || continue
  base=$(basename "$pdf" .pdf)
  series="${base:0:1}"  # t | m | c

  if [[ "$OSTYPE" == "darwin"* ]]; then
    hash=$(md5 -q "$pdf" | cut -c1-12)
  else
    hash=$(md5sum "$pdf" | awk '{print $1}' | cut -c1-12)
  fi

  out_name="${base}.fr.${VERSION}.${hash}.pdf"
  HASH_MAP["$base"]="$out_name"
  ALL_KEYS+=("$base")

  case "$series" in
    t) TECHNIQUE_KEYS+=("$base") ;;
    m) METHODOLOGIE_KEYS+=("$base") ;;
  esac

  echo "  $base → $out_name"
  $DRY_RUN || cp "$pdf" "$PORTFOLIO_DIR/$out_name"
done

echo ""
echo "=== Creating ZIPs ==="

_create_zip() {
  local series_name="$1"
  shift
  local keys=("$@")

  local tmp_dir
  tmp_dir=$(mktemp -d)
  for k in "${keys[@]}"; do
    $DRY_RUN || cp "$PORTFOLIO_DIR/${HASH_MAP[$k]}" "$tmp_dir/"
    $DRY_RUN && echo "  [dry-run] would include ${HASH_MAP[$k]}"
  done

  if $DRY_RUN; then
    echo "  [dry-run] would create recap-cards-${series_name}.fr.${VERSION}.XXXXXXXXXXXX.zip"
    echo "DRYRUN_${series_name^^}"
    return
  fi

  (cd "$tmp_dir" && zip -q "archive.zip" *.pdf)

  if [[ "$OSTYPE" == "darwin"* ]]; then
    zip_hash=$(md5 -q "$tmp_dir/archive.zip" | cut -c1-12)
  else
    zip_hash=$(md5sum "$tmp_dir/archive.zip" | awk '{print $1}' | cut -c1-12)
  fi

  local zip_name="recap-cards-${series_name}.fr.${VERSION}.${zip_hash}.zip"
  cp "$tmp_dir/archive.zip" "$PORTFOLIO_DIR/$zip_name"
  rm -rf "$tmp_dir"
  echo "  ${series_name} ZIP → $zip_name"
  echo "$zip_name"
}

ZIP_T=$(_create_zip "technique" "${TECHNIQUE_KEYS[@]}")
ZIP_M=$(_create_zip "methodologie" "${METHODOLOGIE_KEYS[@]}")

# Last line of _create_zip output is the filename
ZIP_T_NAME=$(echo "$ZIP_T" | tail -1)
ZIP_M_NAME=$(echo "$ZIP_M" | tail -1)

echo ""
echo "=== Generating recap-hashes.json ==="

JSON_FILE="$ROOT/recap-hashes.json"

{
  printf '{\n'
  printf '  "_zips": {\n'
  printf '    "technique": "%s",\n' "$ZIP_T_NAME"
  printf '    "methodologie": "%s"\n' "$ZIP_M_NAME"
  printf '  },\n'
  printf '  "_cards": {\n'
  # Sort keys for deterministic output
  mapfile -t SORTED_KEYS < <(printf '%s\n' "${ALL_KEYS[@]}" | sort)
  last_idx=$(( ${#SORTED_KEYS[@]} - 1 ))
  for i in "${!SORTED_KEYS[@]}"; do
    k="${SORTED_KEYS[$i]}"
    if [[ $i -eq $last_idx ]]; then
      printf '    "%s": "%s"\n' "$k" "${HASH_MAP[$k]}"
    else
      printf '    "%s": "%s",\n' "$k" "${HASH_MAP[$k]}"
    fi
  done
  printf '  }\n'
  printf '}\n'
} > "$JSON_FILE"

echo "  Written: $JSON_FILE"

echo ""
echo "=== Summary ==="
echo "  PDFs processed: ${#ALL_KEYS[@]}"
echo "  Technique cards: ${#TECHNIQUE_KEYS[@]}"
echo "  Methodologie cards: ${#METHODOLOGIE_KEYS[@]}"
echo "  Technique ZIP: $ZIP_T_NAME"
echo "  Methodologie ZIP: $ZIP_M_NAME"
echo "  Output: $PORTFOLIO_DIR"

#!/bin/bash

# Directory to store rune assets
ASSETS_DIR="$(dirname "$0")"
echo "Storing rune assets in: $ASSETS_DIR"

# Make sure the directory exists
mkdir -p "$ASSETS_DIR"

# DataDragon base URL
DD_BASE="https://ddragon.leagueoflegends.com/cdn/13.1.1"

# Path IDs and their icon paths
declare -A PATH_ICONS=(
  ["8000"]="$DD_BASE/img/perk-images/Styles/7201_Precision.png"
  ["8100"]="$DD_BASE/img/perk-images/Styles/7200_Domination.png"
  ["8200"]="$DD_BASE/img/perk-images/Styles/7202_Sorcery.png"
  ["8300"]="$DD_BASE/img/perk-images/Styles/7203_Whimsy.png"
  ["8400"]="$DD_BASE/img/perk-images/Styles/7204_Resolve.png"
)

# Download path icons
for path_id in "${!PATH_ICONS[@]}"; do
  url="${PATH_ICONS[$path_id]}"
  output="$ASSETS_DIR/$path_id.png"
  echo "Downloading $path_id: $url"
  curl -s "$url" -o "$output"
  
  # Check if download succeeded
  if [ -s "$output" ]; then
    echo "  ✓ Downloaded $path_id"
  else
    echo "  ✗ Failed to download $path_id"
    # Create a small empty file as a placeholder
    touch "$output"
  fi
done

# Common rune IDs
RUNE_IDS=(
  # Precision keystones
  "8005" "8008" "8021" "8010"
  # Domination keystones
  "8112" "8128" "9923"
  # Sorcery keystones
  "8214" "8229" "8230"
  # Inspiration keystones
  "8351" "8360" "8369"
  # Resolve keystones
  "8437" "8439" "8465"
  # Other notable runes
  "8126" "8139" "8143" "8347" "8410" "8316"
  "9101" "9111" "8009" "9104" "9105" "9103"
  "8014" "8017" "8299" "8446" "8463" "8401"
  "8429" "8444" "8473" "8451" "8453" "8242"
  "8224" "8226" "8275" "8210" "8234" "8233"
  "8237" "8232" "8236" "8137" "8140" "8141"
  "8135" "8105" "8106" "8313" "8352" "8345"
)

# Rune icon paths by ID
declare -A RUNE_ICONS=(
  # Precision keystones
  ["8005"]="$DD_BASE/img/perk-images/Styles/Precision/PressTheAttack/PressTheAttack.png"
  ["8008"]="$DD_BASE/img/perk-images/Styles/Precision/LethalTempo/LethalTempoTemp.png"
  ["8021"]="$DD_BASE/img/perk-images/Styles/Precision/FleetFootwork/FleetFootwork.png"
  ["8010"]="$DD_BASE/img/perk-images/Styles/Precision/Conqueror/Conqueror.png"
  
  # Domination keystones
  ["8112"]="$DD_BASE/img/perk-images/Styles/Domination/Electrocute/Electrocute.png"
  ["8128"]="$DD_BASE/img/perk-images/Styles/Domination/DarkHarvest/DarkHarvest.png"
  ["9923"]="$DD_BASE/img/perk-images/Styles/Domination/HailOfBlades/HailOfBlades.png"
  
  # Sorcery keystones
  ["8214"]="$DD_BASE/img/perk-images/Styles/Sorcery/SummonAery/SummonAery.png"
  ["8229"]="$DD_BASE/img/perk-images/Styles/Sorcery/ArcaneComet/ArcaneComet.png"
  ["8230"]="$DD_BASE/img/perk-images/Styles/Sorcery/PhaseRush/PhaseRush.png"
  
  # Inspiration keystones
  ["8351"]="$DD_BASE/img/perk-images/Styles/Inspiration/GlacialAugment/GlacialAugment.png"
  ["8360"]="$DD_BASE/img/perk-images/Styles/Inspiration/UnsealedSpellbook/UnsealedSpellbook.png"
  ["8369"]="$DD_BASE/img/perk-images/Styles/Inspiration/FirstStrike/FirstStrike.png"
  
  # Resolve keystones
  ["8437"]="$DD_BASE/img/perk-images/Styles/Resolve/GraspOfTheUndying/GraspOfTheUndying.png"
  ["8439"]="$DD_BASE/img/perk-images/Styles/Resolve/VeteranAftershock/VeteranAftershock.png"
  ["8465"]="$DD_BASE/img/perk-images/Styles/Resolve/Guardian/Guardian.png"
)

# Download rune icons
for rune_id in "${RUNE_IDS[@]}"; do
  if [[ -n "${RUNE_ICONS[$rune_id]}" ]]; then
    url="${RUNE_ICONS[$rune_id]}"
    output="$ASSETS_DIR/$rune_id.png"
    echo "Downloading rune $rune_id: $url"
    curl -s "$url" -o "$output"
    
    # Check if download succeeded
    if [ -s "$output" ]; then
      echo "  ✓ Downloaded rune $rune_id"
    else
      echo "  ✗ Failed to download rune $rune_id"
      # Create a small empty file as a placeholder
      touch "$output"
    fi
  else
    echo "No URL defined for rune $rune_id, creating placeholder"
    touch "$ASSETS_DIR/$rune_id.png"
  fi
done

echo "Finished downloading rune assets"
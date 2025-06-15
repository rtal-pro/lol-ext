#!/bin/bash

# This script creates simple placeholder hexagon icons for the extension
# We're using ImageMagick for this, so make sure it's installed:
# sudo apt-get install imagemagick

# Function to create a hexagon icon with gold border and blue background
create_hexagon_icon() {
  SIZE=$1
  OUTPUT_FILE=$2
  
  # Create a hexagon shaped icon with League of Legends colors
  convert -size ${SIZE}x${SIZE} xc:none \
    -fill "#0A1428" \
    -stroke "#C8AA6E" \
    -strokewidth 2 \
    -draw "polygon ${SIZE}/2,0 ${SIZE},${SIZE}/4 ${SIZE},${SIZE}*3/4 ${SIZE}/2,${SIZE} 0,${SIZE}*3/4 0,${SIZE}/4" \
    -draw "text ${SIZE}/2,${SIZE}/2 'LoL'" \
    -gravity center \
    -font Arial \
    -pointsize $(($SIZE/4)) \
    -fill "#C8AA6E" \
    $OUTPUT_FILE
}

# Create icons in different sizes
create_hexagon_icon 16 "icon16.png"
create_hexagon_icon 48 "icon48.png"
create_hexagon_icon 128 "icon128.png"

echo "Placeholder icons created successfully!"
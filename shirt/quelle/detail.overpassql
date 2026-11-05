[out:json][timeout:90];
(
  way["highway"~"^(footway|path|pedestrian|steps|service|cycleway|track)$"](around:400,50.5545,9.6740);
  node["natural"="tree"](around:400,50.5545,9.6740);
  way["natural"~"^(tree_row|water|wood|scrub)$"](around:400,50.5545,9.6740);
  nwr["amenity"="fountain"](around:400,50.5545,9.6740);
  way["landuse"~"^(flowerbed|grass|meadow)$"](around:400,50.5545,9.6740);
  way["leisure"~"^(garden|playground|pitch)$"](around:400,50.5545,9.6740);
  way["barrier"="hedge"](around:400,50.5545,9.6740);
  way["water"](around:400,50.5545,9.6740);
  way["man_made"](around:400,50.5545,9.6740);
);
out tags geom;

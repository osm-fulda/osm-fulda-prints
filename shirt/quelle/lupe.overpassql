[out:json][timeout:90];
(
  way(1202607461);
  way["building"](around:500,50.5545,9.6740);
  way["highway"~"^(primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|footway)$"](around:500,50.5545,9.6740);
  way["leisure"="park"](around:500,50.5545,9.6740);
  way["historic"="city_gate"](around:500,50.5545,9.6740);
);
out tags geom;

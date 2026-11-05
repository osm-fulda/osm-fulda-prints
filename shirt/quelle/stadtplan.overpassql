[out:json][timeout:90];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|pedestrian|service|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"](around:2200,50.5530,9.6750);
  way["waterway"="river"](around:3500,50.5530,9.6750);
  way["building"="cathedral"](around:2200,50.5530,9.6750);
  way["amenity"="place_of_worship"]["name"~"Dom"](around:2200,50.5530,9.6750);
  way["leisure"="park"]["name"~"Schlossgarten|Dahliengarten"](around:2200,50.5530,9.6750);
  way["historic"="castle"](around:2200,50.5530,9.6750);
  way["name"="Stadtschloss"](around:2200,50.5530,9.6750);
);
out geom;

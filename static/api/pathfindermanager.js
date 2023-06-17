// -------- Tomtom MAP API Integration --------

// -------------------------- Initializing Functions --------------------------
var apiKey = "aAjtLxcAbdt9AAMqonomSBbXHYNWBqaK";
        
// For testing traffic avoidance testing
var lngLatAreaWithHeavyTraffic;
// End
var lngLatIligan;

var map;
var geolocationControl;
function LoadMap(){
    var script = document.createElement("script");
    script.src = "../static/api/maps-web.min.js";
    script.addEventListener('load', function(){
        componentsLoadedCount += 1;
    })

    document.head.appendChild(script);

    script = document.createElement("script");
    script.src = "../static/api/services.min.js";
    script.addEventListener('load', function(){
        componentsLoadedCount += 1;
    })

    document.head.appendChild(script);

    var stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = "../static/api/maps.css";
    stylesheet.addEventListener('load', function(){
        componentsLoadedCount += 1;
    })
    document.head.appendChild(stylesheet);
}

function InitializeMap(){
    lngLatIligan = new tt.LngLat(124.255550, 8.240444);
    map = tt.map({
        key : apiKey,
        container: "map",
        style:{
            map: 'basic_main',
            poi: 'poi_main',
        },
        styleVisibility: {
            trafficFlow: true,
            trafficIncidents: true,
        },
        center: lngLatIligan,
        zoom: 15,
    });

    longitudeCenter.value = lngLatIligan.lng;
    latitudeCenter.value = lngLatIligan.lat;
    
    geolocationControl = new tt.GeolocateControl({
        positionOptions: {
            enableHighAccuracy: false
        }
    });

    var kilometers = turf.distance([124.252613700139, 8.23749488960783], [124.257220003927,8.24422599366544]);
    console.log(kilometers)
    CreateMapListeners();

    clearInterval(mapComponentsLoadedInterval);

}

var componentsLoadedCount = 0;
mapComponentsLoadedInterval = setInterval(function(){
    InitializeMap();    
        
},2000);

function CreateMapListeners(){
    map.on("load", function(event){
        document.querySelector("#loading_Map").style.display = "none";

        map.addControl(geolocationControl);
        
        allMarkers.forEach(function(marker, index) {
            var popup = new tt.Popup({offset:0}).setText(marker.name);
    
            var lngLat = new tt.LngLat(parseFloat(marker.longitude), parseFloat(marker.latitude));
            new tt.Marker()
            .setLngLat(lngLat)
            .setPopup(popup)
            .addTo(map);
        });
    });
    
    geolocationControl.on("geolocate", function(position){
        longitudeCenter.value = position.coords.longitude;
        latitudeCenter.value = position.coords.latitude;
    });
}

class Marker {
    constructor(name, coordinates, connectedPaths, biasLocations, deadEnd) {
      this.name = name;
      this.coordinates = coordinates;
      this.connectedPaths = connectedPaths;
      this.biasLocations = biasLocations;
      this.deadEnd = deadEnd;
    }
  }
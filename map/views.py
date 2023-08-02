from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
import json
from django.core.serializers import serialize
from tablib import Dataset
from .resources import MarkerResource
from .models import Marker
from django.contrib import messages
from map.forms import MarkerForm
from map.forms import UploadMarker
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse
from django.contrib.gis.db.models.functions import AsGeoJSON
import networkx as nx
from django.db.models import Case, When
import osmnx as ox
import numpy as np
from math import radians, cos, sin, asin, sqrt, atan2
import random


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # radius of Earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def get_nearest_point(base_coordinate, intersections):
    closest_coordinate = None
    shortest_distance = None

    base_lat, base_lon = base_coordinate
    for intersection in intersections:
        intersec_id, lat, lon = intersection
        distance = haversine(base_lat, base_lon, lat, lon)

        if shortest_distance is None or distance < shortest_distance:
            shortest_distance = distance
            closest_coordinate = intersec_id

    return closest_coordinate


def index(request):
    msu_iit = Marker.objects.get(id=485)
    form = MarkerForm(initial={'msu_iit': msu_iit})
    upload_form = UploadMarker()

    context = {}
    if request.method == "POST":
        marker_resource = MarkerResource()
        upload_form = UploadMarker(request.POST)
        form = MarkerForm(request.POST)

        if "marker_start" and "marker_destination" in request.POST.keys():
            # marker_start = request.POST['marker_start']
            # marker_destination = request.POST['marker_destination']
            
            marker_start, marker_destination = 261, 262

            marker_est_start = Marker.objects.filter(id=marker_start).values_list('latitude', 'longitude')
            marker_est_dest = Marker.objects.filter(id=marker_destination).values_list('latitude', 'longitude')
            print('marker_est_start', marker_est_start)
            print('marker_est_dest', marker_est_dest)
            intersections = Marker.objects.filter(type="intersection").values_list('id', 'latitude', 'longitude')
            marker_intersec_start = get_nearest_point(marker_est_start[0], intersections)
            marker_intersec_dest = get_nearest_point(marker_est_dest[0], intersections)
            
            routes = iligangraph(nx.DiGraph(), marker_intersec_start, marker_intersec_dest)
            all_routes = []
            for route in routes:
                route[1].insert(0, int(marker_start))
                route[1].append(int(marker_destination))
                route_with_estab = []
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(route[0])])
                route_inter_markers = Marker.objects.filter(type="intersection", pk__in=route[0]).values("id", "latitude", "longitude").order_by(preserved)
                for marker in route_inter_markers:
                    if 'latitude' or 'longitude' in marker.keys():
                        marker['lat'] = marker["latitude"]
                        del marker["latitude"]

                        marker['lng'] = marker["longitude"]
                        del marker["longitude"]
                route_estab = Marker.objects.filter(type__in=["establishment", "start_dest"], pk__in=route[1]).values("id", "latitude", "longitude", 'name', 'category_level')
                for marker in route_estab:
                    if 'latitude' or 'longitude' in marker.keys():
                        marker['lat'] = marker["latitude"]
                        del marker["latitude"]

                        marker['lng'] = marker["longitude"]
                        del marker["longitude"]
                route_with_estab = [list(route_inter_markers), list(route_estab)]
                all_routes.append(list(route_with_estab))
            context["jsonMarkers"] = json.dumps(list(all_routes))

        else:  
            try:
                dataset = Dataset()
                import_markers = request.FILES['my_file']
                imported_data = dataset.load(import_markers.read(), format="xlsx")
                try:
                    for data in imported_data:
                        value = Marker(
                            data[0],
                            data[1],
                            data[2],
                            data[3],
                            data[4],
                        )
                        break
                        value.save()
                except IntegrityError as e:
                    messages.add_message(request, messages.INFO, "ERROR: Imported data contain empty rows.")
                    
            
            except MultiValueDictKeyError as e:
                pass
        

    context["form"] = form
    context["upload_form"] = upload_form
    
    return render(request, "index.html", context)


def modifymarker_view(request):
    if request.method == "POST":

        modifyType = request.POST["modifyType"]
        name = request.POST["name"]

        if modifyType == "" or name == "":
            return render(request, "error.html", {"error_name":"No means no! You can't do that."})

        markers = Marker.objects.all()

        marker = None
        for m in markers:
            if m.name == name:
                marker = m
                break

        if modifyType == "add":
            if marker != None:
                return render(request, "error.html", {"error_name":"Marker Name already exist, check your available markers before attempting to add."})

            longitude = request.POST["longitude"]
            latitude = request.POST["latitude"]
            
            isANumber = False
            try:
                longAsNum = float(longitude)
                latAsNum = float(latitude)

                if longAsNum < -450 or longAsNum > 450 or latAsNum > 80 or latAsNum < -80:
                    raise ValueError()

                isANumber = True
            except:
                isANumber = False

            if isANumber:
                Marker.objects.create(name=name, longitude=longitude, latitude=latitude)
            else:
                return render(request, "error.html", {"error_name":"Invalid value for Longitude and Latitude"})
        elif modifyType == "remove":
            if marker == None:
                return render(request, "error.html", {"error_name":"Marker Name doesn't exist, check your available markers before attempting to remove."})
            else:
                print(f"Removing {name}")
                marker.delete()
        else:
            return render(request, "error.html", {"error_name":"Oops! You finally found me. - Error"})

        return redirect("/map")
    else:
        return render(request, "error.html", {"error_name":"Oops! You finally found me. - Error"})
    
def markers(request):
    coords = []
    markers = Marker.objects.filter(type="intersection")
    for geojson in range(len(markers)):
        # breakpoint()
        pass
        # nodes = json.loads(qs[geojson][0]["location_as_json"])
        # coords.append(nodes["coordinates"])


    markersNodes = serialize('geojson', Marker.objects.filter(type="intersection"), geometry_field="point")
    return HttpResponse(markersNodes, content_type='json')

def nodes_within_radius_along_path(graph, node1, node2, radius=1.5):
    # Get the x, y coordinates of the two nodes
    x1, y1 = graph.nodes[node1].get('pos')[0], graph.nodes[node1].get('pos')[1]
    x2, y2 = graph.nodes[node2].get('pos')[0], graph.nodes[node2].get('pos')[1]

    # Calculate the coefficients for the line equation ax + by + c = 0
    a = y2 - y1
    b = x1 - x2
    c = y1*x2 - y2*x1

    nodes_within_radius = []
    for node in graph.nodes(data=True):
        if 'pos' in node[1].keys():
            node_x = node[1].get('pos')[0]
            node_y = node[1].get('pos')[1]

            # Calculate the perpendicular distance from the node to the line
            distance = abs(a*node_x + b*node_y + c) / sqrt(a**2 + b**2)
            
            # Check if the node falls within the bounding box defined by node1 and node2
            if (min(x1, x2) <= node_x <= max(x1, x2)) and (min(y1, y2) <= node_y <= max(y1, y2)):
                # Check if the distance is within the radius
                if distance <= radius:
                    nodes_within_radius.append(node[0])
    
    return nodes_within_radius


def iligangraph(graph, start, end):
    # 1ST COLUMN
    graph.add_node(261, pos=(1,42)) #int:1
    graph.add_edge(261, 262, weight=95)
    graph.add_edge(261, 455, weight=94)


    # 2ND COLUMN
    graph.add_node(455, pos=(2,50)) #int:118
    graph.add_edge(455, 261, weight=94)
    graph.add_edge(455, 456, weight=100)

    graph.add_node(262, pos=(2,41)) #int:2
    graph.add_edge(262, 261, weight=95)
    graph.add_edge(262, 263, weight=98)
    graph.add_edge(262, 404, weight=85)

    # 3RD COLUMN
    graph.add_node(263, pos=(3,40)) #int:3
    graph.add_edge(263, 262, weight=98)
    graph.add_edge(263, 264, weight=91)
    graph.add_edge(263, 405, weight=88)

    graph.add_node(456, pos=(3,53)) #int:132
    graph.add_edge(456, 403, weight=100)
    graph.add_edge(456, 455, weight=100)

    # 4TH COLUMN

    # 5TH COLUMN
    graph.add_node(403, pos=(5,54)) #int:143
    graph.add_edge(403, 456, weight=100)
    graph.add_edge(403, 398, weight=100) #to recheck(added temporary weight = 0)
    graph.add_edge(403, 404, weight=96)

    # 6TH COLUMN
    graph.add_node(404, pos=(6,48)) #int:144
    graph.add_edge(404, 262, weight=85)
    graph.add_edge(404, 403, weight=96)
    graph.add_edge(404, 405, weight=97)

    # 7TH COLUMN
    graph.add_node(405, pos=(7,44)) #int:145
    graph.add_edge(405, 400, weight=97)
    graph.add_edge(405, 404, weight=100)
    graph.add_edge(405, 406, weight=100)
    graph.add_edge(405, 263, weight=100)

    # 8TH COLUMN
    graph.add_node(406, pos=(8,41)) #int:146
    graph.add_edge(406, 264, weight=100)
    graph.add_edge(406, 401, weight=100)
    graph.add_edge(406, 405, weight=100)

    graph.add_node(264, pos=(8,34)) #int:4
    graph.add_edge(264, 263, weight=100)
    graph.add_edge(264, 265, weight=100)
    graph.add_edge(264, 406, weight=100)

    # 9TH COLUMN
    graph.add_node(398, pos=(9,56)) #int:138
    graph.add_edge(398, 330, weight=100)
    graph.add_edge(398, 399, weight=98)
    graph.add_edge(398, 403, weight=100)

    # 10TH COLUMN
    graph.add_node(265, pos=(10,33)) #int:5
    graph.add_edge(265, 264, weight=100)
    graph.add_edge(265, 402, weight=100)
    graph.add_edge(265, 407, weight=100)

    graph.add_node(399, pos=(10,52)) #int:139
    graph.add_edge(399, 331, weight=99)
    graph.add_edge(399, 398, weight=98)
    graph.add_edge(399, 400, weight=96)

    # 11TH COLUMN
    graph.add_node(400, pos=(11,46)) #int:140
    graph.add_edge(400, 332, weight=94)
    graph.add_edge(400, 399, weight=96)
    graph.add_edge(400, 401, weight=95)
    graph.add_edge(400, 405, weight=97)

    # 12TH COLUMN
    graph.add_node(401, pos=(12,43)) #int:141
    graph.add_edge(401, 400, weight=95)
    graph.add_edge(401, 406, weight=95)
    graph.add_edge(401, 333, weight=92)
    graph.add_edge(401, 407, weight=100)

    # 13TH COLUMN
    graph.add_node(407, pos=(13,41)) #int:147
    graph.add_edge(407, 401, weight=100)
    graph.add_edge(407, 265, weight=100)
    graph.add_edge(407, 335, weight=94)

    graph.add_node(402, pos=(13,31)) #int:142
    graph.add_edge(402, 265, weight=100)
    graph.add_edge(402, 268, weight=100)

    # 14TH COLUMN
    graph.add_node(268, pos=(14,31)) #int:8
    graph.add_edge(268, 266, weight=100)
    graph.add_edge(268, 402, weight=100)

    # 15TH COLUMN
    graph.add_node(266, pos=(15,30)) #int:6
    graph.add_edge(266, 267, weight=100)
    graph.add_edge(266, 268, weight=100)

    # 16TH COLUMN
    graph.add_node(330, pos=(16,61)) #int:70
    graph.add_edge(330, 324, weight=95)
    graph.add_edge(330, 331, weight=94)
    graph.add_edge(330, 398, weight=95)

    graph.add_node(267, pos=(16,32)) #int:7
    graph.add_edge(267, 266, weight=100)
    graph.add_edge(267, 269, weight=97)
    graph.add_edge(267, 336, weight=96)

    # 17TH COLUMN
    graph.add_node(331, pos=(17,56)) #int:71
    graph.add_edge(331, 325, weight=100)
    graph.add_edge(331, 330, weight=94)
    graph.add_edge(331, 332, weight=99)
    graph.add_edge(331, 399, weight=100)

    # 18TH COLUMN
    graph.add_node(332, pos=(18,53)) #int:72
    graph.add_edge(332, 326, weight=100)
    graph.add_edge(332, 331, weight=99)
    graph.add_edge(332, 333, weight=98)
    graph.add_edge(332, 400, weight=94)

    graph.add_node(269, pos=(18,28)) #int:9
    graph.add_edge(269, 267, weight=97)
    graph.add_edge(269, 437, weight=100)
    graph.add_edge(269, 413, weight=93)

    # 19TH COLUMN
    graph.add_node(333, pos=(19,48)) #int:73
    graph.add_edge(333, 332, weight=98)
    graph.add_edge(333, 334, weight=99)
    graph.add_edge(333, 335, weight=100)
    graph.add_edge(333, 401, weight=93)

    # 20TH COLUMN
    graph.add_node(335, pos=(20,45)) #int:75
    graph.add_edge(335, 333, weight=100)
    graph.add_edge(335, 334, weight=100)
    graph.add_edge(335, 336, weight=100)
    graph.add_edge(335, 407, weight=94)



    # 21ST COLUMN
    graph.add_node(437, pos=(21,22)) #int:177
    graph.add_edge(437, 271, weight=100)
    graph.add_edge(437, 269, weight=100)

    # 22ND COLUMN
    graph.add_node(336, pos=(22,42)) #int:76
    graph.add_edge(336, 267, weight=96)
    graph.add_edge(336, 335, weight=100)
    graph.add_edge(336, 337, weight=98)
    graph.add_edge(336, 413, weight=97)

    # 23RD COLUMN
    graph.add_node(324, pos=(23,66)) #int:64
    graph.add_edge(324, 319, weight=100)
    graph.add_edge(324, 325, weight=98)
    graph.add_edge(324, 330, weight=95)

    # 24TH COLUMN
    graph.add_node(334, pos=(24,53)) #int:74
    graph.add_edge(334, 333, weight=99)
    graph.add_edge(334, 335, weight=100)
    graph.add_edge(334, 409, weight=96)

    graph.add_node(450, pos=(24,31)) #int:190
    graph.add_edge(450, 414, weight=100)
    graph.add_edge(450, 416, weight=100)

    # 25TH COLUMN
    graph.add_node(337, pos=(25,44)) #int:77
    graph.add_edge(337, 329, weight=99)
    graph.add_edge(337, 336, weight=98)
    graph.add_edge(337, 408, weight=96)

    graph.add_node(325, pos=(25,61)) #int:65
    graph.add_edge(325, 324, weight=98)
    graph.add_edge(325, 326, weight=99)
    graph.add_edge(325, 331, weight=100)

    graph.add_node(413, pos=(25,41)) #int:153
    graph.add_edge(413, 269, weight=93)
    graph.add_edge(413, 336, weight=97)
    graph.add_edge(413, 414, weight=100)

    # 26TH COLUMN
    graph.add_node(271, pos=(26,14)) #int:11
    graph.add_edge(271, 437, weight=100)
    graph.add_edge(271, 270, weight=100)

    # 27TH COLUMN
    graph.add_node(409, pos=(27,54)) #int:149
    graph.add_edge(409, 326, weight=100)
    graph.add_edge(409, 329, weight=100)
    graph.add_edge(409, 410, weight=100)
    graph.add_edge(409, 334, weight=96)

    graph.add_node(326, pos=(27,58)) #int:66
    graph.add_edge(326, 325, weight=99)
    graph.add_edge(326, 332, weight=100)
    graph.add_edge(326, 409, weight=100)
    graph.add_edge(326, 412, weight=100)

    graph.add_node(329, pos=(27,53)) #int:69
    graph.add_edge(329, 337, weight=99)
    graph.add_edge(329, 409, weight=100)
    graph.add_edge(329, 432, weight=100)

    # 28TH COLUMN
    graph.add_node(319, pos=(28,69)) #int:59
    graph.add_edge(319, 309, weight=97)
    graph.add_edge(319, 324, weight=100)
    graph.add_edge(319, 320, weight=99)

    graph.add_node(416, pos=(28,27)) #int:156
    graph.add_edge(416, 415, weight=100)
    graph.add_edge(416, 450, weight=100) # possible to be removed. to recheck(added temporary weight = 0)

    graph.add_node(414, pos=(28,40)) #int:154
    graph.add_edge(414, 413, weight=100)
    graph.add_edge(414, 415, weight=100)
    graph.add_edge(414, 450, weight=100)

    # 29TH COLUMN
    graph.add_node(408, pos=(29,42)) #int:148
    graph.add_edge(408, 337, weight=96)
    graph.add_edge(408, 451, weight=96)

    graph.add_node(410, pos=(29,54)) #int:150
    graph.add_edge(410, 409, weight=100)
    graph.add_edge(410, 411, weight=100)

    graph.add_node(270, pos=(29,9)) #int:10
    graph.add_edge(270, 271, weight=100)
    graph.add_edge(270, 431, weight=98)
    graph.add_edge(270, 397, weight=99)

    graph.add_node(320, pos=(29,65)) #int:60
    graph.add_edge(320, 319, weight=99)
    graph.add_edge(320, 321, weight=97)
    graph.add_edge(320, 322, weight=98)

    # 30TH COLUMN
    graph.add_node(322, pos=(30,66)) #int:62
    graph.add_edge(322, 320, weight=98)
    graph.add_edge(322, 323, weight=98)

    graph.add_node(432, pos=(30,51)) #int:172
    graph.add_edge(432, 329, weight=100)

    graph.add_node(415, pos=(30,36)) #int:155
    graph.add_edge(415, 414, weight=100)
    graph.add_edge(415, 416, weight=100)

    graph.add_node(412, pos=(30,60)) #int:152
    graph.add_edge(412, 326, weight=100)
    graph.add_edge(412, 411, weight=99)


    # 31ST COLUMN
    graph.add_node(321, pos=(31,62)) #int:61
    graph.add_edge(321, 320, weight=97)
    graph.add_edge(321, 323, weight=97)

    graph.add_node(411, pos=(31,58)) #int:151
    graph.add_edge(411, 410, weight=100)
    graph.add_edge(411, 412, weight=99)

    # 32ND COLUMN
    graph.add_node(338, pos=(32,40)) #int:78
    graph.add_edge(338, 339, weight=96)
    graph.add_edge(338, 340, weight=99)
    graph.add_edge(338, 451, weight=97)

    # 33RD COLUMN
    graph.add_node(323, pos=(33,64)) #int:63
    graph.add_edge(323, 321, weight=97)
    graph.add_edge(323, 322, weight=98)

    graph.add_node(451, pos=(33,44)) #int:191
    graph.add_edge(451, 408, weight=96)
    graph.add_edge(451, 338, weight=97)

    # 34TH COLUMN
    graph.add_node(312, pos=(34,68)) #int:52
    graph.add_edge(312, 310, weight=98)
    graph.add_edge(312, 313, weight=100)

    graph.add_node(309, pos=(34,71)) #int:49
    graph.add_edge(309, 300, weight=94)
    graph.add_edge(309, 310, weight=97)
    graph.add_edge(309, 319, weight=97)

    graph.add_node(446, pos=(34,60)) #int:186
    graph.add_edge(446, 434, weight=100)

    graph.add_node(397, pos=(34,8)) #int:137
    graph.add_edge(397, 270, weight=99)
    graph.add_edge(397, 272, weight=99)
    graph.add_edge(397, 395, weight=99) # to recheck(added temporary weight = 0)


    # 35TH COLUMN
    graph.add_node(393, pos=(35,14)) #int:133
    graph.add_edge(393, 394, weight=100)
    graph.add_edge(393, 439, weight=100)

    # 36TH COLUMN
    graph.add_node(313, pos=(36,65)) #int:53
    graph.add_edge(313, 312, weight=100)
    graph.add_edge(313, 311, weight=100)

    graph.add_node(310, pos=(36,69)) #int:50
    graph.add_edge(310, 309, weight=97)
    graph.add_edge(310, 312, weight=98)
    graph.add_edge(310, 311, weight=96)

    # 37TH COLUMN
    graph.add_node(394, pos=(37,13)) #int:134
    graph.add_edge(394, 393, weight=100)
    graph.add_edge(394, 395, weight=100)
    graph.add_edge(394, 440, weight=100)

    graph.add_node(439, pos=(37,18)) #int:179
    graph.add_edge(439, 393, weight=100)
    graph.add_edge(439, 440, weight=100)

    graph.add_node(315, pos=(37,63)) #int:55
    graph.add_edge(315, 314, weight=100)
    graph.add_edge(315, 434, weight=100)

    graph.add_node(339, pos=(37,53)) #int:79
    graph.add_edge(339, 327, weight=100)
    graph.add_edge(339, 338, weight=96)


    # 38TH COLUMN
    graph.add_node(327, pos=(38,54)) #int:67
    graph.add_edge(327, 339, weight=100)

    graph.add_node(311, pos=(38,66)) #int:51
    graph.add_edge(311, 310, weight=96)
    graph.add_edge(311, 313, weight=100)
    graph.add_edge(311, 314, weight=100)

    graph.add_node(272, pos=(38,5)) #int:12
    graph.add_edge(272, 396, weight=98)
    graph.add_edge(272, 397, weight=99)

    graph.add_node(440, pos=(38,17)) #int:180
    graph.add_edge(440, 394, weight=100)
    graph.add_edge(440, 439, weight=100)
    graph.add_edge(440, 441, weight=100)

    graph.add_node(431, pos=(38,25)) #int:171
    graph.add_edge(431, 391, weight=100)
    graph.add_edge(431, 270, weight=98)

    graph.add_node(395, pos=(38,12)) #int:135
    graph.add_edge(395, 394, weight=100)
    graph.add_edge(395, 441, weight=100)
    graph.add_edge(395, 452, weight=100)

    # 39TH COLUMN
    graph.add_node(340, pos=(39,43)) #int:80
    graph.add_edge(340, 338, weight=99)
    graph.add_edge(340, 341, weight=98)

    graph.add_node(316, pos=(39,59)) #int:56
    graph.add_edge(316, 434, weight=100)
    graph.add_edge(316, 317, weight=100)

    graph.add_node(314, pos=(39,64)) #int:54
    graph.add_edge(314, 315, weight=100)
    graph.add_edge(314, 311, weight=100)
    graph.add_edge(314, 317, weight=100)

    graph.add_node(300, pos=(39,72)) #int:40
    graph.add_edge(300, 298, weight=95)
    graph.add_edge(300, 309, weight=94)
    graph.add_edge(300, 301, weight=92)

    graph.add_node(441, pos=(39,16)) #int:181
    graph.add_edge(441, 395, weight=100)
    graph.add_edge(441, 440, weight=100)
    graph.add_edge(441, 453, weight=99)

    graph.add_node(452, pos=(39,11)) #int:192
    graph.add_edge(452, 397, weight=99)
    graph.add_edge(452, 395, weight=100)
    graph.add_edge(452, 453, weight=98)

    graph.add_node(391, pos=(39,25)) #int:131
    graph.add_edge(391, 390, weight=99)
    graph.add_edge(391, 389, weight=99)
    graph.add_edge(391, 431, weight=100)

    # 40TH COLUMN
    graph.add_node(301, pos=(40,71)) #int:41
    graph.add_edge(301, 300, weight=92)
    graph.add_edge(301, 302, weight=100)
    graph.add_edge(301, 299, weight=100)

    graph.add_node(328, pos=(40,56)) #int:68
    graph.add_edge(328, 318, weight=100)

    graph.add_node(453, pos=(40,16)) #int:193
    graph.add_edge(453, 441, weight=99)
    graph.add_edge(453, 452, weight=98)

    graph.add_node(390, pos=(40,27)) #int:130
    graph.add_edge(390, 358, weight=100)
    graph.add_edge(390, 391, weight=99)

    # 41ST COLUMN
    graph.add_node(317, pos=(41,60)) #int:57
    graph.add_edge(317, 314, weight=100)
    graph.add_edge(317, 316, weight=100)
    graph.add_edge(317, 318, weight=100)

    graph.add_node(302, pos=(41,68)) #int:42
    graph.add_edge(302, 301, weight=96)
    graph.add_edge(302, 304, weight=100)
    graph.add_edge(302, 303, weight=100)

    # 42ND COLUMN
    graph.add_node(389, pos=(42,24)) #int:129
    graph.add_edge(389, 358, weight=100)
    graph.add_edge(389, 391, weight=99)

    graph.add_node(304, pos=(42,65)) #int:44
    graph.add_edge(304, 302, weight=100)
    graph.add_edge(304, 306, weight=100)
    graph.add_edge(304, 305, weight=100)

    # 43RD COLUMN
    graph.add_node(358, pos=(43,26)) #int:98
    graph.add_edge(358, 425, weight=100)
    graph.add_edge(358, 390, weight=99)
    graph.add_edge(358, 389, weight=97)

    graph.add_node(341, pos=(43,46)) #int:81
    graph.add_edge(341, 340, weight=98) #these two line are possible to be removed. to recheck(added temporary weight = 0)
    graph.add_edge(341, 342, weight=100)

    graph.add_node(318, pos=(43,57)) #int:58
    graph.add_edge(318, 317, weight=100)
    graph.add_edge(318, 328, weight=100) #to recheck(added temporary weight = 0)

    graph.add_node(425, pos=(43,27)) #int:165
    graph.add_edge(425, 358, weight=100)
    graph.add_edge(425, 388, weight=100)
    graph.add_edge(425, 356, weight=100) #to recheck(added temporary weight = 0)

    graph.add_node(388, pos=(43,28)) #int:128
    graph.add_edge(388, 353, weight=100)
    graph.add_edge(388, 425, weight=100)

    # 44TH COLUMN
    graph.add_node(356, pos=(44,27)) #int:96
    graph.add_edge(356, 357, weight=100)
    graph.add_edge(356, 424, weight=100)
    graph.add_edge(356, 425, weight=100)
    graph.add_edge(356, 353, weight=100)# to recheck(added temporary weight = 0)

    graph.add_node(353, pos=(44,28)) #int:93
    graph.add_edge(353, 350, weight=100)
    graph.add_edge(353, 354, weight=100)
    graph.add_edge(353, 356, weight=100)
    graph.add_edge(353, 388, weight=100)

    graph.add_node(350, pos=(44,33)) #int:90
    graph.add_edge(350, 348, weight=100)
    graph.add_edge(350, 353, weight=100)
    graph.add_edge(350, 449, weight=100)

    graph.add_node(348, pos=(44,38)) #int:88
    graph.add_edge(348, 443, weight=99)
    graph.add_edge(348, 350, weight=100)
    graph.add_edge(348, 346, weight=97)

    graph.add_node(346, pos=(44,41)) #int:86
    graph.add_edge(346, 348, weight=97)
    graph.add_edge(346, 342, weight=97)
    graph.add_edge(346, 442, weight=100)

    graph.add_node(342, pos=(44,45)) #int:82
    graph.add_edge(342, 341, weight=100)
    graph.add_edge(342, 346, weight=100)
    graph.add_edge(342, 343, weight=99)

    graph.add_node(424, pos=(44,25)) #int:164
    graph.add_edge(424, 356, weight=100)
    graph.add_edge(424, 359, weight=100)

    # 45TH COLUMN
    graph.add_node(305, pos=(45,58)) #int:45
    graph.add_edge(305, 307, weight=100)
    graph.add_edge(305, 304, weight=100)

    graph.add_node(298, pos=(45,74)) #int:38
    graph.add_edge(298, 297, weight=98)
    graph.add_edge(298, 299, weight=95)
    graph.add_edge(298, 300, weight=95)

    # 46TH COLUMN
    graph.add_node(306, pos=(46,67)) #int:46
    graph.add_edge(306, 303, weight=100)
    graph.add_edge(306, 304, weight=100)
    graph.add_edge(306, 308, weight=100)

    graph.add_node(443, pos=(46,39)) #int:183
    graph.add_edge(443, 444, weight=100)
    graph.add_edge(443, 348, weight=100)
    graph.add_edge(443, 442, weight=100)

    # 47TH COLUMN
    graph.add_node(303, pos=(47,70)) #int:43
    graph.add_edge(303, 299, weight=100)
    graph.add_edge(303, 302, weight=100)
    graph.add_edge(303, 306, weight=100)

    # 48TH COLUMN
    graph.add_node(449, pos=(48,33)) #int:189
    graph.add_edge(449, 352, weight=100)
    graph.add_edge(449, 350, weight=100)
    graph.add_edge(449, 448, weight=100)

    graph.add_node(448, pos=(48,36)) #int:188
    graph.add_edge(448, 360, weight=100)
    graph.add_edge(448, 449, weight=100)

    graph.add_node(442, pos=(48,42)) #int:182
    graph.add_edge(442, 347, weight=100)
    graph.add_edge(442, 346, weight=100)
    graph.add_edge(442, 443, weight=100)

    graph.add_node(354, pos=(48,28)) #int:94
    graph.add_edge(354, 352, weight=100)
    graph.add_edge(354, 353, weight=100)
    graph.add_edge(354, 355, weight=100)

    # 49TH COLUMN
    graph.add_node(352, pos=(49,33)) #int:92
    graph.add_edge(352, 351, weight=100)
    graph.add_edge(352, 354, weight=100)
    graph.add_edge(352, 449, weight=100)

    graph.add_node(343, pos=(49,45)) #int:83
    graph.add_edge(343, 342, weight=100)
    graph.add_edge(343, 347, weight=100)
    graph.add_edge(343, 445, weight=99)

    graph.add_node(308, pos=(49,64)) #int:48
    graph.add_edge(308, 306, weight=100)
    graph.add_edge(308, 307, weight=100)

    graph.add_node(444, pos=(49,40)) #int:184
    graph.add_edge(444, 349, weight=100) # to recheck(added temporary weight = 0)
    graph.add_edge(444, 443, weight=100) # to recheck(added temporary weight = 0)
    graph.add_edge(444, 360, weight=100) # to recheck(added temporary weight = 0)

    # 50TH COLUMN
    graph.add_node(360, pos=(50,36)) #int:100
    graph.add_edge(360, 448, weight=100) 
    graph.add_edge(360, 444, weight=100) # to recheck(added temporary weight = 0)

    graph.add_node(347, pos=(50,43)) #int:87
    graph.add_edge(347, 447, weight=100)
    graph.add_edge(347, 442, weight=100)
    graph.add_edge(347, 343, weight=100)

    graph.add_node(307, pos=(50,60)) #int:47
    graph.add_edge(307, 308, weight=100)
    graph.add_edge(307, 305, weight=99)

    graph.add_node(299, pos=(50,73)) #int:39
    graph.add_edge(299, 298, weight=95)
    graph.add_edge(299, 435, weight=100)
    graph.add_edge(299, 301, weight=85)
    graph.add_edge(299, 303, weight=99)

    graph.add_node(396, pos=(50,3)) #int:136
    graph.add_edge(396, 273, weight=98)
    graph.add_edge(396, 272, weight=98)


    # 51ST COLUMN
    graph.add_node(359, pos=(51,25)) #int:99
    graph.add_edge(359, 357, weight=99)
    graph.add_edge(359, 424, weight=100)

    graph.add_node(349, pos=(51,41)) #int:89
    graph.add_edge(349, 447, weight=100)
    graph.add_edge(349, 444, weight=100) # to recheck(added temporary weight = 0)
    graph.add_edge(349, 426, weight=100)

    graph.add_node(447, pos=(51,42)) #int:187
    graph.add_edge(447, 349, weight=100)
    graph.add_edge(447, 347, weight=100)
    graph.add_edge(447, 427, weight=100)

    graph.add_node(445, pos=(51,47)) #int:185
    graph.add_edge(445, 344, weight=100)
    graph.add_edge(445, 343, weight=99)

    # 52ND COLUMN
    graph.add_node(357, pos=(52,27)) #int:97
    graph.add_edge(357, 356, weight=100)
    graph.add_edge(357, 359, weight=99)
    graph.add_edge(357, 355, weight=100)
    graph.add_edge(357, 361, weight=100)

    graph.add_node(355, pos=(52,28)) #int:95
    graph.add_edge(355, 351, weight=97)
    graph.add_edge(355, 354, weight=100)
    graph.add_edge(355, 357, weight=100)

    graph.add_node(436, pos=(52,70)) #int:176
    graph.add_edge(436, 306, weight=99)

    graph.add_node(435, pos=(52,72)) #int:175
    graph.add_edge(435, 299, weight=100)
    graph.add_edge(435, 296, weight=96)

    # 53RD COLUMN
    graph.add_node(427, pos=(53,42)) #int:167
    graph.add_edge(427, 447, weight=100)

    graph.add_node(426, pos=(53,40)) #int:166
    graph.add_edge(426, 351, weight=100)
    graph.add_edge(426, 349, weight=100)# to recheck(added temporary weight = 0)

    graph.add_node(273, pos=(53,2)) #int:13
    graph.add_edge(273, 396, weight=98)
    graph.add_edge(273, 274, weight=99)

    graph.add_node(276, pos=(53,6)) #int:16
    graph.add_edge(276, 273, weight=96)
    graph.add_edge(276, 345, weight=100) # to recheck(added temporary weight = 0)

    graph.add_node(297, pos=(53,77)) #int:37
    graph.add_edge(297, 298, weight=98)
    graph.add_edge(297, 296, weight=100)

    graph.add_node(351, pos=(53,32)) #int:91
    graph.add_edge(351, 426, weight=100)
    graph.add_edge(351, 352, weight=100)
    graph.add_edge(351, 355, weight=97)

    graph.add_node(344, pos=(53,48)) #int:84
    graph.add_edge(344, 445, weight=100)

    graph.add_node(362, pos=(53,24)) #int:102
    graph.add_edge(362, 361, weight=100)
    graph.add_edge(362, 363, weight=99)

    graph.add_node(361, pos=(53,27)) #int:101
    graph.add_edge(361, 357, weight=100)
    graph.add_edge(361, 362, weight=100)
    graph.add_edge(361, 367, weight=97)
    graph.add_edge(361, 366, weight=100)

    # 54TH COLUMN
    graph.add_node(296, pos=(54,76)) #int:36
    graph.add_edge(296, 291, weight=100)
    graph.add_edge(296, 297, weight=100)
    graph.add_edge(296, 435, weight=96)

    # 55TH COLUMN
    graph.add_node(367, pos=(55,39)) #int:107
    graph.add_edge(367, 361, weight=97)
    graph.add_edge(367, 368, weight=100)
    graph.add_edge(367, 370, weight=100)

    graph.add_node(274, pos=(55,1)) #int:14
    graph.add_edge(274, 273, weight=99)
    graph.add_edge(274, 275, weight=100)

    # 56TH COLUMN
    graph.add_node(366, pos=(56,26)) #int:106
    graph.add_edge(366, 361, weight=100)
    graph.add_edge(366, 365, weight=100)
    graph.add_edge(366, 368, weight=100)

    graph.add_node(363, pos=(56,23)) #int:103
    graph.add_edge(363, 362, weight=99)
    graph.add_edge(363, 364, weight=100)

    # 57TH COLUMN
    graph.add_node(275, pos=(57,6)) #int:15
    graph.add_edge(275, 345, weight=100)
    graph.add_edge(275, 274, weight=100)
    graph.add_edge(275, 277, weight=100)

    graph.add_node(434, pos=(37,62)) #int:174
    graph.add_edge(434, 446, weight=100)
    graph.add_edge(434, 315, weight=100)
    graph.add_edge(434, 316, weight=100)

    graph.add_node(370, pos=(57,46)) #int:110
    graph.add_edge(370, 371, weight=100)
    graph.add_edge(370, 367, weight=100)

    # 58TH COLUMN
    graph.add_node(368, pos=(58,38)) #int:108
    graph.add_edge(368, 367, weight=100)
    graph.add_edge(368, 369, weight=100)
    graph.add_edge(368, 366, weight=100)
    graph.add_edge(368, 371, weight=100)

    graph.add_node(364, pos=(58,24)) #int:104
    graph.add_edge(364, 363, weight=100)
    graph.add_edge(364, 433, weight=100)
    graph.add_edge(364, 365, weight=100)

    # 59TH COLUMN
    graph.add_node(365, pos=(59,26)) #int:105
    graph.add_edge(365, 366, weight=100)
    graph.add_edge(365, 364, weight=100)
    graph.add_edge(365, 369, weight=99)

    graph.add_node(291, pos=(59,75)) #int:31
    graph.add_edge(291, 478, weight=100)
    graph.add_edge(291, 296, weight=100)

    # 60TH COLUMN
    graph.add_node(369, pos=(60,37)) #int:109
    graph.add_edge(369, 372, weight=100)
    graph.add_edge(369, 365, weight=99)
    graph.add_edge(369, 368, weight=100) # to recheck(added temporary weight = 0)

    graph.add_node(371, pos=(60,47)) #int:111
    graph.add_edge(371, 370, weight=100)
    graph.add_edge(371, 372, weight=100)
    graph.add_edge(371, 368, weight=100)

    graph.add_node(433, pos=(60,23)) #int:173
    graph.add_edge(433, 430, weight=100)
    graph.add_edge(433, 364, weight=100)


    # 61ST COLUMN
    graph.add_node(277, pos=(61,15)) #int:17
    graph.add_edge(277, 275, weight=100)
    graph.add_edge(277, 278, weight=100)

    graph.add_node(478, pos=(61,74)) #int:32
    graph.add_edge(478, 290, weight=100)
    graph.add_edge(478, 291, weight=100)

    graph.add_node(430, pos=(61,22)) #int:170
    graph.add_edge(430, 429, weight=100)
    graph.add_edge(430, 433, weight=100)

    graph.add_node(374, pos=(61,26)) #int:114
    graph.add_edge(374, 375, weight=100)
    graph.add_edge(374, 380, weight=100)

    graph.add_node(372, pos=(61,49)) #int:112
    graph.add_edge(372, 371, weight=100)
    graph.add_edge(372, 369, weight=100)


    # 62ND COLUMN
    graph.add_node(429, pos=(62,21)) #int:169
    graph.add_edge(429, 279, weight=99)
    graph.add_edge(429, 430, weight=100)

    graph.add_node(290, pos=(62,73)) #int:30
    graph.add_edge(290, 478, weight=100)
    graph.add_edge(290, 289, weight=100)

    # 63RD COLUMN
    graph.add_node(375, pos=(63,24)) #int:115
    graph.add_edge(375, 374, weight=100)
    graph.add_edge(375, 376, weight=100)
    graph.add_edge(375, 280, weight=100)

    graph.add_node(279, pos=(63,20)) #int:19
    graph.add_edge(279, 429, weight=99)
    graph.add_edge(279, 280, weight=100)
    graph.add_edge(279, 278, weight=100)

    graph.add_node(278, pos=(63,19)) #int:18
    graph.add_edge(278, 277, weight=100)
    graph.add_edge(278, 279, weight=100)


    # 64TH COLUMN
    graph.add_node(380, pos=(64,50)) #int:120
    graph.add_edge(380, 381, weight=100)
    graph.add_edge(380, 374, weight=100)


    # 65TH COLUMN
    graph.add_node(280, pos=(65,22)) #int:20
    graph.add_edge(280, 279, weight=100)
    graph.add_edge(280, 428, weight=100)
    graph.add_edge(280, 375, weight=100)

    graph.add_node(377, pos=(65,29)) #int:117
    graph.add_edge(377, 376, weight=99)
    graph.add_edge(377, 383, weight=99)
    graph.add_edge(377, 386, weight=96)

    graph.add_node(376, pos=(65,26)) #int:116
    graph.add_edge(376, 377, weight=99)
    graph.add_edge(376, 387, weight=95)
    graph.add_edge(376, 377, weight=99)#kindly add weight


    # 66TH COLUMN
    graph.add_node(383, pos=(66,42)) #int:123
    graph.add_edge(383, 382, weight=100)
    graph.add_edge(383, 386, weight=100)
    graph.add_edge(383, 377, weight=98)


    graph.add_node(382, pos=(66,51)) #int:121
    graph.add_edge(382, 381, weight=100)
    graph.add_edge(382, 383, weight=100)
    graph.add_edge(382, 385, weight=100)

    graph.add_node(381, pos=(66,46)) #int:122
    graph.add_edge(381, 380, weight=100)
    graph.add_edge(381, 382, weight=100)
    graph.add_edge(381, 384, weight=99)

    graph.add_node(289, pos=(66,71)) #int:29
    graph.add_edge(289, 290, weight=100)
    graph.add_edge(289, 476, weight=99)


    # 67TH COLUMN
    graph.add_node(476, pos=(67,68)) #int:35
    graph.add_edge(476, 289, weight=99)
    graph.add_edge(476, 421, weight=99)


    # 68TH COLUMN
    graph.add_node(423, pos=(68,69)) #int:163
    graph.add_edge(423, 289, weight=100)
    graph.add_edge(423, 422, weight=100)

    graph.add_node(428, pos=(68,26)) #int:168
    graph.add_edge(428, 282, weight=100)
    graph.add_edge(428, 280, weight=100)


    # 69TH COLUMN
    graph.add_node(422, pos=(69,68)) #int:162
    graph.add_edge(422, 477, weight=100)

    graph.add_node(386, pos=(69,43)) #int:126
    graph.add_edge(386, 383, weight=100)
    graph.add_edge(386, 387, weight=100)
    graph.add_edge(386, 377, weight=96)

    # 70TH COLUMN
    graph.add_node(421, pos=(70,62)) #int:161
    graph.add_edge(421, 438, weight=100)

    # 71ST COLUMN
    graph.add_node(438, pos=(71,57)) #int:178
    graph.add_edge(438, 287, weight=97)

    graph.add_node(477, pos=(71,63)) #int:160
    graph.add_edge(477, 422, weight=100)


    # 72ND COLUMN
    graph.add_node(287, pos=(72,54)) #int:27
    graph.add_edge(287, 379, weight=97)

    graph.add_node(387, pos=(72,41)) #int:127
    graph.add_edge(387, 282, weight=99)
    graph.add_edge(387, 376, weight=95)
    graph.add_edge(387, 386, weight=100)


    # 73RD COLUMN
    graph.add_node(282, pos=(73,39)) #int:22
    graph.add_edge(282, 428, weight=100)
    graph.add_edge(282, 281, weight=99)
    graph.add_edge(282, 387, weight=99)

    graph.add_node(419, pos=(73,63)) #int:159
    graph.add_edge(419, 477, weight=100)

    graph.add_node(385, pos=(73,47)) #int:125
    graph.add_edge(385, 384, weight=100)
    graph.add_edge(385, 283, weight=100)
    graph.add_edge(385, 382, weight=100)

    graph.add_node(379, pos=(73,55)) #int:119
    graph.add_edge(379, 479, weight=98)


    # 74TH COLUMN
    graph.add_node(384, pos=(74,53)) #int:124
    graph.add_edge(384, 381, weight=99)
    graph.add_edge(384, 385, weight=100)


    # 75TH COLUMN
    graph.add_node(281, pos=(75,42)) #int:21
    graph.add_edge(281, 282, weight=99)
    graph.add_edge(281, 283, weight=100)

    graph.add_node(288, pos=(75,68)) #int:28
    graph.add_edge(288, 422, weight=100)
    graph.add_edge(288, 417, weight=99)


    # 76TH COLUMN
    graph.add_node(283, pos=(76,44)) #int:23
    graph.add_edge(283, 281, weight=100)
    graph.add_edge(283, 285, weight=96)
    graph.add_edge(283, 385, weight=100)

    graph.add_node(418, pos=(76,63)) #int:158
    graph.add_edge(418, 419, weight=97)


    # 77TH COLUMN
    graph.add_node(479, pos=(77,55)) #int:33
    graph.add_edge(479, 454, weight=100)


    graph.add_node(417, pos=(77,63)) #int:157
    graph.add_edge(417, 288, weight=97)
    graph.add_edge(417, 418, weight=100)

    # 78TH COLUMN
    graph.add_node(454, pos=(78,54)) #int:194
    graph.add_edge(454, 284, weight=100)

    graph.add_node(286, pos=(78,55)) #int:26
    graph.add_edge(286, 417, weight=100)


    # 79TH COLUMN
    graph.add_node(285, pos=(79,54)) #int:25
    graph.add_edge(285, 284, weight=100)
    graph.add_edge(285, 283, weight=96)


    # 80TH COLUMN
    graph.add_node(284, pos=(80,55)) #int:24
    graph.add_edge(284, 286, weight=100)


    #ESTABLISHMENTS
    graph.add_node(17, pos=(4,52)) #Sym Motorcycle Dealer
    graph.add_node(16, pos=(4,51)) #Merry Muffet Fried Chicken
    graph.add_node(15, pos=(3,49)) #Pipie Co Cake Bread and Pastries
    graph.add_node(14, pos=(3,46)) #The Bridge Student Center
    graph.add_node(13, pos=(2,45)) #Wash Up
    graph.add_node(12, pos=(2,44)) #James Letchon Bayug
    graph.add_node(11, pos=(3,42)) #JR Boys Boarding House
    graph.add_node(10, pos=(2,42)) #Vogue Hair Salon and Spa
    graph.add_node(9, pos=(2,41)) #Eunics Marketing
    graph.add_node(8, pos=(19,33)) #Ritza's Garden
    graph.add_node(7, pos=(4,36)) #Motech - Iligan
    graph.add_node(6, pos=(3,38)) #Demver Barbershop
    graph.add_node(5, pos=(1,41)) #Loalve fashion Boutique
    graph.add_node(4, pos=(2,39)) #Kling Eatery
    graph.add_node(3, pos=(1,39)) #Summer Brew
    graph.add_node(2, pos=(1,40)) #Bread and Brew Bakery Cafe
    graph.add_node(1, pos=(1,42)) #MSU-IIT
    graph.add_node(118, pos=(62,20)) #Sj Mart Iligan City
    graph.add_node(117, pos=(60,18)) #Tienda De Rico
    graph.add_node(116, pos=(54,8)) #Seventh Day Adventist Churh
    graph.add_node(115, pos=(51,7)) #Teetay's Quickmeal
    graph.add_node(114, pos=(54,4)) #Payag ni Balot
    graph.add_node(113, pos=(54,2)) #Soy Cafe Diner
    graph.add_node(112, pos=(52,3)) #Ctalipio Construction
    graph.add_node(111, pos=(47,4)) #IBT Badminton Sports center
    graph.add_node(110, pos=(44,4)) #Armies Collect. & Gen. Merch.
    graph.add_node(109, pos=(39,8)) #Sukang Pinakurat Residence
    graph.add_node(108, pos=(34,8)) #SS Coffee Shop
    graph.add_node(107, pos=(32,11)) #JAKS Autocare
    graph.add_node(106, pos=(24,42)) #Doy's Barbershop
    graph.add_node(105, pos=(25,42)) #65 Miguel Sheker
    graph.add_node(104, pos=(27,42)) #Tominio Store
    graph.add_node(103, pos=(31,41)) #Bagong Silang Mosque
    graph.add_node(102, pos=(32,41)) #Lagan Store
    graph.add_node(101, pos=(41,43)) #Phasca Tutorial Learning Center
    graph.add_node(100, pos=(41,40)) #Bagong Silang Elem. School
    graph.add_node(99, pos=(36,27)) #Danights Goodies
    graph.add_node(98, pos=(38,26)) #Namaste Homestay
    graph.add_node(97, pos=(29,22)) #Wet Park
    graph.add_node(96, pos=(24,21)) #BIR
    graph.add_node(95, pos=(22,23)) #Fontana Bakeshop
    graph.add_node(94, pos=(22,26)) #Housing and Resettlement Office
    graph.add_node(93, pos=(21,27)) #COA Provincial Satellite
    graph.add_node(92, pos=(22,28)) #DOST-PAGASA Iligan
    graph.add_node(91, pos=(19,29)) #Cuadro Ocho, Inc.
    graph.add_node(89, pos=(18,31)) #M2 Store
    graph.add_node(88, pos=(18,30)) #Salih Marketing
    graph.add_node(87, pos=(23,43)) #Z's Pares & More
    graph.add_node(86, pos=(26,50)) #South Sea Blue Water
    graph.add_node(85, pos=(24,54)) #Bagong Silang Brgy. Hall
    graph.add_node(84, pos=(20,52)) #Arabigo Coffee Roastery
    graph.add_node(83, pos=(19,49)) #Saladaga Sari-sari Store
    graph.add_node(82, pos=(19,52)) #Grandma's Heritage
    graph.add_node(81, pos=(18,55)) #Apao Dormitory
    graph.add_node(80, pos=(20,62)) #Steel tech Colored roofing
    graph.add_node(79, pos=(20,60)) #Kneekeytaa
    graph.add_node(78, pos=(19,62)) #Leand Enterprises
    graph.add_node(77, pos=(19,61)) #Jadd Boxing and Fitness Gym
    graph.add_node(76, pos=(17,62)) #Five Star
    graph.add_node(75, pos=(17,61)) #Electroscope Electrical Services
    graph.add_node(74, pos=(18,61)) #Chin Glass and Aluminum Supply
    graph.add_node(73, pos=(18,60)) #Gridline Enterprises
    graph.add_node(72, pos=(19,44)) #Identity Church Iligan
    graph.add_node(71, pos=(15,43)) #Flora's Residence Hall
    graph.add_node(70, pos=(14,41)) #ALMING Guest House
    graph.add_node(69, pos=(16,51)) #Motolite Papalo's Battery
    graph.add_node(68, pos=(16,49)) #Raquel Bakeshop
    graph.add_node(67, pos=(15,48)) #Sushi Bake Iligan
    graph.add_node(66, pos=(15,45)) #Christian Group Ministries Inc.
    graph.add_node(65, pos=(15,44)) #Jazz Right
    graph.add_node(64, pos=(12,44)) #Coby' s Fast Food & BBQ haus
    graph.add_node(63, pos=(12,45)) #Happy Choice Guest House
    graph.add_node(62, pos=(15,53)) #Clarks Flower Shells and Crafts
    graph.add_node(61, pos=(15,50)) #L&L Advertising Agency
    graph.add_node(60, pos=(13,48)) #Rhyme Enterprises Laundry Shop
    graph.add_node(59, pos=(11,50)) #Pan-Q C-Park
    graph.add_node(56, pos=(16,60)) #Petron
    graph.add_node(55, pos=(16,59)) #7-Eleven
    graph.add_node(54, pos=(15,59)) #Monlan Suites
    graph.add_node(53, pos=(15,58)) #Black Scoop Cafe
    graph.add_node(52, pos=(15,57)) #Al Hussien Construction
    graph.add_node(51, pos=(14,58)) #Sports Back Family KTV Bar
    graph.add_node(50, pos=(12,56)) #SSS Iligan Branch
    graph.add_node(49, pos=(11,55)) #Hi-Way Pharmart Iligan
    graph.add_node(48, pos=(10,55)) #Shoppe 24
    graph.add_node(47, pos=(8,42)) #Aquarelle Purified Drinking Water
    graph.add_node(46, pos=(9,43)) #Choy Halal BBQ
    graph.add_node(45, pos=(10,44)) #Milestone Van Rental Services
    graph.add_node(44, pos=(11,45)) #Famous Pension House II
    graph.add_node(43, pos=(10,47)) #Adventist Medical Center College
    graph.add_node(42, pos=(7,52)) #Adventist Medical Center - Iligan
    graph.add_node(41, pos=(18,36)) #SMC-Basic Education
    graph.add_node(39, pos=(15,33)) #Miguel Sheker Park
    graph.add_node(38, pos=(14,32)) #Iligan Food Terminal Cooperative
    graph.add_node(37, pos=(13,35)) #San Miguel Brgy. Hall
    graph.add_node(34, pos=(9,39)) #Famous Pension House 1
    graph.add_node(33, pos=(6,36)) #ILIGAN-SDA Church
    graph.add_node(32, pos=(8,41)) #Adventist Elementary School ILG
    graph.add_node(31, pos=(6,42)) #AMC - Iligan Bakery
    graph.add_node(30, pos=(7,43)) #Iligan Bay Multipurpose Cooperative
    graph.add_node(29, pos=(4,40)) #Fire and Ice Hostel
    graph.add_node(28, pos=(5,42)) #Lifebox Bistro
    graph.add_node(27, pos=(5,45)) #Alvanza Boarding House
    graph.add_node(26, pos=(6,46)) #Pinkbox
    graph.add_node(23, pos=(6,42)) #Al Pater Al Kuwait
    graph.add_node(22, pos=(5,52)) #Site Scape Internet Cafe
    graph.add_node(21, pos=(5,51)) #G7 internet Cafe
    graph.add_node(20, pos=(5,50)) #S2h Drugstore
    graph.add_node(19, pos=(4,46)) #Oliverio Boarding House
    graph.add_node(18, pos=(5,52)) #Kainan ni Ate Sweet
    graph.add_node(218, pos=(49,74)) #XanderTech
    graph.add_node(217, pos=(47,74)) #Macarius Eatery
    graph.add_node(216, pos=(48,73)) #Shandy Bakeshop
    graph.add_node(215, pos=(46,73)) #Sweartea Milktea Hub
    graph.add_node(214, pos=(55,74)) #AMS Eatery
    graph.add_node(213, pos=(54,73)) #Unit 3 Fabros Apartment
    graph.add_node(212, pos=(50,71)) #Cherry Blossom
    graph.add_node(211, pos=(58,70)) #Tambo Central School
    graph.add_node(210, pos=(50,70)) #Iligan Online Shop Philippines
    graph.add_node(209, pos=(54,67)) #Momoy Pet Supplies
    graph.add_node(208, pos=(61,66)) #JKM Enterprises Iligan Branch
    graph.add_node(207, pos=(65,69)) #National Housing Authority
    graph.add_node(206, pos=(66,68)) #Kaye and Shan Store
    graph.add_node(205, pos=(50,58)) #Tambo Basketball Court
    graph.add_node(204, pos=(48,57)) #V&4J Enterprises
    graph.add_node(203, pos=(47,60)) #JS Salvador Architect
    graph.add_node(202, pos=(45,73)) #Angels Choice Bakeshop
    graph.add_node(201, pos=(45,72)) #King Motor Parts
    graph.add_node(200, pos=(44,73)) #Aquastar
    graph.add_node(199, pos=(44,72)) #Motorstar
    graph.add_node(198, pos=(43,71)) #Cabili Tomas O. Law Office
    graph.add_node(197, pos=(41,70)) #Hilton Motors Corporation
    graph.add_node(196, pos=(43,72)) #ANP Motolab
    graph.add_node(195, pos=(40,70)) #Air21
    graph.add_node(194, pos=(42,71)) #A&J Eatery
    graph.add_node(193, pos=(39,67)) #STO. Rosario Village School
    graph.add_node(192, pos=(41,71)) #AP Cargo Iligan Branch
    graph.add_node(191, pos=(40,72)) #Norkis 5R Services
    graph.add_node(190, pos=(67,66)) #Ukay-Ukay Shoes
    graph.add_node(188, pos=(72,65)) #Iligan City Public Market
    graph.add_node(187, pos=(74,63)) #Task Force Kalikasan
    graph.add_node(186, pos=(75,64)) #NBI
    graph.add_node(185, pos=(72,59)) #Tea'say Iligan City
    graph.add_node(184, pos=(73,61)) #Westbound Jeepney And Bus Terminal
    graph.add_node(183, pos=(74,59)) #City Agriculture Office
    graph.add_node(182, pos=(75,55)) #Landbank ATM
    graph.add_node(181, pos=(72,55)) #Iligan Integrated Bus Terminal
    graph.add_node(180, pos=(73,56)) #Public Employment Service Office
    graph.add_node(179, pos=(78,53)) #Rosy Lechon Manok
    graph.add_node(178, pos=(79,53)) #Castanares Kambingan
    graph.add_node(177, pos=(78,52)) #Hugo Detailing
    graph.add_node(176, pos=(77,51)) #Chief's Meatshop And D&C Minimart
    graph.add_node(175, pos=(67,46)) #Grocer ILG
    graph.add_node(174, pos=(73,41)) #Benison Residential Homes
    graph.add_node(173, pos=(67,41)) #Immaculate Conception Chapel
    graph.add_node(172, pos=(65,29)) #Stashery. PH
    graph.add_node(171, pos=(66,31)) #Wing of the Day IlG
    graph.add_node(170, pos=(67,30)) #EUG Trading & Heavy Equip.Rental
    graph.add_node(169, pos=(66,27)) #Crinkle Co.
    graph.add_node(168, pos=(40,18)) #Grewy Goodles
    graph.add_node(167, pos=(63,29)) #The Haven
    graph.add_node(166, pos=(58,45)) #Roya House
    graph.add_node(165, pos=(53,31)) #Masjeed Omar and Islamic Center
    graph.add_node(164, pos=(59,32)) #RTN Shoope
    graph.add_node(163, pos=(54,24)) #Erlinda Ville Tennis Club
    graph.add_node(162, pos=(45,34)) #Corong Computeran
    graph.add_node(161, pos=(37,69)) #Bible Christian Fellowship Iligan
    graph.add_node(160, pos=(38,71)) #Gelvic Cons. & Engr. Services
    graph.add_node(159, pos=(39,71)) #New Life Fellowship
    graph.add_node(158, pos=(38,70)) #Omisol Tire Supply
    graph.add_node(157, pos=(39,70)) #Maranda Law Offices
    graph.add_node(156, pos=(40,71)) #Rojon Pharmacy
    graph.add_node(155, pos=(60,52)) #Nah Yoo Frozen Food Trading
    graph.add_node(154, pos=(49,46)) #Cindy's Dreamy prints
    graph.add_node(153, pos=(44,52)) #Aice Cream
    graph.add_node(152, pos=(44,48)) #Hideout Bar
    graph.add_node(151, pos=(40,49)) #Mags Rooftop garden
    graph.add_node(150, pos=(45,45)) #J's Purified Water Refill Sta.
    graph.add_node(149, pos=(36,49)) #Tata Carenderia
    graph.add_node(148, pos=(30,43)) #FLED dive Center
    graph.add_node(147, pos=(32,44)) #Virtual Team PHL
    graph.add_node(146, pos=(29,44)) #Healthy Nuts
    graph.add_node(145, pos=(28,43)) #Mother of Perpetual Help Academy
    graph.add_node(144, pos=(28,45)) #Arkhanok Letchon Manok House
    graph.add_node(143, pos=(28,46)) #MSU-IIT National Coop. Academy
    graph.add_node(142, pos=(29,64)) #Brgy Hall Sto. Rosario
    graph.add_node(141, pos=(21,66)) #CK Tinting & Wraps
    graph.add_node(140, pos=(30,66)) #Rose Garden Apartelle
    graph.add_node(139, pos=(30,67)) #Shell
    graph.add_node(138, pos=(30,69)) #Diesel Calibration Specialist
    graph.add_node(137, pos=(32,69)) #DRBC Hardware
    graph.add_node(136, pos=(34,69)) #Julie's
    graph.add_node(135, pos=(36,70)) #Dutertech
    graph.add_node(134, pos=(31,60)) #NY PIZZA Delivery Iligan
    graph.add_node(133, pos=(32,63)) #Sto. Rosario Chapel
    graph.add_node(132, pos=(29,63)) #Lulabelle's Home Sweet Home
    graph.add_node(131, pos=(26,60)) #GV8 Food Store
    graph.add_node(130, pos=(28,64)) #Neth Hollow Block Concrete Prod.
    graph.add_node(129, pos=(28,67)) #Michael's Eatery
    graph.add_node(128, pos=(27,66)) #Jekun Val Steel Fabrication
    graph.add_node(127, pos=(25,65)) #Miptronics Enterprises
    graph.add_node(126, pos=(45,25)) #Mirait Depot
    graph.add_node(125, pos=(40,25)) #Don Miguel Detailing
    graph.add_node(124, pos=(40,14)) #ECMA Tech Computer Services
    graph.add_node(123, pos=(40,16)) #Lux Lash Extensions By Sarah
    graph.add_node(122, pos=(34,17)) #Brgy. Del Carmen Multipur. Gym
    graph.add_node(121, pos=(37,20)) #Aida's Frozen Products
    graph.add_node(120, pos=(44,23)) #La Cabrera Mini Store
    graph.add_node(119, pos=(52,26)) #Bunocan's Store
    graph.add_node(222, pos=(53,75)) #Ilgn Tattoo Supplies & Tattoo Shop
    graph.add_node(221, pos=(52,75)) #Bayubay Furniture Shop
    graph.add_node(219, pos=(50,74)) #Bonnies Car Rental
    graph.add_node(220, pos=(51,74)) #Palawan Pawnshop

    random_number = random.randint(3, 5)
    print('random_number: ', random_number)
    djikstrapath = nx.dijkstra_path(graph, start, end)
    shortestpath = [p for p in nx.all_shortest_paths(graph, start, end)]
    print('djikstrapath', djikstrapath)
    print('shortestpath', shortestpath)
    possible_routes = shortestpath[:random_number]
    routes = []
    # insert dijkstra routes first
    routes.append(djikstrapath)

    for route in possible_routes:
        routes.append(route)

    routes = [list(route) for route in set(tuple(route) for route in routes)]
    route_with_establishments = []
    for route in routes:
        edge_establishments = []
        for node in range(len(route)):
            try:
                get_establishment = nodes_within_radius_along_path(graph, route[node], route[node+1])
                
                if route[node] or route[node+1] in route[node].keys():
                    get_establishment.remove(route[node])
                    get_establishment.remove(route[node+1])
                edge_establishments.append(get_establishment)
            except IndexError:
                break
        
        djik_estab = [estab for edge_estab in edge_establishments for estab in edge_estab]
        djik_estab = list(set(djik_estab))

        join_route_estab = [route, djik_estab]

        route_with_establishments.append(join_route_estab)

    return route_with_establishments
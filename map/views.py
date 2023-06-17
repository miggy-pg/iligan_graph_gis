from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
import json
from tablib import Dataset
from .resources import MarkerResource
from .models import Marker
from django.contrib import messages
from map.forms import MarkerForm
from map.forms import UploadMarker
from django.utils.datastructures import MultiValueDictKeyError


# @login_required(login_url="login")
def index(request):
    markers = Marker.objects.filter(type="intersection")
    popup_markers = list(markers.values())

    wet_park = Marker.objects.get(id=6)
    form = MarkerForm(initial = {'wet_park': wet_park })
    upload_form = UploadMarker()

    if request.method == "POST":
        marker_resource = MarkerResource()
        upload_form = UploadMarker(request.POST)
        form = MarkerForm(request.POST)

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
                    value.save()
            except IntegrityError as e:
                messages.add_message(request, messages.INFO, "ERROR: Imported data contain empty rows.")
        
        except MultiValueDictKeyError as e:
            pass


    context = {
        "markers": markers, 
        "form": form,
        "upload_form": upload_form,
        "jsonMarkers": json.dumps(popup_markers)
        }
    return render(request, "index.html", context)

@login_required(login_url="login")
def modifymarker_view(request):
    if request.method == "POST":

        modifyType = request.POST["modifyType"]
        name = request.POST["name"]

        if modifyType == "" or name == "":
            return render(request, "error.html", {"error_name":"Forcing to bypass security, you are not allowed to do that"})

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
                print(f"Adding Marker:{name} at Long: {longitude} and Lat: {latitude}")
            else:
                return render(request, "error.html", {"error_name":"Forcing to bypass security, Invalid value for Longitude and Latitude"})
        elif modifyType == "remove":
            if marker == None:
                return render(request, "error.html", {"error_name":"Marker Name doesn't exist, check your available markers before attempting to remove."})
            else:
                print(f"Removing {name}")
                marker.delete()
        else:
            return render(request, "error.html", {"error_name":"Performing an unidentified action"})

        return redirect("index")
    else:
        return render(request, "error.html", {"error_name":"Performing an unidentified action"})


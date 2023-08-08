from map.models import Marker
from django import forms


class MarkerForm(forms.Form):
    marker_start = forms.ModelChoiceField(
        label="",
        required=False,
        queryset=Marker.objects.filter(type="start_dest"),
    )
    marker_destination = forms.ModelChoiceField(
        label="",
        required=False,
        queryset=Marker.objects.filter(type="start_dest"),
    )

    def __init__(self, *args, **kwargs):
        super(MarkerForm, self).__init__(*args, **kwargs)
        self.fields["marker_start"].widget.attrs.update(
            {"class": "form-select mr-3 mb-3 btn btn-secondary"}
        )
        self.fields["marker_destination"].widget.attrs.update(
            {"class": "form-select mr-3 mb-3 btn btn-secondary"}
        )


class UploadMarker(forms.ModelForm):
    class Meta:
        model = Marker
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(UploadMarker, self).__init__(*args, **kwargs)
        self.fields["type"].widget.attrs.update(
            {"class": "form-select mr-5 btn btn-light"}
        )


class ViewEstablishments(forms.Form):
    ESTABLISHMENT_CHOICES = (
        ("establishment", "Establishment"),
        ("intersection", "Intersection"),
        ("start_dest", "Start/Destination"),
    )

    estab_types = forms.ChoiceField(
        label="Select to view", required=False, choices=ESTABLISHMENT_CHOICES
    )

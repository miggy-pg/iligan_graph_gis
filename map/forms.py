from .models import Marker
from django import forms

class MarkerForm(forms.Form):
    marker_start = forms.ModelChoiceField(label="", initial=Marker.objects.get(id=485), queryset=Marker.objects.filter(type="start_dest"))
    marker_destination = forms.ModelChoiceField(label="", initial=Marker.objects.get(id=485), queryset=Marker.objects.filter(type="start_dest"))

    def __init__(self, *args, **kwargs):
        super(MarkerForm, self).__init__(*args, **kwargs)
        self.fields['marker_start'].widget.attrs.update({'class': 'form-select mr-3 mb-3 btn btn-secondary'})
        self.fields['marker_destination'].widget.attrs.update({'class':'form-select mr-3 mb-3 btn btn-secondary'})

class UploadMarker(forms.ModelForm):
    class Meta:
        model = Marker
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(UploadMarker, self).__init__(*args, **kwargs)
        self.fields['type'].widget.attrs.update({'class': 'form-select mr-5 btn btn-light'})
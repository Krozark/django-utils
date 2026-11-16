"""Sample form of the fluid forms tests."""

from django import forms
from django.forms import CheckboxInput, FileInput, PasswordInput

__all__ = ["SampleForm"]


class SampleForm(forms.Form):
    """Sample form for testing fluid_forms template tags."""

    name = forms.CharField(max_length=100, label="Your Name")
    email = forms.EmailField(label="Email Address")
    password = forms.CharField(widget=PasswordInput(), label="Password")
    message = forms.CharField(widget=forms.Textarea(), label="Message", required=False)
    agree = forms.BooleanField(widget=CheckboxInput(), label="I agree", required=False)
    document = forms.FileField(widget=FileInput(), label="Upload", required=False)

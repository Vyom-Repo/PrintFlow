from django import forms
from .models import PrintOrder


class PrintOrderForm(forms.ModelForm):
    """Form for submitting a print order with document upload."""

    class Meta:
        model = PrintOrder
        fields = ['document', 'side_type', 'color_type', 'layout', 'copies', 'instructions']
        widgets = {
            'document': forms.ClearableFileInput(attrs={
                'class': 'form-input file-input',
                'accept': '.pdf,.jpg,.jpeg,.png',
                'id': 'id_document',
            }),
            'side_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_side_type',
            }),
            'color_type': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_color_type',
            }),
            'layout': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_layout',
            }),
            'copies': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '1',
                'max': '100',
                'value': '1',
                'id': 'id_copies',
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'E.g., "Staple top-left", "Print pages 1-5 only", "Spiral bind"...',
                'id': 'id_instructions',
            }),
        }
        labels = {
            'document': 'Upload Document',
            'side_type': 'Printing Side',
            'color_type': 'Color Option',
            'layout': 'Page Layout',
            'copies': 'Number of Copies',
            'instructions': 'Special Instructions',
        }

    def clean_copies(self):
        copies = self.cleaned_data.get('copies')
        if copies is None or copies < 1:
            raise forms.ValidationError('Number of copies must be at least 1.')
        if copies > 100:
            raise forms.ValidationError('Maximum 100 copies per order.')
        return copies

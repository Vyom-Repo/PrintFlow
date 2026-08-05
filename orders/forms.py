from django import forms
from .models import PrintOrder


class PrintOrderForm(forms.ModelForm):
    """Form for submitting a print order with document upload."""

    # -----------------------------------------------------------------------
    # Non-model fields for page selection
    # These are handled in the view and written manually to the model instance.
    # -----------------------------------------------------------------------

    PRINT_MODE_CHOICES = [
        ('all', 'Print All Pages'),
        ('specific', 'Print Specific Pages'),
    ]

    print_mode = forms.ChoiceField(
        choices=PRINT_MODE_CHOICES,
        initial='all',
        required=True,
        widget=forms.RadioSelect(attrs={
            'class': 'print-mode-radio',
            'id': 'id_print_mode',
        }),
        label='Print Pages',
    )

    page_selection = forms.CharField(
        required=False,
        max_length=255,
        label='Pages to Print',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'id': 'id_page_selection',
            'placeholder': 'e.g. 5-19 or 1,3,5-10',
            'autocomplete': 'off',
        }),
        help_text=(
            'Enter page numbers or ranges separated by commas. '
            'Example: 1-5,8,11-13'
        ),
    )

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
                'placeholder': 'E.g., "Staple top-left", "Spiral bind"...',
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

    def clean(self):
        """
        Cross-field validation for the print-mode / page-selection combo.

        Full page-range validation (against total_pages) cannot happen here
        because the form does not know the PDF page count — that is done in
        the view after the file is read.
        """
        cleaned = super().clean()
        print_mode = cleaned.get('print_mode')
        page_selection = cleaned.get('page_selection', '').strip()

        if print_mode == 'specific' and not page_selection:
            self.add_error(
                'page_selection',
                'Please enter the pages you want to print (e.g. 5-19 or 1,3,5-10).'
            )

        return cleaned

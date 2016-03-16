from django import forms

ECOSYSTEM_CHOICES = (
    ("all", "All Ecosystem"),
    ("animal", "Animal/Human"),
    ("anthropogenic", "Anthropogenic"),
    ("freshwater", "Freshwater"),
    ("marine", "Marine"),
    ("soil", "Soil"),
    ("plant", "Plant"),
    ("geothermal", "Geothermal"),
    ("biofilm", "Biofilm"),
)


class BiomSearchForm(forms.Form):
    otu_text = forms.CharField(
        initial="Paste OTU table here",
        label="Paste your BIOM table",
        widget=forms.Textarea(
            attrs={'cols': 30, 'rows': 12}
        ),
    )
    otu_file = forms.FileField(
        label="or upload your BIOM file",
    )
    selection_criteria = forms.MultipleChoiceField(
        label="Select the Ecosystem",
        choices=ECOSYSTEM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

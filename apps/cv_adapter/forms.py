from django import forms
from .models import CVBase, JobApplication


class CVUploadForm(forms.ModelForm):
    class Meta:
        model = CVBase
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'accept': '.pdf,.docx,.doc',
                'class': 'file-input',
            }),
        }

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if f:
            ext = f.name.rsplit('.', 1)[-1].lower()
            if ext not in ('pdf', 'docx', 'doc'):
                raise forms.ValidationError('Only PDF and DOCX files are accepted.')
            if f.size > 5 * 1024 * 1024:  # 5 MB
                raise forms.ValidationError('File size must not exceed 5 MB.')
        return f


class CVPasteForm(forms.Form):
    """Form for pasting CV text directly (no file upload)."""
    cv_name = forms.CharField(
        max_length=255,
        label='CV name',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. My Software Engineer CV'}),
    )
    pasted_text = forms.CharField(
        label='CV text',
        widget=forms.Textarea(attrs={
            'rows': 18,
            'placeholder': 'Paste the full text of your CV here…',
        }),
        min_length=100,
        error_messages={'min_length': 'CV text seems too short. Please paste the complete content.'},
    )


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cv_base', 'job_description']
        widgets = {
            'cv_base': forms.Select(attrs={'class': 'input-field'}),
            'job_description': forms.Textarea(attrs={
                'class': 'input-field font-mono text-sm',
                'rows': 14,
                'placeholder': 'Paste the full job description here\u2026',
            }),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cv_base'].queryset = CVBase.objects.filter(user=user)
        self.fields['cv_base'].empty_label = '— select a CV —'

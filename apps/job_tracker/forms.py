from django import forms
from .models import JobApplication


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['job_title', 'company', 'status', 'link_vaga',
                  'salario_estimado', 'job_description', 'notas']
        widgets = {
            'job_title':        forms.TextInput(attrs={'placeholder': 'e.g. Senior Python Developer'}),
            'company':          forms.TextInput(attrs={'placeholder': 'e.g. Acme Corp'}),
            'status':           forms.Select(),
            'link_vaga':        forms.URLInput(attrs={'placeholder': 'https://...'}),
            'salario_estimado': forms.TextInput(attrs={'placeholder': 'e.g. R$ 8.000 – 12.000'}),
            'job_description':  forms.Textarea(attrs={'rows': 5, 'placeholder': 'Optional: paste the JD text'}),
            'notas':            forms.Textarea(attrs={'rows': 4, 'placeholder': 'Notes, contacts, next steps…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (
                existing + ' w-full bg-gray-700 border border-gray-600 text-white '
                'placeholder-gray-400 rounded-xl px-4 py-3 focus:outline-none '
                'focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
            ).strip()


class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['status', 'notas']
        widgets = {
            'status': forms.Select(),
            'notas':  forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (
                existing + ' w-full bg-gray-700 border border-gray-600 text-white '
                'placeholder-gray-400 rounded-xl px-4 py-3 focus:outline-none '
                'focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition'
            ).strip()

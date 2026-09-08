from django import forms

from knowledge.models import KnowledgeDocument


class KnowledgeUploadForm(forms.ModelForm):
    class Meta:
        model = KnowledgeDocument
        fields = ("title", "file")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например, Поступление 2026"}),
            "file": forms.ClearableFileInput(attrs={"accept": ".txt,.md,.text"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].required = True
        self.fields["title"].required = True


class KnowledgeTextForm(forms.Form):
    title = forms.CharField(label="Название", max_length=255)
    content = forms.CharField(
        label="Текст",
        widget=forms.Textarea(attrs={"rows": 10, "placeholder": "Вставьте материал для базы знаний"}),
    )

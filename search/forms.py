from django import forms
from haystack.forms import SearchForm
from wehaveweneed.web.models import Category


class CategoryChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return obj.name


class PostSearchForm(SearchForm):
    """ Our search form.

    """

    have = forms.BooleanField(initial=True, required=False)
    need = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super(PostSearchForm, self).__init__(*args, **kwargs)
        choices = ((' ', 'all categories'),) + tuple(Category.objects.values_list('slug', 'name'))
        self.fields['category'] = forms.ChoiceField(required=True, choices=choices)

    def search(self):
        
        if self.is_valid():
            if self.cleaned_data['q'].strip():
                sqs = self.searchqueryset.auto_query(self.cleaned_data['q'])
            else:
                sqs = self.searchqueryset.all()
        else:
            return []

        sqs = sqs.filter(fulfilled=False)
        
        category = self.cleaned_data.get('category')
        if category and category.strip():
            sqs = sqs.filter(category=category)
        
        have = self.cleaned_data['have']
        need = self.cleaned_data['need']
        if have and not need:
            sqs = sqs.filter(type='have')
        if need and not have:
            sqs = sqs.filter(type='need')
        
        if self.load_all:
            sqs = sqs.load_all()

        return sqs






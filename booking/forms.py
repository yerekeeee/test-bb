# booking/forms.py

from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    # Явно определяем поле рейтинга здесь
    rating = forms.ChoiceField(
        choices=[(5, 5), (4, 4), (3, 3), (2, 2), (1, 1)], # Ровно 5 звезд, в обратном порядке
        widget=forms.RadioSelect(
            attrs={'class': 'star-rating-container'}
        ),
        label="Ваша оценка"
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Поделитесь вашими впечатлениями...'}),
        }
        labels = {
            'comment': 'Комментарий'
        }
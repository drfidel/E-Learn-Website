from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=[(User.Role.STUDENT, 'Student'), (User.Role.INSTRUCTOR, 'Instructor')])

    class Meta:
        model = User
        fields = ['email', 'username', 'role', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        return email.strip().lower()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'photo',
            'first_name',
            'last_name',
            'headline',
            'phone_number',
            'country',
            'city',
            'website',
            'linkedin_url',
            'bio',
            'learning_goals',
            'qualifications',
        ]
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Backend Developer | Python Instructor'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 555 123 4567'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://yourwebsite.com'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/yourname'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell learners about yourself'}),
            'learning_goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are you currently learning or improving?'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Certifications, achievements, work experience'}),
        }


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'current-password'}
        )
    )

    error_messages = {
        'invalid_login': 'Invalid email or password. Please try again.',
        'inactive': 'This account is inactive.',
    }

    def clean_username(self):
        email = self.cleaned_data.get('username', '')
        return email.strip().lower()

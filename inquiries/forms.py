from django import forms
from .models import Lead, Agent
from django.contrib.auth.models import User
from datetime import date


class InquiryForm(forms.ModelForm):
    assigned_agent = forms.ModelChoiceField(queryset=Agent.objects.all(), required=True)
    
    class Meta:
        model = Lead
        fields = ['student_name','parent_name','mobile_number','email','address','location_tag','inquiry_source','student_class','status','remarks','inquiry_date','follow_up_date','registration_date','admission_test_date','admission_offered_date','admission_confirmed_date','rejected_date','assigned_agent','admin_assigned']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Assign the 'date' widget to the date fields individually
        date_fields = [
            'inquiry_date', 'follow_up_date', 'registration_date', 
            'admission_test_date', 'admission_offered_date', 
            'admission_confirmed_date', 'rejected_date'
        ]
        for field in date_fields:
            self.fields[field].widget = forms.DateInput(attrs={'type': 'date'})
            

class ManageLeadStatusForm(forms.ModelForm):
    assigned_agent = forms.ModelChoiceField(queryset=Agent.objects.all(), required=False)
    
    class Meta:
        model = Lead
        fields = ['assigned_agent', 'status','remarks','inquiry_date','follow_up_date','registration_date','admission_test_date','admission_offered_date','admission_confirmed_date','rejected_date','assigned_agent','admin_assigned']
        
        
        
class ReassignLeadForm(forms.ModelForm):
    assigned_agent = forms.ModelChoiceField(queryset=User.objects.filter(is_staff=True), required=True)

    class Meta:
        model = Lead
        fields = ['assigned_agent']
        

        
class RemoveAgentForm(forms.Form):
    lead = forms.ModelChoiceField(
        queryset=Lead.objects.none(),  # We'll set the queryset dynamically
        empty_label="Select a lead to remove",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        agent = kwargs.pop('agent', None)
        super(RemoveAgentForm, self).__init__(*args, **kwargs)
        if agent:            
            self.fields['lead'].queryset = Lead.objects.filter(assigned_agent=agent)
            
            
            
class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ['name', 'email', 'performance_score']
        widgets = {
            'performance_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),  # Optional: Limit score to a range
        }
        labels = {
            'name': 'Agent Name',
            'email': 'Email Address',
            'performance_score': 'Performance Score (0-100)',
        }
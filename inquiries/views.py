from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Lead, Agent
from cities_light.models import City
from .forms import InquiryForm, ManageLeadStatusForm, ReassignLeadForm, RemoveAgentForm, AgentForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import date, timedelta
import csv
from django.http import HttpResponse
from django.core.mail import send_mail
from django.utils.timezone import now
from django.contrib import messages
from openpyxl import Workbook
from django.db.models import Count, Q, DateField, F
from django.db.models.functions import TruncDate
from django.conf import settings



# Function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_staff  # Only allow staff users (admins)



def agent_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate user based on email and password
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_staff:  # Check if user is admin (staff user)
                print("===============> Admin logged in\n")
                login(request, user)
                return redirect('dashboard')  # Redirect to the admin dashboard (or any other page)

            try:
                print("===============> Agent logged in\n")
                # Check if the authenticated user is an Agent
                agent = user.agent  # This will work only for users who are agents
                login(request, user)
                return redirect('inquiry_list')  # Redirect to the agent's dashboard or inquiry list
            except Agent.DoesNotExist:
                messages.error(request, 'This account is not an agent.')
                return redirect('agent_login')  # Stay on the login page

        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'inquiries/agent_login.html')



@login_required
def inquiry_list(request):
    user = request.user
    if user.is_staff:  # Admins can see all inquiries
        inquiries = Lead.objects.all()
    else:  # Agents can only see inquiries where they are the assigned agent
        # Ensure that the user is an agent and filter based on the assigned_agent
        inquiries = Lead.objects.filter(assigned_agent__user=user)
    
    # Search and filtering logic
    search_query = request.GET.get('q', '')
    if search_query:
        inquiries = inquiries.filter(
            Q(student_name__icontains=search_query) |
            Q(parent_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Add filters for student_class and admin_assigned
    student_class_filter = request.GET.get('student_class', '')
    if student_class_filter:
        inquiries = inquiries.filter(student_class=student_class_filter)

    admin_assigned_filter = request.GET.get('admin_assigned', '')
    if admin_assigned_filter:
        inquiries = inquiries.filter(admin_assigned_id=admin_assigned_filter)

    # Other existing filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        inquiries = inquiries.filter(status=status_filter)

    assigned_agent_filter = request.GET.get('agent', '')
    if assigned_agent_filter:
        inquiries = inquiries.filter(assigned_agent_id=assigned_agent_filter)
    
    location_filter = request.GET.get('location_tag', '')
    if location_filter:
        inquiries = inquiries.filter(location_tag__icontains=location_filter)

    inquiry_source_filter = request.GET.get('inquiry_source', '')
    if inquiry_source_filter:
        inquiries = inquiries.filter(inquiry_source__icontains=inquiry_source_filter)
        
    # Populate options for filtering dropdowns
    agents = Agent.objects.all()
    locations = City.objects.all()
    inquiry_sources = Lead.objects.values_list('inquiry_source', flat=True).distinct()
    statuses = Lead.objects.values_list('status', flat=True).distinct()
    student_classes = Lead.objects.values_list('student_class', flat=True).distinct()  # Populate student_class options
    admins = User.objects.filter(is_staff=True)  # Populate admin_assigned options (only staff users)

    return render(request, 'inquiries/inquiry_list.html', {
        'inquiries': inquiries,
        'agents': agents,
        'locations': locations,
        'inquiry_sources': inquiry_sources,
        'statuses': statuses,
        'student_classes': student_classes,
        'admins': admins,  # Add admins to template context
    })




@login_required
@user_passes_test(is_admin)
def add_inquiry(request):
    if request.method == 'POST':
        form = InquiryForm(request.POST)

        if form.is_valid():
            inquiry = form.save()  # Save the inquiry instance

            # Get the assigned agent
            assigned_agent = inquiry.assigned_agent

            # Email recipient list
            recipient_list = []  # Default recipient email(s)
            if assigned_agent and assigned_agent.email:
                recipient_list.append(assigned_agent.email)
                send_mail(
                    subject='New Inquiry Arrived',
                    message=f'A new inquiry has arrived.\n\nDetails:\n{inquiry}',
                    from_email='sushant889427@gmail.com',  # Sender email
                    recipient_list=recipient_list,  # Recipient email(s)
                    fail_silently=False,
                )                        
            
            return redirect('inquiry_list')
    else:
        form = InquiryForm()
    return render(request, 'inquiries/add_inquiry.html', {'form': form})



@login_required
def manage_lead_status(request, inquiry_id):
    # Fetch the Lead instance for the given inquiry_id
    inquiry = get_object_or_404(Lead, id=inquiry_id)

    if request.method == 'POST':
        # Bind the form with POST data and the current inquiry instance
        form = ManageLeadStatusForm(request.POST, instance=inquiry)
        
        if form.is_valid():
            form.save()  # Save the form with updated values
            
            # Optionally, add logic for email notifications or additional actions here
            
            return redirect('inquiry_list')  # Redirect back to the inquiry list after saving
    else:
        # Prefill form with the inquiry's current details
        form = ManageLeadStatusForm(initial={
            'status': inquiry.status,
            'remarks': inquiry.remarks,
            'follow_up_date': inquiry.follow_up_date,
            'inquiry_date': inquiry.inquiry_date,
            'registration_date': inquiry.registration_date,
            'admission_test_date': inquiry.admission_test_date,
            'admission_offered_date': inquiry.admission_offered_date,
            'admission_confirmed_date': inquiry.admission_confirmed_date,
            'rejected_date': inquiry.rejected_date,
            'assigned_agent': inquiry.assigned_agent,
            'admin_assigned': inquiry.admin_assigned,
        }, instance=inquiry)  # Ensure form is tied to the existing instance

    return render(request, 'inquiries/next_follow_up.html', {'form': form, 'inquiry': inquiry})




@login_required
@user_passes_test(is_admin)  # Restrict access to admins
def remove_agent_view(request):
    if request.method == 'POST':
        # print("===============> request.POST = ",request.POST)
        lead_id = request.POST.get('lead_id')  # Get the lead ID from the form
        
        print("===============> lead_id = ",lead_id)
        if not lead_id:
            messages.error(request, "Please select a lead to remove.")
            return redirect('remove_lead')
        
        lead = get_object_or_404(Lead, id=lead_id)
        lead.assigned_agent = None  # Remove the assigned agent
        
        lead.save()  # Save the updated object to the database
        
        # Add a success message
        messages.success(request, "Lead successfully removed from the agent.")
        
        return redirect('remove_lead')  # Redirect to the same page after removal
    
    else:
        agents = Agent.objects.prefetch_related('lead_set').all()  # Fetch agents and their leads        
        return render(request, 'inquiries/remove_lead.html', {'agents': agents})



@login_required
def dashboard(request):
    user = request.user  # Get the logged-in user

    # Get all inquiries if user is admin, else filter by assigned_agent
    if user.is_staff:  
        inquiries = Lead.objects.all()  # Admin sees all
    else:
        inquiries = Lead.objects.filter(assigned_agent__user=user)  # Agent sees only their assigned inquiries

    # Overall Counts
    total_inquiries = inquiries.filter(status='Inquiry').count()
    total_registrations = inquiries.filter(status='Registration').count()
    total_tests = inquiries.filter(status='Admission Test').count()
    total_admissions_offered = inquiries.filter(status='Admission Offered').count()
    total_admissions_confirmed = inquiries.filter(status='Admission Confirmed').count()
    rejected = inquiries.filter(status='Rejected').count()
        
    # Today's Counts
    today = now().date()
    inquiries_today = inquiries.filter(status='Inquiry', inquiry_date=today).count()
    registrations_today = inquiries.filter(status='Registration', registration_date=today).count()
    tests_today = inquiries.filter(status='Admission Test', admission_test_date=today).count()
    admissions_offered_today = inquiries.filter(status='Admission Offered', admission_confirmed_date=today).count()
    admissions_confirmed_today = inquiries.filter(status='Admission Confirmed', admission_confirmed_date=today).count()
    rejected_today = inquiries.filter(status='Rejected', admission_confirmed_date=today).count()

    # Counts by Student Class
    inquiries_by_class = inquiries.values('student_class').annotate(total=Count('id')).order_by('-total')

    # Counts by Inquiry Source
    inquiries_by_source = inquiries.values('inquiry_source').annotate(total=Count('id')).order_by('-total')

    # Counts by Location (City)
    inquiries_by_location = inquiries.values('location_tag__name').annotate(total=Count('id')).order_by('-total')

    # Inquiry Trends (Last 7 Days)
    recent_trends = inquiries.filter(inquiry_date__gte=today - timedelta(days=7)).annotate(
        day=TruncDate('inquiry_date')
    ).values('day').annotate(total=Count('id')).order_by('day')

    # Most Recent Inquiries (Last 5)
    recent_inquiries = inquiries.order_by('-inquiry_date')[:5]

    context = {
        # Overall Stats
        'total_inquiries': total_inquiries,
        'total_registrations': total_registrations,
        'total_tests': total_tests,
        'total_admissions_offered': total_admissions_offered,
        'total_admissions_confirmed': total_admissions_confirmed,
        'rejected': rejected,

        # Today's Stats
        'inquiries_today': inquiries_today,
        'registrations_today': registrations_today,
        'tests_today': tests_today,
        'admissions_offered_today': admissions_offered_today,
        'admissions_confirmed_today': admissions_confirmed_today,
        'rejected_today': rejected_today,

        # Detailed Stats
        'inquiries_by_class': inquiries_by_class,
        'inquiries_by_source': inquiries_by_source,
        'inquiries_by_location': inquiries_by_location,

        # Trends and Recent Activity
        'recent_trends': recent_trends,
        'recent_inquiries': recent_inquiries,
    }

    return render(request, 'inquiries/dashboard.html', context)



@login_required
def agent_performance(request):
    user = request.user  # Get the logged-in user

    # If the user is an admin, get all agents; otherwise, get only the logged-in agent
    if user.is_staff:
        agents = Agent.objects.all()  # Admins see all agents
    else:
        agents = Agent.objects.filter(user=user)  # Agents see only their own data

    # Initialize list to store agent performance data
    agent_data = []

    for agent in agents:
        # Total Leads Assigned
        total_leads = Lead.objects.filter(assigned_agent=agent).count()

        # Leads Converted to Registration
        leads_to_registration = Lead.objects.filter(assigned_agent=agent, status='Registration').count()

        # Leads Converted to Admission Offered
        leads_to_admission_offered = Lead.objects.filter(assigned_agent=agent, status='Admission Offered').count()

        # Leads Converted to Admission Confirmed
        leads_to_admission_confirmed = Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed').count()

        # Leads Rejected
        leads_rejected = Lead.objects.filter(assigned_agent=agent, status='Rejected').count()

        # Conversion Rates (Admission Offered and Confirmed)
        conversion_rate = (leads_to_admission_offered + leads_to_admission_confirmed) / total_leads * 100 if total_leads > 0 else 0

        # Follow-Up Efficiency (leads with follow-up date set)
        leads_with_follow_up = Lead.objects.filter(assigned_agent=agent, follow_up_date__isnull=False).count()
        follow_up_efficiency = (leads_with_follow_up / total_leads * 100) if total_leads > 0 else 0

        # Average Time to Conversion (from Inquiry to Admission Confirmed)
        total_days_to_conversion = sum(
            (lead.admission_confirmed_date - lead.inquiry_date).days
            for lead in Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed')
            if lead.inquiry_date and lead.admission_confirmed_date
        )
        conversions_count = Lead.objects.filter(assigned_agent=agent, status='Admission Confirmed').count()
        average_days_to_conversion = total_days_to_conversion / conversions_count if conversions_count else 0

        # Leads Remaining in Pending Status (still in Inquiry or Follow-up)
        leads_in_pending = Lead.objects.filter(assigned_agent=agent, status__in=['Inquiry', 'Follow-up']).count()

        # Collect data for each agent
        agent_data.append({
            'agent': agent,
            'total_leads': total_leads,
            'leads_to_registration': leads_to_registration,
            'leads_to_admission_offered': leads_to_admission_offered,
            'leads_to_admission_confirmed': leads_to_admission_confirmed,
            'leads_rejected': leads_rejected,
            'conversion_rate': conversion_rate,
            'follow_up_efficiency': follow_up_efficiency,
            'average_days_to_conversion': average_days_to_conversion,
            'leads_in_pending': leads_in_pending
        })

    # Sort agents by performance (conversion rate as example)
    agent_data = sorted(agent_data, key=lambda x: x['conversion_rate'], reverse=True)

    # Render the performance template
    return render(request, 'inquiries/agent_performance.html', {'agent_data': agent_data})




@login_required
def export_inquiries_excel(request):
    user = request.user  # Get the logged-in user

    # If the user is an admin, get all inquiries; otherwise, get only the logged-in agent's inquiries
    if user.is_staff:
        inquiries = Lead.objects.all()
    else:
        inquiries = Lead.objects.filter(assigned_agent__user=user)  # Filter only assigned inquiries for the agent

    # Create a workbook and select the active worksheet
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Inquiries"

    # Add the header row
    headers = [
        'Student Name', 'Parent Name', 'Mobile Number', 'Email', 'Address',
        'Location', 'Inquiry Source', 'Student Class', 'Status',
        'Remarks', 'Inquiry Date', 'Follow-up Date', 'Registration Date',
        'Admission Test Date', 'Admission Offered Date', 'Admission Confirmed Date',
        'Rejected Date', 'Assigned Agent', 'Admin Assigned'
    ]
    worksheet.append(headers)

    # Add inquiry data to the worksheet
    for inquiry in inquiries:
        worksheet.append([
            inquiry.student_name,
            inquiry.parent_name,
            inquiry.mobile_number,
            inquiry.email,
            inquiry.address,
            inquiry.location_tag.name if inquiry.location_tag else "N/A",
            inquiry.inquiry_source,
            inquiry.student_class,
            inquiry.status,
            inquiry.remarks or "N/A",
            inquiry.inquiry_date if inquiry.inquiry_date else "N/A",
            inquiry.follow_up_date if inquiry.follow_up_date else "N/A",
            inquiry.registration_date if inquiry.registration_date else "N/A",
            inquiry.admission_test_date if inquiry.admission_test_date else "N/A",
            inquiry.admission_offered_date if inquiry.admission_offered_date else "N/A",
            inquiry.admission_confirmed_date if inquiry.admission_confirmed_date else "N/A",
            inquiry.rejected_date if inquiry.rejected_date else "N/A",
            inquiry.assigned_agent.name if inquiry.assigned_agent else "N/A",
            inquiry.admin_assigned.username if inquiry.admin_assigned else "N/A"
        ])

    # Set the response content type and save the workbook to the response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="inquiries.xlsx"'

    workbook.save(response)
    return response



@login_required
@user_passes_test(is_admin)
def assign_lead(request):
    inquiries = Lead.objects.filter(assigned_agent__isnull=True)  # Fetch unassigned inquiries
    agents = Agent.objects.all()  # Fetch all agents

    if request.method == 'POST':
        inquiry_id = request.POST.get('inquiry_id')  # Get selected inquiry ID
        agent_id = request.POST.get('agent_id')  # Get selected agent ID

        # Validate input
        if not inquiry_id or not agent_id:
            messages.error(request, "Please select both an inquiry and an agent.")
            return redirect('assign_lead')

        try:
            # Get the inquiry and agent objects
            inquiry = get_object_or_404(Lead, id=inquiry_id)
            agent = get_object_or_404(Agent, id=agent_id)

            # Assign the agent to the inquiry
            inquiry.assigned_agent = agent
            inquiry.save()

            # Provide success feedback to the user
            messages.success(request, f"Inquiry for '{inquiry.student_name}' has been successfully assigned to Agent '{agent.name}'.")
        except Exception as e:
            # Handle unexpected errors gracefully
            messages.error(request, f"An error occurred while assigning the lead: {str(e)}")

        return redirect('assign_lead')  # Redirect to the same page after assignment

    # Add filters for convenience (optional)
    search_query = request.GET.get('q', '')
    if search_query:
        inquiries = inquiries.filter(
            Q(student_name__icontains=search_query) |
            Q(parent_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )

    return render(request, 'inquiries/assign_lead.html', {
        'inquiries': inquiries,
        'agents': agents
    })
    
    
@login_required
@user_passes_test(is_admin)
def delete_inquiry(request, id):
    # Get the inquiry by ID
    inquiry = get_object_or_404(Lead, id=id)

    # Delete the inquiry
    inquiry.delete()

    # Add a success message
    messages.success(request, "Inquiry deleted successfully!")

    # Redirect to the inquiry list
    return redirect('inquiry_list')
    

# Helper function to send the email with the default password
def send_agent_welcome_email(agent, default_password):
    subject = "Welcome to the Team!"
    message = f"Hello {agent.name},\n\n" \
              f"Your agent account has been created successfully.\n\n" \
              f"Here are your login credentials:\n" \
              f"Email: {agent.email}\n" \
              f"Password: {default_password}\n\n" \
              f"Please login and change your password after the first login.\n\n" \
              f"Best regards,\nThe Team"
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,  # Default email set in settings.py
        recipient_list=[agent.email],
        fail_silently=False,
    )


# View to add agent
@login_required
@user_passes_test(is_admin)  # Make sure only admin can access this
def add_agent(request):
    if request.method == 'POST':
        form = AgentForm(request.POST)
        if form.is_valid():
            # Get the form data
            agent_name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            performance_score = form.cleaned_data['performance_score']
            
            # Create the User for the agent with a default password
            default_password = 'DefaultPassword123!'  # Set a default password
            
            user = User.objects.create_user(username=email, email=email, password=default_password)

            # Create the agent object and associate with the user
            agent = form.save(commit=False)  # Don't save yet; we need to associate it with the user
            agent.user = user  # Associate the user
            agent.save()

            # Send the email with the default password
            send_agent_welcome_email(agent, default_password)

            # Show success message
            messages.success(request, f"Agent '{agent.name}' added successfully! The default password has been sent to their email.")
            return redirect('add_agent')  # Redirect to the same page after success
        else:
            messages.error(request, "Error adding agent. Please correct the errors below.")
    else:
        form = AgentForm()

    return render(request, 'inquiries/add_agent.html', {'form': form})



@login_required
@user_passes_test(is_admin)
def agent_list(request):
    # Get filter query parameters
    name_filter = request.GET.get('name', '')
    email_filter = request.GET.get('email', '')
    min_score_filter = request.GET.get('min_score', '')
    max_score_filter = request.GET.get('max_score', '')

    # Filter agents based on the query parameters
    agents = Agent.objects.all()

    if name_filter:
        agents = agents.filter(name__icontains=name_filter)
    if email_filter:
        agents = agents.filter(email__icontains=email_filter)
    if min_score_filter:
        agents = agents.filter(performance_score__gte=min_score_filter)
    if max_score_filter:
        agents = agents.filter(performance_score__lte=max_score_filter)

    # Handle deletion of agents
    if request.method == 'POST':  # Handle agent deletion
        agent_id = request.POST.get('agent_id')  # Get the agent ID from the form
        agent = get_object_or_404(Agent, id=agent_id)
        agent.delete()
        messages.success(request, f"Agent '{agent.name}' has been deleted successfully.")
        return redirect('agent_list')  # Refresh the agent list after deletion

    return render(request, 'inquiries/agent_list.html', {
        'agents': agents,
        'name_filter': name_filter,
        'email_filter': email_filter,
        'min_score_filter': min_score_filter,
        'max_score_filter': max_score_filter,
    })
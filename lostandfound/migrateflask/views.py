from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from .models import Item
from .forms import RegisterForm, LoginForm, ItemForm, SearchForm,ContactForm
from datetime import datetime
import re
import json




User = get_user_model()
def index(request):
    return render(request, 'index.html')




@login_required
def dashboard(request):
    return render(request, 'dashboard.html')



@login_required
def search_view(request):
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    date = request.GET.get('date', '')
    location = request.GET.get('location', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort_by', '')

    # Start with all items
    items = Item.objects.all()

    # Build Q filters with AND logic for precision
    filters = Q()

    # Apply filters only if fields are provided
    if search:
        filters &= (Q(name__icontains=search) | Q(description__icontains=search))
    if category:
        filters &= Q(category__iexact=category)
    if date:
        filters &= Q(date=date)
    if location:
        filters &= Q(location__icontains=location)
    if status:
        filters &= Q(status__iexact=status)

    # Apply the combined filters
    if any([search, category, date, location, status]):
        items = items.filter(filters)

    # Apply sorting if provided
    if sort_by:
        items = items.order_by(sort_by)

    return render(request, 'search.html', {
        'items': items,
        'search': search,
        'category': category,
        'date': date,
        'location': location,
        'status': status,
        'sort_by': sort_by,
    })

def register_view(request):
    form_data = {}  
    if request.method == 'POST':
        username = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')
        mobile = request.POST.get('phone')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        dob_str = request.POST.get('dob')
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

        form_data = {
            'name': username,
            'email': email,
            'phone': mobile,
            'address': address,
            'gender': gender,
            'dob': dob,
        }

        has_error = False

        if not username:
            messages.error(request, 'Username is required.')
            has_error = True
        if not email:
            messages.error(request, 'Email is required.')
            has_error = True
        if not password:
            messages.error(request, 'Password is required.')
            has_error = True
        if not cpassword:
            messages.error(request, 'Confirm password is required.')
            has_error = True
        if not mobile:
            messages.error(request, 'Mobile number is required.')
            has_error = True

        if password and cpassword and password != cpassword:
            messages.error(request, 'Passwords do not match.')
            has_error = True

        if username and User.objects.filter(name=username).exists():
            messages.error(request, 'Username already exists.')
            has_error = True

        if email and User.objects.filter(email=email).exists():
            messages.error(request, 'Email already used.')
            has_error = True

        if mobile:
            if not re.fullmatch(r'\d{10,15}', mobile):
                messages.error(request, 'Enter a valid mobile number (10 to 15 digits).')
                has_error = True
            elif User.objects.filter(phone=mobile).exists():
                messages.error(request, 'Mobile number already registered.')
                has_error = True

        # Password complexity checks
        if password:
            password_errors = []
            if len(password) < 8:
                password_errors.append("Password must be at least 8 characters long.")
            if not re.search(r"[A-Z]", password):
                password_errors.append("Password must contain at least one uppercase letter.")
            if not re.search(r"[a-z]", password):
                password_errors.append("Password must contain at least one lowercase letter.")
            if not re.search(r"\d", password):
                password_errors.append("Password must contain at least one digit.")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                password_errors.append("Password must contain at least one special character (!@#$%^&* etc).")

            if password_errors:
                for err in password_errors:
                    messages.error(request, err)
                has_error = True

        if not has_error:
            try:
                validate_password(password)
                user = User.objects.create_user(
    email=email,
    name=username,  # this replaces 'username'
    phone=mobile,
    address=address,
    gender=gender,
    dob=dob,
    password=password
                    
                )
                # Assign other fields if custom User model has them
                user.phone = mobile
                user.address = address
                user.gender = gender
                user.dob = dob

                user.save()

                messages.success(request, 'Registration successful! You can now login.')
                return redirect('login')

            except ValidationError as e:
                for error in e:
                    messages.error(request, error)
            except Exception as e:
              messages.error(request, f'Something went wrong: {e}')


    return render(request, 'register.html', {'form_data': form_data})





def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome, {user.name}! You have successfully logged in.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')  # ✅ Use the named URL pattern

    return render(request, 'login.html')



def report_item(request, status="lost"):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category = request.POST.get('category')
        date_string = request.POST.get('date_string')  # Fixed input name
        location = request.POST.get('location')
        image = request.FILES.get('image')

        try:
            # Validate and Convert Date
            if date_string:
                date = datetime.strptime(date_string, "%Y-%m-%d").date()
            else:
                return HttpResponse("Error: Date is required.")

            # Create Item Object
            item = Item.objects.create(
                name=name,
                description=description,
                category=category,
                date=date,
                location=location,
                image=image,
                status=status,  # Assign status dynamically
                user=request.user
            )

            print(f"Item saved successfully: {item}")  # Debug message

            return redirect('login')  # Redirect after successful save
        
        except Exception as e:
            print(f"Error reporting item: {str(e)}")  # Debug error log
            return HttpResponse(f"Error reporting item: {str(e)}")

    return render(request, 'dashboard.html')




@login_required
def gallery(request):
    items = Item.objects.all()
    return render(request, 'gallery.html', {'items': items})



from django.contrib import messages


def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == 'POST':
        item.name = request.POST['item_name']
        item.description = request.POST['description']
        item.category = request.POST['category']
        item.date = request.POST['date']
        item.location = request.POST['location']
        item.status = request.POST['status']

        if 'image' in request.FILES:
            item.image = request.FILES['image']

        item.save()

        messages.success(request, 'Item updated successfully!')
        return redirect('gallery')

    return render(request, 'edit_item.html', {'item': item})






@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    messages.success(request, "Item deleted successfully!")
    return redirect('gallery')


from django.core.mail import send_mail
from django.conf import settings


@login_required
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save()

            # Send confirmation email
            subject = "✅ Claim Submission Received – LostNoMore"
            message = f"""
Hi {claim.name},

Thank you for submitting a claim for the lost item.

Here are the details you submitted:
- Item Name: {claim.product}
- Description: {claim.description}
- Location Lost: {claim.location}
- Date: {claim.date}
- Your Phone: {claim.phone}

Our team will review the details and contact you shortly through a phone call. 
You can expect an update within the next 36 hours if the item is found.

Thanks for trusting LostNoMore.

Warm regards,  
LostNoMore Team  
{settings.DEFAULT_FROM_EMAIL}
"""

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [claim.email],
                fail_silently=False,
            )

            messages.success(request, 'Your claim has been submitted successfully!')
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})



@login_required
def profile(request):
    user_role = 'admin' if request.user.is_superuser else 'user'
    return render(request, 'profile.html', {'user': request.user, 'role': user_role})

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        user.name = request.POST.get('name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        # user.role is not updated since it's readonly

        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('edit_profile')

    return render(request, 'edit_profile.html', {'user': user, 'role': user.role})




# @login_required
# @csrf_exempt
# def claim_item(request, item_id):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             email = data.get('email')
#             phone = data.get('phone')

#             if not email or not phone:
#                 return JsonResponse({'status': 'error', 'message': 'Missing email or phone.'})

#             item = Item.objects.get(id=item_id)

#             # Format the email content
#             subject = "🛠️ Lost & Found Claim Received – We’re on it!"
#             message = f"""
# Hello,

# Thank you for submitting a claim for the item you believe is yours.

# We've received your contact details and have noted your interest in the item. Our team will now review your claim and verify the details. If everything checks out, we'll get in touch with you shortly to arrange the return.

# Here’s a quick summary of what happens next:
# - Our team will match the provided details with the item: "{item.name}" found at "{item.location}" on {item.date}.
# - If there’s a match, we’ll contact you via this email or phone number.
# - You may be asked to provide additional proof of ownership, if necessary.

# We appreciate your patience and honesty in helping us return lost items to their rightful owners.

# Warm regards,  
# LostNoMore Team  
# {settings.DEFAULT_FROM_EMAIL}
# """

#             send_mail(
#                 subject,
#                 message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 [email],
#                 fail_silently=False,
#             )

#             return JsonResponse({'status': 'success', 'message': 'Claim submitted.'})

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)})

#     return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required
@csrf_exempt
def claim_item(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            phone = data.get('phone')

            if not email or not phone:
                return JsonResponse({'status': 'error', 'message': 'Missing email or phone.'})

            item = Item.objects.get(id=item_id)

            subject = "🛠️ Lost & Found Claim Received – We’re on it!"
            message = f"""
Hello,

Thank you for submitting a claim for the item you believe is yours.

Item: "{item.name}"  
Location: "{item.location}"  
Date: {item.date}

We'll contact you soon.

– LostNoMore Team
"""

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return JsonResponse({'status': 'success', 'message': 'Claim submitted.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        # GET request - show a claim template (or even redirect to gallery if you want)
        item = get_object_or_404(Item, id=item_id)
        return render(request, 'gallery.html', {'item': item})



@login_required
def logout_view(request):
    logout(request)  # Log out the user
    return redirect('index')  # Redirect to homepage or another page






from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
import json
import re
from datetime import datetime, timedelta
from django.db.models import Q
from .models import Item


# Format function for item details with claim link
def format_items(items, title="Items found"):
    if not items:
        return f"<strong>{title}:</strong> No items found matching your query.<br>"

    formatted_items = f"<strong>{title}:</strong><br><br>"
    for item in items:
        formatted_items += (
            f"🔹 <strong>{item.name}</strong><br>"
            f"📍 <strong>Location:</strong> {item.location}<br>"
            f"📅 <strong>Date:</strong> {item.date}<br>"
            f"📝 <strong>Description:</strong> {item.description}<br>"
            f"🗂 <strong>Category:</strong> {item.category.capitalize()}<br>"
            f"🔄 <strong>Status:</strong> {item.status.capitalize()}<br>"
            f"🔗 <a href='/claim/{item.id}' target='_blank'>Claim this item</a><br>"
            f"{'-'*40}<br><br>"
        )
    return formatted_items


@csrf_exempt
@require_POST
def chatbot_query(request):
    data = json.loads(request.body)
    user_message = data.get('message', '').lower().strip()

    if not user_message:
        return JsonResponse({'response': "Please describe the item you're looking for."})

    today = datetime.today().date()

    # Time-based filters
    if "yesterday" in user_message:
        query_date = today - timedelta(days=1)
        items = Item.objects.filter(date=query_date)
        return JsonResponse({'response': format_items(items, f"Items reported on {query_date}")})

    if "last 7 days" in user_message or "past 7 days" in user_message:
        week_ago = today - timedelta(days=7)
        items = Item.objects.filter(date__gte=week_ago)
        return JsonResponse({'response': format_items(items, "Items from the past 7 days")})

    match = re.search(r'on (\d{1,2})', user_message)
    if match:
        day = int(match.group(1))
        items = Item.objects.filter(date__day=day)
        return JsonResponse({'response': format_items(items, f"Items from day {day}")})

    # Category detection
    category_map = {
        "pet": ["dog", "cat", "puppy", "kitten", "parrot", "pets"],
        "electronics": ["laptop", "phone", "tablet", "charger"],
        "documents": ["id", "card", "aadhaar", "pan", "license"],
        "accessories": ["hair", "clip", "ring", "watch"],
        "clothing": ["jacket", "sweater", "saree", "shirt", "cap"],
    }

    matched_category = None
    for category, keywords in category_map.items():
        if any(word in user_message for word in keywords):
            matched_category = category
            break

    # Location detection
    location_keywords = ["pythagoras", "turing", "alpha", "pi", "block", "zone"]
    matched_location = None
    for loc in location_keywords:
        if loc in user_message:
            matched_location = loc
            break

    # Build query
    query = Q()
    if matched_category:
        query &= Q(category__iexact=matched_category)
    if matched_location:
        query &= Q(location__icontains=matched_location)

    if not matched_category and not matched_location:
        keywords = re.findall(r'\b\w+\b', user_message)
        for word in keywords:
            query |= Q(name__icontains=word) | Q(description__icontains=word) | Q(location__icontains=word)

    items = Item.objects.filter(query).distinct()[:5]
    return JsonResponse({'response': format_items(items, "Here are some matching items")})
